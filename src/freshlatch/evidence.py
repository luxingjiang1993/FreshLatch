"""evidence_id / as_of 的调用边界校验:Lead / Critic 共享(#16 白名单、§3.4 词表)。

fail-closed 且零副作用:校验不通过返回错误串,由工具层回给模型自我纠正。
每个角色仍持自己的 `_seen_evidence`。Lead 把它钉成 turn-scoped TurnRegistry:
本轮 retrieve 见过的 evidence_id。本模块只收集合,不做状态。
registry 外的 id 返回可枚举 reason `cite_outside_registry`。
"""

from __future__ import annotations

from collections.abc import Iterable


# 轨迹事件与测试共用这一枚拒因码。不是 insufficient_evidence。
CITE_OUTSIDE_REGISTRY = "cite_outside_registry"


class TurnRegistry(set[str]):
    """本轮 turn-scoped evidence registry。

    一次复验会话里 retrieve 返回过的 evidence_id。
    只含本实例 admit 进来的 id,不跨主张,不读金标。
    集合接口与 set 相同,既有 `.add` 仍然可用。
    """

    def admit(self, evidence_ids: Iterable[str]) -> None:
        """登记本轮 retrieve 返回的 evidence_id。"""
        self.update(evidence_ids)


def valid_as_of(value) -> str | None:
    """as_of 校验(调用边界硬校验,非法值整 call 拒绝并回列合法值,§3.4 惯例)。"""
    if value in (None, "", "T0", "T1"):
        return value or None
    raise ValueError("as_of 只能是 T0|T1,收到: %r" % value)


def registry_refusal_code(err: str | None) -> str | None:
    """错误串以 cite_outside_registry 起头时返回该码。空 id 与非 @T1 没有这枚码。"""
    if err is None:
        return None
    if err == CITE_OUTSIDE_REGISTRY or err.startswith(f"{CITE_OUTSIDE_REGISTRY}:"):
        return CITE_OUTSIDE_REGISTRY
    return None


def check_evidence_ids(raw: object, seen: set[str], *, require_t1: bool) -> tuple[list[str] | None, str | None]:
    """id 必须逐字来自本轮 TurnRegistry;require_t1 时还必须锚 T1。

    registry 外的 id 整 call 拒绝,错误串以 cite_outside_registry 起头。
    """
    ids = [str(e).strip() for e in (raw or []) if str(e).strip()]
    if not ids:
        return None, "evidence_ids 不能为空(必须引用 retrieve 返回的证据块)"
    unknown = [e for e in ids if e not in seen]
    if unknown:
        return None, (
            f"{CITE_OUTSIDE_REGISTRY}: evidence_ids 必须逐字来自本轮 TurnRegistry"
            f"(retrieve 返回的 evidence_id),未检索到: {unknown}"
        )
    if require_t1:
        not_t1 = [e for e in ids if not e.endswith("@T1")]
        if not_t1:
            return None, f"引用的证据必须锚 T1 快照(id 以 @T1 结尾),收到: {not_t1}"
    return ids, None
