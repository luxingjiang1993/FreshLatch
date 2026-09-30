"""入站 publish-hook check API 单测(ADR-0031 / #230)。

覆盖:可发 allow、勿发 deny(403/409)、缺 run_id fail-closed、
可选 token 头(配置缺失仍可测)、默认本机绑定常量。零 LLM。
"""

from __future__ import annotations

import ast
import os

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.models import Claim
from freshlatch.publish_hook import (
    HOOK_BIND_HOST_ENV,
    HOOK_DEFAULT_BIND_HOST,
    HOOK_DO_NOT_PUBLISH,
    HOOK_MISSING_RUN_ID,
    HOOK_NEEDS_PATCH_NO_ACK,
    HOOK_OK,
    HOOK_TOKEN_ENV,
    HOOK_TOKEN_HEADER,
    HOOK_UNAUTHORIZED,
    HOOK_UNBOUND_RUN,
    deny_http_status,
)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "CORPUS", tmp_path / "corpus")
    (tmp_path / "corpus" / "t1").mkdir(parents=True)
    appmod._prepublish.clear()
    appmod._state.update({
        "claims": [], "question": "", "trajectory": None,
        "running": False, "latch": dict(appmod.EMPTY_LATCH),
        "budget": dict(appmod.EMPTY_BUDGET), "run_ctx": None,
        "retrieve_zero_hits": [], "active_run_id": None,
    })
    appmod._reset_t1_source(store)
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
    # 配置缺失时本机冒烟仍可测:清掉可能继承的密钥
    monkeypatch.delenv(HOOK_TOKEN_ENV, raising=False)
    return TestClient(appmod.app)


def _seed_run(*, status: str, question: str = "入站 check 样例") -> str:
    """按主张 status 种一条发前 Run,返回 run_id。"""
    claims = [
        Claim(claim_id="c1", statement="样例主张", status=status, reason="fixture"),
    ]
    appmod._state["claims"] = claims
    appmod._state["question"] = question
    row = appmod._sync_prepublish(new_run=True)
    return row["run_id"]


def test_check_allow_for_publishable_run(client):
    """Given 可发 Run,When POST check 带 run_id,Then allow=true。"""
    run_id = _seed_run(status="fresh")
    r = client.post("/api/publish-hook/check", json={"run_id": run_id})
    assert r.status_code == 200
    body = r.json()
    assert body["allow"] is True
    assert body["disposition"] == "可发"
    assert body["code"] == HOOK_OK
    assert "message" in body


def test_check_deny_do_not_publish(client):
    """Given 勿发 Run,When POST check,Then allow=false 且 HTTP 403 或 409。"""
    run_id = _seed_run(status="stale")
    r = client.post("/api/publish-hook/check", json={"run_id": run_id})
    assert r.status_code in (403, 409)
    body = r.json()
    assert body["allow"] is False
    assert body["disposition"] == "勿发"
    assert body["code"] == HOOK_DO_NOT_PUBLISH
    assert r.status_code == deny_http_status(HOOK_DO_NOT_PUBLISH)


def test_check_missing_run_id_fail_closed(client):
    """Given 缺 run_id,When POST check,Then fail-closed deny。"""
    for payload in ({}, {"run_id": None}, {"run_id": ""}, {"run_id": "   "}):
        r = client.post("/api/publish-hook/check", json=payload)
        assert r.status_code in (403, 409), payload
        body = r.json()
        assert body["allow"] is False, payload
        assert body["code"] == HOOK_MISSING_RUN_ID, payload


def test_check_unbound_run_id_fail_closed(client):
    """未知 run_id → 无法解析包结论,deny。"""
    r = client.post("/api/publish-hook/check", json={"run_id": "run-not-exist"})
    assert r.status_code in (403, 409)
    body = r.json()
    assert body["allow"] is False
    assert body["code"] == HOOK_UNBOUND_RUN


def test_check_needs_patch_requires_ack(client):
    """需补丁无 ack → 409;带 ack → allow 且页眉约束。"""
    run_id = _seed_run(status="unknown")
    denied = client.post(
        "/api/publish-hook/check",
        json={"run_id": run_id, "ack_needs_patch": False},
    )
    assert denied.status_code == 409
    assert denied.json()["code"] == HOOK_NEEDS_PATCH_NO_ACK
    assert denied.json()["allow"] is False

    allowed = client.post(
        "/api/publish-hook/check",
        json={"run_id": run_id, "ack_needs_patch": True},
    )
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["allow"] is True
    assert body["requires_needs_patch_banner"] is True


def test_optional_token_header_when_configured(client, monkeypatch):
    """环境变量已设 → 必须匹配 X-FreshLatch-Hook-Token;缺头/错头 403。"""
    monkeypatch.setenv(HOOK_TOKEN_ENV, "secret-for-test")
    run_id = _seed_run(status="fresh")

    no_hdr = client.post("/api/publish-hook/check", json={"run_id": run_id})
    assert no_hdr.status_code == 403
    assert no_hdr.json()["code"] == HOOK_UNAUTHORIZED
    assert no_hdr.json()["allow"] is False

    bad = client.post(
        "/api/publish-hook/check",
        json={"run_id": run_id},
        headers={HOOK_TOKEN_HEADER: "wrong"},
    )
    assert bad.status_code == 403
    assert bad.json()["code"] == HOOK_UNAUTHORIZED

    ok = client.post(
        "/api/publish-hook/check",
        json={"run_id": run_id},
        headers={HOOK_TOKEN_HEADER: "secret-for-test"},
    )
    assert ok.status_code == 200
    assert ok.json()["allow"] is True


def test_token_absent_env_allows_localhost_smoke(client, monkeypatch):
    """配置缺失时本机冒烟仍可测(无 token 头也能探闸)。"""
    monkeypatch.delenv(HOOK_TOKEN_ENV, raising=False)
    run_id = _seed_run(status="fresh")
    r = client.post("/api/publish-hook/check", json={"run_id": run_id})
    assert r.status_code == 200
    assert r.json()["allow"] is True


def test_default_bind_host_is_loopback():
    """默认绑定本机回环;禁止把 0.0.0.0 无鉴权当 Done。"""
    assert HOOK_DEFAULT_BIND_HOST == "127.0.0.1"
    assert HOOK_BIND_HOST_ENV == "FRESHLATCH_BIND_HOST"
    # __main__ 启动路径必须引用默认本机绑定(文档/契约落点)
    src = open(appmod.__file__, encoding="utf-8").read()
    tree = ast.parse(src)
    main_src = None
    for node in tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            # if __name__ == "__main__":
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == "__name__":
                main_src = ast.get_source_segment(src, node) or ""
                break
    assert main_src is not None
    assert "HOOK_DEFAULT_BIND_HOST" in main_src
    assert "uvicorn.run" in main_src


def test_api_layer_delegates_same_gate_no_parallel_if():
    """HTTP 适配层须调用 evaluate_publish_hook,禁止平行 if/else 出口。"""
    src = open(appmod.__file__, encoding="utf-8").read()
    assert "evaluate_publish_hook(" in src
    assert '@app.post("/api/publish-hook/check")' in src
    # 禁止出站通知 webhook 顶替 check;禁止 OpenManus WS 平台化字面
    assert "outbound" not in src.lower()
    assert "OpenManus" not in src
    assert "WebSocket" not in src
