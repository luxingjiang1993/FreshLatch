"""主张导入稿解析:Markdown/粘贴 → 与复验单同构的主张列表。

约定(CONTEXT / #88):每条以 ``## claim_id`` 起头、其后正文一段;
缺 id 时系统分配 ``c-import-N``。只承载已签发主张,不做自由散文抽主张或 LLM 切分。
JSON docket 仍由 ``load_docket`` 作为高级入口,本模块不替代。
"""

from __future__ import annotations

import re

from freshlatch.models import Claim
from freshlatch.runner import Docket

_H1_QUESTION = re.compile(r"(?m)^#\s+(.+)$")
# 只切真正的 H2(##),不误伤 ### 及更深标题
_SPLIT_H2 = re.compile(r"(?m)^##(?!#)[ \t]*")


class ClaimImportError(ValueError):
    """主张导入稿无法解析为至少一条主张。"""


def parse_claim_import_draft(text: str, *, question: str | None = None) -> tuple[Docket, list[str]]:
    """解析主张导入稿。

    Returns:
        (Docket, assigned_ids):assigned_ids 为系统分配的 ``c-import-N`` 列表(可追溯)。
    """
    if not isinstance(text, str):
        raise ClaimImportError("主张导入稿 text 必须为字符串")
    raw = text.replace("\r\n", "\n").replace("\r", "\n")
    q = "" if question is None else question.strip()
    parts = _SPLIT_H2.split(raw)
    preamble = parts[0] if parts else ""
    if not q:
        m = _H1_QUESTION.search(preamble)
        if m:
            q = m.group(1).strip()

    claims: list[Claim] = []
    assigned: list[str] = []
    auto_n = 0
    for block in parts[1:]:
        if not block.strip():
            continue
        if "\n" in block:
            heading, body = block.split("\n", 1)
        else:
            heading, body = block, ""
        heading = heading.strip()
        body = body.strip()
        if not body:
            continue
        if heading:
            claim_id = heading.split()[0]
        else:
            auto_n += 1
            claim_id = f"c-import-{auto_n}"
            assigned.append(claim_id)
        claims.append(Claim(claim_id=claim_id, statement=body))

    if not claims:
        raise ClaimImportError("主张导入稿未解析出任何主张(需 ## claim_id + 正文)")
    return Docket(question=q, claims=claims), assigned
