"""L4-RAG-01:检索观察 sufficiency。夹具确定性,不调用付费 LLM。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.retrieve_sufficiency import (
    REASON_INSUFFICIENT_EVIDENCE,
    label_retrieve_sufficiency,
    may_continue_fresh_write,
)
from freshlatch.runner import Runner
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE, Chunk, InMemoryStore
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import RRF_K

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_ID = "fix-memo#p1@T1"
T0_ONLY_ID = "fix-memo#p1@T0"

_DO_NOT_TOUCH = (
    "src/freshlatch/store/base.py",
    "src/freshlatch/gates/rule_gate.py",
    "src/freshlatch/roles/loop.py",
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
        id=f"call_rag01_{_tc_counter}",
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


def _chunk(evidence_as_of: str = "T1") -> Chunk:
    return Chunk(
        doc_id="fix-memo",
        chunk_id="fix-memo-p1",
        clause_id="p1",
        title="备忘",
        text="T1 原文确认专业版定价仍为 299 元/席/月。",
        source_type="public",
        as_of=evidence_as_of,  # type: ignore[arg-type]
        doc_version="v1",
        checksum="",
        tokens=12,
    )


def _claim() -> Claim:
    return Claim(
        claim_id="c-rag01",
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


def test_label_zero_blocks_insufficient_and_t1_block_sufficient():
    empty = label_retrieve_sufficiency([])
    assert empty == {
        "sufficiency": "insufficient",
        "reason_code": REASON_INSUFFICIENT_EVIDENCE,
    }
    t0_only = label_retrieve_sufficiency([{"evidence_id": T0_ONLY_ID, "text": "旧"}])
    assert t0_only["sufficiency"] == "insufficient"
    assert t0_only["reason_code"] == REASON_INSUFFICIENT_EVIDENCE
    labeled = label_retrieve_sufficiency([
        {"evidence_id": T0_ONLY_ID},
        {"evidence_id": EVIDENCE_ID, "text": "现价"},
    ])
    assert labeled == {"sufficiency": "sufficient", "reason_code": None}
    assert may_continue_fresh_write([empty]) is False
    assert may_continue_fresh_write([labeled]) is True
    assert may_continue_fresh_write([empty, labeled]) is True
    assert may_continue_fresh_write([]) is True


def test_zero_blocks_decision_exit_is_not_fresh(tmp_path):
    """验收 1:零块夹具跑到判定出口,不发 fresh,轨迹带不足标签。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": "c-rag01",
            "status": "fresh",
            "evidence_ids": [EVIDENCE_ID],
        })]),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="未见 T1 块,不判 fresh"),
    ])
    store = _FixtureStore([])
    runner = Runner(store, llm=llm, guardrails=Guardrails())
    result = runner.run([_claim()], trajectory_dir=tmp_path)

    claim = result.claims[0]
    assert claim.status != "fresh"
    assert result.decisions["c-rag01"].status != "fresh"
    observations = _lead_tool_results(runner.ctx.events, "retrieve")
    assert observations[0]["blocks"] == []
    assert observations[0]["sufficiency"] == "insufficient"
    assert observations[0]["reason_code"] == "insufficient_evidence"
    refused = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert refused["sufficiency"] == "insufficient"
    assert refused["reason_code"] == "insufficient_evidence"
    trajectory = result.trajectory_path.read_text(encoding="utf-8")
    assert '"sufficiency": "insufficient"' in trajectory
    assert '"reason_code": "insufficient_evidence"' in trajectory
    assert llm._script == []
    assert llm.calls == 4


def test_t1_block_rule_gate_allow_is_not_forced_refuse(tmp_path):
    """验收 2:至少一条 @T1,且规则闸最小放行输入不被本票改成拒答。"""
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
            "claim_id": "c-rag01",
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
    chunk = _chunk("T1")
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

    observations = _lead_tool_results(runner.ctx.events, "retrieve")
    assert any(block["evidence_id"] == EVIDENCE_ID for block in observations[0]["blocks"])
    assert observations[0]["sufficiency"] == "sufficient"
    assert observations[0]["reason_code"] is None
    assert may_continue_fresh_write(observations) is True
    recorded = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert "error" not in recorded
    assert recorded["recorded"]["status"] == "fresh"
    assert result.claims[0].status == "fresh"
    assert result.decisions["c-rag01"].status == "fresh"


def test_do_not_touch_paths_and_frozen_pins():
    """验收 3:Do-not-touch 路径不在相对 origin/main 的 diff 里;检索常量未改。"""
    diff = subprocess.check_output(
        ["git", "diff", "--name-only", "origin/main"],
        cwd=REPO,
        text=True,
    )
    changed = [line.strip() for line in diff.splitlines() if line.strip()]
    for path in _DO_NOT_TOUCH:
        assert path not in changed
    assert not any(path.startswith("data/exp/x1/") for path in changed)
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert RRF_K == 60
    assert NEURAL_RERANK_K == 10


def test_no_t1_rule_gate_still_blocks_fresh():
    """规则闸无 t1_evidence_ids 不得 fresh,本票未放宽。"""
    blocked = rule_gate(
        _claim(),
        GateDecision(status="fresh", t1_evidence_ids=[], auditor_verdict="fresh"),
        GateContext(checksum_fn=lambda doc_id, as_of: None),
    )
    assert blocked.green is False
    assert blocked.error_code == "NO_T1_EVIDENCE"
