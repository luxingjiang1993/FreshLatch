"""A-P9: 单包 allowlist、tool_tier + ACL、轨迹、该触发/不该触发。零付费 API。"""

from __future__ import annotations

from pathlib import Path

import pytest

from freshlatch.serving.app import SERVING_KEYS_ENV, SERVING_TENANT_MISMATCH, SERVING_UNAUTHORIZED
from freshlatch.skills_loader import (
    BUSINESS_SKILL_PACKAGES,
    REASON_SKILL_ALLOWLIST_INVALID,
    REASON_SKILL_ALLOWLIST_OFF,
    REASON_SKILL_NOT_TRIGGERED,
    REASON_SKILL_OK,
    REASON_SKILL_TOOL_NOT_ALLOWED,
    SKILL_ALLOWLIST_ENV,
    SKILL_TRACE_FIELDS,
    invoke_skill_tool,
    mounted_skill_package,
    triggered_skill_package,
)
from freshlatch.store.tenant_acl import REASON_TENANT_ACL_DENIED
from freshlatch.tools import FIXTURE_TOOL_TIER_2, REASON_TOOL_TIER_DENIED

_REPO = Path(__file__).resolve().parents[2]
_RUNBOOK = _REPO / "docs" / "ops" / "生产路径canary停发.md"

# 三对夹具。must_not 在对方包单独挂载时该触发,避免空句子假绿。
TRIGGER_FIXTURES = (
    {
        "id": "earnings-not-event",
        "package": "earnings_figures",
        "should": "请核对这份财报的收入与毛利",
        "must_not": "这次产品发布是否被监管口径撤回",
        "must_not_package": "event_timeline",
    },
    {
        "id": "event-not-earnings",
        "package": "event_timeline",
        "should": "这次产品发布是否被监管口径撤回",
        "must_not": "请核对这份财报的收入与毛利",
        "must_not_package": "earnings_figures",
    },
    {
        "id": "patch-not-strategy",
        "package": "patch_diff",
        "should": "对比 before_text 与 after_text 的 patch diff 行差",
        "must_not": "按 walkthrough 走查顾问报告里的战略主张",
        "must_not_package": "strategy_walkthrough",
    },
)


def _one(package: str) -> dict[str, str]:
    return {SKILL_ALLOWLIST_ENV: package}


def _boom(args: dict) -> dict:
    raise AssertionError(f"handler 不应被调用: {args}")


@pytest.fixture()
def serving_keys(monkeypatch):
    monkeypatch.setenv(SERVING_KEYS_ENV, "key-a=tenant-a,key-b=tenant-b")


def test_default_allowlist_is_off(monkeypatch):
    """环境与配置都没给开关时不挂任何包。"""
    monkeypatch.delenv(SKILL_ALLOWLIST_ENV, raising=False)
    mounted, reason = mounted_skill_package()
    assert mounted is None
    assert reason == REASON_SKILL_ALLOWLIST_OFF
    assert mounted_skill_package(environ={}) == (None, REASON_SKILL_ALLOWLIST_OFF)
    assert mounted_skill_package(config={}) == (None, REASON_SKILL_ALLOWLIST_OFF)
    assert mounted_skill_package(config={SKILL_ALLOWLIST_ENV: "off"})[0] is None
    assert mounted_skill_package(config={SKILL_ALLOWLIST_ENV: "  "})[0] is None


def test_config_mounts_exactly_one_and_rejects_the_rest():
    """config 优先于环境。多项、角色包、未知 slug 都不挂。"""
    mounted, reason = mounted_skill_package(
        config=_one("patch_diff"),
        environ=_one("earnings_figures"),
    )
    assert mounted == "patch_diff"
    assert reason == REASON_SKILL_OK
    assert mounted_skill_package(environ=_one("event_timeline"))[0] == "event_timeline"
    invalid = (
        ",".join(BUSINESS_SKILL_PACKAGES),
        "earnings_figures,event_timeline",
        "earnings_figures event_timeline",
        "reverify",
        "no_such_pack",
        "*",
    )
    for raw in invalid:
        got, why = mounted_skill_package(config={SKILL_ALLOWLIST_ENV: raw})
        assert got is None
        assert why == REASON_SKILL_ALLOWLIST_INVALID
    assert len(BUSINESS_SKILL_PACKAGES) == 4


def test_trigger_fixture_count():
    assert len(TRIGGER_FIXTURES) >= 3


@pytest.mark.parametrize("case", TRIGGER_FIXTURES, ids=[row["id"] for row in TRIGGER_FIXTURES])
def test_should_trigger_and_must_not_trigger(case):
    """挂上的那一个包才看触发词。对方句子不触发本包,默认 off 时两边都不触发。"""
    should = case["should"]
    must_not = case["must_not"]
    package = case["package"]
    other = case["must_not_package"]
    assert triggered_skill_package(should, config=_one(package)) == package
    assert triggered_skill_package(must_not, config=_one(package)) is None
    assert triggered_skill_package(must_not, config=_one(other)) == other
    assert triggered_skill_package(should, config=_one(other)) is None
    assert triggered_skill_package(should, environ={}) is None
    assert triggered_skill_package(must_not, config={SKILL_ALLOWLIST_ENV: "off"}) is None
    assert triggered_skill_package(
        should,
        config={SKILL_ALLOWLIST_ENV: f"{package},{other}"},
    ) is None


def test_docs_state_single_package_demo_not_marketplace():
    """范围句、开关、轨迹字段、发车勾选落在 canary 同页。"""
    text = _RUNBOOK.read_text(encoding="utf-8")
    assert "单包 demo / 非 marketplace" in text
    assert "FRESHLATCH_SKILL_ALLOWLIST" in text
    assert "tool_tier" in text
    assert "dispatch_tiered_tool" in text
    for field in SKILL_TRACE_FIELDS:
        assert f"`{field}`" in text
    assert "- [ ]" in text
    assert "tests/unit/test_skill_allowlist.py" in text


def test_skill_tool_trace_on_allowed_retrieve(serving_keys):
    """tool_tier_0 在 ACL 通过后执行,轨迹带齐五个字段。"""
    seen: list[dict] = []
    traces: list[dict] = []

    def handler(args: dict) -> dict:
        seen.append(args)
        return {"hits": 1}

    out = invoke_skill_tool(
        "请核对这份财报的收入与毛利",
        "retrieve",
        {"query": "收入"},
        handler,
        config=_one("earnings_figures"),
        authorization="Bearer key-a",
        traces=traces,
        invocation_id="ok-1",
    )
    assert seen == [{"query": "收入"}]
    assert out["ok"] is True
    assert out["fail_closed"] is False
    assert out["result"] == {"hits": 1}
    assert traces == [out["trace"]]
    assert list(out["trace"]) == list(SKILL_TRACE_FIELDS)
    assert out["trace"]["package"] == "earnings_figures"
    assert out["trace"]["id"] == "ok-1"
    assert out["trace"]["ok"] is True
    assert out["trace"]["reason"] == REASON_SKILL_OK
    assert isinstance(out["trace"]["latency"], float)
    assert out["trace"]["latency"] >= 0


@pytest.mark.parametrize(
    "authorization,client_tenant,tool_args,expect",
    [
        (None, "tenant-b", {}, SERVING_UNAUTHORIZED),
        ("Bearer key-a", "tenant-b", {}, SERVING_TENANT_MISMATCH),
        ("Bearer key-a", "tenant-a", {"tenant_id": "tenant-b"}, REASON_TENANT_ACL_DENIED),
    ],
)
def test_cross_tenant_skill_tool_fails_closed(
    serving_keys, authorization, client_tenant, tool_args, expect,
):
    """无凭证、跨租户声明、工具参数租户不一致都不调用工具。"""
    traces: list[dict] = []
    out = invoke_skill_tool(
        "请核对这份财报的收入",
        "retrieve",
        tool_args,
        _boom,
        config=_one("earnings_figures"),
        authorization=authorization,
        client_tenant=client_tenant,
        traces=traces,
        invocation_id="acl-deny",
    )
    assert out["ok"] is False
    assert out["fail_closed"] is True
    assert out["result"] is None
    assert out["trace"]["reason"] == expect
    assert out["trace"]["package"] == "earnings_figures"
    assert out["trace"]["ok"] is False
    assert list(out["trace"]) == list(SKILL_TRACE_FIELDS)
    assert len(traces) == 1


@pytest.mark.parametrize("tool_name", ["spawn_auditor", FIXTURE_TOOL_TIER_2, "not_a_tool"])
def test_tool_tier_2_and_unknown_do_not_run(serving_keys, tool_name):
    """禁档与未分级名字走 tool_tier,handler 不执行。"""
    out = invoke_skill_tool(
        "请核对这份财报的收入",
        tool_name,
        {},
        _boom,
        config=_one("earnings_figures"),
        authorization="Bearer key-a",
        invocation_id="tier2",
    )
    assert out["ok"] is False
    assert out["fail_closed"] is True
    assert out["trace"]["reason"] == REASON_TOOL_TIER_DENIED
    assert out["result"]["reason_code"] == REASON_TOOL_TIER_DENIED
    assert out["result"]["ok"] is False


def test_tool_outside_business_projection_fails_closed(serving_keys):
    """tool_tier_0 但不在业务包投影里的工具不执行。"""
    out = invoke_skill_tool(
        "请核对这份财报的收入",
        "list_memories",
        {},
        _boom,
        config=_one("earnings_figures"),
        authorization="Bearer key-a",
        invocation_id="projection",
    )
    assert out["trace"]["reason"] == REASON_SKILL_TOOL_NOT_ALLOWED
    assert out["fail_closed"] is True
    assert out["result"] is None


def test_tool_tier_1_needs_latch_grant(serving_keys, tmp_path):
    """写观测只在 HumanLatch 放行后执行。"""
    from freshlatch.latch.pipeline import HumanLatch
    from freshlatch.models import Claim

    latch = HumanLatch(object(), tmp_path / "cp.db", mode="online")
    claim = Claim(claim_id="c1", statement="收入仍是 10", status="stale", reason="待审")
    assert latch.enter_round([claim], ts="20261015-120000").waiting
    seen: list[dict] = []

    def handler(args: dict) -> dict:
        seen.append(dict(args))
        return {"recorded": True}

    denied = invoke_skill_tool(
        "请核对这份财报的收入",
        "mark_stale",
        {"claim_id": "c1"},
        handler,
        config=_one("earnings_figures"),
        authorization="Bearer key-a",
        invocation_id="tier1-deny",
    )
    assert seen == []
    assert denied["trace"]["ok"] is False
    assert denied["trace"]["reason"] == REASON_TOOL_TIER_DENIED
    grant = latch.approve_write_tool("mark_stale", claim_id="c1")
    allowed = invoke_skill_tool(
        "请核对这份财报的收入",
        "mark_stale",
        {"claim_id": "c1"},
        handler,
        config=_one("earnings_figures"),
        authorization="Bearer key-a",
        approval=grant,
        invocation_id="tier1-ok",
    )
    assert seen == [{"claim_id": "c1"}]
    assert allowed["ok"] is True
    assert allowed["trace"]["reason"] == REASON_SKILL_OK
    assert allowed["trace"]["package"] == "earnings_figures"
    assert allowed["result"] == {"recorded": True}


def test_off_and_untriggered_do_not_call_tool(serving_keys):
    """默认 off、无效多项、词不中都不碰工具,但仍写轨迹。"""
    traces: list[dict] = []
    off = invoke_skill_tool(
        "请核对这份财报的收入",
        "retrieve",
        {},
        _boom,
        environ={},
        authorization="Bearer key-a",
        traces=traces,
        invocation_id="off",
    )
    invalid = invoke_skill_tool(
        "请核对这份财报的收入",
        "retrieve",
        {},
        _boom,
        config={SKILL_ALLOWLIST_ENV: ",".join(BUSINESS_SKILL_PACKAGES)},
        authorization="Bearer key-a",
        traces=traces,
        invocation_id="invalid",
    )
    quiet = invoke_skill_tool(
        "今天天气怎么样",
        "retrieve",
        {},
        _boom,
        config=_one("earnings_figures"),
        authorization="Bearer key-a",
        traces=traces,
        invocation_id="quiet",
    )
    assert off["trace"]["reason"] == REASON_SKILL_ALLOWLIST_OFF
    assert off["trace"]["package"] == ""
    assert invalid["trace"]["reason"] == REASON_SKILL_ALLOWLIST_INVALID
    assert quiet["trace"]["reason"] == REASON_SKILL_NOT_TRIGGERED
    assert quiet["trace"]["package"] == "earnings_figures"
    assert [row["id"] for row in traces] == ["off", "invalid", "quiet"]
    assert all(row["ok"] is False for row in traces)
    assert all(isinstance(row["latency"], float) for row in traces)


def test_loader_keeps_acl_and_tier_on_the_path():
    """skill→tool 复用 A-P4 入口和 FC 分档,不在加载器里另写一套放行。"""
    text = (_REPO / "src" / "freshlatch" / "skills_loader.py").read_text(encoding="utf-8")
    assert "enforce_mapped_action" in text
    assert "dispatch_tiered_tool" in text
    assert "resolve_pre_retrieval_tenant" in text
