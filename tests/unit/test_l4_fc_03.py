"""L4-FC-03: tool_tier 读、需批、禁。

脚本化假 LLM 与直接调度,不调用付费接口。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.gates.human_latch import DecisionResult
from freshlatch.latch import (
    HumanLatch,
    HumanLatchError,
    ToolReviewGrant,
    human_review_allows_tool,
)
from freshlatch.models import LOCAL_EMBED_MODEL, NEURAL_RERANK_MODEL, Claim
from freshlatch.roles.loop import ILLEGAL_CALL_REPAIR_BUDGET, run_loop
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import RRF_K
from freshlatch.tools import (
    AUDITOR_TOOLS,
    CRITIC_TOOLS,
    FIXTURE_TOOL_TIER_2,
    FORENSIC_TOOLS,
    LEAD_TOOLS_W1,
    LEAD_TOOLS_W3,
    LEAD_TOOLS_W9,
    REASON_ILLEGAL_DIMENSION,
    REASON_ILLEGAL_TOOL_ARGS,
    REASON_TOOL_TIER_DENIED,
    REASON_UNKNOWN_TOOL,
    TOOL_TIER_0,
    TOOL_TIER_1,
    TOOL_TIER_2,
    TOOL_TIERS,
    _TOOL_DEFS,
    dispatch_tiered_tool,
    tool_specs,
    tool_tier_of,
)

REPO = Path(__file__).resolve().parents[2]

_DO_NOT_TOUCH = (
    "src/freshlatch/eval/quality_gate.py",
    "src/freshlatch/gates/rule_gate.py",
    "src/freshlatch/roles/loop.py",
    "src/freshlatch/roles/lead.py",
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

# 规则闸文首。本票只核对,不改写人审出口那一句。
_RULE_GATE_PREAMBLE = "\n".join((
    '"""规则闸:绿灯唯一出口。纯函数、零 I/O(名单/checksum 由调用方注入,ADR-0001)。',
    "",
    "口径(§1.3):「Agent 不得把红灯改回绿灯」只约束 Agent 侧工具链;",
    "人审(L0)是合法出口,由 gates/human_latch.py(W3 起)调本闸实现,此口径写在此(ADR-0006 §4)。",
))

_WHITELISTS = (
    LEAD_TOOLS_W1,
    LEAD_TOOLS_W3,
    LEAD_TOOLS_W9,
    CRITIC_TOOLS,
    AUDITOR_TOOLS,
    FORENSIC_TOOLS,
)

_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_fc03_{_tc_counter}",
        type="function",
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(args, ensure_ascii=False),
        ),
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

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        if not self._script:
            raise AssertionError("脚本已尽,测试不得再调用 LLM")
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


def _run(script, *, execute, tools):
    llm = _ScriptLLM(script)

    def chat(messages, tools=None):
        return llm.chat(messages, tools=tools)

    return run_loop(
        system="s",
        task="t",
        tools=tools,
        execute=execute,
        chat=chat,
        max_steps=4,
        soft_close="预算已尽,基于现有证据下结论。",
    )


def _boom(_args):
    raise AssertionError("未放行或禁档不得执行工具")


def _fixture_blocks():
    return {"blocks": [{"evidence_id": "memo#p1@T1", "text": "夹具原文"}]}


def _tier2_spec():
    return {
        "type": "function",
        "function": {
            "name": FIXTURE_TOOL_TIER_2,
            "description": "夹具:禁动生产臂",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    }


def test_tool_tier_0_retrieve_and_read_source_without_approval():
    """验收 1: 读工具无批成功,返回夹具。"""
    trajectory = []
    retrieve = dispatch_tiered_tool(
        "retrieve",
        {"query": "定价", "as_of": "T1"},
        lambda args: _fixture_blocks(),
        trajectory=trajectory,
    )
    source = dispatch_tiered_tool(
        "read_source",
        {"doc_id": "memo", "as_of": "T1"},
        lambda args: {"doc_id": args["doc_id"], "full_text": "夹具全文"},
        trajectory=trajectory,
    )
    assert retrieve == _fixture_blocks()
    assert source["full_text"] == "夹具全文"
    assert [row["tool_tier"] for row in trajectory] == [TOOL_TIER_0, TOOL_TIER_0]
    assert all(row["ok"] for row in trajectory)
    assert tool_tier_of("retrieve") == TOOL_TIER_0
    assert tool_tier_of("read_source") == TOOL_TIER_0


def test_model_calls_retrieve_without_approval():
    """验收 1 的模型侧:脚本化调用进入调度后仍返回夹具。"""
    trajectory = []

    def execute(name, args):
        return dispatch_tiered_tool(
            name, args, lambda _args: _fixture_blocks(), trajectory=trajectory,
        )

    result = _run(
        [
            _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
            _Msg(content="读完"),
        ],
        execute=execute,
        tools=tool_specs(["retrieve", "read_source"]),
    )
    assert result.failed is False
    assert result.tool_trace[0]["result"] == _fixture_blocks()
    assert trajectory[0]["tool_tier"] == TOOL_TIER_0
    assert trajectory[0]["ok"] is True


def test_tool_tier_1_without_approval_records_denial():
    """验收 2: 写观测无批拒绝,reason 可枚举,轨迹留观察,handler 不跑。"""
    trajectory = []
    out = dispatch_tiered_tool(
        "mark_stale",
        {
            "claim_id": "c1",
            "reason": "T1 原文推翻仍在售的前提",
            "evidence_ids": ["memo#p1@T1"],
            "dimension": "competitor_pricing",
        },
        _boom,
        approval=None,
        trajectory=trajectory,
    )
    assert out["reason_code"] == REASON_TOOL_TIER_DENIED == "tool_tier_denied"
    assert out["tool_tier"] == TOOL_TIER_1
    assert out["ok"] is False
    assert trajectory == [out]
    assert "error" in out


def test_model_mark_stale_without_approval_does_not_run_handler():
    """验收 2 的模型侧:schema 合法的写观测仍被档位拒绝,且不占用非法调用预算。"""
    trajectory = []

    def execute(name, args):
        return dispatch_tiered_tool(name, args, _boom, trajectory=trajectory)

    result = _run(
        [
            _Msg(tool_calls=[_tc("mark_stale", {
                "claim_id": "c1",
                "reason": "T1 原文推翻仍在售的前提",
                "evidence_ids": ["memo#p1@T1"],
                "dimension": "competitor_pricing",
            })]),
            _Msg(content="被拒后收尾"),
        ],
        execute=execute,
        tools=tool_specs(["mark_stale"]),
    )
    assert result.failed is False
    assert result.illegal_repairs == 0
    assert result.illegal_repairs <= ILLEGAL_CALL_REPAIR_BUDGET
    assert result.tool_trace[0]["result"]["reason_code"] == REASON_TOOL_TIER_DENIED
    assert trajectory[0]["type"] == "tool_tier_observation"
    assert TOOL_TIERS["reverify_claim"] == TOOL_TIER_1
    assert TOOL_TIERS["mark_gap"] == TOOL_TIER_1


def test_bare_approval_and_human_decision_do_not_pass():
    """作废/续命决定行和裸真值都不是写观测放行。"""
    decision = DecisionResult("c1", ok=True, action="discard")
    assert human_review_allows_tool(True, "mark_stale") is False
    assert human_review_allows_tool({"ok": True, "action": "renew"}, "mark_stale") is False
    assert human_review_allows_tool(decision, "reverify_claim") is False
    out = dispatch_tiered_tool("reverify_claim", {"status": "unknown"}, _boom, approval=decision)
    assert out["reason_code"] == REASON_TOOL_TIER_DENIED


def test_tool_tier_1_runs_only_with_latch_grant(tmp_path):
    """人审待审轮次签发的放行才能执行对应写观测工具。"""
    latch = HumanLatch(object(), tmp_path / "cp.db", mode="online")
    claim = Claim(claim_id="c1", statement="竞品仍更贵", status="stale", reason="待审")
    waiting = latch.enter_round([claim], ts="20261014-120000")
    assert waiting.waiting
    grant = latch.approve_write_tool("mark_stale", claim_id="c1")
    assert human_review_allows_tool(grant, "mark_stale") is True
    assert human_review_allows_tool(grant, "reverify_claim") is False
    seen = []
    out = dispatch_tiered_tool(
        "mark_stale",
        {"claim_id": "c1"},
        lambda args: seen.append(args) or {"recorded": True},
        approval=grant,
    )
    assert seen == [{"claim_id": "c1"}]
    assert out == {"recorded": True}
    denied = dispatch_tiered_tool(
        "reverify_claim", {"status": "unknown"}, _boom, approval=grant,
    )
    assert denied["reason_code"] == REASON_TOOL_TIER_DENIED


def test_grant_cannot_be_forged_and_eval_skips(tmp_path):
    with pytest.raises(HumanLatchError):
        ToolReviewGrant("mark_stale", "c1")
    latch = HumanLatch(object(), tmp_path / "cp-online.db", mode="online")
    with pytest.raises(HumanLatchError):
        latch.approve_write_tool("mark_gap", claim_id="c1")
    claim = Claim(claim_id="c1", statement="竞品仍更贵", status="stale", reason="待审")
    assert latch.enter_round([claim], ts="20261014-120001").waiting
    with pytest.raises(HumanLatchError):
        latch.approve_write_tool(FIXTURE_TOOL_TIER_2, claim_id="c1")
    with pytest.raises(HumanLatchError):
        latch.approve_write_tool("retrieve", claim_id="c1")
    skipped = HumanLatch(object(), tmp_path / "cp-skip.db", mode="eval")
    with pytest.raises(HumanLatchError):
        skipped.approve_write_tool("mark_gap", claim_id="c1")


def test_tool_tier_2_model_call_fail_closed_and_not_on_w3():
    """验收 3: 夹具生产臂不在默认 Lead 白名单;模型调用 fail-closed。"""
    assert FIXTURE_TOOL_TIER_2 not in LEAD_TOOLS_W3
    assert FIXTURE_TOOL_TIER_2 not in _TOOL_DEFS
    assert tool_tier_of(FIXTURE_TOOL_TIER_2) == TOOL_TIER_2
    assert tool_tier_of("spawn_auditor") == TOOL_TIER_2
    assert "spawn_auditor" not in LEAD_TOOLS_W3
    trajectory = []

    def execute(name, args):
        return dispatch_tiered_tool(
            name, args, _boom, approval=True, trajectory=trajectory,
        )

    result = _run(
        [
            _Msg(tool_calls=[_tc(FIXTURE_TOOL_TIER_2, {})]),
            _Msg(content="禁档后收尾"),
        ],
        execute=execute,
        tools=[_tier2_spec()],
    )
    assert result.failed is False
    observed = result.tool_trace[0]["result"]
    assert observed["reason_code"] == REASON_TOOL_TIER_DENIED
    assert observed["fail_closed"] is True
    assert observed["tool_tier"] == TOOL_TIER_2
    assert trajectory == [observed]
    banned = dispatch_tiered_tool("spawn_auditor", {"claim_id": "c1"}, _boom)
    assert banned["fail_closed"] is True
    assert banned["reason_code"] == REASON_TOOL_TIER_DENIED


def test_permission_tier_names_and_rule_gate_preamble():
    """验收 4: 档名是 tool_tier_*;规则闸文首人审语义保持原句。"""
    tools_src = (REPO / "src/freshlatch/tools.py").read_text(encoding="utf-8")
    latch_src = (REPO / "src/freshlatch/latch/pipeline.py").read_text(encoding="utf-8")
    for src in (tools_src, latch_src):
        code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())
        assert "L0" not in code
    assert TOOL_TIER_0 == "tool_tier_0"
    assert TOOL_TIER_1 == "tool_tier_1"
    assert TOOL_TIER_2 == "tool_tier_2"
    gate = (REPO / "src/freshlatch/gates/rule_gate.py").read_text(encoding="utf-8")
    assert "\n".join(gate.splitlines()[:4]) == _RULE_GATE_PREAMBLE
    context = (REPO / "CONTEXT.md").read_text(encoding="utf-8")
    for name in (TOOL_TIER_0, TOOL_TIER_1, TOOL_TIER_2):
        assert f"**{name}**:" in context
    block = context.split("**tool_tier_0**:", 1)[1].split("**CRAG grade", 1)[0]
    assert block.count("人审 L0") == 3
    assert "tool_tier_denied" in block


def test_w9_not_runner_default_and_web_search_unlisted():
    """验收 5: W9 不是 Runner 默认挂载;web_search 不在任何白名单。"""
    lead = (REPO / "src/freshlatch/roles/lead.py").read_text(encoding="utf-8")
    runner = (REPO / "src/freshlatch/runner.py").read_text(encoding="utf-8")
    assert "LEAD_TOOLS_W3" in lead
    assert "tool_specs(list(LEAD_TOOLS_W3))" in lead
    assert "LEAD_TOOLS_W9" not in lead
    assert "LEAD_TOOLS_W9" not in runner
    mounted = {name for whitelist in _WHITELISTS for name in whitelist}
    assert "web_search" not in mounted
    assert "web_search" not in _TOOL_DEFS
    assert FIXTURE_TOOL_TIER_2 not in mounted
    for name in LEAD_TOOLS_W3:
        assert TOOL_TIERS[name] != TOOL_TIER_2


def test_fc01_reason_codes_unchanged():
    """不放宽非法调用拒因。"""
    assert REASON_UNKNOWN_TOOL == "unknown_tool"
    assert REASON_ILLEGAL_TOOL_ARGS == "illegal_tool_args"
    assert REASON_ILLEGAL_DIMENSION == "illegal_dimension"
    loop = (REPO / "src/freshlatch/roles/loop.py").read_text(encoding="utf-8")
    assert "ILLEGAL_CALL_REPAIR_BUDGET = 2" in loop
    assert ILLEGAL_CALL_REPAIR_BUDGET == 2


def test_frozen_retrieval_pins():
    """检索常量不依赖 git,浅克隆也必须跑。"""
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert RRF_K == 60
    assert NEURAL_RERANK_K == 10
    assert LOCAL_EMBED_MODEL == "BAAI/bge-small-zh-v1.5"
    assert NEURAL_RERANK_MODEL == "BAAI/bge-reranker-base"
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in (
        REPO / "src/freshlatch/store/base.py"
    ).read_text(encoding="utf-8")
    assert "RRF_K = 60" in (REPO / "src/freshlatch/store/pipeline.py").read_text(encoding="utf-8")
    assert "NEURAL_RERANK_K = 10" in (
        REPO / "src/freshlatch/store/neural_rerank.py"
    ).read_text(encoding="utf-8")
    assert "fastembed==0.8.1" in (REPO / "pyproject.toml").read_text(encoding="utf-8")


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
    """有 base 时 Do-not-touch 路径不在 diff 里。缺少 base 时 skip。"""
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


def test_diff_new_identifiers_use_tool_tier_names():
    """验收 4 的 diff 半边:新增行里的权限档名是 tool_tier_*。"""
    base = _git_base_ref()
    if base is None:
        pytest.skip("origin/main 缺失,跳过新增标识符 diff 检查")
    diff = subprocess.run(
        [
            "git", "diff", "-U0", base, "--",
            "src/freshlatch/tools.py",
            "src/freshlatch/latch/pipeline.py",
            "src/freshlatch/latch/__init__.py",
            "CONTEXT.md",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        pytest.skip(
            "无法对 base 做 git diff,跳过新增标识符检查: "
            + (diff.stderr or "").strip()
        )
    added = [
        line[1:]
        for line in diff.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    assert any("tool_tier_0" in line for line in added)
    assert any("tool_tier_1" in line for line in added)
    assert any("tool_tier_2" in line for line in added)
    bare = re.compile(r'(?<![A-Za-z0-9_])L0(?![A-Za-z0-9_])')
    for line in added:
        if not bare.search(line):
            continue
        assert "人审 L0" in line
        assert '"L0"' not in line
        assert "'L0'" not in line
