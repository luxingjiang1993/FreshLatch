"""A-P1 生产路径 canary：off 不晋升，破线停发。

零 LLM、零网络。不读金标，不碰 PRODUCTION_RETRIEVAL_MODE。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from freshlatch.canary import (
    CANARY_MODE_ENV,
    DEFAULT_CANARY_MODE,
    REASON_ACTIVE_PROMOTE,
    REASON_BREACH_HALT,
    REASON_MODE_OFF,
    REASON_SHADOW_OBSERVE,
    CanaryController,
    CanaryError,
    CanarySample,
    parse_canary_mode,
    resolve_canary_mode,
    sample_breached,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUNBOOK = _REPO_ROOT / "docs" / "ops" / "生产路径canary停发.md"
_CLEAN = CanarySample(failed=False, metric="error_count", value=0, halt_above=1)
_FAILED = CanarySample(failed=True, metric="error_count", value=3, halt_above=1)
_OVER = CanarySample(failed=False, metric="error_count", value=4, halt_above=1)


def test_default_mode_is_off_when_unset():
    """环境与配置都没给 CANARY_MODE 时，默认 off。"""
    assert DEFAULT_CANARY_MODE == "off"
    assert resolve_canary_mode(environ={}) == "off"
    assert resolve_canary_mode(config={}, environ={}) == "off"
    assert resolve_canary_mode(environ={CANARY_MODE_ENV: "  "}) == "off"
    assert parse_canary_mode("", blank_is_off=True) == "off"
    with pytest.raises(CanaryError):
        parse_canary_mode("")


def test_config_selects_mode_and_rejects_unknown():
    """配置键优先于环境；非法字面量拒绝，不改写成别的模式。"""
    assert (
        resolve_canary_mode(
            config={CANARY_MODE_ENV: "shadow"},
            environ={CANARY_MODE_ENV: "active"},
        )
        == "shadow"
    )
    assert resolve_canary_mode(environ={CANARY_MODE_ENV: "active"}) == "active"
    with pytest.raises(CanaryError):
        parse_canary_mode("ON")
    with pytest.raises(CanaryError):
        CanaryController(config={CANARY_MODE_ENV: "progressive"})


def test_off_never_promotes_canary_arm():
    """off：健康样本与破线样本都不把 canary 臂升上主路径。"""
    for sample in (_CLEAN, _FAILED, _OVER):
        decision = CanaryController(environ={}).evaluate("candidate", sample)
        assert decision.mode == "off"
        assert decision.promoted is False
        assert decision.canary_halted is False
        assert decision.serving_arm == decision.main_arm == "main"
        assert decision.serving_arm != "candidate"
        assert decision.reason == REASON_MODE_OFF
        assert decision.metrics_recorded is False
        assert decision.event["event"] == "canary_event"
        assert decision.event["promoted"] is False


@pytest.mark.parametrize("mode", ["shadow", "active"])
def test_breach_halts_and_main_path_refuses_promotion(mode: str):
    """shadow / active 注入失败或超阈：canary_halted，主路径拒绝晋升。"""
    for sample in (_FAILED, _OVER):
        seen: list[dict] = []
        controller = CanaryController(
            config={CANARY_MODE_ENV: mode},
            on_event=seen.append,
        )
        decision = controller.evaluate("candidate", sample)
        assert sample_breached(sample) is True
        assert decision.canary_halted is True
        assert controller.canary_halted is True
        assert decision.promoted is False
        assert decision.serving_arm == "main"
        assert decision.serving_arm != "candidate"
        assert decision.reason == REASON_BREACH_HALT
        assert decision.metrics_recorded is True
        assert controller.metrics[-1]["breached"] is True
        assert decision.event["canary_halted"] is True
        assert decision.event["promoted"] is False
        assert seen[-1]["event"] == "canary_event"
        assert seen[-1]["canary_halted"] is True


def test_shadow_records_metrics_without_promotion():
    """shadow 未破线：写对照指标，主路径仍服役 main。"""
    controller = CanaryController(config={CANARY_MODE_ENV: "shadow"})
    decision = controller.evaluate("candidate", _CLEAN)
    assert decision.canary_halted is False
    assert decision.promoted is False
    assert decision.serving_arm == "main"
    assert decision.reason == REASON_SHADOW_OBSERVE
    assert decision.metrics_recorded is True
    assert controller.metrics == [
        {
            "metric": "error_count",
            "value": 0,
            "halt_above": 1,
            "failed": False,
            "breached": False,
        }
    ]


def test_active_promotes_only_when_sample_is_clean():
    """active 未破线才把 canary 臂升上本机主路径。"""
    decision = CanaryController(config={CANARY_MODE_ENV: "active"}).evaluate(
        "candidate", _CLEAN
    )
    assert decision.canary_halted is False
    assert decision.promoted is True
    assert decision.serving_arm == "candidate"
    assert decision.reason == REASON_ACTIVE_PROMOTE


def test_halt_latches_until_mode_off(tmp_path: Path):
    """破线后健康样本仍不得晋升；切 off 解开停发闩，并且继续不晋升。"""
    event_path = tmp_path / "canary_events.jsonl"
    controller = CanaryController(
        config={CANARY_MODE_ENV: "active"},
        event_path=event_path,
    )
    halted = controller.evaluate("candidate", _FAILED)
    assert halted.canary_halted is True
    again = controller.evaluate("candidate", _CLEAN)
    assert again.canary_halted is True
    assert again.promoted is False
    assert again.serving_arm == "main"
    assert again.event["latched"] is True

    controller.set_mode("off")
    rolled = controller.evaluate("candidate", _CLEAN)
    assert controller.canary_halted is False
    assert rolled.mode == "off"
    assert rolled.canary_halted is False
    assert rolled.promoted is False
    assert rolled.serving_arm == "main"

    rows = [
        json.loads(line)
        for line in event_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["reason"] for row in rows] == [
        REASON_BREACH_HALT,
        REASON_BREACH_HALT,
        REASON_MODE_OFF,
    ]
    assert all(row["event"] == "canary_event" for row in rows)


def test_threshold_equal_is_not_a_breach():
    """停发线取严格大于；等于阈值不算破线。"""
    sample = CanarySample(failed=False, metric="error_count", value=1, halt_above=1)
    assert sample_breached(sample) is False
    decision = CanaryController(config={CANARY_MODE_ENV: "active"}).evaluate(
        "candidate", sample
    )
    assert decision.promoted is True
    assert decision.canary_halted is False


def test_runbook_states_scope_owner_halt_and_rollback():
    """剧本写明值班 owner、破线即停、回滚切 off，以及范围句。"""
    text = _RUNBOOK.read_text(encoding="utf-8")
    assert "单机 canary ≠ 多区渐进发布; ≠ 注册分; ≠ L5." in text
    assert "冻结金标canary跑法.md" in text
    assert "owner" in text
    assert "CANARY_MODE=off" in text
    assert "canary_event" in text
    assert "P3" in text
    assert "canary_halted" in text


def test_module_does_not_touch_retrieval_default_or_scores():
    """本模块不引用检索默认臂、金标或注册分入口。"""
    module_path = _REPO_ROOT / "src" / "freshlatch" / "canary.py"
    source_text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert all(not name.startswith("freshlatch") for name in imported)
    assert "PRODUCTION_RETRIEVAL_MODE =" not in source_text
