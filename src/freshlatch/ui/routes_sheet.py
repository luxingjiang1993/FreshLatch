"""复验单 Sheet / boot / 原文 / 页面入口(#758 UI-SPLIT-T4)。

claims · ledger · memo · boot · session reset · source · index HTML。
审计面 HTML 渲染助手同迁,供 index 注入。
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response

from freshlatch.claim_ledger import export_claim_ledger_md
from freshlatch.claim_span import split_sentences
from freshlatch.gates.basis_rot import rot_claims
from freshlatch.prepublish import disposition_for_claims
from freshlatch.publish_hook import HOOK_CHECKSUM_DRIFT
from freshlatch.sheet import (
    PATCH_VISIBILITY_FIELDS,
    export_client_memo_gated,
    project_claim,
    render_failure_buckets_html,
)
from freshlatch.store.checksum import make_checksum_fn
from freshlatch.store.ingest import parse_document
from freshlatch.ui import session_state as ss

router = APIRouter(tags=["sheet"])

_UI_STATIC = Path(__file__).resolve().parent / "static"
HTML_PAGE = (_UI_STATIC / "reverify.html").read_text(encoding="utf-8")
PREPUBLISH_HTML = (_UI_STATIC / "prepublish.html").read_text(encoding="utf-8")


def _app():
    from freshlatch.ui import app as appmod

    return appmod


def _format_audit_score(value: float) -> str:
    """有限数字的短写法。不补小数位,避免把空臂写成 0。"""
    return format(value, ".12g")


def _patch_visibility_html(hit: dict) -> str:
    """命中行上的 as_of / patch_id / valid_from / valid_to。空值写「无」。"""
    esc = html.escape
    parts: list[str] = []
    for key in PATCH_VISIBILITY_FIELDS:
        raw = hit.get(key)
        shown = raw.strip() if isinstance(raw, str) and raw.strip() else ""
        label = esc(shown) if shown else "无"
        css = "hit-" + key.replace("_", "-")
        parts.append(
            f'<span class="{css}" data-{css}="{esc(shown, quote=True)}">'
            f"{esc(key)} {label}</span>"
        )
    return " · ".join(parts)


def _span_link(item: dict, role: str) -> str:
    """句锚链接。可见文本含 evidence id 与句 id。"""
    esc = html.escape
    css = "span-support" if role == "support" else "span-oppose"
    evidence_id = str(item.get("evidence_id") or "")
    sentence_id = str(item.get("sentence_id") or "")
    anchor = str(item.get("anchor") or f"{evidence_id}#{sentence_id}")
    text = str(item.get("text") or "")
    return (
        f'<a class="{css}" data-role="{role}" '
        f'data-evidence-id="{esc(evidence_id, quote=True)}" '
        f'data-sentence-id="{esc(sentence_id, quote=True)}" '
        f'href="#{esc(anchor, quote=True)}" '
        f'onclick="openClaimSpan(this);return false;">'
        f"{esc(anchor)}</a> {esc(text)}"
    )


def _render_claim_spans(spans: list) -> str:
    """主张句分列支撑与反对。无支撑时不画 span-support。"""
    esc = html.escape
    if not spans:
        return '<div id="audit-claim-spans"><b>主张句</b> · 无</div>'
    items: list[str] = []
    for row in spans:
        claim_id = esc(str(row.get("claim_id") or ""), quote=True)
        claim_text = esc(str(row.get("claim_text") or ""))
        flag = "true" if row.get("unsupported") else "false"
        support = row.get("support") or []
        oppose = row.get("oppose") or []
        if support:
            support_html = " ".join(_span_link(item, "support") for item in support)
        else:
            support_html = "无"
        if oppose:
            oppose_html = " ".join(_span_link(item, "oppose") for item in oppose)
        else:
            oppose_html = "无"
        items.append(
            f'<li class="claim-span-card" data-claim-id="{claim_id}" '
            f'data-unsupported="{flag}">'
            f'<div class="claim-span-text">{claim_text}</div>'
            f'<div class="claim-span-support"><b>支撑句</b> · {support_html}</div>'
            f'<div class="claim-span-oppose"><b>反对句</b> · {oppose_html}</div>'
            "</li>"
        )
    return (
        '<div id="audit-claim-spans"><b>主张句</b><ul>'
        + "".join(items)
        + "</ul></div>"
    )


def _render_audit_body(audit: dict) -> str:
    """审计面 HTML。缺查询、缺分、缺依据、缺 reason、缺主张句都写「无」。"""
    from freshlatch.store.pipeline import HIT_SCORE_FIELDS

    esc = html.escape
    path = audit.get("path")
    parsed = bool(audit.get("parsed"))
    if not path and not parsed:
        return "尚无本轮轨迹。完成复验后此处显示查询、命中、判定依据与未知原因。"

    queries = audit.get("query") or []
    if queries:
        query_html = "；".join(esc(str(item)) for item in queries)
    else:
        query_html = "无"

    hits = audit.get("hits") or []
    if not hits:
        hits_html = "无"
    else:
        items: list[str] = []
        for hit in hits:
            evidence_id = esc(str(hit.get("evidence_id") or ""))
            scores = hit.get("scores")
            if not isinstance(scores, dict):
                score_html = "分 无"
            else:
                parts: list[str] = []
                any_number = False
                for arm in HIT_SCORE_FIELDS:
                    value = scores.get(arm)
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        parts.append(f"{arm} 无")
                        continue
                    any_number = True
                    parts.append(f"{arm} {_format_audit_score(float(value))}")
                score_html = " · ".join(parts) if any_number else "分 无"
            items.append(
                f"<li><code>{evidence_id}</code> · {_patch_visibility_html(hit)}"
                f" · {score_html}</li>"
            )
        hits_html = "<ul>" + "".join(items) + "</ul>"

    attribution = audit.get("attribution_ids") or []
    if attribution:
        attribution_html = " ".join(f"<code>{esc(str(item))}</code>" for item in attribution)
    else:
        attribution_html = "无"

    reason = audit.get("unknown_reason")
    if isinstance(reason, str) and reason:
        reason_html = f"<code>{esc(reason)}</code>"
    else:
        reason_html = "无"

    path_html = ""
    if path:
        path_html = f'<div id="audit-path">轨迹路径 · <code>{esc(str(path))}</code></div>'
    return (
        path_html
        + f'<div id="audit-query"><b>查询</b> · {query_html}</div>'
        + f'<div id="audit-hits"><b>命中</b> · {hits_html}</div>'
        + f'<div id="audit-attribution"><b>判定依据</b> · {attribution_html}</div>'
        + f'<div id="audit-unknown"><b>未知原因</b> · {reason_html}</div>'
        + render_failure_buckets_html(audit.get("failure_buckets"))
        + _render_claim_spans(audit.get("claim_spans") or [])
    )


@router.get("/api/claims")
def api_claims() -> dict:
    """拉复验单:对可见 fresh∧basis 主张跑与复验入口同一腐烂路径并真写库(ADR-0025)。"""
    appmod = _app()
    store = appmod._store()
    rot_claims(store, list(ss._state["claims"]), make_checksum_fn(appmod.CORPUS))
    extras = appmod._detail_extras(store)
    return {
        "question": ss._state["question"],
        "claims": appmod._claims_for_ui(store),
        "trajectory": str(ss._state["trajectory"]) if ss._state["trajectory"] else None,
        "audit": appmod._audit_for_ui(),
        "running": ss._state["running"],
        "latch": ss._state["latch"],
        "retrieve_zero_hits": list(ss._state.get("retrieve_zero_hits") or []),
        "budget": appmod._current_budget(),
        "pack": appmod._pack_payload(),
        **extras,
    }


@router.get("/api/claim-ledger")
def api_claim_ledger(run_id: str | None = Query(default=None)) -> dict:
    """#228 主张台账只读投影 API:discard ∪ renew;renew∉作废名单。"""
    appmod = _app()
    return appmod._claim_ledger_for_ui(appmod._store(), run_id=run_id or None)


@router.get("/api/claim-ledger/export.md")
def api_claim_ledger_export(run_id: str | None = Query(default=None)) -> Response:
    """#228 主张台账 Markdown 导出(只读;零新写表)。"""
    md = export_claim_ledger_md(_app()._store(), run_id=run_id or None)
    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="claim-ledger.md"'},
    )


@router.post("/api/client-memo/export")
def api_client_memo_export(
    ack_needs_patch: bool = Query(default=False),
) -> Response:
    """#229 导出客户备忘:与 CLI 共用 export_client_memo_gated。"""
    from freshlatch.ui.routes_publish import hook_error_body

    appmod = _app()
    store = appmod._store()
    if not ss._state.get("active_run_id"):
        appmod._sync_prepublish(new_run=True)
    else:
        appmod._sync_prepublish(new_run=False)

    claims = list(ss._state["claims"])
    projections = [project_claim(store, c) for c in claims]
    disposition = disposition_for_claims(claims)
    hook, md = export_client_memo_gated(
        run_id=ss._state.get("active_run_id"),
        disposition=disposition,
        projections=projections,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ack_needs_patch=bool(ack_needs_patch),
        checksum_fresh=appmod._run_checksum_fresh(store),
        question=str(ss._state.get("question") or ""),
        synthetic=bool(getattr(appmod.ACTIVE_PACK, "synthetic", False)),
        out_path=None,
    )
    if not hook.allow:
        status = 403
        if hook.code == HOOK_CHECKSUM_DRIFT:
            status = 409
        body = hook.to_dict()
        body.update(hook_error_body(hook.code, hook.message))
        return JSONResponse(body, status_code=status)

    assert md is not None
    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="client-memo.md"',
            "X-FreshLatch-Hook-Code": hook.code,
            "X-FreshLatch-Needs-Patch-Banner": (
                "1" if hook.requires_needs_patch_banner else "0"
            ),
        },
    )


@router.get("/api/boot")
def api_boot() -> dict:
    """页面加载/刷新:幂等读取当前会话。不调用 import,不洗勿发与待拍板。"""
    appmod = _app()
    if (not ss._state.get("running") and not ss._state.get("claims")
            and not ss._state.get("active_run_id")):
        snap = appmod._read_run_snapshot()
        if snap and (snap.get("claims") or snap.get("active_run_id")):
            appmod._restore_run_snapshot(snap)
    return api_claims()


@router.post("/api/session/reset")
def api_session_reset() -> JSONResponse:
    """高级「重置」:显式清空当前复验单。不调用 HumanLatch,不改闸。"""
    appmod = _app()
    if ss._state.get("running"):
        return JSONResponse({"error": "复验进行中,不能重置"}, status_code=409)
    appmod._clear_live_sheet()
    clear = getattr(appmod._store(), "clear_run_snapshot", None)
    if clear is not None:
        clear()
    return JSONResponse({
        "reset": True,
        "latch": dict(ss.EMPTY_LATCH),
        "ledger_note": appmod._RESET_LEDGER_NOTE,
    })


@router.get("/api/source/{doc_id}")
def api_source(doc_id: str, as_of: str = Query("T1", pattern="^(T0|T1)$")) -> dict:
    """点回原文:返回条款级锚点段落,前端定位 + 高亮。"""
    appmod = _app()
    path = appmod.CORPUS / as_of.lower() / f"{doc_id}.md"
    if not path.exists():
        return JSONResponse({"error": f"未找到 {doc_id} 的 {as_of} 快照"}, status_code=404)
    doc, chunks = parse_document(path)
    return {
        "doc_id": doc_id,
        "as_of": as_of,
        "title": doc.title,
        "source_type": doc.source_type,
        "sections": [
            {
                "anchor": c.clause_id,
                "text": c.text,
                "sentences": [
                    {"sentence_id": f"s{index}", "text": sentence}
                    for index, sentence in enumerate(split_sentences(c.text))
                ],
            }
            for c in chunks
        ],
    }


@router.get("/", response_class=HTMLResponse)
def index(view: str = Query(default="")) -> str:
    appmod = _app()
    mode = view if view in ("audit", "interview") else appmod.VIEW_MODE_DEFAULT
    page = HTML_PAGE.replace(appmod._VIEW_MODE_TOKEN, mode)
    page = page.replace(
        '<html lang="zh" data-view="craftsman">',
        f'<html lang="zh" data-view="{mode}">',
        1,
    )
    page = page.replace('id="view-craftsman" class="on"', 'id="view-craftsman"')
    if mode == "audit":
        page = page.replace('id="view-audit"', 'id="view-audit" class="on"', 1)
        page = page.replace('id="audit-panel"', 'id="audit-panel" class="visible"', 1)
    elif mode == "interview":
        page = page.replace('id="view-interview"', 'id="view-interview" class="on"', 1)
    else:
        page = page.replace('id="view-craftsman"', 'id="view-craftsman" class="on"', 1)
    if mode != "audit":
        page = page.replace(appmod.SYN_BADGE_FULL_TEXT, appmod.SYN_BADGE_SHORT_TEXT, 1)
    audit = appmod._audit_for_ui()
    badge_html = (
        appmod._render_craftsman_badges(audit["badges"]) if mode == "craftsman" else ""
    )
    page = page.replace(appmod._CRAFTSMAN_BADGES_TOKEN, badge_html)
    return page.replace(appmod._AUDIT_BODY_TOKEN, _render_audit_body(audit))


@router.get("/prepublish", response_class=HTMLResponse)
def prepublish_index() -> str:
    """发前列表页(#173):mission_control 列表壳改编,业务字段换 Run/disposition。"""
    return PREPUBLISH_HTML
