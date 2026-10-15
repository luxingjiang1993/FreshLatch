"""发车检查单上的成本/延迟硬门（A-P5）。

相对调用方给出的基线：成本达到或超过 1.5 倍，或 e2e P95 超过调用方给出的
SLA，检查单记发车红。基线与 SLA 没有默认数。1.5 是检查单倍数，不是 SESOI，
也不是质量分。

e2e P95 可以读 A-P3 ``measure_primary_sli`` 的 ``e2e_p95_ms``。
``abstain_rate`` 与 ``retrieval_fallback_rate`` 只随行抄录，不参与红绿。
本模块不给这两率发明阈值。

成本不伪装质量。``cost_is_quality`` 与 ``counted_as_pass`` 恒为 false。
不写 RESULT-Y，不改 floors / gold / x1 / ``PRODUCTION_RETRIEVAL_MODE``。
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from freshlatch.eval.trajectory_sli import (
    PLACEHOLDER_INSUFFICIENT,
    PLACEHOLDER_UNMEASURED,
)
from freshlatch.sli.alert import SliWindow, measure_primary_sli

COST_FACTOR = Decimal("1.5")
COST_FACTOR_TEXT = "1.5"
RELEASE_GATE_ENV = "FRESHLATCH_RELEASE_GATE"

CHECKLIST_ITEM = "热路径：成本低于调用方基线的 1.5 倍，且 e2e P95 不超过调用方 SLA"
CHECKLIST_RED = "发车红"
CHECKLIST_GREEN = "发车绿"
CHECKLIST_OFF = "关闸"

VERDICT_FAIL = "fail"
VERDICT_PASS = "pass"

REASON_COST = "cost_over_baseline"
REASON_LATENCY = "e2e_p95_over_sla"
REASON_UNMEASURED = "e2e_p95_unmeasured"

NOTES = (
    "成本不伪装质量。"
    "1.5 倍是发车检查单相对基线的硬门，不是 SESOI，不是质量分。"
    "SLA 与基线由调用方传入。"
    "e2e_p95_ms 与 abstain/fallback 率来自主 SLI 时只读抄录；两率不参与红绿。"
    "未测的 P95 不能当成未超 SLA。"
    "不写 RESULT-Y。"
)

_UNMEASURED = frozenset({PLACEHOLDER_INSUFFICIENT, PLACEHOLDER_UNMEASURED})
_RATE_KEYS = (
    "abstain_rate",
    "retrieval_fallback_rate",
    "abstain_fallback_rate",
)


@dataclass(frozen=True)
class ReleaseGateDecision:
    """一次发车检查。``verdict`` 是预算判定，关闸不改写它。

    ``blocked`` 才表示拦住发车。``FRESHLATCH_RELEASE_GATE=off`` 时
    ``blocked`` 为 false，``checklist`` 为「关闸」。
    """

    verdict: str
    checklist: str
    blocked: bool
    raw_fail: bool
    suppressed: bool
    reasons: tuple[str, ...]
    cost_ratio: str
    baseline_cost: int | float
    observed_cost: int | float
    sla_e2e_p95_ms: int | float
    e2e_p95_ms: int | float | str
    latency_source: str
    abstain_rate: str | None
    retrieval_fallback_rate: str | None
    abstain_fallback_rate: str | None
    cost_factor: str
    cost_is_quality: bool
    counted_as_pass: bool
    invents_sesoi: bool
    writes_result_y: bool
    notes: str


def check_release_gate(
    *,
    baseline_cost: int | float,
    observed_cost: int | float,
    sla_e2e_p95_ms: int | float,
    e2e_p95_ms: int | float | str | None = None,
    sli: Mapping[str, Any] | None = None,
    window: SliWindow | None = None,
    environ: Mapping[str, str] | None = None,
) -> ReleaseGateDecision:
    """对照调用方基线与 SLA，给出发车检查单颜色。

    延迟来源只能是 ``window``、``sli``、``e2e_p95_ms`` 三者之一。
    ``window`` 会调用 ``measure_primary_sli``。夹具目录会被拒绝。
    ``sli`` 读取已落下的主 SLI 字段，至少要有 ``e2e_p95_ms``。
    """
    baseline = _require_number("baseline_cost", baseline_cost, positive=True)
    observed = _require_number("observed_cost", observed_cost, positive=False)
    sla = _require_number("sla_e2e_p95_ms", sla_e2e_p95_ms, positive=True)
    reading, rates, source = _latency(e2e_p95_ms=e2e_p95_ms, sli=sli, window=window)
    e2e_number = _e2e_number(reading)

    reasons: list[str] = []
    ratio = observed / baseline
    if ratio >= COST_FACTOR:
        reasons.append(REASON_COST)
    if e2e_number is None:
        reasons.append(REASON_UNMEASURED)
    elif e2e_number > sla:
        reasons.append(REASON_LATENCY)

    raw_fail = bool(reasons)
    suppressed = _suppressed(environ)
    if suppressed:
        checklist = CHECKLIST_OFF
        blocked = False
    elif raw_fail:
        checklist = CHECKLIST_RED
        blocked = True
    else:
        checklist = CHECKLIST_GREEN
        blocked = False

    abstain, fallback, combined = rates
    return ReleaseGateDecision(
        verdict=VERDICT_FAIL if raw_fail else VERDICT_PASS,
        checklist=checklist,
        blocked=blocked,
        raw_fail=raw_fail,
        suppressed=suppressed,
        reasons=tuple(reasons),
        cost_ratio=_ratio_text(ratio),
        baseline_cost=baseline_cost,
        observed_cost=observed_cost,
        sla_e2e_p95_ms=sla_e2e_p95_ms,
        e2e_p95_ms=reading if isinstance(reading, (int, float, str)) else str(reading),
        latency_source=source,
        abstain_rate=abstain,
        retrieval_fallback_rate=fallback,
        abstain_fallback_rate=combined,
        cost_factor=COST_FACTOR_TEXT,
        cost_is_quality=False,
        counted_as_pass=False,
        invents_sesoi=False,
        writes_result_y=False,
        notes=NOTES,
    )


def format_release_gate(decision: ReleaseGateDecision) -> str:
    """一行检查单记录。成本不写成质量分。"""
    reasons = ",".join(decision.reasons) if decision.reasons else "none"
    abstain = decision.abstain_rate if decision.abstain_rate is not None else "-"
    fallback = (
        decision.retrieval_fallback_rate
        if decision.retrieval_fallback_rate is not None
        else "-"
    )
    return (
        f"release_gate checklist={decision.checklist} verdict={decision.verdict} "
        f"blocked={str(decision.blocked).lower()} "
        f"suppressed={str(decision.suppressed).lower()} "
        f"reasons={reasons} cost_ratio={decision.cost_ratio} "
        f"cost_factor={decision.cost_factor} "
        f"baseline_cost={decision.baseline_cost} "
        f"observed_cost={decision.observed_cost} "
        f"e2e_p95_ms={decision.e2e_p95_ms} "
        f"sla_e2e_p95_ms={decision.sla_e2e_p95_ms} "
        f"abstain_rate={abstain} retrieval_fallback_rate={fallback} "
        f"latency_source={decision.latency_source} "
        f"cost_is_quality=false counted_as_pass=false "
        f"invents_sesoi=false writes_result_y=false "
        f"notes={decision.notes}"
    )


def _latency(
    *,
    e2e_p95_ms: int | float | str | None,
    sli: Mapping[str, Any] | None,
    window: SliWindow | None,
) -> tuple[int | float | str, tuple[str | None, str | None, str | None], str]:
    chosen = sum(
        (
            window is not None,
            sli is not None,
            e2e_p95_ms is not None,
        )
    )
    if chosen != 1:
        raise ValueError("延迟来源只能是 window、sli、e2e_p95_ms 之一")
    if window is not None:
        if isinstance(window, (str, os.PathLike)):
            raise TypeError("发车硬门不接受夹具目录。请传入 SliWindow 或主 SLI")
        row = measure_primary_sli(window)
        return row["e2e_p95_ms"], _rates_from_mapping(row), "window"
    if sli is not None:
        if isinstance(sli, (str, os.PathLike)):
            raise TypeError("发车硬门不接受夹具目录。请传入 SliWindow 或主 SLI")
        reading, rates = _from_sli(sli)
        return reading, rates, "sli"
    assert e2e_p95_ms is not None
    return e2e_p95_ms, (None, None, None), "e2e_p95_ms"


def _from_sli(
    sli: Mapping[str, Any],
) -> tuple[int | float | str, tuple[str | None, str | None, str | None]]:
    if not isinstance(sli, Mapping):
        raise TypeError("sli 必须是主 SLI 映射")
    if "e2e_p95_ms" not in sli:
        raise ValueError("主 SLI 缺少 e2e_p95_ms")
    return sli["e2e_p95_ms"], _rates_from_mapping(sli)


def _rates_from_mapping(
    row: Mapping[str, Any],
) -> tuple[str | None, str | None, str | None]:
    present: list[str | None] = []
    for key in _RATE_KEYS:
        if key not in row or row[key] is None:
            present.append(None)
            continue
        value = row[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"主 SLI 的 {key} 必须是非空字符串")
        present.append(value)
    abstain, fallback, combined = present
    if combined is None:
        combined = _combine_rates(abstain, fallback)
    return abstain, fallback, combined


def _combine_rates(abstain: str | None, fallback: str | None) -> str | None:
    if abstain is None or fallback is None:
        return None
    if abstain == PLACEHOLDER_INSUFFICIENT and fallback == PLACEHOLDER_INSUFFICIENT:
        return PLACEHOLDER_INSUFFICIENT
    return f"abstain={abstain}; fallback={fallback}"


def _e2e_number(reading: object) -> Decimal | None:
    if isinstance(reading, str):
        if reading in _UNMEASURED:
            return None
        raise ValueError(
            "e2e_p95_ms 只能是毫秒数，或主 SLI 占位「样本不足」「未计」"
        )
    if isinstance(reading, bool) or not isinstance(reading, (int, float)):
        raise ValueError(
            "e2e_p95_ms 只能是毫秒数，或主 SLI 占位「样本不足」「未计」"
        )
    if isinstance(reading, float) and not _finite(reading):
        raise ValueError("e2e_p95_ms 必须是有限毫秒数")
    number = Decimal(str(reading))
    if number < 0:
        raise ValueError("e2e_p95_ms 不能为负")
    return number


def _require_number(name: str, value: object, *, positive: bool) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} 必须由调用方传入，且为有限数；本模块不预设这个数")
    if isinstance(value, float) and not _finite(value):
        raise ValueError(f"{name} 必须由调用方传入，且为有限数；本模块不预设这个数")
    number = Decimal(str(value))
    if positive and number <= 0:
        raise ValueError(f"{name} 必须由调用方传入，且大于 0；本模块不预设这个数")
    if number < 0:
        raise ValueError(f"{name} 不能为负")
    return number


def _suppressed(environ: Mapping[str, str] | None) -> bool:
    env = os.environ if environ is None else environ
    if RELEASE_GATE_ENV not in env:
        return False
    raw = env.get(RELEASE_GATE_ENV)
    text = "" if raw is None else str(raw).strip().lower()
    if text in {"", "on"}:
        return False
    if text == "off":
        return True
    raise ValueError("FRESHLATCH_RELEASE_GATE 只接受 on 或 off")


def _ratio_text(ratio: Decimal) -> str:
    text = format(ratio, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _finite(value: float) -> bool:
    return value == value and value not in {float("inf"), float("-inf")}
