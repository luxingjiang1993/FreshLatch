"""SLO-02 硬闸违例计数/清单回归（B6/B7/C5/D3/C3）。

复用既有闸语义；断言计数/清单可观察；不放宽 fail-closed。
"""

from __future__ import annotations

from pathlib import Path

from freshlatch.evidence_bound import (
    PATCH_EMPTY_T1,
    PATCH_T1_NOT_ARCHIVED,
    PatchDraftStore,
    confirm_patch,
    propose_patch,
)
from freshlatch.gates.human_latch import apply_decisions
from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import Claim
from freshlatch.slo_hard_gate_violations import (
    HardGateReport,
    classify_confirm_reject,
    classify_renew_reject,
    classify_rule_gate_reject,
    probe_c5_agent_cannot_self_green,
    probe_d3_no_t1_fresh,
    record_confirm_outcome,
    record_renew_outcome,
    run_acceptance_probes,
    scan_b7_unconfirmed_drafts,
)


def _noop_reverify(claim: Claim) -> tuple[str, str]:
    return claim.status, "noop"


# ---------------------------------------------------------------------------
# 分类器（ops ID 对齐）
# ---------------------------------------------------------------------------


def test_classify_maps_error_codes_to_slo_ids():
    assert classify_confirm_reject(PATCH_EMPTY_T1) == "B6"
    assert classify_confirm_reject(PATCH_T1_NOT_ARCHIVED) == "B6"
    assert classify_confirm_reject("PATCH_INELIGIBLE") is None
    assert classify_renew_reject("RENEW_NO_EVIDENCE") == "C3"
    assert classify_rule_gate_reject("NO_T1_EVIDENCE") == "D3"


# ---------------------------------------------------------------------------
# Acceptance: B6
# ---------------------------------------------------------------------------


def test_b6_empty_t1_confirm_block_observable(tmp_path: Path):
    """Given 无合法 t1_ids 的 confirm, When 走 confirm_patch, Then 拒绝且 B6 block≥1。"""
    claims = [Claim(claim_id="c1", statement="旧", status="unknown")]
    before = claims[0].statement
    events_dir = tmp_path / "pe"
    result = confirm_patch(
        claim_id="c1",
        claims=claims,
        archived_t1_ids={"doc#a@T1"},
        after_text="无证改",
        t1_ids=[],
        minutes=1.0,
        events_dir=events_dir,
        reverify_fn=_noop_reverify,
    )
    assert not result.ok
    assert result.error_code == PATCH_EMPTY_T1
    assert claims[0].statement == before

    report = HardGateReport()
    record_confirm_outcome(
        report,
        ok=result.ok,
        error_code=result.error_code,
        claim_id="c1",
        detail=result.detail,
    )
    assert report.blocks("B6") >= 1
    assert report.violations("B6") == 0


# ---------------------------------------------------------------------------
# Acceptance: B7
# ---------------------------------------------------------------------------


def test_b7_unconfirmed_draft_scan_pass(tmp_path: Path):
    """Given 未 confirm 草案, When 检查正文/正式账本, Then 未写入；清单 scan_pass。"""
    claims = [Claim(claim_id="c1", statement="正文不变", status="stale")]
    snaps = {"c1": claims[0].statement}
    drafts = PatchDraftStore()
    events_dir = tmp_path / "pe"
    propose_patch(
        claim_id="c1",
        after_text="仅草案",
        claims=claims,
        drafts=drafts,
        run_id="r1",
        t1_ids=["doc#a@T1"],
    )
    assert claims[0].statement == "正文不变"
    report = HardGateReport()
    scan_b7_unconfirmed_drafts(
        report,
        claims=claims,
        drafts=drafts,
        run_id="r1",
        events_dir=events_dir,
        statement_snapshots=snaps,
    )
    assert report.count("B7", "scan_pass") >= 1
    assert report.violations("B7") == 0


# ---------------------------------------------------------------------------
# Acceptance: D3 / C5
# ---------------------------------------------------------------------------


def test_d3_no_t1_fresh_blocked_violation_target_zero():
    """Given 无 T1 置 fresh, When 走 rule_gate, Then 失败且 D3 违例目标语义=0。"""
    claim = Claim(claim_id="c1", statement="x", status="stale")
    gate = rule_gate(
        claim,
        GateDecision(status="fresh", t1_evidence_ids=[], auditor_verdict="fresh"),
        GateContext(),
    )
    assert not gate.green
    assert gate.error_code == "NO_T1_EVIDENCE"

    report = HardGateReport()
    probe_d3_no_t1_fresh(report, claim=claim)
    assert report.blocks("D3") >= 1
    assert report.violations("D3") == 0


def test_c5_agent_cannot_self_red_to_green():
    """Given Agent 自红转绿尝试形状, When 走闸/白名单机检, Then 失败且 C5 违例=0。"""
    report = HardGateReport()
    probe_c5_agent_cannot_self_green(report)
    assert report.blocks("C5") >= 1
    assert report.violations("C5") == 0


# ---------------------------------------------------------------------------
# Acceptance: C3
# ---------------------------------------------------------------------------


def test_c3_renew_without_t1_rejects_no_validity_basis():
    """Given renew 无新 T1, When 受理, Then 拒绝；不得写 validity_basis。"""

    class _Store:
        def list_invalidation(self):
            return []

        def get_chunk(self, *a, **k):
            return None

        def log_latch(self, *a, **k):
            return None

        def add_invalidation(self, *a, **k):
            return None

        def list_latch_events(self, claim_id=None):
            return []

    claim = Claim(
        claim_id="c1",
        statement="续命",
        status="stale",
        validity_basis=None,
    )
    results = apply_decisions(
        _Store(),
        {"c1": claim},
        [{"claim_id": "c1", "action": "renew"}],
    )
    assert results[0]["ok"] is False
    assert results[0]["error_code"] == "RENEW_NO_EVIDENCE"
    assert claim.validity_basis is None
    assert claim.status == "stale"

    report = HardGateReport()
    record_renew_outcome(
        report,
        ok=False,
        error_code=results[0]["error_code"],
        claim_id="c1",
        validity_basis_before=None,
        validity_basis_after=claim.validity_basis,
        detail=results[0]["detail"],
    )
    assert report.blocks("C3") >= 1
    assert report.violations("C3") == 0


# ---------------------------------------------------------------------------
# 端到端探针 + 周报字段
# ---------------------------------------------------------------------------


def test_run_acceptance_probes_week_fields_zero_violations(tmp_path: Path):
    report = run_acceptance_probes(tmp_events_dir=tmp_path / "events")
    fields = report.week_fields()
    assert report.blocks("B6") >= 1
    assert report.blocks("C3") >= 1
    assert report.count("B7", "scan_pass") >= 1
    assert report.blocks("D3") >= 1
    assert report.blocks("C5") >= 1
    for sid in ("B6", "B7", "C5", "D3", "C3"):
        assert fields["hard_gate_violation_counts"][sid] == 0
    assert "hard_gate_block_counts" in fields
    assert len(fields["records"]) >= 5
