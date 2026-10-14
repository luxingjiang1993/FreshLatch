"""L4-FC-CITE:claim 引用必须落在本轮 TurnRegistry。夹具确定性,不调用付费 LLM。"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.evidence import (
    CITE_OUTSIDE_REGISTRY,
    TurnRegistry,
    check_evidence_ids,
    registry_refusal_code,
)
from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.runner import Runner
from freshlatch.store.base import (
    PRODUCTION_RETRIEVAL_MODE,
    Chunk,
    Document,
    InMemoryStore,
)
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import RRF_K

REPO = Path(__file__).resolve().parents[2]
CLAIM_ID = "c-cite"
CITED_ID = "fix-memo#p1@T1"
OTHER_ID = "fix-memo#p2@T1"
OUTSIDE_ID = "ghost-doc#p9@T1"
T0_ID = "fix-memo#p1@T0"
STALE_REASON = "T1 原文写明专业版已经停售并退出报价单,原先仍在售卖的前提被推翻。"

_DO_NOT_TOUCH = (
    "src/freshlatch/eval/quality_gate.py",
    "src/freshlatch/store/base.py",
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
        id=f"call_cite_{_tc_counter}",
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

    def retrieve(self, query, *, as_of=None, source_type=None, top_k=10, tenant_id=None,
                 patch_id=None, valid_at=None):
        self.retrieve_calls += 1
        self.last_retrieval_mode = "bm25"
        self.last_rerank_mode = "none"
        return list(self._hits)


def _chunk(clause_id: str) -> Chunk:
    return Chunk(
        doc_id="fix-memo",
        chunk_id=f"fix-memo-{clause_id}",
        clause_id=clause_id,
        title="备忘",
        # 主张含 299。span 里逐字带上同一数字,引用成功才不会被数字闸拒掉。
        text=f"T1 原文确认条款 {clause_id} 定价仍为 299,仍可点回。",
        source_type="public",
        as_of="T1",
        doc_version="v1",
        checksum="",
        tokens=12,
    )


def _claim() -> Claim:
    return Claim(
        claim_id=CLAIM_ID,
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


def _events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _store_with_registry() -> _FixtureStore:
    cited = _chunk("p1")
    other = _chunk("p2")
    store = _FixtureStore([cited, other])
    store.add_document(
        Document(
            doc_id="fix-memo",
            as_of="T1",
            source_type="public",
            title="备忘",
            doc_version="v1",
            checksum="",
            full_text=cited.text + "\n" + other.text,
        ),
        [cited, other],
    )
    return store


def test_cite_outside_registry_rejected(tmp_path):
    """验收 1:S 之外的 id 被拒,reason 为 cite_outside_registry,不产生 fresh。"""
    registry = TurnRegistry([CITED_ID, OTHER_ID])
    ids, err = check_evidence_ids([OUTSIDE_ID], registry, require_t1=True)
    assert ids is None
    assert registry_refusal_code(err) == CITE_OUTSIDE_REGISTRY
    assert CITE_OUTSIDE_REGISTRY == "cite_outside_registry"
    assert err is not None and "未检索到" in err
    t0_registry = TurnRegistry([T0_ID])
    _, t0_err = check_evidence_ids([T0_ID], t0_registry, require_t1=True)
    assert registry_refusal_code(t0_err) is None
    _, empty_err = check_evidence_ids([], registry, require_t1=True)
    assert registry_refusal_code(empty_err) is None

    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": CLAIM_ID,
            "status": "fresh",
            "evidence_ids": [OUTSIDE_ID],
        })]),
        _Msg(tool_calls=[_tc("mark_stale", {
            "claim_id": CLAIM_ID,
            "reason": STALE_REASON,
            "evidence_ids": [OUTSIDE_ID],
            "dimension": "competitor_pricing",
        })]),
        _Msg(content="registry 外的 id 不能落判定"),
    ])
    runner = Runner(_store_with_registry(), llm=llm, guardrails=Guardrails())
    result = runner.run([_claim()], trajectory_dir=tmp_path)

    seen = {block["evidence_id"] for block in _lead_tool_results(runner.ctx.events, "retrieve")[0]["blocks"]}
    assert seen == {CITED_ID, OTHER_ID}
    assert OUTSIDE_ID not in seen
    fresh_out = _lead_tool_results(runner.ctx.events, "reverify_claim")[0]
    stale_out = _lead_tool_results(runner.ctx.events, "mark_stale")[0]
    assert fresh_out["reason_code"] == CITE_OUTSIDE_REGISTRY
    assert stale_out["reason_code"] == CITE_OUTSIDE_REGISTRY
    assert CITE_OUTSIDE_REGISTRY in fresh_out["error"]
    assert CITE_OUTSIDE_REGISTRY in stale_out["error"]
    assert "recorded" not in fresh_out
    assert "recorded" not in stale_out
    assert result.claims[0].status != "fresh"
    assert result.decisions[CLAIM_ID].status != "fresh"
    assert result.decisions[CLAIM_ID].status != "stale"
    events = _events(result.trajectory_path)
    refusals = [event for event in events if event.get("type") == "cite_registry_refusal"]
    assert [event["reason_code"] for event in refusals] == [
        CITE_OUTSIDE_REGISTRY,
        CITE_OUTSIDE_REGISTRY,
    ]
    assert [event["tool"] for event in refusals] == ["reverify_claim", "mark_stale"]
    assert not any(event.get("type") == "cite_registry_judgment" for event in events)
    assert llm._script == []


def test_cite_subset_ok(tmp_path):
    """验收 2–3:S 的 @T1 子集不额外拒绝,成功判定的轨迹带所用 evidence_id。"""
    registry = TurnRegistry([CITED_ID, OTHER_ID])
    ids, err = check_evidence_ids([CITED_ID], registry, require_t1=True)
    assert err is None
    assert ids == [CITED_ID]
    assert isinstance(registry, TurnRegistry)

    fresh_llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": CLAIM_ID,
            "status": "fresh",
            "evidence_ids": [CITED_ID],
        })]),
        _Msg(tool_calls=[_tc("report_finding", {
            "finding": "按不限方向检索后未见推翻性 T1 证据",
        })]),
        _Msg(content="无反证"),
        _aud({"status": "fresh", "reason": "T1 原文直接支持该定价", "dimension_match": True}),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    fresh_dir = tmp_path / "fresh"
    fresh_dir.mkdir()
    fresh_runner = Runner(_store_with_registry(), llm=fresh_llm, guardrails=Guardrails())
    fresh_result = fresh_runner.run([_claim()], trajectory_dir=fresh_dir)
    fresh_seen = {
        block["evidence_id"]
        for block in _lead_tool_results(fresh_runner.ctx.events, "retrieve")[0]["blocks"]
    }
    assert {CITED_ID, OTHER_ID} <= fresh_seen
    recorded = _lead_tool_results(fresh_runner.ctx.events, "reverify_claim")[0]
    assert "error" not in recorded
    assert "reason_code" not in recorded
    assert recorded["recorded"]["status"] == "fresh"
    assert recorded["recorded"]["evidence_ids"] == [CITED_ID]
    assert fresh_result.claims[0].status == "fresh"
    fresh_events = _events(fresh_result.trajectory_path)
    judgments = [event for event in fresh_events if event.get("type") == "cite_registry_judgment"]
    assert judgments == [{
        "type": "cite_registry_judgment",
        "claim_id": CLAIM_ID,
        "status": "fresh",
        "evidence_ids": [CITED_ID],
    }]
    assert fresh_llm._script == []

    stale_llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("mark_stale", {
            "claim_id": CLAIM_ID,
            "reason": STALE_REASON,
            "evidence_ids": [CITED_ID],
            "dimension": "competitor_pricing",
        })]),
        _aud({"status": "stale", "reason": "T1 原文推翻仍在售的前提", "dimension_match": True}),
        _Msg(content="复验结束"),
    ])
    stale_dir = tmp_path / "stale"
    stale_dir.mkdir()
    stale_runner = Runner(_store_with_registry(), llm=stale_llm, guardrails=Guardrails())
    stale_result = stale_runner.run([_claim()], trajectory_dir=stale_dir)
    stale_out = _lead_tool_results(stale_runner.ctx.events, "mark_stale")[0]
    assert "error" not in stale_out
    assert "reason_code" not in stale_out
    assert stale_out["recorded"]["status"] == "stale"
    assert stale_out["recorded"]["evidence_ids"] == [CITED_ID]
    stale_events = _events(stale_result.trajectory_path)
    stale_judgments = [
        event for event in stale_events if event.get("type") == "cite_registry_judgment"
    ]
    assert stale_judgments == [{
        "type": "cite_registry_judgment",
        "claim_id": CLAIM_ID,
        "status": "stale",
        "evidence_ids": [CITED_ID],
    }]
    assert stale_llm._script == []


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


def test_frozen_retrieval_pins():
    """检索常量不依赖 git,浅克隆也必须跑。"""
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert RRF_K == 60
    assert NEURAL_RERANK_K == 10


def test_do_not_touch_paths_skip_when_base_missing():
    """验收 4:有 base 时 Do-not-touch 与 score_citation_overlap 所在文件不在 diff 里。

    缺少 base ref 时 skip,避免 git diff 以 128 失败。
    """
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
    overlap = subprocess.run(
        [
            "git", "diff", "--name-only", base, "--",
            "src/freshlatch/eval/quality_gate.py",
            "data/eval/cite_sentence.json",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if overlap.returncode != 0:
        pytest.skip(
            "无法对 base 做 git diff,跳过 citation 文件检查: "
            + (overlap.stderr or "").strip()
        )
    assert overlap.stdout.strip() == ""
