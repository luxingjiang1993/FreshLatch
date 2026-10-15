"""检索前 ACL。tenant_id 只由服务端会话注入。"""

from __future__ import annotations

from freshlatch.store.base import Chunk, Document

# 检索前 ACL 拒绝码。观察回给调用方,不表示检索已执行。
REASON_TENANT_ACL_DENIED = "tenant_acl_denied"


class TenantAclError(RuntimeError):
    """生产检索入口拒绝:缺服务端 tenant_id,或工具参数与会话不一致。"""

    def __init__(self, payload: dict) -> None:
        super().__init__(str(payload.get("error") or "tenant ACL denied"))
        self.payload = payload


def resolve_pre_retrieval_tenant(
    server_tenant: str | None,
    tool_tenant: str | None,
) -> tuple[str | None, dict | None]:
    """检索前 ACL。返回 (服务端 tenant, None) 或 (None, 拒绝观察)。

    服务端 tenant_id 是唯一过滤真相,不信任模型输出或客户端 filter。
    工具参数缺省视为未声明;有值则必须与会话一致,否则拒绝。
    缺服务端 tenant 或空白时 fail-closed。调用方不得再检索,禁止退回全库。
    """
    if server_tenant is None or not str(server_tenant).strip():
        return None, {
            "error": "缺少服务端 tenant_id,检索 fail-closed",
            "reason_code": REASON_TENANT_ACL_DENIED,
            "fail_closed": True,
        }
    server = str(server_tenant).strip()
    if tool_tenant is not None and str(tool_tenant).strip() and str(tool_tenant).strip() != server:
        tool = str(tool_tenant).strip()
        return None, {
            "error": (
                f"工具参数 tenant_id={tool} 与会话 tenant_id={server} 不一致,拒绝检索"
            ),
            "reason_code": REASON_TENANT_ACL_DENIED,
            "fail_closed": True,
        }
    return server, None


def retrieve_for_session(
    store,
    query: str,
    *,
    server_tenant_id: str | None,
    tool_tenant: str | None = None,
    as_of: str | None = None,
    source_type: str | None = None,
    top_k: int = 10,
    patch_id: str | None = None,
    valid_at: str | None = None,
):
    """生产检索入口:先解析服务端 tenant_id,再调用 retrieve。拒绝时不读库。"""
    resolved, denied = resolve_pre_retrieval_tenant(server_tenant_id, tool_tenant)
    if denied is not None:
        raise TenantAclError(denied)
    return store.retrieve(
        query,
        as_of=as_of,
        source_type=source_type,
        top_k=top_k,
        tenant_id=resolved,
        patch_id=patch_id,
        valid_at=valid_at,
    )


def _declared_tenant_conflict(
    resolved: str,
    doc: Document,
    chunks: list[Chunk],
) -> dict | None:
    """对象上的 tenant_id 必须与已解析的服务端租户一致。空白不算另立租户。"""
    declared = [doc.tenant_id]
    declared.extend(chunk.tenant_id for chunk in chunks)
    for raw in declared:
        text = str(raw).strip()
        if text and text != resolved:
            return {
                "error": (
                    f"写入对象 tenant_id={text} 与会话 tenant_id={resolved} 不一致,拒绝写入"
                ),
                "reason_code": REASON_TENANT_ACL_DENIED,
                "fail_closed": True,
            }
    return None


def write_for_session(
    store,
    doc: Document,
    chunks: list[Chunk],
    *,
    server_tenant_id: str | None,
    tool_tenant: str | None = None,
) -> None:
    """写入前 ACL。拒绝时不调用 add_document。

    服务端 tenant_id 是唯一写入归属。工具参数或对象自身的 tenant_id
    与会话不一致则 fail-closed,不把对象改写进调用方声明的租户。
    """
    resolved, denied = resolve_pre_retrieval_tenant(server_tenant_id, tool_tenant)
    if denied is not None:
        raise TenantAclError(denied)
    conflict = _declared_tenant_conflict(resolved, doc, chunks)
    if conflict is not None:
        raise TenantAclError(conflict)
    store.add_document(doc, chunks)
