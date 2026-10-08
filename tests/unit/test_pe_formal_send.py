"""显式 --formal 才会发送。单测替换传输，不读密钥，不连网，不跑 n=30。"""

from __future__ import annotations

import http.client
import socket
from dataclasses import replace
from pathlib import Path

from freshlatch.eval import patch_events_formal as formal
from freshlatch.eval import patch_events_send as send
from freshlatch.eval.patch_events_generate import build_prompt
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]


def _row(claim_id: str, before_text: str, evidence_text: str) -> dict:
    return {
        "claim_id": claim_id,
        "before_text": before_text,
        "evidence_text": evidence_text,
        "model": "别的模型",
        "temperature": 0.7,
    }


def _block_network(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("测试不得连网")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(http.client.HTTPConnection, "request", blocked)
    monkeypatch.setattr(http.client.HTTPSConnection, "request", blocked)


def _spy_env(monkeypatch) -> list[str]:
    import os

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


def _refuse_expansion(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("不得扩到构造、消融或核验")

    monkeypatch.setattr(formal, "construct_samples", blocked)
    monkeypatch.setattr(formal, "run_formal", blocked)
    monkeypatch.setattr(formal, "run_arms", blocked)
    monkeypatch.setattr(formal, "run_ablations", blocked)
    monkeypatch.setattr(formal, "compare_primary", blocked)
    monkeypatch.setattr("freshlatch.eval.patch_events_verify.verify_edit", blocked)


def test_default_entry_still_exits_without_sending(monkeypatch, capsys):
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)

    def blocked(*_args, **_kwargs):
        raise AssertionError("默认入口不得装样本或发请求")

    monkeypatch.setattr(formal, "load_pe_v2_formal_n30", blocked)
    monkeypatch.setattr(formal, "live_chat", blocked)
    monkeypatch.setattr("freshlatch.llm.LLMClient", lambda *_args, **_kwargs: blocked())
    assert formal.main([]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    for key in _SECRET_ENV:
        assert key not in seen


def test_formal_requests_skip_diff_and_request_model():
    rows = [
        _row("a", "甲", "乙"),
        _row("b", "丙", "丁"),
    ]
    requests = send.formal_requests(rows)
    assert [(item["arm"], item["phase"]) for item in requests] == [
        ("C", "rewrite"),
        ("T", "rewrite"),
        ("B1", "rewrite"),
        ("B2", "claim"),
        ("C", "rewrite"),
        ("T", "rewrite"),
        ("B1", "rewrite"),
        ("B2", "claim"),
    ]
    assert all(item["phase"] != "diff" for item in requests)
    assert requests[0]["before_text"] == "甲"
    assert requests[3]["evidence_text"] == "乙"
    assert requests[4]["claim_id"] == "b"
    for item in requests:
        assert "model" not in item
        assert "temperature" not in item
        assert "0.7" not in str(item)
        assert "别的模型" not in str(item)


def test_dispatch_sends_locked_body_and_skips_diff(monkeypatch):
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)
    monkeypatch.setattr("freshlatch.llm.LLMClient", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不得构造客户端")))
    calls: list[dict] = []

    def chat(prompt, *, model, temperature):
        calls.append({"prompt": prompt, "model": model, "temperature": temperature})
        return "生成结果"

    request = _row("c-1", "原文甲", "证据乙")
    for arm, phase, field in (
        ("C", "rewrite", "after_text"),
        ("T", "rewrite", "after_text"),
        ("B1", "rewrite", "after_text"),
        ("B2", "claim", "claim_text"),
    ):
        item = {**request, "arm": arm, "phase": phase}
        result = send.dispatch_prompt(item, chat)
        assert result["sent"] is True
        assert result[field] == "生成结果"
        assert calls[-1]["prompt"] == build_prompt(item)["prompt"]
        assert calls[-1]["model"] == DEFAULT_MODEL
        assert calls[-1]["temperature"] == MODEL_REGISTRY["default_llm"].temperature == 0
        assert calls[-1]["model"] != "别的模型"
        assert calls[-1]["temperature"] != 0.7

    def refuse(*_args, **_kwargs):
        raise AssertionError("B2 的 diff 不得发请求")

    diff = {**request, "arm": "B2", "phase": "diff"}
    skipped = send.dispatch_prompt(diff, refuse)
    assert skipped["sent"] is False
    assert "after_text" not in skipped
    assert "claim_text" not in skipped
    assert build_prompt(diff)["prompt"] == ""

    def filled(_request):
        return {
            "arm": "B2",
            "phase": "diff",
            "prompt": "不该发出去",
            "output_field": "after_text",
        }

    monkeypatch.setattr(send, "build_prompt", filled)
    still_skipped = send.dispatch_prompt(diff, refuse)
    assert still_skipped["sent"] is False
    assert len(calls) == 4
    for key in _SECRET_ENV:
        assert key not in seen


def test_live_chat_uses_user_message_and_passed_decoding(monkeypatch):
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)
    recorded: list[tuple] = []

    class _Message:
        content = "回文"

    class _Client:
        def __init__(self, *_args, **_kwargs):
            return None

        def chat(self, messages, *, decoding=None, **_kwargs):
            recorded.append((messages, decoding))
            return _Message()

    decoding_args: list[tuple] = []
    real_params = __import__("freshlatch.llm", fromlist=["DecodingParams"]).DecodingParams

    def spy_params(*args, **kwargs):
        decoding_args.append((args, kwargs))
        return real_params(*args, **kwargs)

    monkeypatch.setattr("freshlatch.llm.LLMClient", _Client)
    monkeypatch.setattr("freshlatch.llm.DecodingParams", spy_params)
    text = send.live_chat(
        "已合入正文",
        model=DEFAULT_MODEL,
        temperature=MODEL_REGISTRY["default_llm"].temperature,
    )
    assert text == "回文"
    assert recorded[0][0] == [{"role": "user", "content": "已合入正文"}]
    assert decoding_args[0][0] == ()
    assert decoding_args[0][1]["model"] == DEFAULT_MODEL
    assert decoding_args[0][1]["temperature"] == MODEL_REGISTRY["default_llm"].temperature
    assert "seed" not in decoding_args[0][1]
    assert recorded[0][1].seed is None
    for key in _SECRET_ENV:
        assert key not in seen


def test_formal_flag_sends_four_requests_from_stub_row(monkeypatch, capsys):
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)
    _refuse_expansion(monkeypatch)
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不得构造客户端")),
    )
    row = _row("c-1", "原文甲", "证据乙")

    def loader(root=None):
        assert root is None
        return [row]

    sent: list[tuple] = []

    def chat(prompt, *, model, temperature):
        sent.append((prompt, model, temperature))
        return "回文"

    monkeypatch.setattr(formal, "load_pe_v2_formal_n30", loader)
    monkeypatch.setattr(formal, "live_chat", chat)
    assert formal.main(["--formal"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    expected = formal.formal_requests([row])
    assert [(item["arm"], item["phase"]) for item in expected] == [
        ("C", "rewrite"),
        ("T", "rewrite"),
        ("B1", "rewrite"),
        ("B2", "claim"),
    ]
    assert [item[0] for item in sent] == [build_prompt(item)["prompt"] for item in expected]
    assert {item[1] for item in sent} == {DEFAULT_MODEL}
    assert {item[2] for item in sent} == {MODEL_REGISTRY["default_llm"].temperature}
    assert all(item["phase"] != "diff" for item in expected)
    for key in _SECRET_ENV:
        assert key not in seen


def test_temperature_or_model_gap_does_not_send(monkeypatch, capsys):
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)

    def blocked(*_args, **_kwargs):
        raise AssertionError("登记不一致时不得装样本或发请求")

    monkeypatch.setattr(formal, "load_pe_v2_formal_n30", blocked)
    monkeypatch.setattr(formal, "live_chat", blocked)
    registered = MODEL_REGISTRY["default_llm"]
    monkeypatch.setitem(
        MODEL_REGISTRY,
        "default_llm",
        replace(registered, temperature=0.2),
    )
    assert formal.main(["--formal"]) == 2
    assert "default_llm.temperature 不是 0。" in capsys.readouterr().err

    monkeypatch.setitem(
        MODEL_REGISTRY,
        "default_llm",
        replace(registered, model="not-the-registry-model"),
    )
    assert formal.main(["--formal"]) == 2
    assert capsys.readouterr().err
    for key in _SECRET_ENV:
        assert key not in seen


def test_send_source_names_n30_and_keeps_client_out_of_formal():
    formal_src = Path(formal.__file__).read_text(encoding="utf-8")
    send_src = Path(send.__file__).read_text(encoding="utf-8")
    generate_src = (_ROOT / "src" / "freshlatch" / "eval" / "patch_events_generate.py").read_text(
        encoding="utf-8"
    )
    assert "load_pe_v2_formal_n30(" in formal_src
    assert "_FORMAL_N = 30" in formal_src
    assert "formal_requests(" in formal_src
    assert "LLMClient(" not in formal_src
    assert "chat.completions" not in formal_src
    assert "load_dotenv" not in formal_src
    assert "getenv" not in formal_src
    assert "RESULT.md" not in formal_src
    assert "prompts/" not in formal_src
    assert "LLMClient(" in send_src
    assert '"role": "user"' in send_src
    assert '"role": "system"' not in send_src
    assert "你是" not in send_src
    assert "seed" not in send_src
    assert "load_dotenv" not in send_src
    assert "getenv" not in send_src
    assert "RESULT.md" not in send_src
    assert "qwen-flash" not in formal_src
    assert "qwen-flash" not in send_src
    for banned in ("LLMClient(", "chat.completions", "load_dotenv", "getenv"):
        assert banned not in generate_src
