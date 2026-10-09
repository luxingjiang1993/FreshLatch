"""ALT-01：平行轨同文四闸 + compare_alt_natural。零 LLM，不读密钥。"""

from __future__ import annotations

import hashlib
import http.client
import inspect
import os
import socket
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_alt as alt
from freshlatch.eval import patch_events_metrics as metrics
from freshlatch.eval.patch_events_verify import verify_edit

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]
_PREREG = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
_RESULT = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"
_INGESTED = {"doc#p1@T1"}


@pytest.fixture(autouse=True)
def _no_secrets_no_net(monkeypatch):
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

    def blocked(*_args, **_kwargs):
        raise AssertionError("测试不得连网")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(http.client.HTTPConnection, "request", blocked)
    monkeypatch.setattr(http.client.HTTPSConnection, "request", blocked)
    yield seen
    assert not any(name in _SECRET_ENV for name in seen)


def _candidate(claim_id: str, *, gold: str, after: str, evidence: str, eid: str = "doc#p1@T1"):
    return {
        "claim_id": claim_id,
        "construction_gold": gold,
        "after_text": after,
        "evidence_id": eid,
        "evidence_text": evidence,
    }


def test_t_reject_b2_release_natural_false_accept_delta_positive():
    """坏改同文：T reject、B2 release → T-B2 自然误放差 > 0（对照 − T）。"""
    # 坏改：正文与证据不一致 → T 核验拒；B2 有 after_text 仍放行。
    bad = _candidate("bad1", gold="坏", after="被污染的改写", evidence="证据原文")
    # 正确改：挡住「T 全拒装干净」。
    good = _candidate("good1", gold="正确", after="证据原文", evidence="证据原文")
    rows = alt.run_same_text_gates([bad, good], ingested_t1=_INGESTED)

    by = {(r["claim_id"], r["arm"]): r for r in rows}
    assert by[("bad1", "T")]["decision"] == "reject"
    assert by[("bad1", "B2")]["decision"] == "release"
    assert by[("good1", "T")]["decision"] == "release"
    assert by[("bad1", "B1")]["arm"] == "B1"
    assert by[("bad1", "B1")]["evidence_id"] == ""

    report = alt.compare_alt_natural(rows)
    t_b2 = next(c for c in report["contrasts"] if c["name"] == "T-B2")
    assert t_b2["natural_false_accept_delta"] is not None
    assert t_b2["natural_false_accept_delta"] > 0
    assert report["arms"]["T"]["自然放行数"] >= 1
    assert report["arms"]["T"]["自然误放率"] == 0.0
    assert report["arms"]["B2"]["自然误放率"] == 0.5


def test_zero_releases_natural_false_accept_undefined_not_zero():
    """放行数为 0 → 自然误放无定义，禁止 0.0。"""
    rows = [
        {
            "claim_id": "r1",
            "arm": "T",
            "construction_gold": "坏",
            "decision": "reject",
        },
        {
            "claim_id": "r1",
            "arm": "C",
            "construction_gold": "坏",
            "decision": "reject",
        },
        {
            "claim_id": "r1",
            "arm": "B1",
            "construction_gold": "坏",
            "decision": "reject",
        },
        {
            "claim_id": "r1",
            "arm": "B2",
            "construction_gold": "坏",
            "decision": "reject",
        },
    ]
    report = alt.compare_alt_natural(rows)
    for arm in alt.ARMS:
        rate = report["arms"][arm]["自然误放率"]
        assert rate is None
        assert rate != 0.0
        assert report["arms"][arm]["自然放行数"] == 0
    for contrast in report["contrasts"]:
        assert contrast["natural_false_accept_delta"] is None


def test_b1_reject_arm_is_b1_not_t():
    bad = _candidate("x", gold="坏", after="不同", evidence="证据")
    out = alt.decide_same_text_gate("B1", bad, ingested_t1=_INGESTED)
    assert out["decision"] == "reject"
    assert out["arm"] == "B1"
    assert out["evidence_id"] == ""


def test_c_always_releases_without_evidence():
    cand = _candidate("c", gold="坏", after="任意正文", evidence="证据")
    out = alt.decide_same_text_gate("C", cand, ingested_t1=_INGESTED)
    assert out["decision"] == "release"
    assert out["evidence_id"] == ""
    assert out["evidence_text"] == ""


def test_b2_records_reverify_ok_without_hard_reject():
    cand = _candidate("b2", gold="坏", after="不一致正文", evidence="证据原文")
    out = alt.decide_same_text_gate("B2", cand, ingested_t1=_INGESTED, verifier=verify_edit)
    assert out["decision"] == "release"
    assert out["reverify_ok"] is False


def test_alt_does_not_touch_primary_or_prereg_result():
    """本票旁路不得改 compare_primary 行为，也不得回写旧 PREREG / 主 RESULT。"""
    src = inspect.getsource(alt)
    assert "patch_events_metrics" not in src
    assert "write_primary_false_accept" not in src
    assert "open(" not in src
    assert "Path(" not in src
    assert "write_text" not in src
    assert "write_bytes" not in src

    before_prereg = hashlib.sha256(_PREREG.read_bytes()).hexdigest()
    before_result = hashlib.sha256(_RESULT.read_bytes()).hexdigest()
    primary_src = inspect.getsource(metrics.compare_primary)

    rows = alt.run_same_text_gates(
        [_candidate("g", gold="正确", after="证据原文", evidence="证据原文")],
        ingested_t1=_INGESTED,
    )
    alt.compare_alt_natural(rows)

    assert hashlib.sha256(_PREREG.read_bytes()).hexdigest() == before_prereg
    assert hashlib.sha256(_RESULT.read_bytes()).hexdigest() == before_result
    assert inspect.getsource(metrics.compare_primary) == primary_src
