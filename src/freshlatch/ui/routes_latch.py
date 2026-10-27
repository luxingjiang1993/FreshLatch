"""HumanLatch UI 薄壳路由(#757 UI-SPLIT-T3)。

`/api/latch/decide|rerun|status|reopen`。写路径仍唯一经 gates/human_latch;
本模块只搬调用点,不引入核心包 Web 依赖。
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from freshlatch.latch import HumanLatchError
from freshlatch.patch_events import record_human_review_events
from freshlatch.prepublish import disposition_for_claims, list_t1_checksums
from freshlatch.ui import session_state as ss

router = APIRouter(tags=["latch"])


class DecideRequest(BaseModel):
    thread_id: str
    decisions: list[dict] = []


class RerunRequest(BaseModel):
    claim_id: str


def _app():
    from freshlatch.ui import app as appmod

    return appmod


@router.post("/api/latch/decide")
def api_latch_decide(req: DecideRequest) -> JSONResponse:
    """人审批量提交(同步 def):Command(resume=整个决定列表)恢复 interrupt,execute 落档。"""
    appmod = _app()
    if ss._state["latch"].get("thread_id") != req.thread_id:
        return JSONResponse({"error": "该轮人审不存在或已提交(刷新复验单查看最新状态)"}, status_code=409)
    before_disp = disposition_for_claims(list(ss._state["claims"]))
    store = appmod._store()
    t1_ids = [
        f"{row['doc_id']}#{row.get('checksum') or ''}@T1"
        for row in list_t1_checksums(store)
        if row.get("doc_id")
    ]
    try:
        latch = appmod._latch()
        results = latch.decide(req.thread_id, req.decisions, claims=list(ss._state["claims"]))
        latch.prune_rounds()
    except HumanLatchError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    patch_rows = record_human_review_events(
        results,
        before_disp=before_disp,
        t1_ids=t1_ids,
        arm="C",
        actor="human",
        events_dir=appmod._PATCH_EVENTS_DIR,
    )
    ss._state["latch"] = dict(ss.EMPTY_LATCH)
    run_row = appmod._sync_prepublish(new_run=False)
    appmod._write_run_snapshot()
    extras = appmod._detail_extras(store)
    return JSONResponse({
        "results": results,
        "claims": appmod._claims_for_ui(store),
        "latch": ss._state["latch"],
        "run": run_row,
        "patch_events_written": len(patch_rows),
        **extras,
    })


@router.post("/api/latch/rerun")
def api_latch_rerun(req: RerunRequest) -> JSONResponse:
    """人点「重跑作废主张」(同步 def,不自动):新 thread 单主张迷你复验,结果挂时间线。"""
    appmod = _app()
    claim = next((c for c in ss._state["claims"] if c.claim_id == req.claim_id), None)
    if claim is None:
        return JSONResponse({"error": f"未找到主张 {req.claim_id}"}, status_code=404)
    try:
        entry = appmod._latch().rerun(claim)
    except HumanLatchError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    appmod._write_run_snapshot()
    return JSONResponse({"entry": entry, "claim": appmod._one_claim_for_ui(appmod._store(), claim)})


@router.get("/api/latch/status")
def api_latch_status() -> dict:
    """人审轮状态;进程重启后可用 thread_id 从 checkpoint 恢复待审清单(#11 §5.10)。"""
    return {"latch": ss._state["latch"]}


@router.get("/api/latch/reopen")
def api_latch_reopen(claim_id: str = Query(...)) -> dict:
    """再打开 disputed 结论与审计轨迹。只读,不写冻结 gold / floors。"""
    return _app()._latch().reopen_disputed(claim_id)
