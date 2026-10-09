"""#469：T/B1 同 after 再分叉 + 门闩复测夹具。

缝外面注入 generator/verifier/ingested；不读密钥、不发网络。
"""

from __future__ import annotations

import http.client
import os
import socket

import pytest

from freshlatch.eval.patch_events_arms import Decoding, run_arms
from freshlatch.eval.patch_events_verify import verify_edit

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")


def _block_network(monkeypatch) -> None:
    def blocked(*_args, **_kwargs):
        raise AssertionError("测试不得连网")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(http.client.HTTPConnection, "request", blocked)
    monkeypatch.setattr(http.client.HTTPSConnection, "request", blocked)


@pytest.fixture(autouse=True)
def _guard(monkeypatch):
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
    _block_network(monkeypatch)
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    yield
    for key in _SECRET_ENV:
        assert key not in seen


def _candidate(
    claim_id: str,
    *,
    evidence_id: str,
    evidence_text: str,
    construction_gold: str = "坏",
) -> dict[str, str]:
    return {
        "claim_id": claim_id,
        "before_text": "修改前",
        "evidence_id": evidence_id,
        "evidence_text": evidence_text,
        "edit_type": "数值",
        "construction_gold": construction_gold,
    }


def _run(
    *,
    after_by_claim: dict[str, str],
    candidates: list[dict[str, str]],
    ingested_t1: set[str],
) -> dict:
    calls: list[dict] = []

    def generator(request):
        calls.append(dict(request))
        phase = request["phase"]
        claim_id = request["claim_id"]
        if phase == "claim":
            return {"claim_text": f"主张-{claim_id}", "latency_ms": 1, "cost": 0}
        # 若按臂独立生成会写出不同 after；同 after 缝必须压成一份。
        after = after_by_claim[claim_id]
        if request["arm"] == "B1":
            after = f"B1-独写-{after}"
        return {
            "after_text": after,
            "evidence_id": request["evidence_id"],
            "latency_ms": 3,
            "cost": 0,
        }

    result = run_arms(
        candidates,
        generator=generator,
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=20261008),
        ingested_t1=ingested_t1,
    )
    result["_generator_calls"] = calls
    return result


def test_tb1_share_identical_after_text():
    """同一 claim_id 上 T 与 B1 的 after_text 逐字相同。"""
    evidence = "证据正文甲"
    candidates = [
        _candidate("c-share", evidence_id="doc#a@T1", evidence_text=evidence),
    ]
    result = _run(
        after_by_claim={"c-share": evidence},
        candidates=candidates,
        ingested_t1={"doc#a@T1"},
    )
    t_after = result["T"][0]["after_text"]
    b1_after = result["B1"][0]["after_text"]
    assert t_after == b1_after == evidence
    # 共享 rewrite 以 T 请求生成一次；不得再以 B1 臂单独 rewrite。
    rewrites = [
        call
        for call in result["_generator_calls"]
        if call["phase"] == "rewrite" and call["claim_id"] == "c-share"
    ]
    arms = [call["arm"] for call in rewrites]
    assert arms.count("T") == 1
    assert "B1" not in arms


def test_binding_seam_unbound_t1_t_reject_b1_release():
    """after==evidence 且 evidence_id 非已入库 T1 → T reject（未绑定）且 B1 release。"""
    evidence = "绑定缝证据"
    candidates = [
        _candidate(
            "c-unbound",
            evidence_id="doc#unbound@T1",
            evidence_text=evidence,
            construction_gold="坏",
        ),
    ]
    result = _run(
        after_by_claim={"c-unbound": evidence},
        candidates=candidates,
        ingested_t1={"doc#other@T1"},
    )
    tee = result["T"][0]
    b1 = result["B1"][0]
    assert tee["after_text"] == b1["after_text"] == evidence
    assert tee["decision"] == "reject"
    assert "未绑定" in tee["reject_reason"]
    assert b1["decision"] == "release"
    assert b1["reject_reason"] == ""
    assert b1["arm"] == "B1"


def test_verify_fail_rejects_both_t_and_b1():
    """after!=evidence → T 与 B1 均 hard reject（禁止 B1 soft 放行）。"""
    candidates = [
        _candidate(
            "c-mismatch",
            evidence_id="doc#ok@T1",
            evidence_text="金标证据",
            construction_gold="坏",
        ),
    ]
    result = _run(
        after_by_claim={"c-mismatch": "对不上的改写"},
        candidates=candidates,
        ingested_t1={"doc#ok@T1"},
    )
    tee = result["T"][0]
    b1 = result["B1"][0]
    assert tee["after_text"] == b1["after_text"] == "对不上的改写"
    assert tee["decision"] == "reject"
    assert b1["decision"] == "reject"
    assert b1["decision"] != "release"
    assert "核验" in b1["reject_reason"]


def test_bound_and_verify_ok_both_release_same_after():
    """已绑定 T1 且核验 ok → 两臂均 release，after 仍相同。"""
    evidence = "双过证据"
    candidates = [
        _candidate(
            "c-ok",
            evidence_id="doc#ok@T1",
            evidence_text=evidence,
            construction_gold="正确",
        ),
    ]
    result = _run(
        after_by_claim={"c-ok": evidence},
        candidates=candidates,
        ingested_t1={"doc#ok@T1"},
    )
    tee = result["T"][0]
    b1 = result["B1"][0]
    assert tee["after_text"] == b1["after_text"] == evidence
    assert tee["decision"] == "release"
    assert b1["decision"] == "release"


def test_c_and_b2_behavior_unchanged_relative_to_shared_after():
    """C 生成即放行；B2 不因核验 hard reject；且不与 T/B1 共用 after。"""
    evidence = "对照证据"
    candidates = [
        _candidate(
            "c-ctrl",
            evidence_id="doc#ok@T1",
            evidence_text=evidence,
        ),
    ]
    result = _run(
        after_by_claim={"c-ctrl": "故意不对齐"},
        candidates=candidates,
        ingested_t1={"doc#ok@T1"},
    )
    assert result["C"][0]["decision"] == "release"
    assert result["C"][0]["after_text"] == "故意不对齐"
    assert result["B2"][0]["decision"] == "release"
    assert result["B2"][0]["reverify_ok"] is False
    # B2 独立生成，after 可与 T/B1 不同（生成器按臂改写时 B2 仍走自己的请求）。
    assert result["T"][0]["after_text"] == result["B1"][0]["after_text"]
    assert result["B2"][0]["after_text"] == "故意不对齐"
