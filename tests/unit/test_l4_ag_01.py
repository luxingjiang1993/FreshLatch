"""L4-AG-01: verify 后有限 repair,或 abstain 且不写 fresh。

夹具是脚本化假 LLM 与直接 run_loop,不调用付费接口。
grade 由观察给出,循环不重算。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.lead import LeadReverifier
from freshlatch.roles.loop import (
    VERIFY_ABSTAIN_TOOL,
    VERIFY_REPAIR_BUDGET,
    VERIFY_REPAIR_TOOL,
    run_loop,
)
from freshlatch.roles.retrieve_grade import REASON_GRADE_AMBIGUOUS, REASON_GRADE_INCORRECT_EXHAUSTED
from freshlatch.runner import RunContext
from freshlatch.store.base import Chunk, InMemoryStore
from freshlatch.tools import tool_specs

REPO = Path(__file__).resolve().parents[2]
LOOP_PATH = REPO / "src/freshlatch/roles/loop.py"
EVIDENCE_ID = "memo#p1@T1"

_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_ag01_{_tc_counter}",
        type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(args, ensure_ascii=False)),
    )


class _Msg:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        dumped = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            dumped["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in self.tool_calls
            ]
        return dumped


class _ScriptLLM:
    """FIFO 脚本。耗尽即失败,避免落到付费客户端。"""

    def __init__(self, script):
        self._script = list(script)
        self.calls = 0

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        self.calls += 1
        if not self._script:
            raise AssertionError("脚本已尽,测试不得再调用 LLM")
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


def _graded(grade, *, reason=None, sufficiency="sufficient", evidence_id=EVIDENCE_ID):
    return {
        "blocks": [{"evidence_id": evidence_id, "text": "观察块"}],
        "grade": grade,
        "grade_reason_code": reason,
        "sufficiency": sufficiency,
        "grade_token": f"grade={grade}",
    }


def _run(script, *, execute, events=None, max_steps=8):
    llm = _ScriptLLM(script)

    def chat(messages, tools=None):
        return llm.chat(messages, tools=tools)

    result = run_loop(
        system="s",
        task="t",
        tools=tool_specs(["retrieve", "reverify_claim", "finish_reverify"]),
        execute=execute,
        chat=chat,
        max_steps=max_steps,
        soft_close="预算已尽,基于现有证据下结论。",
        on_event=None if events is None else events.append,
    )
    return result, llm


def _fresh_args(status="fresh"):
    return {
        "claim_id": "c-ag01",
        "status": status,
        "evidence_ids": [EVIDENCE_ID],
    }


def test_repair_budget_is_one_retry():
    assert VERIFY_REPAIR_BUDGET == 1


def test_incorrect_repairs_once_then_rereetrieve_increments_retry():
    """验收 1: grade=Incorrect 且 retry 未耗尽时,发生有限再检索,retry_count 增加。"""
    calls = []

    def execute(name, args):
        calls.append(name)
        return _graded("Incorrect")

    result, llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(content="不再检索"),
        ],
        execute=execute,
    )
    assert calls == ["retrieve", "retrieve", "retrieve"]
    assert llm.calls == 4
    assert result.retry_count == VERIFY_REPAIR_BUDGET
    assert result.grade == "incorrect"
    assert result.evidence_ids == [EVIDENCE_ID]
    repairs = [row for row in result.tool_trace if row["tool"] == VERIFY_REPAIR_TOOL]
    assert len(repairs) == 1
    assert repairs[0]["retry_count"] == 1
    assert repairs[0]["result"]["repair"] == "re_retrieve_or_revise_draft"
    assert repairs[0]["evidence_ids"] == [EVIDENCE_ID]
    notes = [m["content"] for m in result.messages if m.get("role") == "system"]
    assert any("再检索一次" in note and "修改判定草稿" in note for note in notes)
    assert result.abstained is True


def test_revise_draft_is_allowed_and_fresh_is_not():
    """repair 可以改判定草稿。草稿若仍是 fresh,不交给执行器。"""
    calls = []

    def execute(name, args):
        calls.append((name, args.get("status")))
        if name == "retrieve":
            return _graded("incorrect")
        return {"recorded": {"status": args.get("status"), "evidence_ids": args.get("evidence_ids")}}

    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", _fresh_args("unknown"))]),
            _Msg(content="草稿已改"),
        ],
        execute=execute,
    )
    assert calls == [("retrieve", None), ("reverify_claim", "unknown")]
    assert result.retry_count == 1
    recorded = [
        row["result"] for row in result.tool_trace if row["tool"] == "reverify_claim"
    ]
    assert recorded[0]["recorded"]["status"] == "unknown"
    assert result.abstained is True


def test_retry_exhausted_abstains_without_writing_fresh():
    """验收 2: retry 耗尽后结束,abstain,不写 fresh。"""
    calls = []

    def execute(name, args):
        calls.append(name)
        if name == "retrieve":
            return _graded(
                "incorrect",
                reason=REASON_GRADE_INCORRECT_EXHAUSTED,
            )
        return {"recorded": {"status": "fresh", "evidence_ids": [EVIDENCE_ID]}}

    events = []
    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", _fresh_args("fresh"))]),
            _Msg(content="结束"),
        ],
        execute=execute,
        events=events,
    )
    assert calls == ["retrieve"]
    assert result.abstained is True
    assert result.retry_count == 1
    assert result.grade == "incorrect"
    assert result.evidence_ids == [EVIDENCE_ID]
    refused = [row for row in result.tool_trace if row["tool"] == "reverify_claim"]
    assert refused[0]["result"]["abstain"] is True
    assert "recorded" not in refused[0]["result"]
    assert refused[0]["result"]["reason_code"] == REASON_GRADE_INCORRECT_EXHAUSTED
    assert any(row["tool"] == VERIFY_ABSTAIN_TOOL for row in result.tool_trace)
    assert all(event["grade"] == "incorrect" for event in events if event["tool"] == VERIFY_ABSTAIN_TOOL)
    assert result.finished is True


def test_ambiguous_abstains_without_writing_fresh():
    """grade 仍不足(ambiguous)时 abstain,不写 fresh,也不占用 repair。"""
    calls = []

    def execute(name, args):
        calls.append(name)
        if name == "retrieve":
            return _graded("ambiguous", reason=REASON_GRADE_AMBIGUOUS)
        return {"recorded": {"status": "fresh"}}

    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", _fresh_args("fresh"))]),
            _Msg(content="结束"),
        ],
        execute=execute,
    )
    assert calls == ["retrieve"]
    assert result.retry_count == 0
    assert result.grade == "ambiguous"
    assert result.evidence_ids == [EVIDENCE_ID]
    assert result.abstained is True
    refused = [row for row in result.tool_trace if row["tool"] == "reverify_claim"][0]
    assert refused["result"]["reason_code"] == REASON_GRADE_AMBIGUOUS
    assert refused["result"]["grade"] == "ambiguous"
    assert "recorded" not in refused["result"]
    assert VERIFY_REPAIR_TOOL not in [row["tool"] for row in result.tool_trace]


def test_correct_grade_still_executes_fresh():
    """Correct 不强制拒答。fresh 仍交给执行器。"""
    calls = []

    def execute(name, args):
        calls.append(name)
        if name == "retrieve":
            return _graded("correct")
        return {"recorded": {"status": "fresh", "evidence_ids": [EVIDENCE_ID]}}

    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", _fresh_args("fresh"))]),
            _Msg(content="结束"),
        ],
        execute=execute,
    )
    assert calls == ["retrieve", "reverify_claim"]
    assert result.grade == "correct"
    assert result.retry_count == 0
    assert result.abstained is False
    assert result.evidence_ids == [EVIDENCE_ID]
    recorded = [row for row in result.tool_trace if row["tool"] == "reverify_claim"][0]
    assert recorded["result"]["recorded"]["status"] == "fresh"


def test_correct_after_repair_clears_abstain():
    """repair 后再读到 Correct 时,本路径不再挡住 fresh。"""
    calls = []
    grades = iter(("incorrect", "correct"))

    def execute(name, args):
        calls.append(name)
        if name == "retrieve":
            return _graded(next(grades))
        return {"recorded": {"status": "fresh", "evidence_ids": [EVIDENCE_ID]}}

    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", _fresh_args("fresh"))]),
            _Msg(content="结束"),
        ],
        execute=execute,
    )
    assert calls == ["retrieve", "retrieve", "reverify_claim"]
    assert result.retry_count == 1
    assert result.grade == "correct"
    assert result.abstained is False
    recorded = [row for row in result.tool_trace if row["tool"] == "reverify_claim"][0]
    assert recorded["result"]["recorded"]["status"] == "fresh"


def test_rule_incorrect_does_not_swallow_sufficiency_fresh_call():
    """无耗尽码且 sufficiency 不足时,fresh 仍交给既有拒答,不改记成这条 repair。"""
    calls = []

    def execute(name, args):
        calls.append(name)
        if name == "retrieve":
            return {
                "blocks": [],
                "grade": "incorrect",
                "grade_reason_code": None,
                "sufficiency": "insufficient",
                "reason_code": "insufficient_evidence",
            }
        return {
            "error": "sufficiency",
            "sufficiency": "insufficient",
            "reason_code": "insufficient_evidence",
        }

    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", _fresh_args("fresh"))]),
            _Msg(content="结束"),
        ],
        execute=execute,
    )
    assert calls == ["retrieve", "reverify_claim"]
    assert result.retry_count == 0
    assert result.abstained is False
    assert result.grade == "incorrect"
    assert result.evidence_ids == []
    refused = [row for row in result.tool_trace if row["tool"] == "reverify_claim"][0]
    assert refused["result"]["reason_code"] == "insufficient_evidence"
    assert "recorded" not in refused["result"]


def test_loop_source_has_no_langgraph_import():
    """验收 3: roles/loop.py 的 import 没有 langgraph。"""
    text = LOOP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    assert modules
    assert not any("langgraph" in name for name in modules)
    imported = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    assert not any("langgraph" in line for line in imported)
    assert "grade_retrieve_observation" not in text
    assert "crag_grade" not in text
    assert "web_search" not in text


def test_lead_loop_end_exposes_verify_state_and_does_not_write_fresh():
    """Lead 轨迹结束事件带上 evidence_ids / grade / retry_count,且不写 fresh。"""
    chunk = Chunk(
        doc_id="fix-memo",
        chunk_id="fix-memo-p1",
        clause_id="p1",
        title="备忘",
        text="T1 原文确认专业版定价仍为 299 元/席/月。",
        source_type="public",
        as_of="T1",
        doc_version="v1",
        checksum="",
        tokens=12,
    )
    chunk.crag_grade = "incorrect"  # type: ignore[attr-defined]

    class _Store(InMemoryStore):
        def __init__(self) -> None:
            super().__init__()
            self.retrieve_calls = 0

        def retrieve(self, query, *, as_of=None, source_type=None, top_k=10, tenant_id=None):
            self.retrieve_calls += 1
            self.last_retrieval_mode = "bm25"
            self.last_rerank_mode = "none"
            return [chunk]

    claim = Claim(
        claim_id="c-ag01",
        statement="专业版定价仍为 299 元/席/月",
        t0_evidence_ids=["fix-memo#p1"],
        dimension="competitor_pricing",
    )
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": "c-ag01",
            "status": "fresh",
            "evidence_ids": ["fix-memo#p1@T1"],
        })]),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="不写 fresh"),
    ])
    store = _Store()
    ctx = RunContext(store=store, guardrails=Guardrails())
    decision = LeadReverifier(ctx, claim, llm).run()
    assert store.retrieve_calls == 2
    assert llm._script == []
    assert decision.status != "fresh"
    end = [event for event in ctx.events if event.get("type") == "lead_loop_end"][-1]
    assert end["grade"] == "incorrect"
    assert end["evidence_ids"] == ["fix-memo#p1@T1"]
    assert end["retry_count"] == 1
    assert end["abstained"] is True
    refused = [
        event["result"]
        for event in ctx.events
        if event.get("type") == "lead_step" and event.get("tool") == "reverify_claim"
    ][0]
    assert refused["abstain"] is True
    assert refused["reason_code"] == REASON_GRADE_INCORRECT_EXHAUSTED
    assert "recorded" not in refused
    blob = json.dumps(ctx.events, ensure_ascii=False)
    assert "web_search" not in blob
