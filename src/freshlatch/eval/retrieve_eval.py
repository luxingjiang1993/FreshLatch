"""retrieve 子系统评测:主张金标派生 query、BM25 Recall/MRR、冒烟基线。

查询表在看指标之前由规则派生,不许按召回结果增删行。
n 为冒烟级,不声称统计显著,不报方差。BM25 确定性,无 temperature/seed。
L4-EV-01 的分臂表入口是 ``run_arm_metric_table``，只列 Recall@k 与 MRR。
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

from freshlatch.models import EMBED_MODEL
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


def ndcg_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    """二元 nDCG@k。命中记 1，理想排序把相关 id 放在最前。"""
    import math

    rel = set(relevant)
    if not rel:
        return 0.0
    dcg = 0.0
    for i, eid in enumerate(ranked[:k], start=1):
        if eid in rel:
            dcg += 1.0 / math.log2(i + 1)
    n_ideal = min(k, len(rel))
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, n_ideal + 1))
    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


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
            "claim_id": row.get("claim_id"),
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
    corpus_files = [
        p for p in corpus.rglob("*")
        if p.is_file() and "traps" not in p.relative_to(corpus).parts
    ]
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


def hard_gold_trap_adversarial_stats(retrieve_gold: dict) -> dict:
    """预登记核验：n 与 traps/对抗占比（category ∈ trap|adversarial）。"""
    rows = list(retrieve_gold.get("queries") or [])
    n = len(rows)
    trap_adv = 0
    for r in rows:
        cat = str(r.get("category") or "").lower()
        if cat in {"trap", "adversarial"}:
            trap_adv += 1
    ratio = (trap_adv / n) if n else 0.0
    return {"n": n, "trap_adversarial_count": trap_adv, "trap_adversarial_ratio": ratio}


def run_hard_gold_retrieve(
    *,
    corpus: Path,
    hard_gold_path: Path,
    trap_root: Path | None = None,
    out_dir: Path,
    dense_db: Path | None = None,
) -> dict:
    """Hard-Gold 骨架评测：分文件难金标 + BM25 报告 + 默认臂仍 bm25。

    不跑冒烟派生一致性校验（hard ≠ smoke）。增益门公式沿用 I0；本波不改臂。
    """
    from math import ceil

    from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

    hard_gold_path = Path(hard_gold_path)
    hard = _load_json(hard_gold_path)
    stats = hard_gold_trap_adversarial_stats(hard)
    if stats["n"] < 20:
        raise ValueError(f"Hard-Gold n={stats['n']} < 20（预登记）")
    need = ceil(0.3 * stats["n"])
    if stats["trap_adversarial_count"] < need:
        raise ValueError(
            f"Hard-Gold traps/对抗={stats['trap_adversarial_count']} < {need}（≥30% 预登记）"
        )

    store = InMemoryStore()
    ingest_into(store, Path(corpus))
    trap_root = Path(trap_root) if trap_root is not None else Path("data/traps")
    if trap_root.is_dir():
        for doc, chunks in load_trap_corpus(trap_root):
            store.add_document(doc, chunks)

    metrics = evaluate_retrieve(store, hard)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "retrieve-hard-gold-bm25.json"
    # 先落 BM25 JSON，供可选臂对比读 A0
    bootstrap = {
        "date": date.today().isoformat(),
        "level": "hard_gold_skeleton",
        "metrics": {
            "n": metrics["n"],
            "retrieval_mode": metrics["retrieval_mode"],
            "recall": metrics["recall"],
            "mrr@10": metrics["mrr@10"],
        },
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
    }
    json_path.write_text(json.dumps(bootstrap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    arm_note = "无 dense 索引：本波仅 BM25 轨；按 I0 纪律标需索引，不得因此改臂。"
    arm_payload = None
    dense_path = Path(dense_db) if dense_db is not None else Path("data/dense/index.sqlite")
    rerank_payload = None
    if dense_path.is_file():
        try:
            # hard 臂对比 / rerank 必须与 A0 同库 = corpus + traps（#259）
            arm_payload = run_arm_compare(
                corpus=Path(corpus),
                retrieve_gold_path=hard_gold_path,
                dense_db=dense_path,
                a0_baseline_path=json_path,
                out_dir=out_dir,
                trap_root=trap_root,
                report_name="retrieve-hard-gold-arm-compare.md",
                level_label="Hard-Gold hard 集",
            )
            arm_note = (
                f"臂对比已跑（见 retrieve-hard-gold-arm-compare.md；同库 corpus+traps）；"
                f"通过线={arm_payload.get('verdict')}。"
                "Hard-Gold 骨架 ≠ 授权换臂。"
            )
            rerank_payload = run_rerank_compare(
                corpus=Path(corpus),
                retrieve_gold_path=hard_gold_path,
                dense_db=dense_path,
                out_dir=out_dir,
                trap_root=trap_root,
                report_name="retrieve-hard-gold-rerank-compare.md",
                level_label="Hard-Gold hard 集",
            )
        except ValueError as exc:
            arm_note = f"臂对比跳过（{exc}）；不得因此改臂。"

    gain_verdict = (
        "关（Hard-Gold 骨架增益门仍单独记录；"
        "2026-10-07 真人拍板后生产默认是 hybrid+rerank；"
        "一键回退 set_retrieval_switch('bm25')；"
        f"PRODUCTION_RETRIEVAL_MODE={PRODUCTION_RETRIEVAL_MODE!r}）"
    )

    lines = [
        "# Hard-Gold 骨架 · BM25 / 增益门复跑",
        "",
        "> 层身份：冒烟 / 面试加固（I3）。本波 Hard-Gold = 骨架语料 + 增益门复跑。",
        "> 2026-10-07 真人拍板后生产默认是 `hybrid+rerank`；一键回退 `set_retrieval_switch(\"bm25\")`。",
        "> 不报方差；不作统计显著。与冒烟 `retrieve_gold.json` 分文件。",
        "",
        f"- 日期: {date.today().isoformat()}",
        f"- hard gold: `{hard_gold_path}`",
        f"- n: {stats['n']}（预登记 ≥20）",
        f"- traps/对抗: {stats['trap_adversarial_count']} "
        f"（{stats['trap_adversarial_ratio']:.1%}，预登记 ≥30%）",
        f"- BM25 Recall@10: {metrics['recall']['10']:.4f}",
        f"- BM25 MRR@10: {metrics['mrr@10']:.4f}",
        f"- 代码生产默认臂: `{PRODUCTION_RETRIEVAL_MODE}`（断言须为 hybrid+rerank）",
        f"- 增益门判决: {gain_verdict}",
        f"- 臂对比备注: {arm_note}",
        "",
        "增益门公式见 `docs/eval-retrieve.md` §3 / ADR-0026；本页不事后改门。",
        "",
    ]
    md_path = out_dir / "retrieve-hard-gold-bm25.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    public = {
        "date": date.today().isoformat(),
        "level": "hard_gold_skeleton",
        "hard_gold_path": str(hard_gold_path),
        "stats": stats,
        "metrics": {
            "n": metrics["n"],
            "retrieval_mode": metrics["retrieval_mode"],
            "recall": metrics["recall"],
            "mrr@10": metrics["mrr@10"],
        },
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "gain_verdict": gain_verdict,
        "arm_note": arm_note,
        "arm_compare": {
            "verdict": arm_payload.get("verdict") if arm_payload else None,
            "report_path": arm_payload.get("report_path") if arm_payload else None,
            "corpus_scope": "corpus+traps",
        },
        "rerank_compare": {
            "sentence": rerank_payload.get("sentence") if rerank_payload else None,
            "report_path": rerank_payload.get("report_path") if rerank_payload else None,
        },
    }
    json_path.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if PRODUCTION_RETRIEVAL_MODE != "hybrid+rerank":
        raise RuntimeError("违例：Hard-Gold 骨架跑后生产默认臂非 hybrid+rerank")
    return {
        "report_path": str(md_path),
        "json_path": str(json_path),
        "metrics": metrics,
        "stats": stats,
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "gain_verdict": gain_verdict,
        "arm_compare": arm_payload,
        "rerank_compare": rerank_payload,
    }


def load_trap_corpus(root: Path) -> list:
    from freshlatch.store.ingest import parse_document

    out = []
    for as_of_dir in ("t0", "t1"):
        folder = Path(root) / as_of_dir
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            out.append(parse_document(path))
    return out


def run_trap_eval(*, trap_root: Path, trap_gold_path: Path, out_dir: Path) -> dict:
    """陷阱子集单独入库,不并进主指标 n,也不写入论文语料 data/corpus。"""
    gold = _load_json(trap_gold_path)
    store = InMemoryStore()
    pairs = load_trap_corpus(trap_root)
    for doc, chunks in pairs:
        store.add_document(doc, chunks)
    kinds = []
    lines = [
        "# 检索陷阱三类（与主金标分列）",
        "",
        "本页只报告陷阱子集,不顶替主张 must_* ,也不计入主指标 n。语料在 data/traps,不改论文语料 data/corpus。冒烟级,不声称统计显著。",
        "",
    ]
    for row in gold["queries"]:
        hits = store.retrieve(row["query"], as_of=row["as_of"], top_k=10)
        ranked = [chunk_evidence_id(c) for c in hits]
        hit = recall_at_k(ranked, row["relevant"], 10)
        kinds.append(row["kind"])
        lines.extend([
            f"## {row['kind']} · {row['id']}",
            "",
            f"- query: {row['query']}",
            f"- as_of: {row['as_of']}",
            f"- 相关 evidence_id: {', '.join(row['relevant'])}",
            f"- 干扰 evidence_id: {', '.join(row['distractors'])}",
            f"- 评测意图: {row['eval_intent']}",
            f"- Recall@10（陷阱子集）: {hit:.4f}",
            f"- 命中序: {', '.join(ranked) if ranked else '(空)'}",
            "",
        ])
    text = "\n".join(lines)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "retrieve-traps.md"
    path.write_text(text, encoding="utf-8")
    return {"kinds": kinds, "report_path": str(path), "n": len(gold["queries"])}


def run_transform_compare(
    *,
    corpus: Path,
    docket_path: Path,
    distractor_path: Path,
    gold_path: Path,
    out_dir: Path,
    llm_rewrite=None,
    llm_record: dict | None = None,
) -> dict:
    """裸 statement / 模板变换 / 可选 LLM 臂。默认不调用 LLM。"""
    docket = _load_json(docket_path)
    distractor = _load_json(distractor_path)
    gold = _load_json(gold_path)
    claims = [
        c for c in list(docket["claims"]) + list(distractor["claims"])
        if c["claim_id"] in (gold.get("causal_chain") or {})
    ]
    claims.sort(key=lambda c: _cid_key(c["claim_id"]))
    record = {
        "enabled": llm_rewrite is not None,
        "model": None,
        "temperature": None,
        "seed": None,
        "on_failure": "statement",
    }
    if llm_record:
        record.update(llm_record)
    store = InMemoryStore()
    ingest_into(store, corpus)

    def score(query: str, relevant: list[str]) -> float:
        hits = store.retrieve(query, as_of="T1", top_k=10)
        ranked = [chunk_evidence_id(c) for c in hits]
        return recall_at_k(ranked, relevant, 10)

    rows = []
    bare_scores = []
    tmpl_scores = []
    llm_scores = []
    for claim in claims:
        cid = claim["claim_id"]
        chain = gold["causal_chain"][cid]
        relevant = [f"{chain['t1_doc']}#{chain['anchor']}@T1"]
        bare = transform_claim_query(claim["statement"])
        templ = transform_claim_query(claim["statement"], dimension=claim.get("dimension"))
        llm_q = bare
        if llm_rewrite is not None:
            try:
                llm_q = llm_rewrite(
                    claim["statement"],
                    model=record.get("model"),
                    temperature=record.get("temperature"),
                    seed=record.get("seed"),
                ) or bare
            except Exception as exc:
                logger.warning(
                    "查询改写失败，回落 bare query exc_type=%s",
                    type(exc).__name__,
                )
                llm_q = bare
        b, t, l = score(bare, relevant), score(templ, relevant), score(llm_q, relevant)
        bare_scores.append(b)
        tmpl_scores.append(t)
        llm_scores.append(l)
        rows.append((cid, b, t, l))

    # 默认路径就是模板变换,不经 LLM。
    lines = [
        "# 主张查询变换前后 Recall 对比（冒烟）",
        "",
        f"- n: {len(rows)}（冒烟级,不声称统计显著,不报方差）",
        "- 默认生产路径: 模板变换,不依赖 LLM 改写",
        f"- LLM 臂启用: {record['enabled']}",
        f"- 模型: {record['model']}",
        f"- temperature: {record['temperature']}",
        f"- seed: {record['seed']}",
        "- 失败回落: statement",
        "",
        "| 主张 | 裸 statement Recall@10 | 模板变换 Recall@10 | LLM 臂 Recall@10 |",
        "| --- | --- | --- | --- |",
    ]
    for cid, b, t, l in rows:
        lines.append(f"| {cid} | {b:.4f} | {t:.4f} | {l:.4f} |")
    lines.extend([
        "",
        f"- 裸 statement 宏平均 Recall@10: {_mean(bare_scores):.4f}",
        f"- 模板变换 宏平均 Recall@10: {_mean(tmpl_scores):.4f}",
        f"- LLM 臂 宏平均 Recall@10: {_mean(llm_scores):.4f}",
        "",
        "LLM 臂未启用时与裸 statement 相同,因为失败或未调用都回落 statement。",
        "",
    ])
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "retrieve-transform-compare.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "report_path": str(path),
        "n": len(rows),
        "bare": _mean(bare_scores),
        "template": _mean(tmpl_scores),
        "llm": _mean(llm_scores),
        "llm_record": record,
    }


# 预登记(#162):确定性 BM25 相对已落档 A0 Recall@10 容差为 0。低于基线即 fail。
A0_BM25_RECALL_TOLERANCE = 0.0


def arm_pass_line(*, bm25: float, dense: float, hybrid: float, a0: float) -> dict:
    """hybrid 不得低于两臂较差者;BM25 不得低于 A0。"""
    bm25_ok = bm25 + 1e-9 >= a0 - A0_BM25_RECALL_TOLERANCE
    hybrid_ok = hybrid + 1e-9 >= min(bm25, dense)
    return {
        "bm25_vs_a0": "pass" if bm25_ok else "fail",
        "hybrid_vs_min": "pass" if hybrid_ok else "fail",
        "pass": bm25_ok and hybrid_ok,
    }


def _load_a0_recall10(path: Path) -> float:
    raw = _load_json(path)
    return float(raw["metrics"]["recall"]["10"])


def _attach_vecs(store: InMemoryStore, db_path: Path) -> int:
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT doc_id, clause_id, as_of, vec FROM chunks"
        ).fetchall()
    finally:
        conn.close()
    index = {
        (row["doc_id"], row["clause_id"], row["as_of"]): row["vec"]
        for row in rows
        if row["vec"]
    }
    attached = 0
    for chunk in store._chunks:
        vec = index.get((chunk.doc_id, chunk.clause_id, chunk.as_of))
        if vec:
            chunk.vec = vec
            attached += 1
    return attached


def _ingest_eval_corpus(
    store: InMemoryStore,
    corpus: Path,
    trap_root: Path | None = None,
) -> int:
    """评测入库：主语料；可选 traps（与 A0 / Hard-Gold 同库口径）。"""
    n = ingest_into(store, Path(corpus))
    if trap_root is None:
        return n
    root = Path(trap_root)
    if not root.is_dir():
        return n
    for doc, chunks in load_trap_corpus(root):
        store.add_document(doc, chunks)
        n += len(chunks)
    return n


def _cached_query_embedder(queries: list[str]):
    from freshlatch.store.embeddings import embed_texts

    cache: dict[str, list[float]] = {}
    pending = [q for q in queries if q not in cache]
    batch = 8
    for start in range(0, len(pending), batch):
        chunk = pending[start:start + batch]
        vectors = embed_texts(chunk)
        for text, vec in zip(chunk, vectors):
            cache[text] = vec

    def embed(query: str) -> list[float]:
        return cache[query]

    return embed


def run_arm_compare(
    *,
    corpus: Path,
    retrieve_gold_path: Path,
    dense_db: Path,
    a0_baseline_path: Path,
    out_dir: Path,
    trap_root: Path | None = None,
    report_name: str = "retrieve-arm-compare.md",
    level_label: str = "冒烟",
) -> dict:
    """同语料同 query 的 BM25 / dense / hybrid 三列。不用 α 加权。

    trap_root 非空时与 A0/Hard-Gold 同库（corpus+traps）；冒烟默认不加 traps。
    """
    from freshlatch.store.pipeline import RRF_K

    retrieve_gold = _load_json(retrieve_gold_path)
    store = InMemoryStore()
    _ingest_eval_corpus(store, corpus, trap_root=trap_root)
    attached = _attach_vecs(store, dense_db)
    if attached != len(store._chunks) or attached == 0:
        raise ValueError("dense 索引未覆盖全部 chunk,拒绝把降级结果写成 dense/hybrid")
    store.query_embedder = _cached_query_embedder(
        [row["query"] for row in retrieve_gold["queries"]]
    )
    columns = {"bm25": [], "dense": [], "hybrid": []}
    modes_seen = {"dense": set(), "hybrid": set()}
    for row in retrieve_gold["queries"]:
        for mode in ("bm25", "dense", "hybrid"):
            store.bind_eval_retrieval_mode(mode if mode != "bm25" else None)
            hits = store.retrieve(row["query"], as_of=row["as_of"], top_k=10)
            got = getattr(store, "last_retrieval_mode", mode)
            if mode in modes_seen:
                modes_seen[mode].add(got)
            ranked = [chunk_evidence_id(c) for c in hits]
            columns[mode].append(recall_at_k(ranked, row["relevant"], 10))
        store.bind_eval_retrieval_mode(None)
    means = {mode: _mean(values) for mode, values in columns.items()}
    dense_honest = modes_seen["dense"] == {"dense"}
    hybrid_honest = modes_seen["hybrid"] == {"hybrid"}
    a0 = _load_a0_recall10(a0_baseline_path)
    verdict = arm_pass_line(
        bm25=means["bm25"], dense=means["dense"], hybrid=means["hybrid"], a0=a0,
    )
    passed = bool(verdict["pass"] and dense_honest and hybrid_honest)
    scope = "corpus+traps" if trap_root is not None else "corpus"
    lines = [
        f"# BM25 / dense / hybrid 三列（{level_label}）",
        "",
        f"- RRF k: {RRF_K}",
        "- 融合: 名次倒数,不是 α 加权",
        f"- 模型: {EMBED_MODEL}",
        "- 解码: 向量为预计算嵌入,打分无 temperature/seed",
        f"- 评测库: {scope}",
        f"- n: {len(retrieve_gold['queries'])}（冒烟级,不声称统计显著,不报方差）",
        f"- BM25 Recall@10: {means['bm25']:.4f}",
        f"- dense Recall@10: {means['dense']:.4f}",
        f"- hybrid Recall@10: {means['hybrid']:.4f}",
        f"- A0 基线 Recall@10: {a0:.4f}",
        f"- BM25 相对 A0 容差: {A0_BM25_RECALL_TOLERANCE}",
        f"- BM25 相对 A0: {verdict['bm25_vs_a0']}",
        f"- hybrid >= min(BM25, dense): {verdict['hybrid_vs_min']}",
        f"- dense 列确为 dense: {'pass' if dense_honest else 'fail'}",
        f"- hybrid 列确为 hybrid: {'pass' if hybrid_honest else 'fail'}",
        f"- 通过线: {'pass' if passed else 'fail'}",
        "",
        f"本页是 {level_label} 对比,不是统计结论。生产默认仍是 BM25。",
        "",
    ]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / report_name
    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "report_path": str(path),
        "rrf_k": RRF_K,
        "means": means,
        "pass": passed,
        "verdict": "pass" if passed else "fail",
        "corpus_scope": scope,
        "bm25_vs_a0": verdict["bm25_vs_a0"],
        "hybrid_vs_min": verdict["hybrid_vs_min"],
    }


# 预登记(#163):Recall@10 必须严格高于 hybrid,且单次 retrieve 含 rerank 的 p95≤800ms,才可写生产默认开。
RERANK_P95_BUDGET_MS = 800.0


def rerank_default_verdict(*, hybrid: float, rerank: float, p95_ms: float) -> str:
    if rerank > hybrid and p95_ms <= RERANK_P95_BUDGET_MS:
        return "生产默认开"
    return "生产默认关"


def _p95_ms(samples: list[float]) -> float:
    import math

    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return ordered[index] * 1000.0


def run_rerank_compare(
    *,
    corpus: Path,
    retrieve_gold_path: Path,
    dense_db: Path,
    out_dir: Path,
    trap_root: Path | None = None,
    report_name: str = "retrieve-rerank-compare.md",
    level_label: str = "冒烟",
) -> dict:
    """hybrid 与 hybrid+rerank 的 Recall@10 和 p95。未过线则生产默认关。"""
    import time

    from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

    retrieve_gold = _load_json(retrieve_gold_path)
    store = InMemoryStore()
    _ingest_eval_corpus(store, corpus, trap_root=trap_root)
    attached = _attach_vecs(store, dense_db)
    if attached != len(store._chunks) or attached == 0:
        raise ValueError("dense 索引未覆盖全部 chunk,拒绝把降级结果写成 rerank 成绩")
    store.query_embedder = _cached_query_embedder(
        [row["query"] for row in retrieve_gold["queries"]]
    )
    recalls = {"hybrid": [], "hybrid+rerank": []}
    latencies = []
    modes = set()
    for row in retrieve_gold["queries"]:
        store.bind_eval_retrieval_mode("hybrid")
        hybrid_hits = store.retrieve(row["query"], as_of=row["as_of"], top_k=10)
        recalls["hybrid"].append(
            recall_at_k([chunk_evidence_id(c) for c in hybrid_hits], row["relevant"], 10)
        )
        store.bind_eval_retrieval_mode("hybrid+rerank")
        started = time.perf_counter()
        rerank_hits = store.retrieve(row["query"], as_of=row["as_of"], top_k=10)
        latencies.append(time.perf_counter() - started)
        modes.add(getattr(store, "last_retrieval_mode", ""))
        recalls["hybrid+rerank"].append(
            recall_at_k([chunk_evidence_id(c) for c in rerank_hits], row["relevant"], 10)
        )
        store.bind_eval_retrieval_mode(None)
    hybrid_mean = _mean(recalls["hybrid"])
    rerank_mean = _mean(recalls["hybrid+rerank"])
    p95 = _p95_ms(latencies)
    honest = modes == {"hybrid+rerank"}
    sentence = rerank_default_verdict(
        hybrid=hybrid_mean, rerank=rerank_mean, p95_ms=p95,
    )
    if not honest:
        sentence = "生产默认关"
    scope = "corpus+traps" if trap_root is not None else "corpus"
    lines = [
        f"# hybrid 与 hybrid+rerank 对比（{level_label}）",
        "",
        "- 对比臂: 本地词重叠精排,不是 bge,不是 α 加权",
        "- 解码: 无 LLM temperature/seed;延迟在本机 perf_counter 上测量",
        f"- 评测库: {scope}",
        f"- n: {len(retrieve_gold['queries'])}（冒烟级,不声称统计显著,不报方差）",
        f"- hybrid Recall@10: {hybrid_mean:.4f}",
        f"- hybrid+rerank Recall@10: {rerank_mean:.4f}",
        f"- p95: {p95:.1f} ms",
        f"- 门槛: Recall@10 严格更好且 p95≤{RERANK_P95_BUDGET_MS:.0f}ms",
        f"- rerank 列确为 hybrid+rerank: {'pass' if honest else 'fail'}",
        f"- 判决: {sentence}",
        f"- 代码生产默认: {PRODUCTION_RETRIEVAL_MODE}",
        "",
        "未同时满足两条门槛时生产默认保持关。本页不是统计结论。",
        "",
    ]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / report_name
    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "report_path": str(path),
        "sentence": sentence,
        "hybrid": hybrid_mean,
        "rerank": rerank_mean,
        "p95_ms": p95,
        "production_mode": PRODUCTION_RETRIEVAL_MODE,
        "corpus_scope": scope,
    }


# L4-EV-01：同 pin、同 gold 的分臂表。不调用 arm_pass_line，不写冻结基线。
ARM_TABLE_ARMS = ("bm25", "dense", "hybrid", "hybrid+rerank")
ARM_TABLE_MARKDOWN = "arm-table.md"
ARM_TABLE_JSON = "arm-table.json"
_ARM_TABLE_BANNED = ("通过", "失败", "counted_as_pass", "SESOI", "status=", "门槛")
_ARM_TABLE_BLOCKED_GOLD = (
    ("data", "eval", "gold.json"),
    ("data", "eval", "guard_should.json"),
    ("data", "eval", "cite_sentence.json"),
    ("data", "eval", "temporal_new_over_old.json"),
    ("data", "exp", "x1"),
    ("docs", "evidence", "neural-rerank"),
)
_ARM_TABLE_BLOCKED_OUT = (
    ("docs", "evidence", "neural-rerank"),
    ("docs", "evidence", "patch-events"),
    ("docs", "evidence", "quality-gate"),
    ("data", "exp", "x1"),
    ("data", "eval"),
)
_CHUNK_KEYS = (
    "doc_id",
    "clause_id",
    "as_of",
    "title",
    "text",
    "source_type",
    "doc_version",
    "checksum",
    "tokens",
    "vec",
)
_QUERY_KEYS = ("id", "query", "as_of", "relevant", "query_vec")


def _path_parts(path: Path | str) -> tuple[str, ...]:
    """按 ``/`` 与 ``\\`` 切段，并折叠 ``.`` / ``..``。不访问磁盘。"""
    text = str(path).replace("\\", "/").strip()
    stack: list[str] = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if stack:
                stack.pop()
            continue
        stack.append(part)
    return tuple(stack)


def _path_contains(path: Path | str, needle: tuple[str, ...]) -> bool:
    parts = _path_parts(path)
    width = len(needle)
    if width == 0 or len(parts) < width:
        return False
    for index in range(len(parts) - width + 1):
        if parts[index:index + width] == needle:
            return True
    return False


def _reject_arm_table_paths(gold_path: Path, out_dir: Path) -> None:
    """受保护金标与冻结目录不能当本表的输入或输出。"""
    for needle in _ARM_TABLE_BLOCKED_GOLD:
        if _path_contains(gold_path, needle):
            joined = "/".join(needle)
            raise ValueError(f"拒绝读取受保护路径 {joined}")
    for needle in _ARM_TABLE_BLOCKED_OUT:
        if _path_contains(out_dir, needle):
            joined = "/".join(needle)
            raise ValueError(f"拒绝把分臂表写进 {joined}")


def _require_keys(row: dict, keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if key not in row or row[key] is None]
    if missing:
        raise ValueError(f"{label} 缺字段 {missing}")


def _as_of_value(value: object, label: str) -> str:
    if value not in ("T0", "T1"):
        raise ValueError(f"{label} as_of 必须为 T0 或 T1")
    return str(value)


def _float_vec(value: object, label: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} 的向量必须是非空数组")
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} 的向量不是数字") from exc


def _fmt_metric(value: float) -> str:
    """固定小数写法，同一 float 每次相同。"""
    if value == 0.0:
        return "0"
    text = format(value, ".12f").rstrip("0").rstrip(".")
    return text or "0"


def _one_observed(values: set[str], label: str) -> str:
    if len(values) != 1:
        raise ValueError(f"{label} 在各 query 上不一致: {sorted(values)}")
    return next(iter(values))


def _read_code_pin(code_pin: str | None) -> str:
    if code_pin is not None:
        text = str(code_pin).strip()
        if not text:
            raise ValueError("code_pin 为空")
        return text
    import subprocess

    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    pin = (proc.stdout or "").strip()
    if proc.returncode != 0 or len(pin) != 40:
        raise ValueError("读不到 git HEAD。请传 --pin")
    return pin


def _display_path(path: Path) -> str:
    try:
        shown = path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        shown = path
    return shown.as_posix()


def _load_arm_table_fixture(gold_path: Path) -> dict:
    """小夹具。必须自带 chunk 向量与 query 向量，本函数不调用 embedding。"""
    raw = _load_json(gold_path)
    for key in ("level", "k", "queries", "chunks", "version"):
        if key not in raw or raw[key] is None:
            raise ValueError(f"夹具缺字段 {key}")
    if raw["level"] != "smoke":
        raise ValueError("分臂表夹具 level 必须为 smoke")
    if isinstance(raw["k"], bool) or not isinstance(raw["k"], int) or raw["k"] < 1:
        raise ValueError("夹具 k 必须是正整数")
    queries = raw["queries"]
    chunks = raw["chunks"]
    if not isinstance(queries, list) or not queries:
        raise ValueError("夹具 queries 必须是非空数组")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("夹具 chunks 必须是非空数组")
    seen_ids: set[str] = set()
    seen_queries: set[str] = set()
    dim: int | None = None
    for index, row in enumerate(queries):
        label = f"queries[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{label} 必须是对象")
        _require_keys(row, _QUERY_KEYS, label)
        qid = str(row["id"])
        if qid in seen_ids:
            raise ValueError(f"query id 重复: {qid}")
        seen_ids.add(qid)
        query = str(row["query"])
        if query in seen_queries:
            raise ValueError(f"query 文本重复: {query}")
        seen_queries.add(query)
        _as_of_value(row["as_of"], label)
        relevant = row["relevant"]
        if not isinstance(relevant, list) or not relevant:
            raise ValueError(f"{label} relevant 必须是非空数组")
        if not all(isinstance(item, str) and item for item in relevant):
            raise ValueError(f"{label} relevant 必须是非空字符串")
        vec = _float_vec(row["query_vec"], label)
        dim = len(vec) if dim is None else dim
        if len(vec) != dim:
            raise ValueError(f"{label} 向量维度与其它 query 不一致")
    seen_evidence: set[str] = set()
    for index, row in enumerate(chunks):
        label = f"chunks[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{label} 必须是对象")
        _require_keys(row, _CHUNK_KEYS, label)
        _as_of_value(row["as_of"], label)
        if isinstance(row["tokens"], bool) or not isinstance(row["tokens"], int):
            raise ValueError(f"{label} tokens 必须是整数")
        vec = _float_vec(row["vec"], label)
        if dim is None or len(vec) != dim:
            raise ValueError(f"{label} 向量维度与 query 不一致")
        evidence = f"{row['doc_id']}#{row['clause_id']}@{row['as_of']}"
        if evidence in seen_evidence:
            raise ValueError(f"chunk 主键重复: {evidence}")
        seen_evidence.add(evidence)
    return raw


def _arm_table_store(fixture: dict):
    """用夹具里的 vec 建内存库。query 向量按 query 文本注入，不打网。"""
    from freshlatch.store.base import Chunk, Document
    from freshlatch.store.pipeline import pack_vec

    store = InMemoryStore()
    grouped: dict[tuple[str, str], list] = {}
    for row in fixture["chunks"]:
        chunk_id = f"{row['doc_id']}-{row['clause_id']}"
        chunk = Chunk(
            doc_id=str(row["doc_id"]),
            chunk_id=chunk_id,
            clause_id=str(row["clause_id"]),
            title=str(row["title"]),
            text=str(row["text"]),
            source_type=str(row["source_type"]),
            as_of=row["as_of"],
            doc_version=str(row["doc_version"]),
            checksum=str(row["checksum"]),
            tokens=int(row["tokens"]),
            vec=pack_vec(_float_vec(row["vec"], str(row["doc_id"]))),
        )
        grouped.setdefault((chunk.doc_id, chunk.as_of), []).append(chunk)
    for (doc_id, as_of), group in grouped.items():
        store.add_document(
            Document(
                doc_id=doc_id,
                as_of=as_of,
                source_type=group[0].source_type,
                title=group[0].title,
                doc_version=group[0].doc_version,
                checksum=group[0].checksum,
                full_text="\n".join(item.text for item in group),
            ),
            group,
        )
    vectors = {
        str(row["query"]): _float_vec(row["query_vec"], str(row["id"]))
        for row in fixture["queries"]
    }

    def embed(query: str) -> list[float]:
        if query not in vectors:
            raise ValueError(f"夹具缺少 query 向量: {query}")
        return vectors[query]

    store.query_embedder = embed
    return store


def _render_arm_table_markdown(payload: dict) -> str:
    lines = [
        "# Recall@k / MRR 分臂表",
        "",
        f"- level: {payload['level']}",
        f"- k: {payload['k']}",
        f"- n: {payload['n']}",
        f"- code_pin: {payload['code_pin']}",
        f"- gold_path: {payload['gold_path']}",
        f"- gold_sha256: {payload['gold_sha256']}",
        f"- fixture_version: {payload['fixture_version']}",
        f"- production_retrieval_mode: {payload['production_retrieval_mode']}",
        f"- rrf_k: {payload['rrf_k']}",
        f"- neural_rerank_k: {payload['neural_rerank_k']}",
        f"- neural_rerank_env: {payload['neural_rerank_env']}",
        "- 解码: 夹具内向量，无 temperature，无 seed",
        "- 检索 top_k 等于 k",
        "- replaces_frozen_baseline: false",
        "- 冻结基线文件不在本目录重写",
        "",
        "| arm | Recall@k | MRR | observed_retrieval_mode | observed_rerank_mode |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {arm} | {recall} | {mrr} | {retrieval} | {rerank} |".format(
                arm=row["arm"],
                recall=_fmt_metric(row["recall_at_k"]),
                mrr=_fmt_metric(row["mrr"]),
                retrieval=row["observed_retrieval_mode"],
                rerank=row["observed_rerank_mode"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def _reject_banned_arm_table_text(text: str) -> None:
    for token in _ARM_TABLE_BANNED:
        if token in text:
            raise ValueError(f"分臂表不得包含 {token}")


def run_arm_metric_table(
    *,
    gold_path: Path,
    out_dir: Path,
    code_pin: str | None = None,
) -> dict:
    """同 pin、同 gold，按臂列出 Recall@k 与 MRR。

    打分调用已有 ``recall_at_k`` / ``mrr_at_k`` / ``_mean``。
    不调用 ``arm_pass_line``。不写 ``docs/evidence/neural-rerank/``。
    """
    import os

    from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
    from freshlatch.store.neural_rerank import NEURAL_RERANK_ENV, NEURAL_RERANK_K
    from freshlatch.store.pipeline import (
        RRF_K,
        HitScoreBook,
        activate_hit_score_book,
        reset_hit_score_book,
    )

    gold = Path(gold_path)
    out = Path(out_dir)
    _reject_arm_table_paths(gold, out)
    if not gold.is_file():
        raise ValueError(f"夹具不存在: {gold.as_posix()}")
    if out.exists() and not out.is_dir():
        raise ValueError(f"输出路径不是目录: {out.as_posix()}")
    pin = _read_code_pin(code_pin)
    fixture = _load_arm_table_fixture(gold)
    k = int(fixture["k"])
    store = _arm_table_store(fixture)
    recalls = {arm: [] for arm in ARM_TABLE_ARMS}
    mrrs = {arm: [] for arm in ARM_TABLE_ARMS}
    seen_retrieval = {arm: set() for arm in ARM_TABLE_ARMS}
    seen_rerank = {arm: set() for arm in ARM_TABLE_ARMS}
    book_token = activate_hit_score_book(HitScoreBook())
    try:
        for row in fixture["queries"]:
            relevant = [str(item) for item in row["relevant"]]
            for arm in ARM_TABLE_ARMS:
                store.bind_eval_retrieval_mode(arm)
                hits = store.retrieve(str(row["query"]), as_of=row["as_of"], top_k=k)
                ranked = [chunk_evidence_id(chunk) for chunk in hits]
                recalls[arm].append(recall_at_k(ranked, relevant, k))
                mrrs[arm].append(mrr_at_k(ranked, relevant, k))
                seen_retrieval[arm].add(str(getattr(store, "last_retrieval_mode", "")))
                seen_rerank[arm].add(str(getattr(store, "last_rerank_mode", "")))
            store.bind_eval_retrieval_mode(None)
    finally:
        reset_hit_score_book(book_token)
    env_value = os.environ.get(NEURAL_RERANK_ENV)
    rows = []
    for arm in ARM_TABLE_ARMS:
        rows.append({
            "arm": arm,
            "recall_at_k": _mean(recalls[arm]),
            "mrr": _mean(mrrs[arm]),
            "observed_retrieval_mode": _one_observed(seen_retrieval[arm], arm),
            "observed_rerank_mode": _one_observed(seen_rerank[arm], arm),
        })
    payload = {
        "code_pin": pin,
        "fixture_version": str(fixture["version"]),
        "gold_path": _display_path(gold),
        "gold_sha256": sha256_hex(gold.read_bytes()),
        "k": k,
        "level": "smoke",
        "n": len(fixture["queries"]),
        "neural_rerank_env": "unset" if env_value is None else str(env_value),
        "neural_rerank_k": NEURAL_RERANK_K,
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "replaces_frozen_baseline": False,
        "rows": rows,
        "rrf_k": RRF_K,
    }
    markdown = _render_arm_table_markdown(payload)
    document = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _reject_banned_arm_table_text(markdown)
    _reject_banned_arm_table_text(document)
    out.mkdir(parents=True, exist_ok=True)
    markdown_path = out / ARM_TABLE_MARKDOWN
    json_path = out / ARM_TABLE_JSON
    markdown_path.write_text(markdown, encoding="utf-8", newline="\n")
    json_path.write_text(document, encoding="utf-8", newline="\n")
    payload["markdown_path"] = str(markdown_path)
    payload["json_path"] = str(json_path)
    return payload
