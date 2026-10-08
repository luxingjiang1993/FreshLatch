"""正式生成器只拼已锁定字段。调用本身不发请求。"""

from __future__ import annotations

import socket
from pathlib import Path

import http.client

from freshlatch.eval.patch_events_generate import build_prompt
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]
_GENERATE = _ROOT / "src" / "freshlatch" / "eval" / "patch_events_generate.py"


def _request(arm: str, phase: str) -> dict:
    return {
        "arm": arm,
        "phase": phase,
        "claim_id": "c-1",
        "model": "别的模型",
        "temperature": 0.7,
        "seed": 7,
        "retrieval_mode": "hybrid+rerank",
        "before_text": "原文甲",
        "evidence_id": "doc#a@T1",
        "evidence_text": "证据乙",
        "edit_type": "replace",
        "claim_text": "不该进提示词",
    }


def test_build_prompt_splices_only_locked_fields(monkeypatch):
    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)
    seen: list[str] = []

    def wrapped(key, default=None):
        seen.append(str(key))
        return None

    def blocked(*_args, **_kwargs):
        raise AssertionError("不得发请求")

    monkeypatch.setattr("os.getenv", wrapped)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(http.client.HTTPConnection, "request", blocked)
    monkeypatch.setattr(http.client.HTTPSConnection, "request", blocked)
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_args, **_kwargs: blocked(),
    )

    c_prompt = build_prompt(_request("C", "rewrite"))
    t_prompt = build_prompt(_request("T", "rewrite"))
    b1_prompt = build_prompt(_request("B1", "rewrite"))
    claim = build_prompt(_request("B2", "claim"))
    diff = build_prompt(_request("B2", "diff"))

    assert c_prompt["prompt"] == {"before_text": "原文甲"}
    assert c_prompt["output_field"] == "after_text"
    assert t_prompt["prompt"] == {"before_text": "原文甲", "evidence_text": "证据乙"}
    assert b1_prompt["prompt"] == {"before_text": "原文甲", "evidence_text": "证据乙"}
    assert t_prompt["output_field"] == b1_prompt["output_field"] == "after_text"
    assert claim["prompt"] == {"before_text": "原文甲", "evidence_text": "证据乙"}
    assert claim["output_field"] == "claim_text"
    assert diff["prompt"] == {}
    assert "output_field" not in diff

    for result in (c_prompt, t_prompt, b1_prompt, claim, diff):
        assert result["model"] == DEFAULT_MODEL
        assert result["model"] == MODEL_REGISTRY["default_llm"].model
        assert result["temperature"] == MODEL_REGISTRY["default_llm"].temperature == 0
        assert result["output"] == "纯文本"
        assert result["model"] != "别的模型"
        assert result["temperature"] != 0.7
        blob = str(result["prompt"])
        assert "你是" not in blob
        assert "请输出" not in blob
        assert "hybrid+rerank" not in blob
        assert "doc#a@T1" not in blob
        assert "不该进提示词" not in blob
        assert "temperature" not in result["prompt"]
        assert "retrieval_mode" not in result["prompt"]
        assert "evidence_id" not in result["prompt"]

    assert "evidence" not in str(c_prompt["prompt"])
    assert "diff" not in claim["prompt"]
    assert "after_text" not in claim["prompt"]
    assert MODEL_REGISTRY["judge_qwen"].temperature == 0
    assert MODEL_REGISTRY["judge_deepseek"].temperature == 0
    assert MODEL_REGISTRY["judge_kimi"].temperature == 0.6
    for key in _SECRET_ENV:
        assert key not in seen

    source = _GENERATE.read_text(encoding="utf-8")
    for banned in (
        "LLMClient(",
        "chat.completions",
        "load_dotenv",
        "getenv",
        "prompts/",
        "你是",
        "请输出",
        "urllib",
        "httpx",
        "requests.",
    ):
        assert banned not in source
