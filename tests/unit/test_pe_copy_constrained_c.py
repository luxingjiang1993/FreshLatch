"""#485：路线 C 强制抄句硬契约 + 同 after 继承夹具。

不发网络、不读密钥、不改 verify_edit、不碰 B 归档文件。
"""

from __future__ import annotations

import hashlib
import http.client
import os
import socket
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_arms import Decoding
from freshlatch.eval.patch_events_copy_constrained import (
    correct_slot_is_copyable,
    forced_copy_after_text,
    make_copy_constrained_generator,
    run_arms_c,
)
from freshlatch.eval.patch_events_verify import verify_edit

_ROOT = Path(__file__).resolve().parents[2]
_VERIFY = _ROOT / "src" / "freshlatch" / "eval" / "patch_events_verify.py"
_VERIFY_SHA256 = "738541f6c55d16ca041b1fd489fe7e2bf1e51d5b1f416bef4366e93c3a964614"
_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_B_ARCHIVE = (
    _ROOT / "docs" / "evidence" / "patch-events" / "RESULT-B.md",
    _ROOT / "docs" / "evidence" / "patch-events" / "PREREG-B.md",
    _ROOT / "docs" / "evidence" / "patch-events" / "formal-generations-b.jsonl",
)


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


def test_forced_copy_is_hard_contract_not_prompt_substring():
    """可执行证明：契约函数产出 after，即使 inner 返回胡写。"""
    evidence = "证据句必须抄我"
    junk_inner_calls: list[dict] = []

    def junk(request):
        junk_inner_calls.append(dict(request))
        return {
            "after_text": "胡写完全不是证据",
            "evidence_id": request["evidence_id"],
            "latency_ms": 9,
            "cost": 1,
        }

    gen = make_copy_constrained_generator(junk)
    out = gen(
        {
            "arm": "T",
            "phase": "rewrite",
            "evidence_text": evidence,
            "evidence_id": "doc#p1@T1",
            "before_text": "旧文",
        }
    )
    assert out["after_text"] == forced_copy_after_text(evidence)
    assert out["after_text"] == evidence
    assert out.get("copy_constrained") is True
    # T/rewrite 不调用 inner：硬契约，非提示词软约束
    assert junk_inner_calls == []
    assert verify_edit(
        {
            "arm": "T",
            "claim_id": "x",
            "after_text": out["after_text"],
            "evidence_id": "doc#p1@T1",
            "evidence_text": evidence,
        }
    )["ok"] is True


def test_run_arms_c_forces_t_after_even_if_inner_would_diverge():
    evidence = "入库证据正文"
    candidates = [
        _candidate(
            "c-copy",
            evidence_id="doc#a@T1",
            evidence_text=evidence,
            construction_gold="正确",
        ),
    ]

    def diverge(request):
        if request["arm"] == "C":
            return {"after_text": "无证改写", "latency_ms": 1, "cost": 0}
        if request["phase"] == "claim":
            return {"claim_text": "主张", "latency_ms": 1, "cost": 0}
        return {
            "after_text": "若走自由改写会偏",
            "evidence_id": request["evidence_id"],
            "latency_ms": 2,
            "cost": 0,
        }

    result = run_arms_c(
        candidates,
        generator=diverge,
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=20261009),
        ingested_t1={"doc#a@T1"},
    )
    assert result["T"][0]["after_text"] == evidence
    assert result["B1"][0]["after_text"] == evidence
    assert result["T"][0]["decision"] == "release"
    assert result["B1"][0]["decision"] == "release"


def test_same_after_binding_seam_t_reject_b1_release():
    """同 after 继承：坏绑定样上 T reject / B1 release。"""
    evidence = "共享 after 正文"
    # evidence_id 不在 ingested → T 绑定失败；B1 不跑绑定，核验可通过
    candidates = [
        _candidate(
            "c-bind",
            evidence_id="doc#missing@T1",
            evidence_text=evidence,
            construction_gold="坏",
        ),
    ]

    def gen(request):
        if request["arm"] == "C":
            return {"after_text": "C改", "latency_ms": 1, "cost": 0}
        if request["phase"] == "claim":
            return {"claim_text": "主张", "latency_ms": 1, "cost": 0}
        return {
            "after_text": "会被强制抄覆盖",
            "evidence_id": request["evidence_id"],
            "latency_ms": 1,
            "cost": 0,
        }

    result = run_arms_c(
        candidates,
        generator=gen,
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=20261009),
        ingested_t1={"doc#other@T1"},
    )
    assert result["T"][0]["after_text"] == result["B1"][0]["after_text"] == evidence
    assert result["T"][0]["decision"] == "reject"
    assert result["T"][0]["reject_reason"] == "证据未绑定已入库 T1"
    assert result["B1"][0]["decision"] == "release"


def test_verify_edit_surface_unchanged():
    digest = hashlib.sha256(_VERIFY.read_bytes()).hexdigest()
    assert digest == _VERIFY_SHA256


def test_correct_slot_copyable_gate():
    assert correct_slot_is_copyable(
        _candidate("ok", evidence_id="d#a@T1", evidence_text="有证据", construction_gold="正确")
    )
    assert not correct_slot_is_copyable(
        _candidate("bad", evidence_id="d#a@T1", evidence_text="  ", construction_gold="正确")
    )
    # 坏槽不拦
    assert correct_slot_is_copyable(
        _candidate("junk", evidence_id="d#a@T1", evidence_text="", construction_gold="坏")
    )


def test_uncopyable_correct_slot_voided_not_released():
    candidates = [
        _candidate(
            "c-empty",
            evidence_id="doc#a@T1",
            evidence_text="",
            construction_gold="正确",
        ),
    ]
    result = run_arms_c(
        candidates,
        generator=lambda r: {"after_text": "x", "latency_ms": 0, "cost": 0},
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=20261009),
        ingested_t1={"doc#a@T1"},
    )
    assert result["T"] == []
    assert any(v["reason"].startswith("正确槽不可抄") for v in result["voids"])


def test_b_archive_files_untouched_by_this_module():
    """本票不得改 B 归档；存在性检查 + 模块源不引用改写路径。"""
    for path in _B_ARCHIVE:
        assert path.is_file(), path
    src = (_ROOT / "src" / "freshlatch" / "eval" / "patch_events_copy_constrained.py").read_text(
        encoding="utf-8"
    )
    assert "RESULT-B" not in src
    assert "formal-generations-b" not in src
    assert "PREREG-B" not in src
