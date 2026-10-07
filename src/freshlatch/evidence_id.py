"""evidence_id 的单一解析。

最后一个 ``#`` 分开 doc_id 与 anchor，最后一个 ``@`` 取 as_of。
as_of 只认 T0|T1。失败、None、非 str 都返回 None。
"""

from __future__ import annotations


def parse_evidence_id(eid: object) -> tuple[str, str, str] | None:
    """``doc_id#anchor@as_of`` → (doc_id, anchor, as_of)。不可解析返回 None。"""
    if not isinstance(eid, str):
        return None
    try:
        body, as_of = eid.rsplit("@", 1)
        doc_id, anchor = body.rsplit("#", 1)
    except ValueError:
        return None
    if not doc_id or not anchor or as_of not in ("T0", "T1"):
        return None
    return doc_id, anchor, as_of
