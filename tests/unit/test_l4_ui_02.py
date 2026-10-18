"""L4-UI-02: 职人视图 UiBadge(verified | partial | abstain)绑真闸。

TestClient 读 HTML,不开浏览器,不调用付费 LLM。
夹具轨迹只放在本文件生成的 tmp 路径。徽章是只读投影,不写 Claim.status。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import get_args

from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.gates.rule_gate import GateResult
from freshlatch.models import Claim, Status
from freshlatch.roles.loop import ABSTENTION_REASONS
from freshlatch.roles.retrieve_sufficiency import REASON_INSUFFICIENT_EVIDENCE
from freshlatch.sheet import project_audit, project_ui_badges
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

EVIDENCE_ID = "memo#p1@T1"
PARTIAL_ID = "memo#p2@T1"
_ROLE_NAMES = ("Lead", "Critic", "Auditor")
_STATUS_MEMBERS = frozenset({"fresh", "stale", "unknown", "void"})


def _write_jsonl(path: Path, events: list[dict]) -> None:
    lines = [json.dumps(event, ensure_ascii=False) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _badge_slot(html: str) -> str:
    marker = 'id="craftsman-badges"'
    assert marker in html
    return html.split(marker, 1)[1].split("</div>", 1)[0]


def _client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    saved = {
        "trajectory": appmod._state.get("trajectory"),
        "claims": list(appmod._state.get("claims") or []),
        "running": appmod._state.get("running"),
        "latch": dict(appmod._state.get("latch") or appmod.EMPTY_LATCH),
    }
    appmod._state["trajectory"] = None
    appmod._state["claims"] = []
    appmod._state["running"] = False
    appmod._state["latch"] = dict(appmod.EMPTY_LATCH)
    client = TestClient(appmod.app)
    return client, saved


def _restore(saved: dict) -> None:
    appmod._state["trajectory"] = saved["trajectory"]
    appmod._state["claims"] = saved["claims"]
    appmod._state["running"] = saved["running"]
    appmod._state["latch"] = saved["latch"]


def _verified_events() -> list[dict]:
    return [
        {
            "type": "lead_loop_end",
            "claim_id": "c-ok",
            "evidence_ids": [EVIDENCE_ID],
            "grade": "correct",
            "retry_count": 0,
            "abstained": False,
        },
        {
            "type": "claim_final",
            "claim_id": "c-ok",
            "statement": "本轮证据足以续验",
            "status": "fresh",
            "reason": "过闸:绿灯",
            "evidence_ids": [EVIDENCE_ID],
            "auditor_verdict": "fresh",
        },
    ]


def test_craftsman_verified_badge_keeps_fresh_status(tmp_path, monkeypatch):
    """验收 1: 闸允许的 fresh 在职人 HTML 里是 verified,status 仍是 fresh。"""
    path = tmp_path / "verified.jsonl"
    _write_jsonl(path, _verified_events())
    claim = Claim(
        claim_id="c-ok",
        statement="本轮证据足以续验",
        status="fresh",
        t1_evidence_ids=[EVIDENCE_ID],
    )
    projected = project_ui_badges(path, [claim])
    assert projected == [{"claim_id": "c-ok", "badge": "verified"}]
    assert claim.status == "fresh"
    assert project_audit(path)["badges"] == projected

    client, saved = _client(tmp_path, monkeypatch)
    try:
        appmod._state["trajectory"] = path
        appmod._state["claims"] = [claim]
        html = client.get("/").text
        slot = _badge_slot(html)
        assert 'class="badge verified"' in slot
        assert ">verified<" in slot
        assert 'class="badge partial"' not in slot
        assert 'class="badge abstain"' not in slot
        assert "__CRAFTSMAN_BADGES__" not in html
        body = client.get("/api/claims").json()
        assert body["claims"][0]["status"] == "fresh"
        assert body["claims"][0]["badge"] == "verified"
        assert body["claims"][0]["status"] != "verified"
        assert claim.status == "fresh"
    finally:
        _restore(saved)


def test_abstain_badge_not_shown_as_verified(tmp_path, monkeypatch):
    """验收 2: insufficient_evidence 投影为 abstain,不得显示为 verified。"""
    path = tmp_path / "abstain.jsonl"
    _write_jsonl(path, [
        {
            "type": "lead_loop_end",
            "claim_id": "c-no",
            "evidence_ids": [EVIDENCE_ID],
            "grade": None,
            "retry_count": 0,
            "abstained": True,
            "reason_code": REASON_INSUFFICIENT_EVIDENCE,
        },
        {
            "type": "claim_final",
            "claim_id": "c-no",
            "statement": "拒答优先",
            "status": "fresh",
            "reason": "夹具故意留着 fresh,徽章仍须 abstain",
            "evidence_ids": [EVIDENCE_ID],
            "auditor_verdict": "fresh",
        },
    ])
    claim = Claim(
        claim_id="c-no",
        statement="拒答优先",
        status="fresh",
        t1_evidence_ids=[EVIDENCE_ID],
    )
    assert REASON_INSUFFICIENT_EVIDENCE in ABSTENTION_REASONS
    projected = project_ui_badges(path, [claim])
    assert projected == [{"claim_id": "c-no", "badge": "abstain"}]
    assert claim.status == "fresh"

    client, saved = _client(tmp_path, monkeypatch)
    try:
        appmod._state["trajectory"] = path
        appmod._state["claims"] = [claim]
        html = client.get("/").text
        slot = _badge_slot(html)
        assert 'class="badge abstain"' in slot
        assert ">abstain<" in slot
        assert 'class="badge verified"' not in slot
        body = client.get("/api/claims").json()
        assert body["claims"][0]["badge"] == "abstain"
        assert body["claims"][0]["status"] == "fresh"
        assert body["claims"][0]["status"] != "abstain"
    finally:
        _restore(saved)


def test_partial_when_round_id_is_not_enough(tmp_path, monkeypatch):
    """验收 3: 有本轮 id,但未形成闸允许的 fresh → partial。"""
    path = tmp_path / "partial.jsonl"
    _write_jsonl(path, [
        {
            "type": "lead_loop_end",
            "claim_id": "c-part",
            "evidence_ids": [PARTIAL_ID],
            "grade": None,
            "retry_count": 0,
            "reason_code": None,
        },
    ])
    claim = Claim(
        claim_id="c-part",
        statement="有本轮 id,证据不全",
        status="unknown",
        t1_evidence_ids=[PARTIAL_ID],
    )
    projected = project_ui_badges(path, [claim])
    assert projected == [{"claim_id": "c-part", "badge": "partial"}]
    assert claim.status == "unknown"

    client, saved = _client(tmp_path, monkeypatch)
    try:
        appmod._state["trajectory"] = path
        appmod._state["claims"] = [claim]
        html = client.get("/").text
        slot = _badge_slot(html)
        assert 'class="badge partial"' in slot
        assert ">partial<" in slot
        assert 'class="badge verified"' not in slot
        assert 'class="badge abstain"' not in slot
        body = client.get("/api/claims").json()
        assert body["claims"][0]["badge"] == "partial"
        assert body["claims"][0]["status"] == "unknown"
    finally:
        _restore(saved)


def test_old_path_only_trajectory_renders_no_badge(tmp_path, monkeypatch):
    """验收 4: 旧轨迹只有路径、无解析字段时不编造三徽章。"""
    path = tmp_path / "only-path.txt"
    path.write_text(str(path), encoding="utf-8")
    assert project_ui_badges(path) == []
    assert project_audit(path)["badges"] == []
    assert project_audit(path)["parsed"] is False

    client, saved = _client(tmp_path, monkeypatch)
    try:
        appmod._state["trajectory"] = path
        html = client.get("/").text
        slot = _badge_slot(html)
        for kind in ("verified", "partial", "abstain"):
            assert f'class="badge {kind}"' not in slot
        assert "__CRAFTSMAN_BADGES__" not in html
    finally:
        _restore(saved)


def test_query_only_trajectory_does_not_invent_badge(tmp_path):
    """有查询、没有本轮 id / 拒答码 / fresh 记录时,badges 仍为空。"""
    path = tmp_path / "query-only.jsonl"
    _write_jsonl(path, [
        {"type": "retrieve", "query": "旧查询", "hits": 1},
    ])
    assert project_audit(path)["parsed"] is True
    assert project_ui_badges(path) == []


def test_stale_with_ids_is_not_partial(tmp_path):
    """stale 已有机器结论,不把反证 id 画成 partial。"""
    path = tmp_path / "stale.jsonl"
    _write_jsonl(path, [
        {
            "type": "claim_final",
            "claim_id": "c-stale",
            "status": "stale",
            "evidence_ids": [PARTIAL_ID],
            "auditor_verdict": "stale",
        },
    ])
    assert project_ui_badges(path) == []


def test_verified_follows_rule_gate(tmp_path, monkeypatch):
    """recorded fresh 若真闸不放行,不得投影 verified。"""
    path = tmp_path / "gate-block.jsonl"
    _write_jsonl(path, _verified_events())

    def _blocked(*_args, **_kwargs):
        return GateResult(
            allowed=False,
            green=False,
            error_code="AUDITOR_ABSENT",
            reason="stub",
        )

    monkeypatch.setattr("freshlatch.gates.rule_gate.rule_gate", _blocked)
    assert project_ui_badges(path) == [{"claim_id": "c-ok", "badge": "partial"}]


def test_human_verbs_status_enum_and_no_role_names(tmp_path, monkeypatch):
    """验收 5–6: 人审仍是 discard/renew;status 枚举不变;职人页无角色专名。"""
    assert set(get_args(Status)) == _STATUS_MEMBERS
    assert "disputed" not in set(get_args(Status))
    assert REASON_INSUFFICIENT_EVIDENCE in ABSTENTION_REASONS
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"

    path = tmp_path / "verified.jsonl"
    _write_jsonl(path, _verified_events())
    client, saved = _client(tmp_path, monkeypatch)
    try:
        appmod._state["trajectory"] = path
        appmod._state["claims"] = [
            Claim(claim_id="c-ok", statement="仍成立", status="fresh"),
        ]
        html = client.get("/").text
        assert "职人视图" in html
        assert 'id="view-craftsman" class="on"' in html
        for role in _ROLE_NAMES:
            assert role not in html
        assert "disputed" not in set(get_args(Status))
        assert "action:'disputed'" in html
        assert "action: 'discard'" in html or 'action: "discard"' in html
        assert "action:'renew'" in html or "action: 'renew'" in html or 'action:"renew"' in html
        assert "作废" in html
        assert "续命" in html
    finally:
        _restore(saved)


def test_i11_first_screen_reduction_keeps_badge_slot_and_verdict(tmp_path, monkeypatch):
    """I-11(#710):首屏降噪不动只读徽章槽与机器判定;职人仍无角色专名。"""
    path = tmp_path / "verified.jsonl"
    _write_jsonl(path, _verified_events())
    client, saved = _client(tmp_path, monkeypatch)
    try:
        appmod._state["trajectory"] = path
        appmod._state["claims"] = [
            Claim(claim_id="c-ok", statement="仍成立", status="fresh",
                  t1_evidence_ids=[EVIDENCE_ID]),
        ]
        html = client.get("/").text
        slot = _badge_slot(html)
        assert 'class="badge verified"' in slot
        # 主 CTA 与 T1 白话状态分支在职人首屏保留
        assert 'id="btn-run"' in html
        branch = '(VIEW_MODE === "audit") ? renderT1Source() : renderT1StatusShort()'
        assert branch in appmod.HTML_PAGE
        # 职人隐藏规则只藏噪音,不藏徽章槽/三类清单
        assert 'html[data-view="craftsman"] #craftsman-badges' not in appmod.HTML_PAGE
        assert 'id="vernacular-lists"' in html
        body = client.get("/api/claims").json()
        assert body["claims"][0]["status"] == "fresh"
        assert body["claims"][0]["badge"] == "verified"
    finally:
        _restore(saved)
