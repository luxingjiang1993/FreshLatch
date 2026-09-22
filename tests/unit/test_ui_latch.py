"""HumanLatch 审批端点(§5.5)与复验单人审交互的单测:零 LLM。

- decide/rerun 均为同步 def 端点(线程池执行,不阻塞事件循环,ADR-0006 §8)。
- 写路径唯一:端点内只调 gates/human_latch(经 latch 管道),不直写库。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.store.base import Chunk, Document


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    appmod._state.update({"claims": [], "question": "", "trajectory": None,
                          "running": False, "latch": dict(appmod.EMPTY_LATCH)})
    return TestClient(appmod.app)


def _seed_claims():
    claims = [Claim(claim_id="c1", statement="竞品客单价仍显著高于我们",
                    status="stale", reason="T1 竞品降价"),
              Claim(claim_id="c2", statement="普查仍支持", status="fresh", reason="T1 仍支持")]
    appmod._state["claims"] = claims
    return claims


# -- HTML 交互件(红线单测的补充,不碰前三条红线)-------------------------------------


def test_void_double_confirm_modal_present():
    """§5.3 步骤 1:点「作废」→ 双重确认弹窗文案「作废后重跑不得再绿」。"""
    assert "作废后重跑不得再绿" in appmod.HTML_PAGE
    assert 'id="modal"' in appmod.HTML_PAGE
    assert "confirmVoid" in appmod.HTML_PAGE


def test_rerun_button_and_banner_present():
    """§5.3 步骤 4:重跑作废主张按钮 + §5.3 步骤 5 待人工横幅。"""
    assert "重跑作废主张" in appmod.HTML_PAGE
    assert "待人工" in appmod.HTML_PAGE
    assert "提交人审决定" in appmod.HTML_PAGE


def test_renew_form_present_and_w5_gate_removed():
    """§5.4 实装后(#23):续命表单(下拉选 T1 证据 + 点回核对)在位,W5 禁用态已退役。"""
    assert 'id="renew-modal"' in appmod.HTML_PAGE
    assert 'id="renew-evidence"' in appmod.HTML_PAGE
    for fn in ("openRenew", "closeRenew", "confirmRenew", "previewRenewEvidence"):
        assert fn in appmod.HTML_PAGE
    assert "本轮已检索的 T1 块" in appmod.HTML_PAGE  # ADR-0006 §4:下拉非自由文本
    assert "续命(W5 开放)" not in appmod.HTML_PAGE   # 禁用态 tooltip 随实装移除


def test_renew_button_disabled_without_t1_evidence():
    """ADR-0006 §6 交互层:无 evidence_id 续命不可用(前端拦截,后端闸兜底)。"""
    assert 'title="本轮无已检索 T1 原文块,续命不可用"' in appmod.HTML_PAGE
    assert "e.endsWith('@T1')" in appmod.HTML_PAGE  # 下拉只收锚 T1 的块


def test_voided_card_gray_and_dual_badge():
    """§5.3 步骤 3:void 灰显;stale(机器)与 void(人)并存不互斥(前端双徽章)。"""
    assert ".claim.voided" in appmod.HTML_PAGE
    assert "BADGE.void" in appmod.HTML_PAGE


# -- 端点行为 ------------------------------------------------------------------------


def test_decide_wrong_thread_rejected(client):
    _seed_claims()
    r = client.post("/api/latch/decide", json={"thread_id": "nope", "decisions": []})
    assert r.status_code == 409


def test_decide_discard_happy_path(client):
    claims = _seed_claims()
    rnd = appmod._latch().enter_round(claims)  # 真实轮次 thread(先在 interrupt 落盘)
    assert rnd.waiting
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
    r = client.post("/api/latch/decide",
                    json={"thread_id": rnd.thread_id,
                          "decisions": [{"claim_id": "c1", "action": "discard"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["results"][0]["ok"] is True
    assert body["latch"]["thread_id"] is None  # 轮次关闭
    j = client.get("/api/claims").json()
    c1 = next(c for c in j["claims"] if c["claim_id"] == "c1")
    assert c1["voided"] is True and c1["status"] == "stale"  # 并存不互斥
    assert "c1" in appmod._store().list_invalidation()


DOC = "t0-competitor-notes"
RENEW_EID = f"{DOC}#p2@T1"


def _seed_t1_chunk(store, *, checksum: str = ""):
    store.add_document(
        Document(doc_id=DOC, as_of="T1", source_type="competitor", title="竞品笔记",
                 doc_version="v2", checksum=checksum,
                 full_text="T1:竞品客单价仍显著高于我们。"),
        [Chunk(doc_id=DOC, chunk_id=f"{DOC}-p2", clause_id="p2", title="竞品笔记",
               text="T1:竞品客单价仍显著高于我们。", source_type="competitor",
               as_of="T1", doc_version="v2", checksum=checksum, tokens=20)],
    )


def test_decide_renew_turns_card_green_with_timeline(client, tmp_path, monkeypatch):
    """#23 用户旅程:红灯主张 → 续命(带 T1 证据)→ 闸过 → 卡片转绿 + 时间线条目。

    Batch 2:UI 已注入真 checksum_fn;夹具语料字节须与 claimed 指纹一致(ATK-CS-04 同构)。
    """
    from freshlatch.store.checksum import sha256_hex

    corpus = tmp_path / "corpus"
    (corpus / "t1").mkdir(parents=True)
    raw = (
        f"---\ndoc_id: {DOC}\nas_of: T1\nsource_type: competitor\n"
        f"title: 竞品笔记\nchecksum:\n---\n\n## p2\n"
        f"T1:竞品客单价仍显著高于我们。\n"
    ).encode("utf-8")
    (corpus / "t1" / f"{DOC}.md").write_bytes(raw)
    cs = sha256_hex(raw)
    monkeypatch.setattr(appmod, "CORPUS", corpus)

    _seed_t1_chunk(appmod._store(), checksum=cs)
    claims = [Claim(claim_id="c1", statement="竞品客单价仍显著高于我们",
                    status="stale", reason="T1 竞品降价", t1_evidence_ids=[RENEW_EID])]
    appmod._state["claims"] = claims
    rnd = appmod._latch().enter_round(claims)
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}

    r = client.post("/api/latch/decide",
                    json={"thread_id": rnd.thread_id,
                          "decisions": [{"claim_id": "c1", "action": "renew",
                                         "evidence_id": RENEW_EID}]})
    assert r.status_code == 200
    assert r.json()["results"][0]["ok"] is True
    c1 = next(c for c in r.json()["claims"] if c["claim_id"] == "c1")
    assert c1["status"] == "fresh"                       # 卡片转绿
    assert c1["last_confirmed_at"]                       # 续命时间戳
    assert c1["validity_basis"]["doc_id"] == DOC         # 新有效性依据
    assert [t["label"] for t in c1["timeline"]] == ["人审续命"]   # 时间线条目
    assert c1["timeline"][0]["evidence_id"] == RENEW_EID          # 依据可点回
    assert "c1" not in appmod._store().list_invalidation()        # 续命不进作废名单


def test_decide_renew_gate_rejection_surfaces_error_code(client):
    """闸打回 = 该条零写,error_code 透传到端点(前端如实上屏,不静默吞)。"""
    claims = [Claim(claim_id="c1", statement="竞品客单价仍显著高于我们",
                    status="stale", reason="T1 竞品降价", t1_evidence_ids=[RENEW_EID])]
    appmod._state["claims"] = claims
    rnd = appmod._latch().enter_round(claims)  # store 无 chunk → 点回校验打回
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}

    r = client.post("/api/latch/decide",
                    json={"thread_id": rnd.thread_id,
                          "decisions": [{"claim_id": "c1", "action": "renew",
                                         "evidence_id": RENEW_EID}]})
    assert r.status_code == 200
    res = r.json()["results"][0]
    assert res["ok"] is False and res["error_code"] == "RENEW_EVIDENCE_UNRESOLVED"
    c1 = next(c for c in r.json()["claims"] if c["claim_id"] == "c1")
    assert c1["status"] == "stale" and c1["last_confirmed_at"] is None


def test_rerun_unknown_claim_404(client):
    _seed_claims()
    r = client.post("/api/latch/rerun", json={"claim_id": "c9"})
    assert r.status_code == 404


def test_rerun_non_invalidated_400(client):
    _seed_claims()
    r = client.post("/api/latch/rerun", json={"claim_id": "c1"})  # 未作废
    assert r.status_code == 400


def test_rerun_voided_claim_happy_path(client, tmp_path, monkeypatch):
    claims = _seed_claims()
    appmod._store().add_invalidation("c1", "2026-09-20T00:00:00", actor="human")
    fake = lambda claim: ("unknown", "Lead 判 fresh,规则闸按作废名单打回(INVALIDATED)")
    monkeypatch.setattr(appmod, "_latch",
                        lambda: HumanLatch(appmod._store(), tmp_path / "cp.db",
                                           mode="online", reverify_fn=fake))
    r = client.post("/api/latch/rerun", json={"claim_id": "c1"})
    assert r.status_code == 200
    entry = r.json()["entry"]
    assert entry["label"] == "重跑后仍红(第 1 次)"
    assert entry["thread_id"].startswith("reverify-c1-")
    assert "INVALIDATED" in entry["note"]
    timeline = appmod._store().list_reruns("c1")
    assert len(timeline) == 1 and timeline[0]["nth"] == 1
