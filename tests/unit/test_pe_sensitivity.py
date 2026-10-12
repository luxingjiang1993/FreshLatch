"""#528 PE-Y-SENS-01：GATE-Y-SENSITIVITY 敏感性闸（S1–S4 · 可扔报告）。

表驱动 stub：坏样本强制低 entail、正确样本高 entail。
断言通过线布尔与报告字段；stub 绿 ≠ 可激活前置。
"""

from __future__ import annotations

import json
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


def test_formal_freeze_sha256_is_the_544_digest():
    """正式 S 的哈希来自冻结 jsonl，不是代码内 24 条，也不是 #543 过早哈希。"""
    from freshlatch.eval.patch_events_sensitivity import (
        FORMAL_FREEZE_SHA256,
        OLD_INCODE_SET_SHA256,
        PREMATURE_PR543_SHA256,
        formal_freeze_sha256,
        load_formal_freeze,
    )

    _header, records, _raw = load_formal_freeze()
    digest = formal_freeze_sha256(records)
    assert digest == FORMAL_FREEZE_SHA256
    assert digest == "e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19"
    assert digest != PREMATURE_PR543_SHA256
    assert digest != OLD_INCODE_SET_SHA256
    assert len(SENSITIVITY_SET_S) == 24
    old_ids = {sample.sample_id for sample in SENSITIVITY_SET_S}
    assert "S-删除-op1" in old_ids
    assert "S-删除-op3" in old_ids
    assert "DIAG-CHEF-03-bad" not in old_ids


def test_formal_freeze_keeps_must_carry_and_s2_denominator(capsys, monkeypatch):
    """CHEF 好侧在 stub 下不为 ok=True 时对无效，坏侧仍留在 20 条分母里。"""
    from freshlatch.eval.patch_events_sensitivity import (
        FORMAL_FREEZE_SHA256,
        run_sens_live2,
    )

    seen: list[str] = []
    checked = {"done": False}

    def _spy(premise: str, hypothesis: str) -> dict[str, float]:
        if not checked["done"]:
            out = capsys.readouterr().out
            assert f"FROZEN_S_SHA256 {FORMAL_FREEZE_SHA256}" in out
            assert "BEGIN_SCORING" in out
            assert out.index(f"FROZEN_S_SHA256 {FORMAL_FREEZE_SHA256}") < out.index(
                "BEGIN_SCORING"
            )
            checked["done"] = True
        seen.append("predict")
        return {"entailment": 0.05, "neutral": 0.10, "contradiction": 0.85}

    monkeypatch.setattr(verify_mod, "predict_xnli_probs", _spy)
    payload = run_sens_live2(log=None)
    text = capsys.readouterr().out
    assert f"FROZEN_S_SHA256_AFTER {FORMAL_FREEZE_SHA256}" in text
    assert checked["done"] is True
    assert seen
    assert payload["activation_prerequisite_met"] is False
    assert payload["summary"]["n_bad"] == 20
    assert payload["summary"]["n_correct"] == 6
    bad_ids = {row["sample_id"] for row in payload["rows"] if row["gold"] == "坏"}
    assert "DIAG-CHEF-03-bad" in bad_ids
    assert "DIAG-CHEF-04-bad" in bad_ids
    assert payload["pair_validity"]["DIAG-CHEF-03"] == "无效"
    assert payload["pair_validity"]["DIAG-CHEF-04"] == "无效"
    chef03 = next(row for row in payload["rows"] if row["sample_id"] == "DIAG-CHEF-03-bad")
    assert chef03["must_carry"] is True
    assert "不少于 3 年" in chef03["after_text"]
    assert "不少于 5 年" in chef03["evidence_text"]
    chef04 = next(row for row in payload["rows"] if row["sample_id"] == "DIAG-CHEF-04-bad")
    assert "大约" in chef04["evidence_text"]
    assert "大约" not in chef04["after_text"]


def _crlf_verify_copy(tmp_path: Path) -> Path:
    """先把工作区字节折成 LF，再合成 CRLF。LF 与 CRLF checkout 走同一条路径。"""
    from freshlatch.eval.patch_events_sensitivity import _verify_py_path

    raw = _verify_py_path().read_bytes()
    path = tmp_path / "patch_events_verify.py"
    path.write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    return path


def test_verify_py_crlf_matches_lf_pin_but_content_change_does_not(tmp_path: Path, monkeypatch):
    """CRLF 检出不得假性打破仪器锁；改 τ 文本后摘要必须离开 LF 冻结值。"""
    import hashlib

    from freshlatch.eval import patch_events_sensitivity as sens

    raw = sens._verify_py_path().read_bytes()
    # 真实工作区内容未改：只比折行后的摘要，原字节不对钉。
    assert sens._verify_py_sha256() == sens.VERIFY_PY_SHA256
    crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    assert hashlib.sha256(crlf).hexdigest() != sens.VERIFY_PY_SHA256
    crlf_path = tmp_path / "patch_events_verify.py"
    crlf_path.write_bytes(crlf)
    monkeypatch.setattr(sens, "_verify_py_path", lambda: crlf_path)
    assert sens._verify_py_sha256() == sens.VERIFY_PY_SHA256

    changed = crlf.replace(b"ENTAILMENT_TAU = 0.5", b"ENTAILMENT_TAU = 0.4", 1)
    assert changed != crlf
    changed_path = tmp_path / "patch_events_verify_changed.py"
    changed_path.write_bytes(changed)
    monkeypatch.setattr(sens, "_verify_py_path", lambda: changed_path)
    assert sens._verify_py_sha256() != sens.VERIFY_PY_SHA256


def test_crlf_checkout_keeps_must_carry_gate(tmp_path: Path, monkeypatch):
    """Windows 语义下，仪器锁通过后仍走正式 S 的 must-carry / 分母断言。"""
    from freshlatch.eval import patch_events_sensitivity as sens

    crlf_path = _crlf_verify_copy(tmp_path)
    monkeypatch.setattr(sens, "_verify_py_path", lambda: crlf_path)
    assert sens._verify_py_sha256() == sens.VERIFY_PY_SHA256
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda _p, _h: {"entailment": 0.05, "neutral": 0.10, "contradiction": 0.85},
    )
    payload = sens.run_sens_live2(log=None)
    assert payload["summary"]["n_bad"] == 20
    bad_ids = {row["sample_id"] for row in payload["rows"] if row["gold"] == "坏"}
    assert "DIAG-CHEF-03-bad" in bad_ids
    assert "DIAG-CHEF-04-bad" in bad_ids


def test_hash_mismatch_does_not_call_nli(tmp_path: Path, monkeypatch):
    from freshlatch.eval.patch_events_sensitivity import load_formal_freeze, run_sens_live2

    _header, records, _raw = load_formal_freeze()
    called: list[str] = []

    def _boom(_premise: str, _hypothesis: str) -> dict[str, float]:
        called.append("predict")
        return {"entailment": 0.1, "neutral": 0.1, "contradiction": 0.8}

    monkeypatch.setattr(verify_mod, "predict_xnli_probs", _boom)
    path = tmp_path / "formal-S.jsonl"
    mutated = dict(records[0])
    mutated["note"] = str(mutated["note"]) + "改"
    header, _records, raw = load_formal_freeze()
    lines = [json.dumps(header, ensure_ascii=False, sort_keys=True)]
    lines.append(json.dumps(mutated, ensure_ascii=False, sort_keys=True))
    for record in records[1:]:
        lines.append(json.dumps(record, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert raw
    with pytest.raises(RuntimeError, match="正式冻结"):
        run_sens_live2(freeze_path=path, log=None)
    assert called == []


def test_hash_mismatch_under_crlf_does_not_call_nli(tmp_path: Path, monkeypatch):
    """CRLF 仪器锁通过后，名单哈希不符仍拒绝开跑，且不调用 NLI。"""
    from freshlatch.eval import patch_events_sensitivity as sens

    crlf_path = _crlf_verify_copy(tmp_path)
    monkeypatch.setattr(sens, "_verify_py_path", lambda: crlf_path)
    assert sens._verify_py_sha256() == sens.VERIFY_PY_SHA256
    called: list[str] = []

    def _boom(_premise: str, _hypothesis: str) -> dict[str, float]:
        called.append("predict")
        return {"entailment": 0.1, "neutral": 0.1, "contradiction": 0.8}

    monkeypatch.setattr(verify_mod, "predict_xnli_probs", _boom)
    _header, records, _raw = sens.load_formal_freeze()
    mutated = dict(records[0])
    mutated["note"] = str(mutated["note"]) + "改"
    header, _records, _file_raw = sens.load_formal_freeze()
    lines = [json.dumps(header, ensure_ascii=False, sort_keys=True)]
    lines.append(json.dumps(mutated, ensure_ascii=False, sort_keys=True))
    for record in records[1:]:
        lines.append(json.dumps(record, ensure_ascii=False, sort_keys=True))
    freeze_path = tmp_path / "formal-S.jsonl"
    freeze_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="正式冻结") as exc_info:
        sens.run_sens_live2(freeze_path=freeze_path, log=None)
    assert "patch_events_verify.py" not in str(exc_info.value)
    assert called == []


def test_live2_report_refuses_activation():
    from freshlatch.eval.patch_events_sensitivity import (
        FORMAL_FREEZE_SHA256,
        render_sens_live2_report,
    )

    summary = {
        "model_id": XNLI_MODEL_ID,
        "tau": ENTAILMENT_TAU,
        "bad_ok_false_min": BAD_OK_FALSE_MIN,
        "correct_ok_true_min": CORRECT_OK_TRUE_MIN,
        "n_score_none": 0,
        "n_reject": 20,
        "n_reject_neg_inf": 20,
        "n_bad": 20,
        "n_correct": 6,
        "bad_ok_false_rate": 1.0,
        "correct_ok_true_rate": 1.0,
        "s1": True,
        "s2": True,
        "s3": True,
        "s4": True,
        "sensitivity_passed": True,
    }
    with pytest.raises(ValueError, match="activation_prerequisite_met"):
        render_sens_live2_report(
            summary,
            [],
            frozen_sha256=FORMAL_FREEZE_SHA256,
            pair_validity={},
            activation_prerequisite_met=True,
            runtime_note="stub",
            verify_py_sha256="x",
        )


def test_issue_538_failure_sentence_unchanged():
    text = Path("docs/evidence/patch-events/GATE-Y-SENSITIVITY.md").read_text(encoding="utf-8")
    assert "实测 0.7000" in text
    assert "未通过" in text
    assert "sensitivity_passed（S1∧S2∧S3∧S4）**：否" in text
