"""DEM-1 / #88:主张导入稿(MD/粘贴)→复验单主张列表。挂复验单 UI 套件(TestClient + 源码红线)。

只测外部行为:HTTP 导入结果、HTML 导入面在位、JSON docket 高级入口仍可用。
不做自由散文抽主张 / 一键 LLM 切分。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    appmod._state.update({"claims": [], "question": "", "trajectory": None,
                          "running": False, "latch": dict(appmod.EMPTY_LATCH)})
    return TestClient(appmod.app)


# -- 源码/DOM 红线(成交面:导入稿入口 ≠ 聊天) ---------------------------------------


def test_claim_import_draft_ui_surface_present():
    """DEM-1:复验单有主张导入稿粘贴面与导入动作(非聊天形态)。"""
    html = appmod.HTML_PAGE
    assert "主张导入稿" in html
    assert 'id="claim-import-draft"' in html
    assert "importClaimDraft" in html
    # 禁止把导入面做成聊天/LLM 切分
    assert "一键 LLM" not in html
    assert "自由散文抽主张" not in html
    assert "chat-input" not in html
    assert "message-input" not in html


def test_json_docket_advanced_entry_still_present():
    """JSON docket 高级入口仍可用(不删除、不降级为唯一路径)。"""
    assert "/api/import" in appmod.HTML_PAGE or "importDocket" in appmod.HTML_PAGE
    assert "高级" in appmod.HTML_PAGE  # 文案标明高级入口


# -- API 行为 ----------------------------------------------------------------------


def test_import_draft_splits_on_claim_id_headings(client):
    """## claim_id + 正文切条正确,导入后出现在复验单 /api/claims。"""
    text = (
        "# 是否进入东南亚客服市场?\n\n"
        "## c1\n"
        "竞品客单价仍显著高于我方\n\n"
        "## c2\n"
        "监管暂无本地化强制要求\n"
    )
    r = client.post("/api/import/draft", json={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 2
    assert body["assigned_ids"] == []  # 两条都自带 id
    j = client.get("/api/claims").json()
    assert j["question"] == "是否进入东南亚客服市场?"
    ids = [c["claim_id"] for c in j["claims"]]
    assert ids == ["c1", "c2"]
    assert j["claims"][0]["statement"] == "竞品客单价仍显著高于我方"
    assert j["claims"][1]["statement"] == "监管暂无本地化强制要求"


def test_import_draft_assigns_c_import_n_when_id_missing(client):
    """缺 id 分配 c-import-N 且可追溯(顺序编号进 assigned_ids)。"""
    text = (
        "##\n"
        "第一条无 id 主张\n\n"
        "## c-known\n"
        "自带 id\n\n"
        "##   \n"
        "第二条无 id 主张\n"
    )
    r = client.post("/api/import/draft", json={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 3
    assert body["assigned_ids"] == ["c-import-1", "c-import-2"]
    j = client.get("/api/claims").json()
    ids = [c["claim_id"] for c in j["claims"]]
    assert ids == ["c-import-1", "c-known", "c-import-2"]
    by_id = {c["claim_id"]: c["statement"] for c in j["claims"]}
    assert by_id["c-import-1"] == "第一条无 id 主张"
    assert by_id["c-import-2"] == "第二条无 id 主张"


def test_import_draft_does_not_extract_free_prose(client):
    """自由散文(无 ## 切条)不得被抽成主张。"""
    r = client.post("/api/import/draft", json={
        "text": "这是一段没有标题的散文,讲了很多定价和监管,但没有 ## 切条。\n",
    })
    assert r.status_code == 400
    assert client.get("/api/claims").json()["claims"] == []


def test_import_draft_ignores_h3_headings(client):
    """### 不是主张切条;不得误当成 ## claim_id。"""
    text = (
        "## c1\n"
        "正主张\n\n"
        "### 小节标题\n"
        "仍属 c1 正文的续写\n"
    )
    r = client.post("/api/import/draft", json={"text": text})
    assert r.status_code == 200
    j = client.get("/api/claims").json()
    assert [c["claim_id"] for c in j["claims"]] == ["c1"]
    assert "小节标题" in j["claims"][0]["statement"]


def test_json_docket_import_still_works(client):
    """既有 JSON docket /api/import 高级入口行为不变。"""
    r = client.post("/api/import")
    assert r.status_code == 200
    assert r.json()["imported"] >= 1
    j = client.get("/api/claims").json()
    assert j["question"]
    assert any(c["claim_id"] == "c1" for c in j["claims"])
