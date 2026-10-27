"""Evidence-bound 补丁路由(#758 UI-SPLIT-T4)。

`/api/patch/propose|confirm|discard-draft`。硬闸仍在 evidence_bound;本模块只搬薄壳。
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from freshlatch.evidence_bound import (
    confirm_patch,
    discard_patch_draft,
    propose_patch,
    single_claim_reverify,
)
from freshlatch.models import Claim
from freshlatch.prepublish import list_archived_t1_evidence_ids
from freshlatch.store.checksum import make_checksum_fn
from freshlatch.ui import session_state as ss

router = APIRouter(tags=["patch"])


class ProposePatchRequest(BaseModel):
    """#200 改稿暂存:after_text + 可选 t1 草案;不改正文、不写正式账本。"""

    claim_id: str
    after_text: str
    t1_ids: list[str] = []


class ConfirmPatchRequest(BaseModel):
    """#200 确认改稿:资格闸+T1硬闸→覆盖正文→T臂账本;职人用语「确认」。"""

    claim_id: str
    after_text: str | None = None
    t1_ids: list[str] | None = None
    minutes: float = 0.0
    patch_span: str | None = None


class DiscardPatchDraftRequest(BaseModel):
    """#200 丢弃未确认草案。"""

    claim_id: str


def _app():
    from freshlatch.ui import app as appmod

    return appmod


def _confirm_patch_reverify(claim: Claim) -> tuple[str, str]:
    """产品路径单条再验(#199);测试可 monkeypatch appmod._confirm_patch_reverify。"""
    appmod = _app()
    return single_claim_reverify(
        claim,
        store=appmod._store(),
        checksum_fn=make_checksum_fn(appmod.CORPUS),
    )


@router.post("/api/patch/propose")
def api_patch_propose(req: ProposePatchRequest) -> JSONResponse:
    """提案暂存(ADR-0029 / #200):走 propose_patch;零改正文、零写正式账本。"""
    appmod = _app()
    result = propose_patch(
        claim_id=req.claim_id,
        after_text=req.after_text,
        t1_ids=req.t1_ids,
        claims=list(ss._state["claims"]),
        drafts=appmod._PATCH_DRAFTS,
        run_id=appmod._patch_run_id(),
    )
    if not result.ok:
        return JSONResponse(result.to_dict(), status_code=400)
    store = appmod._store()
    extras = appmod._detail_extras(store)
    return JSONResponse({
        **result.to_dict(),
        "claims": appmod._claims_for_ui(store),
        **extras,
    })


@router.post("/api/patch/confirm")
def api_patch_confirm(req: ConfirmPatchRequest) -> JSONResponse:
    """确认改稿(#200):confirm_patch 硬闸;产品路径恒 arm=T;发前无 C|T 开关。"""
    appmod = _app()
    store = appmod._store()
    archived = list_archived_t1_evidence_ids(store)
    # 经 app 取名,单测 monkeypatch(appmod._confirm_patch_reverify) 才能拦住 LLM
    result = confirm_patch(
        claim_id=req.claim_id,
        claims={c.claim_id: c for c in ss._state["claims"]},
        claim_list=ss._state["claims"],
        archived_t1_ids=archived,
        minutes=req.minutes,
        after_text=req.after_text,
        t1_ids=req.t1_ids,
        patch_span=req.patch_span,
        drafts=appmod._PATCH_DRAFTS,
        run_id=appmod._patch_run_id(),
        events_dir=appmod._PATCH_EVENTS_DIR,
        actor="human",
        reverify_fn=appmod._confirm_patch_reverify,
    )
    if not result.ok:
        return JSONResponse(result.to_dict(), status_code=400)
    run_row = appmod._sync_prepublish(new_run=False)
    appmod._write_run_snapshot()
    extras = appmod._detail_extras(store)
    return JSONResponse({
        **result.to_dict(),
        "claims": appmod._claims_for_ui(store),
        "run": run_row,
        **extras,
    })


@router.post("/api/patch/discard-draft")
def api_patch_discard_draft(req: DiscardPatchDraftRequest) -> JSONResponse:
    """丢弃未确认改稿草案(#200);不影响主张正文与正式账本。"""
    appmod = _app()
    discarded = discard_patch_draft(
        claim_id=req.claim_id,
        drafts=appmod._PATCH_DRAFTS,
        run_id=appmod._patch_run_id(),
    )
    store = appmod._store()
    extras = appmod._detail_extras(store)
    return JSONResponse({
        "ok": True,
        "claim_id": req.claim_id,
        "discarded": discarded,
        "claims": appmod._claims_for_ui(store),
        **extras,
    })
