"""DEM-4 步数/retrieve 预算进度可见性(α-demo):复验单 UI seam。

挂既有 UI harness(TestClient + 源码/DOM 断言);不开第四类 harness。
本票为 α-demo:可见性 ≠ UX 证明了 latch / 产品已验证 / 一期测量闭合。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.guardrails import Guardrails
from freshlatch.llm import DecodingParams
from freshlatch.models import Claim
from freshlatch.runner import RunContext, RunResult
from freshlatch.store.base import InMemoryStore


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    appmod._state.update({
        "claims": [],
        "question": "",
        "trajectory": None,
        "running": False,
        "latch": dict(appmod.EMPTY_LATCH),
        "budget": dict(appmod.EMPTY_BUDGET),
        "run_ctx": None,
        "retrieve_zero_hits": [],
    })
    appmod._reset_t1_source(store)
    return TestClient(appmod.app)


def test_html_budget_progress_markers_present():
    """DEM-4:进度条(或等价)占位 + 用量字段名与 Guardrails 对齐。"""
    assert 'id="budget-progress"' in appmod.HTML_PAGE
    for token in ("steps_used", "lead_max_steps", "retrieval_used", "retrieval_budget"):
        assert token in appmod.HTML_PAGE
    assert "renderBudget" in appmod.HTML_PAGE


def test_html_polls_budget_during_reverify():
    """复验中轮询 /api/claims 刷新预算(同步 reverify 跑在线程池,可并行读)。"""
    assert "pollBudget" in appmod.HTML_PAGE
    assert "setInterval(pollBudget" in appmod.HTML_PAGE
    assert "clearInterval(budgetPoll)" in appmod.HTML_PAGE


def test_api_claims_includes_budget_defaults(client):
    """会话态暴露预算字段,默认与 Guardrails 默认天花板对齐。"""
    j = client.get("/api/claims").json()
    assert "budget" in j
    b = j["budget"]
    g = Guardrails()
    assert b["steps_used"] == 0
    assert b["retrieval_used"] == 0
    assert b["lead_max_steps"] == g.lead_max_steps
    assert b["retrieval_budget"] == g.retrieval_budget


def test_api_claims_reads_live_run_ctx_while_running(client):
    """复验中 /api/claims 读 RunContext 实时计数(与 Guardrails 对齐写入)。"""
    ctx = RunContext(
        store=InMemoryStore(),
        guardrails=Guardrails(lead_max_steps=18, retrieval_budget=24),
    )
    ctx.lead_steps_used = 7
    ctx.retrieval_used = 3
    appmod._state["running"] = True
    appmod._state["run_ctx"] = ctx
    j = client.get("/api/claims").json()
    assert j["running"] is True
    assert j["budget"] == {
        "steps_used": 7,
        "lead_max_steps": 18,
        "retrieval_used": 3,
        "retrieval_budget": 24,
    }


def test_reverify_keeps_budget_summary_after_complete(client, monkeypatch):
    """完成后会话内仍可读用量摘要(不丢进度)。"""
    # T1 三卡硬条件:未选定不得开复验
    assert client.post("/api/t1-source/synthetic").status_code == 200
    appmod._state["claims"] = [
        Claim(claim_id="c1", statement="demo", status="unknown"),
    ]

    class _FakeRunner:
        def __init__(self, store, **_kwargs):
            self.ctx = RunContext(
                store=store,
                guardrails=Guardrails(lead_max_steps=18, retrieval_budget=24),
            )

        def run(self, claims, **kwargs):
            self.ctx.lead_steps_used = 5
            self.ctx.retrieval_used = 9
            return RunResult(
                claims=list(claims),
                decisions={},
                trajectory_path=None,
                steps_by_claim={"c1": 5},
                retrieval_used=9,
                decoding=DecodingParams(),
                retrieve_zero_hits=[],
            )

    monkeypatch.setattr(appmod, "Runner", _FakeRunner)
    monkeypatch.setattr(appmod, "_latch", lambda: _FakeLatch())

    r = client.post("/api/reverify")
    assert r.status_code == 200
    body = r.json()
    assert body["budget"]["steps_used"] == 5
    assert body["budget"]["lead_max_steps"] == 18
    assert body["budget"]["retrieval_used"] == 9
    assert body["budget"]["retrieval_budget"] == 24

    j = client.get("/api/claims").json()
    assert j["running"] is False
    assert j["budget"]["steps_used"] == 5
    assert j["budget"]["retrieval_used"] == 9


def test_status_line_uses_guardrails_budget_not_hardcoded_24():
    """完成后状态文案读 retrieval_budget,禁止写死 /24。"""
    assert "+'/24" not in appmod.HTML_PAGE
    assert "retrieval_budget" in appmod.HTML_PAGE
    assert "retrieval_used" in appmod.HTML_PAGE


def test_dem4_copy_does_not_escalate_to_latch_proof():
    """验收措辞不升格:进度可见 ≠ UX/产品证明 latch。"""
    src = appmod.HTML_PAGE + (appmod.__doc__ or "")
    for phrase in ("UX 证明了 latch", "产品已验证", "一期测量闭合", "UX证明了latch"):
        assert phrase not in src


class _FakeLatch:
    def enter_round(self, claims):
        return type("R", (), {"thread_id": None, "pending": []})()
