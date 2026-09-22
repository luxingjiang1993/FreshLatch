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


@dataclass
class TokenUsage:
    """单桶累计:prompt/completion(K5-1);角色共用同一 LLMClient 实例即同桶。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add(self, prompt: int, completion: int) -> None:
        self.prompt_tokens += int(prompt or 0)
        self.completion_tokens += int(completion or 0)

    def reset(self) -> None:
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


class LLMClient:
    """不假设并行 tool_calls(qwen-flash 冒烟实测 0 次并行,§3 协议):串行执行。"""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        load_dotenv(find_dotenv(usecwd=True))
        self.client = OpenAI(
            api_key=api_key or os.getenv("DASHSCOPE_API_KEY", ""),
            base_url=base_url or os.getenv("DASHSCOPE_BASE_URL", DASHSCOPE_BASE_URL),
        )
        self.decoding_log: list[DecodingParams] = []
        self.token_usage = TokenUsage()

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
        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.token_usage.add(
                getattr(usage, "prompt_tokens", 0),
                getattr(usage, "completion_tokens", 0),
            )
        return resp.choices[0].message
