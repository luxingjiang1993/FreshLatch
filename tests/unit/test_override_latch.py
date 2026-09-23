"""Batch 5 主缝:HumanLatch apply_decisions → latch_log 行形状(ADR-0023)。

只断言外部行为。override 是派生标签,不是模型变好,本文件不锁 Override Rate 通过线。
禁止:override⇒模型变好。失败或幂等跳过不得冒充新的对抗语义行。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from freshlatch.gates.human_latch import INVALID_ACTION, VALID_ACTIONS, apply_decisions
from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.sheet import project_claim, projections_with_override, render_client_memo_markdown
from freshlatch.store.base import Chunk, Document
from freshlatch.store.sqlite_store import SQLiteStore

DOC = "t0-competitor-notes"
EID = f"{DOC}#p2@T1"


def _now_factory():
    step = {"n": 0}

    def now() -> datetime:
        step["n"] += 1
        return datetime(2026, 9, 23, 12, 0, step["n"])

    return now


def _store(tmp_path) -> SQLiteStore:
    store = SQLiteStore(tmp_path / "freshlatch.db")
    chunk = Chunk(
        doc_id=DOC, chunk_id=f"{DOC}-p2", clause_id="p2", title="竞品笔记",
        text="T1:竞品客单价仍显著高于我们。", source_type="competitor",
        as_of="T1", doc_version="v2", checksum="", tokens=20,
    )
    store.add_document(
        Document(
            doc_id=DOC, as_of="T1", source_type="competitor", title="竞品笔记",
            doc_version="v2", checksum="", full_text=chunk.text,
        ),
        [chunk],
    )
    return store


def _claim(claim_id: str, status: str) -> Claim:
    return Claim(
        claim_id=claim_id,
        statement=f"主张 {claim_id}",
        status=status,
        reason=f"机器理由-{status}",
    )


def _rows(store: SQLiteStore, claim_id: str) -> list[dict]:
    return store.list_latch_rows(claim_id=claim_id)


def test_actions_remain_discard_or_renew():
    """动词封闭集不变,不出现 override action。"""
    assert VALID_ACTIONS == ("discard", "renew")
    assert "override" not in VALID_ACTIONS


def test_override_truth_table_on_apply_decisions(tmp_path):
    """成功人审真值表:fresh 作废与 stale/unknown 续命为对抗;其余成功为 false。"""
    store = _store(tmp_path)
    claims = {
        "c-fresh": _claim("c-fresh", "fresh"),
        "c-stale": _claim("c-stale", "stale"),
        "c-unknown": _claim("c-unknown", "unknown"),
        "c-stale-d": _claim("c-stale-d", "stale"),
        "c-unknown-d": _claim("c-unknown-d", "unknown"),
        "c-fresh-r": _claim("c-fresh-r", "fresh"),
    }
    decisions = [
        {"claim_id": "c-fresh", "action": "discard", "reviewer_note": "人对抗绿灯", "run_id": "run-fresh"},
        {"claim_id": "c-stale-d", "action": "discard"},
        {"claim_id": "c-unknown-d", "action": "discard"},
        {"claim_id": "c-stale", "action": "renew", "evidence_id": EID},
        {"claim_id": "c-unknown", "action": "renew", "evidence_id": EID},
        {"claim_id": "c-fresh-r", "action": "renew", "evidence_id": EID, "run_id": "run-renew-fresh"},
    ]
    results = apply_decisions(store, claims, decisions, now=_now_factory())
    assert [r["ok"] for r in results] == [True, True, True, True, True, True]

    fresh = _rows(store, "c-fresh")[0]
    assert fresh["action"] == "discard"
    assert fresh["machine_status_before"] == "fresh"
    assert fresh["override"] is True
    assert fresh["run_id"] == "run-fresh"
    assert fresh["reviewer_note"] == "人对抗绿灯"
    assert claims["c-fresh"].status == "fresh"  # 机器判定保留
    assert claims["c-fresh"].voided is True
    assert "c-fresh" in store.list_invalidation()

    assert _rows(store, "c-stale-d")[0]["override"] is False
    assert _rows(store, "c-stale-d")[0]["machine_status_before"] == "stale"
    assert claims["c-stale-d"].status == "stale"

    assert _rows(store, "c-unknown-d")[0]["override"] is False
    assert _rows(store, "c-unknown-d")[0]["machine_status_before"] == "unknown"

    stale_renew = _rows(store, "c-stale")[0]
    assert stale_renew["action"] == "renew"
    assert stale_renew["machine_status_before"] == "stale"
    assert stale_renew["override"] is True
    assert stale_renew["evidence_id"] == EID
    assert claims["c-stale"].status == "fresh"

    unknown_renew = _rows(store, "c-unknown")[0]
    assert unknown_renew["machine_status_before"] == "unknown"
    assert unknown_renew["override"] is True

    fresh_renew = _rows(store, "c-fresh-r")[0]
    assert fresh_renew["machine_status_before"] == "fresh"
    assert fresh_renew["override"] is False
    assert fresh_renew["run_id"] == "run-renew-fresh"

    # 作废名单仍是作废单一真相;override 不进名单表
    with store._conn() as conn:
        inv_cols = [r[1] for r in conn.execute("PRAGMA table_info(invalidation_list)")]
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "override" not in inv_cols
    assert "latch_events" not in tables
    assert store.list_reruns("c-fresh") == []


def test_idempotent_discard_does_not_add_adversarial_row(tmp_path):
    """重复 discard 幂等跳过,不把第二次记成新的 override 行。"""
    store = _store(tmp_path)
    claim = _claim("c1", "fresh")
    now = _now_factory()
    first = apply_decisions(store, {"c1": claim}, [{"claim_id": "c1", "action": "discard"}], now=now)
    second = apply_decisions(store, {"c1": claim}, [{"claim_id": "c1", "action": "discard"}], now=now)
    assert first[0]["ok"] is True and second[0]["ok"] is True
    assert "幂等" in second[0]["detail"]
    rows = _rows(store, "c1")
    assert len(rows) == 1
    assert rows[0]["override"] is True
    assert store.list_latch_rows(override=True) == rows


def test_failed_renew_and_bad_action_write_nothing(tmp_path):
    """失败续命与非法 action 零写,不冒充对抗行。"""
    store = _store(tmp_path)
    claims = {
        "c1": _claim("c1", "stale"),
        "c2": _claim("c2", "unknown"),
    }
    results = apply_decisions(
        store,
        claims,
        [
            {"claim_id": "c1", "action": "renew", "evidence_id": "nope"},
            {"claim_id": "c2", "action": "override"},
            {"claim_id": "missing", "action": "discard"},
        ],
        now=_now_factory(),
    )
    assert results[0]["ok"] is False
    assert results[1]["ok"] is False and results[1]["error_code"] == INVALID_ACTION
    assert results[2]["ok"] is False
    assert store.list_latch_rows() == []
    assert claims["c1"].status == "stale"
    assert claims["c2"].status == "unknown"
    assert store.list_invalidation() == []


def test_timeline_shows_override_and_audit_filter(tmp_path):
    """主张时间线可读人审作废/续命;审计过滤只留 override=true。"""
    store = _store(tmp_path)
    fresh = _claim("c-fresh", "fresh")
    stale = _claim("c-stale", "stale")
    apply_decisions(
        store,
        {"c-fresh": fresh, "c-stale": stale},
        [
            {"claim_id": "c-fresh", "action": "discard"},
            {"claim_id": "c-stale", "action": "discard"},
        ],
        now=_now_factory(),
    )
    proj_fresh = project_claim(store, fresh)
    proj_stale = project_claim(store, stale)
    assert proj_fresh["timeline"][0]["label"] == "人审作废"
    assert proj_fresh["timeline"][0]["override"] is True
    assert proj_fresh["timeline"][0]["machine_status_before"] == "fresh"
    assert proj_stale["timeline"][0]["label"] == "人审作废"
    assert proj_stale["timeline"][0]["override"] is False

    kept = projections_with_override([proj_fresh, proj_stale])
    assert [p["claim_id"] for p in kept] == ["c-fresh"]
    assert [r["claim_id"] for r in store.list_latch_rows(override=True)] == ["c-fresh"]
    assert [r["claim_id"] for r in store.list_latch_rows(override=False)] == ["c-stale"]


def test_client_memo_does_not_carry_latch_events(tmp_path):
    """人审事件流不进 Client Memo。"""
    store = _store(tmp_path)
    claim = _claim("c-fresh", "fresh")
    apply_decisions(
        store, {"c-fresh": claim}, [{"claim_id": "c-fresh", "action": "discard"}], now=_now_factory(),
    )
    md = render_client_memo_markdown(
        [project_claim(store, claim)],
        question="课题",
        generated_at="2026-09-23T12:00:00+08:00",
    )
    assert "人审作废" not in md
    assert "人审续命" not in md
    assert "latch_log" not in md
    assert " · override" not in md


def test_human_latch_decide_writes_run_id(tmp_path):
    """管道 decide 成功行带本轮 thread 作为 run_id;stale 作废不是对抗。"""
    store = _store(tmp_path)
    latch = HumanLatch(store, tmp_path / "checkpoints.db")
    claim = _claim("c1", "stale")
    rnd = latch.enter_round([claim], ts="20260923-120000")
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "discard"}])
    assert results[0]["ok"] is True
    row = _rows(store, "c1")[0]
    assert row["override"] is False
    assert row["machine_status_before"] == "stale"
    assert row["run_id"] == "reverify-round-20260923-120000"
    assert claim.status == "stale"


def test_old_latch_log_rows_remain_readable(tmp_path):
    """旧库无新列时迁移后旧行可读,缺省不回填对抗语义。"""
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE latch_log ("
        "ts TEXT NOT NULL, claim_id TEXT NOT NULL, action TEXT NOT NULL, "
        "evidence_id TEXT, actor TEXT NOT NULL DEFAULT 'human')"
    )
    conn.execute(
        "INSERT INTO latch_log (ts, claim_id, action, evidence_id, actor) "
        "VALUES ('2026-09-01T00:00:00', 'c-old', 'discard', NULL, 'human')"
    )
    conn.commit()
    conn.close()

    store = SQLiteStore(path)
    old = store.list_latch_rows(claim_id="c-old")
    assert len(old) == 1
    assert old[0]["action"] == "discard"
    assert old[0]["machine_status_before"] is None
    assert old[0]["override"] is None
    assert store.list_latch_rows(override=True) == []

    store.log_latch(
        "2026-09-23T00:00:00", "c-new", "discard",
        machine_status_before="fresh", override=True,
    )
    new = store.list_latch_rows(claim_id="c-new")[0]
    assert new["override"] is True
    assert new["machine_status_before"] == "fresh"
