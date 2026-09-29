"""#200 复验单 Evidence-bound 补丁条带 UI 验收。

零 LLM:HTML 入口闸 + propose/confirm/discard API 端点契约。
无薄对话、无独立补丁台、无 C|T 开关;discard/renew 回归见 test_ui_latch。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.evidence_bound import PatchDraftStore
from freshlatch.gates.human_latch import VALID_ACTIONS
from freshlatch.models import Claim
from freshlatch.store.base import Chunk, Document, chunk_evidence_id


ARCHIVED_DOC = "ui-t1-arch"
ARCHIVED_CLAUSE = "p1"
ARCHIVED_EID = f"{ARCHIVED_DOC}#{ARCHIVED_CLAUSE}@T1"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
    appmod._PATCH_DRAFTS = PatchDraftStore()
    appmod._state.update({
        "claims": [],
        "question": "",
        "trajectory": None,
        "running": False,
        "latch": dict(appmod.EMPTY_LATCH),
        "active_run_id": "run-ui-200",
    })
    return TestClient(appmod.app)


def _seed_archived_t1(store) -> str:
    """写入一条本 Run 已入库 T1,供多选/硬闸。"""
    text = f"## {ARCHIVED_CLAUSE}\nUI 补丁条带锚词:已入库 T1。"
    store.add_document(
        Document(
            doc_id=ARCHIVED_DOC,
            as_of="T1",
            source_type="private",
            title="UI T1",
            doc_version="1.0",
            checksum="abc",
            full_text=text,
        ),
        [
            Chunk(
                doc_id=ARCHIVED_DOC,
                chunk_id=f"{ARCHIVED_DOC}::{ARCHIVED_CLAUSE}@T1",
                clause_id=ARCHIVED_CLAUSE,
                title="UI T1",
                text=text,
                source_type="private",
                as_of="T1",
                doc_version="1.0",
                checksum="abc",
                tokens=8,
            )
        ],
    )
    return ARCHIVED_EID


def _seed_claims(*, include_fresh: bool = True) -> list[Claim]:
    claims = [
        Claim(claim_id="c-unk", statement="缺口主张原文", status="unknown", reason="证据不足"),
        Claim(claim_id="c-stale", statement="已失效主张", status="stale", reason="T1 推翻"),
        Claim(claim_id="c-void", statement="已作废主张", status="stale", reason="人审", voided=True),
    ]
    if include_fresh:
        claims.append(Claim(claim_id="c-fresh", statement="仍成立", status="fresh", reason="ok"))
    appmod._state["claims"] = claims
    return claims


# -- HTML 交互件(红线)----------------------------------------------------------------


def test_patch_strip_ui_present_no_thin_chat_no_ct_switch():
    """Given 复验单 HTML,Then 有改稿/确认/再验条带入口,无薄对话与 C|T 开关。"""
    html = appmod.HTML_PAGE
    assert "改稿 · 确认 · 再验" in html
    assert "confirmPatchClaim" in html
    assert "proposePatchDraft" in html
    assert "discardPatchDraft" in html
    assert "/api/patch/confirm" in html
    assert "/api/patch/propose" in html
    assert "patch-t1-" in html  # 本 Run 已入库 t1 多选
    assert "工时 minutes" in html
    # 无聊天端点 / 编排角色名 / 发前臂开关控件
    for forbidden in (
        "/api/chat",
        "ask_human",
        "approve_promotion",
        "Orchestrator",
        'id="arm-toggle"',
        "C vs T",
        "独立补丁台",
    ):
        assert forbidden not in html
    # discard/renew 入口保持
    assert 'id="renew-modal"' in html
    assert "confirmVoid" in html
    assert "confirmRenew" in html


def test_prepublish_list_has_no_patch_workbench():
    """列表页只消费 disposition,不另造补丁工作台。"""
    html = appmod.PREPUBLISH_HTML
    assert "/api/patch/" not in html
    assert "改稿" not in html
    assert "confirmPatchClaim" not in html


# -- 投影 / 资格 ----------------------------------------------------------------------


def test_claims_exposes_patch_eligible_and_archived_t1(client):
    """详情 /api/claims 暴露 patch_eligible 与 archived_t1_ids。"""
    _seed_archived_t1(appmod._store())
    _seed_claims()
    j = client.get("/api/claims").json()
    assert ARCHIVED_EID in j["archived_t1_ids"]
    by_id = {c["claim_id"]: c for c in j["claims"]}
    assert by_id["c-unk"]["patch_eligible"] is True
    assert by_id["c-stale"]["patch_eligible"] is True
    assert by_id["c-fresh"]["patch_eligible"] is False
    assert by_id["c-void"]["patch_eligible"] is False


# -- API 端点 -------------------------------------------------------------------------


def test_propose_then_discard_draft_zero_mutation(client):
    """暂存草案不改正文;丢弃后草案清除。"""
    _seed_claims()
    before = appmod._state["claims"][0].statement
    r = client.post(
        "/api/patch/propose",
        json={"claim_id": "c-unk", "after_text": "新改稿句", "t1_ids": [ARCHIVED_EID]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["patch_drafts"]["c-unk"]["after_text"] == "新改稿句"
    assert appmod._state["claims"][0].statement == before

    d = client.post("/api/patch/discard-draft", json={"claim_id": "c-unk"})
    assert d.status_code == 200
    assert d.json()["discarded"] is True
    assert "c-unk" not in d.json()["patch_drafts"]
    assert appmod._state["claims"][0].statement == before


def test_confirm_with_archived_t1_covers_statement(client):
    """Given 合法 after_text + 已入库 t1,When confirm,Then 覆盖正文且走 confirm 成功路径。"""
    eid = _seed_archived_t1(appmod._store())
    assert eid == chunk_evidence_id(appmod._store().get_chunk(ARCHIVED_DOC, ARCHIVED_CLAUSE, as_of="T1"))
    _seed_claims()
    r = client.post(
        "/api/patch/confirm",
        json={
            "claim_id": "c-unk",
            "after_text": "经 T1 核后的主张句",
            "t1_ids": [eid],
            "minutes": 1.5,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["after_text"] == "经 T1 核后的主张句"
    assert body["reverify_requested"] is True
    assert body["disposition"] in ("可发", "需补丁", "勿发")
    unk = next(c for c in body["claims"] if c["claim_id"] == "c-unk")
    assert unk["statement"] == "经 T1 核后的主张句"
    assert eid in unk["t1_evidence_ids"]


def test_confirm_rejects_fresh_and_empty_t1(client):
    """fresh 或空 t1 → 拒确认且零改正文。"""
    _seed_archived_t1(appmod._store())
    claims = _seed_claims()
    fresh_before = next(c for c in claims if c.claim_id == "c-fresh").statement
    r1 = client.post(
        "/api/patch/confirm",
        json={
            "claim_id": "c-fresh",
            "after_text": "不该写上",
            "t1_ids": [ARCHIVED_EID],
            "minutes": 1,
        },
    )
    assert r1.status_code == 400
    assert r1.json()["error_code"] == "PATCH_INELIGIBLE"
    assert next(c for c in appmod._state["claims"] if c.claim_id == "c-fresh").statement == fresh_before

    unk_before = next(c for c in appmod._state["claims"] if c.claim_id == "c-unk").statement
    r2 = client.post(
        "/api/patch/confirm",
        json={"claim_id": "c-unk", "after_text": "无证改稿", "t1_ids": [], "minutes": 1},
    )
    assert r2.status_code == 400
    assert r2.json()["error_code"] == "PATCH_EMPTY_T1"
    assert next(c for c in appmod._state["claims"] if c.claim_id == "c-unk").statement == unk_before


def test_valid_actions_unchanged_by_patch_ui():
    """补丁另缝:HumanLatch VALID_ACTIONS 仍仅 discard|renew。"""
    assert set(VALID_ACTIONS) == {"discard", "renew"}
