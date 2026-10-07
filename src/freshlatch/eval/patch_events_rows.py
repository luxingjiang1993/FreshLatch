"""四臂与消融共用的记录行检查。不抽随机数，不读密钥。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def cost_note(records: Sequence[Mapping[str, Any]]) -> str:
    if any(_number(row.get("cost")) > 0 for row in records):
        return ""
    return "没有调用"


def reject_duplicate_claim_ids(rows: Sequence[Mapping[str, Any]]) -> None:
    seen: set[str] = set()
    for row in rows:
        claim_id = str(row["claim_id"])
        if claim_id in seen:
            raise ValueError(f"claim_id 重复: {claim_id}")
        seen.add(claim_id)
