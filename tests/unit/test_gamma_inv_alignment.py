"""Batch3 γ-INV-1 / γ-INV-2 确定性检查(#118)。

层 = invariant:逐位一致,零 LLM。挂靠既有主缝
Lead 判定包 → Runner._finalize → rule_gate(及 Lead 受理层预检)。
只断言外部行为(落档状态 / error_code / 异议记录)。
本文件不是冒烟,也不把主链抗假绿仅表明句当作通过线。
"""

import pytest

from freshlatch.gates.rule_gate import (
    ERR_DIMENSION_CROSSCHECK_MISMATCH,
    GateContext,
    GateDecision,
    arbitrate_unknown,
    rule_gate,
    seal_no_unfounded_fresh,
)
from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import ClaimDecision, RunContext, Runner
from freshlatch.store.base import Chunk, Document, InMemoryStore

CLAIM_ID = "cx"
EID = "t0-cost-model#p2@T1"
DOC = "t0-cost-model"
REASON = ("T1 成本模型原文显示我方单会话成本 0.009 美元低于竞品折算 0.019 美元,"
          "推翻成本优势消失的前提")
AUD_STALE_REASON = "T1 原文同一度量维度推翻该前提"


class _NoLLM:
    """确定性检查不得打到模型。"""

    def chat(self, *args, **kwargs):
        raise AssertionError("γ-INV 检查为零 LLM")


def _seeded_store() -> InMemoryStore:
    """#150:fresh 构造 validity_basis 须点回 T1 chunk;仲裁单测种最小种子。"""
    store = InMemoryStore()
    chunk = Chunk(
        doc_id=DOC, chunk_id=f"{DOC}-p2", clause_id="p2", title="成本模型",
        text="T1 复测:我方单会话成本 0.009 美元。", source_type="internal",
        as_of="T1", doc_version="v2", checksum="fp-gamma", tokens=20,
    )
    store.add_document(
        Document(
            doc_id=DOC, as_of="T1", source_type="internal", title="成本模型",
            doc_version="v2", checksum="fp-gamma", full_text=chunk.text,
        ),
        [chunk],
    )
    return store


def _finalize(status: str, *, auditor_verdict=None, auditor_reason="",
              auditor_dimension_match=None, evidence=None, dimension=None,
              stale_dimension=None, dimension_objection=None,
              prior_dissent=None) -> Claim:
    runner = Runner(_seeded_store())
    claim = Claim(claim_id=CLAIM_ID, statement="我方单会话服务成本仍低于竞品",
                  t0_evidence_ids=["t0-cost-model#p2"], dimension=dimension)
    if prior_dissent is not None:
        claim.dissent = prior_dissent
    decision = ClaimDecision(
        claim_id=CLAIM_ID, status=status, reason=REASON,
        evidence_ids=evidence if evidence is not None else [EID],
        auditor_verdict=auditor_verdict, auditor_reason=auditor_reason,
        auditor_dimension_match=auditor_dimension_match,
        stale_dimension=stale_dimension,
        dimension_objection=dimension_objection,
    )
    runner._finalize(claim, decision)
    return claim


def _assert_not_unfounded_fresh(claim: Claim, auditor_verdict) -> None:
    """无 Auditor,或仍携带异议,不得留在 fresh。"""
    if auditor_verdict != "fresh" or claim.dissent is not None:
        assert claim.status != "fresh"


# -- γ-INV-1:ADR-0009 3×3,fresh 唯一绿格 -------------------------------------------------


@pytest.mark.parametrize(
    "lead,auditor,expect_status,expect_dissent",
    [
        ("fresh", "fresh", "fresh", False),
        ("fresh", "stale", "stale", False),
        ("fresh", "unknown", "unknown", False),
        ("fresh", None, "unknown", False),
        ("unknown", "fresh", "unknown", True),
        ("unknown", "stale", "stale", False),
        ("unknown", "unknown", "unknown", False),
        ("unknown", None, "unknown", False),
        ("stale", "fresh", "stale", True),
        ("stale", "stale", "stale", False),
        ("stale", "unknown", "stale", False),
        ("stale", None, "unknown", False),
    ],
)
def test_gamma_inv1_truth_table(lead, auditor, expect_status, expect_dissent):
    """双判一致真值表与 ADR-0009 一致;无 Auditor / 带异议仍绿 = 失败。"""
    claim = _finalize(
        lead, auditor_verdict=auditor,
        auditor_reason=AUD_STALE_REASON if auditor else "",
    )
    assert claim.status == expect_status
    assert (claim.status == "fresh") == (lead == "fresh" and auditor == "fresh")
    if expect_dissent:
        assert claim.dissent is not None
        assert claim.dissent["kind"] == "auditor_semantic"
        assert claim.dissent["auditor_verdict"] == auditor
        assert claim.dissent["evidence_ids"] == [EID]
    else:
        assert claim.dissent is None
    _assert_not_unfounded_fresh(claim, auditor)


def test_gamma_inv1_auditor_absent_reason_observable():
    """Auditor 缺席的 fresh 收口形状可观察,不是静默仍绿。"""
    claim = _finalize("fresh", auditor_verdict=None)
    assert claim.status == "unknown"
    assert "缺席" in claim.reason


def test_gamma_inv1_unknown_x_auditor_fresh_dissent_not_green():
    """Lead unknown × Auditor fresh → unknown + 异议,不得改绿。"""
    claim = _finalize("unknown", auditor_verdict="fresh",
                      auditor_reason="Auditor 认为主张仍成立")
    assert claim.status == "unknown"
    assert "双判未一致" in claim.reason
    assert claim.dissent["auditor_verdict"] == "fresh"
    assert "Auditor 认为主张仍成立" in claim.dissent["reason"]


def test_gamma_inv1_unknown_x_auditor_stale_lands_stale():
    """含 stale 落 stale:unknown 行不把 Auditor stale 吞成无声 unknown。"""
    claim = _finalize("unknown", auditor_verdict="stale",
                      auditor_reason=AUD_STALE_REASON)
    assert claim.status == "stale"
    assert "含 stale 落 stale" in claim.reason
    assert claim.dissent is None


def test_gamma_inv1_agreed_fresh_clears_prior_dissent():
    """本轮双判一致的 fresh 收口清除上轮异议,绿灯不携带 dissent。"""
    claim = _finalize(
        "fresh", auditor_verdict="fresh", auditor_reason="T1 复测支持",
        prior_dissent={"kind": "mechanical_precheck", "auditor_verdict": None,
                       "reason": "上轮预检", "evidence_ids": [EID]},
    )
    assert claim.status == "fresh"
    assert claim.dissent is None


def test_gamma_inv1_fresh_without_t1_not_green():
    """双判一致仍须过闸:无 T1 不得 fresh,打回码可观察。"""
    claim = _finalize("fresh", auditor_verdict="fresh", evidence=[])
    assert claim.status == "unknown"
    assert "NO_T1_EVIDENCE" in claim.reason


def test_arbitrate_unknown_row():
    assert arbitrate_unknown("fresh") == ("unknown", True)
    assert arbitrate_unknown("stale") == ("stale", False)
    assert arbitrate_unknown("unknown") == ("unknown", False)
    assert arbitrate_unknown(None) == ("unknown", False)
    assert arbitrate_unknown("green") == ("unknown", False)


def test_seal_downgrades_unfounded_fresh_and_keeps_dissent():
    """加固失败收口:已写上的 fresh 在 Auditor 缺席或未一致时打回,异议保留。"""
    claim = Claim(claim_id=CLAIM_ID, statement="s", status="fresh")
    claim.dissent = {"kind": "auditor_semantic", "auditor_verdict": "stale",
                     "reason": "异议", "evidence_ids": [EID]}
    seal_no_unfounded_fresh(claim, None)
    assert claim.status == "unknown"
    assert "AUDITOR_ABSENT" in claim.reason
    assert claim.dissent["kind"] == "auditor_semantic"

    claim.status = "fresh"
    seal_no_unfounded_fresh(claim, "stale")
    assert claim.status == "unknown"
    assert "ARBITRATION_MISMATCH" in claim.reason
    assert claim.dissent is not None


# -- γ-INV-2:维度不符不得放行 stale;预检 / 跨检 / 异议可机械复现 ---------------------------


def test_gamma_inv2_gate_dimension_mismatch_not_released():
    """不变量 7:dimension_match=False 不得放行 stale,且不发绿。"""
    claim = Claim(claim_id=CLAIM_ID, statement="s")
    result = rule_gate(
        claim,
        GateDecision(status="stale", t1_evidence_ids=[EID], stale_reason=REASON,
                     auditor_verdict="stale", auditor_dimension_match=False),
        GateContext(),
    )
    assert result.allowed is False
    assert result.green is False
    assert result.error_code == "DIMENSION_MISMATCH"


def test_gamma_inv2_gate_crosscheck_before_absent():
    """不变量 8:登记维度 ≠ 反证自标维度打回,且先于 Auditor 缺席。"""
    claim = Claim(claim_id=CLAIM_ID, statement="s", dimension="cost_model")
    result = rule_gate(
        claim,
        GateDecision(status="stale", t1_evidence_ids=[EID], stale_reason=REASON,
                     auditor_verdict=None,
                     registered_dimension="cost_model",
                     stale_dimension="competitor_pricing"),
        GateContext(),
    )
    assert result.allowed is False and result.green is False
    assert result.error_code == ERR_DIMENSION_CROSSCHECK_MISMATCH


def test_gamma_inv2_finalize_crosscheck_unknown_with_dissent():
    """闸层跨检兜底:错配 stale 落 unknown + mechanical_crosscheck,不是 stale。"""
    claim = _finalize(
        "stale", auditor_verdict="stale", auditor_dimension_match=True,
        auditor_reason="反证成立", dimension="cost_model",
        stale_dimension="competitor_pricing",
    )
    assert claim.status == "unknown"
    assert "DIMENSION_CROSSCHECK_MISMATCH" in claim.reason
    assert claim.dissent["kind"] == "mechanical_crosscheck"
    assert "competitor_pricing" in claim.dissent["reason"]


def test_gamma_inv2_finalize_semantic_mismatch_unknown_with_dissent():
    """不变量 7 落档:维度异议 → unknown + auditor_semantic,不得 stale。"""
    claim = _finalize(
        "stale", auditor_verdict="stale", auditor_dimension_match=False,
        auditor_reason="反证锚定的是定价维度",
    )
    assert claim.status == "unknown"
    assert "DIMENSION_MISMATCH" in claim.reason
    assert claim.dissent["kind"] == "auditor_semantic"
    assert claim.dissent["auditor_verdict"] == "stale"


def test_gamma_inv2_fresh_overruled_stale_respects_dimension_mismatch():
    """fresh × Auditor stale 且维度不符:不造维度不符的 stale 落档。"""
    claim = _finalize(
        "fresh", auditor_verdict="stale", auditor_dimension_match=False,
        auditor_reason="包内证据维度不符",
    )
    assert claim.status == "unknown"
    assert "DIMENSION_MISMATCH" in claim.reason
    assert claim.dissent["kind"] == "auditor_semantic"


def test_gamma_inv2_unknown_row_cannot_bypass_dimension_mismatch():
    """unknown × Auditor stale 仍过闸:维度不符不得借 unknown 行放行 stale。"""
    claim = _finalize(
        "unknown", auditor_verdict="stale", auditor_dimension_match=False,
        auditor_reason="反证维度不符",
    )
    assert claim.status == "unknown"
    assert "DIMENSION_MISMATCH" in claim.reason
    assert claim.dissent["kind"] == "auditor_semantic"


def test_gamma_inv2_unknown_row_cannot_bypass_crosscheck():
    claim = _finalize(
        "unknown", auditor_verdict="stale", auditor_reason=AUD_STALE_REASON,
        dimension="cost_model", stale_dimension="competitor_pricing",
    )
    assert claim.status == "unknown"
    assert "DIMENSION_CROSSCHECK_MISMATCH" in claim.reason
    assert claim.dissent["kind"] == "mechanical_crosscheck"


def test_gamma_inv2_precheck_blocks_before_auditor_and_hangs_dissent():
    """受理层预检:错配整 call 拒绝,零 Auditor,落档 unknown + mechanical_precheck。"""
    claim = Claim(claim_id="c5", statement="s", dimension="cost_model")
    ctx = RunContext(store=InMemoryStore(), guardrails=Guardrails())
    lead = LeadReverifier(ctx, claim, _NoLLM())
    lead._seen_evidence.add("t0-x#p2@T1")
    res = lead._t_mark_stale({
        "claim_id": "c5",
        "reason": REASON,
        "evidence_ids": ["t0-x#p2@T1"],
        "dimension": "competitor_pricing",
    })
    assert "error" in res
    assert "不符" in res["error"]
    assert lead.decision.status == "unknown"
    assert lead.decision.auditor_verdict is None
    assert lead._objection["error_code"] == ERR_DIMENSION_CROSSCHECK_MISMATCH
    assert not any(e.get("type") == "auditor_spawn" for e in ctx.events)

    lead.decision.dimension_objection = lead._objection
    Runner(InMemoryStore())._finalize(claim, lead.decision)
    assert claim.status == "unknown"
    assert claim.dissent["kind"] == "mechanical_precheck"
    assert "ADR-0012" in claim.dissent["reason"]
    assert "cost_model" not in claim.dissent["reason"]
