"""四臂正式生成器。只拼已锁定字段，不发请求。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_REWRITE = ("C", "T", "B1")


def build_prompt(request: Mapping[str, Any]) -> dict[str, Any]:
    """按臂和阶段拼提示词字段。模型只读 ``DEFAULT_MODEL``，温度只读登记值。"""
    arm = str(request["arm"])
    phase = str(request["phase"])
    result: dict[str, Any] = {
        "model": DEFAULT_MODEL,
        "temperature": MODEL_REGISTRY["default_llm"].temperature,
        "arm": arm,
        "phase": phase,
        "output": "纯文本",
        "prompt": {},
    }
    if arm == "B2" and phase == "diff":
        return result
    if arm == "B2" and phase == "claim":
        result["output_field"] = "claim_text"
        result["prompt"] = {
            "before_text": request["before_text"],
            "evidence_text": request["evidence_text"],
        }
        return result
    if arm in _REWRITE and phase == "rewrite":
        result["output_field"] = "after_text"
        prompt: dict[str, Any] = {"before_text": request["before_text"]}
        if arm in {"T", "B1"}:
            prompt["evidence_text"] = request["evidence_text"]
        result["prompt"] = prompt
    return result
