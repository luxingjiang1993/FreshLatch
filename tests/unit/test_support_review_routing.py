"""支撑复盘读反——闸打回经 runner 落档路由(#243)。

读反形不得落 stale;合法数值锚仍落 stale。零 LLM。
"""

from freshlatch.models import Claim
from freshlatch.runner import ClaimDecision, Runner
from tests.unit.test_meta_gate import C7_LEGIT
from tests.unit.test_support_review_misread import (
    C6_MIN_MISREAD_REASON,
    C6_RECORDED_MISREAD_REASON,
    C6_STATEMENT,
)


class _StubStore:
    def list_invalidation(self):
        return []


def _run_finalize(reason: str, *, claim_id: str = "c6",
                  statement: str = C6_STATEMENT) -> Claim:
    claim = Claim(claim_id=claim_id, statement=statement,
                  t0_evidence_ids=["t0-competitor-news#p2"])
    decision = ClaimDecision(
        claim_id=claim_id, status="stale", reason=reason,
        evidence_ids=["t0-competitor-news#p3@T1"],
        auditor_verdict="stale", auditor_reason="误读形",
        auditor_dimension_match=True,
    )
    Runner(_StubStore())._finalize(claim, decision)  # noqa: SLF001
    return claim


def test_c6_recorded_misread_routes_to_unknown():
    """#243:c6 实录读反形 ⇒ 闸打回 SUPPORT_REVIEW_MISREAD ⇒ 落 unknown。"""
    claim = _run_finalize(C6_RECORDED_MISREAD_REASON)
    assert claim.status == "unknown"
    assert "SUPPORT_REVIEW_MISREAD" in claim.reason


def test_c6_min_misread_routes_to_unknown():
    """#243:最小合成读反形同样不得落 stale。"""
    claim = _run_finalize(C6_MIN_MISREAD_REASON)
    assert claim.status == "unknown"
    assert "SUPPORT_REVIEW_MISREAD" in claim.reason


def test_legit_c7_still_lands_stale():
    """#243 回归:合法 stale 落档不受读反闸影响。"""
    claim = Claim(claim_id="c7", statement="SeaDesk 客单价 99 美元/月",
                  t0_evidence_ids=["t0-competitor-notes#p2"])
    decision = ClaimDecision(
        claim_id="c7", status="stale", reason=C7_LEGIT,
        evidence_ids=["t0-competitor-notes#p2@T1"],
        auditor_verdict="stale", auditor_reason="反证成立,维度相符",
        auditor_dimension_match=True,
    )
    Runner(_StubStore())._finalize(claim, decision)  # noqa: SLF001
    assert claim.status == "stale"
