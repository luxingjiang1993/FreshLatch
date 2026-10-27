"""UI 跨路由投影助手(#755 UI-SPLIT-T1)。

claims / audit / budget / checksum / snapshot 等只读投影;读可变容器走
`freshlatch.ui.session_state`。依赖 `_store` / pack 别名时延迟从 `app` 取
(兼容单测 monkeypatch appmod)。不注册路由、不改闸语义。
"""

from __future__ import annotations

import html
import json
from dataclasses import asdict

from freshlatch.claim_ledger import get_claim_ledger
from freshlatch.models import Claim
from freshlatch.patch_events import iter_events
from freshlatch.prepublish import (
    derive_run_status,
    disposition_for_claims,
    list_archived_t1_evidence_ids,
    list_t1_checksums,
    project_gate_results,
)
from freshlatch.publish_hook import checksums_fresh
from freshlatch.runner import RunContext
from freshlatch.sheet import (
    UI_BADGE_ABSTAIN,
    UI_BADGE_PARTIAL,
    UI_BADGE_VERIFIED,
    annotate_audit_patch_visibility,
    project_audit,
    project_claim,
    project_ui_badges,
)
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.ui import session_state as ss

RUN_SNAPSHOT_VERSION = 1

_LEDGER_SCOPE_NOTE = (
    "历史人审记录(invalidation_list ∪ latch_log),可能含跨次条目;"
    "「重置」只清当前复验单,不擦除本台账。"
    "renew/disputed 不进作废名单;与 patch_events 分缝;写路径仍唯一经 HumanLatch。"
)
_RESET_LEDGER_NOTE = "历史台账仍保留(不擦除 latch_log / 作废名单)"

_UI_BADGE_TOKENS = frozenset({
    UI_BADGE_VERIFIED,
    UI_BADGE_PARTIAL,
    UI_BADGE_ABSTAIN,
})
_CRAFTSMAN_BADGES_TOKEN = "__CRAFTSMAN_BADGES__"


def _budget_from_ctx(ctx: RunContext) -> dict:
    """从 RunContext 投影预算进度(与 Guardrails 字段对齐)。"""
    g = ctx.guardrails
    return {
        "steps_used": ctx.lead_steps_used,
        "lead_max_steps": g.lead_max_steps,
        "retrieval_used": ctx.retrieval_used,
        "retrieval_budget": g.retrieval_budget,
    }


def _current_budget() -> dict:
    """复验中读 live RunContext;完成后读会话摘要。"""
    if ss._state.get("running") and ss._state.get("run_ctx") is not None:
        return _budget_from_ctx(ss._state["run_ctx"])
    return dict(ss._state.get("budget") or ss.EMPTY_BUDGET)


def _run_metrics(store) -> dict:
    """I-14(#713):审计「本轮指标 / 记账」只读投影。"""
    from freshlatch.ui.app import _PATCH_EVENTS_DIR

    run_id = ss._state.get("active_run_id")
    budget = _current_budget()
    claim_ids = {c.claim_id for c in (ss._state.get("claims") or [])}
    patch_events_rows = 0
    if claim_ids:
        patch_events_rows = sum(
            1 for e in iter_events(events_dir=_PATCH_EVENTS_DIR)
            if str(e.get("claim_id") or "") in claim_ids
        )
    latch_log_rows = 0
    if run_id and hasattr(store, "list_latch_rows"):
        latch_log_rows = sum(
            1 for row in store.list_latch_rows() if row.get("run_id") == run_id
        )
    return {
        "run_id": run_id,
        "steps_used": budget["steps_used"],
        "retrieval_used": budget["retrieval_used"],
        "token_usage": ss._state.get("token_usage"),
        "patch_events_rows": patch_events_rows,
        "latch_log_rows": latch_log_rows,
    }


def _pack_payload() -> dict:
    """只读展示当前包。问题句优先用本会话已导入的 docket。"""
    from freshlatch.ui.app import ACTIVE_PACK

    pack = ACTIVE_PACK
    question = ss._state["question"] or pack.question
    return {
        "pack_id": pack.pack_id,
        "label": pack.label,
        "synthetic": pack.synthetic,
        "question": question,
    }


def _claim_to_dict(store: SQLiteStore, c) -> dict:
    """薄委托:与导出/对账单测同吃核心包 project_claim(K4)。"""
    return project_claim(store, c)


def _ui_badge_rows() -> list[dict]:
    """当前会话的只读 UiBadge。不改主张 status。"""
    return project_ui_badges(
        ss._state.get("trajectory"),
        list(ss._state.get("claims") or []),
    )


def _audit_for_ui() -> dict:
    """审计投影。badges 与职人槽同一份只读列表。补丁四列只读,不改检索。"""
    from freshlatch.ui.app import _store

    audit = project_audit(ss._state.get("trajectory"))
    annotate_audit_patch_visibility(audit, _store())
    audit["badges"] = _ui_badge_rows()
    return audit


def _claims_for_ui(store: SQLiteStore) -> list[dict]:
    """主张投影加只读 badge。"""
    rows = [_claim_to_dict(store, claim) for claim in ss._state["claims"]]
    by_id = {item["claim_id"]: item["badge"] for item in _ui_badge_rows()}
    for row in rows:
        row["badge"] = by_id.get(row["claim_id"])
    return rows


def _one_claim_for_ui(store: SQLiteStore, claim: Claim) -> dict:
    row = _claim_to_dict(store, claim)
    by_id = {item["claim_id"]: item["badge"] for item in _ui_badge_rows()}
    row["badge"] = by_id.get(claim.claim_id)
    return row


def _render_craftsman_badges(rows: list[dict]) -> str:
    """职人视图服务端徽章槽。只渲染三值;null 不占位。"""
    parts: list[str] = []
    for row in rows:
        badge = row.get("badge")
        if badge not in _UI_BADGE_TOKENS:
            continue
        claim_id = html.escape(str(row.get("claim_id") or ""))
        parts.append(
            '<div class="claim ui-badge-card" data-claim-id="'
            + claim_id
            + '"><b>'
            + claim_id
            + '</b><span class="badge '
            + badge
            + '">'
            + badge
            + "</span></div>"
        )
    return "".join(parts)


def _source_label() -> str:
    """发前来源短标签(包 id + T1 入口;非编排角色名)。"""
    from freshlatch.ui.app import ACTIVE_PACK, _t1_session

    pack = ACTIVE_PACK
    bits = [pack.pack_id]
    if pack.label:
        bits.append(pack.label)
    t1 = _t1_session().snapshot()
    kind = t1.get("kind") or "none"
    if kind and kind != "none":
        bits.append(f"T1:{kind}")
    return " · ".join(bits)


def _current_t1_checksum_map(store: SQLiteStore | None = None) -> dict[str, str]:
    """当前库 T1 doc_id→checksum 映射。"""
    from freshlatch.ui.app import _store

    s = store if store is not None else _store()
    return {
        str(row["doc_id"]): str(row.get("checksum") or "")
        for row in list_t1_checksums(s)
    }


def _bind_run_checksums(store: SQLiteStore | None = None) -> None:
    """把当前 T1 checksum 钉到 active Run。"""
    ss._state["bound_t1_checksums"] = _current_t1_checksum_map(store)


def _run_checksum_fresh(store: SQLiteStore | None = None) -> bool:
    """Run 绑定 checksum 相对当前是否未漂。"""
    recorded = ss._state.get("bound_t1_checksums") or {}
    current = _current_t1_checksum_map(store)
    return checksums_fresh(recorded, current)


def _patch_run_id() -> str:
    """补丁草案隔离键:优先当前发前 Run,否则 session。"""
    return str(ss._state.get("active_run_id") or "session")


def _patch_drafts_payload() -> dict[str, dict]:
    """本 Run 暂存草案投影(claim_id → draft dict)。"""
    from freshlatch.ui.app import _PATCH_DRAFTS

    return {
        cid: d.to_dict()
        for cid, d in _PATCH_DRAFTS.list_for_run(_patch_run_id()).items()
    }


def _claim_ledger_for_ui(
    store: SQLiteStore, *, run_id: str | None = None
) -> dict:
    """主张台账只读投影 + scope_note。"""
    ledger = dict(get_claim_ledger(store, run_id=run_id))
    ledger["scope_note"] = _LEDGER_SCOPE_NOTE
    return ledger


def _detail_extras(store: SQLiteStore) -> dict:
    """复验单增量包。"""
    claims = list(ss._state["claims"])
    ledger = _claim_ledger_for_ui(store, run_id=None)
    return {
        "disposition": disposition_for_claims(claims),
        "run_status": derive_run_status(
            running=bool(ss._state["running"]), latch=ss._state.get("latch")),
        "active_run_id": ss._state.get("active_run_id"),
        "t1_checksums": list_t1_checksums(store),
        "gate_results": project_gate_results(claims),
        "archived_t1_ids": list_archived_t1_evidence_ids(store),
        "patch_drafts": _patch_drafts_payload(),
        "claim_ledger": ledger,
        "run_metrics": _run_metrics(store),
    }


def _write_run_snapshot() -> None:
    """判定面写进同库 pack sqlite JSON blob。"""
    from freshlatch.ui.app import _store

    save = getattr(_store(), "save_run_snapshot", None)
    if save is None:
        return
    claims = list(ss._state.get("claims") or [])
    blob = json.dumps({
        "version": RUN_SNAPSHOT_VERSION,
        "active_run_id": ss._state.get("active_run_id"),
        "question": ss._state.get("question") or "",
        "claims": [asdict(c) for c in claims],
        "latch": ss._state.get("latch") or dict(ss.EMPTY_LATCH),
        "trajectory": (
            str(ss._state["trajectory"]) if ss._state.get("trajectory") else None
        ),
        "retrieve_zero_hits": list(ss._state.get("retrieve_zero_hits") or []),
        "budget": dict(ss._state.get("budget") or ss.EMPTY_BUDGET),
        "bound_t1_checksums": dict(ss._state.get("bound_t1_checksums") or {}),
        "token_usage": ss._state.get("token_usage"),
        "disposition": disposition_for_claims(claims),
    }, ensure_ascii=False)
    save(blob)


def _read_run_snapshot() -> dict | None:
    from freshlatch.ui.app import _store

    load = getattr(_store(), "load_run_snapshot", None)
    if load is None:
        return None
    raw = load()
    if not raw:
        return None
    try:
        snap = json.loads(raw)
    except ValueError:
        return None
    if snap.get("version") != RUN_SNAPSHOT_VERSION:
        return None
    return snap
