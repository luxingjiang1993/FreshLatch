"""工具层提前反馈单测(#17):Lead/Critic 的 mark_stale 对纯元陈述理由在环内打回。

闸层兜底之外,工具层用同一判定纯函数先行反馈(省步数预算、引导改走正确出口);
Critic 白名单无 mark_gap/reverify_claim,其引导语按 report_finding 出口适配。
零 LLM(ctx 用桩)。
"""

from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.critic import Critic
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import RunContext
from tests.unit.test_meta_gate import C9_RUN2_REASON, C7_LEGIT


class _StubStore:
    def list_invalidation(self):
        return []


def _ctx() -> RunContext:
    return RunContext(store=_StubStore(), guardrails=Guardrails(), mode="eval")


def test_lead_mark_stale_meta_reason_rejected_with_gap_guidance():
    """Lead:纯元陈述理由打回,错误消息引导走 mark_gap + unknown(Lead 白名单内有此二工具)。"""
    lead = LeadReverifier(_ctx(), Claim(claim_id="c9", statement="s",
                                        t0_evidence_ids=[]), llm=None)
    lead._seen_evidence.add("t0-messaging-survey#p3@T1")  # 白名单先备好,隔离元陈述这一个变量
    r = lead._t_mark_stale({"claim_id": "c9", "reason": C9_RUN2_REASON,
                            "evidence_ids": ["t0-messaging-survey#p3@T1"]})
    assert "error" in r and "mark_gap" in r["error"]
    assert lead.decision.status == "unknown"  # 打回不落判定


def test_lead_mark_stale_legit_reason_recorded():
    """Lead:合法理由(数值锚)照常记录 stale 判定,不被新校验误伤。"""
    lead = LeadReverifier(_ctx(), Claim(claim_id="c7", statement="s",
                                        t0_evidence_ids=[]), llm=None)
    lead._seen_evidence.add("t0-competitor-notes#p2@T1")
    r = lead._t_mark_stale({"claim_id": "c7", "reason": C7_LEGIT,
                            "evidence_ids": ["t0-competitor-notes#p2@T1"],
                            "dimension": "competitor_pricing"})
    assert "error" not in r
    assert lead.decision.status == "stale"


def test_critic_mark_stale_meta_reason_rejected_with_finding_guidance():
    """Critic:纯元陈述理由打回,引导语按 report_finding 出口适配(白名单无 mark_gap)。"""
    critic = Critic(_ctx(), Claim(claim_id="c9", statement="s",
                                  t0_evidence_ids=[]), llm=None)
    critic._seen_evidence.add("t0-messaging-survey#p3@T1")
    r = critic._t_mark_stale({"reason": C9_RUN2_REASON,
                              "evidence_ids": ["t0-messaging-survey#p3@T1"]})
    assert "error" in r and "report_finding" in r["error"]
    assert "mark_gap" not in r["error"]  # 不得引导 Critic 调用其白名单外的工具
    assert critic.result.stale_reason == ""  # 打回不记录反证
