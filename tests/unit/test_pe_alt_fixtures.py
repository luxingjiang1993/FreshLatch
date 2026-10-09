"""ALT-02：平行轨夹具可分开（T vs B2 / B1′）。零 LLM，不读密钥。

层身份：设计探针 / 冒烟。可分开 ≠ 主假设成立；不写主 PREREG/RESULT。
"""

from __future__ import annotations

import http.client
import os
import socket
import subprocess
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_alt as alt

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_INGESTED = {"doc#p1@T1"}
_THIS = Path(__file__).resolve()
_UNIT = _THIS.parent


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


def _candidate(
    claim_id: str,
    *,
    gold: str,
    after: str,
    evidence: str,
    eid: str = "doc#p1@T1",
):
    return {
        "claim_id": claim_id,
        "construction_gold": gold,
        "after_text": after,
        "evidence_id": eid,
        "evidence_text": evidence,
    }


def _good() -> dict:
    """正确修改：挡住 T 全拒装干净。"""
    return _candidate("good1", gold="正确", after="证据原文", evidence="证据原文")


def test_fixture_bad_same_text_t_reject_b2_release_delta_positive():
    """坏修改同文：T reject、B2 release → T-B2 自然误放差 > 0。"""
    bad = _candidate("bad_b2", gold="坏", after="被污染的改写", evidence="证据原文")
    rows = alt.run_same_text_gates([bad, _good()], ingested_t1=_INGESTED)
    by = {(r["claim_id"], r["arm"]): r for r in rows}

    assert by[("bad_b2", "T")]["decision"] == "reject"
    assert by[("bad_b2", "B2")]["decision"] == "release"

    report = alt.compare_alt_natural(rows)
    t_b2 = next(c for c in report["contrasts"] if c["name"] == "T-B2")
    assert t_b2["natural_false_accept_delta"] is not None
    assert t_b2["natural_false_accept_delta"] > 0


def test_fixture_bad_same_text_t_reject_b1_prime_release_unbound_id_delta_positive():
    """坏修改同文：T 绑错 id 拒、B1′ 仅看正文放行（无 binding id）→ T-B1 差 > 0。"""
    # 正文与证据一致 → B1′ 核验放行；evidence_id 不在已入库 T1 → T 绑定拒。
    bad = _candidate(
        "bad_b1",
        gold="坏",
        after="证据原文",
        evidence="证据原文",
        eid="doc#unbound@T1",
    )
    rows = alt.run_same_text_gates([bad, _good()], ingested_t1=_INGESTED)
    by = {(r["claim_id"], r["arm"]): r for r in rows}

    assert by[("bad_b1", "T")]["decision"] == "reject"
    assert by[("bad_b1", "B1")]["decision"] == "release"
    assert by[("bad_b1", "B1")]["evidence_id"] == ""
    assert by[("bad_b1", "B1")]["arm"] == "B1"

    report = alt.compare_alt_natural(rows)
    t_b1 = next(c for c in report["contrasts"] if c["name"] == "T-B1")
    assert t_b1["natural_false_accept_delta"] is not None
    assert t_b1["natural_false_accept_delta"] > 0


def test_fixture_set_t_natural_release_floor():
    """整集：T 自然放行数 ≥ 1 且放行率 ≥ max(1/n, 0.05)；两差均可正。"""
    bad_b2 = _candidate("bad_b2", gold="坏", after="被污染的改写", evidence="证据原文")
    bad_b1 = _candidate(
        "bad_b1",
        gold="坏",
        after="证据原文",
        evidence="证据原文",
        eid="doc#unbound@T1",
    )
    candidates = [bad_b2, bad_b1, _good()]
    n = len(candidates)
    rows = alt.run_same_text_gates(candidates, ingested_t1=_INGESTED)
    report = alt.compare_alt_natural(rows)

    t = report["arms"]["T"]
    assert t["自然放行数"] >= 1
    floor = max(1 / n, 0.05)
    assert t["自然放行率"] >= floor

    by_name = {c["name"]: c for c in report["contrasts"]}
    assert by_name["T-B2"]["natural_false_accept_delta"] > 0
    assert by_name["T-B1"]["natural_false_accept_delta"] > 0


def test_fixture_source_has_no_jia_phrases():
    """平行轨测试源码不得出现禁称短语（拆字拼 pattern，避免本文件自污染）。"""
    # Acceptance：`rg -n '<禁称>' tests/unit/test_pe_alt_*.py` 无匹配。
    pattern = "甲" + "成立" + "|" + "结果" + "甲"
    files = sorted(str(p) for p in _UNIT.glob("test_pe_alt_*.py"))
    assert files, "缺少 test_pe_alt_*.py"
    proc = subprocess.run(
        ["rg", "-n", pattern, *files],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1, f"禁称短语命中:\n{proc.stdout}{proc.stderr}"
    assert proc.stdout == ""
