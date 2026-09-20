"""OpenAI 兼容 chat.completions 薄壳(仅 HTTP 传输)。decoding 参数逐运行记录(§4.7)。

开发期统一 qwen-flash(§6.5):「开发用最便宜模型压成本,真实业务可换更好模型」。
托管端点在漂移,跨会话复现只能是近似的,此限制由 Runner 写入留档。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-flash"


@dataclass
class DecodingParams:
    model: str = DEFAULT_MODEL
    temperature: float = 0.0
    seed: int | None = None
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LLMClient:
    """不假设并行 tool_calls(qwen-flash 冒烟实测 0 次并行,§3 协议):串行执行。"""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        load_dotenv(find_dotenv(usecwd=True))
        self.client = OpenAI(
            api_key=api_key or os.getenv("DASHSCOPE_API_KEY", ""),
            base_url=base_url or os.getenv("DASHSCOPE_BASE_URL", DASHSCOPE_BASE_URL),
        )
        self.decoding_log: list[DecodingParams] = []

    def chat(self, messages: list, *, tools: list | None = None,
             decoding: DecodingParams | None = None,
             response_format: dict | None = None) -> object:
        d = decoding or DecodingParams()
        self.decoding_log.append(d)
        kwargs: dict = {"model": d.model, "messages": messages, "temperature": d.temperature}
        if d.seed is not None:
            kwargs["seed"] = d.seed
        if tools is not None:
            kwargs["tools"] = tools
        if response_format is not None:
            kwargs["response_format"] = response_format
        resp = self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message
