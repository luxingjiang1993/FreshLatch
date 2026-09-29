"""#228 主张台账只读投影:discard∪renew、renew∉作废名单、MD 导出、零双写表。

零 LLM。不改 human_latch 写路径;不与 patch_events 糊缝。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.claim_ledger import (
    export_claim_ledger_md,
    get_claim_ledger,
    render_claim_ledger_markdown,
)
from freshlatch.store.sqlite_store import SCHEMA, SQLiteStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"


@pytest.fixture()
def store(tmp_path) -> SQLiteStore:
    return SQLiteStore(tmp_path / "ledger.db")


def _seed_discard_and_renew(store: SQLiteStore) -> None:
    store.add_invalidation("c-discard", "2026-09-29T10:00:00", reason="人审作废")
    store.log_latch(
        "2026-09-29T10:00:00",
        "c-discard",
        "discard",
        actor="human",
        machine_status_before="stale",
        override=False,
        run_id="run-a",
    )
    store.log_latch(
        "2026-09-29T11:00:00",
        "c-renew",
        "renew",
        evidence_id="doc#p1@T1",
        actor="human",
        machine_status_before="stale",
        override=True,
        run_id="run-a",
    )


def test_ledger_lists_discard_and_renew_distinct(store):
    """Given 已 discard 与已 renew,When 读投影,Then 两者 claim_id 均可见且动作可区分。"""
    _seed_discard_and_renew(store)
    ledger = get_claim_ledger(store)
    assert "c-discard" in ledger["discard_claim_ids"]
    assert "c-renew" in ledger["renew_claim_ids"]
    actions = {e["claim_id"]: e["action"] for e in ledger["entries"]}
    assert actions["c-discard"] == "discard"
    assert actions["c-renew"] == "renew"
    labels = {e["claim_id"]: e["label"] for e in ledger["entries"]}
    assert labels["c-discard"] == "人审作废"
    assert labels["c-renew"] == "人审续命"


def test_renew_not_in_invalidation_list(store):
    """Given 仅 renew 的 claim_id,When list_invalidation,Then 不含该 id。"""
    _seed_discard_and_renew(store)
    void_ids = store.list_invalidation()
    assert "c-renew" not in void_ids
    assert "c-discard" in void_ids
    ledger = get_claim_ledger(store)
    assert "c-renew" not in ledger["invalidation_claim_ids"]
    assert "c-renew" in ledger["renew_claim_ids"]


def test_export_md_contains_claim_ids(store, tmp_path):
    """Given 导出台账 MD,When 打开产物,Then 含 discard/renew claim_id。"""
    _seed_discard_and_renew(store)
    out = tmp_path / "claim-ledger.md"
    md = export_claim_ledger_md(store, out_path=out)
    assert out.read_text(encoding="utf-8") == md
    assert "c-discard" in md and "c-renew" in md
    assert "人审作废" in md and "人审续命" in md
    assert "renew∉" in md or "renew 不" in md or "renew∉此列" in md


def test_no_new_claim_ledger_write_table_in_schema():
    """仓库无新建双写作废表 DDL(SCHEMA 不含 claim_ledger 写表)。"""
    assert "CREATE TABLE" in SCHEMA
    assert not re.search(r"CREATE TABLE IF NOT EXISTS claim_ledger\b", SCHEMA)
    # 主张台账模块自身不得含写表 DDL
    mod = (SRC / "freshlatch" / "claim_ledger.py").read_text(encoding="utf-8")
    assert "CREATE TABLE" not in mod
    assert "INSERT INTO" not in mod
    assert "add_invalidation" not in mod


def test_run_id_filters_latch_entries_only(store):
    """run_id 过滤只作用于 latch 条目;作废名单仍全量可读。"""
    _seed_discard_and_renew(store)
    store.log_latch(
        "2026-09-29T12:00:00",
        "c-other",
        "renew",
        evidence_id="x#p1@T1",
        run_id="run-b",
    )
    scoped = get_claim_ledger(store, run_id="run-a")
    ids = {e["claim_id"] for e in scoped["entries"]}
    assert ids == {"c-discard", "c-renew"}
    assert "c-other" not in ids
    # 作废名单跨 Run 持久,不因 run_id 过滤而吞掉
    assert "c-discard" in scoped["invalidation_claim_ids"]


def test_rerun_not_in_ledger(store):
    """rerun 动作不进主张台账(仅 discard/renew)。"""
    store.log_latch("2026-09-29T09:00:00", "c1", "rerun")
    store.log_latch("2026-09-29T10:00:00", "c1", "discard", run_id="r1")
    store.add_invalidation("c1", "2026-09-29T10:00:00")
    ledger = get_claim_ledger(store)
    assert all(e["action"] in ("discard", "renew") for e in ledger["entries"])
    assert len(ledger["entries"]) == 1


def test_render_markdown_empty():
    md = render_claim_ledger_markdown(
        {
            "run_id": None,
            "entries": [],
            "discard_claim_ids": [],
            "renew_claim_ids": [],
            "invalidation_claim_ids": [],
        }
    )
    assert "主张台账" in md
    assert "尚无人审作废/续命记录" in md


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
    appmod._state.update(
        {
            "claims": [],
            "question": "",
            "trajectory": None,
            "running": False,
            "latch": dict(appmod.EMPTY_LATCH),
        }
    )
    return TestClient(appmod.app), store


def test_api_claim_ledger_and_export(client):
    """旁路 API 能列出 discard/renew;MD 导出含 claim_id。"""
    api, store = client
    _seed_discard_and_renew(store)
    r = api.get("/api/claim-ledger")
    assert r.status_code == 200
    body = r.json()
    assert "c-discard" in body["discard_claim_ids"]
    assert "c-renew" in body["renew_claim_ids"]
    assert "c-renew" not in body["invalidation_claim_ids"]

    md_r = api.get("/api/claim-ledger/export.md")
    assert md_r.status_code == 200
    text = md_r.text
    assert "c-discard" in text and "c-renew" in text
    assert "text/markdown" in md_r.headers.get("content-type", "")


def test_api_claims_includes_claim_ledger_sidepath(client):
    """Run 详情 /api/claims 旁路带 claim_ledger(可折叠 UI 同源数据)。"""
    api, store = client
    _seed_discard_and_renew(store)
    r = api.get("/api/claims")
    assert r.status_code == 200
    ledger = r.json()["claim_ledger"]
    assert "c-discard" in ledger["discard_claim_ids"]
    assert "c-renew" in ledger["renew_claim_ids"]


def test_ui_has_collapsible_claim_ledger_bypass():
    """详情旁路默认可折叠(<details>) + 导出按钮。"""
    assert 'id="claim-ledger"' in appmod.HTML_PAGE
    assert "<details id=\"claim-ledger\"" in appmod.HTML_PAGE or "<details id='claim-ledger'" in appmod.HTML_PAGE or 'id="claim-ledger"' in appmod.HTML_PAGE
    assert "导出台账 Markdown" in appmod.HTML_PAGE
    assert "renderClaimLedger" in appmod.HTML_PAGE
    assert "exportClaimLedgerMd" in appmod.HTML_PAGE
    # 不与 patch_events 糊缝:台账文案明示分缝
    assert "patch_events" in appmod.HTML_PAGE
