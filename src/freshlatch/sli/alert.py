"""主 SLI 窗口与 multiwindow burn-rate page（A-P3）。

观测窗是内存里的轨迹事件和/或 A-P1 ``canary_event``。
``measure_primary_sli`` 不接受夹具目录。目录聚合仍走
``trajectory_sli`` / ``product_sli``，本模块调用它们的内存入口，不另写计数。

主 SLI 三格：``e2e_p95_ms``、``abstain_rate``、``retrieval_fallback_rate``。
``abstain_fallback_rate`` 把后两格写在同一句里。
这是观测。``counted_as_pass`` 恒为 false。不写 RESULT-Y，不发明 SESOI，
不改 floors / gold / x1 / ``PRODUCTION_RETRIEVAL_MODE``。

burn-rate 的允许坏率由调用方传入，本模块没有默认数。
倍数来自 SRE Workbook《Alerting on SLOs》的 multiwindow multi-burn-rate
（按 30 天预算折算的告警策略），不是效应量，也不是注册通过线。

协议页 alone 不算 Done。可调用的 page 路径是 ``dispatch_page``。
webhook / email 的真实外发由调用方注入的 sender 完成；本模块不联网。
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

from freshlatch.canary import CanarySample, sample_breached
from freshlatch.eval.product_sli import (
    OBSERVATION_MARK,
    aggregate_product_runs,
)
from freshlatch.eval.trajectory_sli import (
    PLACEHOLDER_INSUFFICIENT,
    aggregate_trajectory_runs,
)

ONCALL_ROLE = "生产路径值班"
ONCALL_COVERAGE = "非 24×7"
ONCALL_HOURS = "Asia/Shanghai 工作日 09:00–18:00"
PROTOCOL_ONLY_NOT_DONE = "协议页 alone 不算 Done"
NOT_DONE = "NOT Done"
PAGE_PATH = "freshlatch.sli.alert.dispatch_page"
PAGE_SINK_ENV = "FRESHLATCH_PAGE_SINK"
TICKET_RESPOND_BY = "next_business_day"

# 30 天预算上的 multiwindow multi-burn-rate。短窗与长窗必须同时超过倍数。
# 14.4 = 1 小时烧掉预算的 2%；6 = 6 小时烧掉 5%；3 = 1 天烧掉 10%；1 = 3 天烧掉 10%。
_PAGE_FAST = 14.4
_PAGE_SLOW = 6.0
_TICKET_FAST = 3.0
_TICKET_SLOW = 1.0

WINDOW_DURATIONS: dict[str, timedelta] = {
    "5m": timedelta(minutes=5),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "2h": timedelta(hours=2),
    "6h": timedelta(hours=6),
    "1d": timedelta(days=1),
    "3d": timedelta(days=3),
}

_MISSING_DISPATCH = object()


class PagePathError(RuntimeError):
    """破线需要 page，但没有可调用的 sender。协议页 alone 不算 Done。"""


class PrimarySli(TypedDict):
    """一窗主 SLI。比率与占位都是字符串，避免把未计写成 0。"""

    window: str
    e2e_p95_ms: int | float | str
    abstain_rate: str
    retrieval_fallback_rate: str
    abstain_fallback_rate: str
    abstain_numerator: int
    abstain_denominator: int
    fallback_n: int
    N_retrieve: int
    N_request_ok: int
    canary_event_n: int
    canary_sample_n: int
    canary_bad_n: int
    sources: str
    notes: str
    counted_as_pass: bool
    invents_sesoi: bool
    writes_result_y: bool


@dataclass(frozen=True)
class SliWindow:
    """一个观测窗。轨迹与 canary_event 都在内存里，不指向夹具目录。"""

    label: str
    trajectory_runs: tuple[tuple[dict[str, Any], ...], ...]
    canary_events: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class BurnRule:
    """一对长短窗。两窗都超过 ``factor`` 才算这条规则破线。"""

    severity: str
    long_window: str
    short_window: str
    factor: float

    @property
    def rule_id(self) -> str:
        return (
            f"{self.severity}:{self.long_window}+{self.short_window}"
            f">{format(self.factor, 'g')}"
        )


BURN_RULES: tuple[BurnRule, ...] = (
    BurnRule("page", "1h", "5m", _PAGE_FAST),
    BurnRule("page", "6h", "30m", _PAGE_SLOW),
    BurnRule("ticket", "1d", "2h", _TICKET_FAST),
    BurnRule("ticket", "3d", "6h", _TICKET_SLOW),
)


@dataclass(frozen=True)
class BreachDecision:
    """multiwindow 判定。page 与 ticket 可以同时为真。"""

    page: bool
    ticket: bool
    page_rules: tuple[str, ...]
    ticket_rules: tuple[str, ...]


class PageSender:
    """webhook 或 email 的外发口。调用方注入；测试用记录器即可。"""

    def send(self, payload: Mapping[str, Any]) -> None:
        raise NotImplementedError


class RecordingSender:
    """不联网。``send`` 把 payload 记下来，供测试或调用方核对。"""

    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    def send(self, payload: Mapping[str, Any]) -> None:
        self.payloads.append(dict(payload))


def make_window(
    *,
    label: str,
    trajectory_runs: Sequence[Sequence[Mapping[str, Any]]] | None = None,
    canary_events: Sequence[Mapping[str, Any]] | None = None,
) -> SliWindow:
    """组装观测窗。至少要有轨迹或 ``canary_event`` 之一。"""
    text = label.strip() if isinstance(label, str) else ""
    if not text:
        raise ValueError("窗口标签为空")
    runs_in = () if trajectory_runs is None else trajectory_runs
    events_in = () if canary_events is None else canary_events
    runs: list[tuple[dict[str, Any], ...]] = []
    for run in runs_in:
        runs.append(_copy_run(run))
    events: list[dict[str, Any]] = []
    for event in events_in:
        copied = _copy_event(event)
        if copied.get("event") != "canary_event":
            raise ValueError("canary 事件的 event 必须是 canary_event")
        events.append(copied)
    if not runs and not events:
        raise ValueError("窗口没有轨迹事件，也没有 canary_event")
    return SliWindow(label=text, trajectory_runs=tuple(runs), canary_events=tuple(events))


def measure_primary_sli(window: SliWindow) -> PrimarySli:
    """从轨迹 / canary 窗口落下 e2e P95 与 abstain/fallback 率。

    传入目录路径会拒绝。夹具目录不是这个入口。
    """
    if isinstance(window, (str, os.PathLike)):
        raise TypeError(
            "主 SLI 不接受夹具目录。请传入轨迹事件或 canary_event 组成的 SliWindow"
        )
    if not isinstance(window, SliWindow):
        raise TypeError("主 SLI 只接受 SliWindow")

    named = _trajectory_runs(window)
    latency = aggregate_trajectory_runs(
        [list(events) for _name, events in named],
        window=window.label,
    )
    product_rows = aggregate_product_runs(named, window=window.label)
    abstain = _metric_row(product_rows, "abstain")
    sample_n, bad_n = _canary_counts(window.canary_events)
    abstain_rate = abstain["value"]
    fallback_rate = latency["retrieval_fallback_rate"]
    sources = _sources(window)
    return PrimarySli(
        window=window.label,
        e2e_p95_ms=latency["e2e_p95_ms"],
        abstain_rate=abstain_rate,
        retrieval_fallback_rate=fallback_rate,
        abstain_fallback_rate=_abstain_fallback_rate(abstain_rate, fallback_rate),
        abstain_numerator=abstain["numerator"],
        abstain_denominator=abstain["denominator"],
        fallback_n=latency["fallback_n"],
        N_retrieve=latency["N_retrieve"],
        N_request_ok=latency["N_request_ok"],
        canary_event_n=len(window.canary_events),
        canary_sample_n=sample_n,
        canary_bad_n=bad_n,
        sources=sources,
        notes=_notes(sources),
        counted_as_pass=False,
        invents_sesoi=False,
        writes_result_y=False,
    )


def canary_sample_bad(event: Mapping[str, Any]) -> bool | None:
    """一条 ``canary_event`` 是否为坏样本。

    返回 None 表示这不是对照样本（例如 mode off），不进 burn 分母。
    坏的判定调用 A-P1 的 ``sample_breached``：``failed`` 或 ``value > halt_above``。
    """
    if event.get("event") != "canary_event":
        raise ValueError("不是 canary_event")
    failed = event.get("failed")
    if failed is not None and not isinstance(failed, bool):
        raise ValueError("canary_event.failed 必须是布尔或空")
    value = event.get("value")
    halt = event.get("halt_above")
    has_line = value is not None and halt is not None
    if failed is None and not has_line:
        return None
    metric = event.get("metric") or "error"
    if not str(metric).strip():
        raise ValueError("canary_event.metric 为空")
    sample = CanarySample(
        failed=False if failed is None else failed,
        metric=str(metric),
        value=None if value is None else float(value),
        halt_above=None if halt is None else float(halt),
    )
    return sample_breached(sample)


def burn_windows_from_canary_events(
    events: Sequence[Mapping[str, Any]],
    *,
    now: datetime,
) -> dict[str, tuple[int, int]]:
    """把 ``canary_event`` 按 ``ts`` 放进 5m/30m/1h/2h/6h/1d/3d。

    每个窗口的值是 ``(bad, total)``。非样本不进该窗。
    ``ts`` 落在 ``[now - 窗长, now]`` 内才计入。未来事件不计入。
    """
    instant = _require_now(now)
    samples: list[tuple[datetime, bool]] = []
    for event in events:
        if event.get("event") != "canary_event":
            raise ValueError("不是 canary_event")
        bad = canary_sample_bad(event)
        if bad is None:
            continue
        samples.append((_parse_ts(event.get("ts")), bad))
    windows: dict[str, tuple[int, int]] = {}
    for name, span in WINDOW_DURATIONS.items():
        start = instant - span
        chosen = [bad for ts, bad in samples if start <= ts <= instant]
        windows[name] = (sum(1 for bad in chosen if bad), len(chosen))
    return windows


def multiwindow_breach(
    windows: Mapping[str, tuple[int, int]],
    *,
    objective: float,
) -> BreachDecision:
    """长短窗同时超过倍数才破线。缺一窗、或该窗 total 为 0，这条规则不破。"""
    allowed = _require_objective(objective)
    parsed = _parse_windows(windows)
    page_rules: list[str] = []
    ticket_rules: list[str] = []
    for rule in BURN_RULES:
        if _rule_breached(rule, parsed, allowed):
            if rule.severity == "page":
                page_rules.append(rule.rule_id)
            else:
                ticket_rules.append(rule.rule_id)
    return BreachDecision(
        page=bool(page_rules),
        ticket=bool(ticket_rules),
        page_rules=tuple(page_rules),
        ticket_rules=tuple(ticket_rules),
    )


def dispatch_page(
    windows: Mapping[str, tuple[int, int]],
    *,
    objective: float,
    sink: PageSender | RecordingSender | None,
    channel: str = "webhook",
    sli: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """可调用的 page 路径。破线则记录动作；page 才调用 sender。

    ``sink`` 是 webhook 或 email 的外发口，必须可被测试替换。
    环境变量 ``FRESHLATCH_PAGE_SINK=off`` 时仍记录 page，但不调用 sender。
    ticket 只记录，``respond_by`` 为次日，不调用 page sender。
    需要 page 却没有 sender 时抛 ``PagePathError``：协议页 alone 不算 Done。
    """
    decision = multiwindow_breach(windows, objective=objective)
    return _emit(
        decision,
        objective=objective,
        sink=sink,
        channel=channel,
        sli=sli,
        environ=environ,
    )


def evaluate_window(
    window: SliWindow,
    *,
    objective: float,
    sink: PageSender | RecordingSender | None,
    burn_windows: Mapping[str, tuple[int, int]] | None = None,
    now: datetime | None = None,
    channel: str = "webhook",
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """先落主 SLI，再按注入的 burn 窗或 canary_event 时间窗决定 page / ticket。"""
    sli = measure_primary_sli(window)
    if burn_windows is None:
        if now is None:
            raise ValueError("从 canary_event 分窗需要 now")
        ratios = burn_windows_from_canary_events(window.canary_events, now=now)
    else:
        ratios = dict(burn_windows)
    actions = dispatch_page(
        ratios,
        objective=objective,
        sink=sink,
        channel=channel,
        sli=sli,
        environ=environ,
    )
    return {"sli": sli, "actions": actions, "burn_windows": ratios}


def page_path_status(dispatch: object = _MISSING_DISPATCH) -> str:
    """没有可调用 page 路径则 ``NOT Done``。缺省检查 ``dispatch_page`` 自身。"""
    target = dispatch_page if dispatch is _MISSING_DISPATCH else dispatch
    if not callable(target):
        return NOT_DONE
    return "callable"


def _emit(
    decision: BreachDecision,
    *,
    objective: float,
    sink: PageSender | RecordingSender | None,
    channel: str,
    sli: Mapping[str, Any] | None,
    environ: Mapping[str, str] | None,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if decision.page:
        chosen, send = _resolve_channel(channel, environ)
        body: dict[str, Any] = {
            "kind": "page",
            "channel": chosen,
            "recorded": True,
            "sent": False,
            "suppressed": not send,
            "rules": list(decision.page_rules),
            "oncall_role": ONCALL_ROLE,
            "coverage": ONCALL_COVERAGE,
            "hours": ONCALL_HOURS,
            "objective": objective,
            "objective_is_sesoi": False,
            "protocol_only": False,
        }
        _attach_sli(body, sli)
        if send:
            if sink is None or not callable(getattr(sink, "send", None)):
                raise PagePathError(
                    "协议页 alone 不算 Done；缺少可调用的 page sender"
                )
            outgoing = dict(body)
            outgoing["sent"] = True
            sink.send(outgoing)
            body = outgoing
        actions.append(body)
    if decision.ticket:
        ticket: dict[str, Any] = {
            "kind": "ticket",
            "channel": "ticket",
            "recorded": True,
            "sent": False,
            "suppressed": False,
            "respond_by": TICKET_RESPOND_BY,
            "rules": list(decision.ticket_rules),
            "oncall_role": ONCALL_ROLE,
            "coverage": ONCALL_COVERAGE,
            "hours": ONCALL_HOURS,
            "objective": objective,
            "objective_is_sesoi": False,
        }
        _attach_sli(ticket, sli)
        actions.append(ticket)
    return actions


def _attach_sli(body: dict[str, Any], sli: Mapping[str, Any] | None) -> None:
    if sli is None:
        return
    for key in (
        "window",
        "e2e_p95_ms",
        "abstain_rate",
        "retrieval_fallback_rate",
        "abstain_fallback_rate",
        "canary_event_n",
        "canary_bad_n",
    ):
        if key in sli:
            body[key] = sli[key]


def _resolve_channel(
    channel: str,
    environ: Mapping[str, str] | None,
) -> tuple[str, bool]:
    env = os.environ if environ is None else environ
    chosen = channel
    raw = env.get(PAGE_SINK_ENV)
    if raw is not None:
        text = str(raw).strip().lower()
        if text == "off":
            if chosen not in {"webhook", "email"}:
                raise ValueError("page 渠道只接受 webhook 或 email")
            return chosen, False
        if text in {"webhook", "email"}:
            chosen = text
        elif text != "":
            raise ValueError(
                "FRESHLATCH_PAGE_SINK 只接受 off、webhook、email"
            )
    if chosen not in {"webhook", "email"}:
        raise ValueError("page 渠道只接受 webhook 或 email")
    return chosen, True


def _rule_breached(
    rule: BurnRule,
    windows: Mapping[str, tuple[int, int]],
    objective: float,
) -> bool:
    for name in (rule.long_window, rule.short_window):
        pair = windows.get(name)
        if pair is None:
            return False
        bad, total = pair
        if total == 0:
            return False
        if (bad / total) <= rule.factor * objective:
            return False
    return True


def _require_objective(objective: float) -> float:
    if isinstance(objective, bool) or not isinstance(objective, (int, float)):
        raise ValueError(
            "objective 必须由调用方传入，且为 (0, 1) 内的数；本模块不预设 SESOI"
        )
    if isinstance(objective, float) and not _finite(objective):
        raise ValueError(
            "objective 必须由调用方传入，且为 (0, 1) 内的数；本模块不预设 SESOI"
        )
    if not 0 < float(objective) < 1:
        raise ValueError(
            "objective 必须由调用方传入，且为 (0, 1) 内的数；本模块不预设 SESOI"
        )
    return float(objective)


def _finite(value: float) -> bool:
    return value == value and value not in {float("inf"), float("-inf")}


def _parse_windows(
    windows: Mapping[str, tuple[int, int]],
) -> dict[str, tuple[int, int]]:
    if not isinstance(windows, Mapping):
        raise TypeError("burn 窗口必须是映射")
    parsed: dict[str, tuple[int, int]] = {}
    for name, pair in windows.items():
        if name not in WINDOW_DURATIONS:
            raise ValueError(f"未知窗口 {name}")
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError(f"{name} 必须是 (bad, total)")
        bad, total = pair
        if isinstance(bad, bool) or isinstance(total, bool):
            raise ValueError(f"{name} 的计数不能是布尔")
        if not isinstance(bad, int) or not isinstance(total, int):
            raise ValueError(f"{name} 的计数必须是整数")
        if bad < 0 or total < 0 or bad > total:
            raise ValueError(f"{name} 的 bad/total 不合法")
        parsed[name] = (bad, total)
    return parsed


def _trajectory_runs(window: SliWindow) -> list[tuple[str, list[dict]]]:
    named: list[tuple[str, list[dict]]] = []
    for index, run in enumerate(window.trajectory_runs):
        named.append((f"{index:06d}", [dict(event) for event in run]))
    for index, event in enumerate(window.canary_events):
        embedded = event.get("trajectory_events")
        if embedded is None:
            continue
        if not isinstance(embedded, list) or any(
            not isinstance(item, dict) for item in embedded
        ):
            raise ValueError("canary_event.trajectory_events 必须是事件对象列表")
        named.append((f"canary-{index:06d}", [dict(item) for item in embedded]))
    return named


def _copy_run(run: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    if isinstance(run, (str, bytes, Mapping)):
        raise TypeError("一次轨迹必须是事件列表")
    return tuple(_copy_event(event) for event in run)


def _copy_event(event: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(event, Mapping):
        raise TypeError("事件必须是对象")
    return dict(event)


def _metric_row(rows: list[dict], metric: str) -> dict:
    for row in rows:
        if row["metric"] == metric:
            return row
    raise RuntimeError(f"product SLI 缺少 {metric}")


def _canary_counts(events: Sequence[Mapping[str, Any]]) -> tuple[int, int]:
    sample_n = 0
    bad_n = 0
    for event in events:
        bad = canary_sample_bad(event)
        if bad is None:
            continue
        sample_n += 1
        if bad:
            bad_n += 1
    return sample_n, bad_n


def _sources(window: SliWindow) -> str:
    has_trajectory = bool(window.trajectory_runs) or any(
        isinstance(event.get("trajectory_events"), list) and event["trajectory_events"]
        for event in window.canary_events
    )
    parts: list[str] = []
    if has_trajectory:
        parts.append("trajectory")
    if window.canary_events:
        parts.append("canary_event")
    return "+".join(parts)


def _abstain_fallback_rate(abstain_rate: str, fallback_rate: str) -> str:
    if (
        abstain_rate == PLACEHOLDER_INSUFFICIENT
        and fallback_rate == PLACEHOLDER_INSUFFICIENT
    ):
        return PLACEHOLDER_INSUFFICIENT
    return f"abstain={abstain_rate}; fallback={fallback_rate}"


def _notes(sources: str) -> str:
    return (
        f"{OBSERVATION_MARK}。"
        "不发明 SESOI。"
        "不计注册 G1/A1/T1/R1。"
        "不写 RESULT-Y。"
        f"来源 {sources}。"
        "canary_event 来自 A-P1 生产路径 canary，不是冻结金标 SLI 6。"
    )


def _require_now(now: datetime) -> datetime:
    if not isinstance(now, datetime):
        raise ValueError("now 必须是 datetime")
    if now.tzinfo is None:
        raise ValueError("now 必须带时区")
    return now.astimezone(timezone.utc)


def _parse_ts(raw: object) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("canary_event.ts 必须是带时区的时间字符串")
    try:
        ts = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("canary_event.ts 无法解析") from exc
    if ts.tzinfo is None:
        raise ValueError("canary_event.ts 必须带时区")
    return ts.astimezone(timezone.utc)
