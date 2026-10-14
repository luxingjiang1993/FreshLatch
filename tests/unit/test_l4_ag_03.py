"""L4-AG-03: 失败轨迹 JSONL 可确定性复放。

夹具是脚本化假 LLM 与 Runner,不调用付费接口。
人审图 latch/pipeline.py 不在本票改动范围内。
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.loop import (
    ABSTENTION_REASONS,
    VERIFY_ABSTAIN_TOOL,
    VERIFY_REPAIR_TOOL,
)
from freshlatch.roles.retrieve_grade import REASON_GRADE_INCORRECT_EXHAUSTED
from freshlatch.roles.retrieve_sufficiency import REASON_INSUFFICIENT_EVIDENCE
from freshlatch.runner import Runner, parse_failure_replay
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE, Chunk, InMemoryStore
from freshlatch.tools import REASON_UNKNOWN_TOOL

REPO = Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO / "src/freshlatch/runner.py"
LOOP_PATH = REPO / "src/freshlatch/roles/loop.py"
LATCH_PATH = REPO / "src/freshlatch/latch/pipeline.py"
EVIDENCE_ID = "fix-memo#p1@T1"
CLAIM_FINAL_KEYS = frozenset({
    "type",
    "claim_id",
    "statement",
    "status",
    "reason",
    "evidence_ids",
    "auditor_verdict",
    "dissent",
    "schema_version",
})

_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_ag03_{_tc_counter}",
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
    """按构造时给定的块返回。空列表即检索空。不走嵌入,不打网。"""

    def __init__(self, hits: list[Chunk]) -> None:
        super().__init__()
        self._hits = list(hits)
        self.retrieve_calls = 0

    def retrieve(self, query, *, as_of=None, source_type=None, top_k=10, tenant_id=None):
        self.retrieve_calls += 1
        self.last_retrieval_mode = "bm25"
        self.last_rerank_mode = "none"
        return list(self._hits)


def _chunk(grade: str) -> Chunk:
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
    chunk.crag_grade = grade  # type: ignore[attr-defined]
    return chunk


def _claim() -> Claim:
    return Claim(
        claim_id="c-ag03",
        statement="专业版定价仍为 299 元/席/月",
        t0_evidence_ids=["fix-memo#p1"],
        dimension="competitor_pricing",
    )


def _fail_script() -> list[_Msg]:
    return [
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {
            "claim_id": "c-ag03",
            "status": "fresh",
            "evidence_ids": [EVIDENCE_ID],
        })]),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="不写 fresh"),
    ]


def _run(store: _FixtureStore, tmp_path: Path):
    llm = _ScriptLLM(_fail_script())
    runner = Runner(store, llm=llm, guardrails=Guardrails())
    result = runner.run([_claim()], trajectory_dir=tmp_path)
    assert llm._script == []
    assert result.trajectory_path is not None
    return result


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _claim_replay(path: Path) -> dict:
    replay = parse_failure_replay(path)
    assert replay["path"] == str(path)
    assert len(replay["claims"]) == 1
    again = parse_failure_replay(path)
    assert again == replay
    return replay["claims"][0]


def test_empty_retrieve_jsonl_replays_abstention_fields(tmp_path):
    """验收 1:检索空失败后,从落盘 JSONL 读回工具步与拒答字段。"""
    result = _run(_FixtureStore([]), tmp_path)
    assert result.claims[0].status != "fresh"
    path = result.trajectory_path
    rows = _rows(path)
    end = [row for row in rows if row.get("type") == "lead_loop_end"][-1]
    assert end["evidence_ids"] == []
    assert end["grade"] == "incorrect"
    assert end["retry_count"] == 0
    assert end["reason_code"] == REASON_INSUFFICIENT_EVIDENCE
    final = [row for row in rows if row.get("type") == "claim_final"][-1]
    assert set(final) == CLAIM_FINAL_KEYS
    assert "grade" not in final
    assert "retry_count" not in final
    assert "reason_code" not in final

    claim = _claim_replay(path)
    assert claim["evidence_ids"] == []
    assert claim["grade"] == "incorrect"
    assert claim["retry_count"] == 0
    assert claim["reason_code"] == REASON_INSUFFICIENT_EVIDENCE
    assert claim["reason_code"] in ABSTENTION_REASONS
    tools = [step["tool"] for step in claim["tool_steps"]]
    assert "retrieve" in tools
    assert VERIFY_REPAIR_TOOL not in tools
    assert "web_search" not in tools
    raw = path.read_text(encoding="utf-8")
    assert '"reason_code": "insufficient_evidence"' in raw
    assert "langgraph" not in raw


def test_grade_insufficient_jsonl_replays_retry_and_evidence(tmp_path):
    """验收 1 的另一失败:grade 不足时读回 evidence_ids、grade、retry_count、reason code。"""
    result = _run(_FixtureStore([_chunk("incorrect")]), tmp_path)
    assert result.claims[0].status != "fresh"
    path = result.trajectory_path
    claim = _claim_replay(path)
    assert claim["evidence_ids"] == [EVIDENCE_ID]
    assert claim["grade"] == "incorrect"
    assert claim["retry_count"] == 1
    assert claim["reason_code"] == REASON_GRADE_INCORRECT_EXHAUSTED
    assert claim["reason_code"] in ABSTENTION_REASONS
    tools = [step["tool"] for step in claim["tool_steps"]]
    assert tools[0] == "retrieve"
    assert VERIFY_REPAIR_TOOL in tools
    assert VERIFY_ABSTAIN_TOOL in tools
    abstain = [step for step in claim["tool_steps"] if step["tool"] == VERIFY_ABSTAIN_TOOL][-1]
    assert abstain["evidence_ids"] == [EVIDENCE_ID]
    assert abstain["grade"] == "incorrect"
    assert abstain["retry_count"] == 1
    assert abstain["reason_code"] == REASON_GRADE_INCORRECT_EXHAUSTED
    raw = path.read_text(encoding="utf-8")
    assert '"reason_code": "grade_incorrect_exhausted"' in raw
    assert "web_search" not in raw


def test_hygiene_reason_is_not_replayed_as_abstention(tmp_path):
    """unknown_tool 不是 abstention reason,复放不把它当成拒答码。"""
    path = tmp_path / "hygiene.jsonl"
    path.write_text(
        "\n".join([
            json.dumps({
                "type": "lead_step",
                "claim_id": "c-hygiene",
                "step": 1,
                "tool": "not_a_tool",
                "reason_code": REASON_UNKNOWN_TOOL,
            }, ensure_ascii=False),
            json.dumps({
                "type": "lead_loop_end",
                "claim_id": "c-hygiene",
                "evidence_ids": [],
                "grade": None,
                "retry_count": 0,
                "reason_code": REASON_UNKNOWN_TOOL,
            }, ensure_ascii=False),
        ]) + "\n",
        encoding="utf-8",
    )
    claim = _claim_replay(path)
    assert claim["reason_code"] is None
    assert "reason_code" not in claim["tool_steps"][0]
    assert claim["tool_steps"][0]["tool"] == "not_a_tool"
    assert REASON_UNKNOWN_TOOL not in ABSTENTION_REASONS


def test_dump_does_not_add_replay_event_or_langgraph():
    """复放不另造事件类型,run_loop 所在模块与 runner 都不引进 langgraph。"""
    runner_text = RUNNER_PATH.read_text(encoding="utf-8")
    loop_text = LOOP_PATH.read_text(encoding="utf-8")
    assert '"type": "failure_replay"' not in runner_text
    assert "time_travel" not in runner_text
    assert "disputed" not in runner_text
    for path, text in ((RUNNER_PATH, runner_text), (LOOP_PATH, loop_text)):
        tree = ast.parse(text)
        modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
        assert modules, path.name
        assert not any("langgraph" in name for name in modules)
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert "disputed" not in LATCH_PATH.read_text(encoding="utf-8")


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


def test_latch_pipeline_human_review_unchanged():
    """验收 2:人审图职责不变。缺 base 时 skip,不把浅克隆当成失败。"""
    base = _git_base_ref()
    if base is None:
        pytest.skip("origin/main 缺失,跳过 latch/pipeline.py diff")
    diff = subprocess.run(
        ["git", "diff", "--exit-code", base, "--", "src/freshlatch/latch/pipeline.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if diff.returncode not in (0, 1):
        pytest.skip(
            "无法对 base 做 git diff,跳过人审图检查: " + (diff.stderr or "").strip()
        )
    assert diff.stdout.strip() == ""
    assert diff.returncode == 0
