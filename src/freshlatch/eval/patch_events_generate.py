"""四臂正式生成器。正文只重述已锁定的句子，不发请求。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_MARK = "补定，2026-10-08。不是预注册原文。"
_TASK_MARK = "补定，2026-10-09。不是预注册原文。"
_TASK = "根据下面给出的 before_text，改写一句纯文本。"
_BEFORE = "before_text 写进 C、T、B1 和 B2 的 claim 提示词。"
_OUTPUT = "模型输出是纯文本。"
_MODEL = "生成模型只读 DEFAULT_MODEL。"
_REWRITE = ("C", "T", "B1")


def _temperature_line() -> str:
    return f"温度只读 default_llm.temperature：{MODEL_REGISTRY['default_llm'].temperature}"


def _join(lines: list[str]) -> str:
    return "\n".join(lines)


def _given_before(before_text: object) -> list[str]:
    return [_TASK_MARK, _TASK, "before_text：", str(before_text)]


def build_prompt(request: Mapping[str, Any]) -> dict[str, Any]:
    """按臂和阶段拼可发送正文。模型只读 ``DEFAULT_MODEL``，温度只读登记值。"""
    arm = str(request["arm"])
    phase = str(request["phase"])
    result: dict[str, Any] = {
        "model": DEFAULT_MODEL,
        "temperature": MODEL_REGISTRY["default_llm"].temperature,
        "arm": arm,
        "phase": phase,
        "output": "纯文本",
        "prompt": "",
    }
    if arm == "B2" and phase == "diff":
        return result
    tail = [_OUTPUT, _MODEL, _temperature_line()]
    if arm == "B2" and phase == "claim":
        result["output_field"] = "claim_text"
        result["prompt"] = _join(
            [
                _MARK,
                "claim 是一句纯文本，diff 是后面的阶段。",
                _BEFORE,
                *_given_before(request["before_text"]),
                "B2 的 claim 也带上这份 evidence_text。",
                "evidence_text：",
                str(request["evidence_text"]),
                *tail,
            ]
        )
        return result
    if arm in _REWRITE and phase == "rewrite":
        result["output_field"] = "after_text"
        lines = [_MARK, _BEFORE, *_given_before(request["before_text"])]
        if arm == "C":
            lines.append("C 的提示词里不放 evidence。")
        elif arm == "T":
            lines.extend(
                [
                    "T 的证据只用请求里已经有的 evidence_text，提示词不再检索。",
                    "evidence_text：",
                    str(request["evidence_text"]),
                ]
            )
        elif arm == "B1":
            lines.extend(
                [
                    "B1 带上请求里已经有的 evidence_text。",
                    "evidence_text：",
                    str(request["evidence_text"]),
                ]
            )
        lines.extend(tail)
        result["prompt"] = _join(lines)
    return result
