"""verify_edit：NLI 主核验 + 非空 score / reject=−∞（ADR-0040 · #527）。

推理经 ``predict_xnli_probs`` stub，不下载型号、不连网、不把仓外 Acc 当过线。
"""

from __future__ import annotations

import math

import pytest

from freshlatch.eval import patch_events_verify as verify_mod
from freshlatch.eval.patch_events_verify import (
    ENTAILMENT_TAU,
    XNLI_MODEL_ID,
    verify_edit,
)


def _request(after_text: object, evidence_text: object, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "arm": "T",
        "claim_id": "c-lock",
        "after_text": after_text,
        "evidence_id": "doc#anchor@T1",
        "evidence_text": evidence_text,
    }
    payload.update(extra)
    return payload


def _stub_probs(entailment: float, *, argmax: str = "entailment") -> dict[str, float]:
    """构造三分类概率；其余质量在非 argmax 标签上均分。"""
    rest = max(0.0, 1.0 - entailment)
    if argmax == "entailment":
        return {
            "entailment": entailment,
            "neutral": rest / 2.0,
            "contradiction": rest / 2.0,
        }
    if argmax == "neutral":
        return {
            "entailment": entailment,
            "neutral": max(entailment, rest),
            "contradiction": 0.0 if rest <= entailment else rest - entailment,
        }
    return {
        "entailment": entailment,
        "neutral": 0.0,
        "contradiction": max(entailment, rest),
    }


@pytest.fixture(autouse=True)
def _stub_nli(monkeypatch):
    """默认：全文相同 → 高 entailment；否则 contradiction 主导。"""

    def fake(premise: str, hypothesis: str) -> dict[str, float]:
        if premise == hypothesis:
            return _stub_probs(0.92, argmax="entailment")
        return _stub_probs(0.08, argmax="contradiction")

    monkeypatch.setattr(verify_mod, "predict_xnli_probs", fake)


def test_pin_constants_are_visible():
    assert XNLI_MODEL_ID == (
        "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
    )
    assert isinstance(ENTAILMENT_TAU, float)
    assert 0.0 < ENTAILMENT_TAU <= 1.0


def test_released_ok_uses_entailment_probability(monkeypatch):
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda _p, _h: _stub_probs(0.87, argmax="entailment"),
    )
    verdict = verify_edit(_request("改后句", "证据句"))
    assert verdict["ok"] is True
    assert verdict["reason"] == "支撑成立"
    assert verdict["score"] == pytest.approx(0.87)
    assert verdict["score"] is not None
    assert math.isfinite(verdict["score"])


def test_reject_score_is_negative_infinity(monkeypatch):
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda _p, _h: _stub_probs(0.12, argmax="contradiction"),
    )
    verdict = verify_edit(_request("改后句", "证据句"))
    assert verdict["ok"] is False
    assert verdict["reason"] == "核验不过"
    assert verdict["score"] is not None
    assert math.isinf(verdict["score"])
    assert verdict["score"] < 0


def test_entailment_below_tau_is_reject(monkeypatch):
    # argmax 仍是 entailment，但 P < τ → 不得 ok
    low = ENTAILMENT_TAU - 0.01
    assert low > 0.0
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda _p, _h: _stub_probs(low, argmax="entailment"),
    )
    verdict = verify_edit(_request("甲", "乙"))
    assert verdict["ok"] is False
    assert math.isinf(verdict["score"]) and verdict["score"] < 0


def test_entailment_at_tau_passes(monkeypatch):
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda _p, _h: _stub_probs(ENTAILMENT_TAU, argmax="entailment"),
    )
    verdict = verify_edit(_request("甲", "乙"))
    assert verdict["ok"] is True
    assert verdict["score"] == pytest.approx(ENTAILMENT_TAU)


def test_score_never_none_for_invalid_inputs():
    for after, evidence in ((None, "e"), ("a", None), (1, "e"), ("a", 2)):
        verdict = verify_edit(_request(after, evidence))
        assert set(verdict) == {"ok", "score", "reason"}
        assert verdict["ok"] is False
        assert verdict["score"] is not None
        assert math.isinf(verdict["score"]) and verdict["score"] < 0


def test_arm_claim_and_evidence_id_do_not_change_the_comparison():
    same = verify_edit(_request("甲乙丙", "甲乙丙", arm="B1", claim_id="other", evidence_id=""))
    assert same["ok"] is True
    assert same["score"] is not None
    assert math.isfinite(same["score"])
    ignored = verify_edit(
        _request("甲乙丙", "甲乙丙", ablation="soft_warning", ledger="hybrid+rerank")
    )
    assert ignored == same


def test_default_stub_same_text_passes_different_fails():
    passed = verify_edit(_request("甲乙丙", "甲乙丙"))
    failed = verify_edit(_request("甲乙丙", "甲乙丁"))
    assert passed["ok"] is True
    assert math.isfinite(passed["score"])
    assert failed["ok"] is False
    assert math.isinf(failed["score"]) and failed["score"] < 0
