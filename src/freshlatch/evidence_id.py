"""evidence_id 的单一解析 + 显示层映射。

最后一个 ``#`` 分开 doc_id 与 anchor，最后一个 ``@`` 取 as_of。
as_of 只认 T0|T1。失败、None、非 str 都返回 None。

``display_evidence_id`` 是 I-04（#695 / 决议 #689）的纯显示层 helper：
只把已入库 id 渲成可读句，不反向、不入库、不影响检索/金标契约。
"""

from __future__ import annotations

import re

_ANCHOR_SECTION = re.compile(r"p(\d+)")


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


def display_evidence_id(eid: object) -> str:
    """显示层映射（I-04 #689）：``t0-doc#p2@T1`` → ``文档 doc · 第 2 节 · T1 快照``。

    - 剥 ``t0-`` / ``t1-`` 前缀；无前缀原样作文档名。
    - ``#pN`` → ``第 N 节``；非 p 形 anchor 保留原串。
    - ``@T0`` / ``@T1`` → ``T0 快照`` / ``T1 快照``。
    - 解析失败回退原串（非 str 取 ``str(eid)``；``None`` 得 ``""``）。
    """
    parsed = parse_evidence_id(eid)
    if parsed is None:
        return eid if isinstance(eid, str) else str(eid or "")
    doc_id, anchor, as_of = parsed
    name = doc_id.removeprefix("t0-").removeprefix("t1-")
    section = anchor
    m = _ANCHOR_SECTION.fullmatch(anchor)
    if m:
        section = f"第 {m.group(1)} 节"
    return f"文档 {name} · {section} · {as_of} 快照"
