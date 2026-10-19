"""L4-B-05: 审计面失败三桶 + disputed 人审改账。

夹具不等于注册分。不重标冻结 gold,不改 floors。
产品桶(检索空 / grade 不够 / tool_tier_2 拒) ≠ ADR-0028 评测桶。
"""

from __future__ import annotations

import ast
import json
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.gates.human_latch import (
    DISPUTED_NO_CONCLUSION,
    VALID_ACTIONS,
    apply_decisions,
    derive_override,
    read_disputed_reopen,
)
from freshlatch.models import Claim
from freshlatch.sheet import project_audit
from freshlatch.store.base import Chunk, Document
from freshlatch.store.sqlite_store import SQLiteStore

REPO = Path(__file__).resolve().parents[2]
LOOP_PATH = REPO / "src/freshlatch/roles/loop.py"
RUNNER_PATH = REPO / "src/freshlatch/runner.py"
CONTEXT_PATH = REPO / "docs" / "glossary.md"
EVIDENCE_ID = "fix-memo#p1@T1"
DOC = "fix-memo"


def _write_jsonl(path: Path, events: list[dict]) -> None:
    lines = [json.dumps(event, ensure_ascii=False) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _section(html: str, element_id: str) -> str:
    marker = f'id="{element_id}"'
    assert marker in html
    return html.split(marker, 1)[1].split("</div>", 1)[0]


def _active_bucket(html: str) -> str:
    section = _section(html, "audit-failure-buckets")
    assert "检索空" in section
    assert "grade 不够" in section
    assert "tool_tier_2 拒" in section
    assert ">失败<" not in section
    assert section.count("is-active") == 1
    marker = 'class="failure-bucket is-active" data-bucket="'
    assert marker in section
    return section.split(marker, 1)[1].split('"', 1)[0]


def _empty_events() -> list[dict]:
    return [
        {
            "type": "retrieve",
            "claim_id": "c-empty",
            "query": "定价",
            "hits": [],
            "evidence_ids": [],
        },
        {
            "type": "lead_step",
            "claim_id": "c-empty",
            "step": 1,
            "tool": "retrieve",
            "result": {
                "blocks": [],
                "grade": "incorrect",
                "reason_code": "insufficient_evidence",
            },
        },
        {
            "type": "lead_loop_end",
            "claim_id": "c-empty",
            "evidence_ids": [],
            "grade": "incorrect",
            "retry_count": 0,
            "reason_code": "insufficient_evidence",
        },
    ]


def _grade_events() -> list[dict]:
    return [
        {
            "type": "lead_step",
            "claim_id": "c-grade",
            "step": 1,
            "tool": "retrieve",
            "result": {
                "blocks": [{"evidence_id": EVIDENCE_ID}],
                "grade": "incorrect",
            },
        },
        {
            "type": "lead_loop_end",
            "claim_id": "c-grade",
            "evidence_ids": [EVIDENCE_ID],
            "grade": "incorrect",
            "retry_count": 1,
            "reason_code": "grade_incorrect_exhausted",
        },
    ]


def _tier_events() -> list[dict]:
    return [
        {
            "type": "lead_step",
            "claim_id": "c-tier",
            "step": 1,
            "tool": "spawn_auditor",
            "result": {
                "type": "tool_tier_observation",
                "tool": "spawn_auditor",
                "tool_tier": "tool_tier_2",
                "ok": False,
                "fail_closed": True,
                "reason_code": "tool_tier_denied",
                "error": "spawn_auditor 属于 tool_tier_2,禁止调用",
            },
        },
        {
            "type": "lead_loop_end",
            "claim_id": "c-tier",
            "evidence_ids": [],
            "grade": None,
            "retry_count": 0,
        },
    ]


def test_three_buckets_stay_distinct_on_audit_ui(tmp_path, monkeypatch):
    """验收 1: 三条失败夹具各高亮自己的桶,不收成一个「失败」。"""
    store = SQLiteStore(tmp_path / "ui.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
    appmod._state.update({
        "claims": [],
        "question": "",
        "trajectory": None,
        "running": False,
        "latch": dict(appmod.EMPTY_LATCH),
    })
    client = TestClient(appmod.app)
    cases = [
        ("empty.jsonl", _empty_events(), "retrieval_empty", "检索空"),
        ("grade.jsonl", _grade_events(), "grade_insufficient", "grade 不够"),
        ("tier.jsonl", _tier_events(), "tool_tier_2_denied", "tool_tier_2 拒"),
    ]
    for name, events, bucket_id, label in cases:
        path = tmp_path / name
        _write_jsonl(path, events)
        projected = project_audit(path)
        assert projected["failure_bucket"] == bucket_id
        active = [row for row in projected["failure_buckets"] if row["active"]]
        assert active == [{"id": bucket_id, "label": label, "active": True}]
        assert [row["label"] for row in projected["failure_buckets"]] == [
            "检索空",
            "grade 不够",
            "tool_tier_2 拒",
        ]
        appmod._state["trajectory"] = path
        html = client.get("/?view=audit").text
        assert _active_bucket(html) == bucket_id
        assert label in _section(html, "audit-failure-buckets")


def test_grade_ambiguous_is_grade_bucket_not_eval_bucket(tmp_path):
    """grade=ambiguous 归 grade 不够。评测桶名不进产品高亮。"""
    path = tmp_path / "ambiguous.jsonl"
    _write_jsonl(path, [{
        "type": "lead_loop_end",
        "claim_id": "c-amb",
        "evidence_ids": [EVIDENCE_ID],
        "grade": "ambiguous",
        "retry_count": 0,
        "reason_code": "grade_ambiguous",
    }])
    projected = project_audit(path)
    assert projected["failure_bucket"] == "grade_insufficient"
    labels = [row["label"] for row in projected["failure_buckets"]]
    for banned in ("找不到", "找错", "没用上", "失败"):
        assert banned not in labels


def test_tool_tier_1_denial_is_not_tool_tier_2_bucket(tmp_path):
    """tool_tier_1 未批不是 tool_tier_2 拒。"""
    path = tmp_path / "tier1.jsonl"
    _write_jsonl(path, [{
        "type": "lead_step",
        "claim_id": "c-t1",
        "step": 1,
        "tool": "reverify_claim",
        "result": {
            "tool": "reverify_claim",
            "tool_tier": "tool_tier_1",
            "ok": False,
            "reason_code": "tool_tier_denied",
        },
    }, {
        "type": "lead_loop_end",
        "claim_id": "c-t1",
        "evidence_ids": [],
        "grade": None,
        "retry_count": 0,
    }])
    projected = project_audit(path)
    assert projected["failure_bucket"] is None
    assert projected["failure_bucket_claims"] == []
    assert all(not row["active"] for row in projected["failure_buckets"])


def _now_factory():
    step = {"n": 0}

    def now() -> datetime:
        step["n"] += 1
        return datetime(2026, 10, 15, 9, 0, step["n"])

    return now


def _store(tmp_path) -> SQLiteStore:
    store = SQLiteStore(tmp_path / "latch.db")
    chunk = Chunk(
        doc_id=DOC, chunk_id=f"{DOC}-p1", clause_id="p1", title="备忘",
        text="T1 原文确认专业版定价仍为 299 元/席/月。", source_type="public",
        as_of="T1", doc_version="v1", checksum="", tokens=12,
    )
    store.add_document(
        Document(
            doc_id=DOC, as_of="T1", source_type="public", title="备忘",
            doc_version="v1", checksum="", full_text=chunk.text,
        ),
        [chunk],
    )
    return store


def test_disputed_ledger_reopen_keeps_discard_and_renew(tmp_path):
    """验收 2: disputed 进台账且可再打开;discard / renew 仍可用;不写回主张。"""
    store = _store(tmp_path)
    disputed = Claim(claim_id="c-disputed", statement="待改账", status="unknown", reason="机器未知")
    discarded = Claim(claim_id="c-discard", statement="待作废", status="stale", reason="机器红")
    renewed = Claim(claim_id="c-renew", statement="待续命", status="stale", reason="机器红")
    claims = {
        disputed.claim_id: disputed,
        discarded.claim_id: discarded,
        renewed.claim_id: renewed,
    }
    assert derive_override("disputed", "unknown") is False
    missing = apply_decisions(
        store, claims,
        [{"claim_id": "c-disputed", "action": "disputed"}],
        now=_now_factory(),
    )
    assert missing[0]["ok"] is False
    assert missing[0]["error_code"] == DISPUTED_NO_CONCLUSION
    assert store.list_latch_rows(claim_id="c-disputed") == []

    conclusion = "人认为 grade 不够的拒答过严,先改账不改机器判定"
    results = apply_decisions(
        store, claims,
        [
            {"claim_id": "c-disputed", "action": "disputed", "reviewer_note": conclusion},
            {"claim_id": "c-discard", "action": "discard"},
            {"claim_id": "c-renew", "action": "renew", "evidence_id": EVIDENCE_ID},
        ],
        now=_now_factory(),
    )
    assert [row["ok"] for row in results] == [True, True, True]
    assert [row["action"] for row in results] == ["disputed", "discard", "renew"]

    assert disputed.status == "unknown"
    assert disputed.voided is False
    assert disputed.validity_basis is None
    assert "c-disputed" not in store.list_invalidation()
    assert discarded.voided is True
    assert discarded.status == "stale"
    assert renewed.status == "fresh"
    assert renewed.validity_basis is not None

    before = store.list_latch_rows(claim_id="c-disputed")
    opened = read_disputed_reopen(store, "c-disputed")
    after = store.list_latch_rows(claim_id="c-disputed")
    assert before == after
    assert opened["reopenable"] is True
    assert opened["conclusion"] == conclusion
    assert opened["audit_trail"][0]["action"] == "disputed"
    assert opened["audit_trail"][0]["label"] == "人审改账"
    assert opened["audit_trail"][0]["reviewer_note"] == conclusion

    again = apply_decisions(
        store, claims,
        [{"claim_id": "c-disputed", "action": "disputed", "reviewer_note": conclusion}],
        now=_now_factory(),
    )
    assert again[0]["ok"] is True
    assert len(store.list_latch_rows(claim_id="c-disputed")) == 1

    for banned in ("找不到", "找错", "没用上"):
        assert banned not in VALID_ACTIONS


def test_graph_disputed_reopen_does_not_close_claim(tmp_path, monkeypatch):
    """人审图 execute 接受 disputed。再打开见结论;主张仍可进入下一轮。"""
    store = SQLiteStore(tmp_path / "graph.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
    claim = Claim(claim_id="c-d", statement="定价仍为 299", status="unknown", reason="机器未知")
    appmod._state.update({
        "claims": [claim],
        "question": "",
        "trajectory": None,
        "running": False,
        "latch": dict(appmod.EMPTY_LATCH),
    })
    client = TestClient(appmod.app)
    rnd = appmod._latch().enter_round([claim])
    assert rnd.waiting
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
    conclusion = "检索空,但人认为查询词偏了"
    response = client.post("/api/latch/decide", json={
        "thread_id": rnd.thread_id,
        "decisions": [{
            "claim_id": "c-d",
            "action": "disputed",
            "reviewer_note": conclusion,
        }],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["ok"] is True
    assert body["results"][0]["action"] == "disputed"
    assert claim.status == "unknown"
    assert claim.voided is False
    assert claim.validity_basis is None
    assert "c-d" not in store.list_invalidation()
    ledger = body["claim_ledger"]
    assert "c-d" in ledger["disputed_claim_ids"]
    assert "c-d" not in ledger["invalidation_claim_ids"]
    opened = client.get("/api/latch/reopen", params={"claim_id": "c-d"})
    assert opened.status_code == 200
    view = opened.json()
    assert view["reopenable"] is True
    assert view["conclusion"] == conclusion
    assert any(row["action"] == "disputed" for row in view["audit_trail"])
    nxt = appmod._latch().enter_round([claim])
    assert nxt.waiting
    assert any(item["claim_id"] == "c-d" for item in nxt.pending)


def test_run_loop_has_no_langgraph_and_context_splits_buckets():
    """验收 3: run_loop 不引进 langgraph。词表写明产品桶 ≠ ADR-0028。"""
    for path in (LOOP_PATH, RUNNER_PATH):
        source = path.read_text(encoding="utf-8")
        assert "disputed" not in source
        tree = ast.parse(source)
        modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
        assert modules
        assert not any("langgraph" in name for name in modules)
    text = CONTEXT_PATH.read_text(encoding="utf-8")
    assert "产品失败三桶 ≠ ops ADR-0028 评测桶" in text
    assert "docs/ops/挂标-失败归因三桶.md" in text
    assert "tool_tier_0" in text and "tool_tier_1" in text and "tool_tier_2" in text
