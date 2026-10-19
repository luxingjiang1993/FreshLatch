"""HumanLatch 审批端点(§5.5)与复验单人审交互的单测:零 LLM。

- decide/rerun 均为同步 def 端点(线程池执行,不阻塞事件循环,ADR-0006 §8)。
- 写路径唯一:端点内只调 gates/human_latch(经 latch 管道),不直写库。
- I-10(#696):reverify 为 async(POST 立刻返回 run_id,后台线程跑主链);
  cancel/progress 见文件尾新节。
"""

from __future__ import annotations

import threading
import time

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
    # 人审成功后写 patch_events;单测落到临时目录
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
    appmod._state.update({"claims": [], "question": "", "trajectory": None,
                          "running": False, "latch": dict(appmod.EMPTY_LATCH),
                          "active_run_id": None, "run_ctx": None,
                          "budget": dict(appmod.EMPTY_BUDGET),
                          "retrieve_zero_hits": [], "bound_t1_checksums": {}})
    appmod._reset_run_task()
    return TestClient(appmod.app)


def _seed_claims():
    claims = [Claim(claim_id="c1", statement="竞品客单价仍显著高于我们",
                    status="stale", reason="T1 竞品降价"),
              Claim(claim_id="c2", statement="普查仍支持", status="fresh", reason="T1 仍支持")]
    appmod._state["claims"] = claims
    return claims


# -- HTML 交互件(红线单测的补充,不碰前三条红线)-------------------------------------


def test_void_double_confirm_modal_present():
    """§5.3 步骤 1:点「作废」→ 双重确认弹窗文案「作废后重跑不得再变有效」(#736 AC0.5 去颜色字)。"""
    assert "作废后重跑不得再变有效" in appmod.HTML_PAGE
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


def test_banner_pending_same_source_excludes_voided(client):
    """I-05(#693):人审横幅只渲染 enter_round 过滤后的 pending(API 同源,不靠 UI 藏)。

    discard 后 c1 voided 且机器 status 仍 stale;下一轮 pending(= 横幅数据源)不得含 c1。
    """
    claims = [Claim(claim_id="c1", statement="竞品客单价仍显著高于我们",
                    status="stale", reason="T1 竞品降价"),
              Claim(claim_id="c2", statement="普查仍支持", status="fresh", reason="T1 仍支持"),
              Claim(claim_id="c3", statement="T1 无原文覆盖", status="unknown")]
    appmod._state["claims"] = claims
    rnd1 = appmod._latch().enter_round(claims)
    appmod._state["latch"] = {"thread_id": rnd1.thread_id, "pending": rnd1.pending}
    r = client.post("/api/latch/decide",
                    json={"thread_id": rnd1.thread_id,
                          "decisions": [{"claim_id": "c1", "action": "discard"}]})
    assert r.status_code == 200
    rnd2 = appmod._latch().enter_round(claims)
    appmod._state["latch"] = {"thread_id": rnd2.thread_id, "pending": rnd2.pending}
    assert [p["claim_id"] for p in appmod._state["latch"]["pending"]] == ["c3"]


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


# -- I-10(#696):async 启动 / 五态轮询 / 整轮取消 --------------------------------------
#
# 退役同步阻塞双轨:POST /api/reverify 只负责校验+起后台线程+立刻返回 run_id;
# 主链在后台线程跑,经 GET /api/reverify/progress 轮询五态;
# POST /api/reverify/cancel 请求整轮取消(协作点 = 主张边界)。


def _poll_until(client, run_id, targets, timeout_s=10.0):
    """轮询进度直到 status ∈ targets;返回最后一次响应体。"""
    deadline = time.monotonic() + timeout_s
    body = None
    while time.monotonic() < deadline:
        r = client.get("/api/reverify/progress", params={"run_id": run_id})
        assert r.status_code == 200
        body = r.json()
        if body["status"] in targets:
            return body
        time.sleep(0.01)
    pytest.fail(f"轮询超时:run_id={run_id} 最后状态={body}")


class _PacedRunner:
    """假 Runner:逐主张推进度;hold_after=N 时停在第 N 个已完成主张之后(测 cancel)。

    与真 Runner 同构:原地改写传入 Claim;接受 progress/should_cancel 协作钩子。
    停车期间每 5ms 看一次 should_cancel,cancel 即提前退出(整轮取消协作点)。
    """

    def __init__(self, store, **_kwargs):
        self.ctx = appmod.RunContext(store=store)
        self.hold_after = None  # 已完成 N 个主张后停车;0 = 第一个主张前即停车

    def run(self, claims, *, progress=None, should_cancel=None, **_kw):
        done = 0
        for c in claims:
            if should_cancel is not None and should_cancel():
                break
            if progress is not None:
                progress(current=c.claim_id)
            if self.hold_after is not None and done >= self.hold_after:
                # 停车:协作点每 5ms 看 cancel;外部把 hold_after 置 None 即放行
                while self.hold_after is not None:
                    if should_cancel is not None and should_cancel():
                        break
                    time.sleep(0.005)
                if should_cancel is not None and should_cancel():
                    break  # cancel 已置位,整轮提前退出
            c.status = "fresh"
            c.reason = "fake T1 仍支撑"
            done += 1
            if progress is not None:
                progress(done=done)
        from freshlatch.runner import RunResult
        from freshlatch.llm import DecodingParams

        return RunResult(
            claims=list(claims), decisions={},
            trajectory_path=None, steps_by_claim={},
            retrieval_used=0, decoding=DecodingParams(),
            retrieve_zero_hits=[],
        )


def _install_paced_runner(monkeypatch, hold_after=None):
    runner = _PacedRunner(None)
    runner.hold_after = hold_after

    class _Factory:
        def __init__(self, store, **_kwargs):
            runner.ctx = appmod.RunContext(store=store)
            self.ctx = runner.ctx  # 端点经 runner.ctx 读 RunContext(预算/降级旗标)

    def _run(_self, claims, **kwargs):
        return _PacedRunner.run(runner, claims, **kwargs)

    _Factory.run = _run
    monkeypatch.setattr(appmod, "Runner", _Factory)
    return runner


class _RecordingLatch:
    """记录 enter_round 调用;done 路径返回空 pending 轮次(thread_id=None)。

    线程内 enter_round 抛异常会被兜底成 failed——所以 done 路径用返回空轮代替,
    cancel 路径测试改用断言 calls == [] 钉死「取消不进 latch」。
    """

    def __init__(self):
        self.calls = []

    def enter_round(self, claims):
        self.calls.append(list(claims))

        class _Round:
            thread_id = None
            pending = []

        return _Round()


def _seed_t1_and_claims(client, n=3):
    assert client.post("/api/t1-source/synthetic").status_code == 200
    claims = [Claim(claim_id=f"c{i}", statement=f"主张{i}", status="unknown")
              for i in range(1, n + 1)]
    appmod._state["claims"] = claims
    return claims


def test_reverify_async_returns_run_id_same_line_as_active_run(client, monkeypatch):
    """POST 立刻返回 run_id,且与 Phase 0 active_run_id 同线(不另开第二套身份)。"""
    _seed_t1_and_claims(client)
    _install_paced_runner(monkeypatch)
    monkeypatch.setattr(appmod, "_latch", lambda: _RecordingLatch())
    r = client.post("/api/reverify")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "running"
    assert body["run_id"] == appmod._state["active_run_id"]
    final = _poll_until(client, body["run_id"], {"done"})
    assert final["done"] == 3 and final["total"] == 3
    assert final["current_claim_id"] is None
    # done 负载与原同步响应同形状,UI 渲染不分叉
    for key in ("claims", "latch", "budget", "run", "retrieve_zero_hits", "trajectory"):
        assert key in final
    assert appmod._state["running"] is False


def test_poll_observes_running_progress_and_current_claim(client, monkeypatch):
    """轮询面:status=running、完成数/总数、当前 claim_id 可观察。"""
    _seed_t1_and_claims(client)
    runner = _install_paced_runner(monkeypatch, hold_after=0)
    monkeypatch.setattr(appmod, "_latch", lambda: _RecordingLatch())
    body = client.post("/api/reverify").json()
    run_id = body["run_id"]
    deadline = time.monotonic() + 5
    seen = None
    while time.monotonic() < deadline:
        seen = client.get("/api/reverify/progress",
                          params={"run_id": run_id}).json()
        if seen["status"] == "running" and seen["current_claim_id"] == "c1":
            break
        time.sleep(0.01)
    assert seen["status"] == "running"
    assert seen["done"] == 0 and seen["total"] == 3
    assert seen["current_claim_id"] == "c1"
    runner.hold_after = None  # 放行,跑完剩余主张
    final = _poll_until(client, run_id, {"done"})
    assert final["done"] == 3


def test_progress_unknown_run_id_404(client):
    r = client.get("/api/reverify/progress", params={"run_id": "run-nope"})
    assert r.status_code == 404


def test_cancel_whole_run_transitions_and_keeps_partial_results(client, monkeypatch):
    """cancel → cancelling → cancelled:已完成主张保留;不进 latch;清 active_run。"""
    claims = _seed_t1_and_claims(client)
    _install_paced_runner(monkeypatch, hold_after=1)
    latch = _RecordingLatch()
    monkeypatch.setattr(appmod, "_latch", lambda: latch)
    run_id = client.post("/api/reverify").json()["run_id"]
    _poll_until(client, run_id, {"running"})
    deadline = time.monotonic() + 5
    started = None
    while time.monotonic() < deadline:  # 等第一个主张真正跑完(done=1)
        started = client.get("/api/reverify/progress",
                             params={"run_id": run_id}).json()
        if started["done"] >= 1:
            break
        time.sleep(0.01)

    r = client.post("/api/reverify/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelling"
    mid = client.get("/api/reverify/progress", params={"run_id": run_id}).json()
    assert mid["status"] in ("cancelling", "cancelled")  # 协作点收口中

    final = _poll_until(client, run_id, {"cancelled"})
    assert final["done"] == 1 and final["total"] == 3

    j = client.get("/api/claims").json()
    assert j["running"] is False
    assert j["latch"]["thread_id"] is None and j["latch"]["pending"] == []
    assert j["active_run_id"] is None  # 无半残 active_run
    by_id = {c["claim_id"]: c for c in j["claims"]}
    assert by_id["c1"]["status"] == "fresh"     # 已完成主张结果保留
    assert by_id["c2"]["status"] == "unknown"   # 未完成项不被改写
    assert by_id["c3"]["status"] == "unknown"
    assert claims[1].status == "unknown"        # 内存态同样保留
    assert latch.calls == []                  # 取消整轮不进 HumanLatch


def test_cancelled_run_can_restart_within_seconds(client, monkeypatch):
    """取消后立刻可再跑:新 run_id,无半残 active_run 挡路。"""
    _seed_t1_and_claims(client)
    runner = _install_paced_runner(monkeypatch, hold_after=1)
    latch = _RecordingLatch()
    monkeypatch.setattr(appmod, "_latch", lambda: latch)
    old_run = client.post("/api/reverify").json()["run_id"]
    client.post("/api/reverify/cancel")
    _poll_until(client, old_run, {"cancelled"})
    assert latch.calls == []                  # 取消轮不进 latch

    r = client.post("/api/reverify")  # ≤3s(测试内立即)再跑
    assert r.status_code == 200
    assert r.json()["run_id"] != old_run
    assert r.json()["run_id"] == appmod._state["active_run_id"]
    runner.hold_after = None                  # 放行第二跑,跑完剩余主张
    _poll_until(client, r.json()["run_id"], {"done"})
    assert len(latch.calls) == 1              # 第二跑(done)正常进 latch


def test_cancel_without_active_run_409(client):
    r = client.post("/api/reverify/cancel")
    assert r.status_code == 409


def test_reverify_while_running_409(client, monkeypatch):
    _seed_t1_and_claims(client)
    _install_paced_runner(monkeypatch, hold_after=1)
    latch = _RecordingLatch()
    monkeypatch.setattr(appmod, "_latch", lambda: latch)
    assert client.post("/api/reverify").status_code == 200
    r = client.post("/api/reverify")
    assert r.status_code == 409
    assert "已有复验" in r.json()["error"]


def test_failed_run_surfaces_error_via_poll(client, monkeypatch):
    """后台异常 → status=failed;错误负载为中文可操作,不裸抛堆栈。"""
    _seed_t1_and_claims(client)

    class _Boom:
        def __init__(self, store, **_kwargs):
            self.ctx = appmod.RunContext(store=store)

        def run(self, claims, **kwargs):
            raise RuntimeError("english detail must not leak")

    monkeypatch.setattr(appmod, "Runner", _Boom)
    run_id = client.post("/api/reverify").json()["run_id"]
    final = _poll_until(client, run_id, {"failed"})
    assert final["error_code"] == "REVERIFY_INTERNAL"
    assert "复验执行失败" in final["error"]
    assert "english detail" not in final["error"]
    assert appmod._state["running"] is False
    assert appmod._state["active_run_id"] == run_id  # failed 与 Phase 0 同线保留


def test_no_sse_websocket_or_single_claim_skip_entry():
    """OUT 红线:无 SSE/WebSocket;无单主张 skip 入口;cancel/progress 端点在位。"""
    assert "EventSource" not in appmod.HTML_PAGE
    assert "WebSocket" not in appmod.HTML_PAGE
    assert "single claim skip" not in appmod.HTML_PAGE
    paths = [getattr(route, "path", "") for route in appmod.app.routes]
    assert "/api/reverify/cancel" in paths
    assert "/api/reverify/progress" in paths
    assert not any("skip" in p for p in paths)


def test_cancel_button_and_progress_poll_present():
    """UI:取消按钮 + 轮询/渲染函数在位;文案含五态。"""
    assert 'id="btn-cancel-run"' in appmod.HTML_PAGE
    for token in ("pollReverifyRun", "cancelReverifyRun", "/api/reverify/progress",
                  "/api/reverify/cancel"):
        assert token in appmod.HTML_PAGE
