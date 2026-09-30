"""#231 V2 发前钩子冒烟 e2e(ADR-0031 Exit 预锁脚本)。

层身份:冒烟 / 采用层(零 LLM CI)。不报采用率/方差;不硬绑包结论「可发」;
curl(或 TestClient)≠ 插件/webhook 平台已交付。

预锁脚本(禁事后改期望凑绿 / HARKing):
  样例包主张态 → 勿发 → 入站 check deny + Memo 闸拒零写
  → 人审 discard mck-1 + renew mck-4 → 台账可见两 claim_id
  → 包结论至需补丁(非硬绑可发)→ ack 后 check allow + Memo 放行标「需补丁」。

硬条(硬 Exit):Memo 闸正确 · curl/TestClient allow≥1 ∧ deny≥1 · 台账 discard/renew。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.disposition import DISPOSITIONS
from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import Claim
from freshlatch.packs import repo_root
from freshlatch.prepublish import disposition_for_claims
from freshlatch.publish_hook import (
    HOOK_DO_NOT_PUBLISH,
    HOOK_NEEDS_PATCH_NO_ACK,
    HOOK_OK,
    NEEDS_PATCH_BANNER,
)
from freshlatch.runner import load_docket
from freshlatch.store.ingest import ingest_into

PACK_ID = "v1-mck-soai"
PACK_DIR = repo_root() / "data" / "packs" / PACK_ID
PACK_CORPUS = PACK_DIR / "corpus"
RENEW_EID = "mck-soai-agents-2025-11#p3@T1"

# -- 预锁脚本(ADR-0031 §5 / 评估 Q19;抽检前写死,禁止事后改「什么算点到」) ----------
PRELOCK = {
    "case_id": "v2-publish-hook-prelock-mck-soai",
    "claim_outcomes": {
        "mck-1": {
            "status": "stale",
            "t1_evidence_ids": ["mck-soai-agents-2025-11#p2@T1"],
        },
        "mck-2": {
            "status": "fresh",
            "t1_evidence_ids": ["mck-soai-agents-2025-11#p4@T1"],
        },
        "mck-3": {"status": "unknown", "t1_evidence_ids": []},
        "mck-4": {
            "status": "stale",
            "t1_evidence_ids": [RENEW_EID],
        },
    },
    "initial_disposition": "勿发",
    "after_human_review": "需补丁",
    "discard_claim_id": "mck-1",
    "renew_claim_id": "mck-4",
    "renew_evidence_id": RENEW_EID,
}


def _load_sample_claims() -> list[Claim]:
    docket = load_docket(PACK_DIR / "docket.json")
    return list(docket.claims)


def _apply_rule_gate_outcomes(claims: list[Claim], outcomes: dict) -> None:
    """零 LLM:按预登记结局走规则闸后写回主张态。"""
    ctx = GateContext(checksum_fn=lambda doc_id, as_of: None)
    for c in claims:
        o = outcomes[c.claim_id]
        status = o["status"]
        t1_ids = list(o.get("t1_evidence_ids") or [])
        decision = GateDecision(
            status=status,
            t1_evidence_ids=t1_ids,
            auditor_verdict=status if status != "unknown" else "unknown",
        )
        gate = rule_gate(c, decision, ctx)
        if gate.allowed:
            c.status = status
            c.t1_evidence_ids = t1_ids
            c.reason = o.get("reason") or f"闸放行:{status}"
        else:
            c.status = "unknown"
            c.reason = f"[闸打回:{gate.error_code}] {gate.reason}"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """发前主缝夹具:样例包语料入库 + 真 checksum_fn(供 renew)。"""
    store = appmod.SQLiteStore(tmp_path / "t.db")
    corpus = tmp_path / "corpus"
    shutil.copytree(PACK_CORPUS, corpus)
    assert ingest_into(store, corpus) >= 1
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    # HumanLatch 经 _latch() 读 CORPUS 现算 checksum;与入库指纹对齐
    monkeypatch.setattr(appmod, "CORPUS", corpus)
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
    appmod._prepublish.clear()
    appmod._state.update({
        "claims": [],
        "question": "",
        "trajectory": None,
        "running": False,
        "latch": dict(appmod.EMPTY_LATCH),
        "budget": dict(appmod.EMPTY_BUDGET),
        "run_ctx": None,
        "retrieve_zero_hits": [],
        "active_run_id": None,
        "bound_t1_checksums": {},
    })
    appmod._reset_t1_source(store)
    return TestClient(appmod.app), store, tmp_path


def test_v2_prelock_main_seam_hard_bars(client):
    """Given ADR-0031 预锁脚本,When 跑通人审+三出口,Then 硬条可勾且不硬绑可发。"""
    http, store, tmp_path = client
    assert PACK_DIR.is_dir()
    assert PACK_CORPUS.is_dir()

    # 1) 顾问样例包主张集
    claims = _load_sample_claims()
    assert {c.claim_id for c in claims} >= {"mck-1", "mck-2", "mck-3", "mck-4"}
    docket_q = json.loads((PACK_DIR / "docket.json").read_text(encoding="utf-8"))[
        "question"
    ]
    appmod._state["claims"] = claims
    appmod._state["question"] = docket_q

    # 2) 零 LLM 预登记结局 → 初始勿发;钉发前 Run
    _apply_rule_gate_outcomes(claims, PRELOCK["claim_outcomes"])
    disp0 = disposition_for_claims(claims)
    assert disp0 == PRELOCK["initial_disposition"] == "勿发"
    assert disp0 in DISPOSITIONS
    row = appmod._sync_prepublish(new_run=True)
    run_id = row["run_id"]
    assert run_id
    assert row["disposition"] == disp0
    assert appmod._state["active_run_id"] == run_id

    # ---- 硬条:入站 check deny≥1(勿发;TestClient ≡ curl) ----
    r_deny = http.post("/api/publish-hook/check", json={"run_id": run_id})
    assert r_deny.status_code in (403, 409), r_deny.text
    deny_body = r_deny.json()
    assert deny_body["allow"] is False
    assert deny_body["disposition"] == "勿发"
    assert deny_body["code"] == HOOK_DO_NOT_PUBLISH

    # ---- 硬条:Memo 闸拒(勿发 → 零写 / 403 JSON) ----
    r_memo_deny = http.post("/api/client-memo/export")
    assert r_memo_deny.status_code == 403, r_memo_deny.text
    memo_deny = r_memo_deny.json()
    assert memo_deny["allow"] is False
    assert memo_deny["code"] == HOOK_DO_NOT_PUBLISH
    # HTTP 路径不落盘;确认响应非 Markdown
    assert "客户向复验备忘" not in (r_memo_deny.text or "")

    # CLI 同闸零写(对照 #229)
    from freshlatch.sheet import export_client_memo_gated, project_claim

    out_cli = tmp_path / "should_not_exist.md"
    hook_cli, md_cli = export_client_memo_gated(
        run_id=run_id,
        disposition="勿发",
        projections=[project_claim(store, c) for c in claims],
        generated_at="2026-09-30T00:00:00Z",
        out_path=out_cli,
    )
    assert hook_cli.allow is False
    assert hook_cli.code == HOOK_DO_NOT_PUBLISH
    assert md_cli is None
    assert not out_cli.exists()

    # 3) 人审:discard mck-1 + renew mck-4(预锁;不 discard mck-3)
    rnd = appmod._latch().enter_round(claims)
    assert rnd.waiting
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
    appmod._sync_prepublish(new_run=False)

    decisions = [
        {"claim_id": PRELOCK["discard_claim_id"], "action": "discard"},
        {
            "claim_id": PRELOCK["renew_claim_id"],
            "action": "renew",
            "evidence_id": PRELOCK["renew_evidence_id"],
        },
    ]
    r_dec = http.post(
        "/api/latch/decide",
        json={"thread_id": rnd.thread_id, "decisions": decisions},
    )
    assert r_dec.status_code == 200, r_dec.text
    body = r_dec.json()
    assert all(x.get("ok") for x in body["results"]), body["results"]
    # 包结论至「需补丁」(剩 mck-3 unknown);**非**硬绑可发
    assert body["disposition"] == PRELOCK["after_human_review"] == "需补丁"
    assert disposition_for_claims(claims) == "需补丁"
    assert disposition_for_claims(claims) != "可发"  # 本硬条路径不要求可发
    mck1 = next(c for c in claims if c.claim_id == "mck-1")
    mck4 = next(c for c in claims if c.claim_id == "mck-4")
    assert mck1.voided is True
    assert mck4.status == "fresh"
    assert PRELOCK["renew_evidence_id"] in mck4.t1_evidence_ids

    # ---- 硬条:台账可见本次 discard/renew claim_id ----
    ledger = http.get("/api/claim-ledger").json()
    assert PRELOCK["discard_claim_id"] in ledger["discard_claim_ids"]
    assert PRELOCK["renew_claim_id"] in ledger["renew_claim_ids"]
    # renew 不进作废名单
    assert PRELOCK["renew_claim_id"] not in ledger["invalidation_claim_ids"]
    assert PRELOCK["discard_claim_id"] in ledger["invalidation_claim_ids"]
    md = http.get("/api/claim-ledger/export.md")
    assert md.status_code == 200
    md_text = md.text
    assert PRELOCK["discard_claim_id"] in md_text
    assert PRELOCK["renew_claim_id"] in md_text

    # 需补丁无 ack → check 仍 deny(对照;计入 deny 语义,不另计硬条)
    r_np = http.post(
        "/api/publish-hook/check",
        json={"run_id": run_id, "ack_needs_patch": False},
    )
    assert r_np.status_code == 409
    assert r_np.json()["code"] == HOOK_NEEDS_PATCH_NO_ACK
    assert r_np.json()["allow"] is False

    # ---- 硬条:入站 check allow≥1(需补丁+ack;仍不升格「可发」) ----
    r_allow = http.post(
        "/api/publish-hook/check",
        json={"run_id": run_id, "ack_needs_patch": True},
    )
    assert r_allow.status_code == 200, r_allow.text
    allow_body = r_allow.json()
    assert allow_body["allow"] is True
    assert allow_body["disposition"] == "需补丁"
    assert allow_body["code"] == HOOK_OK
    assert allow_body["requires_needs_patch_banner"] is True

    # ---- 硬条:Memo 闸放行(ack)且页眉「需补丁」;ADR-0015 无商业裁决 ----
    r_memo_ok = http.post("/api/client-memo/export?ack_needs_patch=true")
    assert r_memo_ok.status_code == 200, r_memo_ok.text
    memo_text = r_memo_ok.text
    assert NEEDS_PATCH_BANNER in memo_text
    assert "客户向复验备忘" in memo_text
    # 与 #229 同构:禁语只查 DEM-3 前正文(页脚可声明「禁止项」字样)
    body = memo_text.split("## DEM-3")[0] if "## DEM-3" in memo_text else memo_text
    assert "建议进入" not in body and "建议不进入" not in body
    assert "Lead" not in body and "Critic" not in body
    assert r_memo_ok.headers.get("X-FreshLatch-Hook-Code") == HOOK_OK
    assert r_memo_ok.headers.get("X-FreshLatch-Needs-Patch-Banner") == "1"

    # 护栏:本路径未把「可发」写成硬失败条件
    assert allow_body["disposition"] in DISPOSITIONS
    assert allow_body["disposition"] != "可发"


def test_v2_acceptance_doc_smoke_layer_and_hard_bars():
    """ACCEPTANCE 文首冒烟采用层 + 硬条可勾且无「必须可发」。"""
    path = repo_root() / "docs" / "evidence" / "v2" / "ACCEPTANCE.md"
    assert path.is_file(), "须落盘 docs/evidence/v2/ACCEPTANCE.md"
    text = path.read_text(encoding="utf-8")
    # 文首冒烟/采用层声明
    head = text[:800]
    assert "冒烟" in head
    assert "采用层" in head or "采用" in head
    assert "Hard-Gold" in head or "不是 Hard-Gold" in text
    # 硬条区
    assert "Memo" in text
    assert "allow" in text.lower() and "deny" in text.lower()
    assert "discard" in text and "renew" in text
    # 禁升格
    assert "采用率" in text  # 须显式声明不报
    assert "不报采用率" in text or "禁止" in text and "采用率" in text
    assert "可发" in text
    # 不得把「必须可发」写成硬条勾选条件
    assert "必须可发" not in text
    assert "硬绑" in text or "不硬绑" in text
    assert "webhook" in text.lower() or "插件" in text
    # 权威复跑含 compileall / pytest / curl(或等价说明)
    assert "compileall" in text
    assert "test_v2_publish_hook_e2e" in text
    assert "curl" in text.lower() or "TestClient" in text
