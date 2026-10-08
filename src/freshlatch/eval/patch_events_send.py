"""显式正式入口的发送。只发送已经拼好的正文，不改提示词。"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from freshlatch.eval.patch_events_generate import build_prompt
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_SEND: tuple[tuple[str, str], ...] = (
    ("C", "rewrite"),
    ("T", "rewrite"),
    ("B1", "rewrite"),
    ("B2", "claim"),
)


def formal_requests(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """每条样本只排 C、T、B1 的 rewrite 和 B2 的 claim。不排 B2 的 diff。"""
    requests: list[dict[str, Any]] = []
    for row in rows:
        for arm, phase in _SEND:
            requests.append(
                {
                    "arm": arm,
                    "phase": phase,
                    "claim_id": row["claim_id"],
                    "before_text": row["before_text"],
                    "evidence_text": row["evidence_text"],
                }
            )
    return requests


def dispatch_prompt(
    request: Mapping[str, Any],
    chat: Callable[..., Any],
) -> dict[str, Any]:
    """空正文和 B2 的 diff 不调用 chat。其余请求的模型与温度只读登记。"""
    built = build_prompt(request)
    arm = str(built["arm"])
    phase = str(built["phase"])
    prompt = str(built["prompt"])
    result: dict[str, Any] = {
        "sent": False,
        "arm": arm,
        "phase": phase,
        "claim_id": request.get("claim_id"),
    }
    if (arm == "B2" and phase == "diff") or prompt == "":
        return result
    text = chat(
        prompt,
        model=DEFAULT_MODEL,
        temperature=MODEL_REGISTRY["default_llm"].temperature,
    )
    field = str(built["output_field"])
    result["sent"] = True
    result[field] = "" if text is None else str(text)
    return result


def live_chat(prompt: str, *, model: str, temperature: float) -> str:
    """用用户角色消息发送已拼好的正文。密钥只留在传输层，不在这里读取或打印。"""
    from freshlatch.llm import DecodingParams, LLMClient

    message = LLMClient().chat(
        [{"role": "user", "content": prompt}],
        decoding=DecodingParams(model=model, temperature=temperature),
    )
    content = getattr(message, "content", "")
    return "" if content is None else str(content)
