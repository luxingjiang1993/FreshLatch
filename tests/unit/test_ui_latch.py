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


def test_renew_button_still_disabled():
    """§5.4:续命渲染但 disabled,红线以禁用态可见(不因 T9 误开)。"""
    assert 'disabled title="W5 开放:续命必须带 T1 原文证据"' in appmod.HTML_PAGE


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


def test_decide_renew_fail_closed(client):
    claims = _seed_claims()
    rnd = appmod._latch().enter_round(claims)
    appmod._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
    r = client.post("/api/latch/decide",
                    json={"thread_id": rnd.thread_id,
                          "decisions": [{"claim_id": "c1", "action": "renew",
                                         "evidence_id": "t0-competitor-notes#p2@T1"}]})
    assert r.status_code == 200
    assert r.json()["results"][0]["error_code"] == "RENEW_NOT_OPEN"


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
