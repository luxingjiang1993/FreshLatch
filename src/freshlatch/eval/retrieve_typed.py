"""x1 分型三臂打分（RET-01.5）。

从 retrieve_eval import 打分函数，不改该文件。查询嵌入走 embed_cache。
语料与 traps 都经 load_corpus。主指标只含 score_role=arm。
不调用 _cached_query_embedder、_ingest_eval_corpus、load_trap_corpus、rerank_lexical。
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from freshlatch.eval.retrieve_eval import (
    _attach_vecs,
    _p95_ms,
    arm_pass_line,
    mrr_at_k,
    recall_at_k,
)
from freshlatch.eval.x1_checks import check_x1
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE, InMemoryStore, chunk_evidence_id
from freshlatch.store.checksum import aggregate_checksum, sha256_hex
from freshlatch.store.embed_cache import EMBED_CACHE_TABLE, embed_texts_cached, make_embed_cache_key
from freshlatch.store.embeddings import EMBED_MODEL
from freshlatch.store.ingest import load_corpus
from freshlatch.store.pipeline import RRF_K

# 成本估算（仓内未复核单价；标「估」）
CHARS_PER_TOKEN = 1.39
CNY_PER_MILLION_TOKENS = 0.5
TOP_K = 10
PRODUCTION_DENSE_DB_POSIX = "data/dense/index.sqlite"
ROW_LABELS = ("总体", "lexical", "paraphrase", "multi_hop", "trap+adversarial")
PREREG_FP_KEYS = (
    "corpus_aggregate_sha256",
    "questions_aggregate_sha256",
    "config_sha256",
)


def is_production_dense_db(path: str | Path) -> bool:
    """路径是否等于生产默认库。只做字符串比较，不 stat、不打开该文件。"""
    raw = str(path).replace("\\", "/").rstrip("/")
    if raw == PRODUCTION_DENSE_DB_POSIX:
        return True
    return raw.endswith("/" + PRODUCTION_DENSE_DB_POSIX)


def score_role_of(question: dict[str, Any]) -> str:
    """缺省视为 arm。"""
    role = question.get("score_role")
    if role is None or role == "":
        return "arm"
    return str(role)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _p50_ms(samples: list[float]) -> float:
    """与 _p95_ms 同一排序与 ceil 分位，取 0.50；入参是秒，返回毫秒。"""
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = max(0, math.ceil(0.50 * len(ordered)) - 1)
    return ordered[index] * 1000.0


def parse_prereg_fingerprints(text: str) -> dict[str, str]:
    """只解析三行指纹。忽略文件里其他 hex，不读 owner_freeze。"""
    found: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        for key in PREREG_FP_KEYS:
            prefix = key + ":"
            if stripped.startswith(prefix):
                found[key] = stripped[len(prefix) :].strip()
    return found


def compute_x1_fingerprints(
    *,
    corpus: Path,
    traps: Path,
    questions: Path,
    config: Path,
) -> dict[str, str]:
    """口径同 RET-01.4：语料聚合 root 为 corpus 与 traps 的共同父目录。"""
    corpus = Path(corpus)
    traps = Path(traps)
    questions = Path(questions)
    config = Path(config)
    md_files = sorted(corpus.rglob("*.md")) + sorted(traps.rglob("*.md"))
    root = corpus.parent
    return {
        "corpus_aggregate_sha256": aggregate_checksum(md_files, root=root),
        "questions_aggregate_sha256": aggregate_checksum(
            [questions], root=questions.parent
        ),
        "config_sha256": sha256_hex(config.read_bytes()),
    }


def fingerprints_match(prereg_text: str, computed: dict[str, str]) -> bool:
    parsed = parse_prereg_fingerprints(prereg_text)
    return all(parsed.get(k) == computed.get(k) for k in PREREG_FP_KEYS)


def _load_questions(source: Path | str | list | dict) -> list[dict[str, Any]]:
    if isinstance(source, list):
        return list(source)
    if isinstance(source, dict):
        qs = source.get("queries", source)
        if isinstance(qs, list):
            return list(qs)
        raise ValueError("questions JSON 需要 queries 数组")
    path = Path(source)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _load_questions(raw)


def _load_config(config: dict | Path | str) -> dict[str, Any]:
    if isinstance(config, dict):
        return dict(config)
    return json.loads(Path(config).read_text(encoding="utf-8"))


def ingest_x1_corpus(store: InMemoryStore, corpus: Path, traps: Path) -> int:
    """两个目录都走 load_corpus（断言 as_of 与 t0/ t1/ 一致）。"""
    n = 0
    for doc, chunks in load_corpus(Path(corpus)):
        store.add_document(doc, chunks)
        n += len(chunks)
    trap_root = Path(traps)
    if trap_root.is_dir():
        for doc, chunks in load_corpus(trap_root):
            store.add_document(doc, chunks)
            n += len(chunks)
    return n


def unique_embed_texts(corpus: Path, traps: Path, questions: Path | str | list | dict) -> list[str]:
    """估算与缓存键使用的文本：全部 chunk 正文 + 全部 query，按首次出现去重。"""
    seen: set[str] = set()
    out: list[str] = []
    store = InMemoryStore()
    ingest_x1_corpus(store, Path(corpus), Path(traps))
    for chunk in store._chunks:
        text = chunk.text
        if text not in seen:
            seen.add(text)
            out.append(text)
    for item in _load_questions(questions):
        q = str(item.get("query", ""))
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out


def count_uncached(
    texts: list[str],
    *,
    cache_path: Path | str | None,
    model: str,
    dim: int,
) -> tuple[int, int, int]:
    """返回 (uncached_chars, n_miss, n_hit)。不调用 embed_texts。"""
    if not texts:
        return 0, 0, 0
    found: set[str] = set()
    conn = None
    path = Path(cache_path) if cache_path is not None else None
    if path is not None and path.is_file():
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {EMBED_CACHE_TABLE} ("
                "key TEXT PRIMARY KEY NOT NULL,"
                "vec BLOB NOT NULL"
                ")"
            )
        except sqlite3.Error:
            conn.close()
            conn = None
    miss_chars = 0
    n_miss = 0
    n_hit = 0
    seen: set[str] = set()
    try:
        for text in texts:
            key = make_embed_cache_key(model, dim, text)
            if key in seen:
                continue
            seen.add(key)
            hit = False
            if conn is not None:
                row = conn.execute(
                    f"SELECT 1 FROM {EMBED_CACHE_TABLE} WHERE key = ?",
                    (key,),
                ).fetchone()
                hit = row is not None
            if hit:
                n_hit += 1
                found.add(key)
            else:
                n_miss += 1
                miss_chars += len(text)
    finally:
        if conn is not None:
            conn.close()
    return miss_chars, n_miss, n_hit


def estimate_cost_from_uncached(uncached_chars: int) -> tuple[float, float]:
    est_tokens = uncached_chars / CHARS_PER_TOKEN
    est_cny = est_tokens / 1_000_000 * CNY_PER_MILLION_TOKENS
    return est_tokens, est_cny


def format_estimate_lines(uncached_chars: int, est_tokens: float, est_cny: float) -> str:
    return (
        f"uncached_chars={uncached_chars}\n"
        f"est_tokens={est_tokens:.6f} 估 (uncached_chars / {CHARS_PER_TOKEN})\n"
        f"est_cny={est_cny:.8f} 估 (est_tokens / 1000000 * {CNY_PER_MILLION_TOKENS})\n"
    )


def conflict_pair_correct(ranked: list[str], pair: dict[str, Any]) -> bool:
    """现行条排名严格高于被取代条。被取代不在且现行在 → 正确；两者都不在或只有被取代 → 不正确。"""
    in_force = str(pair.get("in_force", ""))
    superseded = str(pair.get("superseded", ""))
    try:
        ri = ranked.index(in_force)
    except ValueError:
        ri = None
    try:
        rs = ranked.index(superseded)
    except ValueError:
        rs = None
    if ri is not None and rs is not None:
        return ri < rs
    if ri is not None and rs is None:
        return True
    return False


def guardrail_pass(hits: list, *, query_as_of: str = "T1") -> bool:
    """T1 查询的返回列表里不得出现 as_of=T0 的块。"""
    del query_as_of
    return all(getattr(c, "as_of", None) != "T0" for c in hits)


def _full_hit(ranked: list[str], relevant: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    head = set(ranked[:k])
    return 1.0 if all(eid in head for eid in relevant) else 0.0


def _distractor_hit(ranked: list[str], distractors: list[str], k: int) -> float:
    if not distractors:
        return 0.0
    head = set(ranked[:k])
    return 1.0 if any(eid in head for eid in distractors) else 0.0


def _win_tie_loss(hybrid_r: float, bm25_r: float) -> str:
    if hybrid_r > bm25_r:
        return "win"
    if hybrid_r < bm25_r:
        return "loss"
    return "tie"


def _in_bucket(question: dict[str, Any], label: str) -> bool:
    if label == "总体":
        return True
    if label == "trap+adversarial":
        return question.get("category") in {"trap", "adversarial"}
    return question.get("qtype") == label


class _CountingEmbedder:
    """注入假 embed_fn 时计数；未注入则走 embed_texts（正式跑分）。"""

    def __init__(self, inner: Callable[[list[str]], list[list[float]]] | None):
        self.inner = inner
        self.calls = 0
        self.n_texts = 0

    def __call__(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        self.n_texts += len(texts)
        if self.inner is None:
            from freshlatch.store.embeddings import embed_texts

            return embed_texts(texts)
        return self.inner(texts)


def make_cached_query_embedder(
    queries: list[str],
    *,
    cache_path: Path | str,
    model: str,
    dim: int,
    embed_fn: Callable[[list[str]], list[list[float]]] | None = None,
) -> tuple[Callable[[str], list[float]], _CountingEmbedder]:
    """查询向量只走 embed_cache。禁止使用 retrieve_eval._cached_query_embedder。"""
    counter = _CountingEmbedder(embed_fn)
    unique: list[str] = []
    seen: set[str] = set()
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    vecs = embed_texts_cached(
        unique,
        dim=dim,
        cache_path=cache_path,
        model=model,
        embed_fn=counter,
    )
    mapping = {text: vec for text, vec in zip(unique, vecs)}

    def embed(query: str) -> list[float]:
        return mapping[query]

    return embed, counter


def _empty_arm_metrics() -> dict[str, Any]:
    return {
        "n": 0,
        "R@10": 0.0,
        "MRR@10": 0.0,
        "multi_hop_full_hit@10": None,
        "distractor_hit@10": 0.0,
        "win": 0,
        "tie": 0,
        "loss": 0,
        "p50_ms": 0.0,
        "p95_ms": 0.0,
        "modes_seen": [],
        "mode_honest": True,
    }


def _aggregate_arm(
    rows: list[dict[str, Any]],
    latencies: list[float],
    modes: list[str],
    expected_mode: str,
    *,
    full_hit_applicable: bool,
) -> dict[str, Any]:
    if not rows:
        out = _empty_arm_metrics()
        out["mode_honest"] = True
        return out
    recs = [r["recall@10"] for r in rows]
    mrrs = [r["mrr@10"] for r in rows]
    dist = [r["distractor_hit@10"] for r in rows]
    wtl = [r["wtl"] for r in rows]
    fulls = [r["full_hit@10"] for r in rows if r.get("qtype") == "multi_hop"]
    seen = sorted(set(modes))
    honest = set(modes) == {expected_mode} if expected_mode != "bm25" else True
    if expected_mode == "bm25":
        honest = set(modes) <= {"bm25"}
    return {
        "n": len(rows),
        "R@10": _mean(recs),
        "MRR@10": _mean(mrrs),
        "multi_hop_full_hit@10": _mean(fulls) if full_hit_applicable and fulls else None,
        "distractor_hit@10": _mean(dist),
        "win": sum(1 for x in wtl if x == "win"),
        "tie": sum(1 for x in wtl if x == "tie"),
        "loss": sum(1 for x in wtl if x == "loss"),
        "p50_ms": _p50_ms(latencies),
        "p95_ms": _p95_ms(latencies),
        "modes_seen": seen,
        "mode_honest": honest,
    }


def run_typed_compare(
    *,
    corpus: Path,
    traps: Path,
    questions: Path | str | list | dict,
    config: dict | Path | str,
    dense_db: Path,
    cache_path: Path,
    out_dir: Path | None,
    embed_fn: Callable[[list[str]], list[list[float]]] | None = None,
    disable_as_of: bool = False,
    skip_estimate: bool = False,
) -> dict[str, Any]:
    """三臂分型打分。主数字始终带 as_of 过滤。disable_as_of 只额外出诊断，不覆盖主表。"""
    if is_production_dense_db(dense_db):
        raise ValueError("拒绝使用生产默认 dense 库 data/dense/index.sqlite")
    cfg = _load_config(config)
    model = str(cfg["embed_model"]) if cfg.get("embed_model") else EMBED_MODEL
    dim = int(cfg["embed_dim"]) if cfg.get("embed_dim") is not None else 1024
    budget = float(cfg["budget_cny_max"]) if cfg.get("budget_cny_max") is not None else 10.0
    top_k = int(cfg["top_k"]) if cfg.get("top_k") is not None else TOP_K
    qs = _load_questions(questions)

    texts = unique_embed_texts(Path(corpus), Path(traps), questions)
    uncached_chars, n_miss, n_hit_est = count_uncached(
        texts, cache_path=cache_path, model=model, dim=dim
    )
    est_tokens, est_cny = estimate_cost_from_uncached(uncached_chars)
    estimate = {
        "uncached_chars": uncached_chars,
        "est_tokens": est_tokens,
        "est_cny": est_cny,
        "n_miss": n_miss,
        "n_hit": n_hit_est,
    }
    if not skip_estimate and est_cny > budget:
        raise RuntimeError(f"est_cny={est_cny} 超过 budget_cny_max={budget}")

    store = InMemoryStore()
    n_chunks = ingest_x1_corpus(store, Path(corpus), Path(traps))
    attached = _attach_vecs(store, Path(dense_db))
    if attached != len(store._chunks) or attached == 0:
        raise ValueError("dense 索引未覆盖全部 chunk,拒绝把降级结果写成 dense/hybrid")

    query_texts = [str(q.get("query", "")) for q in qs]
    embedder, counter = make_cached_query_embedder(
        query_texts,
        cache_path=cache_path,
        model=model,
        dim=dim,
        embed_fn=embed_fn,
    )
    store.query_embedder = embedder

    def _run_pool(*, as_of_off: bool) -> dict[str, Any]:
        per_query: list[dict[str, Any]] = []
        guardrail_rows: list[dict[str, Any]] = []
        conflict_ok = 0
        conflict_n = 0
        arm_by_mode: dict[str, list[dict[str, Any]]] = {
            "bm25": [],
            "dense": [],
            "hybrid": [],
        }
        lat_by_mode: dict[str, list[float]] = {"bm25": [], "dense": [], "hybrid": []}
        modes_by_mode: dict[str, list[str]] = {"bm25": [], "dense": [], "hybrid": []}

        for item in qs:
            role = score_role_of(item)
            as_of = None if as_of_off else item.get("as_of", "T1")
            ranked_by_mode: dict[str, list[str]] = {}
            hits_by_mode: dict[str, list] = {}
            rec_by_mode: dict[str, float] = {}
            for mode in ("bm25", "dense", "hybrid"):
                store.bind_eval_retrieval_mode(None if mode == "bm25" else mode)
                started = time.perf_counter()
                hits = store.retrieve(
                    str(item.get("query", "")),
                    as_of=as_of,  # type: ignore[arg-type]
                    top_k=top_k,
                )
                elapsed = time.perf_counter() - started
                got_mode = getattr(store, "last_retrieval_mode", mode)
                ranked = [chunk_evidence_id(c) for c in hits]
                ranked_by_mode[mode] = ranked
                hits_by_mode[mode] = hits
                relevant = [str(x) for x in (item.get("relevant") or [])]
                distractors = [str(x) for x in (item.get("distractors") or [])]
                rec = recall_at_k(ranked, relevant, top_k)
                rec_by_mode[mode] = rec
                row = {
                    "id": item.get("id"),
                    "qtype": item.get("qtype"),
                    "category": item.get("category"),
                    "score_role": role,
                    "recall@10": rec,
                    "mrr@10": mrr_at_k(ranked, relevant, top_k),
                    "full_hit@10": _full_hit(ranked, relevant, top_k),
                    "distractor_hit@10": _distractor_hit(ranked, distractors, top_k),
                    "wtl": "tie",
                    "latency_s": elapsed,
                    "last_retrieval_mode": got_mode,
                }
                if role == "arm":
                    arm_by_mode[mode].append(row)
                    lat_by_mode[mode].append(elapsed)
                    modes_by_mode[mode].append(got_mode)
            store.bind_eval_retrieval_mode(None)
            rec_by_mode["hybrid_vs_bm25"] = rec_by_mode["hybrid"] - rec_by_mode["bm25"]
            wtl = _win_tie_loss(rec_by_mode["hybrid"], rec_by_mode["bm25"])
            if role == "arm":
                for mode in ("bm25", "dense", "hybrid"):
                    if arm_by_mode[mode] and arm_by_mode[mode][-1]["id"] == item.get("id"):
                        arm_by_mode[mode][-1]["wtl"] = wtl

            pair = item.get("conflict_pair")
            pair_ok = None
            if isinstance(pair, dict) and pair.get("in_force") and pair.get("superseded"):
                pair_ok = conflict_pair_correct(ranked_by_mode["hybrid"], pair)
                conflict_n += 1
                if pair_ok:
                    conflict_ok += 1

            g_pass = None
            t0_in_hits = 0
            if role == "guardrail":
                g_hits = hits_by_mode["hybrid"]
                t0_in_hits = sum(1 for c in g_hits if getattr(c, "as_of", None) == "T0")
                g_pass = t0_in_hits == 0
                guardrail_rows.append({
                    "id": item.get("id"),
                    "pass": g_pass,
                    "t0_hits": t0_in_hits,
                    "as_of": item.get("as_of"),
                })

            per_query.append({
                "id": item.get("id"),
                "qtype": item.get("qtype"),
                "category": item.get("category"),
                "score_role": role,
                "as_of": item.get("as_of"),
                "ranked": ranked_by_mode,
                "recall@10": rec_by_mode,
                "conflict_pair_correct": pair_ok,
                "guardrail_pass": g_pass,
                "t0_hits": t0_in_hits if role == "guardrail" else None,
            })

        buckets: dict[str, dict[str, Any]] = {}
        for label in ROW_LABELS:
            buckets[label] = {}
            for mode in ("bm25", "dense", "hybrid"):
                selected_rows = []
                selected_lat = []
                selected_modes = []
                arm_items = [item for item in qs if score_role_of(item) == "arm"]
                arm_index = {id(item): j for j, item in enumerate(arm_items)}
                for item in qs:
                    if score_role_of(item) != "arm" or not _in_bucket(item, label):
                        continue
                    j = arm_index[id(item)]
                    selected_rows.append(arm_by_mode[mode][j])
                    selected_lat.append(lat_by_mode[mode][j])
                    selected_modes.append(modes_by_mode[mode][j])
                full_ok = label in {"总体", "multi_hop"}
                buckets[label][mode] = _aggregate_arm(
                    selected_rows,
                    selected_lat,
                    selected_modes,
                    mode,
                    full_hit_applicable=full_ok,
                )

        dense_honest = buckets["总体"]["dense"]["mode_honest"]
        hybrid_honest = buckets["总体"]["hybrid"]["mode_honest"]
        bm25_r = buckets["总体"]["bm25"]["R@10"]
        dense_r = buckets["总体"]["dense"]["R@10"]
        hybrid_r = buckets["总体"]["hybrid"]["R@10"]
        # 参考列：a0 取本轮 bm25，避免误用 hard-gold A0
        verdict = arm_pass_line(
            bm25=bm25_r, dense=dense_r, hybrid=hybrid_r, a0=bm25_r
        )
        return {
            "per_query": per_query,
            "buckets": buckets,
            "guardrail": guardrail_rows,
            "conflict_pair_ordering_accuracy": (
                (conflict_ok / conflict_n) if conflict_n else None
            ),
            "conflict_pair_n": conflict_n,
            "conflict_pair_ok": conflict_ok,
            "dense_honest": dense_honest,
            "hybrid_honest": hybrid_honest,
            "arm_pass_line": verdict,
            "n_arm": sum(1 for q in qs if score_role_of(q) == "arm"),
            "n_guardrail": sum(1 for q in qs if score_role_of(q) == "guardrail"),
        }

    main = _run_pool(as_of_off=False)
    diagnostic = None
    if disable_as_of:
        diagnostic = _run_pool(as_of_off=True)

    payload: dict[str, Any] = {
        "level": "实验/冒烟",
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "rrf_k": RRF_K,
        "top_k": top_k,
        "n_chunks": n_chunks,
        "estimate": estimate,
        "embed_calls": counter.calls,
        "embed_texts_n": counter.n_texts,
        "cache_hits_estimate": n_hit_est,
        "llm_tokens": 0,
        "main": main,
        "as_of_off_diagnostic": diagnostic,
        "diagnostic_ran": bool(disable_as_of),
    }
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        md_path = out / "retrieve-x1-arm-compare.md"
        json_path = out / "retrieve-x1-arm-compare.json"
        md_path.write_text(
            render_typed_report(payload, include_diagnostic=disable_as_of),
            encoding="utf-8",
        )
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        payload["report_path"] = str(md_path)
        payload["json_path"] = str(json_path)
        if disable_as_of and diagnostic is not None:
            diag_path = out / "retrieve-x1-as-of-off.md"
            diag_path.write_text(
                render_diagnostic_section(diagnostic),
                encoding="utf-8",
            )
            payload["diagnostic_path"] = str(diag_path)
    return payload


def _fmt_full(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def render_typed_report(payload: dict[str, Any], *, include_diagnostic: bool) -> str:
    main = payload["main"]
    lines = [
        "# x1 BM25 / dense / hybrid 分型对比（实验 / 冒烟）",
        "",
        "- 层身份: 实验/冒烟；不报方差；不作统计显著；非改臂授权",
        f"- 代码生产默认: {payload['production_retrieval_mode']}",
        f"- RRF k: {payload['rrf_k']}",
        "- 融合: 名次倒数,不是 α 加权；本路径不调用 rerank_lexical",
        "- 查询嵌入: embed_cache（不是 retrieve_eval._cached_query_embedder）",
        f"- n_arm: {main['n_arm']}（主 R@10 / MRR / 干扰命中 只含 score_role=arm）",
        f"- n_guardrail: {main['n_guardrail']}（不进主 R@10 分母）",
        f"- dense 列确为 dense: {'pass' if main['dense_honest'] else 'fail'}",
        f"- hybrid 列确为 hybrid: {'pass' if main['hybrid_honest'] else 'fail'}",
        f"- embed 调用次数: {payload['embed_calls']}（缓存未命中才调用）",
        f"- 缓存命中（估, unique texts）: {payload['cache_hits_estimate']}",
        f"- embed token: {payload['estimate']['est_tokens']:.6f} 估",
        f"- LLM token: {payload['llm_tokens']}",
        f"- 估算成本 CNY: {payload['estimate']['est_cny']:.8f} 估",
        "",
        "## 主表（as_of 过滤打开；不含护栏题）",
        "",
        "| 行 | 臂 | R@10 | MRR@10 | multi_hop全命中@10 | 干扰命中@10 | 胜/平/负 | p50_ms | p95_ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for label in ROW_LABELS:
        for mode in ("bm25", "dense", "hybrid"):
            b = main["buckets"][label][mode]
            wtl = f"{b['win']}/{b['tie']}/{b['loss']}" if mode == "hybrid" else "n/a"
            lines.append(
                f"| {label} | {mode} | {b['R@10']:.4f} | {b['MRR@10']:.4f} | "
                f"{_fmt_full(b['multi_hop_full_hit@10'])} | {b['distractor_hit@10']:.4f} | "
                f"{wtl} | {b['p50_ms']:.3f} | {b['p95_ms']:.3f} |"
            )
    lines.extend(["", "## 护栏（不改写主 R@10）", ""])
    if not main["guardrail"]:
        lines.append("- （无 guardrail 题）")
    else:
        for row in main["guardrail"]:
            flag = "通过" if row["pass"] else "不通过"
            lines.append(
                f"- {row['id']}: {flag}（T1 结果中 T0 块数={row['t0_hits']}）"
            )
    acc = main["conflict_pair_ordering_accuracy"]
    acc_s = "n/a" if acc is None else f"{acc:.4f}"
    lines.extend([
        "",
        "## conflict-pair ordering accuracy（单列，不并进 R@10）",
        "",
        f"- {acc_s}（配对 n={main['conflict_pair_n']}，正确 {main['conflict_pair_ok']}）",
        "",
        "## 参考（arm_pass_line，失败不导致本脚本非 0）",
        "",
        f"- bm25_vs_a0: {main['arm_pass_line']['bm25_vs_a0']}（本轮 a0 取 bm25 自身，仅参考）",
        f"- hybrid_vs_min: {main['arm_pass_line']['hybrid_vs_min']}",
        f"- pass: {main['arm_pass_line']['pass']}",
        f"- hybrid 落后不是脚本错误；非改臂授权",
        "",
        "## 关掉 as_of 的诊断",
        "",
    ])
    if include_diagnostic and payload.get("as_of_off_diagnostic") is not None:
        lines.append("- 已跑。数字见下一节与 retrieve-x1-as-of-off.md，**不覆盖主表**。")
        lines.append("")
        lines.append(render_diagnostic_section(payload["as_of_off_diagnostic"]))
    else:
        lines.append("- 未跑（缺省关闭）。")
        lines.append("")
    lines.append("本页是实验轨对比,不是统计结论。生产默认仍是 BM25。")
    lines.append("")
    return "\n".join(lines)


def render_diagnostic_section(diagnostic: dict[str, Any]) -> str:
    lines = [
        "## 诊断：as_of 过滤关闭（不进主结论）",
        "",
        "| 行 | 臂 | R@10 | MRR@10 |",
        "|---|---|---|---|",
    ]
    for label in ROW_LABELS:
        for mode in ("bm25", "dense", "hybrid"):
            b = diagnostic["buckets"][label][mode]
            lines.append(
                f"| {label} | {mode} | {b['R@10']:.4f} | {b['MRR@10']:.4f} |"
            )
    lines.append("")
    lines.append("以上不得覆盖主 R@10 / MRR。生产检索未改。")
    lines.append("")
    return "\n".join(lines)


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="x1 分型三臂打分（假向量单测 / RET-01.6 复跑）")
    parser.add_argument("--corpus", default="data/exp/x1/corpus")
    parser.add_argument("--traps", default="data/exp/x1/traps")
    parser.add_argument("--questions", default="data/eval/retrieve_x1.json")
    parser.add_argument("--config", required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--estimate-only", action="store_true")
    parser.add_argument("--dense-db", default=None)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--prereg", default=None)
    parser.add_argument(
        "--disable-as-of",
        action="store_true",
        help="可选诊断：关掉本次跑分的 as_of 过滤。缺省关闭。不改生产检索。",
    )
    args = parser.parse_args(argv)

    corpus = Path(args.corpus)
    traps = Path(args.traps)
    questions = Path(args.questions)
    config = Path(args.config)

    if args.dense_db is not None and is_production_dense_db(args.dense_db):
        print("拒绝 --dense-db=data/dense/index.sqlite", file=sys.stderr)
        return 1

    if args.check_only:
        result = check_x1(corpus, traps, questions, config)
        print(result.format_report(), end="")
        if args.prereg:
            prereg_text = Path(args.prereg).read_text(encoding="utf-8")
            computed = compute_x1_fingerprints(
                corpus=corpus, traps=traps, questions=questions, config=config
            )
            if not fingerprints_match(prereg_text, computed):
                print("prereg fingerprint mismatch", file=sys.stderr)
                parsed = parse_prereg_fingerprints(prereg_text)
                for key in PREREG_FP_KEYS:
                    print(
                        f"  {key} file={parsed.get(key)} computed={computed.get(key)}",
                        file=sys.stderr,
                    )
                return 1
            print("prereg fingerprints ok")
        return result.exit_code

    if args.estimate_only:
        cfg = _load_config(config)
        model = str(cfg["embed_model"]) if cfg.get("embed_model") else EMBED_MODEL
        dim = int(cfg["embed_dim"]) if cfg.get("embed_dim") is not None else 1024
        budget = float(cfg["budget_cny_max"]) if cfg.get("budget_cny_max") is not None else 10.0
        texts = unique_embed_texts(corpus, traps, questions)
        uncached_chars, _n_miss, _n_hit = count_uncached(
            texts, cache_path=args.cache, model=model, dim=dim
        )
        est_tokens, est_cny = estimate_cost_from_uncached(uncached_chars)
        print(format_estimate_lines(uncached_chars, est_tokens, est_cny), end="")
        if est_cny > budget:
            print(f"est_cny exceeds budget_cny_max={budget}", file=sys.stderr)
            return 1
        return 0

    missing = [
        name
        for name, val in (
            ("--dense-db", args.dense_db),
            ("--cache", args.cache),
            ("--out", args.out),
            ("--prereg", args.prereg),
        )
        if val is None
    ]
    if missing:
        print(
            "正式模式需要 --dense-db --cache --out --prereg；"
            "本票默认请用 --check-only 或 --estimate-only。缺少: "
            + " ".join(missing),
            file=sys.stderr,
        )
        return 2

    if args.prereg:
        prereg_text = Path(args.prereg).read_text(encoding="utf-8")
        computed = compute_x1_fingerprints(
            corpus=corpus, traps=traps, questions=questions, config=config
        )
        if not fingerprints_match(prereg_text, computed):
            print("prereg fingerprint mismatch", file=sys.stderr)
            return 1

    try:
        run_typed_compare(
            corpus=corpus,
            traps=traps,
            questions=questions,
            config=config,
            dense_db=Path(args.dense_db),
            cache_path=Path(args.cache),
            out_dir=Path(args.out),
            disable_as_of=bool(args.disable_as_of),
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return run_cli()
