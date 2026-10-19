"""L4-B-01: 主张数字与所引 @T1 span 逐字对账。夹具确定性,不调用付费 LLM。"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.numeric_gate import (
    NUMERIC_TOLERANCE,
    REASON_NUMERIC_MISMATCH,
    check_verbatim_numbers,
    extract_numeric_tokens,
)
from freshlatch.roles.loop import ABSTENTION_REASONS
from freshlatch.runner import Runner
from freshlatch.store.base import Chunk, InMemoryStore

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_ID = "fix-memo#p1@T1"
CLAIM_ID = "c-b01"

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
        id=f"call_b01_{_tc_counter}",
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


def _chunk(text: str) -> Chunk:
    return Chunk(
        doc_id="fix-memo",
        chunk_id="fix-memo-p1",
        clause_id="p1",
        title="备忘",
        text=text,
        source_type="public",
        as_of="T1",
        doc_version="v1",
        checksum="",
        tokens=12,
    )


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


def _run(statement: str, span: str, script: list, tmp_path: Path):
    chunk = _chunk(span)
    store = _FixtureStore([chunk])
    store.add_document(
        SimpleNamespace(
            doc_id="fix-memo",
            as_of="T1",
            source_type="public",
            title="备忘",
            doc_version="v1",
            checksum="",
            full_text=span,
        ),
        [chunk],
    )
    llm = _ScriptLLM(script)
    runner = Runner(store, llm=llm, guardrails=Guardrails())
    result = runner.run([_claim(statement)], trajectory_dir=tmp_path)
    return result, runner, llm


def test_tolerance_is_declared_empty_and_reason_is_enum():
    """容差为空。拒因码与 abstention reason 是同一符号。"""
    assert NUMERIC_TOLERANCE is None
    assert REASON_NUMERIC_MISMATCH == "numeric_mismatch"
    assert REASON_NUMERIC_MISMATCH in ABSTENTION_REASONS


def test_verbatim_match_does_not_abstain():
    """验收 1 的纯函数半边:数字在 T1 span 中逐字可定位,本闸不拒。"""
    claim = "专业版定价仍为 299 元/席/月,毛利 12.5%。"
    span = "T1 备忘:专业版定价仍为 299 元/席/月,毛利 12.5%。"
    result = check_verbatim_numbers(claim, [span])
    assert result.ok is True
    assert result.reason_code is None
    assert result.missing == ()
    assert extract_numeric_tokens("T1 快照 p1 无独立数字") == ()
    assert extract_numeric_tokens("营收 299B") == ("299",)


def test_number_in_any_cited_span_is_enough():
    """多个所引 span 时,数字落在其中一条即可。"""
    result = check_verbatim_numbers(
        "客单价 99 美元",
        ["T1 只谈续约", "客单价仍为 99 美元"],
    )
    assert result.ok is True
    assert result.missing == ()


def test_claim_without_numbers_is_not_refused_by_this_gate():
    """主张没有数字字面量时,本闸不拒答。"""
    result = check_verbatim_numbers("监管暂无本地化强制要求", ["T1 原文无数字"])
    assert result.ok is True
    assert result.reason_code is None


def test_fake_quote_and_rewritten_number_are_mismatch():
    """假 quote / 改写数字对不上,不得当成通过。"""
    fake = check_verbatim_numbers(
        "营收为 5.2 亿美元",
        ["原文写明营收为 4.1 亿美元"],
    )
    assert fake.ok is False
    assert fake.reason_code == REASON_NUMERIC_MISMATCH
    assert fake.missing == ("5.2",)
    rewritten = check_verbatim_numbers("定价仍为 299 元", ["定价已改为 399 元"])
    assert rewritten.reason_code == REASON_NUMERIC_MISMATCH
    assert rewritten.missing == ("299",)
    missing = check_verbatim_numbers("定价仍为 299 元", ["原文未给价格"])
    assert missing.missing == ("299",)
    # 更长数字、千分位与小数位都不是容差。
    assert check_verbatim_numbers("299", ["看到 1299"]).ok is False
    assert check_verbatim_numbers("1,299", ["1299"]).ok is False
    assert check_verbatim_numbers("12.5", ["12.50"]).ok is False
    assert check_verbatim_numbers("15%", ["15"]).ok is False
    assert check_verbatim_numbers("变化 -3.2", ["变化 3.2"]).ok is False
    assert check_verbatim_numbers("增长 1 倍", ["T1 快照写增长 2 倍"]).missing == ("1",)


def test_match_fixture_fresh_is_not_refused_by_this_gate(tmp_path):
    """验收 1:数字逐字在 T1 span 中,本票不因此拒答。"""
    statement = "专业版定价仍为 299 元/席/月"
    span = "T1 原文确认专业版定价仍为 299 元/席/月。"
    result, runner, llm = _run(
        statement,
        span,
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", {
                "claim_id": CLAIM_ID,
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
        ],
        tmp_path,
    )
    recorded = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert "error" not in recorded
    assert recorded.get("reason_code") != REASON_NUMERIC_MISMATCH
    assert recorded["recorded"]["status"] == "fresh"
    assert result.claims[0].status == "fresh"
    assert result.decisions[CLAIM_ID].status == "fresh"
    trajectory = result.trajectory_path.read_text(encoding="utf-8")
    assert "numeric_mismatch" not in trajectory
    assert llm._script == []


def test_fake_quote_fixture_is_not_fresh_and_names_numeric_mismatch(tmp_path):
    """验收 2:假 quote / 数字不在证据中,结果不是 fresh,轨迹含 numeric_mismatch。"""
    result, runner, llm = _run(
        "专业版定价仍为 299 元/席/月",
        "T1 原文把专业版定价改写成 199 元/席/月。",
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(tool_calls=[_tc("reverify_claim", {
                "claim_id": CLAIM_ID,
                "status": "fresh",
                "evidence_ids": [EVIDENCE_ID],
            })]),
            _Msg(tool_calls=[_tc("finish_reverify", {})]),
            _Msg(content="数字对不上,不判 fresh"),
        ],
        tmp_path,
    )
    assert result.claims[0].status != "fresh"
    assert result.decisions[CLAIM_ID].status != "fresh"
    assert result.decisions[CLAIM_ID].status == "unknown"
    refused = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    assert "recorded" not in refused
    assert refused["reason_code"] == REASON_NUMERIC_MISMATCH
    assert refused["missing"] == ["299"]
    assert not any(event.get("type") == "critic_spawn" for event in runner.ctx.events)
    trajectory = result.trajectory_path.read_text(encoding="utf-8")
    assert '"reason_code": "numeric_mismatch"' in trajectory
    refusals = [
        event for event in runner.ctx.events
        if event.get("type") == "numeric_verbatim_refusal"
    ]
    assert len(refusals) == 1
    assert refusals[0]["reason_code"] == REASON_NUMERIC_MISMATCH
    end = [event for event in runner.ctx.events if event.get("type") == "lead_loop_end"][-1]
    assert end["reason_code"] == REASON_NUMERIC_MISMATCH
    assert llm._script == []
    assert llm.calls == 4


def test_context_registers_numeric_mismatch():
    """词表登记与代码常量是同一符号。"""
    text = (REPO / "docs" / "glossary.md").read_text(encoding="utf-8")
    assert "**numeric_mismatch**:" in text
    assert "**verbatim 数字闸**:" in text
    assert "`numeric_mismatch`" in text.split("**abstention reason**:", 1)[1].split("**", 1)[0]


def test_do_not_touch_prereg_golds_and_neural_rerank():
    """验收 3:PREREG、三份金标与 neural-rerank 不在 diff 里。"""
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
