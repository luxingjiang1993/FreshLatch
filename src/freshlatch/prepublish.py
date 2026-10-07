"""发前列表与 Run 摘要投影(ADR-0027 / #173)。

改编 mission_control 列表壳的信息架构(列表→详情),业务字段换
Run / disposition;不引入编排角色名,不重写 HumanLatch。
详情仍走既有复验单,本模块只做摘要投影与包结论消费。
"""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Literal, Sequence

from freshlatch.disposition import (
    DISPOSITIONS,
    ClaimDispositionInput,
    Disposition,
    aggregate_disposition,
)
from freshlatch.models import Claim

# Run 状态封闭词表(发前 UX;非编排角色名)
RunStatus = Literal["未复验", "复验中", "待人审", "已落档"]
RUN_STATUSES: frozenset[str] = frozenset({"未复验", "复验中", "待人审", "已落档"})

_GATE_CODE_RE = re.compile(r"\[闸打回:([^\]]+)\]")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def claim_to_disposition_input(claim: Claim) -> ClaimDispositionInput:
    """主张 → disposition 输入向量(voided/续命映射人审收口;不改底层词表)。"""
    human_action = None
    if claim.voided:
        human_action = "discard"
    elif claim.last_confirmed_at:
        human_action = "renew"
    status = claim.status if claim.status in ("fresh", "stale", "unknown", "void") else "unknown"
    return ClaimDispositionInput(status=status, human_action=human_action, has_gap=False)


def disposition_for_claims(claims: Iterable[Claim]) -> Disposition:
    """报告级包结论:只消费 aggregate_disposition,禁止平行发明词。"""
    return aggregate_disposition(claim_to_disposition_input(c) for c in claims)


def project_gate_results(claims: Sequence[Claim]) -> list[dict[str, Any]]:
    """逐条闸结果投影(可见 error_code / 是否闸过;不升格为 latch 证明)。"""
    rows: list[dict[str, Any]] = []
    for c in claims:
        m = _GATE_CODE_RE.search(c.reason or "")
        error_code = m.group(1) if m else None
        rows.append({
            "claim_id": c.claim_id,
            "status": c.status,
            "voided": bool(c.voided),
            "gate_rejected": error_code is not None,
            "error_code": error_code,
            "reason": c.reason or "",
        })
    return rows


def list_t1_checksums(store: Any) -> list[dict[str, str]]:
    """T1 文档 checksum 列表(读 documents 表;空 checksum 仍列出以便可见)。"""
    if store is None:
        return []
    conn_factory = getattr(store, "_conn", None)
    if conn_factory is None:
        return []
    with conn_factory() as conn:
        rows = conn.execute(
            "SELECT doc_id, title, checksum, doc_version FROM documents "
            "WHERE as_of = 'T1' ORDER BY doc_id"
        ).fetchall()
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for r in rows:
        doc_id = r["doc_id"]
        if doc_id in seen:
            continue
        seen.add(doc_id)
        out.append({
            "doc_id": doc_id,
            "title": r["title"] or "",
            "checksum": r["checksum"] or "",
            "doc_version": r["doc_version"] or "",
        })
    return out


def list_archived_t1_evidence_ids(store: Any) -> list[str]:
    """本库已入库 T1 证据 id(形如 doc_id#clause@T1),供 confirm_patch ⊆ 硬闸。

    SQLite:读 chunks 表;InMemoryStore:读内存 _chunks。空 store → []。
    """
    if store is None:
        return []
    from freshlatch.store.base import chunk_evidence_id

    conn_factory = getattr(store, "_conn", None)
    if conn_factory is not None:
        with conn_factory() as conn:
            rows = conn.execute(
                "SELECT doc_id, clause_id, as_of FROM chunks WHERE as_of = 'T1' "
                "ORDER BY doc_id, clause_id"
            ).fetchall()
        out: list[str] = []
        seen: set[str] = set()
        for r in rows:
            eid = f"{r['doc_id']}#{r['clause_id']}@{r['as_of']}"
            if eid in seen:
                continue
            seen.add(eid)
            out.append(eid)
        return out

    chunks = getattr(store, "_chunks", None)
    if chunks is None:
        return []
    out = []
    seen = set()
    for c in chunks:
        if getattr(c, "as_of", None) != "T1":
            continue
        eid = chunk_evidence_id(c)
        if eid in seen:
            continue
        seen.add(eid)
        out.append(eid)
    return out


def derive_run_status(*, running: bool, latch: dict | None) -> RunStatus:
    """由会话态推导 Run 状态(与 latch 线程对齐,不发明第四套处置词)。"""
    if running:
        return "复验中"
    thread_id = (latch or {}).get("thread_id")
    if thread_id:
        return "待人审"
    return "已落档"


@dataclass
class RunSummary:
    """发前列表一行:标题/来源、disposition、更新时间、Run 状态。"""

    run_id: str
    title: str
    source: str
    disposition: Disposition
    updated_at: str
    status: RunStatus
    claim_count: int = 0
    pack_id: str = ""
    trajectory: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        assert d["disposition"] in DISPOSITIONS
        assert d["status"] in RUN_STATUSES
        return d


@dataclass
class PrepublishRegistry:
    """进程内发前 Run 摘要表(列表壳;详情仍进既有复验单)。"""

    runs: dict[str, RunSummary] = field(default_factory=dict)
    active_run_id: str | None = None

    def clear(self) -> None:
        self.runs.clear()
        self.active_run_id = None

    def upsert(
        self,
        *,
        run_id: str | None,
        title: str,
        source: str,
        claims: Sequence[Claim],
        status: RunStatus,
        pack_id: str = "",
        trajectory: str | None = None,
        updated_at: str | None = None,
    ) -> RunSummary:
        rid = run_id or self.active_run_id or f"run-{uuid.uuid4().hex[:10]}"
        summary = RunSummary(
            run_id=rid,
            title=title or "(无标题)",
            source=source or "(无来源)",
            disposition=disposition_for_claims(claims),
            updated_at=updated_at or _utc_now(),
            status=status,
            claim_count=len(claims),
            pack_id=pack_id,
            trajectory=trajectory,
        )
        self.runs[rid] = summary
        self.active_run_id = rid
        return summary

    def list_runs(self) -> list[dict[str, Any]]:
        """按更新时间倒序。"""
        items = sorted(self.runs.values(), key=lambda r: r.updated_at, reverse=True)
        return [r.to_dict() for r in items]

    def get(self, run_id: str) -> RunSummary | None:
        return self.runs.get(run_id)
