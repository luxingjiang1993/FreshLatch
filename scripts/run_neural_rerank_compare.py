"""神经 rerank 离线对照。不改 PRODUCTION_RETRIEVAL_MODE，不调用付费 API。

两步：
1. ``dump`` 用生产钉死的 fastembed 0.7.1 取出 hybrid 的 top-10 与 top-30。
2. ``score`` 在装了 requirements-eval-neural-rerank.txt 的解释器里加载 BAAI/bge-reranker-base。

口径见 docs/evidence/neural-rerank/PREREG.md。本脚本不改那一页。
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.pop("DASHSCOPE_API_KEY", None)

from freshlatch.eval.neural_rerank import (  # noqa: E402
    BOOT_SEED,
    KEEP_LEXICAL,
    P95_BUDGET_MS,
    TOP_K,
    order_by_scores,
    p95_ms,
    pair_metric,
    pair_recall,
    ranking_metrics,
    recommend_neural_rerank,
    same_id_set,
    unique_bytes_matching,
)
from freshlatch.store.base import (  # noqa: E402
    PRODUCTION_RETRIEVAL_MODE,
    Chunk,
    InMemoryStore,
    chunk_evidence_id,
)
from freshlatch.store.ingest import load_corpus  # noqa: E402
from freshlatch.store.pipeline import rerank_lexical, tokenize  # noqa: E402

GOLD_COMMIT = "50adc3251737c318815105b3562a823198b80dc3"
NEURAL_MODEL = "BAAI/bge-reranker-base"
QUESTIONS = ROOT / "data/exp/x1/questions.json"
CORPUS = ROOT / "data/exp/x1/corpus"
TRAPS = ROOT / "data/exp/x1/traps"
CANDIDATE_K = 30


def _chunks_for(eids: list[str], texts: dict[str, str]) -> list[Chunk]:
    out: list[Chunk] = []
    for eid in eids:
        doc_id, rest = eid.split("#", 1)
        clause_id, as_of = rest.rsplit("@", 1)
        out.append(
            Chunk(
                doc_id=doc_id,
                chunk_id=eid,
                clause_id=clause_id,
                title="",
                text=texts[eid],
                source_type="private",
                as_of=as_of,  # type: ignore[arg-type]
                doc_version="",
                checksum="",
                tokens=0,
            )
        )
    return out


def _lexical(query: str, eids: list[str], texts: dict[str, str]) -> list[str]:
    ranked = rerank_lexical(query, _chunks_for(eids, texts), top_k=TOP_K)
    return [chunk_evidence_id(chunk) for chunk in ranked]


def _arm_queries() -> list[dict[str, Any]]:
    raw = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    arm = [item for item in raw["queries"] if (item.get("score_role") or "arm") == "arm"]
    if len(arm) != 224:
        raise SystemExit(f"作答臂应为 224，得到 {len(arm)}")
    return arm


def _assert_production_mode() -> None:
    if PRODUCTION_RETRIEVAL_MODE != "hybrid+rerank":
        raise SystemExit(f"生产默认被改成 {PRODUCTION_RETRIEVAL_MODE}")
    if "freshlatch.store.embeddings" in sys.modules:
        raise SystemExit("embeddings 模块被加载")


def dump_candidates(path: Path) -> None:
    import importlib.metadata as importlib_metadata

    _assert_production_mode()
    version = importlib_metadata.version("fastembed")
    if version != "0.7.1":
        raise SystemExit(f"dump 必须用 fastembed 0.7.1，当前是 {version}")
    from freshlatch.store.local_embed import embed_texts_local
    from freshlatch.store.pipeline import pack_vec

    questions = _arm_queries()
    store = InMemoryStore()
    n = 0
    for folder in (CORPUS, TRAPS):
        for doc, chunks in load_corpus(folder):
            store.add_document(doc, chunks)
            n += len(chunks)
    texts = embed_texts_local([chunk.text for chunk in store._chunks])
    if len(texts) != n:
        raise SystemExit("向量条数与 chunk 数不一致")
    for chunk, vec in zip(store._chunks, texts):
        chunk.vec = pack_vec(vec)
    by_text: dict[str, list[float]] = {}
    unique = list(dict.fromkeys(str(item.get("query", "")) for item in questions))
    for query, vec in zip(unique, embed_texts_local(unique)):
        by_text[query] = vec
    store.query_embedder = lambda query: by_text[query]
    store.bind_eval_retrieval_mode("hybrid")

    rows = []
    for item in questions:
        query = str(item.get("query", ""))
        as_of = item.get("as_of")
        hits30 = store.retrieve(query, as_of=as_of, top_k=CANDIDATE_K)
        if store.last_retrieval_mode != "hybrid":
            raise SystemExit(f"{item['id']} hybrid 不诚实：{store.last_retrieval_mode}")
        eids = [chunk_evidence_id(chunk) for chunk in hits30]
        if len(eids) < TOP_K:
            raise SystemExit(f"{item['id']} hybrid 候选不足 {TOP_K}")
        text_map = {chunk_evidence_id(chunk): chunk.text for chunk in hits30}
        rows.append(
            {
                "id": item["id"],
                "query": query,
                "as_of": as_of,
                "qtype": item.get("qtype"),
                "relevant": [str(x) for x in (item.get("relevant") or [])],
                "hybrid_k10": eids[:TOP_K],
                "hybrid_k30": eids,
                "texts": text_map,
            }
        )
    payload = {
        "gold_commit": GOLD_COMMIT,
        "questions": "data/exp/x1/questions.json",
        "n_arm": len(rows),
        "n_chunks": n,
        "fastembed_version": version,
        "embed_model": "BAAI/bge-small-zh-v1.5",
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "queries": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path} n_arm={len(rows)} chunks={n}")


def _load_encoder(cache_dir: str | None) -> tuple[Any, float]:
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    started = time.perf_counter()
    encoder = TextCrossEncoder(
        model_name=NEURAL_MODEL,
        cache_dir=cache_dir,
        cuda=False,
    )
    list(encoder.rerank("预热", ["预热文档"]))
    return encoder, time.perf_counter() - started


def _weight_bytes(cache_dir: str | None) -> int | None:
    roots: list[object] = []
    if cache_dir:
        roots.append(cache_dir)
    roots.append("/tmp/fastembed_cache")
    return unique_bytes_matching(roots, "reranker")


def _score_pool(
    query: str,
    eids: list[str],
    texts: dict[str, str],
    neural_scores: Callable[[str, list[str]], list[float]],
) -> dict[str, Any]:
    started = time.perf_counter()
    lexical_ids = _lexical(query, eids, texts)
    lexical_s = time.perf_counter() - started
    docs = [texts[eid] for eid in eids]
    started = time.perf_counter()
    scores = neural_scores(query, docs)
    neural_s = time.perf_counter() - started
    neural_ids = order_by_scores(eids, scores)[:TOP_K]
    if not same_id_set(lexical_ids, eids[:TOP_K]) and len(eids) == TOP_K:
        raise SystemExit("lexical 重排丢掉了 K=10 的 id")
    if len(eids) == TOP_K and not same_id_set(neural_ids, eids):
        raise SystemExit("神经重排丢掉了 K=10 的 id")
    return {
        "lexical": lexical_ids,
        "neural": neural_ids,
        "lexical_s": lexical_s,
        "neural_s": neural_s,
    }


def _column(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    paired = []
    lex_s: list[float] = []
    neu_s: list[float] = []
    per_query = []
    for row in rows:
        block = row[key]
        relevant = row["relevant"]
        lexical = ranking_metrics(block["lexical"], relevant)
        neural = ranking_metrics(block["neural"], relevant)
        if key == "k10" and lexical["recall"] != neural["recall"]:
            raise SystemExit(f"{row['id']} K=10 Recall 不一致，运行作废")
        if key == "k10" and not same_id_set(block["lexical"], block["neural"]):
            raise SystemExit(f"{row['id']} K=10 id 集合不一致，运行作废")
        paired.append({"lexical": lexical, "neural": neural})
        lex_s.append(block["lexical_s"])
        neu_s.append(block["neural_s"])
        per_query.append(
            {
                "id": row["id"],
                "relevant": relevant,
                "lexical_ranked": block["lexical"],
                "neural_ranked": block["neural"],
                "lexical": lexical,
                "neural": neural,
                "lexical_s": block["lexical_s"],
                "neural_s": block["neural_s"],
            }
        )
    rng = random.Random(BOOT_SEED)
    recall = pair_recall(paired, rng)
    mrr = pair_metric(paired, key="mrr", rng=rng)
    ndcg = pair_metric(paired, key="ndcg", rng=rng)
    return {
        "n": len(rows),
        "recall": recall,
        "mrr": mrr,
        "ndcg": ndcg,
        "p95_ms": {"lexical": p95_ms(lex_s), "neural": p95_ms(neu_s)},
        "per_query": per_query,
    }


def _fmt(value: float) -> str:
    return json.dumps(value)


def _render_result(payload: dict[str, Any]) -> str:
    primary = payload["k10"]
    extra = payload["k30"]
    recall = primary["recall"]
    mcn = recall["mcnemar"]
    lines = [
        "# 神经 reranker 对照结果",
        "",
        "口径是 `PREREG.md`，本页不改那一页。不改 `PRODUCTION_RETRIEVAL_MODE`。",
        "",
        f"- 金标提交：`{GOLD_COMMIT}`",
        f"- 作答臂 n={primary['n']}",
        f"- 模型：`{NEURAL_MODEL}`，fastembed `TextCrossEncoder`，CPU，`cuda=False`",
        f"- 评测 fastembed：{payload['fastembed_version']}",
        f"- 取舍句：{payload['recommendation']}",
        "",
        "金标仍是模型双标加 Ronin 代理人（模型）代审。人工审核只覆盖 DECISION-16 的 16 道题。",
        "",
        "## K=10（决策列）",
        "",
        "两边重排 hybrid 的同一组前 10 条。Recall@10 相同是机制结果。",
        "",
        "| 指标 | lexical | neural | 差（neural − lexical） | 95% 区间 |",
        "|---|---:|---:|---:|---|",
        (
            f"| Recall@10 | {_fmt(recall['left_mean'])} | {_fmt(recall['right_mean'])} | "
            f"{_fmt(recall['estimate'])} | {_fmt(recall['ci95_low'])} ~ {_fmt(recall['ci95_high'])} |"
        ),
        (
            f"| MRR@10 | {_fmt(primary['mrr']['left_mean'])} | {_fmt(primary['mrr']['right_mean'])} | "
            f"{_fmt(primary['mrr']['estimate'])} | {_fmt(primary['mrr']['ci95_low'])} ~ {_fmt(primary['mrr']['ci95_high'])} |"
        ),
        (
            f"| nDCG@10 | {_fmt(primary['ndcg']['left_mean'])} | {_fmt(primary['ndcg']['right_mean'])} | "
            f"{_fmt(primary['ndcg']['estimate'])} | {_fmt(primary['ndcg']['ci95_low'])} ~ {_fmt(primary['ndcg']['ci95_high'])} |"
        ),
        "",
        (
            f"McNemar：只 lexical {mcn['left_only']}，只 neural {mcn['right_only']}，"
            f"都中 {mcn['both_hit']}，都未中 {mcn['neither']}，p={_fmt(mcn['p_two_sided'])}。"
        ),
        "",
        (
            f"p95：lexical {_fmt(primary['p95_ms']['lexical'])} ms，"
            f"neural {_fmt(primary['p95_ms']['neural'])} ms。门槛 {P95_BUDGET_MS:g} ms。"
            "只计重排，不含 hybrid 检索，不含加载。"
        ),
        "",
        "## K=30 取 top-10（加报，不改取舍句）",
        "",
        "| 指标 | lexical | neural | 差 | 95% 区间 |",
        "|---|---:|---:|---:|---|",
        (
            f"| Recall@10 | {_fmt(extra['recall']['left_mean'])} | {_fmt(extra['recall']['right_mean'])} | "
            f"{_fmt(extra['recall']['estimate'])} | {_fmt(extra['recall']['ci95_low'])} ~ {_fmt(extra['recall']['ci95_high'])} |"
        ),
        (
            f"| MRR@10 | {_fmt(extra['mrr']['left_mean'])} | {_fmt(extra['mrr']['right_mean'])} | "
            f"{_fmt(extra['mrr']['estimate'])} | {_fmt(extra['mrr']['ci95_low'])} ~ {_fmt(extra['mrr']['ci95_high'])} |"
        ),
        (
            f"| nDCG@10 | {_fmt(extra['ndcg']['left_mean'])} | {_fmt(extra['ndcg']['right_mean'])} | "
            f"{_fmt(extra['ndcg']['estimate'])} | {_fmt(extra['ndcg']['ci95_low'])} ~ {_fmt(extra['ndcg']['ci95_high'])} |"
        ),
        "",
        (
            f"McNemar：只 lexical {extra['recall']['mcnemar']['left_only']}，"
            f"只 neural {extra['recall']['mcnemar']['right_only']}，"
            f"都中 {extra['recall']['mcnemar']['both_hit']}，"
            f"都未中 {extra['recall']['mcnemar']['neither']}，"
            f"p={_fmt(extra['recall']['mcnemar']['p_two_sided'])}。"
        ),
        "",
        (
            f"p95：lexical {_fmt(extra['p95_ms']['lexical'])} ms，"
            f"neural {_fmt(extra['p95_ms']['neural'])} ms。"
        ),
        "",
        "## 代价",
        "",
        f"- 首次加载（构造加第一次 rerank）：{_fmt(payload['load_s'])} 秒",
        f"- 权重字节：{payload['weight_bytes']}（inode 去重；同一缓存根只走一次。HF 快照是符号链接，不能按路径加总）",
        "- 额外依赖：`requirements-eval-neural-rerank.txt`（fastembed==0.8.1）。生产 `requirements.txt` 仍是 fastembed==0.7.1，不含 bge-reranker。",
        f"- v2-m3：{payload['v2_m3']}",
        "",
        f"## 取舍",
        "",
        payload["recommendation_paragraph"],
        "",
    ]
    return "\n".join(lines)


def _paragraph(recommendation: str, primary: dict[str, Any]) -> str:
    ndcg = primary["ndcg"]
    mrr = primary["mrr"]
    p95 = primary["p95_ms"]["neural"]
    common = (
        f"K=10 上 nDCG@10 差 {_fmt(ndcg['estimate'])}，区间 {_fmt(ndcg['ci95_low'])} ~ {_fmt(ndcg['ci95_high'])}；"
        f"MRR@10 差 {_fmt(mrr['estimate'])}，区间 {_fmt(mrr['ci95_low'])} ~ {_fmt(mrr['ci95_high'])}；"
        f"神经 rerank p95 {_fmt(p95)} ms。"
    )
    if recommendation == KEEP_LEXICAL:
        return common + "按跑数前写死的四条，不建议换生产 rerank。保持 lexical rerank，等大语料复测。本页不改生产默认。"
    return common + "按跑数前写死的四条，建议另开切换票。本页不改生产默认。"


def score_candidates(candidates: Path, out_dir: Path, cache_dir: str | None) -> None:
    import importlib.metadata as importlib_metadata

    _assert_production_mode()
    payload_in = json.loads(candidates.read_text(encoding="utf-8"))
    if payload_in.get("n_arm") != 224:
        raise SystemExit("候选文件的 n_arm 不是 224")
    if payload_in.get("fastembed_version") != "0.7.1":
        raise SystemExit("候选不是用 fastembed 0.7.1 dump 的")
    encoder, load_s = _load_encoder(cache_dir)
    tokenize("预热")

    def neural_scores(query: str, docs: list[str]) -> list[float]:
        scores = [float(item) for item in encoder.rerank(query, docs)]
        if len(scores) != len(docs):
            raise SystemExit("rerank 分数条数与文档不一致")
        return scores

    scored_rows = []
    for row in payload_in["queries"]:
        texts = row["texts"]
        k10 = _score_pool(row["query"], row["hybrid_k10"], texts, neural_scores)
        k30 = _score_pool(row["query"], row["hybrid_k30"], texts, neural_scores)
        scored_rows.append(
            {
                "id": row["id"],
                "relevant": row["relevant"],
                "k10": k10,
                "k30": k30,
            }
        )
    k10_stats = _column(scored_rows, "k10")
    k30_stats = _column(scored_rows, "k30")
    recommendation = recommend_neural_rerank(
        ndcg_estimate=float(k10_stats["ndcg"]["estimate"]),
        ndcg_ci_low=float(k10_stats["ndcg"]["ci95_low"]),
        mrr_ci_low=float(k10_stats["mrr"]["ci95_low"]),
        p95_ms=float(k10_stats["p95_ms"]["neural"]),
    )
    supported = []
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        supported = [item.get("model") for item in TextCrossEncoder.list_supported_models()]
    except Exception as exc:  # noqa: BLE001
        supported = [f"list_failed:{type(exc).__name__}"]
    v2 = (
        "未跑。本环境的 fastembed TextCrossEncoder 支持列表没有 BAAI/bge-reranker-v2-m3。"
        "没有另装 sentence-transformers 或 torch。"
        if "BAAI/bge-reranker-v2-m3" not in supported
        else "支持列表里有该模型，但本轮决策臂仍只跑 bge-reranker-base。"
    )
    cost = {
        "model": NEURAL_MODEL,
        "engine": "fastembed TextCrossEncoder",
        "cuda": False,
        "fastembed_version_score": importlib_metadata.version("fastembed"),
        "fastembed_version_dump": payload_in["fastembed_version"],
        "load_s": load_s,
        "weight_bytes": _weight_bytes(cache_dir),
        "weight_bytes_method": "unique inode; path contains reranker; same cache root once",
        "p95_budget_ms": P95_BUDGET_MS,
        "p95_ms_k10": k10_stats["p95_ms"],
        "p95_ms_k30": k30_stats["p95_ms"],
        "extra_requirements": "requirements-eval-neural-rerank.txt",
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "gold_commit": GOLD_COMMIT,
        "n_arm": 224,
        "supported_cross_encoders": supported,
        "v2_m3": v2,
        "recommendation": recommendation,
    }
    result_payload = {
        "k10": {key: k10_stats[key] for key in ("n", "recall", "mrr", "ndcg", "p95_ms")},
        "k30": {key: k30_stats[key] for key in ("n", "recall", "mrr", "ndcg", "p95_ms")},
        "load_s": load_s,
        "weight_bytes": cost["weight_bytes"],
        "fastembed_version": cost["fastembed_version_score"],
        "v2_m3": v2,
        "recommendation": recommendation,
        "recommendation_paragraph": _paragraph(recommendation, k10_stats),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    per_query = []
    for row, src in zip(k10_stats["per_query"], k30_stats["per_query"]):
        per_query.append(
            {
                "id": row["id"],
                "relevant": row["relevant"],
                "k10": row,
                "k30": src,
            }
        )
    (out_dir / "per-query.json").write_text(
        json.dumps(per_query, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "cost.json").write_text(
        json.dumps(cost, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "RESULT.md").write_text(_render_result(result_payload), encoding="utf-8")
    (out_dir / "summary.json").write_text(
        json.dumps(result_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(recommendation)
    print("p95_k10", k10_stats["p95_ms"])
    print("ndcg", k10_stats["ndcg"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    dump = sub.add_parser("dump")
    dump.add_argument("--out", type=Path, required=True)
    score = sub.add_parser("score")
    score.add_argument("--candidates", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    score.add_argument("--cache-dir", default=os.environ.get("FASTEMBED_CACHE_PATH") or None)
    args = parser.parse_args(argv)
    if args.cmd == "dump":
        dump_candidates(args.out)
        return 0
    score_candidates(args.candidates, args.out, args.cache_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
