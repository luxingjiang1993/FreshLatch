"""evidence_id / as_of 的调用边界校验:Lead / Critic 共享(#16 白名单、§3.4 词表)。

fail-closed 且零副作用:校验不通过返回错误串或抛 ValueError,由工具层回给模型自我纠正;
每个角色仍持自己的 `_seen_evidence`(会话级 retrieve 白名单),本模块只收集合不做状态。
"""

from __future__ import annotations


def valid_as_of(value) -> str | None:
    """as_of 校验(调用边界硬校验,非法值整 call 拒绝并回列合法值,§3.4 惯例)。"""
    if value in (None, "", "T0", "T1"):
        return value or None
    raise ValueError("as_of 只能是 T0|T1,收到: %r" % value)


def check_evidence_ids(raw: object, seen: set[str], *, require_t1: bool) -> tuple[list[str] | None, str | None]:
    """#16 白名单:id 必须逐字来自本会话 retrieve 返回;require_t1 时还必须锚 T1。"""
    ids = [str(e).strip() for e in (raw or []) if str(e).strip()]
    if not ids:
        return None, "evidence_ids 不能为空(必须引用 retrieve 返回的证据块)"
    unknown = [e for e in ids if e not in seen]
    if unknown:
        return None, f"evidence_ids 必须逐字来自本会话 retrieve 返回的 evidence_id,未检索到: {unknown}"
    if require_t1:
        not_t1 = [e for e in ids if not e.endswith("@T1")]
        if not_t1:
            return None, f"引用的证据必须锚 T1 快照(id 以 @T1 结尾),收到: {not_t1}"
    return ids, None
