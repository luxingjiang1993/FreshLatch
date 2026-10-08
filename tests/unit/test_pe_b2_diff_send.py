"""B2 diff 只补已有 claim 的 claim_id。桩客户端，临时文件，不跑 --formal。"""

from __future__ import annotations

import http.client
import inspect
import json
import os
import socket
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_formal as formal
from freshlatch.eval import patch_events_send as send
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]
_REAL_GENERATIONS = _ROOT / "docs" / "evidence" / "patch-events" / "formal-generations.jsonl"
_PREREG = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
_RESULT = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"


def _bytes(path: Path) -> bytes | None:
    if not path.exists():
        return None
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
    before = {
        _REAL_GENERATIONS: _bytes(_REAL_GENERATIONS),
        _PREREG: _bytes(_PREREG),
        _RESULT: _bytes(_RESULT),
    }
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不得构造客户端")),
    )
    yield seen
    for path, blob in before.items():
        assert _bytes(path) == blob
    for key in _SECRET_ENV:
        assert key not in seen


def _lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _claim_record(claim_id: str, text: str) -> dict:
    return {
        "claim_id": claim_id,
        "arm": "B2",
        "phase": "claim",
        "output_field": "claim_text",
        "text": text,
        "model": DEFAULT_MODEL,
        "temperature": MODEL_REGISTRY["default_llm"].temperature,
    }


def _write(path: Path, records: list[dict]) -> None:
    payload = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records)
    path.write_text(payload, encoding="utf-8")


def _real_claims() -> list[dict]:
    claims = [
        item
        for item in _lines(_REAL_GENERATIONS)
        if item.get("arm") == "B2"
        and item.get("phase") == "claim"
        and item.get("output_field") == "claim_text"
    ]
    assert len(claims) == 30
    assert len({item["claim_id"] for item in claims}) == 30
    return claims


def test_stub_appends_diff_for_existing_claims_then_skips(tmp_path, _guard):
    claims = _real_claims()
    claim_ids = [item["claim_id"] for item in claims]
    claim_text = {item["claim_id"]: item["text"] for item in claims}
    path = tmp_path / "formal-generations.jsonl"
    _write(path, claims)
    rows = [
        {
            "claim_id": claim_id,
            "before_text": f"before-{claim_id}",
            "evidence_text": f"evidence-{claim_id}",
        }
        for claim_id in claim_ids
    ]
    rows.append({"claim_id": "not-a-claim", "before_text": "旁的", "evidence_text": "旁的证据"})
    calls: list[str] = []

    def chat(prompt, *, model, temperature):
        body = path.read_text(encoding="utf-8")
        assert body.count("\n") == len(claims) + len(calls)
        claim_id = claim_ids[len(calls)]
        assert claim_text[claim_id] in prompt
        assert "补定 draft，不是预注册原文" in prompt
        calls.append(claim_id)
        assert model == DEFAULT_MODEL
        assert temperature == MODEL_REGISTRY["default_llm"].temperature
        reply = f"diff-after-{claim_id}"
        assert reply != claim_text[claim_id]
        return reply

    assert formal.append_b2_diffs(rows, path, chat) == 30
    assert calls == claim_ids
    saved = _lines(path)
    assert saved[:30] == claims
    diffs = saved[30:]
    assert len(diffs) == 30
    for claim, diff in zip(claims, diffs):
        assert diff["claim_id"] == claim["claim_id"]
        assert diff["arm"] == "B2"
        assert diff["phase"] == "diff"
        assert diff["output_field"] == "after_text"
        assert diff["text"] == f"diff-after-{claim['claim_id']}"
        assert diff["text"] != claim["text"]
    again: list[str] = []

    def refuse(prompt, *, model, temperature):
        again.append(prompt)
        raise AssertionError("已有 after_text 不得再发")

    assert formal.append_b2_diffs(rows, path, refuse) == 0
    assert again == []
    assert _lines(path) == saved
    assert "append_b2_diffs" not in inspect.getsource(formal.main)
    assert "live_chat(" not in inspect.getsource(send.append_b2_diffs)


def test_existing_diff_after_text_is_skipped_and_claim_stays(tmp_path, _guard):
    path = tmp_path / "formal-generations.jsonl"
    claims = [
        _claim_record("c-keep", "claim-only-c-keep"),
        _claim_record("c-new", "claim-only-c-new"),
    ]
    done = {
        "claim_id": "c-keep",
        "arm": "B2",
        "phase": "diff",
        "output_field": "after_text",
        "text": "diff-after-c-keep",
        "model": DEFAULT_MODEL,
        "temperature": MODEL_REGISTRY["default_llm"].temperature,
    }
    _write(path, [*claims, done])
    rows = [
        {"claim_id": "c-keep", "before_text": "前-keep", "evidence_text": "证-keep"},
        {"claim_id": "c-new", "before_text": "前-new", "evidence_text": "证-new"},
        {"claim_id": "c-missing", "before_text": "前-missing", "evidence_text": "证-missing"},
    ]
    seen: list[str] = []

    def chat(prompt, *, model, temperature):
        assert path.read_text(encoding="utf-8").count("\n") == 3 + len(seen)
        seen.append(prompt)
        assert "claim-only-c-new" in prompt
        assert "claim-only-c-keep" not in prompt
        return "diff-after-c-new"

    assert send.append_b2_diffs(rows, path, chat) == 1
    assert len(seen) == 1
    saved = _lines(path)
    assert saved[:2] == claims
    assert saved[2] == done
    assert saved[3]["claim_id"] == "c-new"
    assert saved[3]["text"] == "diff-after-c-new"
    assert saved[3]["text"] != "claim-only-c-new"


def test_empty_prompt_does_not_send_or_write(tmp_path, monkeypatch, _guard):
    path = tmp_path / "formal-generations.jsonl"
    claim = _claim_record("c-1", "claim-only-c-1")
    _write(path, [claim])
    before = path.read_bytes()

    def empty(_request):
        return {"arm": "B2", "phase": "diff", "prompt": "", "output_field": "after_text"}

    def refuse(*_args, **_kwargs):
        raise AssertionError("空正文不得发请求")

    monkeypatch.setattr(send, "build_prompt", empty)
    assert formal.append_b2_diffs(
        [{"claim_id": "c-1", "before_text": "前", "evidence_text": "证"}],
        path,
        refuse,
    ) == 0
    assert path.read_bytes() == before
    assert _lines(path) == [claim]
