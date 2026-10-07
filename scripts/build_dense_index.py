"""重建 dense 索引:语料文本 → text-embedding-v4 → SQLite vec。不以 FAISS 为真相。

Hard-Gold / A0 同库口径(#259):索引覆盖 data/corpus + data/traps。
冒烟臂对比仅 ingest corpus 时,多余 trap 向量不影响 attached==len(store) 校验。

可选参数由 parse_rebuild_paths 解析。五个都不传时仍用模块常量，
不打开缓存，直接调用 embed_texts（#259 路径）。
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from freshlatch.store.embed_cache import embed_texts_cached
from freshlatch.store.embeddings import EMBED_MODEL, embed_texts, redact
from freshlatch.store.ingest import load_corpus
from freshlatch.store.pipeline import pack_vec
from freshlatch.store.sqlite_store import SQLiteStore

CORPUS = ROOT / "data" / "corpus"
TRAPS = ROOT / "data" / "traps"
DB = ROOT / "data" / "dense" / "index.sqlite"
REPORT = ROOT / "reports" / "dense-rebuild.md"
BATCH = 8
# x1 缓存路径使用的维度；无参数重建不走缓存，也不把该常量传给 embed_texts。
X1_EMBED_DIM = 1024


class RebuildPathError(ValueError):
    """显式路径违反隔离规则：缺 --db/--cache/--report，或三者指向默认路径。"""


@dataclass(frozen=True)
class RebuildPaths:
    corpus: Path
    traps: Path
    db: Path
    report: Path
    cache: Path | None


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def parse_rebuild_paths(argv: list[str]) -> RebuildPaths:
    """解析可选路径。argv 不含程序名。空列表 = 模块常量且不启用缓存。

    只要传了任何参数，就必须显式给出 --db、--cache、--report，
    且三者都不能解析到默认 DB / REPORT。缺一或撞默认则报错，不开始构建。
    """
    parser = argparse.ArgumentParser(prog="build_dense_index.py")
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--traps", type=Path, default=None)
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--cache", type=Path, default=None)
    args = parser.parse_args(argv)
    if not argv:
        return RebuildPaths(
            corpus=CORPUS, traps=TRAPS, db=DB, report=REPORT, cache=None
        )
    missing = [
        flag
        for flag, value in (
            ("--db", args.db),
            ("--cache", args.cache),
            ("--report", args.report),
        )
        if value is None
    ]
    if missing:
        raise RebuildPathError(
            "传入参数时必须显式给出 --db、--cache、--report，缺少: "
            + "、".join(missing)
        )
    db = _resolved(args.db)
    cache = _resolved(args.cache)
    report = _resolved(args.report)
    forbidden = {_resolved(DB), _resolved(REPORT)}
    for flag, path in (("--db", db), ("--cache", cache), ("--report", report)):
        if path in forbidden:
            raise RebuildPathError(f"{flag} 不能指向默认路径")
    return RebuildPaths(
        corpus=CORPUS if args.corpus is None else args.corpus,
        traps=TRAPS if args.traps is None else args.traps,
        db=db,
        report=report,
        cache=cache,
    )


def _load_pairs(corpus: Path = CORPUS, traps: Path = TRAPS) -> list:
    """主语料 + traps（与 hard A0 / 臂对比同库）。"""
    pairs = list(load_corpus(corpus))
    if traps.is_dir():
        pairs.extend(load_corpus(traps))
    return pairs


def main() -> int:
    try:
        paths = parse_rebuild_paths(sys.argv[1:])
    except RebuildPathError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    pairs = _load_pairs(paths.corpus, paths.traps)
    chunks = [c for _doc, cs in pairs for c in cs]
    corpus_n = sum(len(cs) for _d, cs in load_corpus(paths.corpus))
    trap_n = len(chunks) - corpus_n
    status = "ok"
    detail = f"chunks={len(chunks)} corpus={corpus_n} traps={trap_n}"
    try:
        vectors: list[list[float]] = []
        for start in range(0, len(chunks), BATCH):
            batch = chunks[start:start + BATCH]
            texts = [c.text for c in batch]
            if paths.cache is None:
                vectors.extend(embed_texts(texts))
            else:
                vectors.extend(
                    embed_texts_cached(
                        texts,
                        dim=X1_EMBED_DIM,
                        cache_path=paths.cache,
                        model=EMBED_MODEL,
                    )
                )
        if len(vectors) != len(chunks):
            raise RuntimeError("向量条数与 chunk 数不一致")
        for chunk, vec in zip(chunks, vectors):
            chunk.vec = pack_vec(vec)
        paths.db.parent.mkdir(parents=True, exist_ok=True)
        if paths.db.exists():
            paths.db.unlink()
        store = SQLiteStore(paths.db)
        for doc, doc_chunks in pairs:
            store.add_document(doc, doc_chunks)
        dim = len(vectors[0]) if vectors else 0
        detail = (
            f"chunks={len(chunks)} corpus={corpus_n} traps={trap_n} dim={dim} "
            f"scope=corpus+traps"
        )
    except Exception as exc:
        status = "failed"
        detail = redact(str(exc))[:180]
    paths.report.parent.mkdir(parents=True, exist_ok=True)
    paths.report.write_text(
        "\n".join([
            "# Dense 索引重建",
            "",
            f"- 模型: {EMBED_MODEL}",
            f"- 状态: {status}",
            f"- 说明: {detail}",
            "- 评测库: corpus + traps（与 Hard-Gold A0 / 臂对比同库；#259）",
            "- 存储: SQLite chunks.vec,不是 FAISS",
            "- 密钥未写入本报告",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"status={status} model={EMBED_MODEL} {detail}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
