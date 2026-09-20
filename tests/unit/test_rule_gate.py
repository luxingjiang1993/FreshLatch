"""规则闸四条不变量单测(§7.1 W1-4)。纯函数直测,零 LLM、零磁盘。"""

import pytest

from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import AsOf, Claim


def make_claim(claim_id: str = "c1") -> Claim:
    return Claim(claim_id=claim_id, statement="测试主张", t0_evidence_ids=["t0-x#p2"])


def make_ctx(**kw) -> GateContext:
    kw.setdefault("checksum_fn", lambda doc_id, as_of: None)
    return GateContext(**kw)


def test_stale_not_green():
    """不变量 1:stale/unknown 不得绿灯(可落档,但 green 恒 False)。"""
    for status in ("stale", "unknown"):
        d = GateDecision(status=status,
                         t1_evidence_ids=["t0-x#p2@T1"] if status == "stale" else [],
                         auditor_verdict="stale" if status == "stale" else None)
        r = rule_gate(make_claim(), d, make_ctx())
        assert r.allowed and not r.green


def test_stale_without_evidence_blocked():
    """不变量 5(#15):stale 必须携带可点回的 t1 反证,无反证打回落 unknown。"""
    r = rule_gate(make_claim(), GateDecision(status="stale", t1_evidence_ids=[]), make_ctx())
    assert not r.allowed and not r.green and r.error_code == "NO_STALE_EVIDENCE"


def test_stale_with_evidence_passes_not_green():
    """不变量 5 正例:带反证的 stale 落档放行,但恒不绿灯。"""
    d = GateDecision(status="stale", t1_evidence_ids=["t0-x#p2@T1"],
                     auditor_verdict="stale")
    r = rule_gate(make_claim(), d, make_ctx())
    assert r.allowed and not r.green


def test_no_t1_evidence_not_fresh():
    """不变量 2:无 t1_evidence_ids 不得 fresh。"""
    r = rule_gate(make_claim(), GateDecision(status="fresh", t1_evidence_ids=[]), make_ctx())
    assert not r.allowed and not r.green and r.error_code == "NO_T1_EVIDENCE"


def test_checksum_mismatch_not_fresh():
    """不变量 3:checksum 对不上不得 fresh/续命。"""
    ctx = make_ctx(checksum_fn=lambda doc_id, as_of: "real-checksum")
    d = GateDecision(status="fresh", t1_evidence_ids=["t0-x#p2"],
                     validity_basis={"doc_id": "t0-x", "checksum": "tampered"},
                     auditor_verdict="fresh")
    r = rule_gate(make_claim(), d, ctx)
    assert not r.allowed and r.error_code == "CHECKSUM_MISMATCH"


def test_checksum_placeholder_empty_passes():
    """三处留位本期为空:checksum_fn 返回 None/空 = 未启用,不拦截。"""
    ctx = make_ctx(checksum_fn=lambda doc_id, as_of: None)
    d = GateDecision(status="fresh", t1_evidence_ids=["t0-x#p2"], auditor_verdict="fresh")
    r = rule_gate(make_claim(), d, ctx)
    assert r.green


def test_invalidation_list_blocks_fresh():
    """不变量 4:作废名单内不得 fresh(重跑打回)。"""
    ctx = make_ctx(invalidation_list={"c1"})
    d = GateDecision(status="fresh", t1_evidence_ids=["t0-x#p2"], auditor_verdict="fresh")
    r = rule_gate(make_claim("c1"), d, ctx)
    assert not r.allowed and not r.green and r.error_code == "INVALIDATED"
    # 名单外不受影响
    r2 = rule_gate(make_claim("c2"), d, ctx)
    assert r2.green


def test_stale_meta_only_disproof_blocked():
    """不变量 6(#17):stale 反证不得为纯元陈述——打回 META_ONLY_DISPROOF,经 runner 落 unknown。"""
    from tests.unit.test_meta_gate import C9_RUN2_REASON
    d = GateDecision(status="stale", t1_evidence_ids=["t0-messaging-survey#p3@T1"],
                     stale_reason=C9_RUN2_REASON, auditor_verdict="stale")
    r = rule_gate(make_claim("c9"), d, make_ctx())
    assert not r.allowed and not r.green and r.error_code == "META_ONLY_DISPROOF"


def test_stale_legit_reason_passes():
    """不变量 6 正例:含数值锚的实质反证照常放行(不误伤合法 stale)。"""
    from tests.unit.test_meta_gate import C7_LEGIT
    d = GateDecision(status="stale", t1_evidence_ids=["t0-competitor-notes#p2@T1"],
                     stale_reason=C7_LEGIT, auditor_verdict="stale")
    r = rule_gate(make_claim("c7"), d, make_ctx())
    assert r.allowed and not r.green


def test_stale_empty_reason_not_meta_blocked():
    """不变量 6 向后兼容:stale_reason 缺省(空)不做元陈述校验,老调用点行为不变。"""
    d = GateDecision(status="stale", t1_evidence_ids=["t0-x#p2@T1"],
                     auditor_verdict="stale")
    r = rule_gate(make_claim(), d, make_ctx())
    assert r.allowed and not r.green


def test_renew_path_also_gated():
    """续命(renew)同样过闸:名单与 checksum 都管。"""
    ctx = make_ctx(invalidation_list={"c1"})
    d = GateDecision(status="renew", t1_evidence_ids=["t0-x#p2"])
    assert not rule_gate(make_claim("c1"), d, ctx).green
    assert rule_gate(make_claim("c2"), d, make_ctx()).green
