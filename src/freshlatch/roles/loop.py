"""裸 ReAct 循环(toolcall.py 种子,06 课 openai_native_tool_calling 模式)。

单循环内 think → act(tool_call) → observe(tool_result) 交错;无独立规划器(ADR-0004)。
本模块不 import langgraph(图不是 Agent,§0.4.1);LangGraph 只用于 checkpoint/interrupt(W3 起)。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class LoopResult:
    messages: list = field(default_factory=list)
    steps_used: int = 0
    finished: bool = False  # 模型自发收尾(finish 工具或无 tool_calls)
    tool_trace: list[dict] = field(default_factory=list)


def run_loop(
    *,
    system: str,
    task: str,
    tools: list[dict],
    execute: Callable[[str, dict], dict],
    chat: Callable[..., object],
    max_steps: int,
    soft_close: str,
    on_event: Callable[[dict], None] | None = None,
) -> LoopResult:
    """裸 while 循环。execute(name, args)->dict 必须 fail-closed(白名单外 raise)。

    步数预算归零不硬断:注入软收尾消息,做最后一次无工具调用(护栏管天花板,不管结论)。
    """
    result = LoopResult()
    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user", "content": task},
    ]
    allowed = [t["function"]["name"] for t in tools]

    while result.steps_used < max_steps:
        msg = chat(messages, tools=tools)
        messages.append(msg.model_dump(exclude_none=True))
        result.steps_used += 1
        tool_calls = getattr(msg, "tool_calls", None) or []
        if not tool_calls:
            result.finished = True
            break
        for tc in tool_calls:  # 串行执行,不主动开并行(§3 协议)
            if tc.type != "function":
                raise ValueError(f"不支持的工具调用类型: {tc.type}")
            name = tc.function.name
            if name not in allowed:
                raise UnknownToolGuard(name, allowed)
            try:
                args = json.loads(tc.function.arguments or "{}")
                out = execute(name, args)
            except UnknownToolGuard:
                raise
            except Exception as e:  # 工具失败 = 观察的一部分,回给模型自我纠正
                out = {"error": f"{type(e).__name__}: {e}"}
            record = {"step": result.steps_used, "tool": name, "args": args, "result": out}
            result.tool_trace.append(record)
            if on_event:
                on_event(record)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(out, ensure_ascii=False),
            })

    if not result.finished:
        messages.append({"role": "system", "content": soft_close})
        final = chat(messages, tools=None)
        messages.append(final.model_dump(exclude_none=True))
        result.tool_trace.append({"step": result.steps_used, "tool": "__soft_close__", "args": {}, "result": soft_close})

    result.messages = messages
    return result


class UnknownToolGuard(Exception):
    def __init__(self, name: str, allowed: list[str]) -> None:
        self.name = name
        self.allowed = allowed
        super().__init__(f"未允许的工具: {name};白名单: {sorted(allowed)}")
