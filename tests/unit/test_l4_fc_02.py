"""L4-FC-02: tools strict 探测。假端点,不调用付费接口。

默认端点结论是接受 strict(见 LLMClient.chat)。拒绝端点走声明分支,
请求不写 strict。dimension 仍由运行时再验整 call 拒绝。
"""

from __future__ import annotations

import inspect
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.llm import (
    DEFAULT_ENDPOINT_ACCEPTS_TOOLS_STRICT,
    LLMClient,
)
from freshlatch.models import LOCAL_EMBED_MODEL, MODEL_REGISTRY, Claim
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import RunContext
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE, InMemoryStore
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import RRF_K
from freshlatch.tools import (
    FOCUS_DIMENSIONS,
    REASON_ILLEGAL_DIMENSION,
    tool_specs,
)

REPO = Path(__file__).resolve().parents[2]
LLM_PY = REPO / "src" / "freshlatch" / "llm.py"

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


class _Msg:
    def __init__(self, content="ok"):
        self.content = content
        self.tool_calls = None


def _resp():
    return SimpleNamespace(
        usage=None,
        choices=[SimpleNamespace(message=_Msg())],
    )


def _client(create, *, accepts_tools_strict):
    llm = LLMClient(api_key="test-key", base_url="http://127.0.0.1:9")
    completions = SimpleNamespace(create=create)
    if accepts_tools_strict is not None:
        completions.accepts_tools_strict = accepts_tools_strict
    llm.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return llm


def test_accepting_fake_endpoint_payload_includes_strict():
    """验收 1: 假端点接受 strict 时,请求 payload 含该字段,且不改写 additionalProperties。"""
    seen: dict = {}

    def create(**kwargs):
        seen.update(kwargs)
        return _resp()

    specs = tool_specs(["retrieve", "mark_stale"])
    before = [dict(spec["function"]) for spec in specs]
    llm = _client(create, accepts_tools_strict=True)
    llm.chat([{"role": "user", "content": "probe"}], tools=specs)

    sent = seen["tools"]
    assert len(sent) == 2
    for original, tool in zip(specs, sent):
        function = tool["function"]
        assert function["strict"] is True
        assert function["parameters"]["additionalProperties"] is False
        assert "strict" not in original["function"]
        assert original["function"]["parameters"]["additionalProperties"] is False
    assert before[0]["parameters"]["required"] == specs[0]["function"]["parameters"]["required"]
    assert "source_type" not in specs[0]["function"]["parameters"]["required"]


def test_unmarked_client_follows_accepting_probe():
    """未标记的客户端按默认端点探测结论传 strict。"""
    assert DEFAULT_ENDPOINT_ACCEPTS_TOOLS_STRICT is True
    seen: dict = {}

    def create(**kwargs):
        seen.update(kwargs)
        return _resp()

    llm = _client(create, accepts_tools_strict=None)
    llm.chat([{"role": "user", "content": "probe"}], tools=tool_specs(["read_source"]))
    assert seen["tools"][0]["function"]["strict"] is True
    assert seen["tools"][0]["function"]["parameters"]["additionalProperties"] is False


def test_rejecting_endpoint_declaration_does_not_pretend_strict():
    """验收 2: 拒绝端点走声明分支。请求无 strict,注释写明仅运行时再验,非法 dimension 仍拒绝。"""
    seen: dict = {}

    def create(**kwargs):
        seen.update(kwargs)
        for tool in kwargs.get("tools") or []:
            function = tool.get("function") or {}
            if "strict" in function:
                raise AssertionError("声明分支不得把请求假装成已经 strict")
        return _resp()

    seeded = {
        "type": "function",
        "function": {
            "name": "ping",
            "description": "ping",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    }
    llm = _client(create, accepts_tools_strict=False)
    llm.chat([{"role": "user", "content": "probe"}], tools=[seeded, *tool_specs(["mark_stale"])])

    for tool in seen["tools"]:
        assert "strict" not in tool["function"]
        assert tool["function"]["parameters"]["additionalProperties"] is False
    assert seeded["function"]["strict"] is True

    doc = inspect.getdoc(LLMClient.chat)
    assert doc is not None
    assert "仅运行时再验" in doc
    assert "不假装已经 strict" in doc
    assert "这不是召回率,也不是通过率" in doc
    source = LLM_PY.read_text(encoding="utf-8")
    assert "counted_as_pass" not in source
    assert "langgraph" not in source

    claim = Claim(claim_id="c5", statement="专业版定价 299 元/席/月", dimension="cost_model")
    quiet = _QuietLLM()
    lead = LeadReverifier(RunContext(store=InMemoryStore()), claim, llm=quiet)
    lead._seen_evidence.add("t0-x#p2@T1")
    rejected = lead._t_mark_stale({
        "claim_id": "c5",
        "reason": "T1 原文写明专业版已经停售并退出报价单,原先仍在售卖的前提被推翻。",
        "evidence_ids": ["t0-x#p2@T1"],
        "dimension": "pricing",
    })
    assert rejected["reason_code"] == REASON_ILLEGAL_DIMENSION
    assert "error" in rejected
    for dim in FOCUS_DIMENSIONS:
        assert dim in rejected["error"]
    assert lead.decision.status == "unknown"
    assert lead.decision.stale_dimension is None
    assert quiet.calls == 0


class _QuietLLM:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        self.calls += 1
        raise AssertionError("业务再验不得调用模型")


def test_chat_without_tools_does_not_add_tools():
    seen: dict = {}

    def create(**kwargs):
        seen.update(kwargs)
        return _resp()

    llm = _client(create, accepts_tools_strict=True)
    llm.chat([{"role": "user", "content": "plain"}])
    assert "tools" not in seen


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
