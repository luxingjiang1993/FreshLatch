"""重建 dense 索引:语料文本 → text-embedding-v4 → SQLite vec。不以 FAISS 为真相。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freshlatch.store.embeddings import EMBED_MODEL, embed_texts, redact
from freshlatch.store.ingest import load_corpus
from freshlatch.store.pipeline import pack_vec
from freshlatch.store.sqlite_store import SQLiteStore

CORPUS = ROOT / "data" / "corpus"
DB = ROOT / "data" / "dense" / "index.sqlite"
REPORT = ROOT / "reports" / "dense-rebuild.md"
BATCH = 8


def main() -> int:
    pairs = load_corpus(CORPUS)
    chunks = [c for _doc, cs in pairs for c in cs]
    status = "ok"
    detail = f"chunks={len(chunks)}"
    try:
        vectors: list[list[float]] = []
        for start in range(0, len(chunks), BATCH):
            batch = chunks[start:start + BATCH]
            vectors.extend(embed_texts([c.text for c in batch]))
        if len(vectors) != len(chunks):
            raise RuntimeError("向量条数与 chunk 数不一致")
        for chunk, vec in zip(chunks, vectors):
            chunk.vec = pack_vec(vec)
        DB.parent.mkdir(parents=True, exist_ok=True)
        if DB.exists():
            DB.unlink()
        store = SQLiteStore(DB)
        for doc, doc_chunks in pairs:
            store.add_document(doc, doc_chunks)
        dim = len(vectors[0]) if vectors else 0
        detail = f"chunks={len(chunks)} dim={dim}"
    except Exception as exc:
        status = "failed"
        detail = redact(str(exc))[:180]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "\n".join([
            "# Dense 索引重建",
            "",
            f"- 模型: {EMBED_MODEL}",
            f"- 状态: {status}",
            f"- 说明: {detail}",
            "- 存储: SQLite chunks.vec,不是 FAISS",
            "- 密钥未写入本报告",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"status={status} model={EMBED_MODEL}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
