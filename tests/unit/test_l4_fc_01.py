"""L4-FC-01: 非法调用 typed reason、有限自纠、耗尽 fail-closed。

夹具是脚本化假 LLM,不调用付费接口。
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.guardrails import Guardrails
from freshlatch.models import LOCAL_EMBED_MODEL, MODEL_REGISTRY, Claim
from freshlatch.roles.lead import LeadReverifier
from freshlatch.roles.loop import (
    ILLEGAL_CALL_EXHAUSTED_TOOL,
    ILLEGAL_CALL_REPAIR_BUDGET,
    UnknownToolGuard,
    run_loop,
)
from freshlatch.runner import RunContext
from freshlatch.store.base import (
    PRODUCTION_RETRIEVAL_MODE,
    Chunk,
    InMemoryStore,
)
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import RRF_K
from freshlatch.store.query_transform import transform_claim_query
from freshlatch.tools import (
    FOCUS_DIMENSIONS,
    LEAD_TOOLS_W3,
    LEAD_TOOLS_W9,
    REASON_ILLEGAL_DIMENSION,
    REASON_ILLEGAL_TOOL_ARGS,
    REASON_UNKNOWN_TOOL,
    tool_schema_error,
    tool_specs,
)

REPO = Path(__file__).resolve().parents[2]
MODEL_QUERY = "这是一段自由散文检索词"

_DO_NOT_TOUCH = (
    "src/freshlatch/eval/quality_gate.py",
    "src/freshlatch/evidence.py",
    "src/freshlatch/store/base.py",
    "src/freshlatch/store/pipeline.py",
    "src/freshlatch/store/neural_rerank.py",
    "docs/evidence/patch-events/RESULT-Y.md",
    "docs/evidence/patch-events/PREREG-Y.md",
    "docs/evidence/quality-gate/PREREG.md",
    "docs/evidence/neural-rerank/summary.json",
    "docs/evidence/neural-rerank/per-query.json",
    "data/eval/guard_should.json",
    "data/eval/cite_sentence.json",
    "data/eval/temporal_new_over_old.json",
    "data/eval/gold.json",
)

_tc_counter = 0


def _tc(name, args, *, raw=None):
    global _tc_counter
    _tc_counter += 1
    if raw is None:
        raw = json.dumps(args, ensure_ascii=False)
    return SimpleNamespace(
        id=f"call_fc01_{_tc_counter}",
        type="function",
        function=SimpleNamespace(name=name, arguments=raw),
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


def _run(script, *, execute, tools=None, max_steps=8, events=None):
    llm = _ScriptLLM(script)
    specs = tools if tools is not None else tool_specs(["retrieve"])

    def chat(messages, tools=None):
        return llm.chat(messages, tools=tools)

    result = run_loop(
        system="s",
        task="t",
        tools=specs,
        execute=execute,
        chat=chat,
        max_steps=max_steps,
        soft_close="预算已尽,基于现有证据下结论。",
        on_event=None if events is None else events.append,
    )
    return result, llm


def _unknown(name="web_search"):
    return _Msg(tool_calls=[_tc(name, {"query": "x"})])


def test_repair_budget_is_finite_and_explicit():
    assert ILLEGAL_CALL_REPAIR_BUDGET == 2


def test_unknown_tool_retries_then_fail_closed_with_trail():
    """验收 1: 白名单外工具名留下 reason code,有限再试,耗尽失败且不抛异常。"""
    executed = []
    events = []
    result, llm = _run(
        [_unknown(), _unknown(), _unknown(), _Msg(content="不应再被调用")],
        execute=lambda name, args: executed.append((name, args)) or {"ok": True},
        events=events,
    )
    assert executed == []
    assert llm.calls == ILLEGAL_CALL_REPAIR_BUDGET + 1
    assert result.failed is True
    assert result.finished is False
    assert result.failure_reason == REASON_UNKNOWN_TOOL
    assert result.illegal_repairs == ILLEGAL_CALL_REPAIR_BUDGET + 1
    assert [row["tool"] for row in result.tool_trace] == [
        "web_search", "web_search", "web_search", ILLEGAL_CALL_EXHAUSTED_TOOL,
    ]
    assert [row["reason_code"] for row in result.tool_trace] == [REASON_UNKNOWN_TOOL] * 4
    assert result.tool_trace[-1]["result"]["failed"] is True
    assert result.tool_trace[-1]["result"]["repair_budget"] == ILLEGAL_CALL_REPAIR_BUDGET
    assert all(event["reason_code"] == REASON_UNKNOWN_TOOL for event in events)
    assert not any(row["tool"] == "__soft_close__" for row in result.tool_trace)
    roles = [message["role"] for message in result.messages]
    assert roles == ["system", "user", "assistant", "tool", "assistant", "tool", "assistant", "tool"]
    fed_back = json.loads(result.messages[3]["content"])
    assert fed_back["reason_code"] == REASON_UNKNOWN_TOOL
    assert "web_search" in fed_back["error"]
    assert "retrieve" in fed_back["error"]


def test_two_illegal_calls_still_allow_self_repair():
    """预算内的两次非法调用回灌后,模型可以收尾,运行不算失败。"""
    result, llm = _run(
        [_unknown(), _unknown(), _Msg(content="改回白名单内工具后收尾")],
        execute=lambda name, args: {"ok": True},
    )
    assert llm.calls == 3
    assert result.failed is False
    assert result.finished is True
    assert result.illegal_repairs == ILLEGAL_CALL_REPAIR_BUDGET
    assert [row["reason_code"] for row in result.tool_trace] == [REASON_UNKNOWN_TOOL, REASON_UNKNOWN_TOOL]
    assert ILLEGAL_CALL_EXHAUSTED_TOOL not in [row["tool"] for row in result.tool_trace]


def test_illegal_args_share_the_same_repair_budget():
    """缺参、坏 JSON、白名单外名字共用一个预算,且都不执行工具。"""
    executed = []
    bad_json = _Msg(tool_calls=[_tc("retrieve", {}, raw="{")])
    missing = _Msg(tool_calls=[_tc("retrieve", {})])
    result, llm = _run(
        [missing, bad_json, _unknown(), _Msg(content="不应再被调用")],
        execute=lambda name, args: executed.append(name) or {"blocks": []},
    )
    assert executed == []
    assert llm.calls == 3
    assert result.failed is True
    assert result.failure_reason == REASON_UNKNOWN_TOOL
    assert [row["reason_code"] for row in result.tool_trace[:3]] == [
        REASON_ILLEGAL_TOOL_ARGS,
        REASON_ILLEGAL_TOOL_ARGS,
        REASON_UNKNOWN_TOOL,
    ]
    assert "缺少必填参数" in result.tool_trace[0]["result"]["error"]
    assert "不是合法 JSON" in result.tool_trace[1]["result"]["error"]


def test_mark_stale_without_claim_id_stays_schema_legal():
    """Critic 的 mark_stale 不传 claim_id。循环层不得把它当成非法参数。"""
    spec = tool_specs(["mark_stale"])[0]
    args = {
        "reason": "T1 原文写明前提已被推翻,主张不再成立。",
        "evidence_ids": ["doc#p1@T1"],
        "dimension": "cost_model",
    }
    assert tool_schema_error(spec, args) is None


def test_schema_valid_retrieve_still_executes():
    """schema 再验不拦截声明过的可选字段。多余字段在执行前拒绝。"""
    spec = tool_specs(["retrieve"])[0]
    legal = {"query": "q", "source_type": "public", "as_of": "T1", "tenant_id": "acme"}
    assert tool_schema_error(spec, legal) is None
    assert tool_schema_error(spec, {"query": "q", "retrieval_mode": "dense"})
    executed = []
    result, _llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", legal)]),
            _Msg(content="收尾"),
        ],
        execute=lambda name, args: executed.append(args) or {"blocks": []},
    )
    assert result.failed is False
    assert executed == [legal]


def test_step_budget_soft_close_unchanged_inside_repair_budget():
    """步数耗尽仍走软收尾。非法调用未到自纠上限时不改这条路径。"""
    result, llm = _run(
        [_unknown(), _Msg(content="软收尾后的最终结论")],
        execute=lambda name, args: {"blocks": []},
        max_steps=1,
    )
    assert llm.calls == 2
    assert result.failed is False
    assert result.finished is False
    assert result.tool_trace[-1]["tool"] == "__soft_close__"
    assert result.tool_trace[0]["reason_code"] == REASON_UNKNOWN_TOOL


def test_execute_unknown_tool_guard_is_recorded_not_raised():
    """执行器若仍抛 UnknownToolGuard,循环记下同一 reason code,不把异常抛出。"""

    def execute(name, args):
        raise UnknownToolGuard(name, ["retrieve"])

    result, llm = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "q"})]),
            _Msg(tool_calls=[_tc("retrieve", {"query": "q"})]),
            _Msg(tool_calls=[_tc("retrieve", {"query": "q"})]),
        ],
        execute=execute,
    )
    assert llm.calls == 3
    assert result.failed is True
    assert result.failure_reason == REASON_UNKNOWN_TOOL
    assert result.tool_trace[0]["tool"] == "retrieve"


def test_handler_illegal_dimension_is_not_the_loop_repair_budget():
    """dimension 非法值仍进处理函数整 call 拒绝,不占用循环自纠预算。"""
    specs = tool_specs(["mark_stale"])
    args = {
        "claim_id": "c5",
        "reason": "T1 原文写明前提已不成立,所以主张失效。",
        "evidence_ids": ["doc#p1@T1"],
        "dimension": "pricing",
    }
    seen = []

    def execute(name, got):
        seen.append(got)
        return {
            "error": "dimension 只能是 %s 之一;收到: %r" % ("/".join(FOCUS_DIMENSIONS), got["dimension"]),
            "reason_code": REASON_ILLEGAL_DIMENSION,
        }

    result, _llm = _run(
        [_Msg(tool_calls=[_tc("mark_stale", args)]), _Msg(content="收尾")],
        execute=execute,
        tools=specs,
    )
    assert seen == [args]
    assert result.failed is False
    assert result.illegal_repairs == 0
    assert result.tool_trace[0]["result"]["reason_code"] == REASON_ILLEGAL_DIMENSION


def _chunk(doc_id: str, text: str) -> Chunk:
    return Chunk(
        doc_id=doc_id, chunk_id=f"{doc_id}-p1", clause_id="p1", title="t",
        text=text, source_type="public", as_of="T1", doc_version="v1",
        checksum="", tokens=8,
    )


def _store() -> InMemoryStore:
    store = InMemoryStore()
    store.add_document(
        SimpleNamespace(doc_id="t1-pricing", as_of="T1", source_type="public",
                        title="t", doc_version="v1", checksum="", full_text="x"),
        [
            _chunk("t1-pricing", "专业版定价已调整,旧定价不再适用。"),
            _chunk("t1-other", "访谈纪要只谈交付周期。"),
            _chunk("t1-market", "市场结构观察与定价无关。"),
        ],
    )
    return store


def test_legal_retrieve_still_uses_claim_query_transform():
    """验收 3: 合法 retrieve 的查询串仍来自 transform_claim_query,模型 query 被忽略。"""
    claim = Claim(
        claim_id="c-fc01",
        statement="专业版定价 299 元/席/月",
        dimension="competitor_pricing",
    )
    ctx = RunContext(store=_store(), mode="online", guardrails=Guardrails())
    llm = _ScriptLLM([
        _unknown(),
        _Msg(tool_calls=[_tc("retrieve", {
            "query": MODEL_QUERY,
            "as_of": "T1",
            "source_type": "public",
        })]),
        _Msg(content="检索后收尾"),
    ])
    lead = LeadReverifier(ctx, claim, llm)
    decision = lead.run()
    assert llm._script == []
    assert llm.calls == 3
    expected = transform_claim_query(claim.statement, dimension=claim.dimension)
    queries = [event["query"] for event in ctx.events if event.get("type") == "retrieve"]
    assert queries
    assert queries == [expected] * len(queries)
    assert all(MODEL_QUERY not in query for query in queries)
    ends = [event for event in ctx.events if event.get("type") == "lead_loop_end"]
    assert ends[-1]["failed"] is False
    assert ends[-1]["finished"] is True
    assert decision.status == "unknown"
    assert "fail-closed" not in decision.reason


def test_lead_unknown_tool_exhaustion_fails_closed_on_the_run():
    """Lead 跑完时轨迹与判定都记下失败,而不是无记录抛出。"""
    claim = Claim(claim_id="c-fc01", statement="专业版定价 299 元/席/月")
    ctx = RunContext(store=InMemoryStore(), guardrails=Guardrails())
    llm = _ScriptLLM([_unknown(), _unknown(), _unknown(), _Msg(content="不应再被调用")])
    lead = LeadReverifier(ctx, claim, llm)
    decision = lead.run()
    assert llm.calls == ILLEGAL_CALL_REPAIR_BUDGET + 1
    steps = [event for event in ctx.events if event.get("type") == "lead_step"]
    assert [event["reason_code"] for event in steps] == [REASON_UNKNOWN_TOOL] * 4
    assert steps[-1]["tool"] == ILLEGAL_CALL_EXHAUSTED_TOOL
    end = [event for event in ctx.events if event.get("type") == "lead_loop_end"][-1]
    assert end["failed"] is True
    assert end["failure_reason"] == REASON_UNKNOWN_TOOL
    assert end["finished"] is False
    assert decision.status == "unknown"
    assert decision.reason == f"非法调用自纠耗尽({REASON_UNKNOWN_TOOL}),fail-closed"


def test_lead_mark_stale_illegal_dimension_keeps_whole_call_rejection():
    """验收 2: 非法 dimension 仍整 call 拒绝,并带上 typed reason。"""
    claim = Claim(claim_id="c5", statement="专业版定价 299 元/席/月", dimension="cost_model")
    lead = LeadReverifier(RunContext(store=InMemoryStore()), claim, llm=_ScriptLLM([]))
    lead._seen_evidence.add("t0-x#p2@T1")
    reason = "T1 原文写明专业版已经停售并退出报价单,原先仍在售卖的前提被推翻。"
    rejected = lead._t_mark_stale({
        "claim_id": "c5",
        "reason": reason,
        "evidence_ids": ["t0-x#p2@T1"],
        "dimension": "pricing",
    })
    assert rejected["reason_code"] == REASON_ILLEGAL_DIMENSION
    assert "error" in rejected
    for dim in FOCUS_DIMENSIONS:
        assert dim in rejected["error"]
    assert lead.decision.status == "unknown"
    assert lead.decision.stale_dimension is None
    assert lead.decision.auditor_verdict is None
    assert llm_was_not_called(lead)


def llm_was_not_called(lead: LeadReverifier) -> bool:
    assert lead.llm.calls == 0
    return True


def test_default_mounts_stay_closed():
    assert "web_search" not in LEAD_TOOLS_W3
    assert "web_search" not in LEAD_TOOLS_W9
    assert "list_memories" not in LEAD_TOOLS_W3
    assert "spawn_forensic" not in LEAD_TOOLS_W3


def test_loop_does_not_import_langgraph():
    text = (REPO / "src/freshlatch/roles/loop.py").read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        assert not stripped.startswith("import langgraph")
        assert not stripped.startswith("from langgraph")


def test_frozen_retrieval_pins():
    """检索常量不依赖 git,浅克隆也必须跑。"""
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert RRF_K == 60
    assert NEURAL_RERANK_K == 10
    assert LOCAL_EMBED_MODEL == "BAAI/bge-small-zh-v1.5"
    assert MODEL_REGISTRY["neural_rerank"].model == "BAAI/bge-reranker-base"
    pin = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "fastembed==0.8.1" in pin


def _git_base_ref() -> str | None:
    """解析对比基线。浅克隆没有 origin/main 时返回 None,不 fetch。"""
    candidates = ["origin/main"]
    extra = os.environ.get("GITHUB_BASE_REF", "").strip()
    if extra:
        candidates.append(f"origin/{extra}")
    seen: list[str] = []
    for ref in candidates:
        if ref in seen:
            continue
        seen.append(ref)
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return ref
    return None


def test_do_not_touch_paths_skip_when_base_missing():
    """有 base 时 Do-not-touch 路径不在 diff 里。缺少 base ref 时 skip。"""
    base = _git_base_ref()
    if base is None:
        pytest.skip("origin/main 缺失,跳过 Do-not-touch git 路径检查")
    diff = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        pytest.skip(
            "无法对 base 做 git diff,跳过 Do-not-touch git 路径检查: "
            + (diff.stderr or "").strip()
        )
    changed = [line.strip().replace("\\", "/") for line in diff.stdout.splitlines() if line.strip()]
    for path in _DO_NOT_TOUCH:
        assert path not in changed
    assert not any(path.startswith("data/exp/x1/") for path in changed)
