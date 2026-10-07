"""神经 rerank 对照的纯函数。不下载权重，不改生产默认臂。

口径锁在 ``docs/evidence/neural-rerank/PREREG.md``。这里只实现那一页已经写死的计算。
"""

from __future__ import annotations

import math
import random

from freshlatch.eval.retrieve_eval import _p95_ms, mrr_at_k, ndcg_at_k, recall_at_k

N_BOOT = 10000
BOOT_SEED = 20261007
P95_BUDGET_MS = 800.0
NDCG_MIN_ESTIMATE = 0.01
TOP_K = 10
KEEP_LEXICAL = "保持 lexical rerank，等大语料复测"
SUGGEST_TICKET = "建议另开切换票"


def order_by_scores(ids: list[str], scores: list[float]) -> list[str]:
    """分数高的在前。分数相同则保持输入顺序。"""
    if len(ids) != len(scores):
        raise ValueError(f"分数条数 {len(scores)} 与候选 {len(ids)} 不一致")
    order = sorted(range(len(ids)), key=lambda i: (-float(scores[i]), i))
    return [ids[i] for i in order]


def ranking_metrics(ranked: list[str], relevant: list[str], k: int = TOP_K) -> dict[str, float]:
    head = list(ranked[:k])
    return {
        "recall": recall_at_k(head, relevant, k),
        "mrr": mrr_at_k(head, relevant, k),
        "ndcg": ndcg_at_k(head, relevant, k),
    }


def same_id_set(left: list[str], right: list[str]) -> bool:
    return set(left) == set(right)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _percentile(sorted_xs: list[float], p: float) -> float:
    """线性插值百分位。与 #285 的 ``_percentile`` 同一公式。"""
    if not sorted_xs:
        return 0.0
    k = (len(sorted_xs) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_xs[lo]
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (k - lo)


def _binom_cdf_half(n: int, k: int) -> float:
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


def mcnemar_p(left_only: int, right_only: int) -> float:
    n = left_only + right_only
    if n == 0:
        return 1.0
    return min(1.0, 2.0 * _binom_cdf_half(n, min(left_only, right_only)))


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


def pair_metric(
    rows: list[dict[str, float]],
    *,
    key: str,
    rng: random.Random,
) -> dict[str, float]:
    """配对差 = 右（neural）− 左（lexical）。``rows`` 每项含 lexical / neural。"""
    diffs = [row["neural"][key] - row["lexical"][key] for row in rows]
    ci = _boot_ci(diffs, rng)
    return {
        "left_mean": _mean([row["lexical"][key] for row in rows]),
        "right_mean": _mean([row["neural"][key] for row in rows]),
        **ci,
    }


def pair_recall(rows: list[dict[str, float]], rng: random.Random) -> dict[str, object]:
    stats = pair_metric(rows, key="recall", rng=rng)
    left_only = sum(1 for row in rows if row["lexical"]["recall"] == 1.0 and row["neural"]["recall"] == 0.0)
    right_only = sum(1 for row in rows if row["lexical"]["recall"] == 0.0 and row["neural"]["recall"] == 1.0)
    both = sum(1 for row in rows if row["lexical"]["recall"] == 1.0 and row["neural"]["recall"] == 1.0)
    neither = sum(1 for row in rows if row["lexical"]["recall"] == 0.0 and row["neural"]["recall"] == 0.0)
    stats["mcnemar"] = {
        "left_only": left_only,
        "right_only": right_only,
        "both_hit": both,
        "neither": neither,
        "p_two_sided": mcnemar_p(left_only, right_only),
    }
    return stats


def recommend_neural_rerank(
    *,
    ndcg_estimate: float,
    ndcg_ci_low: float,
    mrr_ci_low: float,
    p95_ms: float,
) -> str:
    """K=10、bge-reranker-base 的取舍句。条件写在 PREREG，这里不另加。"""
    if (
        ndcg_ci_low > 0.0
        and ndcg_estimate >= NDCG_MIN_ESTIMATE
        and mrr_ci_low > 0.0
        and p95_ms <= P95_BUDGET_MS
    ):
        return SUGGEST_TICKET
    return KEEP_LEXICAL


def p95_ms(samples_s: list[float]) -> float:
    return _p95_ms(samples_s)


def unique_bytes_matching(roots: list[object], needle: str) -> int | None:
    """路径里含 needle 的文件按 inode 加总。同一根目录和符号链接只算一次。"""
    from pathlib import Path

    seen_roots: set[Path] = set()
    seen_inodes: set[tuple[int, int]] = set()
    total = 0
    found = False
    for raw in roots:
        if not raw:
            continue
        root = Path(str(raw)).resolve()
        if root in seen_roots or not root.is_dir():
            continue
        seen_roots.add(root)
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if needle not in str(path).lower():
                continue
            try:
                st = path.stat()
            except OSError:
                continue
            key = (st.st_dev, st.st_ino)
            if key in seen_inodes:
                continue
            seen_inodes.add(key)
            total += st.st_size
            found = True
    return total if found else None
