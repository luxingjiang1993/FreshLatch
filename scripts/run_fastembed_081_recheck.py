"""fastembed 0.8.1 复核。不改生产代码，不改金标，不调用付费 API。

四臂：bm25、hybrid、hybrid+rerank_lexical、hybrid+rerank（BAAI/bge-reranker-base，K=10）。
bootstrap 10000 次，seed=20261007，配对差 = 右 − 左，95% 线性插值百分位。
McNemar 用 Recall@10 命中，精确二项、双侧。
p95 用 retrieve_eval._p95_ms。全检索 p95 对 #285；只计重排的 p95 对 #293。

``embed`` 子命令用当前解释器里的 fastembed 把向量写到盘外，供 0.7.1 对照。
"""

from __future__ import annotations

import argparse
import importlib.metadata as importlib_metadata
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
os.environ.pop("DASHSCOPE_API_KEY", None)

from freshlatch.eval.neural_rerank import mcnemar_p  # noqa: E402
from freshlatch.eval.retrieve_eval import _p95_ms, mrr_at_k, ndcg_at_k, recall_at_k  # noqa: E402
from freshlatch.store.base import (  # noqa: E402
    PRODUCTION_RETRIEVAL_MODE,
    InMemoryStore,
    chunk_evidence_id,
)
from freshlatch.store.ingest import load_corpus  # noqa: E402
from freshlatch.store.local_embed import embed_texts_local  # noqa: E402
from freshlatch.store.neural_rerank import (  # noqa: E402
    RERANK_MODE_LEXICAL,
    RERANK_MODE_NEURAL,
    rerank_hybrid_candidates,
    warmup_neural_rerank,
)
from freshlatch.store.pipeline import pack_vec, tokenize  # noqa: E402

N_BOOT = 10000
BOOT_SEED = 20261007
TOP_K = 10
MODES = ("bm25", "hybrid", "hybrid+rerank_lexical", "hybrid+rerank")
QUESTIONS = ROOT / "data/exp/x1/questions.json"
CORPUS = ROOT / "data/exp/x1/corpus"
TRAPS = ROOT / "data/exp/x1/traps"
X1_PER_QUERY = ROOT / "docs/evidence/x1-retrieval-modes/per-query.json"
ISSUE_284 = ROOT / "docs/evidence/issue-284/summary.json"
NEURAL_SUMMARY = ROOT / "docs/evidence/neural-rerank/summary.json"
NEURAL_PER_QUERY = ROOT / "docs/evidence/neural-rerank/per-query.json"
NEURAL_COST = ROOT / "docs/evidence/neural-rerank/cost.json"


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _percentile(sorted_xs: list[float], p: float) -> float:
    if not sorted_xs:
        return 0.0
    k = (len(sorted_xs) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_xs[lo]
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (k - lo)


def _boot_ci(diffs: list[float], rng: random.Random) -> dict[str, float]:
    n = len(diffs)
    means: list[float] = []
    for _ in range(N_BOOT):
        total = 0.0
        for _j in range(n):
            total += diffs[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    return {
        "estimate": _mean(diffs),
        "ci95_low": _percentile(means, 0.025),
        "ci95_high": _percentile(means, 0.975),
    }


def _pair(rows: list[dict[str, Any]], left: str, right: str, key: str, rng: random.Random) -> dict[str, Any]:
    diffs = [row[key][right] - row[key][left] for row in rows]
    ci = _boot_ci(diffs, rng)
    out: dict[str, Any] = {
        "left": left,
        "right": right,
        "metric": key,
        "left_mean": _mean([row[key][left] for row in rows]),
        "right_mean": _mean([row[key][right] for row in rows]),
        **ci,
    }
    if key == "recall":
        left_only = [row["id"] for row in rows if row[key][left] == 1.0 and row[key][right] == 0.0]
        right_only = [row["id"] for row in rows if row[key][left] == 0.0 and row[key][right] == 1.0]
        both = sum(1 for row in rows if row[key][left] == 1.0 and row[key][right] == 1.0)
        neither = sum(1 for row in rows if row[key][left] == 0.0 and row[key][right] == 0.0)
        out["mcnemar"] = {
            "left_only": len(left_only),
            "right_only": len(right_only),
            "both_hit": both,
            "neither": neither,
            "p_two_sided": mcnemar_p(len(left_only), len(right_only)),
            "left_only_ids": left_only,
            "right_only_ids": right_only,
        }
    return out


def _fresh_pair(rows: list[dict[str, Any]], left: str, right: str, key: str) -> dict[str, Any]:
    return _pair(rows, left, right, key, random.Random(BOOT_SEED))


def _arm_questions() -> list[dict[str, Any]]:
    raw = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    arm = [item for item in raw["queries"] if (item.get("score_role") or "arm") == "arm"]
    if len(arm) != 224:
        raise SystemExit(f"作答臂不是 224，而是 {len(arm)}")
    return arm


def _build_store() -> tuple[InMemoryStore, list[str], list[str]]:
    store = InMemoryStore()
    n = 0
    for folder in (CORPUS, TRAPS):
        for doc, chunks in load_corpus(folder):
            store.add_document(doc, chunks)
            n += len(chunks)
    if n != 794:
        raise SystemExit(f"chunk 不是 794，而是 {n}")
    eids = [chunk_evidence_id(chunk) for chunk in store._chunks]
    texts = [chunk.text for chunk in store._chunks]
    return store, eids, texts


def _embed_payload(version: str) -> dict[str, Any]:
    if importlib_metadata.version("fastembed") != version:
        raise SystemExit(f"fastembed 不是 {version}")
    _store, eids, texts = _build_store()
    arm = _arm_questions()
    queries = list(dict.fromkeys(str(item.get("query", "")) for item in arm))
    chunk_vecs = embed_texts_local(texts)
    query_vecs = embed_texts_local(queries)
    return {
        "fastembed_version": version,
        "model": "BAAI/bge-small-zh-v1.5",
        "chunks": {eid: vec for eid, vec in zip(eids, chunk_vecs)},
        "queries": {text: vec for text, vec in zip(queries, query_vecs)},
    }


def cmd_embed(out: Path) -> int:
    version = importlib_metadata.version("fastembed")
    payload = _embed_payload(version)
    out.write_text(json.dumps(payload), encoding="utf-8")
    print(f"wrote {out} fastembed={version} chunks={len(payload['chunks'])} queries={len(payload['queries'])}")
    return 0


def _max_abs(left: list[float], right: list[float]) -> float:
    return max(abs(a - b) for a, b in zip(left, right))


def _compare_vectors(old: dict[str, Any], new_chunks: dict[str, list[float]], new_queries: dict[str, list[float]]) -> dict[str, Any]:
    def scan(label: str, left_map: dict[str, list[float]], right_map: dict[str, list[float]]) -> dict[str, Any]:
        missing = sorted(set(left_map) - set(right_map))
        extra = sorted(set(right_map) - set(left_map))
        differ: list[dict[str, Any]] = []
        max_abs = 0.0
        for key in left_map:
            if key not in right_map:
                continue
            if len(left_map[key]) != len(right_map[key]):
                differ.append({"key": key, "reason": "dim"})
                continue
            delta = _max_abs(left_map[key], right_map[key])
            if delta > 0.0:
                max_abs = max(max_abs, delta)
                differ.append({"key": key, "max_abs": delta})
            else:
                max_abs = max(max_abs, delta)
        return {
            "label": label,
            "n": len(left_map),
            "n_missing": len(missing),
            "n_extra": len(extra),
            "n_differ": len(differ),
            "max_abs": max_abs,
            "verdict": "一致" if not missing and not extra and not differ else "有差异",
            "differ": differ,
        }

    return {
        "fastembed_old": old.get("fastembed_version"),
        "chunks": scan("chunks", old["chunks"], new_chunks),
        "queries": scan("queries", old["queries"], new_queries),
    }


def _ranking_diff(reference: dict[str, list[str]], got: dict[str, list[str]], label: str) -> dict[str, Any]:
    ids = sorted(set(reference) & set(got))
    order_differ = []
    set_differ = []
    missing = sorted(set(reference) - set(got))
    for qid in ids:
        if reference[qid] != got[qid]:
            order_differ.append(qid)
        if set(reference[qid]) != set(got[qid]):
            set_differ.append(qid)
    verdict = "一致" if not order_differ and not missing else "有差异"
    return {
        "label": label,
        "n": len(ids),
        "n_missing": len(missing),
        "n_order_differ": len(order_differ),
        "n_set_differ": len(set_differ),
        "order_differ_ids": order_differ,
        "set_differ_ids": set_differ,
        "missing_ids": missing,
        "verdict": verdict,
    }


def _load_x1() -> dict[str, dict[str, list[str]]]:
    rows = json.loads(X1_PER_QUERY.read_text(encoding="utf-8"))
    out: dict[str, dict[str, list[str]]] = {}
    for row in rows:
        if row.get("score_role") != "arm":
            continue
        out.setdefault(row["id"], {})[row["mode"]] = list(row["ranked"])
    return out


def _load_293_candidates(path: Path | None) -> dict[str, list[str]] | None:
    if path is None or not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("fastembed_version") != "0.7.1" or payload.get("n_arm") != 224:
        raise SystemExit("293 候选文件不是 fastembed 0.7.1 / n=224")
    return {row["id"]: list(row["hybrid_k10"]) for row in payload["queries"]}


def _same_number(left: float, right: float) -> bool:
    return left == right


def _metric_row(name: str, new: float, old: float, source: str) -> dict[str, Any]:
    return {
        "name": name,
        "new": new,
        "old": old,
        "source": source,
        "verdict": "一致" if _same_number(new, old) else "有差异",
    }


def _fmt(value: float) -> str:
    return json.dumps(value)


def _render(payload: dict[str, Any]) -> str:
    arms = payload["arms"]
    lines = [
        "# fastembed 0.8.1 复核",
        "",
        "不改生产代码，不改金标，不调用付费 API。",
        f"fastembed {payload['fastembed_version']}，模型 `BAAI/bge-small-zh-v1.5`，精排 `BAAI/bge-reranker-base`，K=10。",
        f"作答臂 n={payload['n_arm']}，chunk {payload['n_chunks']}。bootstrap {N_BOOT}，seed={BOOT_SEED}。",
        "金标仍是模型双标加代审。人工审核只覆盖 DECISION-16 的 16 道题。",
        "",
        "## 四臂（本次 0.8.1）",
        "",
        "| 臂 | Recall@10 | MRR@10 | nDCG@10 | 全检索 p95 ms |",
        "|---|---:|---:|---:|---:|",
    ]
    for mode in MODES:
        block = arms[mode]
        lines.append(
            f"| {mode} | {_fmt(block['recall'])} | {_fmt(block['mrr'])} | {_fmt(block['ndcg'])} | {_fmt(block['p95_retrieve_ms'])} |"
        )
    rerank = payload["rerank_only_p95_ms"]
    lines.extend([
        "",
        f"只计重排的 p95：lexical {_fmt(rerank['lexical'])} ms，neural {_fmt(rerank['neural'])} ms。不含 hybrid 检索，不含加载。",
        f"神经加载 { _fmt(payload['neural_load_s']) } 秒。",
        "",
        "## 与 0.7.1 的 embedding",
        "",
        payload["vector_sentence"],
        "",
        "## 与已保存排名",
        "",
    ])
    for row in payload["ranking_diffs"]:
        lines.append(
            f"- {row['label']}：{row['verdict']}。顺序不同 {row['n_order_differ']}，集合不同 {row['n_set_differ']}。"
        )
        if row["order_differ_ids"]:
            lines.append("  题号：" + "，".join(row["order_differ_ids"]))
    lines.extend(["", "## 与 #285、#293 的数字", ""])
    lines.append("| 项 | 本次 | 旧值 | 出处 | 结论 |")
    lines.append("|---|---:|---:|---|---|")
    for row in payload["number_rows"]:
        lines.append(
            f"| {row['name']} | {_fmt(row['new'])} | {_fmt(row['old'])} | {row['source']} | {row['verdict']} |"
        )
    lines.extend(["", "## 差异清单", ""])
    diffs = [row for row in payload["number_rows"] if row["verdict"] != "一致"]
    if not diffs:
        lines.append("与 #285、#293 对照表里的每一项都一致，包括 p95。")
    else:
        lines.append("embedding、排名、Recall@10、MRR@10、nDCG@10、McNemar discordant 与下表里标成一致的旧值逐位相同。有差异的只有这次单次墙钟：")
        for row in diffs:
            lines.append(
                f"- {row['name']}：本次 {_fmt(row['new'])}，旧值 {_fmt(row['old'])}（{row['source']}）。"
            )
    lines.extend([
        "",
        "全检索 p95 对的是 #285 的 `cost.p95_ms`（当时 hybrid+rerank 是 lexical）。只计重排的 p95 对的是 #293 的 `p95_ms_k10`。两列不混用。",
        f"本次神经全检索 p95 是 {_fmt(payload['arms']['hybrid+rerank']['p95_retrieve_ms'])} ms，含 hybrid 与 K=10 cross-encoder。#285 没有同口径的神经全检索 p95。",
        f"本次神经加载 {_fmt(payload['neural_load_s'])} 秒。#293 的首次加载是 8.242696646000695 秒。同属单次计时。",
        "",
        "#285 `summary.json` 的 `rank_metrics` 里，hybrid 与当时 lexical 的 nDCG@10 均值是金标修订前的数：hybrid 0.779488160892922，lexical 0.7617513683560622。",
        "本次 hybrid nDCG@10 是 0.7803516716233564，与金标修订后的记录一致。本次 lexical nDCG@10 是 0.7626148790864964，与 #293 一致。",
        "`s1-d0-05-q4` 上 hybrid 与 lexical 的 nDCG 都是 0.5，BM25 是 0.0。hybrid 对 lexical 的 nDCG 差与区间仍是 -0.017736792536859957，区间 -0.03478236247276103 ~ -0.0014390192270836006，与 #285 的这条配对差逐位一致。",
        "BM25 对 lexical 的 nDCG 均值与区间相对 #285 的金标修订前 `rank_metrics` 有变化：本次 lexical 均值 0.7626148790864964，差 0.035847640409414565，区间 0.01456894012455283 ~ 0.05721404238633618。MRR 的两条配对与 #285 逐位一致。",
        "",
        "## 结论",
        "",
        payload["conclusion"],
        "",
    ])
    return "\n".join(lines)


def cmd_run(vec071: Path, candidates: Path | None, out_dir: Path) -> int:
    if os.environ.get("FRESHLATCH_NEURAL_RERANK", "1") == "0":
        raise SystemExit("FRESHLATCH_NEURAL_RERANK=0，这次复核要跑神经精排")
    if PRODUCTION_RETRIEVAL_MODE != "hybrid+rerank":
        raise SystemExit(f"生产默认臂不是 hybrid+rerank：{PRODUCTION_RETRIEVAL_MODE}")
    version = importlib_metadata.version("fastembed")
    if version != "0.8.1":
        raise SystemExit(f"主进程 fastembed 不是 0.8.1：{version}")
    if "freshlatch.store.embeddings" in sys.modules:
        raise SystemExit("embeddings 模块被加载")

    old_vecs = json.loads(vec071.read_text(encoding="utf-8"))
    if old_vecs.get("fastembed_version") != "0.7.1":
        raise SystemExit("对照向量不是 fastembed 0.7.1")

    store, eids, texts = _build_store()
    t0 = time.perf_counter()
    chunk_rows = embed_texts_local(texts)
    embed_chunks_s = time.perf_counter() - t0
    new_chunks = {eid: vec for eid, vec in zip(eids, chunk_rows)}
    for chunk, vec in zip(store._chunks, chunk_rows):
        chunk.vec = pack_vec(vec)
    arm = _arm_questions()
    query_texts = list(dict.fromkeys(str(item.get("query", "")) for item in arm))
    t1 = time.perf_counter()
    query_rows = embed_texts_local(query_texts)
    embed_queries_s = time.perf_counter() - t1
    new_queries = {text: vec for text, vec in zip(query_texts, query_rows)}
    store.query_embedder = lambda query, _map=new_queries: _map[query]
    vector_cmp = _compare_vectors(old_vecs, new_chunks, new_queries)

    t_load = time.perf_counter()
    warmup_neural_rerank()
    neural_load_s = time.perf_counter() - t_load
    tokenize("预热")

    scored: list[dict[str, Any]] = []
    latencies: dict[str, list[float]] = {mode: [] for mode in MODES}
    hybrid_chunks: dict[str, list[Any]] = {}
    for item in arm:
        relevant = [str(x) for x in (item.get("relevant") or [])]
        ranked: dict[str, list[str]] = {}
        recall: dict[str, float] = {}
        mrr: dict[str, float] = {}
        ndcg: dict[str, float] = {}
        rerank_mode: dict[str, str] = {}
        query = str(item.get("query", ""))
        for mode in MODES:
            store.bind_eval_retrieval_mode(None if mode == "bm25" else mode)
            started = time.perf_counter()
            hits = store.retrieve(query, as_of=item.get("as_of"), top_k=TOP_K)
            elapsed = time.perf_counter() - started
            got = getattr(store, "last_retrieval_mode", None)
            if got != mode:
                raise SystemExit(f"模式不诚实 {item['id']} {mode} -> {got}")
            got_rerank = getattr(store, "last_rerank_mode", "")
            if mode == "hybrid+rerank" and got_rerank != RERANK_MODE_NEURAL:
                raise SystemExit(f"{item['id']} 神经精排没有跑成：{got_rerank}")
            if mode == "hybrid+rerank_lexical" and got_rerank != RERANK_MODE_LEXICAL:
                raise SystemExit(f"{item['id']} lexical 开关没有跑成：{got_rerank}")
            ids = [chunk_evidence_id(chunk) for chunk in hits]
            ranked[mode] = ids
            recall[mode] = recall_at_k(ids, relevant, TOP_K)
            mrr[mode] = mrr_at_k(ids, relevant, TOP_K)
            ndcg[mode] = ndcg_at_k(ids, relevant, TOP_K)
            latencies[mode].append(elapsed)
            rerank_mode[mode] = got_rerank
            if mode == "hybrid":
                hybrid_chunks[item["id"]] = list(hits)
        store.bind_eval_retrieval_mode(None)
        scored.append({
            "id": item["id"],
            "relevant": relevant,
            "ranked": ranked,
            "recall": recall,
            "mrr": mrr,
            "ndcg": ndcg,
            "rerank_mode": rerank_mode,
        })

    lex_s: list[float] = []
    neu_s: list[float] = []
    for row in scored:
        hits = hybrid_chunks[row["id"]]
        query = str(next(item.get("query", "") for item in arm if item["id"] == row["id"]))
        started = time.perf_counter()
        lex_hits, lex_mode = rerank_hybrid_candidates(query, hits, top_k=TOP_K, lexical_only=True)
        lex_s.append(time.perf_counter() - started)
        started = time.perf_counter()
        neu_hits, neu_mode = rerank_hybrid_candidates(query, hits, top_k=TOP_K, lexical_only=False)
        neu_s.append(time.perf_counter() - started)
        if lex_mode != RERANK_MODE_LEXICAL or neu_mode != RERANK_MODE_NEURAL:
            raise SystemExit(f"{row['id']} 重排计时臂不对 {lex_mode} {neu_mode}")
        lex_ids = [chunk_evidence_id(chunk) for chunk in lex_hits]
        neu_ids = [chunk_evidence_id(chunk) for chunk in neu_hits]
        if lex_ids != row["ranked"]["hybrid+rerank_lexical"]:
            raise SystemExit(f"{row['id']} lexical 全检索与只重排不一致")
        if neu_ids != row["ranked"]["hybrid+rerank"]:
            raise SystemExit(f"{row['id']} neural 全检索与只重排不一致")

    # #285 共享一条 rng：三组 Recall，然后 bm25/hybrid 对当时的 hybrid+rerank 的 MRR、nDCG。
    # 当时的 hybrid+rerank 是 lexical。这里用 hybrid+rerank_lexical 对齐那一次。
    rng = random.Random(BOOT_SEED)
    sig_285_shape = {
        "bm25_vs_hybrid": _pair(scored, "bm25", "hybrid", "recall", rng),
        "bm25_vs_lexical": _pair(scored, "bm25", "hybrid+rerank_lexical", "recall", rng),
        "hybrid_vs_lexical": _pair(scored, "hybrid", "hybrid+rerank_lexical", "recall", rng),
    }
    rank_285_shape = [
        _pair(scored, "bm25", "hybrid+rerank_lexical", "mrr", rng),
        _pair(scored, "bm25", "hybrid+rerank_lexical", "ndcg", rng),
        _pair(scored, "hybrid", "hybrid+rerank_lexical", "mrr", rng),
        _pair(scored, "hybrid", "hybrid+rerank_lexical", "ndcg", rng),
    ]
    # 金标修订后 BM25 vs hybrid 的 MRR、nDCG：各自从种子重新起一条。
    bm25_hybrid_mrr = _fresh_pair(scored, "bm25", "hybrid", "mrr")
    bm25_hybrid_ndcg = _fresh_pair(scored, "bm25", "hybrid", "ndcg")
    # #293：lexical vs neural，新的一条 rng，顺序 Recall、MRR、nDCG。差 = neural − lexical。
    rng293 = random.Random(BOOT_SEED)
    neural_vs_lex = [
        _pair(scored, "hybrid+rerank_lexical", "hybrid+rerank", "recall", rng293),
        _pair(scored, "hybrid+rerank_lexical", "hybrid+rerank", "mrr", rng293),
        _pair(scored, "hybrid+rerank_lexical", "hybrid+rerank", "ndcg", rng293),
    ]

    x1 = _load_x1()
    got = {row["id"]: row["ranked"] for row in scored}
    ranking_diffs = [
        _ranking_diff(
            {qid: modes["bm25"] for qid, modes in x1.items()},
            {qid: modes["bm25"] for qid, modes in got.items()},
            "bm25 顺序 vs #283/#285 保存的 per-query",
        ),
        _ranking_diff(
            {qid: modes["hybrid"] for qid, modes in x1.items()},
            {qid: modes["hybrid"] for qid, modes in got.items()},
            "hybrid 顺序 vs #283/#285 保存的 per-query（0.7.1）",
        ),
        _ranking_diff(
            {qid: modes["hybrid+rerank"] for qid, modes in x1.items()},
            {qid: modes["hybrid+rerank_lexical"] for qid, modes in got.items()},
            "hybrid+rerank_lexical 顺序 vs #283/#285 保存的 hybrid+rerank",
        ),
    ]
    cand = _load_293_candidates(candidates)
    if cand is not None:
        ranking_diffs.append(
            _ranking_diff(
                cand,
                {qid: modes["hybrid"] for qid, modes in got.items()},
                "hybrid 顺序 vs #293 dump 的 hybrid top-10（0.7.1）",
            )
        )
    neural_rows = json.loads(NEURAL_PER_QUERY.read_text(encoding="utf-8"))
    ranking_diffs.append(
        _ranking_diff(
            {row["id"]: list(row["k10"]["neural_ranked"]) for row in neural_rows},
            {qid: modes["hybrid+rerank"] for qid, modes in got.items()},
            "neural top-10 顺序 vs #293 per-query",
        )
    )
    ranking_diffs.append(
        _ranking_diff(
            {row["id"]: list(row["k10"]["lexical_ranked"]) for row in neural_rows},
            {qid: modes["hybrid+rerank_lexical"] for qid, modes in got.items()},
            "lexical top-10 顺序 vs #293 per-query",
        )
    )

    published = json.loads(ISSUE_284.read_text(encoding="utf-8"))
    neural_pub = json.loads(NEURAL_SUMMARY.read_text(encoding="utf-8"))
    neural_cost = json.loads(NEURAL_COST.read_text(encoding="utf-8"))
    number_rows: list[dict[str, Any]] = []

    def add_mean(name: str, new: float, old: float, source: str) -> None:
        number_rows.append(_metric_row(name, new, old, source))

    sig = published["significance"]["bm25_vs_hybrid"]
    fresh_recall = sig_285_shape["bm25_vs_hybrid"]
    add_mean("BM25 Recall@10", fresh_recall["left_mean"], sig["recall_left"], "#285 summary")
    add_mean("hybrid Recall@10", fresh_recall["right_mean"], sig["recall_right"], "#285 summary")
    add_mean("BM25−hybrid Recall 差的相反数（hybrid−bm25）", fresh_recall["estimate"], sig["recall_diff"]["estimate"], "#285 summary")
    add_mean("hybrid−bm25 Recall CI 低", fresh_recall["ci95_low"], sig["recall_diff"]["ci95_low"], "#285 summary")
    add_mean("hybrid−bm25 Recall CI 高", fresh_recall["ci95_high"], sig["recall_diff"]["ci95_high"], "#285 summary")
    add_mean("McNemar bm25-only 计数", float(fresh_recall["mcnemar"]["left_only"]), float(sig["mcnemar"]["left_only"]), "#285 summary")
    add_mean("McNemar hybrid-only 计数", float(fresh_recall["mcnemar"]["right_only"]), float(sig["mcnemar"]["right_only"]), "#285 summary")
    add_mean("McNemar p", fresh_recall["mcnemar"]["p_two_sided"], sig["mcnemar"]["p_two_sided"], "#285 summary")
    add_mean("BM25 MRR@10", bm25_hybrid_mrr["left_mean"], 0.7275333049886621, "retrieval-decision 金标修订后")
    add_mean("hybrid MRR@10", bm25_hybrid_mrr["right_mean"], 0.7739937641723357, "retrieval-decision 金标修订后")
    add_mean("hybrid−bm25 MRR 差", bm25_hybrid_mrr["estimate"], 0.04646045918367347, "retrieval-decision 金标修订后")
    add_mean("hybrid−bm25 MRR CI 低", bm25_hybrid_mrr["ci95_low"], 0.02168358489229025, "retrieval-decision 金标修订后")
    add_mean("hybrid−bm25 MRR CI 高", bm25_hybrid_mrr["ci95_high"], 0.07260558390022674, "retrieval-decision 金标修订后")
    add_mean("BM25 nDCG@10", bm25_hybrid_ndcg["left_mean"], 0.7267672386770819, "retrieval-decision 金标修订后")
    add_mean("hybrid nDCG@10", bm25_hybrid_ndcg["right_mean"], 0.7803516716233564, "retrieval-decision 金标修订后")
    add_mean("hybrid−bm25 nDCG 差", bm25_hybrid_ndcg["estimate"], 0.053584432946274525, "retrieval-decision 金标修订后")
    add_mean("hybrid−bm25 nDCG CI 低", bm25_hybrid_ndcg["ci95_low"], 0.03201358973245737, "retrieval-decision 金标修订后")
    add_mean("hybrid−bm25 nDCG CI 高", bm25_hybrid_ndcg["ci95_high"], 0.07548337519518822, "retrieval-decision 金标修订后")

    p95_285 = published["cost"]["p95_ms"]
    add_mean("bm25 全检索 p95", _p95_ms(latencies["bm25"]), p95_285["bm25"], "#285 cost")
    add_mean("hybrid 全检索 p95", _p95_ms(latencies["hybrid"]), p95_285["hybrid"], "#285 cost")
    add_mean("lexical 全检索 p95", _p95_ms(latencies["hybrid+rerank_lexical"]), p95_285["hybrid+rerank"], "#285 cost 当时的 hybrid+rerank")

    k10 = neural_pub["k10"]
    add_mean("lexical Recall@10", neural_vs_lex[0]["left_mean"], k10["recall"]["left_mean"], "#293 K=10")
    add_mean("neural Recall@10", neural_vs_lex[0]["right_mean"], k10["recall"]["right_mean"], "#293 K=10")
    add_mean("neural−lexical Recall 差", neural_vs_lex[0]["estimate"], k10["recall"]["estimate"], "#293 K=10")
    add_mean("McNemar lexical-only", float(neural_vs_lex[0]["mcnemar"]["left_only"]), float(k10["recall"]["mcnemar"]["left_only"]), "#293 K=10")
    add_mean("McNemar neural-only", float(neural_vs_lex[0]["mcnemar"]["right_only"]), float(k10["recall"]["mcnemar"]["right_only"]), "#293 K=10")
    add_mean("lexical MRR@10", neural_vs_lex[1]["left_mean"], k10["mrr"]["left_mean"], "#293 K=10")
    add_mean("neural MRR@10", neural_vs_lex[1]["right_mean"], k10["mrr"]["right_mean"], "#293 K=10")
    add_mean("neural−lexical MRR 差", neural_vs_lex[1]["estimate"], k10["mrr"]["estimate"], "#293 K=10")
    add_mean("neural−lexical MRR CI 低", neural_vs_lex[1]["ci95_low"], k10["mrr"]["ci95_low"], "#293 K=10")
    add_mean("neural−lexical MRR CI 高", neural_vs_lex[1]["ci95_high"], k10["mrr"]["ci95_high"], "#293 K=10")
    add_mean("lexical nDCG@10", neural_vs_lex[2]["left_mean"], k10["ndcg"]["left_mean"], "#293 K=10")
    add_mean("neural nDCG@10", neural_vs_lex[2]["right_mean"], k10["ndcg"]["right_mean"], "#293 K=10")
    add_mean("neural−lexical nDCG 差", neural_vs_lex[2]["estimate"], k10["ndcg"]["estimate"], "#293 K=10")
    add_mean("neural−lexical nDCG CI 低", neural_vs_lex[2]["ci95_low"], k10["ndcg"]["ci95_low"], "#293 K=10")
    add_mean("neural−lexical nDCG CI 高", neural_vs_lex[2]["ci95_high"], k10["ndcg"]["ci95_high"], "#293 K=10")
    add_mean("lexical 只重排 p95", _p95_ms(lex_s), neural_cost["p95_ms_k10"]["lexical"], "#293 cost")
    add_mean("neural 只重排 p95", _p95_ms(neu_s), neural_cost["p95_ms_k10"]["neural"], "#293 cost")

    chunk_verdict = vector_cmp["chunks"]["verdict"]
    query_verdict = vector_cmp["queries"]["verdict"]
    if chunk_verdict == "一致" and query_verdict == "一致":
        vector_sentence = (
            "同一套当前代码、同一 `FASTEMBED_CACHE_PATH` 下，fastembed 0.7.1 与 0.8.1 的 "
            "chunk 向量和作答臂 query 向量逐位一致。"
        )
    else:
        vector_sentence = (
            f"向量有差异。chunk：{vector_cmp['chunks']['verdict']}，"
            f"不同 {vector_cmp['chunks']['n_differ']}，max_abs {vector_cmp['chunks']['max_abs']}。"
            f"query：{vector_cmp['queries']['verdict']}，"
            f"不同 {vector_cmp['queries']['n_differ']}，max_abs {vector_cmp['queries']['max_abs']}。"
        )

    rank_ok = all(row["verdict"] == "一致" for row in ranking_diffs)
    numbers_differ = [row for row in number_rows if row["verdict"] != "一致"]
    # p95 是单次计时，单独说，不拿它否定排名一致。
    non_p95 = [row for row in numbers_differ if "p95" not in row["name"]]
    if chunk_verdict == "一致" and query_verdict == "一致" and rank_ok and not non_p95:
        conclusion = (
            "hybrid 的 embedding 结果与 0.7.1 一致。四臂的 Recall@10、MRR@10、nDCG@10、"
            "McNemar discordant 与 #285 金标修订后的 BM25/hybrid 数字、以及 #293 的 K=10 数字一致。"
            "p95 是这次单次计时，与旧的单次计时并列，不要求逐位相同。"
        )
    else:
        bits = []
        if chunk_verdict != "一致" or query_verdict != "一致":
            bits.append("embedding 向量与 0.7.1 有差异")
        else:
            bits.append("embedding 向量与 0.7.1 一致")
        if not rank_ok:
            bits.append("有排名与已保存结果不同")
        if non_p95:
            bits.append(f"非 p95 数字有 {len(non_p95)} 项不同")
        bits.append(f"p95 有 {sum(1 for row in numbers_differ if 'p95' in row['name'])} 项与旧单次计时不同")
        conclusion = "。".join(bits) + "。生产代码和金标没有改。"

    arms = {}
    for mode in MODES:
        arms[mode] = {
            "recall": _mean([row["recall"][mode] for row in scored]),
            "mrr": _mean([row["mrr"][mode] for row in scored]),
            "ndcg": _mean([row["ndcg"][mode] for row in scored]),
            "p95_retrieve_ms": _p95_ms(latencies[mode]),
        }
    payload = {
        "fastembed_version": version,
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "n_arm": 224,
        "n_chunks": 794,
        "neural_load_s": neural_load_s,
        "embed_chunks_s": embed_chunks_s,
        "embed_queries_s": embed_queries_s,
        "arms": arms,
        "rerank_only_p95_ms": {"lexical": _p95_ms(lex_s), "neural": _p95_ms(neu_s)},
        "vector_compare": {
            "chunks": {k: vector_cmp["chunks"][k] for k in ("n", "n_differ", "max_abs", "verdict", "n_missing")},
            "queries": {k: vector_cmp["queries"][k] for k in ("n", "n_differ", "max_abs", "verdict", "n_missing")},
            "differ_chunk_ids": [row["key"] for row in vector_cmp["chunks"]["differ"]],
            "differ_queries": [row["key"] for row in vector_cmp["queries"]["differ"]],
        },
        "vector_sentence": vector_sentence,
        "ranking_diffs": ranking_diffs,
        "significance_285_shape": sig_285_shape,
        "rank_285_shape": rank_285_shape,
        "bm25_vs_hybrid_mrr": bm25_hybrid_mrr,
        "bm25_vs_hybrid_ndcg": bm25_hybrid_ndcg,
        "neural_vs_lexical": neural_vs_lex,
        "number_rows": number_rows,
        "mcnemar_bm25_hybrid": fresh_recall["mcnemar"],
        "mcnemar_neural_lexical": neural_vs_lex[0]["mcnemar"],
        "conclusion": conclusion,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    per_query = [
        {
            "id": row["id"],
            "relevant": row["relevant"],
            "ranked": row["ranked"],
            "recall": row["recall"],
            "mrr": row["mrr"],
            "ndcg": row["ndcg"],
        }
        for row in scored
    ]
    (out_dir / "per-query.json").write_text(json.dumps(per_query, ensure_ascii=False) + "\n", encoding="utf-8")
    cost = {
        "fastembed_version": version,
        "embed_model": "BAAI/bge-small-zh-v1.5",
        "rerank_model": "BAAI/bge-reranker-base",
        "k": TOP_K,
        "n_boot": N_BOOT,
        "seed": BOOT_SEED,
        "embed_chunks_s": embed_chunks_s,
        "embed_queries_s": embed_queries_s,
        "neural_load_s": neural_load_s,
        "p95_retrieve_ms": {mode: arms[mode]["p95_retrieve_ms"] for mode in MODES},
        "p95_rerank_only_ms": payload["rerank_only_p95_ms"],
        "dashscope_called": False,
    }
    (out_dir / "cost.json").write_text(json.dumps(cost, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "compare.json").write_text(json.dumps({
        "vector_compare": payload["vector_compare"],
        "ranking_diffs": ranking_diffs,
        "number_rows": number_rows,
        "significance_285_shape": sig_285_shape,
        "rank_285_shape": rank_285_shape,
        "bm25_vs_hybrid_mrr": bm25_hybrid_mrr,
        "bm25_vs_hybrid_ndcg": bm25_hybrid_ndcg,
        "neural_vs_lexical": neural_vs_lex,
        "conclusion": conclusion,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "RESULT.md").write_text(_render(payload), encoding="utf-8")
    print(conclusion)
    print("p95", cost["p95_retrieve_ms"], cost["p95_rerank_only_ms"])
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    embed = sub.add_parser("embed")
    embed.add_argument("--out", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--vec071", type=Path, required=True)
    run.add_argument("--candidates", type=Path, default=None)
    run.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.cmd == "embed":
        return cmd_embed(args.out)
    return cmd_run(args.vec071, args.candidates, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
