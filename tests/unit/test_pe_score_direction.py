"""高分方向是补定 draft。score 为空，不改已经写好的放行或拒绝。"""

from __future__ import annotations

import http.client
import os
import socket
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_ablation import primary_comparison_rows
from freshlatch.eval.patch_events_arms import ARMS, Decoding, run_arms
from freshlatch.eval.patch_events_metrics import (
    PRIMARY_CONTRASTS,
    compare_primary,
    named_streams,
    select_scored_positions,
)
from freshlatch.eval import patch_events_metrics as metrics
from freshlatch.eval import patch_events_verify as verify_mod
from freshlatch.eval.patch_events_verify import verify_edit

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]
_GAPS = _ROOT / "docs" / "evidence" / "patch-events" / "PROMPT-AND-VERIFY-GAPS.md"
_PREREG = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
_RESULT = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"
_MARK = "补定 draft，不是预注册原文"
_SENTENCE = "高分不代表放行，也不代表拒绝。score 继续为空，不把 score 当结果。放行只使用已经写好的 decision。"
_CLAIM = "只属于主张"
_DIFF = "只属于差异"


def _bytes(path: Path) -> bytes:
    return path.read_bytes()


def _block_network(monkeypatch) -> None:
    def blocked(*_args, **_kwargs):
        raise AssertionError("测试不得连网")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(http.client.HTTPConnection, "request", blocked)
    monkeypatch.setattr(http.client.HTTPSConnection, "request", blocked)


def _spy_env(monkeypatch) -> list[str]:
    seen: list[str] = []
    real = os.getenv

    def wrapped(key, default=None):
        name = str(key)
        seen.append(name)
        if name in _SECRET_ENV:
            raise AssertionError("不得读取密钥")
        return real(key, default)

    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(os, "getenv", wrapped)
    return seen


@pytest.fixture(autouse=True)
def _guard(monkeypatch):
    before = {path: _bytes(path) for path in (_GAPS, _PREREG, _RESULT)}
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    # #527：本文件不测真实 NLI；stub 概率，避免下模型 / 连网
    def _fake_nli(premise: str, hypothesis: str) -> dict[str, float]:
        if premise == hypothesis:
            return {"entailment": 0.91, "neutral": 0.05, "contradiction": 0.04}
        return {"entailment": 0.05, "neutral": 0.10, "contradiction": 0.85}

    monkeypatch.setattr(verify_mod, "predict_xnli_probs", _fake_nli)
    yield seen
    for path, blob in before.items():
        assert _bytes(path) == blob
    for key in _SECRET_ENV:
        assert key not in seen


def _candidates() -> list[dict[str, str]]:
    return [
        {
            "claim_id": "c-ok",
            "before_text": "前",
            "evidence_id": "doc#ok@T1",
            "evidence_text": "证据甲",
            "edit_type": "数值",
            "construction_gold": "正确",
        },
        {
            "claim_id": "c-bad",
            "before_text": "前",
            "evidence_id": "doc#bad@T1",
            "evidence_text": "证据乙",
            "edit_type": "数值",
            "construction_gold": "坏",
        },
    ]


def _generator(request):
    if request["phase"] == "claim":
        return {"claim_text": _CLAIM}
    if request["phase"] == "diff":
        return {"after_text": _DIFF, "evidence_id": request["evidence_id"]}
    if request["claim_id"] == "c-ok":
        return {"after_text": request["evidence_text"], "evidence_id": request["evidence_id"]}
    return {"after_text": "对不上", "evidence_id": request["evidence_id"]}


def _verifier(score):
    def verifier(request):
        verdict = verify_edit(request)
        verdict["score"] = score
        return verdict

    return verifier


def _run(score):
    return run_arms(
        _candidates(),
        generator=_generator,
        verifier=_verifier(score),
        decoding=Decoding(temperature=0, seed=20261007),
        ingested_t1={"doc#ok@T1"},
    )


def _verdicts(result) -> dict[tuple[str, str], tuple[str, str, bool | None]]:
    found = {}
    for arm in ARMS:
        for row in result[arm]:
            found[(arm, row["claim_id"])] = (
                row["decision"],
                row["reject_reason"],
                row.get("reverify_ok"),
            )
    return found


def test_score_direction_sentence_keeps_the_draft_mark():
    text = _GAPS.read_text(encoding="utf-8")
    assert _SENTENCE in text
    start = 0
    found = 0
    while True:
        index = text.find(_SENTENCE, start)
        if index < 0:
            break
        window = text[max(0, index - 40) : index]
        assert _MARK in window
        found += 1
        start = index + len(_SENTENCE)
    assert found >= 1
    prereg = _PREREG.read_text(encoding="utf-8")
    result = _RESULT.read_text(encoding="utf-8")
    assert _SENTENCE not in prereg
    assert _SENTENCE not in result
    assert "高分不代表放行" not in prereg


def test_empty_score_keeps_release_and_reject():
    assert "B2" in PRIMARY_CONTRASTS
    empty = _run(None)
    high = _run(100)
    low = _run(-1)
    assert _verdicts(empty) == _verdicts(high) == _verdicts(low)
    expected = {
        ("C", "c-ok"): ("release", "", None),
        ("C", "c-bad"): ("release", "", None),
        ("T", "c-ok"): ("release", "", True),
        ("T", "c-bad"): ("reject", "证据未绑定已入库 T1", False),
        ("B1", "c-ok"): ("release", "", True),
        ("B1", "c-bad"): ("reject", "核验不过", False),
        ("B2", "c-ok"): ("release", "", False),
        ("B2", "c-bad"): ("release", "", False),
    }
    assert _verdicts(empty) == expected
    rows = primary_comparison_rows(empty)
    assert {row["arm"] for row in rows} == {"C", "T", "B1", "B2"}
    assert all(row["score"] is None for row in rows)
    for row in empty["B2"]:
        assert row["after_text"] == _DIFF
        assert row["after_text"] != _CLAIM
    failed = run_arms(
        _candidates(),
        generator=lambda _request: {"void": True},
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=20261007),
        ingested_t1={"doc#ok@T1"},
    )
    assert all(failed[arm] == [] for arm in ARMS)
    assert failed["voids"]
    assert {item["reason"] for item in failed["voids"]} == {"生成失败"}


def test_legacy_score_order_helper_unchanged_and_primary_uses_r(monkeypatch):
    rows = [
        {"claim_id": "b", "score": 2},
        {"claim_id": "a", "score": 2},
        {"claim_id": "d", "score": 0.1},
        {"claim_id": "c", "score": None},
    ]
    assert select_scored_positions(rows, 3) == [1, 0, 2]
    assert 3 not in select_scored_positions(rows, 3)
    sample_calls = []
    real_sample = metrics._sample_positions

    def sample_wrapped(n, k, rng):
        sample_calls.append(rng)
        return real_sample(n, k, rng)

    monkeypatch.setattr(metrics, "_sample_positions", sample_wrapped)
    streams = named_streams()
    coverage_before = streams["coverage_c"].getstate()
    report = compare_primary(primary_comparison_rows(_run(None)), streams=streams)
    assert sample_calls == []
    assert streams["coverage_c"].getstate() == coverage_before
    for arm in ("C", "T", "B1", "B2"):
        selected = report["arms"][arm]["fixed"]["selected_claim_ids"]
        if selected is not None:
            assert selected == sorted(selected)
