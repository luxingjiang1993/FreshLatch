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
    if dense_path.is_file():
        try:
            arm_payload = run_arm_compare(
                corpus=Path(corpus),
                retrieve_gold_path=hard_gold_path,
                dense_db=dense_path,
                a0_baseline_path=json_path,
                out_dir=out_dir,
            )
            arm_note = (
                f"臂对比已跑（见 retrieve-arm-compare.md）；"
                f"通过线={arm_payload.get('verdict')}。"
                "Hard-Gold 骨架 ≠ 授权换臂。"
            )
        except ValueError as exc:
            arm_note = f"臂对比跳过（{exc}）；不得因此改臂。"

    gain_verdict = (
        "关（Hard-Gold 骨架已跑；改生产默认臂仍须另决议 + 过线；"
        f"PRODUCTION_RETRIEVAL_MODE={PRODUCTION_RETRIEVAL_MODE!r}）"
    )

    lines = [
        "# Hard-Gold 骨架 · BM25 / 增益门复跑",
        "",
        "> 层身份：冒烟 / 面试加固（I3）。本波 Hard-Gold = 骨架语料 + 增益门复跑；**未授权改臂**。",
        "> 不报方差；不作统计显著。与冒烟 `retrieve_gold.json` 分文件。",
        "",
        f"- 日期: {date.today().isoformat()}",
        f"- hard gold: `{hard_gold_path}`",
        f"- n: {stats['n']}（预登记 ≥20）",
        f"- traps/对抗: {stats['trap_adversarial_count']} "
        f"（{stats['trap_adversarial_ratio']:.1%}，预登记 ≥30%）",
        f"- BM25 Recall@10: {metrics['recall']['10']:.4f}",
        f"- BM25 MRR@10: {metrics['mrr@10']:.4f}",
        f"- 代码生产默认臂: `{PRODUCTION_RETRIEVAL_MODE}`（断言须为 bm25）",
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
        },
    }
    json_path.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if PRODUCTION_RETRIEVAL_MODE != "bm25":
        raise RuntimeError("违例：Hard-Gold 骨架跑后生产默认臂非 bm25")
    return {
        "report_path": str(md_path),
        "json_path": str(json_path),
        "metrics": metrics,
        "stats": stats,
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "gain_verdict": gain_verdict,
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
            except Exception:
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
) -> dict:
    """同语料同 query 的 BM25 / dense / hybrid 三列。不用 α 加权。"""
    from freshlatch.store.pipeline import RRF_K

    retrieve_gold = _load_json(retrieve_gold_path)
    store = InMemoryStore()
    ingest_into(store, corpus)
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
    lines = [
        "# BM25 / dense / hybrid 三列（冒烟）",
        "",
        f"- RRF k: {RRF_K}",
        "- 融合: 名次倒数,不是 α 加权",
        "- 模型: text-embedding-v4",
        "- 解码: 向量为预计算嵌入,打分无 temperature/seed",
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
        "本页是冒烟对比,不是统计结论。生产默认仍是 BM25。",
        "",
    ]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "retrieve-arm-compare.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "report_path": str(path),
        "rrf_k": RRF_K,
        "means": means,
        "pass": passed,
        "verdict": "pass" if passed else "fail",
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
) -> dict:
    """hybrid 与 hybrid+rerank 的 Recall@10 和 p95。未过线则生产默认关。"""
    import time

    from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

    retrieve_gold = _load_json(retrieve_gold_path)
    store = InMemoryStore()
    ingest_into(store, corpus)
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
    lines = [
        "# hybrid 与 hybrid+rerank 对比（冒烟）",
        "",
        "- 对比臂: 本地词重叠精排,不是 bge,不是 α 加权",
        "- 解码: 无 LLM temperature/seed;延迟在本机 perf_counter 上测量",
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
    path = out / "retrieve-rerank-compare.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "report_path": str(path),
        "sentence": sentence,
        "hybrid": hybrid_mean,
        "rerank": rerank_mean,
        "p95_ms": p95,
        "production_mode": PRODUCTION_RETRIEVAL_MODE,
    }
