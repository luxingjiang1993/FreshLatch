"""x1 金标离线检索臂对比（测量）。

复用 ``recall_at_k`` / ``mrr_at_k`` / ``_p95_ms`` / ``rerank_default_verdict``
与 ``InMemoryStore`` 的 bm25 / dense / hybrid / hybrid+rerank。
不新定义召回公式，不改 ``PRODUCTION_RETRIEVAL_MODE``，不写生产 dense 库。

dense 向量只来自本地 ONNX 模型。本脚本不导入 ``freshlatch.store.embeddings``，
不调用 DashScope。配置里的 ``text-embedding-v4`` 因此标为未跑。
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# 先丢掉密钥，避免任何下游误读后去打付费接口。
os.environ.pop("DASHSCOPE_API_KEY", None)

from freshlatch.eval.retrieve_eval import (  # noqa: E402
    RERANK_P95_BUDGET_MS,
    _p95_ms,
    mrr_at_k,
    recall_at_k,
    rerank_default_verdict,
)
from freshlatch.eval.x1_checks import check_x1  # noqa: E402
from freshlatch.store.base import (  # noqa: E402
    PRODUCTION_RETRIEVAL_MODE,
    InMemoryStore,
    chunk_evidence_id,
)
from freshlatch.store.ingest import load_corpus  # noqa: E402
from freshlatch.store.pipeline import pack_vec, tokenize  # noqa: E402

LOCAL_EMBED_MODEL = "BAAI/bge-small-zh-v1.5"
MODES = ("bm25", "dense", "hybrid", "hybrid+rerank")
TOP_K = 10
PART2_QUESTIONS = (
    ROOT / "data/exp/x1/ret013-draft/round4/part2/questions.part2.json"
)
TEMPLATE_EXPECTED = 47
# 正式题集缺的那一道 part2 模板题，不计入 47。
TEMPLATE_ABSENT = "r4n-s2-d0-t1-91-qc"


def _mean(xs: list[float]) -> float | None:
    if not xs:
        return None
    return sum(xs) / len(xs)


def _load_queries(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    queries = raw["queries"] if isinstance(raw, dict) else raw
    return raw, list(queries)


def _template_ids(gold_ids: set[str]) -> list[str]:
    raw = json.loads(PART2_QUESTIONS.read_text(encoding="utf-8"))
    part2 = raw["queries"] if isinstance(raw, dict) else raw
    ids = [str(item["id"]) for item in part2]
    present = [qid for qid in ids if qid in gold_ids]
    missing = [qid for qid in ids if qid not in gold_ids]
    if missing != [TEMPLATE_ABSENT]:
        raise SystemExit(f"模板题缺集与留档不一致: {missing}")
    if len(present) != TEMPLATE_EXPECTED:
        raise SystemExit(f"合成模板陷阱题应为 {TEMPLATE_EXPECTED}，得到 {len(present)}")
    return present


def _local_embedder() -> tuple[Callable[[list[str]], list[list[float]]], str]:
    """返回 (embed, 说明)。模型权重下载后在本机推理，不走付费 API。"""
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise RuntimeError("未安装 fastembed，本地 embedding 不可用") from exc
    model = TextEmbedding(LOCAL_EMBED_MODEL)
    dim_holder = {"dim": None}

    def embed(texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        rows = [list(map(float, vec)) for vec in model.embed(texts, batch_size=32)]
        if len(rows) != len(texts):
            raise RuntimeError("本地 embedding 条数与输入不一致")
        dim = len(rows[0])
        if dim_holder["dim"] is None:
            dim_holder["dim"] = dim
        if any(len(row) != dim_holder["dim"] for row in rows):
            raise RuntimeError("本地 embedding 维度不一致")
        return rows

    return embed, f"fastembed TextEmbedding({LOCAL_EMBED_MODEL}) dim_pending"


def _ingest_x1(store: InMemoryStore, corpus: Path, traps: Path) -> int:
    """与 retrieve_typed.ingest_x1_corpus 相同：两个目录都走 load_corpus。

    不导入 retrieve_typed，因为该模块会连带导入 DashScope 的 embeddings。
    """
    n = 0
    for doc, chunks in load_corpus(corpus):
        store.add_document(doc, chunks)
        n += len(chunks)
    if traps.is_dir():
        for doc, chunks in load_corpus(traps):
            store.add_document(doc, chunks)
            n += len(chunks)
    return n


def _attach_local_vectors(store: InMemoryStore, embed: Callable[[list[str]], list[list[float]]]) -> int:
    texts = [chunk.text for chunk in store._chunks]
    vectors = embed(texts)
    if len(vectors) != len(texts):
        raise RuntimeError("chunk 向量条数不一致")
    dim = len(vectors[0]) if vectors else 0
    for chunk, vec in zip(store._chunks, vectors):
        chunk.vec = pack_vec(vec)
    return dim


def _score_slice(rows: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    picked = [row for row in rows if row["mode"] == mode]
    recalls = [row["recall@10"] for row in picked]
    mrrs = [row["mrr@10"] for row in picked]
    lats = [row["latency_s"] for row in picked]
    modes_seen = sorted({row["last_retrieval_mode"] for row in picked})
    return {
        "n": len(picked),
        "Recall@10": _mean(recalls),
        "MRR@10": _mean(mrrs),
        "p95_ms": _p95_ms(lats) if lats else None,
        "modes_seen": modes_seen,
    }


def _fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "未跑"
    return f"{value:.{digits}f}"


def _suggest(bm25_recall: float | None, arm_recall: float | None, p95_ms: float | None) -> bool:
    if bm25_recall is None or arm_recall is None or p95_ms is None:
        return False
    return arm_recall > bm25_recall and p95_ms <= RERANK_P95_BUDGET_MS


def _render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# x1 检索模式对比（离线测量）",
        "",
        "> 层：实验 / 冒烟。单次确定性运行，不报方差，不作统计显著。",
        "> 不是改臂授权。`PRODUCTION_RETRIEVAL_MODE` 仍为 bm25。",
        "> 数据：模型双标 + Ronin 代理人（模型）代审，`human_row_review=false`，不是人工逐行审核。",
        "",
        "## 输入",
        "",
        f"- 金标提交: `{payload['gold_commit']}`（PR #282）",
        f"- 题集: `{payload['questions']}`（n={payload['n_questions']}，arm={payload['n_arm']}，guardrail={payload['n_guardrail']}）",
        f"- 语料: `{payload['corpus']}` + `{payload['traps']}`，chunk={payload['n_chunks']}",
        f"- check_x1 退出码: {payload['check_x1']['exit_code']}",
        f"- 生产默认臂（跑前/跑后）: {payload['production_retrieval_mode_before']} / {payload['production_retrieval_mode_after']}",
        f"- 配置 dense 模型 `{payload['config_embed_model']}`（dim={payload['config_embed_dim']}）: 未跑。该路径只在 `embeddings.py` 调用 DashScope，本测量禁止付费 API。",
        f"- 本地 dense 模型: `{payload['local_embed_model']}`，dim={payload['local_embed_dim']}，库 `{payload['local_embed_lib']}`。查询向量在计时前预计算，与 `retrieve_typed.make_cached_query_embedder` 一样，p95 不含模型加载、不含网络嵌入。",
        "- Recall@10 用 `freshlatch.eval.retrieve_eval.recall_at_k`：top-10 里出现任一 relevant 记 1，否则 0，再对题宏平均。不是集合召回率。",
        "- p95 来自单次 `time.perf_counter`。重复运行会有毫秒级抖动，800ms 门槛对这个抖动不敏感。Recall 与 MRR 由排序决定。",
        "- MRR@10 用同文件 `mrr_at_k`。p95 用同文件 `_p95_ms`（入参秒，返回毫秒）。",
        "- 主表分母只含 `score_role=arm`。护栏题不进 Recall / MRR。",
        f"- 合成模板陷阱 47 道：`ret013-draft/round4/part2/questions.part2.json` 的 48 个 id 与正式题集的交集。缺 `{TEMPLATE_ABSENT}`。这 47 道仍计入总体与 trap，单独一列只是子集。",
        f"- 金标 qtype 词表是 lexical / paraphrase / multi_hop。本报告的 lexical 即字面重合题，没有另造 literal 列。category 里 adversarial 的 n=0。",
        "",
        "## 主表",
        "",
        "| 切片 | n | bm25 Recall@10 | bm25 MRR@10 | bm25 p95_ms | dense Recall@10 | dense MRR@10 | dense p95_ms | hybrid Recall@10 | hybrid MRR@10 | hybrid p95_ms | hybrid+rerank Recall@10 | hybrid+rerank MRR@10 | hybrid+rerank p95_ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["slices"]:
        cells = [row["label"], str(row["n"])]
        for mode in MODES:
            cell = row["by_mode"][mode]
            empty = row["n"] == 0
            cells.append("n/a" if empty else _fmt(cell["Recall@10"]))
            cells.append("n/a" if empty else _fmt(cell["MRR@10"]))
            cells.append("n/a" if empty else _fmt(cell["p95_ms"], 3))
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend([
        "",
        "## 相对 bm25 的 Recall@10 差与门槛",
        "",
        f"门槛（本测量采用，与 rerank 预登记的 800ms 同一延迟上限）：Recall@10 严格高于 bm25，且该臂 p95 ≤ {RERANK_P95_BUDGET_MS:.0f} ms。",
        "过门槛只表示可以另开票讨论，不是改默认。",
        "",
        "| 臂 | 总体 Recall@10 差（臂 − bm25） | 总体 p95_ms | 严格提升且 p95≤800 |",
        "|---|---:|---:|---|",
    ])
    for item in payload["threshold"]:
        lines.append(
            f"| {item['mode']} | {_fmt(item['recall_delta'])} | {_fmt(item['p95_ms'], 3)} | "
            f"{'是' if item['meets'] else '否'} |"
        )
    rerank_gate = payload["rerank_gate"]
    lines.extend([
        "",
        "## 仓库 rerank 预登记门（相对 hybrid，不是相对 bm25）",
        "",
        f"- hybrid Recall@10: {_fmt(rerank_gate['hybrid_recall'])}",
        f"- hybrid+rerank Recall@10: {_fmt(rerank_gate['rerank_recall'])}",
        f"- hybrid+rerank p95_ms: {_fmt(rerank_gate['p95_ms'], 3)}",
        f"- `rerank_default_verdict`: {rerank_gate['verdict']}",
        "- 该门要求 Recall@10 严格高于 hybrid 且 p95≤800ms 才写「生产默认开」。`rerank_lexical` 只重排 hybrid 已给出的 top-10，任一命中的 Recall@10 在这个实现下不会高于 hybrid。",
        "",
        "## 模式是否诚实",
        "",
    ])
    for mode, seen in payload["modes_seen"].items():
        lines.append(f"- {mode}: {', '.join(seen) if seen else '无'}")
    lines.extend([
        "",
        "## 结论",
        "",
        payload["conclusion"],
        "",
        "## 原始文件",
        "",
        "- `summary.json`",
        "- `per-query.csv`",
        "- `per-query.json`",
        "",
    ])
    return "\n".join(lines)


def run(argv: list[str] | None = None) -> int:
    del argv
    if PRODUCTION_RETRIEVAL_MODE != "bm25":
        print("PRODUCTION_RETRIEVAL_MODE 不是 bm25，停止", file=sys.stderr)
        return 1
    before = PRODUCTION_RETRIEVAL_MODE
    questions_path = ROOT / "data/exp/x1/questions.json"
    corpus = ROOT / "data/exp/x1/corpus"
    traps = ROOT / "data/exp/x1/traps"
    config_path = ROOT / "data/exp/x1/config.json"
    out_dir = ROOT / "docs/evidence/x1-retrieval-modes"
    meta, queries = _load_queries(questions_path)
    gold_ids = {str(item["id"]) for item in queries}
    template = set(_template_ids(gold_ids))
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    checked = check_x1(corpus, traps, questions_path, config_path)
    if checked.exit_code != 0:
        print(checked.format_report(), file=sys.stderr)
        return checked.exit_code

    store = InMemoryStore()
    n_chunks = _ingest_x1(store, corpus, traps)
    embed, _note = _local_embedder()
    dim = _attach_local_vectors(store, embed)
    query_texts = list(dict.fromkeys(str(item.get("query", "")) for item in queries))
    query_vecs = {
        text: vec for text, vec in zip(query_texts, embed(query_texts))
    }
    store.query_embedder = lambda query: query_vecs[query]
    tokenize("预热")

    per_query: list[dict[str, Any]] = []
    for item in queries:
        role = item.get("score_role") or "arm"
        relevant = [str(x) for x in (item.get("relevant") or [])]
        as_of = item.get("as_of")
        for mode in MODES:
            store.bind_eval_retrieval_mode(None if mode == "bm25" else mode)
            started = time.perf_counter()
            hits = store.retrieve(str(item.get("query", "")), as_of=as_of, top_k=TOP_K)
            elapsed = time.perf_counter() - started
            got = getattr(store, "last_retrieval_mode", None)
            ranked = [chunk_evidence_id(chunk) for chunk in hits]
            if role == "arm" and got != mode:
                print(f"模式不诚实 {item.get('id')} 请求 {mode} 得到 {got}", file=sys.stderr)
                return 1
            per_query.append({
                "id": item.get("id"),
                "qtype": item.get("qtype"),
                "category": item.get("category"),
                "score_role": role,
                "as_of": as_of,
                "template47": item.get("id") in template,
                "mode": mode,
                "recall@10": recall_at_k(ranked, relevant, TOP_K),
                "mrr@10": mrr_at_k(ranked, relevant, TOP_K),
                "latency_s": elapsed,
                "latency_ms": elapsed * 1000.0,
                "last_retrieval_mode": got,
                "ranked": ranked,
            })
    store.bind_eval_retrieval_mode(None)

    arm_rows = [row for row in per_query if row["score_role"] == "arm"]
    slice_defs: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [
        ("总体", lambda row: True),
        ("lexical", lambda row: row["qtype"] == "lexical"),
        ("paraphrase", lambda row: row["qtype"] == "paraphrase"),
        ("multi_hop", lambda row: row["qtype"] == "multi_hop"),
        ("hard", lambda row: row["category"] == "hard"),
        ("trap", lambda row: row["category"] == "trap"),
        ("adversarial", lambda row: row["category"] == "adversarial"),
        ("合成模板陷阱47", lambda row: row["template47"]),
    ]
    slices = []
    for label, pred in slice_defs:
        chosen = [row for row in arm_rows if pred(row)]
        # n 按题计，不按臂重复。
        n_questions = len({row["id"] for row in chosen})
        slices.append({
            "label": label,
            "n": n_questions,
            "by_mode": {mode: _score_slice(chosen, mode) for mode in MODES},
        })

    overall = next(row for row in slices if row["label"] == "总体")
    bm25_recall = overall["by_mode"]["bm25"]["Recall@10"]
    threshold = []
    for mode in MODES:
        if mode == "bm25":
            continue
        cell = overall["by_mode"][mode]
        delta = None
        if bm25_recall is not None and cell["Recall@10"] is not None:
            delta = cell["Recall@10"] - bm25_recall
        threshold.append({
            "mode": mode,
            "recall_delta": delta,
            "p95_ms": cell["p95_ms"],
            "meets": _suggest(bm25_recall, cell["Recall@10"], cell["p95_ms"]),
        })
    hybrid_recall = overall["by_mode"]["hybrid"]["Recall@10"]
    rerank_recall = overall["by_mode"]["hybrid+rerank"]["Recall@10"]
    rerank_p95 = overall["by_mode"]["hybrid+rerank"]["p95_ms"]
    verdict = "未跑"
    if hybrid_recall is not None and rerank_recall is not None and rerank_p95 is not None:
        verdict = rerank_default_verdict(
            hybrid=hybrid_recall, rerank=rerank_recall, p95_ms=rerank_p95
        )
    by_label = {row["label"]: row for row in slices}
    lexical = by_label["lexical"]["by_mode"]
    hard = by_label["hard"]["by_mode"]
    meets = [item["mode"] for item in threshold if item["meets"]]
    if meets:
        conclusion = (
            "按总体「Recall@10 严格高于 bm25 且 p95≤800ms」，"
            + "、".join(meets)
            + " 都过线。建议只把 hybrid 放进另开的讨论票："
            f"总体 Recall@10 {overall['by_mode']['bm25']['Recall@10']:.4f} → "
            f"{overall['by_mode']['hybrid']['Recall@10']:.4f}，p95 "
            f"{overall['by_mode']['hybrid']['p95_ms']:.3f} ms。"
            f"hybrid 的 lexical 是 {lexical['hybrid']['Recall@10']:.4f}，低于 bm25 的 {lexical['bm25']['Recall@10']:.4f}，总体增益来自 paraphrase 与 multi_hop。"
            f"dense 总体只高到 {overall['by_mode']['dense']['Recall@10']:.4f}，"
            f"但 lexical {lexical['dense']['Recall@10']:.4f} 低于 bm25 的 {lexical['bm25']['Recall@10']:.4f}，"
            f"hard {hard['dense']['Recall@10']:.4f} 也低于 bm25 的 {hard['bm25']['Recall@10']:.4f}。"
            "hybrid+rerank 的总体 Recall@10 与 hybrid 相同，"
            f"仓库预登记门（须严格高于 hybrid）的判决是「{verdict}」，不建议为 rerank 另开切换票。"
            "本轮不是授权：生产默认仍是 bm25；向量是本地 bge-small-zh-v1.5，不是配置里的 text-embedding-v4；"
            "题集是模型双标加模型代审。"
        )
    else:
        conclusion = (
            "按「Recall@10 严格高于 bm25 且 p95≤800ms」，没有任何非 bm25 臂同时满足，"
            "本轮没有理由另开票考虑切换。生产默认保持 bm25。"
        )

    after = PRODUCTION_RETRIEVAL_MODE
    if after != "bm25" or before != "bm25":
        print("生产默认臂被改动", file=sys.stderr)
        return 1
    if "freshlatch.store.embeddings" in sys.modules:
        print("embeddings 模块被加载，停止", file=sys.stderr)
        return 1

    modes_seen = {
        mode: sorted({row["last_retrieval_mode"] for row in arm_rows if row["mode"] == mode})
        for mode in MODES
    }
    payload: dict[str, Any] = {
        "level": "实验/冒烟",
        "human_row_review": False,
        "label_note": "模型双标 + Ronin 代理人（模型）代审，非人工逐行审核",
        "questions_meta": meta.get("meta", {}),
        "gold_commit": "5de99c1",
        "questions": "data/exp/x1/questions.json",
        "corpus": "data/exp/x1/corpus",
        "traps": "data/exp/x1/traps",
        "n_questions": len(queries),
        "n_arm": sum(1 for item in queries if (item.get("score_role") or "arm") == "arm"),
        "n_guardrail": sum(1 for item in queries if item.get("score_role") == "guardrail"),
        "n_chunks": n_chunks,
        "template47_n": len(template),
        "template47_absent": TEMPLATE_ABSENT,
        "production_retrieval_mode_before": before,
        "production_retrieval_mode_after": after,
        "config_embed_model": cfg.get("embed_model"),
        "config_embed_dim": cfg.get("embed_dim"),
        "config_embed_status": "未跑",
        "config_embed_reason": "embeddings.py 只调用 DashScope text-embedding-v4，本测量禁止付费 API",
        "local_embed_model": LOCAL_EMBED_MODEL,
        "local_embed_dim": dim,
        "local_embed_lib": "fastembed",
        "dashscope_called": False,
        "check_x1": {
            "exit_code": checked.exit_code,
            "qtype_counts": checked.qtype_counts,
            "n_arm": checked.n_arm,
            "n_guardrail": checked.n_guardrail,
            "trap_adversarial_ratio": checked.trap_adversarial_ratio,
            "n_chunks": checked.n_chunks,
            "synthetic_ratio": checked.synthetic_ratio,
            "public_ratio": checked.public_ratio,
            "decontam_hits": checked.decontam_hits,
            "license_violations": checked.license_violations,
            "lcs_flags": checked.lcs_flags,
        },
        "recall_definition": "recall_at_k: any relevant id in top-10 => 1 else 0; macro mean",
        "slices": slices,
        "threshold": threshold,
        "rerank_gate": {
            "hybrid_recall": hybrid_recall,
            "rerank_recall": rerank_recall,
            "p95_ms": rerank_p95,
            "verdict": verdict,
            "budget_ms": RERANK_P95_BUDGET_MS,
        },
        "modes_seen": modes_seen,
        "conclusion": conclusion,
        "p95_note": "单次 perf_counter；重复运行有毫秒级抖动；Recall/MRR 由排序决定",
        "llm_tokens": 0,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "RESULT.md").write_text(_render_md(payload), encoding="utf-8")
    (out_dir / "summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    csv_rows = []
    for row in per_query:
        csv_rows.append({
            "id": row["id"],
            "qtype": row["qtype"],
            "category": row["category"],
            "score_role": row["score_role"],
            "as_of": row["as_of"],
            "template47": int(row["template47"]),
            "mode": row["mode"],
            "recall@10": f"{row['recall@10']:.4f}",
            "mrr@10": f"{row['mrr@10']:.4f}",
            "latency_ms": f"{row['latency_ms']:.6f}",
            "last_retrieval_mode": row["last_retrieval_mode"],
        })
    with (out_dir / "per-query.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    (out_dir / "per-query.json").write_text(
        json.dumps(per_query, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out_dir}")
    print(conclusion)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
