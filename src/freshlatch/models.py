"""共享内存模型。语料/金标单一真相在 data/,本模块只是运行时对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Status = Literal["fresh", "stale", "unknown", "void"]
AsOf = Literal["T0", "T1"]


@dataclass
class Claim:
    """主张(§2.2 schema)。statement 与 t0_evidence_ids 导入后只读。"""

    claim_id: str
    statement: str
    t0_evidence_ids: list[str] = field(default_factory=list)
    t1_evidence_ids: list[str] = field(default_factory=list)
    status: Status = "unknown"
    reason: str = ""
    last_confirmed_at: str | None = None
    validity_basis: dict | None = None  # {doc_id, checksum},W5 起续命写入
    voided: bool = False  # 人的决定(ADR-0006 §3);与 status 的机器判定并存不互斥
    voided_at: str | None = None
