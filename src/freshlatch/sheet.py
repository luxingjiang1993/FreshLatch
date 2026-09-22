"""复验单共享投影与 Markdown 导出(K4)。

真源:内存 Claim ⊕ 审计表(latch_log / rerun_log)合并投影——与复验单 UI 卡片同构。
导出写 voided,不伪造 status=void。CLI 读快照 JSON,不现场跑复验。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.store.base import RetrievalStore

# 人审动作时间线文案(后端唯一生成;重跑文案走 HumanLatch.timeline_label)
LATCH_EVENT_LABELS = {"discard": "人审作废", "renew": "人审续命"}


def project_claim(store: RetrievalStore, claim: Claim) -> dict[str, Any]:
    """Claim ⊕ 审计表 → UI/导出/对账单测同吃的字典投影。"""
    # 时间线 = 重跑(rerun_log)+ 人审动作(latch_log 的作废/续命)两条审计迹按 ts 合并;
    # rerun 同时写两表,只从 rerun_log 计一次,不重复。单一真相在库表。
    events = [
        {
            **t,
            "kind": "rerun",
            "evidence_id": None,
            "label": HumanLatch.timeline_label(t["verdict"], t["nth"]),
        }
        for t in store.list_reruns(claim.claim_id)
    ]
    events += [
        {
            "kind": e["action"],
            "ts": e["ts"],
            "thread_id": None,
            "note": "",
            "evidence_id": e["evidence_id"],
            "label": LATCH_EVENT_LABELS.get(e["action"], e["action"]),
        }
        for e in store.list_latch_events(claim.claim_id)
        if e["action"] != "rerun"
    ]
    events.sort(key=lambda e: e["ts"])
    return {
        "claim_id": claim.claim_id,
        "statement": claim.statement,
        "t0_evidence_ids": list(claim.t0_evidence_ids),
        "t1_evidence_ids": list(claim.t1_evidence_ids),
        "status": claim.status,
        "reason": claim.reason,
        "voided": claim.voided,
        "voided_at": claim.voided_at,
        "last_confirmed_at": claim.last_confirmed_at,  # 续命时间戳(§5.4)
        "validity_basis": claim.validity_basis,  # 续命写的新有效性依据(§5.4)
        "timeline": events,
    }


def claim_from_dict(raw: dict[str, Any]) -> Claim:
    """快照 JSON 单条主张 → Claim(忽略未知键)。"""
    return Claim(
        claim_id=raw["claim_id"],
        statement=raw["statement"],
        t0_evidence_ids=list(raw.get("t0_evidence_ids") or []),
        t1_evidence_ids=list(raw.get("t1_evidence_ids") or []),
        dimension=raw.get("dimension"),
        status=raw.get("status") or "unknown",
        reason=raw.get("reason") or "",
        last_confirmed_at=raw.get("last_confirmed_at"),
        validity_basis=raw.get("validity_basis"),
        voided=bool(raw.get("voided", False)),
        voided_at=raw.get("voided_at"),
        dissent=raw.get("dissent"),
    )


def load_snapshot(path: str | Path) -> dict[str, Any]:
    """读复验单快照 JSON。须含 claims;可选 question / store(或 db)。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "claims" not in data:
        raise ValueError("快照须为含 claims 数组的 JSON 对象")
    if not isinstance(data["claims"], list):
        raise ValueError("快照 claims 须为数组")
    return data


def _fmt_evidence_ids(proj: dict[str, Any]) -> str:
    ids = list(proj.get("t0_evidence_ids") or []) + list(proj.get("t1_evidence_ids") or [])
    return ", ".join(f"`{eid}`" for eid in ids) if ids else "(无)"


def _fmt_timeline(proj: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for ev in proj.get("timeline") or []:
        label = ev.get("label") or ev.get("kind") or ""
        ts = ev.get("ts") or ""
        eid = ev.get("evidence_id")
        note = ev.get("note") or ""
        parts = [f"- {ts} · {label}".rstrip(" ·")]
        if eid:
            parts.append(f"  evidence_id: `{eid}`")
        if note:
            parts.append(f"  note: {note}")
        lines.append("\n".join(parts) if len(parts) > 1 else parts[0])
    return lines


def render_claim_markdown(proj: dict[str, Any]) -> str:
    """单主张 Markdown 块(对齐 UI 卡片字段;写 voided 不伪造 status=void)。"""
    void_mark = "【已作废·灰显】" if proj.get("voided") else ""
    title = f"## {proj['claim_id']} {void_mark}".rstrip()
    lines = [
        title,
        "",
        proj.get("statement") or "",
        "",
        f"- **判定**: `{proj.get('status')}`",
        f"- **作废(voided)**: {'是' if proj.get('voided') else '否'}"
        + (f" · `{proj['voided_at']}`" if proj.get("voided_at") else ""),
        f"- **理由**: {proj.get('reason') or '(空)'}",
        f"- **原文点回(evidence_id)**: {_fmt_evidence_ids(proj)}",
        f"- **续命 last_confirmed_at**: "
        f"{'`' + proj['last_confirmed_at'] + '`' if proj.get('last_confirmed_at') else '(无)'}",
        f"- **续命 validity_basis**: "
        f"{json.dumps(proj['validity_basis'], ensure_ascii=False) if proj.get('validity_basis') else '(无)'}",
        "- **人审/重跑时间线**:",
    ]
    tl = _fmt_timeline(proj)
    if tl:
        lines.extend(tl)
    else:
        lines.append("- (空)")
    return "\n".join(lines)


def render_sheet_markdown(
    projections: list[dict[str, Any]],
    *,
    question: str = "",
) -> str:
    """全量复验单 Markdown。"""
    parts = [
        "# 复验单",
        "",
        f"**问题**: {question or '(未提供)'}",
        "",
        f"**主张数**: {len(projections)}",
        "",
    ]
    for proj in projections:
        parts.append(render_claim_markdown(proj))
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def export_sheet_from_snapshot(
    snapshot_path: str | Path,
    store: RetrievalStore,
    *,
    out_path: str | Path | None = None,
) -> str:
    """读快照 → 投影 → Markdown;可选落盘。返回 Markdown 文本。"""
    snap = load_snapshot(snapshot_path)
    claims = [claim_from_dict(c) for c in snap["claims"]]
    projections = [project_claim(store, c) for c in claims]
    md = render_sheet_markdown(projections, question=str(snap.get("question") or ""))
    if out_path is not None:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
    return md
