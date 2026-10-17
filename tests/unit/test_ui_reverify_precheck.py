"""#679 T2(I-02 + I-07):开始复验预检 / bm25_fallback 知情降级 / 代理中文映射 / trust_env=False。

验收对齐(零付费 LLM、零真实下载):
- 缺权重时点「开始复验」走纯文件层预检(毫秒级),面板数据含 ~1.1GB 说明与下载状态。
- 「先用 BM25(精度降级)」= 本跑 bm25_fallback_accepted:轨迹 run_meta 与 retrieve 事件
  记 bm25_fallback;不改 PRODUCTION_RETRIEVAL_MODE;与 set_retrieval_switch("bm25")
  (last_retrieval_mode=bm25)语义可区分。
- 坏 NO_PROXY/代理失败:describe_llm_transport_error 映射「代理/NO_PROXY 配置异常」+ 怎么办;
  /api/reverify 不裸抛 500 英文堆栈。
- LLMClient 默认装配 trust_env=False,坏环境变量不污染请求路径。
"""

from __future__ import annotations

import json
import threading
import time

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APIConnectionError

import freshlatch.ui.app as appmod
from freshlatch.llm import (
    PROXY_ERROR_CODE,
    LLMClient,
    DecodingParams,
    default_http_client,
    describe_llm_transport_error,
)
from freshlatch.runner import ClaimDecision, RunResult, Runner
from freshlatch.store.base import (
    PRODUCTION_RETRIEVAL_MODE,
    Document,
    InMemoryStore,
)
from freshlatch.ui.weight_precheck import (
    fastembed_weights_present,
    local_embed_weights_ready,
)


def _blank() -> None:
    appmod._clear_live_sheet()
    appmod._state["running"] = False
    appmod._prepublish.clear()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
    _blank()
    yield TestClient(appmod.app)
    _blank()


def _seed_ready_t1_and_claims(client: TestClient) -> None:
    """选定合法 T1 来源,否则 /api/reverify 400。"""
    assert client.post("/api/t1-source/synthetic").status_code == 200
    client.post("/api/import")


# -- 权重文件层预检(纯 stat,毫秒级) ----------------------------------------------------


def test_fastembed_weights_present_huggingface_snapshot_layout(tmp_path):
    onnx = tmp_path / "models--BAAI--bge-reranker-base" / "snapshots" / "abc123" / "onnx"
    onnx.mkdir(parents=True)
    (onnx / "model.onnx").write_bytes(b"weights")
    assert fastembed_weights_present("bge-reranker-base", str(tmp_path)) is True
    assert fastembed_weights_present("bge-small-zh-v1.5", str(tmp_path)) is False


def test_fastembed_weights_present_direct_dir_layout(tmp_path):
    d = tmp_path / "bge-small-zh-v1.5"
    d.mkdir()
    (d / "model.onnx").write_bytes(b"weights")
    assert fastembed_weights_present("bge-small-zh-v1.5", str(tmp_path)) is True


def test_precheck_endpoint_reports_missing_with_size_hint(client, monkeypatch, tmp_path):
    """缺权重:ok=false,带 ~1.1GB 说明、缓存目录与下载状态;全在毫秒级返回。"""
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path))
    started = time.monotonic()
    r = client.get("/api/retrieval/precheck")
    elapsed = time.monotonic() - started
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["embedding"] is False
    assert body["reranker"] is False
    assert "1.1GB" in body["reranker_size_hint"]
    assert body["cache_dir"] == str(tmp_path)
    assert body["download"]["state"] == "idle"
    assert elapsed < 10.0  # 验收硬线:≤10s 出面板(实际为毫秒级)


def test_precheck_endpoint_ok_when_weights_present(client, monkeypatch, tmp_path):
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path))
    for short in ("bge-small-zh-v1.5", "bge-reranker-base"):
        d = tmp_path / f"models--BAAI--{short}" / "snapshots" / "rev" / "onnx"
        d.mkdir(parents=True)
        (d / "model.onnx").write_bytes(b"w")
    assert local_embed_weights_ready(str(tmp_path)) is True
    body = client.get("/api/retrieval/precheck").json()
    assert body["ok"] is True
    assert body["embedding"] is True and body["reranker"] is True


# -- 下载任务(后台线程;单测 monkeypatch 零真实下载) ---------------------------------------


def _wait_job_done(timeout_s: float = 10.0) -> dict:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        state = appmod._WEIGHT_DOWNLOAD_JOB["state"]
        if state in ("ok", "error"):
            return dict(appmod._WEIGHT_DOWNLOAD_JOB)
        time.sleep(0.02)
    raise AssertionError(f"下载任务未在 {timeout_s}s 内结束 state={state}")


def test_download_job_success_path(client, monkeypatch):
    entered = threading.Event()
    finish = threading.Event()

    def _noop_warmup() -> None:
        entered.set()
        finish.wait(10)

    monkeypatch.setattr(appmod, "_warmup_local_weights", _noop_warmup)
    try:
        r = client.post("/api/retrieval/precheck/download")
        assert r.status_code == 200
        assert entered.wait(5)  # 后台线程确已接管,状态必为 running(无竞态)
        assert r.json()["download"]["state"] == "running"
    finally:
        finish.set()
    job = _wait_job_done()
    assert job["state"] == "ok"
    assert job["error"] is None


def test_download_job_failure_reason_is_chinese(client, monkeypatch):
    def _boom() -> None:
        raise ConnectionError("网络不可达(测试夹具)")

    monkeypatch.setattr(appmod, "_warmup_local_weights", _boom)
    r = client.post("/api/retrieval/precheck/download")
    assert r.status_code == 200
    job = _wait_job_done()
    assert job["state"] == "error"
    assert "下载/预热失败" in job["error"]
    assert "ConnectionError" in job["error"]
    # 失败原因经 GET 预检透出,供面板「失败原因」位展示
    status = client.get("/api/retrieval/precheck").json()["download"]
    assert status["state"] == "error"
    assert "网络不可达" in status["error"]


def test_download_refused_while_offline(client, monkeypatch):
    monkeypatch.setenv("FRESHLATCH_EMBED_OFFLINE", "1")
    r = client.post("/api/retrieval/precheck/download")
    assert r.status_code == 409
    assert "离线模式" in r.json()["error"]


def test_download_rejects_double_start(client, monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def _blocked() -> None:
        started.set()
        release.wait(5)

    monkeypatch.setattr(appmod, "_warmup_local_weights", _blocked)
    try:
        assert client.post("/api/retrieval/precheck/download").status_code == 200
        assert started.wait(5)
        again = client.post("/api/retrieval/precheck/download")
        assert again.status_code == 409
        assert "已在进行" in again.json()["error"]
    finally:
        release.set()
    _wait_job_done()


# -- bm25_fallback 知情降级:轨迹字段 vs 运维开关 -----------------------------------------


def _store_with_chunk() -> InMemoryStore:
    from freshlatch.store.base import Chunk

    store = InMemoryStore()
    # 单文档语料 BM25Okapi 的 idf 为负、得分恒 ≤0 会被 recall_bm25 的 s>0 过滤;
    # 铺两条无关 chunk 让正命中得分 >0(与生产多 chunk 语料同形)。
    store.add_document(
        Document(doc_id="d1", as_of="T1", source_type="www", title="t",
                 doc_version="v1", checksum="c", full_text="原文"),
        [Chunk(doc_id="d1", chunk_id="k1", clause_id="p1", title="t",
               text="定价已改", source_type="www", as_of="T1",
               doc_version="v1", checksum="c", tokens=4)],
    )
    store.add_document(
        Document(doc_id="d2", as_of="T1", source_type="www", title="u",
                 doc_version="v1", checksum="c", full_text="无关"),
        [Chunk(doc_id="d2", chunk_id="k2", clause_id="p2", title="u",
               text="交付地点在上海", source_type="www", as_of="T1",
               doc_version="v1", checksum="c", tokens=6)],
    )
    store.add_document(
        Document(doc_id="d3", as_of="T1", source_type="www", title="v",
                 doc_version="v1", checksum="c", full_text="无关二"),
        [Chunk(doc_id="d3", chunk_id="k3", clause_id="p3", title="v",
               text="违约责任另议", source_type="www", as_of="T1",
               doc_version="v1", checksum="c", tokens=6)],
    )
    return store


def test_accepted_fallback_runs_bm25_fallback_arm_without_switch():
    """accept_bm25_fallback=True:整臂 bm25_fallback,轨迹事件与 store 记号一致;
    retrieval_switch 仍是 None——与 set_retrieval_switch('bm25') 语义可区分。"""
    store = _store_with_chunk()
    ctx = appmod.RunContext(store=store)
    ctx.bm25_fallback_accepted = True
    assert ctx._active_retrieval_mode() == "bm25_fallback"
    hits = ctx.try_retrieve("定价", as_of="T1")
    assert [c.clause_id for c in hits] == ["p1"]
    event = next(e for e in ctx.events if e.get("type") == "retrieve")
    assert event["retrieval_mode"] == "bm25_fallback"
    assert store.last_retrieval_mode == "bm25_fallback"
    assert ctx.retrieval_switch is None
    assert store._requested_retrieval_mode() is None  # 本轮结束后不残留绑定
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"  # 常量未被改动


def test_retrieval_switch_bm25_semantics_unchanged():
    """运维开关老语义:last_retrieval_mode=bm25(不是 bm25_fallback),一字不动。"""
    store = _store_with_chunk()
    ctx = appmod.RunContext(store=store)
    ctx.set_retrieval_switch("bm25")
    assert ctx._active_retrieval_mode() == "bm25"
    ctx.try_retrieve("定价", as_of="T1")
    event = next(e for e in ctx.events if e.get("type") == "retrieve")
    assert event["retrieval_mode"] == "bm25"
    assert store.last_retrieval_mode == "bm25"
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"


def test_run_meta_records_bm25_fallback_flag(tmp_path, monkeypatch):
    """本跑轨迹 run_meta 带 bm25_fallback 布尔;未知情降级的常规跑为 false。"""
    from freshlatch.models import Claim

    def _run(accepted: bool) -> dict:
        runner = Runner(_store_with_chunk())
        runner.ctx.bm25_fallback_accepted = accepted

        class _StubLead:
            steps_used = 1

            def run(self) -> ClaimDecision:
                return ClaimDecision(claim_id="c1", status="unknown", reason="测试")

        monkeypatch.setattr(runner, "_spawn_lead", lambda claim: _StubLead())
        result = runner.run([Claim(claim_id="c1", statement="s", t0_evidence_ids=[])],
                            trajectory_dir=str(tmp_path))
        first = result.trajectory_path.read_text(encoding="utf-8").splitlines()[0]
        return json.loads(first)

    meta_off = _run(accepted=False)
    assert meta_off["bm25_fallback"] is False
    meta_on = _run(accepted=True)
    assert meta_on["bm25_fallback"] is True
    assert meta_on["mode"] == "online"


# -- /api/reverify:接受知情降级 + 传输层中文映射 -------------------------------------------


def test_reverify_accepts_bm25_fallback_flag(client, monkeypatch):
    """accept_bm25_fallback=true 透传到 RunContext;响应仍是既有 200 形状。"""
    _seed_ready_t1_and_claims(client)
    seen: dict = {}

    class _FakeRunner:
        def __init__(self, store, **_kwargs):
            self.ctx = appmod.RunContext(store=store)

        def run(self, claims):
            seen["accepted"] = self.ctx.bm25_fallback_accepted
            return RunResult(
                claims=list(claims), decisions={}, trajectory_path=None,
                steps_by_claim={}, retrieval_used=0,
                decoding=DecodingParams(model="mock", temperature=0.0),
                retrieve_zero_hits=[],
            )

    monkeypatch.setattr(appmod, "Runner", _FakeRunner)
    monkeypatch.setattr(
        appmod, "_latch",
        lambda: type("L", (), {"enter_round": lambda self, claims: type(
            "R", (), {"thread_id": None, "pending": []})()})(),
    )
    r = client.post("/api/reverify", json={"accept_bm25_fallback": True})
    assert r.status_code == 200
    assert seen["accepted"] is True
    # 常规调用(无 body)不受影响
    r2 = client.post("/api/reverify")
    assert r2.status_code == 200
    assert seen["accepted"] is False


def test_reverify_maps_transport_error_to_chinese(client, monkeypatch):
    """坏代理/NO_PROXY 走到 OpenAI-compat 路径时:502 + 中文可操作错误,无英文堆栈。"""
    _seed_ready_t1_and_claims(client)

    class _FailingRunner:
        def __init__(self, store, **_kwargs):
            self.ctx = appmod.RunContext(store=store)

        def run(self, claims):
            request = httpx.Request("POST", "https://dashscope.example/v1/chat")
            raise APIConnectionError(request=request, message="连接经代理失败")

    monkeypatch.setattr(appmod, "Runner", _FailingRunner)
    r = client.post("/api/reverify")
    assert r.status_code == 502
    body = r.json()
    assert body["error_code"] == PROXY_ERROR_CODE
    assert "代理/NO_PROXY 配置异常" in body["error"]
    assert "怎么办" in body["error"]
    assert "Traceback" not in r.text
    assert "ssl." not in r.text


def test_reverify_internal_error_is_chinese_not_bare_500(client, monkeypatch):
    _seed_ready_t1_and_claims(client)

    class _BoomRunner:
        def __init__(self, store, **_kwargs):
            self.ctx = appmod.RunContext(store=store)

        def run(self, claims):
            raise RuntimeError("english internal detail must not leak")

    monkeypatch.setattr(appmod, "Runner", _BoomRunner)
    r = client.post("/api/reverify")
    assert r.status_code == 500
    body = r.json()
    assert body["error_code"] == "REVERIFY_INTERNAL"
    assert "复验执行失败" in body["error"]
    assert "english internal detail" not in r.text
    assert "Traceback" not in r.text
    assert appmod._state["running"] is False  # finally 收口,不卡 running


# -- trust_env=False 默认装配 ------------------------------------------------------------


def test_default_http_client_ignores_bad_proxy_env(monkeypatch):
    """坏 NO_PROXY(裸 ::1)+ 坏代理并存:默认 client 不读环境变量(trust_env=False)。"""
    monkeypatch.setenv("NO_PROXY", "::1")
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    http = default_http_client()
    assert http.trust_env is False


def test_llm_client_default_trust_env_false(monkeypatch):
    """LLMClient 默认装配的 OpenAI-compat 底层 httpx client 可外观察证 trust_env=False。"""
    monkeypatch.setenv("NO_PROXY", "::1")
    client = LLMClient()
    raw = client.client  # 首次访问才真构造 SDK client
    assert raw._client.trust_env is False


def test_describe_llm_transport_error_mapping():
    mapped = describe_llm_transport_error(httpx.ConnectError("refused"))
    assert mapped is not None
    assert mapped["error_code"] == PROXY_ERROR_CODE
    assert "代理/NO_PROXY 配置异常" in mapped["error"]
    wrapped = describe_llm_transport_error(
        APIConnectionError(request=httpx.Request("POST", "http://x"), message="m")
    )
    assert wrapped is not None and wrapped["error_code"] == PROXY_ERROR_CODE
    # 非传输层异常不映射,走内部错误路径
    assert describe_llm_transport_error(RuntimeError("boom")) is None
    assert describe_llm_transport_error(ValueError("bad")) is None
