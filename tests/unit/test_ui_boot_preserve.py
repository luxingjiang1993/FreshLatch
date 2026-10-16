"""#665 boot 防洗:页面加载与隐式 import 不得清掉勿发 / 待拍板。

对齐 playtest WIPE_NOTE。显式清空只走高级「重置」。
不改闸门、RESULT-Y、HumanLatch discard|renew。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.models import Claim


def _blank() -> None:
    appmod._clear_live_sheet()
    appmod._state["running"] = False
    appmod._prepublish.clear()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    _blank()
    yield TestClient(appmod.app)
    _blank()


def _seed_blocked_sheet() -> dict:
    """样例复验留下的形状:未收口 stale → 勿发,且 latch pending 仍在。"""
    appmod._state["claims"] = [
        Claim(claim_id="keep-stale", statement="这条定价已经变了",
              status="stale", reason="T1 改写"),
        Claim(claim_id="keep-fresh", statement="这条份额仍在",
              status="fresh", reason="T1 仍支持"),
    ]
    appmod._state["question"] = "样例走完后的课题"
    appmod._state["latch"] = {
        "thread_id": "reverify-round-keep",
        "pending": [
            {"claim_id": "keep-stale", "status": "stale", "statement": "这条定价已经变了"},
        ],
    }
    appmod._state["trajectory"] = "keep-trajectory.jsonl"
    return appmod._sync_prepublish(new_run=True)


def _pending_ids(body: dict) -> list[str]:
    latch = body.get("latch") or {}
    return [row.get("claim_id") for row in (latch.get("pending") or [])]


def test_boot_and_refresh_keep_blocked_sheet_and_pending(client):
    """有勿发和待拍板时,GET /api/boot 与 GET / 都不洗。"""
    row = _seed_blocked_sheet()
    run_id = row["run_id"]
    runs_before = len(appmod._prepublish.runs)

    page = client.get("/")
    assert page.status_code == 200
    boot = client.get("/api/boot")
    assert boot.status_code == 200
    body = boot.json()
    assert body["disposition"] == "勿发"
    assert _pending_ids(body) == ["keep-stale"]
    assert body["latch"]["thread_id"] == "reverify-round-keep"
    assert body["active_run_id"] == run_id
    ids = [c["claim_id"] for c in body["claims"]]
    assert ids == ["keep-stale", "keep-fresh"]
    again = client.get("/api/boot").json()
    assert _pending_ids(again) == ["keep-stale"]
    assert again["disposition"] == "勿发"
    assert len(appmod._prepublish.runs) == runs_before
    assert appmod._prepublish.get(run_id).disposition == "勿发"


def test_import_does_not_wipe_pending_or_blocked_disposition(client):
    """隐式 import(boot 以前会调的那个入口)不再当作默认洗态。"""
    row = _seed_blocked_sheet()
    run_id = row["run_id"]

    imported = client.post("/api/import")
    assert imported.status_code == 200
    assert imported.json()["preserved"] is True
    body = client.get("/api/claims").json()
    assert body["disposition"] == "勿发"
    assert _pending_ids(body) == ["keep-stale"]
    assert body["active_run_id"] == run_id
    assert [c["claim_id"] for c in body["claims"]] == ["keep-stale", "keep-fresh"]

    draft = client.post("/api/import/draft", json={
        "text": "## other\n另一条主张\n",
    })
    assert draft.status_code == 200
    assert draft.json()["preserved"] is True
    body = client.get("/api/boot").json()
    assert _pending_ids(body) == ["keep-stale"]
    assert body["disposition"] == "勿发"
    assert appmod._prepublish.get(run_id).disposition == "勿发"


def test_pending_alone_is_enough_to_keep_sheet(client):
    """待拍板集合在,即使包结论不是勿发,import 也不清。"""
    appmod._state["claims"] = [
        Claim(claim_id="keep-unknown", statement="证据还不够", status="unknown"),
    ]
    appmod._state["latch"] = {
        "thread_id": "round-unknown",
        "pending": [{"claim_id": "keep-unknown", "status": "unknown", "statement": "证据还不够"}],
    }
    appmod._sync_prepublish(new_run=True)
    imported = client.post("/api/import")
    assert imported.json()["preserved"] is True
    body = client.get("/api/boot").json()
    assert _pending_ids(body) == ["keep-unknown"]
    assert [c["claim_id"] for c in body["claims"]] == ["keep-unknown"]


def test_blocked_disposition_alone_is_enough_to_keep_sheet(client):
    """没有 pending 时,勿发本身也不被 import 洗掉。"""
    appmod._state["claims"] = [
        Claim(claim_id="keep-stale", statement="材料变了", status="stale"),
    ]
    appmod._state["latch"] = dict(appmod.EMPTY_LATCH)
    appmod._sync_prepublish(new_run=True)
    assert client.get("/api/boot").json()["disposition"] == "勿发"
    imported = client.post("/api/import")
    assert imported.json()["preserved"] is True
    body = client.get("/api/claims").json()
    assert body["disposition"] == "勿发"
    assert [c["claim_id"] for c in body["claims"]] == ["keep-stale"]
    assert _pending_ids(body) == []


def test_import_still_loads_docket_when_sheet_is_empty(client):
    """空会话的显式 JSON docket 导入行为不变。"""
    imported = client.post("/api/import")
    assert imported.status_code == 200
    assert imported.json()["imported"] >= 1
    assert not imported.json().get("preserved")
    body = client.get("/api/claims").json()
    assert body["question"]
    assert any(c["claim_id"] == "c1" for c in body["claims"])


def test_import_still_replaces_unlocked_sheet(client):
    """没有勿发、也没有待拍板时,显式导入仍替换主张。"""
    appmod._state["claims"] = [
        Claim(claim_id="tmp-open", statement="可被显式导入替换", status="unknown"),
    ]
    appmod._state["latch"] = dict(appmod.EMPTY_LATCH)
    imported = client.post("/api/import")
    assert not imported.json().get("preserved")
    ids = [c["claim_id"] for c in client.get("/api/claims").json()["claims"]]
    assert "tmp-open" not in ids
    assert "c1" in ids


def test_reset_clears_live_sheet_and_keeps_history_row(client):
    """高级重置清空当前待拍板;已记下的勿发行还在。之后导入才生效。"""
    row = _seed_blocked_sheet()
    run_id = row["run_id"]

    reset = client.post("/api/session/reset")
    assert reset.status_code == 200
    assert reset.json()["reset"] is True
    live = client.get("/api/boot").json()
    assert live["claims"] == []
    assert _pending_ids(live) == []
    assert live["active_run_id"] is None
    listed = client.get("/api/prepublish/runs").json()["runs"]
    saved = next(item for item in listed if item["run_id"] == run_id)
    assert saved["disposition"] == "勿发"

    imported = client.post("/api/import")
    assert not imported.json().get("preserved")
    assert any(
        c["claim_id"] == "c1" for c in client.get("/api/claims").json()["claims"]
    )
    assert appmod._prepublish.get(run_id).disposition == "勿发"


def test_reset_refuses_while_reverify_running(client):
    _seed_blocked_sheet()
    appmod._state["running"] = True
    denied = client.post("/api/session/reset")
    assert denied.status_code == 409
    assert _pending_ids(client.get("/api/boot").json()) == ["keep-stale"]


def test_boot_js_loads_without_import_and_reset_is_advanced_only():
    """boot 不再调 import;「重置」只出现在高级/证据里,不在页头主路径。"""
    html = appmod.HTML_PAGE
    boot = html.split("async function boot()", 1)[1].split("async function resetSession", 1)[0]
    assert "fetch('/api/boot')" in boot
    assert "fetch('/api/import'" not in boot
    assert "renderClaims" in boot
    reset = html.split("async function resetSession()", 1)[1].split(
        "async function refreshT1Source", 1,
    )[0]
    assert "/api/session/reset" in reset
    assert "/api/import" not in reset
    assert "discard" not in reset
    assert "renew" not in reset

    body = html.split("<body>", 1)[1]
    before_advanced = body.split('<details id="advanced-evidence">', 1)[0]
    assert "重置" not in before_advanced
    assert 'id="btn-reset"' not in before_advanced
    advanced = html.split('<details id="advanced-evidence">', 1)[1].split(
        'id="craftsman-badges"', 1,
    )[0]
    assert 'id="btn-reset"' in advanced
    assert 'onclick="resetSession()"' in advanced
    assert ">重置</button>" in advanced
    header = html.split("<header>", 1)[1].split("</header>", 1)[0]
    assert "重置" not in header
    assert 'class="big"' in header
    # HumanLatch 动词集仍在,本票不改
    assert "action: 'discard'" in html
    assert "action:'renew'" in html
