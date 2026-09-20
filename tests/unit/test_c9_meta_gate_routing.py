"""c9 缺口句法闸端到端落档测试(#17):闸打回经 runner 既有路径路由 unknown。

runner._finalize 是 stale→unknown 的唯一落档路径(绿灯唯一出口的镜像);
本测试把 c9 两次实录失败形状注入,验证最终 claim.status 逐位为 unknown。
零 LLM(store 用桩,list_invalidation 是 Runner.__init__ 唯一需要的口)。
"""

from freshlatch.models import Claim
from freshlatch.runner import ClaimDecision, Runner
from tests.unit.test_meta_gate import C9_REPRO2_REASON, C9_RUN2_REASON


class _StubStore:
    def list_invalidation(self):
        return []


def _run_finalize(reason: str) -> Claim:
    claim = Claim(claim_id="c9", statement="目标市场 WhatsApp Business 渗透率不低于 70%",
                  t0_evidence_ids=["t0-messaging-survey#p2"])
    decision = ClaimDecision(claim_id="c9", status="stale", reason=reason,
                             evidence_ids=["t0-messaging-survey#p3@T1"])
    Runner(_StubStore())._finalize(claim, decision)  # noqa: SLF001 — 落档路径直测
    return claim


def test_c9_run2_shape_routes_to_unknown():
    """c9 run2 实录形状(不再列入跟踪项)⇒ 闸打回 META_ONLY_DISPROOF ⇒ 落 unknown。"""
    claim = _run_finalize(C9_RUN2_REASON)
    assert claim.status == "unknown"
    assert "META_ONLY_DISPROOF" in claim.reason


def test_c9_repro2_shape_routes_to_unknown():
    """c9 复现2 实录形状(未复测当推翻)⇒ 同上。两次历史失败从此确定性落 unknown。"""
    claim = _run_finalize(C9_REPRO2_REASON)
    assert claim.status == "unknown"
    assert "META_ONLY_DISPROOF" in claim.reason


def test_legit_stale_still_lands_stale():
    """对照:合法 stale(数值锚)落档不受新不变量影响,仍判 stale。"""
    from tests.unit.test_meta_gate import C7_LEGIT
    claim = Claim(claim_id="c7", statement="SeaDesk 客单价 99 美元/月",
                  t0_evidence_ids=["t0-competitor-notes#p2"])
    decision = ClaimDecision(claim_id="c7", status="stale", reason=C7_LEGIT,
                             evidence_ids=["t0-competitor-notes#p2@T1"])
    Runner(_StubStore())._finalize(claim, decision)  # noqa: SLF001
    assert claim.status == "stale"
