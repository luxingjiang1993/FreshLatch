"""支撑复盘读反——工具层提前打回(#243)。

Lead/Critic mark_stale 对读反形在环内打回;引导 Lead 走 fresh 同维支持,
Critic 走 report_finding(未见推翻)。零 LLM。
"""

from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.critic import Critic
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import RunContext
from tests.unit.test_meta_gate import C7_LEGIT
from tests.unit.test_support_review_misread import (
    C6_MIN_MISREAD_REASON,
    C6_RECORDED_MISREAD_REASON,
    C6_STATEMENT,
)


class _StubStore:
    def list_invalidation(self):
        return []


def _ctx() -> RunContext:
    return RunContext(store=_StubStore(), guardrails=Guardrails(), mode="eval")


def test_lead_mark_stale_c6_misread_rejected_with_fresh_guidance():
    """#243:Lead 对 c6 实录读反形打回,引导走 reverify_claim(fresh)。"""
    lead = LeadReverifier(
        _ctx(),
        Claim(claim_id="c6", statement=C6_STATEMENT, t0_evidence_ids=[]),
        llm=None,
    )
    lead._seen_evidence.add("t0-competitor-news#p3@T1")
    r = lead._t_mark_stale({
        "claim_id": "c6",
        "reason": C6_RECORDED_MISREAD_REASON,
        "evidence_ids": ["t0-competitor-news#p3@T1"],
        "dimension": "competitor_pricing",
    })
    assert "error" in r
    assert "fresh" in r["error"]
    assert "窗口不佳" in r["error"] or "支撑" in r["error"]
    assert lead.decision.status == "unknown"  # 打回不落 stale


def test_lead_mark_stale_min_misread_rejected():
    """#243:最小合成读反形同样打回。"""
    lead = LeadReverifier(
        _ctx(),
        Claim(claim_id="cx", statement=C6_STATEMENT, t0_evidence_ids=[]),
        llm=None,
    )
    lead._seen_evidence.add("t0-competitor-news#p3@T1")
    r = lead._t_mark_stale({
        "claim_id": "cx",
        "reason": C6_MIN_MISREAD_REASON,
        "evidence_ids": ["t0-competitor-news#p3@T1"],
        "dimension": "competitor_pricing",
    })
    assert "error" in r
    assert lead.decision.status == "unknown"


def test_lead_mark_stale_pricing_as_window_rejected():
    """#243:旁近 Lite 定价当窗口反证形同样打回。"""
    lead = LeadReverifier(
        _ctx(),
        Claim(claim_id="c6", statement=C6_STATEMENT, t0_evidence_ids=[]),
        llm=None,
    )
    lead._seen_evidence.add("t0-competitor-notes#p2@T1")
    from tests.unit.test_support_review_misread import C6_PRICING_AS_WINDOW_REASON
    r = lead._t_mark_stale({
        "claim_id": "c6",
        "reason": C6_PRICING_AS_WINDOW_REASON,
        "evidence_ids": ["t0-competitor-notes#p2@T1"],
        "dimension": "competitor_pricing",
    })
    assert "error" in r
    assert "fresh" in r["error"] or "Lite" in r["error"] or "窗口" in r["error"]
    assert lead.decision.status == "unknown"


def test_lead_legit_c7_still_recorded():
    """#243 回归:合法 c7 数值锚仍可落 stale。"""
    lead = LeadReverifier(
        _ctx(),
        Claim(claim_id="c7", statement="竞品 SeaDesk 客单价仍为 99 美元/月",
              t0_evidence_ids=[]),
        llm=None,
    )
    lead._seen_evidence.add("t0-competitor-notes#p2@T1")
    r = lead._t_mark_stale({
        "claim_id": "c7",
        "reason": C7_LEGIT,
        "evidence_ids": ["t0-competitor-notes#p2@T1"],
        "dimension": "competitor_pricing",
    })
    assert "error" not in r
    assert lead.decision.status == "stale"


def test_critic_mark_stale_misread_rejected_with_finding_guidance():
    """#243:Critic 对读反形打回,引导 report_finding(白名单无 fresh)。"""
    critic = Critic(
        _ctx(),
        Claim(claim_id="c6", statement=C6_STATEMENT, t0_evidence_ids=[]),
        llm=None,
    )
    critic._seen_evidence.add("t0-competitor-news#p3@T1")
    r = critic._t_mark_stale({
        "reason": C6_MIN_MISREAD_REASON,
        "evidence_ids": ["t0-competitor-news#p3@T1"],
        "dimension": "competitor_pricing",
    })
    assert "error" in r and "report_finding" in r["error"]
    assert "reverify_claim" not in r["error"]
    assert critic.result.stale_reason == ""
