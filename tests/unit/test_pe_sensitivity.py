"""#528 PE-Y-SENS-01：GATE-Y-SENSITIVITY 敏感性闸（S1–S4 · 可扔报告）。

表驱动 stub：坏样本强制低 entail、正确样本高 entail。
断言通过线布尔与报告字段；stub 绿 ≠ 可激活前置。
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_verify as verify_mod
from freshlatch.eval.patch_events_construct import STRATA
from freshlatch.eval.patch_events_sensitivity import (
    BAD_OK_FALSE_MIN,
    CORRECT_OK_TRUE_MIN,
    REPORT_LAYER_STUB,
    SENSITIVITY_SET_S,
    assert_set_s_locked,
    evaluate_s1_s4,
    make_table_driven_nli_stub,
    render_sensitivity_report,
    run_sensitivity_cases,
    write_sensitivity_report,
)
from freshlatch.eval.patch_events_verify import ENTAILMENT_TAU, XNLI_MODEL_ID


@pytest.fixture(autouse=True)
def _stub_nli(monkeypatch):
    stub = make_table_driven_nli_stub(SENSITIVITY_SET_S)
    monkeypatch.setattr(verify_mod, "predict_xnli_probs", stub)


def test_set_s_is_locked_four_strata_times_mod4():
    assert_set_s_locked(SENSITIVITY_SET_S)
    for stratum in STRATA:
        for op in range(4):
            assert any(
                s.kind == "construct_bad"
                and s.stratum == stratum
                and s.operator == op
                for s in SENSITIVITY_SET_S
            )
    assert any(s.kind == "abolish_trap" for s in SENSITIVITY_SET_S)
    assert any(s.kind == "version_trap" for s in SENSITIVITY_SET_S)
    assert sum(1 for s in SENSITIVITY_SET_S if s.gold == "正确") >= 4


def test_s1_s4_pass_under_table_driven_stub():
    rows = run_sensitivity_cases(SENSITIVITY_SET_S)
    summary = evaluate_s1_s4(rows)
    assert summary["s1"] is True
    assert summary["s2"] is True
    assert summary["s3"] is True
    assert summary["s4"] is True
    assert summary["sensitivity_passed"] is True
    assert summary["n_score_none"] == 0
    assert summary["bad_ok_false_rate"] >= BAD_OK_FALSE_MIN
    assert summary["correct_ok_true_rate"] >= CORRECT_OK_TRUE_MIN
    assert summary["model_id"] == XNLI_MODEL_ID
    assert summary["tau"] == ENTAILMENT_TAU


def test_reject_scores_are_neg_inf_never_none():
    rows = run_sensitivity_cases(SENSITIVITY_SET_S)
    for row in rows:
        assert row["score"] is not None
        if row["ok"] is False:
            assert type(row["score"]) is float
            assert math.isinf(row["score"]) and row["score"] < 0
        else:
            assert math.isfinite(row["score"])
            assert 0.0 <= row["score"] <= 1.0


def test_bad_forced_low_entail_correct_forced_high(monkeypatch):
    """表驱动可控：坏强制低 entail、正确强制高 entail。"""
    calls: list[tuple[str, str]] = []

    def recording_stub(premise: str, hypothesis: str) -> dict[str, float]:
        calls.append((premise, hypothesis))
        base = make_table_driven_nli_stub(SENSITIVITY_SET_S)
        return base(premise, hypothesis)

    monkeypatch.setattr(verify_mod, "predict_xnli_probs", recording_stub)
    rows = run_sensitivity_cases(SENSITIVITY_SET_S)
    assert len(calls) == len(SENSITIVITY_SET_S)
    for row in rows:
        if row["gold"] == "坏":
            assert row["ok"] is False
        else:
            assert row["ok"] is True


def test_s2_fails_when_bad_always_accepted(monkeypatch):
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda _p, _h: {"entailment": 0.99, "neutral": 0.005, "contradiction": 0.005},
    )
    rows = run_sensitivity_cases(SENSITIVITY_SET_S)
    summary = evaluate_s1_s4(rows)
    assert summary["s2"] is False
    assert summary["sensitivity_passed"] is False


def test_s4_fails_on_wrong_tau_or_model():
    rows = run_sensitivity_cases(SENSITIVITY_SET_S)
    bad_tau = evaluate_s1_s4(rows, tau=0.9)
    assert bad_tau["s4"] is False
    bad_model = evaluate_s1_s4(rows, model_id="not-the-pin")
    assert bad_model["s4"] is False


def test_report_firewall_fields(tmp_path: Path):
    out = tmp_path / "GATE-Y-SENSITIVITY.md"
    payload = write_sensitivity_report(
        out,
        inference_layer=REPORT_LAYER_STUB,
        activation_prerequisite_met=False,
    )
    text = out.read_text(encoding="utf-8")
    assert payload["gate_passed"] is False
    assert payload["activation_prerequisite_met"] is False
    assert payload["inference_layer"] == REPORT_LAYER_STUB
    assert "夹具/stub 层 · 非真模型过线" in text
    assert "不进 `RESULT-Y`" in text or "不进 RESULT-Y" in text
    assert "gate_passed**：否" in text
    assert "activation_prerequisite_met**：否" in text
    assert "禁止放宽" in text
    assert XNLI_MODEL_ID in text
    assert str(ENTAILMENT_TAU) in text


def test_stub_cannot_claim_activation_prerequisite():
    summary = evaluate_s1_s4(run_sensitivity_cases(SENSITIVITY_SET_S))
    with pytest.raises(ValueError, match="stub"):
        render_sensitivity_report(
            summary,
            run_sensitivity_cases(SENSITIVITY_SET_S),
            inference_layer=REPORT_LAYER_STUB,
            activation_prerequisite_met=True,
        )


def test_report_does_not_mention_result_y_pass_or_yi_guarantee(tmp_path: Path):
    out = tmp_path / "GATE-Y-SENSITIVITY.md"
    write_sensitivity_report(out)
    text = out.read_text(encoding="utf-8")
    assert "保证乙" not in text or "不保证乙" in text
    assert "gate_passed**：否" in text
    assert "RESULT-Y" in text  # 防火墙提及
