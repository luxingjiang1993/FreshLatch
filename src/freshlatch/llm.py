"""OpenAI 兼容 chat.completions 薄壳(仅 HTTP 传输)。decoding 参数逐运行记录(§4.7)。

开发期统一 qwen-flash(§6.5):「开发用最便宜模型压成本,真实业务可换更好模型」。
托管端点在漂移,跨会话复现只能是近似的,此限制由 Runner 写入留档。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_default_base = MODEL_REGISTRY["default_llm"].base_url
if not isinstance(_default_base, str) or not _default_base:
    raise RuntimeError("default_llm 缺少 base_url")
DASHSCOPE_BASE_URL = _default_base

# 未标记 accepts_tools_strict 时是否传 function.strict。结论写在 LLMClient.chat。
DEFAULT_ENDPOINT_ACCEPTS_TOOLS_STRICT = True


def endpoint_accepts_tools_strict(client: Any) -> bool:
    """读端点标记。显式 True/False 覆盖缺省;缺省见 LLMClient.chat 的探测结论。"""
    chat = getattr(client, "chat", None)
    completions = getattr(chat, "completions", None) if chat is not None else None
    for node in (completions, chat, client):
        if node is None or not hasattr(node, "accepts_tools_strict"):
            continue
        flag = getattr(node, "accepts_tools_strict")
        if flag is True or flag is False:
            return flag
    return DEFAULT_ENDPOINT_ACCEPTS_TOOLS_STRICT


def tools_for_request(tools: list, *, accepts_strict: bool) -> list:
    """按端点是否接受 strict 做发送副本,不改调用方持有的 schema。

    接受时在 function 副本写入 strict=true,parameters 里已有的
    additionalProperties 原样保留。拒绝时去掉 strict,请求不假装已经 strict。
    """
    bound: list = []
    for tool in tools:
        if not isinstance(tool, dict) or tool.get("type") != "function":
            bound.append(tool)
            continue
        function = tool.get("function")
        if not isinstance(function, dict):
            bound.append(tool)
            continue
        function_copy = dict(function)
        parameters = function_copy.get("parameters")
        if isinstance(parameters, dict):
            function_copy["parameters"] = dict(parameters)
        if accepts_strict:
            function_copy["strict"] = True
        else:
            function_copy.pop("strict", None)
        tool_copy = dict(tool)
        tool_copy["function"] = function_copy
        bound.append(tool_copy)
    return bound


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
    """不假设并行 tool_calls(qwen-flash 冒烟实测 0 次并行,§3 协议):串行执行。

    OpenAI 客户端延迟到首次 chat()/访问 client 再构造:装配 Runner/接线/finalize
    不需要凭据。避免 openai 新版对空 api_key 在 __init__ 即抛 Missing credentials,
    从而让无密钥的 CI unit 误红(本机有 .env 则假绿)。
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        load_dotenv(find_dotenv(usecwd=True))
        self._api_key = api_key
        self._base_url = base_url
        self._client: Any | None = None
        self.decoding_log: list[DecodingParams] = []
        self.token_usage = TokenUsage()

    @property
    def client(self) -> Any:
        """兼容旧代码读 self.client;首次访问时才向 OpenAI SDK 要凭据。"""
        if self._client is None:
            entry = MODEL_REGISTRY["default_llm"]
            env_key = entry.env_key
            base_url = entry.base_url
            if not isinstance(env_key, str) or not env_key:
                raise RuntimeError("default_llm 缺少 env_key")
            if not isinstance(base_url, str) or not base_url:
                raise RuntimeError("default_llm 缺少 base_url")
            key = self._api_key if self._api_key is not None else os.getenv(env_key, "")
            # 非空占位仅绕过 SDK 对 "" 的构造期拒绝;真调用仍会因无效 key 鉴权失败。
            if not key:
                key = "MISSING_DASHSCOPE_API_KEY"
            # 默认 base_url 读 registry。已有的 DASHSCOPE_BASE_URL 环境变量仍可覆盖。
            self._client = OpenAI(
                api_key=key,
                base_url=self._base_url or os.getenv("DASHSCOPE_BASE_URL", base_url),
            )
        return self._client

    @client.setter
    def client(self, value: Any) -> None:
        """单测可注入 mock client,跳过真实 SDK 构造。"""
        self._client = value

    def chat(self, messages: list, *, tools: list | None = None,
             decoding: DecodingParams | None = None,
             response_format: dict | None = None) -> object:
        """把 messages 发给当前客户端的 chat.completions。

        A-FC-02: tools 的 function.strict 已有探测结论。这不是召回率,也不是通过率。

        默认端点是 MODEL_REGISTRY 里的 DashScope compatible-mode,模型 qwen-flash。
        2026-10-14 对该端点发了两次 chat.completions(temperature=0):
        一次是最小 function,strict=true 且 additionalProperties=false;
        一次是现有 retrieve schema,可选字段仍不全部列入 required,并加上 strict=true。
        两次都返回正常完成,没有参数错误。n=2,只说明该字段被接受,不报方差。

        客户端、chat 或 completions 上没有 accepts_tools_strict 标记时,按上述结论
        在即将发送的 function 副本里写入 strict=true。已有的 additionalProperties: false
        保持原样,不改写必填列表。

        声明分支: 上述对象把 accepts_tools_strict 标为 False(端点拒绝该字段)时,
        请求不写 strict,不假装已经 strict。
        dimension、evidence id、as_of 在两条分支上都仅运行时再验(L4-FC-01)。
        """
        d = decoding or DecodingParams()
        self.decoding_log.append(d)
        kwargs: dict[str, Any] = {"model": d.model, "messages": messages, "temperature": d.temperature}
        if d.seed is not None:
            kwargs["seed"] = d.seed
        if tools is not None:
            kwargs["tools"] = tools_for_request(
                tools,
                accepts_strict=endpoint_accepts_tools_strict(self.client),
            )
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
