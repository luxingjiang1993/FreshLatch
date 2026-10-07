"""PE-05：固定放行率下的误放率，以及配对 bootstrap。

四条随机流各自 ``random.Random(20261007)``：``coverage_c``、``bootstrap``、
``bootstrap_ablation``、``spotcheck``。本模块只推进前三条。抽检流由调用方保留。
跨 Python 3.11 与 3.12 只使用 ``Random.random()`` 自行取下标，避免全局随机状态。
"""

from __future__ import annotations

import math
import random
from collections.abc import Collection, Mapping, Sequence
from typing import Any

from freshlatch.evidence_id import parse_evidence_id
from freshlatch.eval.patch_events_exp import normalize_experiment_record

SEED = 20261007
N_BOOT = 10000
STREAM_NAMES = ("coverage_c", "bootstrap", "bootstrap_ablation", "spotcheck")
PRIMARY_CONTRASTS = ("C", "B1", "B2")
METRIC_ORDER = ("误放率", "误拒率", "错改率", "可复验率")
RELEASE_DENOMINATOR = frozenset({"误放率", "可复验率"})
ABLATION_ORDER = (
    "no_chunk_bind",
    "no_auto_verify",
    "soft_warning",
    "retrieval_bm25",
)


def format_rate(value: float | None) -> str:
    """无定义写成「无定义」。数字 0 只留给确实算出来的 0。"""
    if value is None:
        return "无定义"
    return format(value, ".16g")


def named_streams() -> dict[str, random.Random]:
    """四条独立随机流，种子相同，互不推进。"""
    return {name: random.Random(SEED) for name in STREAM_NAMES}


def _linear_percentile(ordered: Sequence[float], p: float) -> float:
    """线性插值百分位。``p`` 取 0.025 与 0.975 即 95% 区间。"""
    if not ordered:
        raise ValueError("空样本没有百分位")
    rank = (len(ordered) - 1) * p
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return float(ordered[lo])
    weight = rank - lo
    return float(ordered[lo] * (1.0 - weight) + ordered[hi] * weight)


def interval_from_draws(
    values: Sequence[float],
    *,
    dropped: int,
    n_boot: int = N_BOOT,
) -> dict[str, Any]:
    """丢弃比例超过 5% 则区间无定义。恰好 5% 仍只对保留下来的值取百分位。"""
    if n_boot <= 0:
        raise ValueError("n_boot 必须为正")
    kept = len(values)
    if kept + dropped != n_boot:
        raise ValueError("保留数加丢弃数必须等于 bootstrap 次数")
    if dropped * 20 > n_boot or kept == 0:
        return {
            "defined": False,
            "low": None,
            "high": None,
            "dropped": dropped,
            "kept": kept,
        }
    ordered = sorted(values)
    return {
        "defined": True,
        "low": _linear_percentile(ordered, 0.025),
        "high": _linear_percentile(ordered, 0.975),
        "dropped": dropped,
        "kept": kept,
    }


def _sample_positions(n: int, k: int, rng: random.Random) -> list[int]:
    """无放回取 k 个下标。k 为 0 或等于 n 时不消耗随机流。"""
    if k <= 0:
        return []
    if k >= n:
        return list(range(n))
    index = list(range(n))
    for i in range(k):
        j = i + int(rng.random() * (n - i))
        index[i], index[j] = index[j], index[i]
    return index[:k]


def _resample(n: int, rng: random.Random) -> list[int]:
    return [int(rng.random() * n) for _ in range(n)]


def _top_positions(
    drawn: Sequence[int],
    scores: Sequence[float | None],
    claim_ids: Sequence[str],
    k: int,
) -> list[int]:
    """``drawn`` 是重抽样后的总体下标。返回其中应放行的位置。"""
    n = len(drawn)
    if k <= 0:
        return []
    if k >= n:
        return list(range(n))

    def sort_key(pos: int) -> tuple[bool, float, str, int]:
        score = scores[drawn[pos]]
        missing = score is None
        return (missing, -(score if score is not None else 0.0), claim_ids[drawn[pos]], pos)

    order = sorted(range(n), key=sort_key)
    return order[:k]


def select_scored_positions(rows: Sequence[Mapping[str, Any]], k: int) -> list[int]:
    """分数从高到低，同分 ``claim_id`` 字典序在前，缺分数排在最后。"""
    scores = [row.get("score") for row in rows]
    claim_ids = [str(row["claim_id"]) for row in rows]
    return _top_positions(list(range(len(rows))), scores, claim_ids, k)


def _reverify_ok(row: Mapping[str, Any], ingested: set[str]) -> bool:
    evidence_id = row.get("evidence_id")
    if not isinstance(evidence_id, str) or evidence_id == "":
        return False
    parsed = parse_evidence_id(evidence_id)
    if parsed is None:
        return False
    doc_id, anchor, as_of = parsed
    if as_of != "T1":
        return False
    if f"{doc_id}#{anchor}@T1" not in ingested:
        return False
    return row.get("reverify_ok") is True


def _metric_on(
    metric: str,
    drawn: Sequence[int],
    selected: Sequence[int],
    bad: Sequence[bool],
    correct: Sequence[bool],
    reverify: Sequence[bool],
) -> float | None:
    n = len(drawn)
    releases = len(selected)
    if metric == "误放率":
        if releases == 0:
            return None
        return sum(bad[drawn[pos]] for pos in selected) / releases
    if metric == "可复验率":
        if releases == 0:
            return None
        return sum(reverify[drawn[pos]] for pos in selected) / releases
    if metric == "错改率":
        if n == 0:
            return None
        return sum(bad[drawn[pos]] for pos in selected) / n
    if metric == "误拒率":
        chosen = set(selected)
        total = 0
        rejected = 0
        for pos, src in enumerate(drawn):
            if correct[src]:
                total += 1
                if pos not in chosen:
                    rejected += 1
        if total == 0:
            return None
        return rejected / total
    raise ValueError(f"未知指标: {metric}")


class _Col:
    def __init__(self, rows: Sequence[Mapping[str, Any]], ingested: set[str]) -> None:
        ordered = sorted(rows, key=lambda row: row["claim_id"])
        claim_ids = [row["claim_id"] for row in ordered]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("同一臂的 claim_id 重复")
        self.rows = ordered
        self.claim_id = claim_ids
        self.bad = [row["construction_gold"] == "坏" for row in ordered]
        self.correct = [row["construction_gold"] == "正确" for row in ordered]
        self.release = [row.get("decision") == "release" for row in ordered]
        self.score = [row.get("score") for row in ordered]
        self.reverify = [_reverify_ok(row, ingested) for row in ordered]

    def __len__(self) -> int:
        return len(self.claim_id)


def _rates(
    col: _Col,
    drawn: Sequence[int],
    selected: Sequence[int],
) -> dict[str, Any]:
    rates: dict[str, Any] = {
        metric: _metric_on(metric, drawn, selected, col.bad, col.correct, col.reverify)
        for metric in METRIC_ORDER
    }
    n = len(drawn)
    releases = len(selected)
    rates["放行数"] = releases
    rates["放行率"] = releases / n
    return rates


def natural_rates(
    rows: Sequence[Mapping[str, Any]],
    *,
    ingested_t1: Collection[str] = (),
) -> dict[str, Any]:
    """按记录上的 decision 计算。放行数为 0 时误放率与可复验率是 None。"""
    if not rows:
        raise ValueError("候选数为 0")
    ingested = set(ingested_t1)
    n = len(rows)
    bad = [row.get("construction_gold") == "坏" for row in rows]
    correct = [row.get("construction_gold") == "正确" for row in rows]
    selected = [i for i, row in enumerate(rows) if row.get("decision") == "release"]
    reverify = [_reverify_ok(row, ingested) for row in rows]
    drawn = list(range(n))
    rates = {
        metric: _metric_on(metric, drawn, selected, bad, correct, reverify)
        for metric in METRIC_ORDER
    }
    rates["放行数"] = len(selected)
    rates["放行率"] = len(selected) / n
    return rates


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _side_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    latencies = [float(row["latency_ms"]) for row in rows if _is_number(row.get("latency_ms"))]
    if latencies:
        latencies.sort()
        median = _linear_percentile(latencies, 0.50)
        p95 = _linear_percentile(latencies, 0.95)
    else:
        median = None
        p95 = None
    costs = [float(row["cost"]) for row in rows if _is_number(row.get("cost"))]
    if any(cost > 0 for cost in costs):
        return {
            "latency_median": median,
            "latency_p95": p95,
            "cost": float(sum(costs)),
            "cost_note": "",
        }
    return {
        "latency_median": median,
        "latency_p95": p95,
        "cost": 0,
        "cost_note": "没有调用",
    }


def _arm_block(col: _Col, selected: Sequence[int], k: int) -> dict[str, Any]:
    drawn = list(range(len(col)))
    natural_selected = [i for i, flag in enumerate(col.release) if flag]
    fixed = _rates(col, drawn, selected)
    fixed["k"] = k
    block = _side_report(col.rows)
    block["natural"] = _rates(col, drawn, natural_selected)
    block["fixed"] = fixed
    return block


def _bootstrap_fixed(
    metric: str,
    left: _Col,
    right: _Col,
    *,
    contrast_is_c: bool,
    rng: random.Random,
) -> dict[str, Any]:
    n = len(left)
    values: list[float] = []
    dropped = 0
    for _ in range(N_BOOT):
        drawn = _resample(n, rng)
        k = sum(left.release[src] for src in drawn)
        if k == 0 and metric in RELEASE_DENOMINATOR:
            dropped += 1
            continue
        left_selected = _top_positions(drawn, left.score, left.claim_id, k)
        if contrast_is_c:
            right_selected = _sample_positions(n, k, rng)
        else:
            right_selected = _top_positions(drawn, right.score, right.claim_id, k)
        left_value = _metric_on(metric, drawn, left_selected, left.bad, left.correct, left.reverify)
        right_value = _metric_on(
            metric, drawn, right_selected, right.bad, right.correct, right.reverify
        )
        if left_value is None or right_value is None:
            dropped += 1
            continue
        values.append(right_value - left_value)
    return interval_from_draws(values, dropped=dropped)


def _aligned(rows: Sequence[Mapping[str, Any]], ingested: set[str]) -> dict[str, _Col]:
    grouped: dict[str, list[Mapping[str, Any]]] = {arm: [] for arm in ("C", "T", "B1", "B2")}
    for row in rows:
        if row.get("ablation", "") != "":
            continue
        arm = row["arm"]
        if arm not in grouped:
            raise ValueError(f"arm 非法: {arm!r}")
        grouped[arm].append(row)
    missing = [arm for arm, items in grouped.items() if not items]
    if missing:
        raise ValueError(f"主比较缺臂: {', '.join(missing)}")
    columns = {arm: _Col(items, ingested) for arm, items in grouped.items()}
    reference = columns["T"].claim_id
    for arm in PRIMARY_CONTRASTS:
        if columns[arm].claim_id != reference:
            raise ValueError(f"{arm} 的候选 id 与 T 不一致")
    return columns


def compare_primary(
    rows: Sequence[Mapping[str, Any]],
    *,
    ingested_t1: Collection[str] = (),
    streams: Mapping[str, random.Random] | None = None,
) -> dict[str, Any]:
    """三条主比较。成立只看固定放行率误放率的点估计和区间下界。"""
    rngs = streams if streams is not None else named_streams()
    coverage = rngs["coverage_c"]
    bootstrap = rngs["bootstrap"]
    ingested = set(ingested_t1)
    normalized = [normalize_experiment_record(row) for row in rows]
    columns = _aligned(normalized, ingested)
    reference = columns["T"]
    n = len(reference)
    if n == 0:
        raise ValueError("候选数为 0")
    k = sum(reference.release)
    drawn = list(range(n))
    selected: dict[str, list[int]] = {}
    for arm, col in columns.items():
        if arm == "C":
            selected[arm] = _sample_positions(n, k, coverage)
        else:
            selected[arm] = _top_positions(drawn, col.score, col.claim_id, k)
    arms = {arm: _arm_block(col, selected[arm], k) for arm, col in columns.items()}
    comparisons = []
    for order, contrast in enumerate(PRIMARY_CONTRASTS, start=1):
        intervals = {
            metric: _bootstrap_fixed(
                metric,
                reference,
                columns[contrast],
                contrast_is_c=contrast == "C",
                rng=bootstrap,
            )
            for metric in METRIC_ORDER
        }
        false_release = intervals["误放率"]
        left_rate = arms["T"]["fixed"]["误放率"]
        right_rate = arms[contrast]["fixed"]["误放率"]
        if left_rate is None or right_rate is None:
            point = None
        else:
            point = right_rate - left_rate
        low = false_release["low"]
        established = (
            point is not None
            and point > 0
            and false_release["defined"]
            and low is not None
            and low > 0
        )
        comparisons.append(
            {
                "order": order,
                "name": f"T-{contrast}",
                "point": point,
                "ci95_low": low,
                "ci95_high": false_release["high"],
                "established": established,
                "intervals": intervals,
            }
        )
    return {"k": k, "arms": arms, "comparisons": comparisons}


def _bootstrap_natural(
    metric: str,
    left: _Col,
    right: _Col,
    rng: random.Random,
) -> dict[str, Any]:
    n = len(left)
    values: list[float] = []
    dropped = 0
    for _ in range(N_BOOT):
        drawn = _resample(n, rng)
        left_selected = [pos for pos, src in enumerate(drawn) if left.release[src]]
        right_selected = [pos for pos, src in enumerate(drawn) if right.release[src]]
        left_value = _metric_on(metric, drawn, left_selected, left.bad, left.correct, left.reverify)
        right_value = _metric_on(
            metric, drawn, right_selected, right.bad, right.correct, right.reverify
        )
        if left_value is None or right_value is None:
            dropped += 1
            continue
        values.append(right_value - left_value)
    return interval_from_draws(values, dropped=dropped)


def _point_natural(metric: str, left: _Col, right: _Col) -> float | None:
    drawn = list(range(len(left)))
    left_selected = [pos for pos, flag in enumerate(left.release) if flag]
    right_selected = [pos for pos, flag in enumerate(right.release) if flag]
    left_value = _metric_on(metric, drawn, left_selected, left.bad, left.correct, left.reverify)
    right_value = _metric_on(metric, drawn, right_selected, right.bad, right.correct, right.reverify)
    if left_value is None or right_value is None:
        return None
    return right_value - left_value


def ablation_intervals(
    rows: Sequence[Mapping[str, Any]],
    *,
    ingested_t1: Collection[str] = (),
    rng: random.Random,
) -> list[dict[str, Any]]:
    """消融按自然放行规则报区间，只消耗调用方传入的那条随机流。"""
    ingested = set(ingested_t1)
    normalized = [normalize_experiment_record(row) for row in rows]
    main_rows = [row for row in normalized if row["arm"] == "T" and row["ablation"] == ""]
    if not main_rows:
        raise ValueError("消融对照缺主 T")
    main = _Col(main_rows, ingested)
    by_tag: dict[str, list[Mapping[str, Any]]] = {}
    for row in normalized:
        if row["ablation"] == "":
            continue
        by_tag.setdefault(row["ablation"], []).append(row)
    reports = []
    for tag in ABLATION_ORDER:
        tagged = by_tag.get(tag)
        if not tagged:
            continue
        column = _Col(tagged, ingested)
        if column.claim_id != main.claim_id:
            raise ValueError(f"{tag} 的候选 id 与主 T 不一致")
        intervals = {
            metric: _bootstrap_natural(metric, main, column, rng) for metric in METRIC_ORDER
        }
        reports.append(
            {
                "ablation": tag,
                "reference": "T",
                "participates": False,
                "point": {metric: _point_natural(metric, main, column) for metric in METRIC_ORDER},
                "intervals": intervals,
            }
        )
    return reports
