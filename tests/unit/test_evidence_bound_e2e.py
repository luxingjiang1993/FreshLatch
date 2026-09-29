"""#202 V1.5 Evidence-bound 主缝 e2e(ADR-0029 Exit 预锁脚本)。

层身份:冒烟 / 对客 demo(零 LLM CI)。不报方差,不作 C vs T 显著。
预锁脚本(禁事后改期望凑绿):
  discard mck-1 与 mck-4 → 包结论「需补丁」→ 对 mck-3 表单/API 补丁 confirm
  → 单条再验触发 → 导出包存在。

硬条四勾(硬 Exit):无证拒确认 · 有证 confirm · reverify=true/单条再验 · 导出存在。
升「可发」仅为加分,非硬 Exit。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch import patch_events as pe
from freshlatch.disposition import DISPOSITIONS
from freshlatch.evidence_bound import (
    PATCH_EMPTY_T1,
    PatchDraftStore,
    confirm_patch,
    propose_patch,
)
from freshlatch.evidence_bound_export import REQUIRED_JSON_KEYS
from freshlatch.gates.human_latch import VALID_ACTIONS
from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import Claim
from freshlatch.packs import repo_root
from freshlatch.prepublish import disposition_for_claims
from freshlatch.runner import load_docket
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.t1_source import ALLOWED_URL_HOST, HttpGetResult

PACK_ID = "v1-mck-soai"
PACK_DIR = repo_root() / "data" / "packs" / PACK_ID
WHITELIST_URL = (
    f"https://{ALLOWED_URL_HOST}/capabilities/quantumblack/our-insights/state-of-ai"
)
T1_ANCHOR = (
    "公开洞察写明:88 percent report regular AI use in at least one business function。"
    "Twenty-three percent are scaling an agentic AI system。"
)

# -- 预锁脚本(ADR-0029 §8 / V15-Q14;抽检前写死,禁止事后改期望凑绿) ---------------
# 初始主张态同 V1 PREREG:未收口 stale → 勿发;
# 对人审范围仅 discard mck-1 与 mck-4 → 剩 mck-3 unknown → 需补丁;
# 再对 mck-3 Evidence-bound 补丁(硬条),升可发仅加分。
PRELOCK = {
    "case_id": "v15-evidence-bound-prelock-mck-soai",
    "claim_outcomes": {
        "mck-1": {"status": "stale", "t1_evidence_ids": ["mck-soai-agents-2025-11#p2@T1"]},
        "mck-2": {"status": "fresh", "t1_evidence_ids": ["mck-soai-agents-2025-11#p4@T1"]},
        "mck-3": {"status": "unknown", "t1_evidence_ids": []},
        "mck-4": {"status": "stale", "t1_evidence_ids": ["mck-soai-agents-2025-11#p3@T1"]},
    },
    "initial_disposition": "勿发",
    "after_discard_mck1_mck4": "需补丁",
    "discard_claim_ids": ("mck-1", "mck-4"),
    "patch_claim_id": "mck-3",
    "after_text": "经已入库 T1 核后的缺口主张改写句(Evidence-bound 冒烟)。",
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


def _fresh_reverify(claim: Claim) -> tuple[str, str]:
    """夹具:确定性把目标主张打成 fresh(零 LLM;加分勾用)。"""
    claim.status = "fresh"
    claim.reason = "fixture single-claim reverify (v15 e2e)"
    return "fresh", "fixture-to-fresh"


def _noop_reverify(claim: Claim) -> tuple[str, str]:
    """夹具:不改主张态,只证明再验回调被调用。"""
    return claim.status, "fixture-noop"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "CORPUS", tmp_path / "corpus")
    (tmp_path / "corpus" / "t1").mkdir(parents=True)
    events_dir = tmp_path / "patch_events"
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", events_dir)
    # 零 LLM:confirm 再验钩子不进 Runner/托管端点
    monkeypatch.setattr(
        appmod,
        "_confirm_patch_reverify",
        lambda claim: _fresh_reverify(claim),
    )
    appmod._PATCH_DRAFTS = PatchDraftStore()
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
        "active_run_id": "run-v15-202",
    })
    sess = appmod._reset_t1_source(store)

    def _fixture_get(url: str, timeout: float) -> HttpGetResult:
        html = (
            "<!DOCTYPE html><html><head><title>SoAI</title></head><body>"
            f"<h1>State of AI</h1><p>{T1_ANCHOR}</p></body></html>"
        )
        return HttpGetResult(
            ok=True,
            status=200,
            content_type="text/html; charset=utf-8",
            body=html.encode("utf-8"),
        )

    sess.http_get = _fixture_get
    return TestClient(appmod.app), events_dir, store


# ---------------------------------------------------------------------------
# 主缝:预锁脚本(HTTP 人审 + API 补丁;夹具再验)
# ---------------------------------------------------------------------------


def test_v15_prelock_main_seam_hard_bars(client):
    """Given 预锁脚本路径,When discard mck-1&4 → patch mck-3 → confirm,
    Then 硬条四勾可引用为 pass;升可发仅为加分。
    """
    http, events_dir, store = client
    assert PACK_DIR.is_dir()

    # 1) 主张集:顾问样例包
    claims = _load_sample_claims()
    assert {c.claim_id for c in claims} >= {"mck-1", "mck-2", "mck-3", "mck-4"}
    docket_q = json.loads((PACK_DIR / "docket.json").read_text(encoding="utf-8"))[
        "question"
    ]
    appmod._state["claims"] = claims
    appmod._state["question"] = docket_q

    # 2) 合法 T1:夹具薄 URL 入库(供 ⊆ 硬闸)
    r_url = http.post("/api/t1-source/url", json={"url": WHITELIST_URL})
    assert r_url.status_code == 200, r_url.text
    assert r_url.json()["ready"] is True
    from freshlatch.prepublish import list_archived_t1_evidence_ids

    archived = list_archived_t1_evidence_ids(store)
    assert archived, "夹具薄 URL 须落至少一条已入库 T1"
    t1_id = archived[0]

    # 3) 复验/规则闸(零 LLM 预登记结局)→ 初始勿发
    _apply_rule_gate_outcomes(claims, PRELOCK["claim_outcomes"])
    disp0 = disposition_for_claims(claims)
    assert disp0 == PRELOCK["initial_disposition"] == "勿发"
    assert disp0 in DISPOSITIONS
    row = appmod._sync_prepublish(new_run=True)
    assert row["disposition"] == disp0

    # 4) 人审:仅 discard mck-1 与 mck-4(预锁;不 discard mck-3)
    rnd = appmod._latch().enter_round(claims)
    assert rnd.waiting
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
    appmod._sync_prepublish(new_run=False)

    decisions = [
        {"claim_id": cid, "action": "discard"} for cid in PRELOCK["discard_claim_ids"]
    ]
    r_dec = http.post(
        "/api/latch/decide",
        json={"thread_id": rnd.thread_id, "decisions": decisions},
    )
    assert r_dec.status_code == 200, r_dec.text
    body = r_dec.json()
    assert all(x.get("ok") for x in body["results"])
    # 包结论至「需补丁」(剩 mck-3 unknown;非硬绑可发)
    assert body["disposition"] == PRELOCK["after_discard_mck1_mck4"] == "需补丁"
    assert disposition_for_claims(claims) == "需补丁"
    mck3 = next(c for c in claims if c.claim_id == "mck-3")
    assert mck3.voided is False
    assert mck3.status == "unknown"
    before_text = mck3.statement

    # ---- 硬条 1:无证拒确认 + 零改正文零写正式账本 ----
    before_n = len(pe.read_events(events_dir=events_dir))
    r_reject = http.post(
        "/api/patch/confirm",
        json={
            "claim_id": PRELOCK["patch_claim_id"],
            "after_text": PRELOCK["after_text"],
            "t1_ids": [],
            "minutes": 5.0,
        },
    )
    assert r_reject.status_code == 400, r_reject.text
    rej = r_reject.json()
    assert rej["ok"] is False
    assert rej["error_code"] == PATCH_EMPTY_T1
    assert mck3.statement == before_text
    assert len(pe.read_events(events_dir=events_dir)) == before_n
    assert rej.get("reverify_triggered") in (False, None)

    # ---- 硬条 2+3+4:有证 propose → confirm → reverify → 导出 ----
    r_prop = http.post(
        "/api/patch/propose",
        json={
            "claim_id": PRELOCK["patch_claim_id"],
            "after_text": PRELOCK["after_text"],
            "t1_ids": [t1_id],
        },
    )
    assert r_prop.status_code == 200, r_prop.text
    assert r_prop.json()["ok"] is True
    assert mck3.statement == before_text  # propose 零改正文

    r_ok = http.post(
        "/api/patch/confirm",
        json={
            "claim_id": PRELOCK["patch_claim_id"],
            "minutes": 11.0,
            # after_text / t1_ids 可从草案取;显式再传一遍更可读
            "after_text": PRELOCK["after_text"],
            "t1_ids": [t1_id],
        },
    )
    assert r_ok.status_code == 200, r_ok.text
    ok_body = r_ok.json()
    assert ok_body["ok"] is True
    assert mck3.statement == PRELOCK["after_text"]
    assert ok_body["before_text"] == before_text
    assert ok_body["after_text"] == PRELOCK["after_text"]

    # 硬条 3:单条再验触发 + 正式事件 reverify=true
    assert ok_body["reverify_requested"] is True
    assert ok_body["reverify_triggered"] is True
    assert ok_body["reverify_verdict"] == "fresh"
    rows = pe.read_events(events_dir=events_dir)
    patch_rows = [r for r in rows if r.get("claim_id") == "mck-3" and r.get("arm") == "T"]
    assert patch_rows, "须有产品路径 T 臂 patch_events 行"
    last = patch_rows[-1]
    assert last["reverify"] is True
    assert last["human_confirm"] is True
    assert last["before_text"] == before_text
    assert last["after_text"] == PRELOCK["after_text"]
    assert t1_id in last["t1_ids"]

    # 硬条 4:导出包存在(JSON + 短 MD 关键字段)
    export = ok_body.get("export")
    assert export is not None
    payload = export["json_payload"]
    for key in REQUIRED_JSON_KEYS:
        assert key in payload, f"导出 JSON 缺关键字段: {key}"
    assert export.get("markdown")
    assert "mck-3" in export["markdown"] or PRELOCK["after_text"] in export["markdown"]

    # 加分(非硬 Exit):夹具再验后包结论可升「可发」
    bonus_ke_fa = ok_body.get("disposition") == "可发"
    assert disposition_for_claims(claims) == ok_body["disposition"]
    # 记录加分结果供 ACCEPTANCE 引用;本断言不把「可发」绑成硬失败
    assert bonus_ke_fa or ok_body["disposition"] in DISPOSITIONS


def test_v15_prelock_library_fixture_equivalent(tmp_path: Path):
    """夹具等价路径(不经 HTTP):同一预锁脚本,硬条四勾可引用。

    discard 以 voided=True 夹具等价(真人审走 test_v15_prelock_main_seam_hard_bars)。
    """
    claims = _load_sample_claims()
    _apply_rule_gate_outcomes(claims, PRELOCK["claim_outcomes"])
    assert disposition_for_claims(claims) == "勿发"

    by_id = {c.claim_id: c for c in claims}
    for cid in PRELOCK["discard_claim_ids"]:
        by_id[cid].voided = True
    assert disposition_for_claims(claims) == "需补丁"

    events_dir = tmp_path / "patch_events"
    archived = {"mck-soai-agents-2025-11#p3@T1"}
    mck3 = by_id["mck-3"]
    before = mck3.statement

    # 硬条 1
    rej = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids=archived,
        after_text=PRELOCK["after_text"],
        t1_ids=[],
        minutes=1.0,
        events_dir=events_dir,
        claim_list=claims,
        reverify_fn=_noop_reverify,
    )
    assert not rej.ok and rej.error_code == PATCH_EMPTY_T1
    assert mck3.statement == before
    assert pe.read_events(events_dir=events_dir) == []

    # 硬条 2–4(+加分再验夹具)
    drafts = PatchDraftStore()
    prop = propose_patch(
        claim_id="mck-3",
        after_text=PRELOCK["after_text"],
        claims=claims,
        drafts=drafts,
        run_id="v15-lib",
        t1_ids=list(archived),
    )
    assert prop.ok
    ok = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids=archived,
        minutes=7.0,
        drafts=drafts,
        run_id="v15-lib",
        events_dir=events_dir,
        claim_list=claims,
        reverify_fn=_fresh_reverify,
    )
    assert ok.ok
    assert mck3.statement == PRELOCK["after_text"]
    assert ok.reverify_requested and ok.reverify_triggered
    assert pe.read_events(events_dir=events_dir)[0]["reverify"] is True
    assert ok.export is not None
    for key in REQUIRED_JSON_KEYS:
        assert key in ok.export.json_payload
    assert ok.export.markdown
    # 加分:升可发(非硬 Exit;本夹具可演示)
    assert ok.disposition == "可发"


# ---------------------------------------------------------------------------
# 回归护栏(本票不改生产默认臂 / 不扩 latch)
# ---------------------------------------------------------------------------


def test_v15_valid_actions_and_default_arm_unchanged():
    """HumanLatch 仍仅 discard|renew;生产默认臂仍 bm25。"""
    assert VALID_ACTIONS == ("discard", "renew")
    assert "confirm_patch" not in VALID_ACTIONS
    assert PRODUCTION_RETRIEVAL_MODE == "bm25"


def test_v15_prelock_constants_match_adr0029():
    """预锁常量自检:禁 HARKing——脚本步骤与 ADR-0029 一致。"""
    assert PRELOCK["discard_claim_ids"] == ("mck-1", "mck-4")
    assert PRELOCK["patch_claim_id"] == "mck-3"
    assert PRELOCK["after_discard_mck1_mck4"] == "需补丁"
    assert PRELOCK["initial_disposition"] == "勿发"
    assert (PACK_DIR / "docket.json").is_file()
