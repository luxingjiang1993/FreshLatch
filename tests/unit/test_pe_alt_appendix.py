"""ALT-03：compare_alt_fixed_k_appendix（附录 only）。零 LLM，不读密钥。"""

from __future__ import annotations

import copy
import hashlib
import http.client
import inspect
import os
import socket
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_alt as alt
from freshlatch.eval import patch_events_metrics as metrics

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


def _fixture_rows():
    """坏改 T 拒 / B2 放 + 正确改 T 放；夹具层可构造自然率差。"""
    bad = _candidate("bad1", gold="坏", after="被污染的改写", evidence="证据原文")
    good = _candidate("good1", gold="正确", after="证据原文", evidence="证据原文")
    return alt.run_same_text_gates([bad, good], ingested_t1=_INGESTED)


def test_natural_main_fields_unchanged_after_appendix():
    """先 natural 再 appendix 后，natural 主表字段不变。"""
    rows = _fixture_rows()
    natural_before = alt.compare_alt_natural(rows)
    snapshot = copy.deepcopy(natural_before)

    appendix = alt.compare_alt_fixed_k_appendix(rows)
    natural_after = alt.compare_alt_natural(rows)

    assert natural_after == snapshot
    assert natural_before == snapshot
    assert appendix["appendix_only"] is True
    assert appendix["feeds_upgrade"] is False
    assert "established" not in appendix
    assert appendix["k"] == natural_before["arms"]["T"]["自然放行数"]
    for arm in alt.ARMS:
        assert "固定k误放率" in appendix["arms"][arm]
        assert "自然误放率" not in appendix["arms"][arm]


def test_appendix_alone_cannot_hard_pass_separable():
    """仅附录输出不得使「可分开」硬通过（显式拒绝）。"""
    rows = _fixture_rows()
    appendix = alt.compare_alt_fixed_k_appendix(rows)

    with pytest.raises(ValueError, match="附录"):
        alt.upgrade_tier(appendix)

    # 伪造「固定 k 看起来很好」仍须拒绝，不得读成可分开。
    fake_green_appendix = {
        "appendix_only": True,
        "feeds_upgrade": False,
        "k": 1,
        "arms": {
            "T": {"固定k误放率": 0.0, "固定k放行数": 1, "候选数": 2},
            "B1": {"固定k误放率": 1.0, "固定k放行数": 1, "候选数": 2},
            "B2": {"固定k误放率": 1.0, "固定k放行数": 1, "候选数": 2},
            "C": {"固定k误放率": 1.0, "固定k放行数": 1, "候选数": 2},
        },
        "contrasts": [
            {"name": "T-B1", "fixed_k_false_accept_delta": 1.0},
            {"name": "T-B2", "fixed_k_false_accept_delta": 1.0},
        ],
    }
    with pytest.raises(ValueError, match="附录|feeds_upgrade"):
        alt.upgrade_tier(fake_green_appendix)


def test_upgrade_tier_consumes_natural_only():
    """升级判定夹具只喂自然率；本夹具未必可分开，但不得抛附录拒绝。"""
    rows = _fixture_rows()
    natural = alt.compare_alt_natural(rows)
    tier = alt.upgrade_tier(natural)
    assert tier in ("可分开", "分不开")


def test_appendix_does_not_touch_primary_or_prereg_result():
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

    rows = _fixture_rows()
    natural = alt.compare_alt_natural(rows)
    alt.compare_alt_fixed_k_appendix(rows)
    with pytest.raises(ValueError):
        alt.upgrade_tier(alt.compare_alt_fixed_k_appendix(rows))
    alt.upgrade_tier(natural)

    assert hashlib.sha256(_PREREG.read_bytes()).hexdigest() == before_prereg
    assert hashlib.sha256(_RESULT.read_bytes()).hexdigest() == before_result
    assert inspect.getsource(metrics.compare_primary) == primary_src
