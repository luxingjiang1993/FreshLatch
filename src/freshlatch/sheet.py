"""复验单共享投影与 Markdown 导出(K4)+ 客户向复验备忘(ADR-0015)。

真源:内存 Claim ⊕ 审计表(latch_log / rerun_log)合并投影——与复验单 UI 卡片同构。
导出写 voided,不伪造 status=void。CLI 读快照 JSON,不现场跑复验。
客户向备忘复用同一投影,但不含轨迹/人审时间线,并过禁语与字段契约。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from freshlatch.evidence_bound import is_patch_eligible
from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.prepublish import disposition_for_claims
from freshlatch.publish_hook import (
    NEEDS_PATCH_BANNER,
    PublishHookResult,
    evaluate_publish_hook,
)
from freshlatch.reading_source import BYPASS_TEXT, MEMO_NOTE
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
            "override": None,
            "machine_status_before": None,
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
            # override 是派生标签,可在时间线上观察;不表示模型变好
            "override": e.get("override"),
            "machine_status_before": e.get("machine_status_before"),
            "run_id": e.get("run_id"),
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
        # #200:补丁条带入口闸(与 evidence_bound.is_patch_eligible 同口径)
        "patch_eligible": is_patch_eligible(claim),
    }


def project_run_disposition(claims: list[Claim] | tuple[Claim, ...]) -> str:
    """报告级包结论投影(#173):与发前列表/复验单包结论条同吃 disposition 纯函数。"""
    from freshlatch.prepublish import disposition_for_claims

    return disposition_for_claims(claims)


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


def projections_with_override(projections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """审计过滤:时间线含 override=true 的主张。

    过滤只便于抽查人机对抗。结果不是模型变好,也不作 Override Rate 通过线。
    """
    kept: list[dict[str, Any]] = []
    for proj in projections:
        if any(ev.get("override") is True for ev in (proj.get("timeline") or [])):
            kept.append(proj)
    return kept


def _fmt_timeline(proj: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for ev in proj.get("timeline") or []:
        label = ev.get("label") or ev.get("kind") or ""
        ts = ev.get("ts") or ""
        eid = ev.get("evidence_id")
        note = ev.get("note") or ""
        line = f"- {ts} · {label}".rstrip(" ·")
        if ev.get("override") is True:
            line += " · override"
        parts = [line]
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
        BYPASS_TEXT,
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


# ---- 客户向复验备忘 (Client Memo;ADR-0015 / INV-2·INV-3) ----
# 与复验单导出分离:读同一投影,不写轨迹/人审时间线,过禁语与字段契约。

# 禁止项字面:「建议进入/不进入」→ 建议进入 | 建议不进入(不含裸「不进入」,避免误伤)
_CLIENT_MEMO_FORBIDDEN = re.compile(r"Lead|Critic|建议进入|建议不进入")
_CLIENT_MEMO_DISCLAIMER = (
    "免责声明:本备忘非法律意见、非自动商业决策;"
    "仅反映既定 T1 事实下的复验投影,不构成投资或交易建议。"
)


def _sanitize_client_memo_text(text: str) -> str:
    """洗掉角色名与商业裁决禁语,避免投影理由泄漏进客户向正文。"""
    cleaned = _CLIENT_MEMO_FORBIDDEN.sub("", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def _client_memo_bucket(proj: dict[str, Any]) -> str:
    """三分栏归属:已作废优先;仍成立=fresh 且未作废;其余进缺口。"""
    if proj.get("voided"):
        return "voided"
    if (proj.get("status") or "") == "fresh":
        return "held"
    return "gap"


def _client_memo_pointback_ids(proj: dict[str, Any]) -> list[str]:
    """可点回 evidence_id:仅 T1;`doc_id#anchor@as_of`,不做字符级偏移。"""
    return [str(e) for e in (proj.get("t1_evidence_ids") or []) if e]


def _render_client_memo_entry(proj: dict[str, Any], *, gap_no_t1: bool = False) -> str:
    """单条:claim_id + 一句话理由 + 可选 evidence_id 点回。

    「无 T1 覆盖」仅挂在缺口栏(gap_no_t1);仍成立/已作废不强制该文案。
    """
    cid = proj.get("claim_id") or ""
    reason = _sanitize_client_memo_text(str(proj.get("reason") or ""))
    eids = _client_memo_pointback_ids(proj)
    if gap_no_t1:
        if not reason:
            reason = "无 T1 覆盖"
        elif "无 T1 覆盖" not in reason:
            reason = f"{reason};无 T1 覆盖"
    if not reason:
        reason = "(无理由)"
    lines = [f"- **{cid}**: {reason}"]
    for eid in eids:
        # Markdown 链接保留完整 evidence_id,供点回;无字符偏移 span
        lines.append(f"  - 证据: [`{eid}`](evidence:{eid})")
    return "\n".join(lines)


def _render_client_memo_section(
    title: str,
    entries: list[dict[str, Any]],
    *,
    empty_gap_explicit: bool = False,
) -> str:
    parts = [f"## {title}", ""]
    if not entries:
        if empty_gap_explicit:
            parts.append("- 无 T1 覆盖")
        else:
            parts.append("- (无)")
        parts.append("")
        return "\n".join(parts)
    for proj in entries:
        gap_no_t1 = empty_gap_explicit and not _client_memo_pointback_ids(proj)
        parts.append(_render_client_memo_entry(proj, gap_no_t1=gap_no_t1))
        parts.append("")
    return "\n".join(parts)


def _render_dem3_rubric_checklist() -> str:
    """DEM-3 人工勾选面:五条「是」+禁止项「无」;不升格为产品验证。"""
    return "\n".join(
        [
            "## DEM-3 人工 rubric(勾选面;不升格为产品验证)",
            "",
            "以下由人勾选;机器套件只锁字段/禁语边界,勾选结果不作通过线。",
            "",
            "- [ ] 有课题问题句与生成时间戳",
            "- [ ] 有免责声明(非法律意见/非自动决策;可标明 synthetic)",
            "- [ ] 三分栏齐全:仍成立/已作废/缺口",
            "- [ ] 每条有 claim_id + 一句话理由",
            "- [ ] 至少一条带可点回 evidence_id,或缺口栏显式写「无 T1 覆盖」",
            "- [ ] 禁止项全无:无「建议进入/不进入」;默认备忘正文无 Lead/Critic 字样",
            "",
        ]
    )


def render_client_memo_markdown(
    projections: list[dict[str, Any]],
    *,
    question: str = "",
    generated_at: str,
    synthetic: bool = False,
    needs_patch_banner: bool = False,
) -> str:
    """客户向复验备忘 Markdown(ADR-0015 必填字段;禁轨迹与商业裁决句)。

    needs_patch_banner:发前钩子需补丁+ack 放行时强制页眉标明「需补丁」(ADR-0031);
    不扩商业裁决、不写轨迹。
    """
    held: list[dict[str, Any]] = []
    voided: list[dict[str, Any]] = []
    gap: list[dict[str, Any]] = []
    for proj in projections:
        bucket = _client_memo_bucket(proj)
        if bucket == "held":
            held.append(proj)
        elif bucket == "voided":
            voided.append(proj)
        else:
            gap.append(proj)

    disclaimer = _CLIENT_MEMO_DISCLAIMER
    if synthetic:
        disclaimer += "本导出所依据语料标明为 synthetic(合成评测包)。"

    parts = [
        "# 客户向复验备忘",
        "",
    ]
    # 需补丁页眉紧贴标题后,强制可见;字面量与闸约束对齐
    if needs_patch_banner:
        parts.extend([f"**{NEEDS_PATCH_BANNER}**", ""])
    parts.extend(
        [
            f"**课题问题句**: {_sanitize_client_memo_text(question) or '(未提供)'}",
            "",
            f"**生成时间**: {generated_at}",
            "",
            f"**{disclaimer}**",
            "",
            MEMO_NOTE,
            "",
            _render_client_memo_section("仍成立", held),
            _render_client_memo_section("已作废", voided),
            _render_client_memo_section("缺口", gap, empty_gap_explicit=True),
            _render_dem3_rubric_checklist(),
        ]
    )
    return "\n".join(parts).rstrip() + "\n"


def export_client_memo_gated(
    *,
    run_id: str | None,
    disposition: str | None,
    projections: list[dict[str, Any]],
    generated_at: str,
    ack_needs_patch: bool = False,
    checksum_fresh: bool = True,
    question: str = "",
    synthetic: bool = False,
    out_path: str | Path | None = None,
) -> tuple[PublishHookResult, str | None]:
    """Client Memo 套发前钩子闸(#229 / ADR-0031)。

    先 evaluate_publish_hook;deny → 零写 out_path、markdown=None;
    allow → 渲染 ADR-0015 字段集;需补丁+ack 时强制页眉「需补丁」。
    UI/CLI 必须走本函数,禁止平行 if/else 出口。
    """
    hook = evaluate_publish_hook(
        run_id=run_id,
        disposition=disposition,
        ack_needs_patch=ack_needs_patch,
        checksum_fresh=checksum_fresh,
    )
    if not hook.allow:
        return hook, None

    md = render_client_memo_markdown(
        projections,
        question=question,
        generated_at=generated_at,
        synthetic=synthetic,
        needs_patch_banner=hook.requires_needs_patch_banner,
    )
    if out_path is not None:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
    return hook, md


def export_client_memo_from_snapshot(
    snapshot_path: str | Path,
    store: RetrievalStore,
    *,
    generated_at: str,
    out_path: str | Path | None = None,
) -> str:
    """读复验投影 → 客户向备忘 Markdown;不跑复验。可选落盘。

    无闸渲染(字段契约/单测用)。发前导出请走 export_client_memo_from_snapshot_gated。
    """
    snap = load_snapshot(snapshot_path)
    claims = [claim_from_dict(c) for c in snap["claims"]]
    projections = [project_claim(store, c) for c in claims]
    md = render_client_memo_markdown(
        projections,
        question=str(snap.get("question") or ""),
        generated_at=generated_at,
        synthetic=bool(snap.get("synthetic")),
    )
    if out_path is not None:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
    return md


def export_client_memo_from_snapshot_gated(
    snapshot_path: str | Path,
    store: RetrievalStore,
    *,
    run_id: str | None,
    generated_at: str,
    disposition: str | None = None,
    ack_needs_patch: bool = False,
    checksum_fresh: bool = True,
    out_path: str | Path | None = None,
) -> tuple[PublishHookResult, str | None]:
    """快照 → 套闸 Client Memo;deny 零写。disposition 缺省时由主张聚合。"""
    snap = load_snapshot(snapshot_path)
    claims = [claim_from_dict(c) for c in snap["claims"]]
    projections = [project_claim(store, c) for c in claims]
    disp = disposition if disposition is not None else disposition_for_claims(claims)
    # 快照可覆写 run_id(便于夹具自带绑定键)
    rid = run_id if run_id is not None else snap.get("run_id")
    return export_client_memo_gated(
        run_id=str(rid) if rid is not None else None,
        disposition=disp,
        projections=projections,
        generated_at=generated_at,
        ack_needs_patch=ack_needs_patch,
        checksum_fresh=checksum_fresh,
        question=str(snap.get("question") or ""),
        synthetic=bool(snap.get("synthetic")),
        out_path=out_path,
    )
