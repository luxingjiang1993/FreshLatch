"""跨租户读 / 写 / 会话的 Serving 入口。

身份只来自 authorize_session 核对过的服务端凭证映射。
客户端单独提交的 tenant_id 不构成访问权。
薄 ACL 不等于完整 SaaS 多租户。
"""

from __future__ import annotations

import json

from starlette.requests import Request

from freshlatch.serving.app import authorize_session
from freshlatch.store.base import Chunk, Document
from freshlatch.store.tenant_acl import (
    TenantAclError,
    retrieve_for_session,
    write_for_session,
)

_ACTIONS = frozenset({"read", "write", "session"})


def _request(authorization: str | None, api_key: str | None) -> Request:
    """只带凭证头。tenant_id 不进头,避免把客户端声明当成身份。"""
    headers: list[tuple[bytes, bytes]] = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode("utf-8")))
    if api_key is not None:
        headers.append((b"x-api-key", api_key.encode("utf-8")))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/session",
        "raw_path": b"/api/session",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 0),
        "server": ("127.0.0.1", 8001),
    }
    return Request(scope)


def _http_denial(action: str, status_code: int, body: dict) -> dict:
    return {
        "ok": False,
        "fail_closed": True,
        "action": action,
        "status_code": status_code,
        "code": body.get("code"),
    }


def _acl_denial(action: str, payload: dict) -> dict:
    return {
        "ok": False,
        "fail_closed": True,
        "action": action,
        "code": payload.get("reason_code"),
        "error": payload.get("error"),
    }


def enforce_mapped_action(
    store,
    action: str,
    *,
    authorization: str | None = None,
    api_key: str | None = None,
    client_tenant: str | None = None,
    query: str = "",
    document: Document | None = None,
    chunks: list[Chunk] | None = None,
) -> dict:
    """先走 authorize_session,再按服务端租户读或写。拒绝时不碰库。"""
    if action not in _ACTIONS:
        raise ValueError(f"未知 ACL 动作: {action}")
    response = authorize_session(
        _request(authorization, api_key),
        [client_tenant],
    )
    body = json.loads(bytes(response.body))
    if response.status_code != 200 or body.get("ok") is not True:
        return _http_denial(action, response.status_code, body)
    server_tenant = body["tenant_id"]
    if action == "session":
        return {
            "ok": True,
            "fail_closed": False,
            "action": action,
            "status_code": response.status_code,
            "code": "ok",
            "tenant_id": server_tenant,
            "credential": body.get("credential"),
        }
    if action == "read":
        try:
            hits = retrieve_for_session(
                store,
                query,
                server_tenant_id=server_tenant,
                tool_tenant=client_tenant,
            )
        except TenantAclError as exc:
            return _acl_denial(action, exc.payload)
        return {
            "ok": True,
            "fail_closed": False,
            "action": action,
            "tenant_id": server_tenant,
            "hits": hits,
        }
    if document is None:
        raise ValueError("写入动作缺少文档")
    try:
        write_for_session(
            store,
            document,
            list(chunks or []),
            server_tenant_id=server_tenant,
            tool_tenant=client_tenant,
        )
    except TenantAclError as exc:
        return _acl_denial(action, exc.payload)
    return {
        "ok": True,
        "fail_closed": False,
        "action": action,
        "tenant_id": server_tenant,
    }
