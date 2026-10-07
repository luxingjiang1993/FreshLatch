"""#174 发前主缝贯通冒烟(零 LLM CI)。

主缝:顾问样例包 + 合法 T1(夹具薄 URL) → 规则闸 → disposition → 人审
→ 发前列表/详情投影一致 + 至少一条 patch_events 可读 + T1 checksum 可追。

另含:ADR-0027 映射抽检 ≥1;thesis-1 / QuoteTTL 软 Port 不红且非第二垂直;
生产默认检索臂是 hybrid+rerank；空库记 bm25_fallback。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch import patch_events as pe
from freshlatch.disposition import DISPOSITIONS, ClaimDispositionInput, aggregate_disposition
from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import Claim
from freshlatch.packs import (
    DEFAULT_PACK_ID,
    KNOWN_PACK_IDS,
    P1_PACK_ID,
    repo_root,
    resolve_pack,
)
from freshlatch.prepublish import disposition_for_claims
from freshlatch.runner import load_docket
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.t1_source import ALLOWED_URL_HOST, HttpGetResult

PACK_ID = "v1-mck-soai"
PACK_DIR = repo_root() / "data" / "packs" / PACK_ID
WHITELIST_URL = (
    f"https://{ALLOWED_URL_HOST}/capabilities/quantumblack/our-insights/state-of-ai"
)
# 夹具正文须含可读文本,供薄 URL 切块落盘
T1_ANCHOR = (
    "公开洞察写明:88 percent report regular AI use in at least one business function。"
    "Twenty-three percent are scaling an agentic AI system。"
)

# -- 预登记映射用例(grill-prep Q3 / ADR-0027;抽检前写死,禁止事后改期望凑绿) ----------
# 样例主张态按 provenance contrast_hint 钉死:数字漂移/新事实 → stale;仍支持 → fresh;
# 缺口/口径不清 → unknown。期望包结论 = 勿发(任一条未收口 stale)。
PREREG_MAPPING = {
    "case_id": "mck-soai-post-reverify-unresolved-stale",
    "claim_outcomes": {
        "mck-1": {"status": "stale", "t1_evidence_ids": ["mck-soai-agents-2025-11#p2@T1"]},
        "mck-2": {"status": "fresh", "t1_evidence_ids": ["mck-soai-agents-2025-11#p4@T1"]},
        "mck-3": {"status": "unknown", "t1_evidence_ids": []},
        "mck-4": {"status": "stale", "t1_evidence_ids": ["mck-soai-agents-2025-11#p3@T1"]},
    },
    "expected_disposition": "勿发",
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "CORPUS", tmp_path / "corpus")
    (tmp_path / "corpus" / "t1").mkdir(parents=True)
    events_dir = tmp_path / "patch_events"
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", events_dir)
    appmod._prepublish.clear()
    appmod._state.update({
        "claims": [], "question": "", "trajectory": None,
        "running": False, "latch": dict(appmod.EMPTY_LATCH),
        "budget": dict(appmod.EMPTY_BUDGET), "run_ctx": None,
        "retrieve_zero_hits": [], "active_run_id": None,
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
    return TestClient(appmod.app), events_dir


def _load_sample_claims() -> list[Claim]:
    docket = load_docket(PACK_DIR / "docket.json")
    return list(docket.claims)


def _apply_rule_gate_outcomes(claims: list[Claim], outcomes: dict) -> None:
    """零 LLM:按预登记结局走规则闸后写回主张态(模拟复验收尾)。"""
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


# -- 主缝贯通 -------------------------------------------------------------------


def test_main_seam_sample_pack_thin_url_to_patch_events(client):
    """Given 顾问样例包 + 夹具薄 URL,When 跑发前主缝,Then disposition/投影/checksum/账本齐。"""
    http, events_dir = client
    assert PACK_DIR.is_dir()

    # 1) 主张集:顾问样例包(不经 active_pack,避免冒充第二垂直)
    claims = _load_sample_claims()
    assert len(claims) >= 3
    assert all(c.claim_id.startswith("mck-") for c in claims)
    docket_q = json.loads((PACK_DIR / "docket.json").read_text(encoding="utf-8"))["question"]
    appmod._state["claims"] = claims
    appmod._state["question"] = docket_q

    # 2) 合法 T1:夹具薄 URL 入库
    r_url = http.post("/api/t1-source/url", json={"url": WHITELIST_URL})
    assert r_url.status_code == 200, r_url.text
    snap = r_url.json()
    assert snap["ready"] is True
    assert snap["kind"] == "url"
    assert snap["checksum"]
    t1_checksum = snap["checksum"]

    # 3) 复验/规则闸(零 LLM 夹具结局)
    _apply_rule_gate_outcomes(claims, PREREG_MAPPING["claim_outcomes"])
    disp = disposition_for_claims(claims)
    assert disp == PREREG_MAPPING["expected_disposition"]
    assert disp in DISPOSITIONS

    # 4) 发前列表投影
    row = appmod._sync_prepublish(new_run=True)
    assert row["disposition"] == disp
    listed = http.get("/api/prepublish/runs").json()["runs"]
    assert listed and listed[0]["disposition"] == disp
    assert listed[0]["title"]
    assert listed[0]["status"] in ("未复验", "复验中", "待人审", "已落档")

    # 5) 详情包结论条与列表一致 + T1 checksum 可追
    detail = http.get("/api/claims").json()
    assert detail["disposition"] == listed[0]["disposition"]
    assert any(x.get("checksum") == t1_checksum for x in detail["t1_checksums"])

    # 6) 人审:收口未处理 stale(mck-1/mck-4);unknown mck-3 亦 discard → 可发
    rnd = appmod._latch().enter_round(claims)
    assert rnd.waiting
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
    appmod._sync_prepublish(new_run=False)
    assert http.get("/api/prepublish/runs").json()["runs"][0]["status"] == "待人审"

    decisions = [
        {"claim_id": "mck-1", "action": "discard"},
        {"claim_id": "mck-3", "action": "discard"},
        {"claim_id": "mck-4", "action": "discard"},
    ]
    r_dec = http.post(
        "/api/latch/decide",
        json={"thread_id": rnd.thread_id, "decisions": decisions},
    )
    assert r_dec.status_code == 200, r_dec.text
    body = r_dec.json()
    assert all(x.get("ok") for x in body["results"])
    assert body["disposition"] == "可发"
    assert body["patch_events_written"] >= 1
    listed2 = http.get("/api/prepublish/runs").json()["runs"]
    assert listed2[0]["disposition"] == body["disposition"] == "可发"
    assert listed2[0]["status"] == "已落档"

    # 7) patch_events 至少一行字段齐全
    rows = pe.read_events(events_dir=events_dir)
    assert len(rows) >= 1
    for key in pe.REQUIRED_FIELDS:
        assert key in rows[0]
    assert rows[0]["before_disp"] == "勿发"
    assert rows[0]["human_confirm"] is True
    assert rows[0]["actor"] == "human"
    assert rows[0]["arm"] in ("C", "T")


# -- 映射抽检 -------------------------------------------------------------------


def test_prereg_mapping_disposition_matches_adr0027():
    """Given 预登记样例主张态,When 聚合 disposition,Then 与 ADR-0027 边界一致。"""
    rows = [
        ClaimDispositionInput(status=o["status"])
        for o in PREREG_MAPPING["claim_outcomes"].values()
    ]
    got = aggregate_disposition(rows)
    assert got == PREREG_MAPPING["expected_disposition"]
    assert got == "勿发"  # 未收口 stale 优先
    assert got in DISPOSITIONS

    # 收口全部红/黄灯后 → 可发(边界 4)
    closed = [
        ClaimDispositionInput(status="stale", human_action="discard"),
        ClaimDispositionInput(status="fresh"),
        ClaimDispositionInput(status="unknown", human_action="discard"),
        ClaimDispositionInput(status="stale", human_action="discard"),
    ]
    assert aggregate_disposition(closed) == "可发"


# -- 软 Port / 默认臂 ------------------------------------------------------------


def test_thesis1_soft_port_not_second_vertical_and_smoke():
    """thesis-1 / QuoteTTL 可解析烟测不红;v1 样例包不算第二 active_pack 垂直。"""
    assert KNOWN_PACK_IDS == (DEFAULT_PACK_ID, P1_PACK_ID)
    assert PACK_ID not in KNOWN_PACK_IDS
    t1 = resolve_pack(DEFAULT_PACK_ID)
    assert t1.pack_id == DEFAULT_PACK_ID
    assert t1.docket.is_file()
    assert (t1.corpus / "t0").is_dir() and (t1.corpus / "t1").is_dir()
    p1 = resolve_pack(P1_PACK_ID)
    assert p1.pack_id == P1_PACK_ID
    assert p1.docket.is_file()
    # 样例包仍可引用(只读),但不进 KNOWN_PACK_IDS
    assert (PACK_DIR / "docket.json").is_file()


def test_production_retrieval_default_is_hybrid_rerank(tmp_path):
    """在线默认是 hybrid+rerank。空库没有可用向量，这次检索记 bm25_fallback。回退不改常量。"""
    from freshlatch.runner import RunContext
    from freshlatch.store.sqlite_store import SQLiteStore

    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    store = SQLiteStore(tmp_path / "hybrid-check.db")
    ctx = RunContext(store=store, mode="online")
    hits = ctx.try_retrieve("探针查询", as_of="T1", top_k=3)
    assert hits == [] or isinstance(hits, list)
    assert ctx.events[-1]["retrieval_mode"] == "bm25_fallback"
    ctx.set_retrieval_switch("bm25")
    ctx.try_retrieve("探针查询", as_of="T1", top_k=3)
    assert ctx.events[-1]["retrieval_mode"] == "bm25"
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
