"""角色工具白名单矩阵(§3.3)单测:禁止事项靠工具不存在,不靠提示词。"""

from freshlatch.tools import (
    AUDITOR_TOOLS,
    CRITIC_TOOLS,
    FOCUS_DIMENSIONS,
    LEAD_TOOLS_W1,
    LEAD_TOOLS_W3,
    tool_specs,
)


def test_critic_cannot_fresh_or_spawn():
    """Critic:无 reverify_claim(想强化也没有工具可写)、无 spawn(深度恒 1)、无放行。"""
    assert "reverify_claim" not in CRITIC_TOOLS
    assert not any(t.startswith("spawn_") for t in CRITIC_TOOLS)
    assert "report_finding" in CRITIC_TOOLS  # 唯一出口


def test_lead_w1_has_no_spawn_critic():
    """阶段挂载:W1–W2 Lead 白名单不含 spawn_critic(Critic W3 才启用)。"""
    assert "spawn_critic" not in LEAD_TOOLS_W1
    assert "spawn_critic" in LEAD_TOOLS_W3


def test_lead_w1_has_no_auditor_or_memory_tools():
    """阶段挂载:W1–W4 不含 spawn_auditor(W5–W8)与记忆卫生工具(W9–W12)。"""
    for t in LEAD_TOOLS_W1 + LEAD_TOOLS_W3:
        assert t not in ("spawn_auditor", "list_memories", "spawn_forensic",
                         "flag_contradiction", "flag_dead", "flag_unverified",
                         "propose_quarantine")


def test_auditor_only_verdict():
    """Auditor(W5–W8):唯一出口 verdict,无检索/读写工具,不得拥有放行权。"""
    assert AUDITOR_TOOLS == ("verdict",)


def test_focus_dimensions_closed_enum():
    """封闭枚举 6 值(§3.4),与语料金标维度同构。"""
    assert FOCUS_DIMENSIONS == (
        "competitor_pricing", "regulatory_stance", "interview_reversal",
        "cost_model", "market_structure", "tech_ecosystem",
    )


def test_tool_specs_known_names_only():
    for names in (LEAD_TOOLS_W1, LEAD_TOOLS_W3, CRITIC_TOOLS, AUDITOR_TOOLS):
        assert len(tool_specs(list(names))) == len(names)
