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
    dimension: str | None = None  # 签发登记维度(ADR-0011;封闭枚举同 FOCUS_DIMENSIONS,load_docket 硬校验)
    status: Status = "unknown"
    reason: str = ""
    last_confirmed_at: str | None = None
    # ADR-0024 / #149:目标形状 list[{doc_id, checksum}];renew 写一元 list;历史 dict 读侧过渡归一
    validity_basis: list[dict] | None = None
    voided: bool = False  # 人的决定(ADR-0006 §3);与 status 的机器判定并存不互斥
    voided_at: str | None = None
    dissent: dict | None = None  # 异议记录(ADR-0009/0010/0012):{kind, auditor_verdict, reason, evidence_ids}
    # kind:auditor_semantic(不变量7)/mechanical_crosscheck(不变量8)/mechanical_precheck(ADR-0012 受理层)
