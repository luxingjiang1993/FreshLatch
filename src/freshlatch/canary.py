"""生产路径 canary 控制（A-P1）。

单机开关：环境变量或配置项 ``CANARY_MODE=off|shadow|active``，缺省 ``off``。
``off`` 时主路径不晋升 canary 臂。
``shadow`` 只把对照写进指标，不晋升。
``active`` 在未破线时允许本机把 canary 臂升上主路径。
失败注入或 ``value > halt_above`` 视为破线：``canary_halted=true``，主路径拒绝晋升。
停发闩住，直到模式切回 ``off``。

``halt_above`` 由调用方随本次样本传入，只作为这次停发线。
本模块发出 ``canary_event``（返回值，以及可选 JSONL / hook）。分页留给 P3。

与 ``docs/ops/冻结金标canary跑法.md``（冻结金标 SLI 6）不是同一条 canary。
不读金标，不写注册分，不改 ``PRODUCTION_RETRIEVAL_MODE``。
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANARY_MODE_ENV = "CANARY_MODE"
DEFAULT_CANARY_MODE = "off"
CANARY_MODES = ("off", "shadow", "active")
MAIN_ARM = "main"

REASON_MODE_OFF = "mode_off"
REASON_SHADOW_OBSERVE = "shadow_observe"
REASON_ACTIVE_PROMOTE = "active_promote"
REASON_BREACH_HALT = "breach_halt"

_REASON_MESSAGE = {
    REASON_MODE_OFF: "模式为 off，主路径不晋升 canary 臂",
    REASON_SHADOW_OBSERVE: "shadow 只记对照指标，不晋升",
    REASON_ACTIVE_PROMOTE: "active 未破线，本机可晋升 canary 臂",
    REASON_BREACH_HALT: "破线停发，主路径拒绝晋升",
}


class CanaryError(ValueError):
    """canary 模式或样本不合法。"""


def resolve_canary_mode(
    *,
    config: Mapping[str, str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """解析 ``CANARY_MODE``。

    配置里有该键时用配置；否则读环境。键缺失或空白为 ``off``。
    显式给出的其它字面量抛 ``CanaryError``。
    """
    if config is not None and CANARY_MODE_ENV in config:
        return parse_canary_mode(config[CANARY_MODE_ENV], blank_is_off=True)
    env = environ if environ is not None else os.environ
    if CANARY_MODE_ENV not in env:
        return DEFAULT_CANARY_MODE
    return parse_canary_mode(env[CANARY_MODE_ENV], blank_is_off=True)


def parse_canary_mode(raw: object, *, blank_is_off: bool = False) -> str:
    """必须是 ``off|shadow|active``。仅在解析缺省配置时把空白当成 ``off``。"""
    text = str(raw).strip() if raw is not None else ""
    if text == "":
        if blank_is_off:
            return DEFAULT_CANARY_MODE
        raise CanaryError("CANARY_MODE 为空")
    if text not in CANARY_MODES:
        raise CanaryError(
            f"CANARY_MODE 只接受 off|shadow|active，收到 {text!r}"
        )
    return text


@dataclass(frozen=True)
class CanarySample:
    """一次主路径对照样本。

    ``failed=True`` 或 ``value > halt_above`` 为破线。
    只设置其中一侧阈值时，数值比较不触发。
    """

    failed: bool = False
    metric: str = "error"
    value: float | None = None
    halt_above: float | None = None

    def __post_init__(self) -> None:
        if not str(self.metric).strip():
            raise CanaryError("指标名为空")


def sample_breached(sample: CanarySample) -> bool:
    """失败注入或超过本次停发线。"""
    if sample.failed:
        return True
    if sample.value is None or sample.halt_above is None:
        return False
    return float(sample.value) > float(sample.halt_above)


@dataclass(frozen=True)
class CanaryDecision:
    """一次生产路径咨询结果。``promoted`` 为真才表示 canary 臂升上主路径。"""

    mode: str
    canary_halted: bool
    promoted: bool
    serving_arm: str
    main_arm: str
    canary_arm: str
    reason: str
    message: str
    metrics_recorded: bool
    event: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "canary_halted": self.canary_halted,
            "promoted": self.promoted,
            "serving_arm": self.serving_arm,
            "main_arm": self.main_arm,
            "canary_arm": self.canary_arm,
            "reason": self.reason,
            "message": self.message,
            "metrics_recorded": self.metrics_recorded,
            "event": dict(self.event),
        }


class CanaryController:
    """本机 canary 控制。停发状态只活在这个实例里。"""

    def __init__(
        self,
        *,
        config: Mapping[str, str] | None = None,
        environ: Mapping[str, str] | None = None,
        main_arm: str = MAIN_ARM,
        event_path: Path | None = None,
        on_event: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> None:
        self.mode = resolve_canary_mode(config=config, environ=environ)
        self.main_arm = _require_main_arm(main_arm)
        self.metrics: list[dict[str, Any]] = []
        self._halted = False
        self._event_path = event_path
        self._on_event = on_event

    def set_mode(self, mode: str) -> None:
        """切换模式。``off`` 同时解开停发闩，主路径仍不晋升。"""
        self.mode = parse_canary_mode(mode, blank_is_off=False)
        if self.mode == "off":
            self._halted = False

    @property
    def canary_halted(self) -> bool:
        return self._halted

    def evaluate(
        self,
        canary_arm: str,
        sample: CanarySample | None = None,
    ) -> CanaryDecision:
        """咨询主路径该服役哪条臂。

        ``off`` 忽略样本，永远服役主路径。
        ``shadow`` / ``active`` 在尚未停发时必须带样本。
        已停发后再咨询，仍拒绝晋升，直到 ``set_mode("off")``。
        """
        arm = _require_canary_arm(canary_arm, self.main_arm)
        if self.mode == "off":
            self._halted = False
            return self._finish(
                canary_arm=arm,
                halted=False,
                promoted=False,
                reason=REASON_MODE_OFF,
                sample=sample,
                metrics_recorded=False,
                latched=False,
            )

        if self._halted:
            recorded = self._record(sample) if sample is not None else False
            return self._finish(
                canary_arm=arm,
                halted=True,
                promoted=False,
                reason=REASON_BREACH_HALT,
                sample=sample,
                metrics_recorded=recorded,
                latched=True,
            )

        if sample is None:
            raise CanaryError("shadow 与 active 必须带对照样本")

        breached = sample_breached(sample)
        self._record(sample)
        if breached:
            self._halted = True
            return self._finish(
                canary_arm=arm,
                halted=True,
                promoted=False,
                reason=REASON_BREACH_HALT,
                sample=sample,
                metrics_recorded=True,
                latched=False,
            )
        if self.mode == "shadow":
            return self._finish(
                canary_arm=arm,
                halted=False,
                promoted=False,
                reason=REASON_SHADOW_OBSERVE,
                sample=sample,
                metrics_recorded=True,
                latched=False,
            )
        return self._finish(
            canary_arm=arm,
            halted=False,
            promoted=True,
            reason=REASON_ACTIVE_PROMOTE,
            sample=sample,
            metrics_recorded=True,
            latched=False,
        )

    def _record(self, sample: CanarySample | None) -> bool:
        if sample is None:
            return False
        self.metrics.append(
            {
                "metric": sample.metric,
                "value": sample.value,
                "halt_above": sample.halt_above,
                "failed": sample.failed,
                "breached": sample_breached(sample),
            }
        )
        return True

    def _finish(
        self,
        *,
        canary_arm: str,
        halted: bool,
        promoted: bool,
        reason: str,
        sample: CanarySample | None,
        metrics_recorded: bool,
        latched: bool,
    ) -> CanaryDecision:
        serving = canary_arm if promoted else self.main_arm
        event = _canary_event(
            mode=self.mode,
            canary_halted=halted,
            promoted=promoted,
            main_arm=self.main_arm,
            canary_arm=canary_arm,
            serving_arm=serving,
            reason=reason,
            sample=sample,
            latched=latched,
        )
        self._emit(event)
        return CanaryDecision(
            mode=self.mode,
            canary_halted=halted,
            promoted=promoted,
            serving_arm=serving,
            main_arm=self.main_arm,
            canary_arm=canary_arm,
            reason=reason,
            message=_REASON_MESSAGE[reason],
            metrics_recorded=metrics_recorded,
            event=event,
        )

    def _emit(self, event: Mapping[str, Any]) -> None:
        if self._event_path is not None:
            line = json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
            with self._event_path.open("a", encoding="utf-8") as handle:
                handle.write(line)
        if self._on_event is not None:
            self._on_event(event)


def _require_main_arm(main_arm: str) -> str:
    arm = (main_arm or "").strip()
    if not arm:
        raise CanaryError("主路径臂名为空")
    return arm


def _require_canary_arm(canary_arm: str, main_arm: str) -> str:
    arm = (canary_arm or "").strip()
    if not arm:
        raise CanaryError("canary 臂名为空")
    if arm == main_arm:
        raise CanaryError("canary 臂不得与主路径同名")
    return arm


def _canary_event(
    *,
    mode: str,
    canary_halted: bool,
    promoted: bool,
    main_arm: str,
    canary_arm: str,
    serving_arm: str,
    reason: str,
    sample: CanarySample | None,
    latched: bool,
) -> dict[str, Any]:
    return {
        "event": "canary_event",
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "canary_halted": canary_halted,
        "promoted": promoted,
        "main_arm": main_arm,
        "canary_arm": canary_arm,
        "serving_arm": serving_arm,
        "reason": reason,
        "message": _REASON_MESSAGE[reason],
        "metric": None if sample is None else sample.metric,
        "value": None if sample is None else sample.value,
        "halt_above": None if sample is None else sample.halt_above,
        "failed": None if sample is None else sample.failed,
        "latched": latched,
    }
