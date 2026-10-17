"""#665 boot 防洗 + #678(I-01) run snapshot 恢复与 import 守卫。

对齐 playtest WIPE_NOTE 与父规格 #677 I-01:
- 页面加载/刷新不洗勿发/待拍板(#665);判定面经同库 pack sqlite JSON blob
  落盘/恢复(#678 I-01),不新开表、不新开 DB,LangGraph checkpoint 仍只救人审 interrupt。
- 非空 active_run 时 /api/import、/api/import/draft 硬 409 + 高级重置指引
  (breaking vs #669 的 200+preserved);确认重置后才可导入。
- 不做轨迹逐步回放(本期 OUT)。
不改闸门、RESULT-Y、HumanLatch discard|renew。
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.models import Claim


def _blank() -> None:
    appmod._clear_live_sheet()
    appmod._state["running"] = False
    appmod._prepublish.clear()


def _simulate_restart() -> None:
    """模拟 F5/新标签落到新进程:内存态与进程内注册表清空,pack sqlite 留在磁盘。"""
    _blank()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    # decide 成功写 patch_events;单测落到临时目录,不进 data/patch_events/
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
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


def test_import_conflicts_with_nonempty_active_run(client):
    """#678(I-01) breaking:非空 active_run 时 import 硬 409 + 重置指引,不静默保留。"""
    row = _seed_blocked_sheet()
    run_id = row["run_id"]

    imported = client.post("/api/import")
    assert imported.status_code == 409
    conflict = imported.json()
    assert conflict["code"] == "ACTIVE_RUN_CONFLICT"
    assert conflict["active_run_id"] == run_id
    assert "/api/session/reset" in conflict["reset_hint"]
    body = client.get("/api/claims").json()
    assert body["disposition"] == "勿发"
    assert _pending_ids(body) == ["keep-stale"]
    assert body["active_run_id"] == run_id
    assert [c["claim_id"] for c in body["claims"]] == ["keep-stale", "keep-fresh"]

    draft = client.post("/api/import/draft", json={
        "text": "## other\n另一条主张\n",
    })
    assert draft.status_code == 409
    assert draft.json()["code"] == "ACTIVE_RUN_CONFLICT"
    body = client.get("/api/boot").json()
    assert _pending_ids(body) == ["keep-stale"]
    assert body["disposition"] == "勿发"
    assert appmod._prepublish.get(run_id).disposition == "勿发"


def test_pending_alone_is_enough_to_conflict_import(client):
    """待拍板集合在(且已绑 Run),即使包结论不是勿发,import 也 409。"""
    appmod._state["claims"] = [
        Claim(claim_id="keep-unknown", statement="证据还不够", status="unknown"),
    ]
    appmod._state["latch"] = {
        "thread_id": "round-unknown",
        "pending": [{"claim_id": "keep-unknown", "status": "unknown", "statement": "证据还不够"}],
    }
    appmod._sync_prepublish(new_run=True)
    imported = client.post("/api/import")
    assert imported.status_code == 409
    assert imported.json()["code"] == "ACTIVE_RUN_CONFLICT"
    body = client.get("/api/boot").json()
    assert _pending_ids(body) == ["keep-unknown"]
    assert [c["claim_id"] for c in body["claims"]] == ["keep-unknown"]


def test_blocked_disposition_alone_is_enough_to_conflict_import(client):
    """没有 pending 时,勿发本身 + 已绑 Run 也使 import 409。"""
    appmod._state["claims"] = [
        Claim(claim_id="keep-stale", statement="材料变了", status="stale"),
    ]
    appmod._state["latch"] = dict(appmod.EMPTY_LATCH)
    appmod._sync_prepublish(new_run=True)
    assert client.get("/api/boot").json()["disposition"] == "勿发"
    imported = client.post("/api/import")
    assert imported.status_code == 409
    body = client.get("/api/claims").json()
    assert body["disposition"] == "勿发"
    assert [c["claim_id"] for c in body["claims"]] == ["keep-stale"]
    assert _pending_ids(body) == []


def test_import_still_loads_docket_when_sheet_is_empty(client):
    """空会话(无 active_run)的显式 JSON docket 导入行为不变。"""
    imported = client.post("/api/import")
    assert imported.status_code == 200
    assert imported.json()["imported"] >= 1
    assert not imported.json().get("preserved")
    body = client.get("/api/claims").json()
    assert body["question"]
    assert any(c["claim_id"] == "c1" for c in body["claims"])


def test_import_still_replaces_unlocked_sheet(client):
    """没有 active_run 绑定时,显式导入仍替换主张。"""
    appmod._state["claims"] = [
        Claim(claim_id="tmp-open", statement="可被显式导入替换", status="unknown"),
    ]
    appmod._state["latch"] = dict(appmod.EMPTY_LATCH)
    imported = client.post("/api/import")
    assert imported.status_code == 200
    assert not imported.json().get("preserved")
    ids = [c["claim_id"] for c in client.get("/api/claims").json()["claims"]]
    assert "tmp-open" not in ids
    assert "c1" in ids


def test_reset_clears_live_sheet_snapshot_and_keeps_history_row(client):
    """高级重置清空当前待拍板并洗 snapshot;已记下的勿发行还在。之后导入才生效。"""
    row = _seed_blocked_sheet()
    run_id = row["run_id"]
    appmod._write_run_snapshot()  # 复验结束/人审后 blob 已落盘;这里显式补齐

    reset = client.post("/api/session/reset")
    assert reset.status_code == 200
    assert reset.json()["reset"] is True
    assert appmod._store().load_run_snapshot() is None  # snapshot 随重置洗掉
    live = client.get("/api/boot").json()
    assert live["claims"] == []
    assert _pending_ids(live) == []
    assert live["active_run_id"] is None
    listed = client.get("/api/prepublish/runs").json()["runs"]
    saved = next(item for item in listed if item["run_id"] == run_id)
    assert saved["disposition"] == "勿发"

    imported = client.post("/api/import")
    assert imported.status_code == 200
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


# -- I-01(#678):run snapshot 落盘/恢复 ------------------------------------------------


def test_import_writes_run_snapshot_to_pack_sqlite(client):
    """I-01:导入成功即写 snapshot;JSON blob 在同库 pack sqlite,不新开表/不新开 DB。"""
    imported = client.post("/api/import")
    assert imported.status_code == 200
    blob = appmod._store().load_run_snapshot()
    assert blob is not None
    snap = json.loads(blob)
    assert snap["version"] == appmod.RUN_SNAPSHOT_VERSION
    assert snap["active_run_id"] == imported.json()["run"]["run_id"]
    assert len(snap["claims"]) == imported.json()["imported"]


def test_boot_restores_verdict_surface_from_run_snapshot(client):
    """I-01:F5/新标签(模拟进程重启)后,判定/理由/voided/active_run_id/包结论与磁盘一致。"""
    row = _seed_blocked_sheet()
    run_id = row["run_id"]
    claims = appmod._state["claims"]
    claims[0].voided = True  # 人审作废标记也进 snapshot
    claims[0].voided_at = "2026-10-17T00:00:00"
    appmod._sync_prepublish(new_run=False)
    before = client.get("/api/claims").json()
    appmod._write_run_snapshot()
    blob = appmod._store().load_run_snapshot()
    assert blob is not None and '"voided": true' in blob

    _simulate_restart()
    boot = client.get("/api/boot")
    assert boot.status_code == 200
    body = boot.json()
    assert body["active_run_id"] == run_id
    assert body["disposition"] == before["disposition"]
    assert _pending_ids(body) == ["keep-stale"]
    assert body["latch"]["thread_id"] == "reverify-round-keep"
    by_id = {c["claim_id"]: c for c in body["claims"]}
    assert by_id["keep-stale"]["status"] == "stale"
    assert by_id["keep-stale"]["reason"] == "T1 改写"
    assert by_id["keep-stale"]["voided"] is True
    assert by_id["keep-fresh"]["status"] == "fresh"
    # 刷新幂等:再 boot 一次仍是同一份判定面
    again = client.get("/api/boot").json()
    assert again["active_run_id"] == run_id
    assert {c["claim_id"] for c in again["claims"]} == {"keep-stale", "keep-fresh"}
    # 恢复出的非空 active_run 仍挡 import(与 409 守卫一致)
    assert client.post("/api/import").status_code == 409


def test_snapshot_updates_after_human_review_change(client):
    """I-01:人审变更(作废)后 snapshot 立刻更新;再「重启」boot 仍是最新人审结果。"""
    claims = [Claim(claim_id="h-stale", statement="旧定价已变",
                    status="stale", reason="T1 改写")]
    appmod._state["claims"] = claims
    appmod._state["question"] = "人审样例课题"
    rnd = appmod._latch().enter_round(claims)  # 真实轮次 thread(先在 interrupt 落盘)
    assert rnd.waiting
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
    appmod._sync_prepublish(new_run=True)

    r = client.post("/api/latch/decide",
                    json={"thread_id": rnd.thread_id,
                          "decisions": [{"claim_id": "h-stale", "action": "discard",
                                         "reviewer_note": "人审作废"}]})
    assert r.status_code == 200
    live = next(c for c in r.json()["claims"] if c["claim_id"] == "h-stale")
    assert live["voided"] is True

    blob = appmod._store().load_run_snapshot()
    assert blob is not None
    snap = json.loads(blob)
    saved = next(c for c in snap["claims"] if c["claim_id"] == "h-stale")
    assert saved["voided"] is True

    _simulate_restart()
    boot = client.get("/api/boot").json()
    restored = next(c for c in boot["claims"] if c["claim_id"] == "h-stale")
    assert restored["voided"] is True
    assert restored["reason"] == "T1 改写"
    assert boot["active_run_id"] == snap["active_run_id"]


def test_boot_without_snapshot_keeps_demo_path(client):
    """I-01:无 active_run 且 snapshot 空 → boot 不恢复、import 可导 demo(新手路径不破)。"""
    boot = client.get("/api/boot").json()
    assert boot["claims"] == []
    assert boot["active_run_id"] is None
    imported = client.post("/api/import")
    assert imported.status_code == 200
    assert imported.json()["imported"] >= 1


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
