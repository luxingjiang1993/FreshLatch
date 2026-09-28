"""retrieve 子系统评测:主张金标派生 query、BM25 Recall/MRR、冒烟基线。

查询表在看指标之前由规则派生,不许按召回结果增删行。
n 为冒烟级,不声称统计显著,不报方差。BM25 确定性,无 temperature/seed。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from freshlatch.store.base import InMemoryStore, chunk_evidence_id
from freshlatch.store.checksum import aggregate_checksum, sha256_hex
from freshlatch.store.ingest import ingest_into, load_corpus
from freshlatch.store.query_transform import DIMENSION_ZH, transform_claim_query

K_LIST = (5, 10)


def _cid_key(claim_id: str) -> int:
    return int(str(claim_id).lstrip("c"))


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_retrieve_gold(
    docket: dict,
    distractor_docket: dict,
    gold: dict,
) -> dict:
    """从主张金标与卷宗派生 retrieve 金标。无 causal_chain 的主张不编相关集。"""
    claims = list(docket.get("claims") or []) + list(distractor_docket.get("claims") or [])
    claims.sort(key=lambda c: _cid_key(c["claim_id"]))
    chains = gold.get("causal_chain") or {}
    rows: list[dict] = []
    for claim in claims:
        cid = claim["claim_id"]
        chain = chains.get(cid)
        if not chain:
            continue
        statement = claim["statement"]
        dimension = claim.get("dimension")
        relevant_t1 = [f"{chain['t1_doc']}#{chain['anchor']}@T1"]
        relevant_t0 = []
        for eid in claim.get("t0_evidence_ids") or []:
            relevant_t0.append(eid if "@" in str(eid) else f"{eid}@T0")
        variants: list[tuple[str, str, str, list[str]]] = []
        q_id = transform_claim_query(statement)
        q_dim = transform_claim_query(statement, dimension=dimension)
        variants.append((f"{cid}-t1-identity", "T1", q_id, relevant_t1))
        if q_dim != q_id:
            variants.append((f"{cid}-t1-dimension", "T1", q_dim, relevant_t1))
        if dimension and dimension in DIMENSION_ZH:
            prefix = f"{DIMENSION_ZH[dimension]} {statement}"
            variants.append((f"{cid}-t1-prefix", "T1", prefix, relevant_t1))
        if relevant_t0:
            variants.append((f"{cid}-t0-identity", "T0", q_id, relevant_t0))
        seen: set[tuple[str, str]] = set()
        for qid, as_of, query, relevant in variants:
            key = (as_of, query)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "id": qid,
                "claim_id": cid,
                "query": query,
                "as_of": as_of,
                "relevant": relevant,
            })
    return {
        "version": "v0",
        "level": "smoke",
        "note": "由主张金标派生,规则先于指标。冒烟级,不声称统计显著。",
        "n": len(rows),
        "queries": rows,
    }


def recall_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    return 1.0 if any(eid in ranked[:k] for eid in relevant) else 0.0


def mrr_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    rel = set(relevant)
    for i, eid in enumerate(ranked[:k], start=1):
        if eid in rel:
            return 1.0 / i
    return 0.0


def must_stale_replay_failures(store, gold: dict, claims: list[dict]) -> list[tuple]:
    """must_stale:变换后 query × as_of=T1 × top_k=10 须命中 causal_chain 锚。"""
    by_id = {c["claim_id"]: c for c in claims}
    failures = []
    for cid in gold.get("must_stale") or []:
        chain = gold["causal_chain"][cid]
        claim = by_id[cid]
        query = transform_claim_query(claim["statement"], dimension=claim.get("dimension"))
        hits = store.retrieve(query, as_of="T1", top_k=10)
        got = {f"{c.doc_id}#{c.clause_id}" for c in hits}
        expected = f"{chain['t1_doc']}#{chain['anchor']}"
        if expected not in got:
            failures.append((cid, expected, sorted(got)))
    return failures


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def evaluate_retrieve(store, retrieve_gold: dict) -> dict:
    per_query = []
    recalls = {k: [] for k in K_LIST}
    mrrs = []
    for row in retrieve_gold["queries"]:
        hits = store.retrieve(row["query"], as_of=row["as_of"], top_k=10)
        ranked = [chunk_evidence_id(c) for c in hits]
        item = {
            "id": row["id"],
            "claim_id": row["claim_id"],
            "as_of": row["as_of"],
            "retrieval_mode": "bm25",
            "ranked": ranked,
        }
        for k in K_LIST:
            rec = recall_at_k(ranked, row["relevant"], k)
            item[f"recall@{k}"] = rec
            recalls[k].append(rec)
        mrr = mrr_at_k(ranked, row["relevant"], 10)
        item["mrr@10"] = mrr
        mrrs.append(mrr)
        per_query.append(item)
    return {
        "n": len(per_query),
        "retrieval_mode": "bm25",
        "recall": {str(k): _mean(recalls[k]) for k in K_LIST},
        "mrr@10": _mean(mrrs),
        "per_query": per_query,
    }


def render_baseline_report(payload: dict) -> str:
    rec = payload["metrics"]["recall"]
    replay = "pass" if payload["replay_pass"] else "fail"
    return "\n".join([
        "# BM25 retrieve 基线（冒烟）",
        "",
        f"- 日期: {payload['date']}",
        f"- 语料文件数: {payload['file_count']}",
        f"- chunk 数: {payload['chunk_count']}",
        f"- retrieval_mode: bm25",
        f"- 解码: 无 LLM,不适用 temperature/seed",
        f"- n: {payload['metrics']['n']}（冒烟级,不声称统计显著,不报方差）",
        f"- K∈{{5,10}}",
        f"- Recall@5: {rec['5']:.4f}",
        f"- Recall@10: {rec['10']:.4f}",
        f"- MRR@10: {payload['metrics']['mrr@10']:.4f}",
        f"- must_stale 回放: {replay}",
        f"- corpus+retrieve 金标聚合 checksum: `{payload['aggregate_checksum']}`",
        f"- corpus checksum: `{payload['corpus_checksum']}`",
        f"- retrieve 金标 checksum: `{payload['retrieve_gold_checksum']}`",
        "",
        "本页是 A0 冒烟基线,不是统计结论。查询表由主张金标规则派生,先于本页指标锁定。",
        "",
    ])


def run_retrieve_baseline(
    *,
    corpus: Path,
    gold_path: Path,
    docket_path: Path,
    distractor_path: Path,
    retrieve_gold_path: Path,
    out_dir: Path,
) -> dict:
    corpus = Path(corpus)
    gold = _load_json(gold_path)
    docket = _load_json(docket_path)
    distractor = _load_json(distractor_path)
    retrieve_gold = _load_json(retrieve_gold_path)
    built = build_retrieve_gold(docket, distractor, gold)
    if built["queries"] != retrieve_gold.get("queries"):
        raise ValueError("retrieve 金标与派生规则不一致,拒绝按结果改表")

    store = InMemoryStore()
    ingest_into(store, corpus)
    metrics = evaluate_retrieve(store, retrieve_gold)
    claims = list(docket["claims"]) + list(distractor["claims"])
    failures = must_stale_replay_failures(store, gold, claims)
    corpus_files = [p for p in corpus.rglob("*") if p.is_file()]
    data_root = corpus.parent
    payload = {
        "date": date.today().isoformat(),
        "file_count": len(corpus_files),
        "chunk_count": sum(len(cs) for _, cs in load_corpus(corpus)),
        "metrics": metrics,
        "replay_pass": not failures,
        "replay_failures": [
            {"claim_id": cid, "expected": exp} for cid, exp, _got in failures
        ],
        "corpus_checksum": aggregate_checksum(corpus_files, root=data_root),
        "retrieve_gold_checksum": sha256_hex(Path(retrieve_gold_path).read_bytes()),
        "aggregate_checksum": aggregate_checksum(
            [*corpus_files, Path(retrieve_gold_path)], root=data_root,
        ),
    }
    text = render_baseline_report(payload)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "retrieve-bm25-baseline.md"
    json_path = out_dir / "retrieve-bm25-baseline.json"
    md_path.write_text(text, encoding="utf-8")
    # 原始 JSON 不落每条 ranked 全文以外的秘密;指标与回放即可复跑。
    public = {k: v for k, v in payload.items() if k != "metrics"}
    public["metrics"] = {
        "n": metrics["n"],
        "retrieval_mode": metrics["retrieval_mode"],
        "recall": metrics["recall"],
        "mrr@10": metrics["mrr@10"],
    }
    json_path.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["report_path"] = str(md_path)
    return payload
