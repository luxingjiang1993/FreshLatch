"""裸 ReAct 循环(toolcall.py 种子,06 课 openai_native_tool_calling 模式)。

单循环内 think → act(tool_call) → observe(tool_result) 交错;无独立规划器(ADR-0004)。
本模块不 import langgraph(图不是 Agent,§0.4.1);LangGraph 只用于 checkpoint/interrupt(W3 起)。

非法调用(白名单外工具名、schema 再验失败)回灌 typed reason。自纠次数见
ILLEGAL_CALL_REPAIR_BUDGET。耗尽后 fail-closed 并留下轨迹,不以 UnknownToolGuard
拆掉循环作为唯一失败形态。

verify 短环只读工具观察上已经写好的 grade(RAG-02 的边),不在这里重算。
Incorrect 且 retry 未耗尽时做一次有限 repair(再检索或改判定草稿);
retry 耗尽或 grade 仍不足则 abstain,不把 fresh 交给执行器。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from freshlatch.tools import (
    REASON_ILLEGAL_TOOL_ARGS,
    REASON_UNKNOWN_TOOL,
    illegal_call_payload,
    parse_tool_arguments,
    tool_schema_error,
)

# 回灌次数上限。前 N 次非法调用把 typed reason 交回模型并继续;
# 第 N+1 次不再继续,运行以失败结束并留下轨迹。
ILLEGAL_CALL_REPAIR_BUDGET = 2
ILLEGAL_CALL_EXHAUSTED_TOOL = "__illegal_call_exhausted__"

# verify 短环与非法调用自纠分开计数。Incorrect 只再给一次 repair。
VERIFY_REPAIR_BUDGET = 1
VERIFY_REPAIR_TOOL = "__verify_repair__"
VERIFY_ABSTAIN_TOOL = "__verify_abstain__"
_GRADE_VALUES = frozenset({"correct", "incorrect", "ambiguous"})


@dataclass
class LoopResult:
    messages: list = field(default_factory=list)
    steps_used: int = 0
    finished: bool = False  # 模型自发收尾(finish 工具或无 tool_calls)
    failed: bool = False  # 非法调用自纠耗尽,fail-closed
    failure_reason: str | None = None
    illegal_repairs: int = 0
    tool_trace: list[dict] = field(default_factory=list)
    # 短环状态。grade 来自工具观察,本循环不另算。
    evidence_ids: list[str] = field(default_factory=list)
    grade: str | None = None
    retry_count: int = 0
    abstained: bool = False
    grade_reason_code: str | None = None
    repair_note: str | None = None


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
    """裸 while 循环。白名单外工具名与 schema 非法参数不抛出拆循环。

    步数预算归零不硬断:注入软收尾消息,做最后一次无工具调用(护栏管天花板,不管结论)。
    非法调用自纠耗尽则不再请求模型,也不走软收尾。
    观察里若有 grade,只读取它:Incorrect 且 retry 未耗尽则有限 repair;
    retry 耗尽或 grade 仍不足则 abstain,fresh 不交给执行器。
    """
    result = LoopResult()
    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user", "content": task},
    ]
    allowed = [t["function"]["name"] for t in tools]
    specs = {t["function"]["name"]: t for t in tools}

    while result.steps_used < max_steps and not result.failed:
        msg = chat(messages, tools=tools)
        messages.append(msg.model_dump(exclude_none=True))
        result.steps_used += 1
        tool_calls = getattr(msg, "tool_calls", None) or []
        if not tool_calls:
            result.finished = True
            break
        for tc in tool_calls:  # 串行执行,不主动开并行(§3 协议)
            _dispatch_tool_call(
                result, messages, tc, allowed, specs, execute, on_event,
            )
            if result.failed:
                break
        _flush_repair_note(result, messages)

    if result.failed:
        _flush_repair_note(result, messages)
        result.messages = messages
        return result

    if not result.finished:
        messages.append({"role": "system", "content": soft_close})
        final = chat(messages, tools=None)
        messages.append(final.model_dump(exclude_none=True))
        result.tool_trace.append({"step": result.steps_used, "tool": "__soft_close__", "args": {}, "result": soft_close})

    result.messages = messages
    return result


class UnknownToolGuard(Exception):
    """白名单外工具名。run_loop 把它收成 unknown_tool 观察,不让它单独拆掉循环。"""

    def __init__(self, name: str, allowed: list[str]) -> None:
        self.name = name
        self.allowed = allowed
        super().__init__(f"未允许的工具: {name};白名单: {sorted(allowed)}")


def _dispatch_tool_call(
    result: LoopResult,
    messages: list[dict],
    tc,
    allowed: list[str],
    specs: dict[str, dict],
    execute: Callable[[str, dict], dict],
    on_event: Callable[[dict], None] | None,
) -> None:
    if tc.type != "function":
        _reject_illegal(
            result, messages, tc, "__unsupported_tool_call__", {"type": tc.type},
            illegal_call_payload(
                reason_code=REASON_ILLEGAL_TOOL_ARGS,
                error=f"不支持的工具调用类型: {tc.type}",
            ),
            on_event,
        )
        return
    name = tc.function.name
    if name not in allowed:
        guard = UnknownToolGuard(name, allowed)
        _reject_illegal(
            result, messages, tc, name, _peek_arguments(tc.function.arguments),
            illegal_call_payload(reason_code=REASON_UNKNOWN_TOOL, error=str(guard)),
            on_event,
        )
        return
    args, parse_error = parse_tool_arguments(tc.function.arguments)
    if parse_error or args is None:
        _reject_illegal(
            result, messages, tc, name, {"_unparsed": tc.function.arguments or ""},
            illegal_call_payload(
                reason_code=REASON_ILLEGAL_TOOL_ARGS,
                error=parse_error or "工具参数无法解析",
            ),
            on_event,
        )
        return
    schema_error = tool_schema_error(specs[name], args)
    if schema_error:
        _reject_illegal(
            result, messages, tc, name, args,
            illegal_call_payload(reason_code=REASON_ILLEGAL_TOOL_ARGS, error=schema_error),
            on_event,
        )
        return
    if _fresh_blocked(result, name, args):
        _observe(
            result, messages, tc, name, args, _abstain_fresh_result(result), on_event,
        )
        return
    try:
        out = execute(name, args)
    except UnknownToolGuard as guard:
        _reject_illegal(
            result, messages, tc, name, args,
            illegal_call_payload(reason_code=REASON_UNKNOWN_TOOL, error=str(guard)),
            on_event,
        )
        return
    except Exception as e:  # 工具失败 = 观察的一部分,回给模型自我纠正
        out = {"error": f"{type(e).__name__}: {e}"}
    _observe(result, messages, tc, name, args, out, on_event)


def _reject_illegal(
    result: LoopResult,
    messages: list[dict],
    tc,
    name: str,
    args: dict,
    out: dict,
    on_event: Callable[[dict], None] | None,
) -> None:
    """记下非法调用。预算内回灌;超出后写耗尽轨迹并标记失败,不抛异常。"""
    result.illegal_repairs += 1
    code = str(out["reason_code"])
    _observe(result, messages, tc, name, args, out, on_event, reason_code=code)
    if result.illegal_repairs <= ILLEGAL_CALL_REPAIR_BUDGET:
        return
    result.failed = True
    result.failure_reason = code
    terminal = {
        "step": result.steps_used,
        "tool": ILLEGAL_CALL_EXHAUSTED_TOOL,
        "args": {},
        "result": {
            "failed": True,
            "reason_code": code,
            "repair_budget": ILLEGAL_CALL_REPAIR_BUDGET,
            "repairs_used": result.illegal_repairs,
        },
        "reason_code": code,
    }
    result.tool_trace.append(terminal)
    if on_event:
        on_event(terminal)


def _observe(
    result: LoopResult,
    messages: list[dict],
    tc,
    name: str,
    args: dict,
    out: dict,
    on_event: Callable[[dict], None] | None,
    *,
    reason_code: str | None = None,
) -> None:
    record = {"step": result.steps_used, "tool": name, "args": args, "result": out}
    if reason_code:
        record["reason_code"] = reason_code
    result.tool_trace.append(record)
    if on_event:
        on_event(record)
    messages.append({
        "role": "tool",
        "tool_call_id": tc.id,
        "content": json.dumps(out, ensure_ascii=False),
    })
    if isinstance(out, dict):
        _note_verify(result, out, on_event)


def _peek_arguments(raw: str | None) -> dict:
    parsed, error = parse_tool_arguments(raw)
    if error or parsed is None:
        return {"_unparsed": raw or ""}
    return parsed


def _read_grade(out: dict) -> str | None:
    """读观察上的 grade。没有三态字段时返回 None,不另算。"""
    raw = out.get("grade")
    if not isinstance(raw, str):
        return None
    grade = raw.strip().lower()
    if grade not in _GRADE_VALUES:
        return None
    return grade


def _evidence_ids_from(out: dict) -> list[str]:
    """从这次观察的 blocks / evidence_ids 收集 id,保持原顺序。"""
    found: list[str] = []
    blocks = out.get("blocks")
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, dict):
                continue
            evidence_id = block.get("evidence_id")
            if isinstance(evidence_id, str) and evidence_id and evidence_id not in found:
                found.append(evidence_id)
    raw_ids = out.get("evidence_ids")
    if isinstance(raw_ids, list):
        for item in raw_ids:
            evidence_id = item if isinstance(item, str) else ""
            if evidence_id and evidence_id not in found:
                found.append(evidence_id)
    return found


def _is_rule_incorrect(out: dict, grade: str) -> bool:
    """无耗尽码且充分性不足:拒答仍走 sufficiency,本短环不抢这一跳。"""
    if grade != "incorrect":
        return False
    if out.get("grade_reason_code"):
        return False
    return out.get("sufficiency") == "insufficient"


def _note_verify(
    result: LoopResult,
    out: dict,
    on_event: Callable[[dict], None] | None,
) -> None:
    """根据已写入观察的 grade 更新短环状态。

    abstain 回执自身也带 grade,不能再走一遍 repair。
    """
    if out.get("abstain") is True:
        return
    grade = _read_grade(out)
    if grade is None:
        return
    result.grade = grade
    result.evidence_ids = _evidence_ids_from(out)
    reason = out.get("grade_reason_code")
    result.grade_reason_code = reason if isinstance(reason, str) and reason else None
    if grade == "correct":
        result.abstained = False
        return
    if _is_rule_incorrect(out, grade):
        return
    if grade == "incorrect" and result.retry_count < VERIFY_REPAIR_BUDGET:
        result.retry_count += 1
        _emit_verify(
            result,
            on_event,
            tool=VERIFY_REPAIR_TOOL,
            payload={
                "repair": "re_retrieve_or_revise_draft",
                "evidence_ids": list(result.evidence_ids),
                "grade": result.grade,
                "retry_count": result.retry_count,
                "grade_reason_code": result.grade_reason_code,
            },
        )
        result.repair_note = (
            "verify: 检索边 grade=incorrect,repair 预算内。"
            "请再检索一次,或修改判定草稿。"
            "grade 仍不足时不得写 fresh。"
            f"retry_count={result.retry_count}。"
        )
        if result.retry_count < VERIFY_REPAIR_BUDGET:
            return
    _mark_abstain(result, on_event)


def _mark_abstain(
    result: LoopResult,
    on_event: Callable[[dict], None] | None,
) -> None:
    if result.abstained:
        return
    result.abstained = True
    _emit_verify(
        result,
        on_event,
        tool=VERIFY_ABSTAIN_TOOL,
        payload={
            "abstain": True,
            "evidence_ids": list(result.evidence_ids),
            "grade": result.grade,
            "retry_count": result.retry_count,
            "grade_reason_code": result.grade_reason_code,
        },
    )


def _emit_verify(
    result: LoopResult,
    on_event: Callable[[dict], None] | None,
    *,
    tool: str,
    payload: dict,
) -> None:
    record = {
        "step": result.steps_used,
        "tool": tool,
        "args": {},
        "result": payload,
        "evidence_ids": list(result.evidence_ids),
        "grade": result.grade,
        "retry_count": result.retry_count,
    }
    result.tool_trace.append(record)
    if on_event:
        on_event(record)


def _flush_repair_note(result: LoopResult, messages: list[dict]) -> None:
    if not result.repair_note:
        return
    messages.append({"role": "system", "content": result.repair_note})
    result.repair_note = None


def _fresh_blocked(result: LoopResult, name: str, args: dict) -> bool:
    return bool(
        result.abstained
        and name == "reverify_claim"
        and args.get("status") == "fresh"
    )


def _abstain_fresh_result(result: LoopResult) -> dict:
    """fresh 不交给执行器。reason 只转发观察上已有的码,不新造枚举。"""
    out: dict = {
        "abstain": True,
        "grade": result.grade,
        "evidence_ids": list(result.evidence_ids),
        "retry_count": result.retry_count,
        "error": "abstain: grade 不足,不得写 fresh",
    }
    if result.grade_reason_code:
        out["reason_code"] = result.grade_reason_code
    if result.grade:
        out["grade_token"] = f"grade={result.grade}"
    return out
