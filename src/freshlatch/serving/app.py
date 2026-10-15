"""Serving 最小 HTTP：服务端鉴权、租户映射、存活/就绪探针。

凭证到 `tenant_id` 的映射只来自环境变量 `FRESHLATCH_SERVING_API_KEYS`。
客户端单独提交的 `tenant_id` 不是身份。未配置映射时受保护路由拒绝，
`/health/ready` 为未就绪。非回环地址在没有映射时拒绝启动。

本模块不是复验单，也不提供聊天。形状对照：Bearer 密钥在服务端
（Stripe API authentication），存活与就绪分开（Kubernetes probes）。
"""

from __future__ import annotations

import hmac
import os
from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from freshlatch.store.tenant_acl import resolve_pre_retrieval_tenant

# 服务端凭证映射。格式：token=tenant_id，多项用逗号分隔。未配置则未就绪。
SERVING_KEYS_ENV = "FRESHLATCH_SERVING_API_KEYS"
SERVING_API_KEY_HEADER = "X-API-Key"
SERVING_BIND_HOST_ENV = "FRESHLATCH_SERVING_BIND_HOST"
SERVING_DEFAULT_BIND_HOST = "127.0.0.1"
SERVING_PORT_ENV = "FRESHLATCH_SERVING_PORT"
SERVING_DEFAULT_PORT = 8001

SERVING_UNAUTHORIZED = "SERVING_UNAUTHORIZED"
SERVING_TENANT_MISMATCH = "SERVING_TENANT_MISMATCH"
SERVING_AUTH_MALFORMED = "serving_auth_malformed"
SERVING_AUTH_UNCONFIGURED = "serving_auth_unconfigured"

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_WILDCARD_HOSTS = frozenset({"0.0.0.0", "::", "[::]"})


class ServingBindError(RuntimeError):
    """非回环监听且没有服务端鉴权。0.0.0.0 无鉴权不是 Serving Done。"""


class SessionBody(BaseModel):
    """受保护会话请求体。`tenant_id` 只是声明，不是放行依据。"""

    tenant_id: str | None = None


@dataclass(frozen=True)
class ServingIdentity:
    """一次通过的服务端身份。tenant_id 来自凭证映射。"""

    tenant_id: str
    credential: str


app = FastAPI(
    title="FreshLatch Serving",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def parse_serving_key_map(raw: str | None) -> tuple[dict[str, str], str | None]:
    """解析 token=tenant 映射。

    空白或未设置视为未配置，返回空映射且无故障码。
    任一片段不合法则整表作废，不保留已经解析的片段。
    """
    if raw is None or not str(raw).strip():
        return {}, None
    mapping: dict[str, str] = {}
    for part in str(raw).split(","):
        piece = part.strip()
        if not piece or "=" not in piece:
            return {}, SERVING_AUTH_MALFORMED
        token, tenant = piece.split("=", 1)
        token = token.strip()
        tenant = tenant.strip()
        if not token or not tenant or token in mapping:
            return {}, SERVING_AUTH_MALFORMED
        mapping[token] = tenant
    if not mapping:
        return {}, SERVING_AUTH_MALFORMED
    return mapping, None


def load_serving_key_map() -> tuple[dict[str, str], str | None]:
    """读取当前进程的服务端凭证映射。"""
    return parse_serving_key_map(os.environ.get(SERVING_KEYS_ENV))


def resolve_serving_bind_host(raw: str | None = None) -> str:
    """监听地址。未设置时为本机回环，不默认 0.0.0.0。"""
    if raw is None:
        raw = os.environ.get(SERVING_BIND_HOST_ENV)
    text = (raw or "").strip()
    return text or SERVING_DEFAULT_BIND_HOST


def refuse_unauthenticated_bind(host: str, *, keys_configured: bool) -> None:
    """没有服务端映射时，拒绝把非回环地址当作可对外的 Serving。"""
    if keys_configured:
        return
    normalized = (host or "").strip().lower()
    if normalized in _LOOPBACK_HOSTS:
        return
    if normalized in _WILDCARD_HOSTS:
        raise ServingBindError("0.0.0.0 无服务端鉴权不是 Serving Done")
    raise ServingBindError("非回环地址且无服务端鉴权不是 Serving Done")


def bearer_token(authorization: str | None) -> str | None:
    """从 Authorization 取出 Bearer 凭证。其它方案视为未提供。"""
    if authorization is None:
        return None
    parts = authorization.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def api_key_token(value: str | None) -> str | None:
    """从 X-API-Key 取出凭证。空白视为未提供。"""
    if value is None:
        return None
    text = value.strip()
    return text or None


def _secret_equal(left: str, right: str) -> bool:
    a = left.encode("utf-8")
    b = right.encode("utf-8")
    if len(a) != len(b):
        return False
    return hmac.compare_digest(a, b)


def match_serving_identity(
    key_map: dict[str, str],
    *,
    bearer: str | None,
    api_key: str | None,
) -> ServingIdentity | None:
    """用服务端映射核对 Bearer 或 API key。两种凭证同时出现且不一致则拒绝。"""
    if not key_map:
        return None
    if bearer is not None and api_key is not None and not _secret_equal(bearer, api_key):
        return None
    presented = bearer if bearer is not None else api_key
    if presented is None:
        return None
    kind = "bearer" if bearer is not None else "api_key"
    found: ServingIdentity | None = None
    for token, tenant in key_map.items():
        if _secret_equal(presented, token):
            found = ServingIdentity(tenant_id=tenant, credential=kind)
    return found


def _clean_client_tenant(value: str | None) -> str | None:
    """空白声明视为未提供。不把空白收成 default。"""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _unauthorized() -> JSONResponse:
    return JSONResponse(
        {
            "ok": False,
            "code": SERVING_UNAUTHORIZED,
            "message": "缺少或错误的服务端凭证",
        },
        status_code=401,
    )


def _tenant_mismatch() -> JSONResponse:
    return JSONResponse(
        {
            "ok": False,
            "code": SERVING_TENANT_MISMATCH,
            "message": "客户端 tenant_id 与服务端身份映射不一致",
        },
        status_code=403,
    )


def authorize_session(request: Request, client_tenants: list[str | None]) -> JSONResponse:
    """先认证，再核对客户端 tenant 声明。声明缺失时身份仍只取映射。"""
    key_map, fault = load_serving_key_map()
    if fault is not None or not key_map:
        return _unauthorized()
    bearer = bearer_token(request.headers.get("authorization"))
    api_key = api_key_token(request.headers.get(SERVING_API_KEY_HEADER))
    identity = match_serving_identity(key_map, bearer=bearer, api_key=api_key)
    if identity is None:
        return _unauthorized()
    cleaned = [
        tenant for tenant in (_clean_client_tenant(value) for value in client_tenants)
        if tenant is not None
    ]
    if len(set(cleaned)) > 1:
        return _tenant_mismatch()
    client_tenant = cleaned[0] if cleaned else None
    resolved, denied = resolve_pre_retrieval_tenant(identity.tenant_id, client_tenant)
    if denied is not None or resolved is None:
        return _tenant_mismatch()
    return JSONResponse(
        {
            "ok": True,
            "tenant_id": resolved,
            "credential": identity.credential,
        },
        status_code=200,
    )


def readiness_body() -> tuple[dict[str, str], int]:
    """就绪表示服务端凭证映射已配置且格式合法。存活不在这里判断。"""
    key_map, fault = load_serving_key_map()
    if fault is not None:
        return {"readiness": "not_ready", "reason": fault}, 503
    if not key_map:
        return {"readiness": "not_ready", "reason": SERVING_AUTH_UNCONFIGURED}, 503
    return {"readiness": "ok"}, 200


@app.get("/health/live")
def health_live() -> dict[str, str]:
    """存活：进程能应答。不表示鉴权已配置，也不携带租户。"""
    return {"liveness": "ok"}


@app.get("/health/ready")
def health_ready() -> JSONResponse:
    """就绪：服务端凭证映射可用。未配置或格式错误为 503。"""
    body, status = readiness_body()
    return JSONResponse(body, status_code=status)


@app.get("/health")
def health() -> JSONResponse:
    """同时给出存活与就绪字段。进程能应答则为 200，就绪与否看字段。"""
    body, _status = readiness_body()
    return JSONResponse({"liveness": "ok", **body}, status_code=200)


@app.get("/api/session")
def api_session_get(request: Request, tenant_id: str | None = None) -> JSONResponse:
    """受保护会话。查询参数 tenant_id 不能单独放行。"""
    return authorize_session(request, [tenant_id])


@app.post("/api/session")
def api_session_post(
    request: Request,
    body: SessionBody,
    tenant_id: str | None = None,
) -> JSONResponse:
    """受保护会话。查询参数与请求体的 tenant_id 都不能单独放行。"""
    return authorize_session(request, [tenant_id, body.tenant_id])


def run() -> None:
    """启动 Serving。默认只绑回环；无映射时拒绝 0.0.0.0。"""
    host = resolve_serving_bind_host()
    key_map, fault = load_serving_key_map()
    keys_configured = fault is None and bool(key_map)
    refuse_unauthenticated_bind(host, keys_configured=keys_configured)
    import uvicorn

    port_text = (os.environ.get(SERVING_PORT_ENV) or "").strip()
    port = int(port_text) if port_text else SERVING_DEFAULT_PORT
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
