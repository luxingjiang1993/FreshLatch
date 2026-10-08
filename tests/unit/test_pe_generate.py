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
    frozen = {
        path: path.read_bytes()
        for path in (
            _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md",
            _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md",
            _ROOT / "docs" / "evidence" / "patch-events" / "formal-generations.jsonl",
        )
    }
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
    tail = (
        "模型输出是纯文本。\n"
        "生成模型只读 DEFAULT_MODEL。\n"
        "温度只读 default_llm.temperature：0"
    )
    mark = (
        "补定，2026-10-08。不是预注册原文。\n"
        "before_text 写进 C、T、B1 和 B2 的 claim 提示词。\n"
        "补定，2026-10-09。不是预注册原文。\n"
        "根据下面给出的 before_text，改写一句纯文本。\n"
        "before_text：\n原文甲\n"
    )

    assert c_prompt["prompt"] == mark + "C 的提示词里不放 evidence。\n" + tail
    assert c_prompt["output_field"] == "after_text"
    assert t_prompt["prompt"] == (
        mark + "T 的证据只用请求里已经有的 evidence_text，提示词不再检索。\nevidence_text：\n证据乙\n" + tail
    )
    assert b1_prompt["prompt"] == (
        mark + "B1 带上请求里已经有的 evidence_text。\nevidence_text：\n证据乙\n" + tail
    )
    assert t_prompt["output_field"] == b1_prompt["output_field"] == "after_text"
    assert claim["prompt"] == (
        "补定，2026-10-08。不是预注册原文。\n"
        "claim 是一句纯文本，diff 是后面的阶段。\n"
        "before_text 写进 C、T、B1 和 B2 的 claim 提示词。\n"
        "补定，2026-10-09。不是预注册原文。\n"
        "根据下面给出的 before_text，改写一句纯文本。\n"
        "before_text：\n原文甲\n"
        "B2 的 claim 也带上这份 evidence_text。\n"
        "evidence_text：\n证据乙\n" + tail
    )
    assert claim["output_field"] == "claim_text"
    draft = (
        "补定 draft，不是预注册原文。\n"
        "根据下面给出的 before_text、上一阶段的 claim_text，以及请求里已经有的 evidence_text，改写一句纯文本。"
        "这一句是 after_text。claim_text 不是 after_text。不要输出 diff 标记。提示词不再检索。\n"
        "before_text：\n原文甲\n"
        "claim_text：\n不该进提示词\n"
        "evidence_text：\n证据乙\n" + tail
    )
    assert diff["prompt"] == draft
    assert "补定 draft，不是预注册原文" in diff["prompt"]
    assert diff["prompt"].count("预注册原文") == 1
    assert diff["output_field"] == "after_text"
    assert "after_text" not in diff
    assert diff["prompt"].index("before_text：\n原文甲") < diff["prompt"].index(
        "claim_text：\n不该进提示词"
    ) < diff["prompt"].index("evidence_text：\n证据乙")

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
        if result is not diff:
            assert "不该进提示词" not in blob
        assert "0.7" not in blob
        assert "retrieval_mode" not in blob
        assert "evidence_id" not in blob

    assert "证据乙" not in c_prompt["prompt"]
    assert "evidence_text" not in c_prompt["prompt"]
    assert "after_text" not in claim["prompt"]
    task = "根据下面给出的 before_text，改写一句纯文本。"
    for result in (c_prompt, t_prompt, b1_prompt, claim):
        assert task in result["prompt"]
        assert result["prompt"].index(task) < result["prompt"].index("before_text：\n原文甲")
    for result in (t_prompt, b1_prompt, claim):
        assert result["prompt"].index(task) < result["prompt"].index("evidence_text：\n证据乙")
    assert task not in diff["prompt"]
    assert MODEL_REGISTRY["judge_qwen"].temperature == 0
    assert MODEL_REGISTRY["judge_deepseek"].temperature == 0
    assert MODEL_REGISTRY["judge_kimi"].temperature == 0.6
    for key in _SECRET_ENV:
        assert key not in seen

    for path, blob in frozen.items():
        assert path.read_bytes() == blob

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
