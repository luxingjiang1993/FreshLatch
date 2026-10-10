"""#527 PE-Y-INST-01：verify_edit 契约夹具（无 None · reject=−∞ · τ 可见）。"""

from __future__ import annotations

import math

import pytest

from freshlatch.eval import patch_events_verify as verify_mod
from freshlatch.eval.patch_events_verify import ENTAILMENT_TAU, verify_edit


@pytest.fixture(autouse=True)
def _no_real_model(monkeypatch):
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda _p, _h: {"entailment": 0.99, "neutral": 0.005, "contradiction": 0.005},
    )


def test_return_keys_stable():
    verdict = verify_edit({"after_text": "后", "evidence_text": "证"})
    assert set(verdict.keys()) == {"ok", "score", "reason"}


def test_reject_path_score_is_neg_inf_not_none(monkeypatch):
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda _p, _h: {"entailment": 0.2, "neutral": 0.3, "contradiction": 0.5},
    )
    verdict = verify_edit({"after_text": "后", "evidence_text": "证"})
    assert verdict["ok"] is False
    assert type(verdict["score"]) is float
    assert verdict["score"] == float("-inf")
    assert not math.isfinite(verdict["score"])


def test_released_score_in_unit_interval(monkeypatch):
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda _p, _h: {"entailment": 0.77, "neutral": 0.13, "contradiction": 0.10},
    )
    verdict = verify_edit({"after_text": "后", "evidence_text": "证"})
    assert verdict["ok"] is True
    assert 0.0 <= verdict["score"] <= 1.0
    assert verdict["score"] >= ENTAILMENT_TAU
