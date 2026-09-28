"""发前列表 API/投影单测(#173):零 LLM。

覆盖:列表字段(标题/来源、disposition、更新时间、Run 状态);
详情增量包结论条 + decide 路径仍可用;checksum/闸结果可见。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.disposition import DISPOSITIONS
from freshlatch.models import Claim
from freshlatch.prepublish import (
    RUN_STATUSES,
    claim_to_disposition_input,
    derive_run_status,
    disposition_for_claims,
    list_t1_checksums,
    project_gate_results,
)
from freshlatch.sheet import project_run_disposition
from freshlatch.store.base import Chunk, Document


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "CORPUS", tmp_path / "corpus")
    (tmp_path / "corpus" / "t1").mkdir(parents=True)
    appmod._prepublish.clear()
    appmod._state.update({
        "claims": [], "question": "", "trajectory": None,
        "running": False, "latch": dict(appmod.EMPTY_LATCH),
        "budget": dict(appmod.EMPTY_BUDGET), "run_ctx": None,
        "retrieve_zero_hits": [], "active_run_id": None,
    })
    appmod._reset_t1_source(store)
    return TestClient(appmod.app)


def _seed_stale_fresh():
    claims = [
        Claim(claim_id="c1", statement="份额仍高", status="stale", reason="T1 下降"),
        Claim(claim_id="c2", statement="采用率仍升", status="fresh", reason="T1 仍支持"),
    ]
    appmod._state["claims"] = claims
    appmod._state["question"] = "顾问报告发前复验"
    return claims


def test_list_api_exposes_required_fields(client):
    """Given 含 disposition 的 Run 摘要,When 请求发前列表,Then 四字段齐全。"""
    _seed_stale_fresh()
    appmod._sync_prepublish(new_run=True)
    r = client.get("/api/prepublish/runs")
    assert r.status_code == 200
    body = r.json()
    assert body["runs"], "至少一条 Run 摘要"
    row = body["runs"][0]
    for key in ("title", "source", "disposition", "updated_at", "status"):
        assert key in row and row[key], f"缺字段 {key}"
    assert row["disposition"] in DISPOSITIONS
    assert row["disposition"] == "勿发"  # 未收口 stale
    assert row["status"] in RUN_STATUSES


def test_disposition_bar_on_claims_and_sheet_helper(client):
    """详情 /api/claims 含包结论条字段;sheet 投影与之对齐。"""
    claims = _seed_stale_fresh()
    assert project_run_disposition(claims) == "勿发"
    j = client.get("/api/claims").json()
    assert j["disposition"] == "勿发"
    assert "gate_results" in j and len(j["gate_results"]) == 2
    assert j["gate_results"][0]["claim_id"] == "c1"


def test_detail_html_has_disposition_and_prepublish_list_shell(client):
    """既有复验单增量包结论条;发前列表页存在;无第二 UI 栈词。"""
    assert 'id="disposition-bar"' in appmod.HTML_PAGE
    assert "包结论" in appmod.HTML_PAGE
    assert 'id="t1-checksums"' in appmod.HTML_PAGE
    assert 'id="gate-results"' in appmod.HTML_PAGE
    assert "/api/latch/decide" in appmod.HTML_PAGE  # discard/renew 路径仍在
    html = client.get("/prepublish").text
    assert "发前" in html and "包结论" in html
    assert "Run 状态" in html
    # 禁止抄编排角色名当词表
    assert "Orchestrator" not in html
    assert "approve_promotion" not in html
    assert "ask_human" not in appmod.HTML_PAGE


def test_list_opens_detail_path(client):
    """列表 Run 详情路由指向既有复验单 `/`,不造第三套详情。"""
    _seed_stale_fresh()
    row = appmod._sync_prepublish(new_run=True)
    r = client.get(f"/api/prepublish/runs/{row['run_id']}")
    assert r.status_code == 200
    assert r.json()["detail_path"] == "/"
    assert r.json()["run"]["disposition"] == "勿发"


def test_decide_path_still_works_after_disposition(client):
    """从列表语义进入详情后,/api/latch/decide 仍可用。"""
    claims = _seed_stale_fresh()
    appmod._sync_prepublish(new_run=True)
    rnd = appmod._latch().enter_round(claims)
    assert rnd.waiting
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
    appmod._sync_prepublish(new_run=False)
    r = client.post(
        "/api/latch/decide",
        json={"thread_id": rnd.thread_id,
              "decisions": [{"claim_id": "c1", "action": "discard"}]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["results"][0]["ok"] is True
    assert body["disposition"] == "可发"  # stale 已 discard 收口
    assert body["latch"]["thread_id"] is None
    listed = client.get("/api/prepublish/runs").json()["runs"]
    assert listed[0]["disposition"] == "可发"
    assert listed[0]["status"] == "已落档"


def test_t1_checksums_visible(client):
    """详情可投影 T1 checksum 列表。"""
    store = appmod._store()
    store.add_document(
        Document(doc_id="doc-a", as_of="T1", source_type="report", title="摘录",
                 doc_version="v1", checksum="abc123", full_text="正文"),
        [Chunk(doc_id="doc-a", chunk_id="doc-a-p1", clause_id="p1", title="摘录",
               text="正文", source_type="report", as_of="T1", doc_version="v1",
               checksum="abc123", tokens=2)],
    )
    _seed_stale_fresh()
    rows = list_t1_checksums(store)
    assert rows and rows[0]["checksum"] == "abc123"
    j = client.get("/api/claims").json()
    assert any(x["checksum"] == "abc123" for x in j["t1_checksums"])


def test_gate_results_surface_rejection_code():
    """闸打回 error_code 可从 reason 投影。"""
    claims = [Claim(claim_id="c1", statement="x", status="unknown",
                    reason="[闸打回:CHECKSUM_MISMATCH] 指纹不对; 原理由: ...")]
    rows = project_gate_results(claims)
    assert rows[0]["gate_rejected"] is True
    assert rows[0]["error_code"] == "CHECKSUM_MISMATCH"


def test_derive_run_status_and_claim_mapping():
    assert derive_run_status(running=True, latch={}) == "复验中"
    assert derive_run_status(running=False, latch={"thread_id": "t1"}) == "待人审"
    assert derive_run_status(running=False, latch={}) == "已落档"
    c = Claim(claim_id="c1", statement="s", status="stale", voided=True)
    assert claim_to_disposition_input(c).human_action == "discard"
    assert disposition_for_claims([c]) == "可发"
