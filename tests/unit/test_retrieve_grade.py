"""L4-RAG-02:retrieve 边 CRAG 三态。夹具确定性,不调用付费 LLM。"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.retrieve_grade import (
    REASON_GRADE_AMBIGUOUS,
    REASON_GRADE_INCORRECT_EXHAUSTED,
    fresh_refused_by_grade,
    grade_retrieve_observation,
    mark_incorrect_exhausted,
    should_refine_incorrect,
)
from freshlatch.runner import Runner
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE, Chunk, InMemoryStore
from freshlatch.store.neural_rerank import NEURAL_RERANK_K, NEURAL_RERANK_MODEL
from freshlatch.store.pipeline import RRF_K
from freshlatch.tools import LEAD_TOOLS_W3

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_ID = "fix-memo#p1@T1"

# L4-RAG-03 允许给 Chunk 加可选字段。生产臂字面量不在本表里放开。
_DO_NOT_TOUCH = (
    "src/freshlatch/gates/rule_gate.py",
    # L4-FC-01 起 loop.py 承载非法调用自纠,不再列入未改路径。
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


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_rag02_{_tc_counter}",
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


class _FixtureStore(InMemoryStore):
    """按构造时给定的块返回,不走嵌入,不打网。"""

    def __init__(self, hits: list[Chunk]) -> None:
        super().__init__()
        self._hits = list(hits)
        self.retrieve_calls = 0

    def retrieve(self, query, *, as_of=None, source_type=None, top_k=10, tenant_id=None):
        self.retrieve_calls += 1
        self.last_retrieval_mode = "bm25"
        self.last_rerank_mode = "none"
        return list(self._hits)


def _chunk(grade: str | None = None) -> Chunk:
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
    if grade is not None:
        chunk.crag_grade = grade  # type: ignore[attr-defined]
    return chunk


def _claim() -> Claim:
    return Claim(
        claim_id="c-rag02",
        statement="专业版定价仍为 299 元/席/月",
        t0_evidence_ids=["fix-memo#p1"],
        dimension="competitor_pricing",
    )


def _aud(payload: dict) -> _Msg:
    return _Msg(content=json.dumps(payload, ensure_ascii=False))


def _lead_tool_results(events: list[dict], tool: str) -> list[dict]:
    return [
        event["result"]
        for event in events
        if event.get("type") == "lead_step" and event.get("tool") == tool
    ]


def _short_refuse_script() -> list[_Msg]:
    return [
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": "c-rag02",
            "status": "fresh",
            "evidence_ids": [EVIDENCE_ID],
        })]),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="不写 fresh"),
    ]


def test_rule_grades_t1_correct_and_injection_wins():
    """无注入:有 @T1 为 correct,没有则为 incorrect。注入覆盖规则。"""
    empty = grade_retrieve_observation([])
    assert empty["grade"] == "incorrect"
    assert empty["source"] == "rule"
    assert empty["reason_code"] is None
    assert should_refine_incorrect(empty) is False
    t1 = grade_retrieve_observation([{"evidence_id": EVIDENCE_ID, "text": "现价"}])
    assert t1 == {"grade": "correct", "reason_code": None, "source": "rule"}
    injected = grade_retrieve_observation([
        {"evidence_id": EVIDENCE_ID, "crag_grade": "Incorrect"},
    ])
    assert injected["grade"] == "incorrect"
    assert injected["source"] == "injected"
    assert should_refine_incorrect(injected) is True
    exhausted = mark_incorrect_exhausted(injected)
    assert exhausted["reason_code"] == REASON_GRADE_INCORRECT_EXHAUSTED
    ambiguous = grade_retrieve_observation([
        {"evidence_id": EVIDENCE_ID, "crag_grade": "ambiguous"},
    ])
    assert ambiguous["grade"] == "ambiguous"
    assert ambiguous["reason_code"] == REASON_GRADE_AMBIGUOUS
    mixed = grade_retrieve_observation([
        {"evidence_id": EVIDENCE_ID, "crag_grade": "correct"},
        {"evidence_id": "other#p1@T1", "crag_grade": "ambiguous"},
        {"evidence_id": "third#p1@T1", "crag_grade": "incorrect"},
    ])
    assert mixed["grade"] == "incorrect"


def test_two_t1_blocks_are_not_conflicting_evidence():
    """两条 T1 正文不同仍是 correct。conflicting_evidence 不在本票。"""
    graded = grade_retrieve_observation([
        {"evidence_id": "a#p1@T1", "text": "定价 299"},
        {"evidence_id": "b#p1@T1", "text": "定价 199"},
    ])
    assert graded["grade"] == "correct"
    assert "conflicting_evidence" not in json.dumps(graded)


def test_consumer_reads_grade_and_does_not_recompute():
    """Agent 只读观察上的 grade。块内容即使像 correct,也不改写 ambiguous。"""
    assert fresh_refused_by_grade([]) is None
    assert fresh_refused_by_grade([
        {"grade": "correct", "blocks": [], "grade_reason_code": None},
    ]) is None
    assert fresh_refused_by_grade([
        {"grade": "incorrect", "grade_reason_code": None, "blocks": []},
    ]) is None
    refused = fresh_refused_by_grade([
        {
            "grade": "ambiguous",
            "grade_reason_code": REASON_GRADE_AMBIGUOUS,
            "blocks": [{"evidence_id": EVIDENCE_ID, "text": "充分支持"}],
        },
    ])
    assert refused == {"grade": "ambiguous", "reason_code": REASON_GRADE_AMBIGUOUS}
    exhausted = fresh_refused_by_grade([
        {
            "grade": "incorrect",
            "grade_reason_code": REASON_GRADE_INCORRECT_EXHAUSTED,
        },
        {"grade": "correct", "grade_reason_code": None},
    ])
    assert exhausted is None


def test_incorrect_fixture_retries_once_then_refuses(tmp_path):
    """验收 1:Incorrect 再检索一次后仍失败并拒答,reason 可枚举,无 web_search。"""
    llm = _ScriptLLM(_short_refuse_script())
    store = _FixtureStore([_chunk("incorrect")])
    runner = Runner(store, llm=llm, guardrails=Guardrails())
    result = runner.run([_claim()], trajectory_dir=tmp_path)

    assert store.retrieve_calls == 2
    retrieve_events = [e for e in runner.ctx.events if e.get("type") == "retrieve"]
    assert len(retrieve_events) == 2
    observation = _lead_tool_results(runner.ctx.events, "retrieve")[0]
    assert observation["grade"] == "incorrect"
    assert observation["grade_reason_code"] == REASON_GRADE_INCORRECT_EXHAUSTED
    assert observation["grade_attempts"] == 2
    assert observation["grade_token"] == "grade=incorrect"
    assert "crag_grade" not in observation["blocks"][0]
    refused = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert refused["reason_code"] == "grade_incorrect_exhausted"
    assert refused["grade"] == "incorrect"
    assert "recorded" not in refused
    assert result.claims[0].status != "fresh"
    assert result.decisions["c-rag02"].status != "fresh"
    trajectory = result.trajectory_path.read_text(encoding="utf-8")
    assert "grade_incorrect_exhausted" in trajectory
    assert "web_search" not in trajectory
    assert "web_search" not in LEAD_TOOLS_W3
    assert all(event.get("tool") != "web_search" for event in runner.ctx.events)
    assert llm._script == []


def test_correct_fixture_rule_gate_allow_is_not_forced_refuse(tmp_path):
    """验收 2:Correct 且规则闸会放行时,本票不强制拒答。"""
    minimal = GateDecision(
        status="fresh",
        t1_evidence_ids=[EVIDENCE_ID],
        auditor_verdict="fresh",
    )
    gate = rule_gate(
        _claim(),
        minimal,
        GateContext(checksum_fn=lambda doc_id, as_of: None),
    )
    assert gate.green is True

    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": "c-rag02",
            "status": "fresh",
            "evidence_ids": [EVIDENCE_ID],
        })]),
        _Msg(tool_calls=[_tc("report_finding", {
            "finding": "按不限方向检索后未见推翻性 T1 证据",
        })]),
        _Msg(content="无反证"),
        _aud({"status": "fresh", "reason": "T1 原文直接支持该定价", "dimension_match": True}),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    chunk = _chunk("correct")
    store = _FixtureStore([chunk])
    store.add_document(
        SimpleNamespace(
            doc_id="fix-memo",
            as_of="T1",
            source_type="public",
            title="备忘",
            doc_version="v1",
            checksum="",
            full_text=chunk.text,
        ),
        [chunk],
    )
    runner = Runner(store, llm=llm, guardrails=Guardrails())
    result = runner.run([_claim()], trajectory_dir=tmp_path)

    assert store.retrieve_calls == 1
    observation = _lead_tool_results(runner.ctx.events, "retrieve")[0]
    assert observation["grade"] == "correct"
    assert observation["grade_reason_code"] is None
    assert observation["grade_token"] == "grade=correct"
    assert fresh_refused_by_grade([observation]) is None
    recorded = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert "error" not in recorded
    assert recorded["recorded"]["status"] == "fresh"
    assert result.claims[0].status == "fresh"
    assert result.decisions["c-rag02"].status == "fresh"
    trajectory = result.trajectory_path.read_text(encoding="utf-8")
    assert "web_search" not in trajectory


def test_ambiguous_fixture_keeps_grade_and_does_not_write_fresh(tmp_path):
    """验收 3:轨迹含 grade=ambiguous,且不把该状态写成 fresh。"""
    llm = _ScriptLLM(_short_refuse_script())
    store = _FixtureStore([_chunk("ambiguous")])
    runner = Runner(store, llm=llm, guardrails=Guardrails())
    result = runner.run([_claim()], trajectory_dir=tmp_path)

    assert store.retrieve_calls == 1
    observation = _lead_tool_results(runner.ctx.events, "retrieve")[0]
    assert observation["grade"] == "ambiguous"
    assert observation["grade_token"] == "grade=ambiguous"
    assert observation["grade_reason_code"] == "grade_ambiguous"
    refused = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert refused["grade"] == "ambiguous"
    assert refused["reason_code"] == "grade_ambiguous"
    assert "recorded" not in refused
    assert result.claims[0].status != "fresh"
    assert result.decisions["c-rag02"].status != "fresh"
    trajectory = result.trajectory_path.read_text(encoding="utf-8")
    assert "grade=ambiguous" in trajectory
    assert '"grade": "ambiguous"' in trajectory
    assert "web_search" not in trajectory
    assert llm._script == []


def test_loop_does_not_grade():
    """Agent 循环不另写 grade,也不引进 langgraph。"""
    text = (REPO / "src/freshlatch/roles/loop.py").read_text(encoding="utf-8")
    imported = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    assert not any("langgraph" in line for line in imported)
    assert "grade_retrieve_observation" not in text
    assert "crag_grade" not in text
    assert "web_search" not in text


def test_frozen_retrieval_pins():
    """检索常量不依赖 git,浅克隆也必须跑。"""
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert RRF_K == 60
    assert NEURAL_RERANK_K == 10
    assert NEURAL_RERANK_MODEL == "BAAI/bge-reranker-base"
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "fastembed==0.8.1" in pyproject


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


def test_do_not_touch_paths_and_frozen_pins():
    """验收 4 的路径半边:有 base 时 Do-not-touch 不在 diff 里。缺 ref 则跳过,不让 CI exit 128。"""
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


def test_no_t1_rule_gate_still_blocks_fresh():
    """规则闸无 t1_evidence_ids 不得 fresh,本票未放宽。"""
    blocked = rule_gate(
        _claim(),
        GateDecision(status="fresh", t1_evidence_ids=[], auditor_verdict="fresh"),
        GateContext(checksum_fn=lambda doc_id, as_of: None),
    )
    assert blocked.green is False
    assert blocked.error_code == "NO_T1_EVIDENCE"
