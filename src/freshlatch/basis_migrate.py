"""显式批迁:存量 validity_basis 单对象 dict → 一元 list(ADR-0024 / #150)。

禁止把读时懒包当作唯一迁移手段;本模块供脚本/一次性步骤调用。
验收目标:库内/快照无 dict 形状残留。不得升格为 latch 证明。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from freshlatch.models import Claim


def migrate_claim_validity_basis(claim: Claim) -> bool:
    """原地把 claim.validity_basis 从 dict 迁成一元 list。

    返回是否发生写回。已是 list / None 不改。
    """
    raw = claim.validity_basis
    if isinstance(raw, dict):
        claim.validity_basis = [raw]
        return True
    return False


def migrate_claims(claims: list[Claim]) -> int:
    """批量迁移;返回发生写回的条数。"""
    return sum(1 for c in claims if migrate_claim_validity_basis(c))


def migrate_snapshot_dict(data: dict[str, Any]) -> int:
    """迁移快照 JSON 对象内 claims[*].validity_basis;返回写回条数。"""
    claims = data.get("claims")
    if not isinstance(claims, list):
        return 0
    n = 0
    for raw in claims:
        if not isinstance(raw, dict):
            continue
        basis = raw.get("validity_basis")
        if isinstance(basis, dict):
            raw["validity_basis"] = [basis]
            n += 1
    return n


def migrate_snapshot_file(path: str | Path, *, write: bool = True) -> int:
    """读快照 → 迁 → 可选写回。返回写回条数。"""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("快照须为 JSON 对象")
    n = migrate_snapshot_dict(data)
    if write and n:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n
