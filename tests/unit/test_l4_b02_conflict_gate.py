"""L4-B-02: 两条 @T1 对同一可判定前提互斥则 conflicting_evidence,不得 fresh。

夹具确定性,不调用付费 LLM。Ambiguous 不单独写成这一码。
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.conflict_evidence import (
    CONFLICT_NUMERIC_TOLERANCE,
    REASON_CONFLICTING_EVIDENCE,
    T1Span,
    find_conflicting_evidence,
    fresh_refusal_for_conflicting_evidence,
)
from freshlatch.roles.lead import LEAD_PERSONA
from freshlatch.roles.loop import ABSTENTION_REASONS, run_loop
from freshlatch.roles.retrieve_grade import (
    REASON_GRADE_AMBIGUOUS,
    grade_retrieve_observation,
)
from freshlatch.runner import Runner
from freshlatch.store.base import Chunk, InMemoryStore
from freshlatch.tools import tool_specs

REPO = Path(__file__).resolve().parents[2]
CLAIM_ID = "c-b02"
LEFT_ID = "fix-memo#p1@T1"
RIGHT_ID = "fix-memo#p2@T1"
SMOOTH = "T1 原文确认专业版月费仍为 299 元/席/月。"
OTHER = "T1 原文确认专业版月费已改为 199 元/席/月。"
AGREE = "T1 原文确认专业版定价仍为 299 元/席/月。"

_DO_NOT_TOUCH = (
    "docs/evidence/quality-gate/PREREG.md",
    "docs/evidence/patch-events/RESULT-Y.md",
    "docs/evidence/patch-events/PREREG-Y.md",
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
        id=f"call_b02_{_tc_counter}",
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
    def __init__(self, hits: list[Chunk]) -> None:
        super().__init__()
        self._hits = list(hits)

    def retrieve(self, query, *, as_of=None, source_type=None, top_k=10, tenant_id=None):
        self.last_retrieval_mode = "bm25"
        self.last_rerank_mode = "none"
        return list(self._hits)


def _chunk(clause_id: str, text: str, grade: str | None = None) -> Chunk:
    chunk = Chunk(
        doc_id="fix-memo",
        chunk_id=f"fix-memo-{clause_id}",
        clause_id=clause_id,
        title="备忘",
        text=text,
        source_type="public",
        as_of="T1",
        doc_version="v1",
        checksum="",
        tokens=12,
    )
    if grade is not None:
        chunk.crag_grade = grade  # type: ignore[attr-defined]
    return chunk


def _claim(statement: str) -> Claim:
    return Claim(
        claim_id=CLAIM_ID,
        statement=statement,
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


def _store(chunks: list[Chunk]) -> _FixtureStore:
    store = _FixtureStore(chunks)
    store.add_document(
        SimpleNamespace(
            doc_id="fix-memo",
            as_of="T1",
            source_type="public",
            title="备忘",
            doc_version="v1",
            checksum="",
            full_text="\n".join(chunk.text for chunk in chunks),
        ),
        chunks,
    )
    return store


def _run(statement: str, chunks: list[Chunk], script: list, tmp_path: Path):
    llm = _ScriptLLM(script)
    runner = Runner(_store(chunks), llm=llm, guardrails=Guardrails())
    result = runner.run([_claim(statement)], trajectory_dir=tmp_path)
    return result, runner, llm


def _span(evidence_id: str, text: str) -> T1Span:
    return T1Span(evidence_id=evidence_id, text=text)


def test_tolerance_is_empty_and_reason_is_enum():
    """容差为空。拒因码与 abstention reason 是同一符号。"""
    assert CONFLICT_NUMERIC_TOLERANCE is None
    assert REASON_CONFLICTING_EVIDENCE == "conflicting_evidence"
    assert REASON_CONFLICTING_EVIDENCE in ABSTENTION_REASONS
    assert REASON_CONFLICTING_EVIDENCE != "grade_ambiguous"
    assert REASON_CONFLICTING_EVIDENCE != "numeric_mismatch"


def test_exclusive_price_pair_is_conflicting_evidence():
    """同一对象、同一属性、数字字面量互斥。不挑其中一侧。"""
    scan = find_conflicting_evidence([
        _span(LEFT_ID, SMOOTH),
        _span(RIGHT_ID, OTHER),
    ])
    assert scan.ok is False
    assert scan.reason_code == REASON_CONFLICTING_EVIDENCE
    assert len(scan.pairs) == 1
    pair = scan.pairs[0]
    assert pair.premise == "专业版月费"
    assert pair.left_id == LEFT_ID
    assert pair.right_id == RIGHT_ID
    assert pair.left_value == "299"
    assert pair.right_value == "199"
    assert "12.5" != "12.50"
    rewritten = find_conflicting_evidence([
        _span(LEFT_ID, "专业版定价仍为 12.5 元"),
        _span(RIGHT_ID, "专业版定价仍为 12.50 元"),
    ])
    assert rewritten.reason_code == REASON_CONFLICTING_EVIDENCE


def test_explicit_premise_conflict_does_not_need_a_price_word():
    """可判定前提不限于价格词。取值按字符串比较,没有容差。"""
    scan = find_conflicting_evidence([
        _span(LEFT_ID, "前提「是否续约」：续约"),
        _span(RIGHT_ID, "前提「是否续约」：不续约"),
    ])
    assert scan.reason_code == REASON_CONFLICTING_EVIDENCE
    assert scan.pairs[0].premise == "是否续约"
    assert scan.pairs[0].left_value == "续约"
    assert scan.pairs[0].right_value == "不续约"
    same = find_conflicting_evidence([
        _span(LEFT_ID, "前提「是否续约」：续约"),
        _span(RIGHT_ID, "前提「是否续约」：续约"),
    ])
    assert same.ok is True
    other_key = find_conflicting_evidence([
        _span(LEFT_ID, "前提「是否续约」：续约"),
        _span(RIGHT_ID, "前提「区域」：华北"),
    ])
    assert other_key.ok is True


def test_polarity_pair_conflicts_without_picking_a_side():
    """封闭反义对,同一属性。不低于里的低于不算反义。"""
    scan = find_conflicting_evidence([
        _span(LEFT_ID, "竞品月费仍高于本品。"),
        _span(RIGHT_ID, "竞品月费已降至本品之下。"),
    ])
    assert scan.reason_code == REASON_CONFLICTING_EVIDENCE
    assert scan.pairs[0].left_value == "高于"
    assert scan.pairs[0].right_value == "降至"
    negated = find_conflicting_evidence([
        _span(LEFT_ID, "专业版月费不低于本品。"),
        _span(RIGHT_ID, "专业版月费高于本品。"),
    ])
    assert negated.ok is True


def test_non_conflict_controls_stay_clear():
    """同意取值、不同对象、不同属性、单块、T0、新旧数同块,都不是这一码。"""
    agree = find_conflicting_evidence([
        _span(LEFT_ID, AGREE),
        _span(RIGHT_ID, AGREE),
    ])
    assert agree.ok is True
    assert agree.reason_code is None
    disjoint = find_conflicting_evidence([
        _span(LEFT_ID, "竞品A月费仍为 99 元"),
        _span(RIGHT_ID, "竞品B月费仍为 79 元"),
    ])
    assert disjoint.ok is True
    other_attr = find_conflicting_evidence([
        _span(LEFT_ID, "专业版定价仍为 299 元"),
        _span(RIGHT_ID, "续约率升至 80%"),
    ])
    assert other_attr.ok is True
    alone = find_conflicting_evidence([_span(LEFT_ID, OTHER)])
    assert alone.ok is True
    t0 = find_conflicting_evidence([
        _span("fix-memo#p1@T0", SMOOTH),
        _span(RIGHT_ID, OTHER),
    ])
    assert t0.ok is True
    superseded = find_conflicting_evidence([
        _span(LEFT_ID, "专业版定价从 299 降至 199"),
        _span(RIGHT_ID, "专业版定价为 199"),
    ])
    assert superseded.ok is True


def test_grade_does_not_emit_conflicting_evidence():
    """CRAG grade 仍不写这一码。两条价格不同的 T1 可以是 correct。"""
    graded = grade_retrieve_observation([
        {"evidence_id": LEFT_ID, "text": "定价 299"},
        {"evidence_id": RIGHT_ID, "text": "定价 199"},
    ])
    assert graded["grade"] == "correct"
    assert graded["reason_code"] is None
    assert "conflicting_evidence" not in json.dumps(graded)
    ambiguous = grade_retrieve_observation([
        {"evidence_id": LEFT_ID, "crag_grade": "ambiguous", "text": SMOOTH},
    ])
    assert ambiguous["reason_code"] == REASON_GRADE_AMBIGUOUS
    assert ambiguous["reason_code"] != REASON_CONFLICTING_EVIDENCE


def test_detector_refuses_before_executor_without_prompt():
    """检测边在循环里。系统提示没有冲突说明,fresh 也不交给执行器。"""
    calls: list[str] = []

    def execute(name, args):
        calls.append(name)
        if name == "retrieve":
            return {
                "blocks": [
                    {"evidence_id": LEFT_ID, "text": SMOOTH},
                    {"evidence_id": RIGHT_ID, "text": OTHER},
                ],
                "grade": "correct",
                "sufficiency": "sufficient",
            }
        if name == "reverify_claim":
            raise AssertionError("互斥对存在时 fresh 不得交给执行器")
        return {"ok": True}

    events: list[dict] = []
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "月费", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": CLAIM_ID,
            "status": "fresh",
            "evidence_ids": [LEFT_ID],
        })]),
        _Msg(content="不写 fresh"),
    ])
    result = run_loop(
        system="s",
        task="t",
        tools=tool_specs(["retrieve", "reverify_claim", "finish_reverify"]),
        execute=execute,
        chat=lambda messages, tools=None: llm.chat(messages, tools=tools),
        max_steps=4,
        soft_close="预算已尽,基于现有证据下结论。",
        on_event=events.append,
    )
    assert calls == ["retrieve"]
    refused = next(event["result"] for event in events if event.get("tool") == "reverify_claim")
    assert refused["reason_code"] == REASON_CONFLICTING_EVIDENCE
    assert "recorded" not in refused
    assert "已解决" not in refused["error"]
    assert "静默合并" in refused["error"]
    assert all(
        {pair["left_id"], pair["right_id"]} == {LEFT_ID, RIGHT_ID}
        for pair in refused["pairs"]
    )
    assert result.abstention_reason == REASON_CONFLICTING_EVIDENCE
    assert "conflicting_evidence" not in LEAD_PERSONA
    skill = (REPO / "skills/reverify/SKILL.md").read_text(encoding="utf-8")
    assert "conflicting_evidence" not in skill
    assert llm._script == []


def test_agreeing_pair_is_not_blocked_at_the_loop():
    """非冲突对照:两块取值相同,本闸不拒,执行器仍会看到 fresh。"""
    calls: list[str] = []

    def execute(name, args):
        calls.append(name)
        if name == "retrieve":
            return {
                "blocks": [
                    {"evidence_id": LEFT_ID, "text": AGREE},
                    {"evidence_id": RIGHT_ID, "text": AGREE},
                ],
                "grade": "correct",
                "sufficiency": "sufficient",
            }
        return {"recorded": {"status": "fresh", "evidence_ids": args.get("evidence_ids")}}

    events: list[dict] = []
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": CLAIM_ID,
            "status": "fresh",
            "evidence_ids": [LEFT_ID],
        })]),
        _Msg(content="可以写"),
    ])
    run_loop(
        system="s",
        task="t",
        tools=tool_specs(["retrieve", "reverify_claim"]),
        execute=execute,
        chat=lambda messages, tools=None: llm.chat(messages, tools=tools),
        max_steps=4,
        soft_close="预算已尽,基于现有证据下结论。",
        on_event=events.append,
    )
    assert calls == ["retrieve", "reverify_claim"]
    recorded = next(event["result"] for event in events if event.get("tool") == "reverify_claim")
    assert recorded["recorded"]["status"] == "fresh"
    assert "conflicting_evidence" not in json.dumps(recorded, ensure_ascii=False)
    assert fresh_refusal_for_conflicting_evidence([
        {"tool": "retrieve", "result": {"blocks": [
            {"evidence_id": LEFT_ID, "text": AGREE},
            {"evidence_id": RIGHT_ID, "text": AGREE},
        ]}},
    ]) is None


def test_exclusive_fixture_is_not_fresh_and_names_conflicting_evidence(tmp_path):
    """验收 1:只引用较顺的一侧也不是 fresh,轨迹含 conflicting_evidence,没有静默合并。"""
    result, runner, llm = _run(
        "专业版月费仍为 299 元/席/月",
        [_chunk("p1", SMOOTH), _chunk("p2", OTHER)],
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "月费", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", {
                "claim_id": CLAIM_ID,
                "status": "fresh",
                "evidence_ids": [LEFT_ID],
            })]),
            _Msg(tool_calls=[_tc("finish_reverify", {})]),
            _Msg(content="两块互斥,不判 fresh"),
        ],
        tmp_path,
    )
    assert result.claims[0].status != "fresh"
    assert result.decisions[CLAIM_ID].status != "fresh"
    assert result.decisions[CLAIM_ID].status == "unknown"
    refused = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert "recorded" not in refused
    assert refused["reason_code"] == REASON_CONFLICTING_EVIDENCE
    assert {item["left_id"] for item in refused["pairs"]} == {LEFT_ID}
    assert {item["right_id"] for item in refused["pairs"]} == {RIGHT_ID}
    assert "已解决" not in refused["error"]
    assert not any(event.get("type") == "critic_spawn" for event in runner.ctx.events)
    assert not any(
        event.get("type") == "cite_registry_judgment" and event.get("status") == "fresh"
        for event in runner.ctx.events
    )
    trajectory = result.trajectory_path.read_text(encoding="utf-8")
    assert '"reason_code": "conflicting_evidence"' in trajectory
    assert "已解决" not in trajectory
    assert "resolved" not in trajectory.lower()
    end = [event for event in runner.ctx.events if event.get("type") == "lead_loop_end"][-1]
    assert end["reason_code"] == REASON_CONFLICTING_EVIDENCE
    assert llm._script == []


def test_agreeing_fixture_can_still_be_fresh(tmp_path):
    """非冲突对照走到判定出口时,本闸不拒。"""
    result, runner, llm = _run(
        "专业版定价仍为 299 元/席/月",
        [_chunk("p1", AGREE), _chunk("p2", AGREE)],
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", {
                "claim_id": CLAIM_ID,
                "status": "fresh",
                "evidence_ids": [LEFT_ID],
            })]),
            _Msg(tool_calls=[_tc("report_finding", {
                "finding": "按不限方向检索后未见推翻性 T1 证据",
            })]),
            _Msg(content="无反证"),
            _aud({"status": "fresh", "reason": "T1 原文直接支持该定价", "dimension_match": True}),
            _Msg(tool_calls=[_tc("finish_reverify", {})]),
            _Msg(content="复验结束"),
        ],
        tmp_path,
    )
    recorded = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert "error" not in recorded
    assert recorded.get("reason_code") != REASON_CONFLICTING_EVIDENCE
    assert recorded["recorded"]["status"] == "fresh"
    assert result.claims[0].status == "fresh"
    trajectory = result.trajectory_path.read_text(encoding="utf-8")
    assert "conflicting_evidence" not in trajectory
    assert llm._script == []


def test_ambiguous_grade_alone_does_not_emit_conflicting_evidence(tmp_path):
    """验收 2:只有 Ambiguous、没有互斥对时,拒因仍是 grade_ambiguous。"""
    result, runner, llm = _run(
        "专业版定价仍为 299 元/席/月",
        [_chunk("p1", AGREE, grade="ambiguous")],
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", {
                "claim_id": CLAIM_ID,
                "status": "fresh",
                "evidence_ids": [LEFT_ID],
            })]),
            _Msg(tool_calls=[_tc("finish_reverify", {})]),
            _Msg(content="观察不够,不写 fresh"),
        ],
        tmp_path,
    )
    assert result.claims[0].status != "fresh"
    refused = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert refused["reason_code"] == REASON_GRADE_AMBIGUOUS
    assert refused["reason_code"] != REASON_CONFLICTING_EVIDENCE
    trajectory = result.trajectory_path.read_text(encoding="utf-8")
    assert "grade_ambiguous" in trajectory
    assert "conflicting_evidence" not in trajectory
    assert llm._script == []


def test_context_registers_conflicting_evidence():
    """词表登记与代码常量是同一符号,并与 Ambiguous 分开。"""
    text = (REPO / "CONTEXT.md").read_text(encoding="utf-8")
    assert "**conflicting_evidence**:" in text
    assert "**T1 冲突闸**:" in text
    abstention = text.split("**abstention reason**:", 1)[1].split("**", 1)[0]
    assert "`conflicting_evidence`" in abstention
    assert "`grade_ambiguous`" in abstention


def test_do_not_touch_prereg_golds_and_neural_rerank():
    """验收 4:PREREG、三份金标、x1 与 neural-rerank 不在 diff 里。"""
    base = "origin/main"
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        extra = os.environ.get("GITHUB_BASE_REF", "").strip()
        if not extra:
            pytest.skip("origin/main 缺失,跳过 Do-not-touch git 路径检查")
        base = f"origin/{extra}"
    diff = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        pytest.skip("无法对 base 做 git diff,跳过 Do-not-touch git 路径检查")
    changed = [line.strip().replace("\\", "/") for line in diff.stdout.splitlines() if line.strip()]
    for path in _DO_NOT_TOUCH:
        assert path not in changed
    assert not any(path.startswith("docs/evidence/neural-rerank/") for path in changed)
    assert not any(path.startswith("data/exp/x1/") for path in changed)
