"""L4-AG-02: 拒答原因是封闭枚举,写入轨迹。

夹具是脚本化假 LLM 与直接 run_loop,不调用付费接口。
枚举成员与 RAG-01 / FC-CITE 已有常量是同一符号。
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from freshlatch.evidence import CITE_OUTSIDE_REGISTRY
from freshlatch.guardrails import Guardrails
from freshlatch.numeric_gate import REASON_NUMERIC_MISMATCH
from freshlatch.models import Claim
from freshlatch.roles.lead import LeadReverifier
from freshlatch.roles.loop import (
    ABSTENTION_REASONS,
    VERIFY_ABSTAIN_TOOL,
    named_abstention_reason,
    run_loop,
)
from freshlatch.roles.retrieve_grade import (
    REASON_GRADE_AMBIGUOUS,
    REASON_GRADE_INCORRECT_EXHAUSTED,
)
from freshlatch.roles.retrieve_sufficiency import REASON_INSUFFICIENT_EVIDENCE
from freshlatch.runner import RunContext
from freshlatch.store.base import Chunk, InMemoryStore
from freshlatch.tools import tool_specs

REPO = Path(__file__).resolve().parents[2]
LOOP_PATH = REPO / "src/freshlatch/roles/loop.py"
EVIDENCE_ID = "memo#p1@T1"
_SPELLINGS = (
    "insufficient_evidence",
    "cite_outside_registry",
    "grade_incorrect_exhausted",
    "grade_ambiguous",
    "numeric_mismatch",
)

_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_ag02_{_tc_counter}",
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


def _fresh_args():
    return {
        "claim_id": "c-ag02",
        "status": "fresh",
        "evidence_ids": [EVIDENCE_ID],
    }


def _jsonl(events: list[dict], path: Path) -> list[dict]:
    path.write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
    )
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_enum_is_the_same_symbols_as_rag01_and_fc_cite():
    """验收 2:枚举与 RAG-01、FC-CITE 测试引用的常量是同一符号。"""
    assert any(code is REASON_INSUFFICIENT_EVIDENCE for code in ABSTENTION_REASONS)
    assert any(code is CITE_OUTSIDE_REGISTRY for code in ABSTENTION_REASONS)
    assert any(code is REASON_GRADE_INCORRECT_EXHAUSTED for code in ABSTENTION_REASONS)
    assert any(code is REASON_GRADE_AMBIGUOUS for code in ABSTENTION_REASONS)
    assert any(code is REASON_NUMERIC_MISMATCH for code in ABSTENTION_REASONS)
    assert ABSTENTION_REASONS == frozenset({
        REASON_INSUFFICIENT_EVIDENCE,
        CITE_OUTSIDE_REGISTRY,
        REASON_GRADE_INCORRECT_EXHAUSTED,
        REASON_GRADE_AMBIGUOUS,
        REASON_NUMERIC_MISMATCH,
    })
    assert REASON_INSUFFICIENT_EVIDENCE == "insufficient_evidence"
    assert CITE_OUTSIDE_REGISTRY == "cite_outside_registry"
    assert REASON_NUMERIC_MISMATCH == "numeric_mismatch"
    text = LOOP_PATH.read_text(encoding="utf-8")
    assert "REASON_INSUFFICIENT_EVIDENCE" in text
    assert "CITE_OUTSIDE_REGISTRY" in text
    assert "REASON_GRADE_INCORRECT_EXHAUSTED" in text
    assert "REASON_GRADE_AMBIGUOUS" in text
    assert "REASON_NUMERIC_MISMATCH" in text
    for spelling in _SPELLINGS:
        assert f'"{spelling}"' not in text
        assert f"'{spelling}'" not in text


def test_abstain_jsonl_reason_is_enum_member_not_free_text_only(tmp_path):
    """验收 1:abstain 轨迹的 reason code 属于枚举,自由文本不能单独充当原因。"""
    calls = []

    def execute(name, args):
        calls.append(name)
        if name == "retrieve":
            return _graded("incorrect", reason=REASON_GRADE_INCORRECT_EXHAUSTED)
        return {"recorded": {"status": "fresh", "evidence_ids": [EVIDENCE_ID]}}

    events = []
    result, llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", _fresh_args())]),
            _Msg(content="结束"),
        ],
        execute=execute,
        events=events,
    )
    assert calls == ["retrieve"]
    assert llm.calls == 3
    assert result.abstained is True
    assert result.abstention_reason is REASON_GRADE_INCORRECT_EXHAUSTED
    rows = _jsonl(events, tmp_path / "trace.jsonl")
    abstain = [row for row in rows if row["tool"] == VERIFY_ABSTAIN_TOOL]
    assert len(abstain) == 1
    code = abstain[0]["reason_code"]
    assert code in ABSTENTION_REASONS
    assert code == REASON_GRADE_INCORRECT_EXHAUSTED
    assert abstain[0]["result"]["reason_code"] == code
    fresh = [row for row in rows if row["tool"] == "reverify_claim"][0]
    assert fresh["reason_code"] == code
    assert fresh["result"]["reason_code"] == code
    assert fresh["result"]["error"]
    assert fresh["result"]["error"] != code
    assert "recorded" not in fresh["result"]
    raw = (tmp_path / "trace.jsonl").read_text(encoding="utf-8")
    assert '"reason_code": "grade_incorrect_exhausted"' in raw


def test_ambiguous_abstain_uses_the_same_grade_symbol(tmp_path):
    """已发出的 grade_ambiguous 进入 abstain 轨迹,不另起拼写。"""
    events = []

    def execute(name, args):
        if name == "retrieve":
            return _graded("ambiguous", reason=REASON_GRADE_AMBIGUOUS)
        return {"recorded": {"status": "fresh"}}

    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(content="结束"),
        ],
        execute=execute,
        events=events,
    )
    assert result.abstention_reason is REASON_GRADE_AMBIGUOUS
    rows = _jsonl(events, tmp_path / "ambiguous.jsonl")
    abstain = [row for row in rows if row["tool"] == VERIFY_ABSTAIN_TOOL][0]
    assert abstain["reason_code"] == REASON_GRADE_AMBIGUOUS
    assert abstain["reason_code"] in ABSTENTION_REASONS


def test_insufficient_and_cite_codes_land_on_trajectory(tmp_path):
    """RAG-01 与 FC-CITE 的码写入轨迹事件,并且是枚举成员。"""
    events = []

    def execute(name, args):
        if name == "retrieve":
            return {
                "blocks": [],
                "grade": "incorrect",
                "grade_reason_code": None,
                "sufficiency": "insufficient",
                "reason_code": REASON_INSUFFICIENT_EVIDENCE,
                "error": "本轮未见可引用的 T1 块,不得写 fresh",
            }
        return {
            "error": f"{CITE_OUTSIDE_REGISTRY}: evidence_ids 必须逐字来自本轮 TurnRegistry",
            "reason_code": CITE_OUTSIDE_REGISTRY,
        }

    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", _fresh_args())]),
            _Msg(content="结束"),
        ],
        execute=execute,
        events=events,
    )
    assert result.abstained is False
    assert result.abstention_reason is CITE_OUTSIDE_REGISTRY
    rows = _jsonl(events, tmp_path / "named.jsonl")
    retrieve = [row for row in rows if row["tool"] == "retrieve"][0]
    refused = [row for row in rows if row["tool"] == "reverify_claim"][0]
    assert retrieve["reason_code"] == REASON_INSUFFICIENT_EVIDENCE
    assert retrieve["reason_code"] in ABSTENTION_REASONS
    assert retrieve["result"]["error"] != retrieve["reason_code"]
    assert refused["reason_code"] == CITE_OUTSIDE_REGISTRY
    assert refused["reason_code"] in ABSTENTION_REASONS
    assert refused["result"]["error"] != refused["reason_code"]
    assert CITE_OUTSIDE_REGISTRY in refused["result"]["error"]


def test_free_text_does_not_become_abstention_reason(tmp_path):
    """自由文本可以留在观察里,但不能成为轨迹上的 reason_code。"""
    prose = "看起来证据不太够,先不回答"
    assert named_abstention_reason(prose) is None
    assert prose not in ABSTENTION_REASONS
    events = []

    def execute(name, args):
        if name == "retrieve":
            return _graded("ambiguous", reason=prose)
        return {"recorded": {"status": "fresh"}}

    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", _fresh_args())]),
            _Msg(content="结束"),
        ],
        execute=execute,
        events=events,
    )
    assert result.abstained is True
    assert result.abstention_reason is None
    rows = _jsonl(events, tmp_path / "prose.jsonl")
    abstain = [row for row in rows if row["tool"] == VERIFY_ABSTAIN_TOOL][0]
    fresh = [row for row in rows if row["tool"] == "reverify_claim"][0]
    assert "reason_code" not in abstain
    assert "reason_code" not in abstain["result"]
    assert abstain["result"]["grade_reason_code"] == prose
    assert named_abstention_reason(abstain["result"]["grade_reason_code"]) is None
    assert "reason_code" not in fresh
    assert fresh["result"]["error"]
    assert "reason_code" not in fresh["result"]


def test_lead_loop_end_writes_enum_reason_into_events(tmp_path):
    """Lead 结束事件带上枚举拒因。Runner 落盘原样写入 JSONL。"""
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
        def retrieve(self, query, *, as_of=None, source_type=None, top_k=10, tenant_id=None):
            self.last_retrieval_mode = "bm25"
            self.last_rerank_mode = "none"
            return [chunk]

    claim = Claim(
        claim_id="c-ag02",
        statement="专业版定价仍为 299 元/席/月",
        t0_evidence_ids=["fix-memo#p1"],
        dimension="competitor_pricing",
    )
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": "c-ag02",
            "status": "fresh",
            "evidence_ids": ["fix-memo#p1@T1"],
        })]),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="不写 fresh"),
    ])
    ctx = RunContext(store=_Store(), guardrails=Guardrails())
    decision = LeadReverifier(ctx, claim, llm).run()
    assert llm._script == []
    assert decision.status != "fresh"
    rows = _jsonl(ctx.events, tmp_path / "lead.jsonl")
    end = [row for row in rows if row.get("type") == "lead_loop_end"][-1]
    assert end["abstained"] is True
    assert end["reason_code"] == REASON_GRADE_INCORRECT_EXHAUSTED
    assert end["reason_code"] in ABSTENTION_REASONS
    abstain = [
        row for row in rows
        if row.get("type") == "lead_step" and row.get("tool") == VERIFY_ABSTAIN_TOOL
    ][0]
    fresh = [
        row for row in rows
        if row.get("type") == "lead_step" and row.get("tool") == "reverify_claim"
    ][0]
    assert abstain["reason_code"] == end["reason_code"]
    assert fresh["reason_code"] == end["reason_code"]
    assert fresh["result"]["error"]
    assert fresh["result"]["error"] != end["reason_code"]
