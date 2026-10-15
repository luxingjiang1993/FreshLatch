"""A-P2 Serving 最小 HTTP。

服务端 Bearer / API key、客户端 tenant_id 不能单独放行、存活与就绪探针。
零付费 API。不启动对外监听。
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.serving.app as serving
from freshlatch.serving.app import (
    SERVING_API_KEY_HEADER,
    SERVING_AUTH_MALFORMED,
    SERVING_AUTH_UNCONFIGURED,
    SERVING_BIND_HOST_ENV,
    SERVING_DEFAULT_BIND_HOST,
    SERVING_KEYS_ENV,
    SERVING_TENANT_MISMATCH,
    SERVING_UNAUTHORIZED,
    ServingBindError,
    app,
    parse_serving_key_map,
    refuse_unauthenticated_bind,
    resolve_serving_bind_host,
)

_REPO = Path(__file__).resolve().parents[2]
_DOC = _REPO / "docs" / "ops" / "serving-failure-budget.md"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv(SERVING_KEYS_ENV, raising=False)
    monkeypatch.delenv(SERVING_BIND_HOST_ENV, raising=False)
    return TestClient(app)


def _auth(token: str, *, scheme: str = "bearer") -> dict[str, str]:
    if scheme == "bearer":
        return {"Authorization": f"Bearer {token}"}
    return {SERVING_API_KEY_HEADER: token}


def test_missing_auth_is_401_even_with_client_tenant(client):
    """无凭证时，查询参数、请求体或租户头都不能放行。"""
    alone = (
        client.get("/api/session"),
        client.get("/api/session", params={"tenant_id": "victim"}),
        client.get("/api/session", headers={"X-Tenant-Id": "victim"}),
        client.post("/api/session", json={"tenant_id": "victim"}),
        client.post(
            "/api/session",
            params={"tenant_id": "victim"},
            json={"tenant_id": "other"},
        ),
    )
    for response in alone:
        assert response.status_code == 401
        body = response.json()
        assert body["ok"] is False
        assert body["code"] == SERVING_UNAUTHORIZED
        assert "tenant_id" not in body


def test_wrong_bearer_and_api_key_are_401(client, monkeypatch):
    monkeypatch.setenv(SERVING_KEYS_ENV, "good=tenant-a")
    bad_bearer = client.get("/api/session", headers=_auth("wrong"))
    bad_key = client.get("/api/session", headers=_auth("wrong", scheme="api_key"))
    assert bad_bearer.status_code == 401
    assert bad_key.status_code == 401
    assert bad_bearer.json()["code"] == SERVING_UNAUTHORIZED
    assert bad_key.json()["code"] == SERVING_UNAUTHORIZED


def test_bearer_and_api_key_map_to_server_tenant(client, monkeypatch):
    """身份来自服务端映射。未带 tenant_id 时也返回映射值。"""
    monkeypatch.setenv(SERVING_KEYS_ENV, "key-a=tenant-a, key-b=tenant-b")
    by_bearer = client.get("/api/session", headers=_auth("key-a"))
    by_key = client.get(
        "/api/session", headers=_auth("key-b", scheme="api_key"),
    )
    assert by_bearer.status_code == 200
    assert by_bearer.json() == {
        "ok": True,
        "tenant_id": "tenant-a",
        "credential": "bearer",
    }
    assert by_key.status_code == 200
    assert by_key.json()["tenant_id"] == "tenant-b"
    assert by_key.json()["credential"] == "api_key"


def test_client_tenant_mismatch_is_403_and_does_not_grant(client, monkeypatch):
    """凭证属于 tenant-a 时，客户端声明 tenant-b 或 default 都不能换成那个租户。"""
    monkeypatch.setenv(SERVING_KEYS_ENV, "key-a=tenant-a")
    headers = _auth("key-a")
    cases = (
        client.get("/api/session", params={"tenant_id": "tenant-b"}, headers=headers),
        client.post("/api/session", json={"tenant_id": "tenant-b"}, headers=headers),
        client.get("/api/session", params={"tenant_id": "default"}, headers=headers),
        client.post(
            "/api/session",
            params={"tenant_id": "tenant-a"},
            json={"tenant_id": "tenant-b"},
            headers=headers,
        ),
    )
    for response in cases:
        assert response.status_code == 403
        body = response.json()
        assert body["ok"] is False
        assert body["code"] == SERVING_TENANT_MISMATCH
        assert "tenant_id" not in body


def test_matching_client_tenant_keeps_server_mapping(client, monkeypatch):
    monkeypatch.setenv(SERVING_KEYS_ENV, " key-a = tenant-a ")
    headers = _auth("key-a")
    response = client.post(
        "/api/session",
        json={"tenant_id": "tenant-a"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "tenant-a"
    omitted = client.get("/api/session", headers={"Authorization": "bearer key-a"})
    assert omitted.status_code == 200
    assert omitted.json()["tenant_id"] == "tenant-a"
    assert omitted.json()["credential"] == "bearer"


def test_conflicting_credentials_are_rejected(client, monkeypatch):
    """Bearer 与 API key 同时出现且不一致时拒绝，不挑选其中一个。"""
    monkeypatch.setenv(SERVING_KEYS_ENV, "key-a=tenant-a,key-b=tenant-b")
    response = client.get(
        "/api/session",
        headers={
            "Authorization": "Bearer key-a",
            SERVING_API_KEY_HEADER: "key-b",
        },
    )
    assert response.status_code == 401
    assert response.json()["code"] == SERVING_UNAUTHORIZED


def test_malformed_map_fail_closed_without_partial_grant(client, monkeypatch):
    monkeypatch.setenv(SERVING_KEYS_ENV, "good=tenant-a,broken")
    denied = client.get("/api/session", headers=_auth("good"))
    assert denied.status_code == 401
    ready = client.get("/health/ready")
    assert ready.status_code == 503
    assert ready.json()["readiness"] == "not_ready"
    assert ready.json()["reason"] == SERVING_AUTH_MALFORMED
    parsed, fault = parse_serving_key_map("good=tenant-a,broken")
    assert parsed == {}
    assert fault == SERVING_AUTH_MALFORMED


def test_duplicate_token_is_malformed():
    parsed, fault = parse_serving_key_map("same=tenant-a,same=tenant-b")
    assert parsed == {}
    assert fault == SERVING_AUTH_MALFORMED


def test_health_liveness_and_readiness(client, monkeypatch):
    """未配置时存活仍 ok，就绪为 not_ready。配置后两者都 ok。"""
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    combined = client.get("/health")
    assert live.status_code == 200
    assert live.json() == {"liveness": "ok"}
    assert ready.status_code == 503
    assert ready.json()["readiness"] == "not_ready"
    assert ready.json()["reason"] == SERVING_AUTH_UNCONFIGURED
    assert combined.status_code == 200
    assert combined.json()["liveness"] == "ok"
    assert combined.json()["readiness"] == "not_ready"
    secret = "super-secret-token"
    for body in (live.json(), ready.json(), combined.json()):
        assert secret not in str(body)

    monkeypatch.setenv(SERVING_KEYS_ENV, f"{secret}=tenant-a")
    ready_ok = client.get("/health/ready")
    combined_ok = client.get("/health")
    assert ready_ok.status_code == 200
    assert ready_ok.json() == {"readiness": "ok"}
    assert combined_ok.json()["liveness"] == "ok"
    assert combined_ok.json()["readiness"] == "ok"
    assert secret not in ready_ok.text
    assert secret not in combined_ok.text
    assert "tenant-a" not in ready_ok.text


def test_health_does_not_require_auth(client, monkeypatch):
    monkeypatch.setenv(SERVING_KEYS_ENV, "key-a=tenant-a")
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200
    assert client.get("/health").status_code == 200


def test_run_refuses_non_loopback_without_a_valid_map(monkeypatch):
    """启动路径本身拒绝 0.0.0.0 无鉴权，而不是只在文档里声明。"""
    monkeypatch.delenv(SERVING_KEYS_ENV, raising=False)
    monkeypatch.setenv(SERVING_BIND_HOST_ENV, "0.0.0.0")
    with pytest.raises(ServingBindError, match="0.0.0.0"):
        serving.run()
    monkeypatch.setenv(SERVING_KEYS_ENV, "broken")
    with pytest.raises(ServingBindError, match="0.0.0.0"):
        serving.run()


def test_run_binds_loopback_by_default_and_wildcard_only_with_keys(monkeypatch):
    import uvicorn

    captured: dict[str, object] = {}

    def fake_run(app_obj, host, port):
        captured["app"] = app_obj
        captured["host"] = host
        captured["port"] = port

    monkeypatch.setattr(uvicorn, "run", fake_run)
    monkeypatch.delenv(SERVING_KEYS_ENV, raising=False)
    monkeypatch.delenv(SERVING_BIND_HOST_ENV, raising=False)
    monkeypatch.delenv(serving.SERVING_PORT_ENV, raising=False)
    serving.run()
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == serving.SERVING_DEFAULT_PORT
    assert captured["app"] is app

    monkeypatch.setenv(SERVING_KEYS_ENV, "key-a=tenant-a")
    monkeypatch.setenv(SERVING_BIND_HOST_ENV, "0.0.0.0")
    monkeypatch.setenv(serving.SERVING_PORT_ENV, "8011")
    serving.run()
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 8011


def test_wildcard_without_auth_is_refused():
    with pytest.raises(ServingBindError, match="0.0.0.0"):
        refuse_unauthenticated_bind("0.0.0.0", keys_configured=False)
    with pytest.raises(ServingBindError):
        refuse_unauthenticated_bind("::", keys_configured=False)
    with pytest.raises(ServingBindError):
        refuse_unauthenticated_bind("10.1.2.3", keys_configured=False)
    refuse_unauthenticated_bind("0.0.0.0", keys_configured=True)
    refuse_unauthenticated_bind("127.0.0.1", keys_configured=False)
    refuse_unauthenticated_bind("localhost", keys_configured=False)


def test_default_bind_is_loopback(monkeypatch):
    monkeypatch.delenv(SERVING_BIND_HOST_ENV, raising=False)
    assert SERVING_DEFAULT_BIND_HOST == "127.0.0.1"
    assert resolve_serving_bind_host(None) == "127.0.0.1"
    assert resolve_serving_bind_host("  ") == "127.0.0.1"
    assert resolve_serving_bind_host("0.0.0.0") == "0.0.0.0"
    source = Path(serving.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    main_src = ""
    for node in tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == "__name__":
                main_src = ast.get_source_segment(source, node) or ""
    assert "run()" in main_src
    run_fn = ast.get_source_segment(
        source,
        next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "run"
        ),
    )
    assert run_fn is not None
    assert "refuse_unauthenticated_bind" in run_fn
    assert "resolve_serving_bind_host" in run_fn
    assert "uvicorn.run" in run_fn
    assert "host=host" in run_fn
    assert 'host="0.0.0.0"' not in run_fn
    assert "host='0.0.0.0'" not in run_fn


def test_failure_budget_doc_locks_serving_done():
    text = _DOC.read_text(encoding="utf-8")
    assert "无服务端鉴权 ≠ Serving Done" in text
    assert "失败预算" in text
    assert "P3/P5" in text
    assert "0.0.0.0" in text
    assert "FRESHLATCH_SERVING_API_KEYS" in text


def test_serving_source_avoids_locked_surfaces():
    text = Path(serving.__file__).read_text(encoding="utf-8")
    for needle in (
        "PRODUCTION_RETRIEVAL_MODE",
        "RESULT-Y",
        "SESOI",
        "C-04",
    ):
        assert needle not in text


def test_serving_import_does_not_load_ui_app():
    code = (
        "import freshlatch.serving.app\n"
        "import sys\n"
        "raise SystemExit(0 if 'freshlatch.ui.app' not in sys.modules else 1)\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], check=False)
    assert proc.returncode == 0
