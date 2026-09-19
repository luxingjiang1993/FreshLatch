"""Guardrails 单测:参数集中 dataclass、可被 eval 代码级覆盖、软收尾消息。"""

from freshlatch.guardrails import BUDGET_EXHAUSTED_MESSAGE, Guardrails
from freshlatch.runner import RunContext
from freshlatch.store.base import InMemoryStore


def test_defaults_locked():
    g = Guardrails()
    assert g.lead_max_steps == 18
    assert g.critic_max_steps == 8
    assert g.auditor_max_steps == 6
    assert g.forensic_max_steps == 8
    assert g.retrieval_budget == 24


def test_eval_can_override():
    """eval harness 代码级覆盖(§6.1)——金标可复现的工程手段。"""
    g = Guardrails(lead_max_steps=3, retrieval_budget=1)
    assert g.lead_max_steps == 3 and g.retrieval_budget == 1


def test_soft_close_message():
    assert "基于现有证据下结论" in BUDGET_EXHAUSTED_MESSAGE
    assert Guardrails().exhausted_soft_close() == BUDGET_EXHAUSTED_MESSAGE


def test_retrieval_budget_fail_soft():
    """检索预算超限:结构化「预算已尽」,不抛异常,引导改用 read_source。"""
    ctx = RunContext(store=InMemoryStore(), guardrails=Guardrails(retrieval_budget=2))
    r1 = ctx.try_retrieve("q")
    r2 = ctx.try_retrieve("q")
    r3 = ctx.try_retrieve("q")
    assert not isinstance(r1, dict) and not isinstance(r2, dict)
    assert r3["budget_exhausted"] is True and "read_source" in r3["message"]
    assert ctx.retrieval_used == 2  # 计数不越界
