"""报告级包结论(disposition)纯函数聚合层(ADR-0027 / #170)。

输入主张态(fresh/stale/unknown/void)与人审收口标志(discard/renew),
输出仅三值:可发 / 需补丁 / 勿发。禁止第四套正式状态词。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Sequence

# 封闭三值——契约唯一出口;UI/API 不得另造近义词
Disposition = Literal["可发", "需补丁", "勿发"]
DISPOSITIONS: frozenset[str] = frozenset({"可发", "需补丁", "勿发"})

ClaimStatus = Literal["fresh", "stale", "unknown", "void"]
HumanAction = Literal["discard", "renew"]

# 人审收口动作:与 HumanLatch discard/renew 对齐(底层词表不改名)
_RESOLVING_ACTIONS: frozenset[str] = frozenset({"discard", "renew"})


@dataclass(frozen=True)
class ClaimDispositionInput:
    """合成主张态向量中的一条(本票表驱动验收用;非持久化模型)。

    status: 主张级机器态(或已 void 的人决终态字面量)
    human_action: 人审收口;None = 未收口
    has_gap: 缺口标志(如缺覆盖);与未处理 unknown 同侧进「需补丁」
    """

    status: ClaimStatus
    human_action: HumanAction | None = None
    has_gap: bool = False


def _is_resolved(row: ClaimDispositionInput) -> bool:
    """已收口:人审 discard/renew,或 status 已为 void。"""
    if row.status == "void":
        return True
    return row.human_action in _RESOLVING_ACTIONS


def _has_unresolved_stale(rows: Sequence[ClaimDispositionInput]) -> bool:
    """任一条未收口 stale → 勿发(ADR-0027 边界 1)。"""
    return any(row.status == "stale" and not _is_resolved(row) for row in rows)


def _has_unresolved_unknown_or_gap(rows: Sequence[ClaimDispositionInput]) -> bool:
    """无未收口 stale 前提下:未处理 unknown 或缺口 → 需补丁(ADR-0027 边界 2)。"""
    for row in rows:
        if row.has_gap:
            return True
        if row.status == "unknown" and not _is_resolved(row):
            return True
    return False


def aggregate_disposition(claims: Iterable[ClaimDispositionInput]) -> Disposition:
    """按 ADR-0027 四条边界聚合报告级包结论。

    优先级:未收口 stale → 勿发;否则未处理 unknown/缺口 → 需补丁;否则 → 可发。
    覆盖:全 fresh 无人审 → 可发;红灯均已 discard/renew 且无未处理 unknown → 可发。
    """
    rows = tuple(claims)
    if _has_unresolved_stale(rows):
        return "勿发"
    if _has_unresolved_unknown_or_gap(rows):
        return "需补丁"
    return "可发"
