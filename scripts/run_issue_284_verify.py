"""Issue #284 切换前验证。只测量，不改生产默认臂。

口径在写循环之前锁死，与 issue 正文一致：
- 配对 bootstrap 10000 次，seed=20261007，配对差 = 右臂 − 左臂，95% 为线性插值百分位
- McNemar 用 Recall@10 命中（0/1），精确二项、双侧（较小一侧概率乘 2，封顶 1）
- 分差 = top-10 的 id 集合或顺序不同
- 不导入 freshlatch.store.embeddings，不调用 DashScope
"""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
os.environ.pop("DASHSCOPE_API_KEY", None)

from freshlatch.eval.retrieve_eval import _p95_ms, mrr_at_k, recall_at_k  # noqa: E402
from freshlatch.eval.x1_checks import check_x1  # noqa: E402
from freshlatch.runner import RunContext  # noqa: E402
from freshlatch.store.base import (  # noqa: E402
    PRODUCTION_RETRIEVAL_MODE,
    InMemoryStore,
    chunk_evidence_id,
)
from freshlatch.store.ingest import load_corpus  # noqa: E402
from freshlatch.store.pipeline import pack_vec, tokenize  # noqa: E402

LOCAL_MODEL = "BAAI/bge-small-zh-v1.5"
MODES = ("bm25", "hybrid", "hybrid+rerank")
PAIRS = (
    ("bm25", "hybrid"),
    ("bm25", "hybrid+rerank"),
    ("hybrid", "hybrid+rerank"),
)
N_BOOT = 10000
BOOT_SEED = 20261007
P95_BUDGET_MS = 800.0
TOP_K = 10
PART2 = ROOT / "data/exp/x1/ret013-draft/round4/part2/questions.part2.json"
TEMPLATE_ABSENT = "r4n-s2-d0-t1-91-qc"
NICK = {"bm25": "词法", "hybrid": "混合", "hybrid+rerank": "重排"}
QTYPE_ZH = {"lexical": "字面题", "paraphrase": "换一种说法", "multi_hop": "要拼多处"}
CAT_ZH = {"hard": "普通难例", "trap": "陷阱", "adversarial": "对抗"}


def _rss_kb() -> tuple[int, int]:
    rss = hwm = 0
    for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            rss = int(line.split()[1])
        elif line.startswith("VmHWM:"):
            hwm = int(line.split()[1])
    return rss, hwm


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _percentile(sorted_xs: list[float], p: float) -> float:
    """线性插值百分位。p 取 0.025 与 0.975。"""
    if not sorted_xs:
        return 0.0
    k = (len(sorted_xs) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_xs[lo]
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (k - lo)


def _binom_cdf_half(n: int, k: int) -> float:
    """P(X<=k)，X~Binomial(n, 0.5)。"""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    log_denom = n * math.log(2.0)
    total = 0.0
    for i in range(k + 1):
        log_c = math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
        total += math.exp(log_c - log_denom)
    return min(1.0, total)


def _mcnemar_p(left_only: int, right_only: int) -> float:
    n = left_only + right_only
    if n == 0:
        return 1.0
    return min(1.0, 2.0 * _binom_cdf_half(n, min(left_only, right_only)))


def _ndcg_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
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


def _template_ids(gold_ids: set[str]) -> set[str]:
    raw = json.loads(PART2.read_text(encoding="utf-8"))
    ids = [str(item["id"]) for item in raw["queries"]]
    missing = [qid for qid in ids if qid not in gold_ids]
    if missing != [TEMPLATE_ABSENT]:
        raise SystemExit(f"模板题缺集与留档不一致: {missing}")
    present = {qid for qid in ids if qid in gold_ids}
    if len(present) != 47:
        raise SystemExit(f"合成模板陷阱题应为 47，得到 {len(present)}")
    return present


def _ingest(store: InMemoryStore, corpus: Path, traps: Path) -> int:
    n = 0
    for doc, chunks in load_corpus(corpus):
        store.add_document(doc, chunks)
        n += len(chunks)
    for doc, chunks in load_corpus(traps):
        store.add_document(doc, chunks)
        n += len(chunks)
    return n


def _local_embedder() -> tuple[Any, Callable[[list[str]], list[list[float]]]]:
    from fastembed import TextEmbedding

    model = TextEmbedding(LOCAL_MODEL)

    def embed(texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        rows = [list(map(float, vec)) for vec in model.embed(texts, batch_size=32)]
        if len(rows) != len(texts):
            raise RuntimeError("本地向量条数与输入不一致")
        return rows

    return model, embed


def _differs(left: list[str], right: list[str]) -> bool:
    return left[:TOP_K] != right[:TOP_K]


def _suggest(
    left: str,
    right: str,
    rec: dict[str, float],
    mrr: dict[str, float],
    p95_ok: dict[str, bool],
) -> tuple[str, str]:
    """机械建议。不是人工审核，也不是切换决定。"""
    if all(rec[mode] == 0.0 for mode in MODES):
        return (
            "需要改题",
            "词法、混合、重排的前 10 条里都没有金标。先请人看这道题和金标对不对，不谈换臂。",
        )
    rl, rr = rec[left], rec[right]
    ml, mr = mrr[left], mrr[right]

    def label_for(mode: str) -> str:
        if mode == "bm25":
            return "保持 bm25"
        if mode == "hybrid":
            return "可议 hybrid"
        return "可议 hybrid+rerank"

    def blocked(mode: str, body: str) -> tuple[str, str] | None:
        if mode != "bm25" and not p95_ok[mode]:
            return (
                "保持 bm25",
                f"{body}但这条臂的慢查询超过 800 毫秒，按验收不能写成可议。",
            )
        return None

    if rr > rl:
        body = f"{NICK[right]}的前 10 条里有金标，{NICK[left]}没有。"
        hit = blocked(right, body)
        if hit:
            return hit
        return label_for(right), body
    if rl > rr:
        body = f"{NICK[left]}的前 10 条里有金标，{NICK[right]}没有。"
        hit = blocked(left, body)
        if hit:
            return hit
        return label_for(left), body
    if mr > ml:
        body = f"两边都碰上了金标，{NICK[right]}把金标排得更靠前。"
        hit = blocked(right, body)
        if hit:
            return hit
        return label_for(right), body
    if ml > mr:
        body = f"两边都碰上了金标，{NICK[left]}把金标排得更靠前。"
        hit = blocked(left, body)
        if hit:
            return hit
        return label_for(left), body
    return (
        "保持 bm25",
        "金标撞上没有变，排位也没有变，变的是旁边材料谁先谁后。这一题不支持换臂。",
    )


def _fmt_rank(ranked: list[str]) -> str:
    if not ranked:
        return "（无）"
    return " ".join(f"{i}.{eid}" for i, eid in enumerate(ranked, start=1))


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


def _pair_recall_test(rows: list[dict[str, Any]], left: str, right: str, rng: random.Random) -> dict[str, Any]:
    diffs = [row["recall"][right] - row["recall"][left] for row in rows]
    left_only = sum(1 for row in rows if row["recall"][left] == 1.0 and row["recall"][right] == 0.0)
    right_only = sum(1 for row in rows if row["recall"][left] == 0.0 and row["recall"][right] == 1.0)
    both = sum(1 for row in rows if row["recall"][left] == 1.0 and row["recall"][right] == 1.0)
    neither = sum(1 for row in rows if row["recall"][left] == 0.0 and row["recall"][right] == 0.0)
    ci = _boot_ci(diffs, rng)
    return {
        "left": left,
        "right": right,
        "n": len(rows),
        "recall_left": _mean([row["recall"][left] for row in rows]),
        "recall_right": _mean([row["recall"][right] for row in rows]),
        "recall_diff": ci,
        "mcnemar": {
            "left_only": left_only,
            "right_only": right_only,
            "both_hit": both,
            "neither": neither,
            "p_two_sided": _mcnemar_p(left_only, right_only),
        },
    }


def _pair_metric_ci(rows: list[dict[str, Any]], left: str, right: str, key: str, rng: random.Random) -> dict[str, Any]:
    diffs = [row[key][right] - row[key][left] for row in rows]
    ci = _boot_ci(diffs, rng)
    return {
        "left": left,
        "right": right,
        "metric": key,
        "left_mean": _mean([row[key][left] for row in rows]),
        "right_mean": _mean([row[key][right] for row in rows]),
        **ci,
    }


def _recommend(tests: dict[str, Any], p95_ok: dict[str, bool], sync_gap: bool) -> str:
    """跑数前写死的建议规则。结构性缺向量时生产默认保持 bm25。"""
    if sync_gap:
        return "保持 bm25"
    rerank_vs_hybrid = tests["hybrid_vs_hybrid+rerank"]["recall_diff"]
    hybrid_vs_bm25 = tests["bm25_vs_hybrid"]["recall_diff"]
    if (
        p95_ok["hybrid+rerank"]
        and rerank_vs_hybrid["ci95_low"] > 0
    ):
        return "hybrid+rerank"
    if p95_ok["hybrid"] and hybrid_vs_bm25["ci95_low"] > 0:
        return "hybrid"
    return "保持 bm25"


def _req_names(requires: list[str]) -> list[str]:
    names: list[str] = []
    for req in requires:
        name = req.split(";", 1)[0].strip().split()[0]
        name = name.split("[")[0].split(">")[0].split("<")[0].split("!")[0].split("=")[0]
        if name and name not in names:
            names.append(name)
    return names


def _recommend_sentence(
    choice: str,
    tests: dict[str, Any],
    sync_gap: bool,
    rank_metrics: list[dict[str, Any]],
) -> str:
    hybrid = tests["bm25_vs_hybrid"]["recall_diff"]
    rerank = tests["hybrid_vs_hybrid+rerank"]
    ndcg = next(
        row for row in rank_metrics
        if row["left"] == "hybrid" and row["right"] == "hybrid+rerank" and row["metric"] == "ndcg"
    )
    if choice == "保持 bm25" and sync_gap:
        return (
            "建议保持 bm25：混合相对词法的 Recall@10 配对差点估计 "
            f"{hybrid['estimate']:+.4f}（区间 {hybrid['ci95_low']:+.4f} 到 {hybrid['ci95_high']:+.4f}），"
            "但入库和补丁不写向量，池里缺一条向量就会整池降成 bm25_fallback，不能当成已经切到混合；"
            f"重排相对混合的 Recall 配对差为 {rerank['recall_diff']['estimate']:+.4f}，"
            f"nDCG@10 配对差 {ndcg['estimate']:+.4f}"
            f"（区间 {ndcg['ci95_low']:+.4f} 到 {ndcg['ci95_high']:+.4f}），"
            "没有单独构成换默认的理由。"
        )
    if choice == "hybrid":
        return (
            "建议可议 hybrid：相对词法的 Recall@10 区间整个在 0 之上，p95 未过 800 毫秒，"
            "且重排的 Recall 区间没有整个高于混合。这不是切换授权。"
        )
    if choice == "hybrid+rerank":
        return (
            "建议可议 hybrid+rerank：相对混合的 Recall@10 区间整个在 0 之上，且 p95 未过 800 毫秒。"
            "这不是切换授权。"
        )
    return "建议保持 bm25：没有任何一条臂的 Recall@10 区间整个高于对照，且 p95 也在门槛内。这不是切换授权。"


def _render_checklist(items: list[dict[str, Any]], counts: dict[str, dict[str, int]]) -> str:
    lines = [
        "# 分差题抽查清单（给 Oriental Ronin 看）",
        "",
        "这份清单由模型按下面的固定规则起草，供 Oriental Ronin 人工审。",
        "还没有人逐条看过。这里的「建议」不是切换决定，也不是人工审核结论。",
        "数据是模型双标 + Ronin 代理人（模型）代审，不是人工逐行审核。",
        "",
        "分差：两边前 10 条的证据编号集合或顺序不同。只比有没有撞上金标不够，名次不同也算。",
        "分母只含作答臂（score_role=arm）。护栏题不在这里。",
        "",
        "规则：",
        "- 三条路的前 10 条都没有金标 → 需要改题。",
        "- 只有一边撞上金标 → 建议走撞上的那一边（词法写成「保持 bm25」）。",
        "- 两边都撞上，但一边把金标排得更靠前 → 建议走更靠前的那一边。",
        "- 撞上和排位都没变，只是旁边材料换了次序 → 保持 bm25。",
        "- 慢查询 p95 超过 800 毫秒的臂，不写成可议。",
        "",
        "## 条数",
        "",
    ]
    for left, right in PAIRS:
        key = f"{left}_vs_{right}"
        bucket = counts[key]
        lines.append(
            f"- {NICK[left]} vs {NICK[right]}：{bucket['n']} 题。"
            f"保持 bm25 {bucket.get('保持 bm25', 0)}，"
            f"可议 hybrid {bucket.get('可议 hybrid', 0)}，"
            f"可议 hybrid+rerank {bucket.get('可议 hybrid+rerank', 0)}，"
            f"需要改题 {bucket.get('需要改题', 0)}。"
        )
    lines.append("")
    current = ""
    number = 0
    for item in items:
        pair = item["pair"]
        if pair != current:
            current = pair
            number = 0
            left, right = pair.split("_vs_")
            lines.extend([
                f"## {NICK[left]} vs {NICK[right]}",
                "",
            ])
        number += 1
        points = "；".join(item["answer_points"]) if item["answer_points"] else "（无）"
        relevant = "；".join(item["relevant"]) if item["relevant"] else "（无）"
        lines.extend([
            f"### {number}. `{item['id']}`",
            "",
            f"- 问：{item['query']}",
            (
                f"- 题型：{QTYPE_ZH.get(item['qtype'], item['qtype'])}（{item['qtype']}）"
                f" · 类别：{CAT_ZH.get(item['category'], item['category'])}（{item['category']}）"
                f" · 合成模板陷阱：{'是' if item['template47'] else '否'}"
            ),
            f"- 金标证据：{relevant}",
            f"- 金标要点：{points}",
            f"- 词法前 10：{_fmt_rank(item['ranked']['bm25'])}",
            f"- 混合前 10：{_fmt_rank(item['ranked']['hybrid'])}",
            f"- 重排前 10：{_fmt_rank(item['ranked']['hybrid+rerank'])}",
            f"- 建议：{item['suggestion']}",
            f"- 理由：{item['reason']}",
            "",
        ])
    return "\n".join(lines)


def _render_result(payload: dict[str, Any]) -> str:
    lines = [
        "# Issue #284 切换前验证",
        "",
        "层：实验 / 冒烟，外加跑数前写死的配对区间。单次运行。不是切换授权，不报已证明最优。",
        "数据是模型双标 + Ronin 代理人（模型）代审，`human_row_review=false`，不是人工逐行审核。",
        "抽查清单是模型按规则起草的，供 Oriental Ronin 人工审，本页不宣称已经人工审核。",
        "",
        f"- 票：https://github.com/luxingjiang1993/FreshLatch/issues/284",
        "- 引用：https://github.com/luxingjiang1993/FreshLatch/pull/283",
        f"- 金标：`data/exp/x1/questions.json`，arm={payload['n_arm']}，guardrail={payload['n_guardrail']}，chunk={payload['n_chunks']}",
        f"- 向量：本地 `{payload['embed_model']}`，dim={payload['embed_dim']}，库 fastembed {payload['fastembed_version']}。不是 `text-embedding-v4`。",
        f"- 生产默认臂（跑前/跑后）：{payload['mode_before']} / {payload['mode_after']}",
        f"- check_x1 退出码：{payload['check_exit']}",
        "- Recall@10 沿用 `recall_at_k`（前 10 条里出现任一金标记 1）。MRR 沿用 `mrr_at_k`。",
        "- nDCG@10：金标集合内为 1、否则为 0，理想排序把金标放在最前。",
        f"- bootstrap：{N_BOOT} 次，seed={BOOT_SEED}，配对差 = 右 − 左，95% 线性插值百分位。顺序：三组 Recall，然后两组重排的 MRR，然后两组重排的 nDCG。",
        "- McNemar：Recall 命中的精确二项、双侧。",
        "",
        "## 显著性",
        "",
        "| 配对 | Recall 左 | Recall 右 | 差 | 95% 区间 | 只左中 | 只右中 | 都中 | 都未中 | McNemar p |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for key in ("bm25_vs_hybrid", "bm25_vs_hybrid+rerank", "hybrid_vs_hybrid+rerank"):
        row = payload["significance"][key]
        diff = row["recall_diff"]
        mc = row["mcnemar"]
        lines.append(
            f"| {NICK[row['left']]} vs {NICK[row['right']]} | {row['recall_left']:.4f} | "
            f"{row['recall_right']:.4f} | {diff['estimate']:+.4f} | "
            f"{diff['ci95_low']:+.4f} ~ {diff['ci95_high']:+.4f} | "
            f"{mc['left_only']} | {mc['right_only']} | {mc['both_hit']} | {mc['neither']} | "
            f"{mc['p_two_sided']:.6f} |"
        )
    lines.extend([
        "",
        "重排额外的排序指标（配对差 = 右 − 左）：",
        "",
        "| 配对 | 指标 | 左 | 右 | 差 | 95% 区间 |",
        "|---|---|---:|---:|---:|---|",
    ])
    for row in payload["rank_metrics"]:
        lines.append(
            f"| {NICK[row['left']]} vs {NICK[row['right']]} | {row['metric']} | "
            f"{row['left_mean']:.4f} | {row['right_mean']:.4f} | {row['estimate']:+.4f} | "
            f"{row['ci95_low']:+.4f} ~ {row['ci95_high']:+.4f} |"
        )
    cost = payload["cost"]
    lines.extend([
        "",
        "## 代价",
        "",
        f"- 模型载入：{cost['model_load_s']:.3f} 秒（权重已在本地缓存，不含首次下载）。",
        f"- 语料向量构建：{cost['index_build_s']:.3f} 秒，{cost['n_chunks']} 块，dim={cost['embed_dim']}，向量本体约 {cost['vec_bytes']} 字节。",
        f"- 问句向量：{cost['query_embed_s']:.3f} 秒，{cost['n_queries']} 条。p95 不含这段，也不含模型载入。",
        f"- 内存：构建前 RSS {cost['rss_before_kb']} KiB，构建后 RSS {cost['rss_after_kb']} KiB，进程峰值 HWM {cost['hwm_kb']} KiB。",
        f"- 查询 p95：混合 {cost['p95_ms']['hybrid']:.3f} ms，重排 {cost['p95_ms']['hybrid+rerank']:.3f} ms，词法 {cost['p95_ms']['bm25']:.3f} ms。门槛 800 ms。",
        f"- 新增依赖没有写进 `requirements.txt`。测量用 fastembed {payload['fastembed_version']}，包名：{', '.join(_req_names(cost['fastembed_requires']))}。完整版本约束在 `cost.json`。",
        f"- 补丁/失效：{cost['sync_note']}",
        "",
        "## 开关与回退",
        "",
        payload["smoke"]["steps_md"],
        "",
        "## 清单",
        "",
        f"- 路径：`docs/evidence/issue-284/CHECKLIST.md`",
        f"- 分差条数：词法 vs 混合 {payload['checklist_counts']['bm25_vs_hybrid']['n']}，"
        f"词法 vs 重排 {payload['checklist_counts']['bm25_vs_hybrid+rerank']['n']}，"
        f"混合 vs 重排 {payload['checklist_counts']['hybrid_vs_hybrid+rerank']['n']}。",
        "",
        "## 一句话建议",
        "",
        payload["recommendation_sentence"],
        "",
        "生产默认没有改。切换仍等真人终收。",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    if PRODUCTION_RETRIEVAL_MODE != "bm25":
        print("生产默认臂不是 bm25", file=sys.stderr)
        return 1
    before = PRODUCTION_RETRIEVAL_MODE
    questions_path = ROOT / "data/exp/x1/questions.json"
    corpus = ROOT / "data/exp/x1/corpus"
    traps = ROOT / "data/exp/x1/traps"
    config = ROOT / "data/exp/x1/config.json"
    checked = check_x1(corpus, traps, questions_path, config)
    if checked.exit_code != 0:
        print(checked.format_report(), file=sys.stderr)
        return checked.exit_code

    raw = json.loads(questions_path.read_text(encoding="utf-8"))
    queries = list(raw["queries"])
    gold_ids = {str(item["id"]) for item in queries}
    template = _template_ids(gold_ids)
    arm = [item for item in queries if (item.get("score_role") or "arm") == "arm"]

    rss_before, _ = _rss_kb()
    t0 = time.perf_counter()
    _model, embed = _local_embedder()
    model_load_s = time.perf_counter() - t0

    store = InMemoryStore()
    n_chunks = _ingest(store, corpus, traps)
    t1 = time.perf_counter()
    vectors = embed([chunk.text for chunk in store._chunks])
    index_build_s = time.perf_counter() - t1
    if len(vectors) != n_chunks or not vectors:
        raise SystemExit("语料向量构建失败")
    dim = len(vectors[0])
    for chunk, vec in zip(store._chunks, vectors):
        chunk.vec = pack_vec(vec)
    rss_after, hwm = _rss_kb()

    query_texts = list(dict.fromkeys(str(item.get("query", "")) for item in arm))
    t2 = time.perf_counter()
    query_vecs = {text: vec for text, vec in zip(query_texts, embed(query_texts))}
    query_embed_s = time.perf_counter() - t2
    store.query_embedder = lambda query: query_vecs[query]
    tokenize("预热")

    scored: list[dict[str, Any]] = []
    latencies: dict[str, list[float]] = {mode: [] for mode in MODES}
    for item in arm:
        relevant = [str(x) for x in (item.get("relevant") or [])]
        ranked: dict[str, list[str]] = {}
        recall: dict[str, float] = {}
        mrr: dict[str, float] = {}
        ndcg: dict[str, float] = {}
        for mode in MODES:
            store.bind_eval_retrieval_mode(None if mode == "bm25" else mode)
            started = time.perf_counter()
            hits = store.retrieve(str(item.get("query", "")), as_of=item.get("as_of"), top_k=TOP_K)
            elapsed = time.perf_counter() - started
            got = getattr(store, "last_retrieval_mode", None)
            if got != mode:
                print(f"模式不诚实 {item.get('id')} {mode} -> {got}", file=sys.stderr)
                return 1
            ids = [chunk_evidence_id(chunk) for chunk in hits]
            ranked[mode] = ids
            recall[mode] = recall_at_k(ids, relevant, TOP_K)
            mrr[mode] = mrr_at_k(ids, relevant, TOP_K)
            ndcg[mode] = _ndcg_at_k(ids, relevant, TOP_K)
            latencies[mode].append(elapsed)
        store.bind_eval_retrieval_mode(None)
        scored.append({
            "id": item["id"],
            "query": item.get("query", ""),
            "qtype": item.get("qtype"),
            "category": item.get("category"),
            "template47": item["id"] in template,
            "relevant": relevant,
            "answer_points": [str(x) for x in (item.get("answer_points") or [])],
            "ranked": ranked,
            "recall": recall,
            "mrr": mrr,
            "ndcg": ndcg,
        })

    p95 = {mode: _p95_ms(latencies[mode]) for mode in MODES}
    p95_ok = {mode: p95[mode] <= P95_BUDGET_MS for mode in MODES}

    rng = random.Random(BOOT_SEED)
    significance: dict[str, Any] = {}
    for left, right in PAIRS:
        significance[f"{left}_vs_{right}"] = _pair_recall_test(scored, left, right, rng)
    rank_metrics = []
    for left, right in (("bm25", "hybrid+rerank"), ("hybrid", "hybrid+rerank")):
        for key in ("mrr", "ndcg"):
            rank_metrics.append(_pair_metric_ci(scored, left, right, key, rng))

    items: list[dict[str, Any]] = []
    counts: dict[str, dict[str, int]] = {}
    for left, right in PAIRS:
        key = f"{left}_vs_{right}"
        bucket = {"n": 0, "保持 bm25": 0, "可议 hybrid": 0, "可议 hybrid+rerank": 0, "需要改题": 0}
        for row in scored:
            if not _differs(row["ranked"][left], row["ranked"][right]):
                continue
            suggestion, reason = _suggest(left, right, row["recall"], row["mrr"], p95_ok)
            bucket["n"] += 1
            bucket[suggestion] += 1
            items.append({
                "pair": key,
                "id": row["id"],
                "query": row["query"],
                "qtype": row["qtype"],
                "category": row["category"],
                "template47": row["template47"],
                "relevant": row["relevant"],
                "answer_points": row["answer_points"],
                "ranked": row["ranked"],
                "suggestion": suggestion,
                "reason": reason,
            })
        counts[key] = bucket

    # 端到端：eval 开关打开两臂，再一键回到 bm25。然后证明缺向量不会被标成 hybrid。
    sample = arm[0]
    runner = RunContext(store=store, mode="eval")
    smoke_modes: list[dict[str, Any]] = []
    for mode in ("hybrid", "hybrid+rerank", "bm25"):
        runner.arm_eval_retrieval_mode(mode)
        runner.try_retrieve(str(sample.get("query", "")), as_of=sample.get("as_of"), top_k=TOP_K)
        event = runner.events[-1]
        smoke_modes.append({
            "requested": mode,
            "retrieval_mode": event.get("retrieval_mode"),
            "hits": event.get("hits"),
        })
        if event.get("retrieval_mode") != mode:
            print(f"冒烟模式不对 {mode} -> {event.get('retrieval_mode')}", file=sys.stderr)
            return 1
    online = RunContext(store=store, mode="online")
    online_refused = False
    online_message = ""
    try:
        online.arm_eval_retrieval_mode("hybrid")
    except RuntimeError as exc:
        online_refused = True
        online_message = str(exc)
    online.try_retrieve(str(sample.get("query", "")), as_of=sample.get("as_of"), top_k=TOP_K)
    online_mode = online.events[-1].get("retrieval_mode")
    if not online_refused or online_mode != "bm25":
        print("生产路径没有拒绝切臂", file=sys.stderr)
        return 1

    victim = next(chunk for chunk in store._chunks if chunk.as_of == sample.get("as_of"))
    saved_vec = victim.vec
    victim.vec = None
    store.bind_eval_retrieval_mode("hybrid")
    store.retrieve(str(sample.get("query", "")), as_of=sample.get("as_of"), top_k=TOP_K)
    fallback_mode = getattr(store, "last_retrieval_mode", None)
    victim.vec = saved_vec
    store.bind_eval_retrieval_mode(None)
    if fallback_mode != "bm25_fallback":
        print(f"缺向量没有降级标记，得到 {fallback_mode}", file=sys.stderr)
        return 1
    store.bind_eval_retrieval_mode("hybrid")
    store.retrieve(str(sample.get("query", "")), as_of=sample.get("as_of"), top_k=TOP_K)
    restored = getattr(store, "last_retrieval_mode", None)
    store.bind_eval_retrieval_mode(None)
    if restored != "hybrid":
        print("恢复向量后没有回到 hybrid", file=sys.stderr)
        return 1

    sync_gap = True
    sync_note = (
        "解析入库（`parse_document_text` / `confirm_paste`）不计算向量，新块 `vec` 为空。"
        "`invalidation_list` 只记主张 id，不改块向量。"
        "再次 `add_document` 会把块上的 `vec` 原样写入；空向量会覆盖旧向量。"
        "池中只要有一块缺向量，`rank_dense` 返回空，检索记 `bm25_fallback`，不会把这次结果标成 hybrid。"
        "本次冒烟清掉一块向量后，请求 hybrid，记录为 bm25_fallback；写回向量后恢复为 hybrid。"
    )
    requires = list(importlib_metadata.requires("fastembed") or [])
    fastembed_version = importlib_metadata.version("fastembed")
    _rss, hwm = _rss_kb()
    after = PRODUCTION_RETRIEVAL_MODE
    if after != "bm25" or before != "bm25":
        print("生产默认臂被改动", file=sys.stderr)
        return 1
    if "freshlatch.store.embeddings" in sys.modules:
        print("embeddings 模块被加载", file=sys.stderr)
        return 1

    choice = _recommend(significance, p95_ok, sync_gap)
    sentence = _recommend_sentence(choice, significance, sync_gap, rank_metrics)
    steps_md = "\n".join([
        "回退步骤（本次冒烟已做完，可复做）：",
        "",
        "1. 只在 `RunContext.mode == \"eval\"` 时调用 `arm_eval_retrieval_mode`。",
        "2. `arm_eval_retrieval_mode(\"hybrid\")` 后 `try_retrieve`，轨迹 `retrieval_mode` 为 hybrid。",
        "3. `arm_eval_retrieval_mode(\"hybrid+rerank\")` 后同样为 hybrid+rerank。",
        "4. 一键回到词法：`arm_eval_retrieval_mode(\"bm25\")` 再查一次，轨迹为 bm25。",
        "5. `mode == \"online\"` 时 `arm_eval_retrieval_mode` 抛出「生产路径不可强制 retrieval_mode」，检索仍是 bm25。",
        "6. 不修改 `PRODUCTION_RETRIEVAL_MODE`。本次结束时它仍是 bm25。",
        "",
        "冒烟记录：",
        "",
        *[
            f"- 请求 {row['requested']} → 记录 {row['retrieval_mode']}，命中 {row['hits']} 条"
            for row in smoke_modes
        ],
        f"- 生产路径拒绝切臂：{online_message}",
        f"- 生产路径实际检索：{online_mode}",
        f"- 缺一块向量时请求 hybrid → {fallback_mode}；写回后 → {restored}",
    ])
    cost = {
        "model_load_s": model_load_s,
        "index_build_s": index_build_s,
        "query_embed_s": query_embed_s,
        "n_chunks": n_chunks,
        "n_queries": len(query_texts),
        "embed_dim": dim,
        "vec_bytes": n_chunks * dim * 4,
        "rss_before_kb": rss_before,
        "rss_after_kb": rss_after,
        "hwm_kb": hwm,
        "p95_ms": p95,
        "p95_ok": p95_ok,
        "fastembed_requires": requires,
        "sync_gap": sync_gap,
        "sync_note": sync_note,
        "requirements_txt_unchanged": True,
    }
    payload: dict[str, Any] = {
        "issue": 284,
        "pr": 283,
        "human_row_review": False,
        "checklist_is_human_review": False,
        "n_arm": len(arm),
        "n_guardrail": sum(1 for item in queries if item.get("score_role") == "guardrail"),
        "n_chunks": n_chunks,
        "embed_model": LOCAL_MODEL,
        "embed_dim": dim,
        "fastembed_version": fastembed_version,
        "mode_before": before,
        "mode_after": after,
        "check_exit": checked.exit_code,
        "dashscope_called": False,
        "significance": significance,
        "rank_metrics": rank_metrics,
        "cost": cost,
        "smoke": {
            "modes": smoke_modes,
            "online_refused": online_refused,
            "online_message": online_message,
            "online_mode": online_mode,
            "missing_vec_mode": fallback_mode,
            "restored_mode": restored,
            "steps_md": steps_md,
        },
        "checklist_counts": counts,
        "recommendation": choice,
        "recommendation_sentence": sentence,
        "method": {
            "n_boot": N_BOOT,
            "seed": BOOT_SEED,
            "p95_budget_ms": P95_BUDGET_MS,
        },
    }
    out = ROOT / "docs/evidence/issue-284"
    out.mkdir(parents=True, exist_ok=True)
    (out / "RESULT.md").write_text(_render_result(payload), encoding="utf-8")
    (out / "CHECKLIST.md").write_text(_render_checklist(items, counts), encoding="utf-8")
    (out / "significance.json").write_text(
        json.dumps({"significance": significance, "rank_metrics": rank_metrics}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "cost.json").write_text(json.dumps(cost, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    smoke_out = {k: v for k, v in payload["smoke"].items() if k != "steps_md"}
    (out / "smoke.json").write_text(json.dumps(smoke_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(sentence)
    print("counts", {key: counts[key]["n"] for key in counts})
    print("p95", {key: round(p95[key], 3) for key in p95})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
