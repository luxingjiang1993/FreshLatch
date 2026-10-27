"""复验异步任务路由(#757 UI-SPLIT-T3)。

`/api/reverify` · `/progress` · `/cancel` 及 `_run_reverify_task`。
契约:I-10 五态轮询、取消协作点;不改 PRODUCTION_RETRIEVAL_MODE。
"""

from __future__ import annotations

import logging
import threading

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from freshlatch.llm import describe_llm_transport_error
from freshlatch.runner import load_docket
from freshlatch.store.checksum import make_checksum_fn
from freshlatch.ui import session_state as ss

router = APIRouter(tags=["reverify"])
logger = logging.getLogger(__name__)


class ReverifyRequest(BaseModel):
    """I-02(#679):预检面板「先用 BM25(精度降级)」的知情确认。缺省不改变任何行为。"""

    accept_bm25_fallback: bool = False


def _app():
    from freshlatch.ui import app as appmod

    return appmod


def _run_reverify_task(run_id: str) -> None:
    """I-10(#696)后台主链:异步跑复验,五态收口经 ss._RUN_TASK 供轮询。

    取消语义(决议 #690):已完成主张判定保留(Runner 原地改写);取消整轮
    不进 latch;清 active_run(无半残 run);快照仍写,部分判定面落盘可恢复。
    协作点 = 主张边界,单主张内部不打断(MVP);取消若落在全部主张完成后,
    按完成收口(done),不丢人审入口。
    """
    appmod = _app()
    with ss._RUN_TASK_LOCK:
        task = ss._RUN_TASK
    if task is None or task["run_id"] != run_id:
        return
    accept_bm25 = task["accept_bm25"]

    def _progress(*, current: str | None = None, done: int | None = None) -> None:
        with ss._RUN_TASK_LOCK:
            t = ss._RUN_TASK
            if t is None or t["run_id"] != run_id:
                return
            if current is not None:
                t["current_claim_id"] = current
            if done is not None:
                t["done"] = done
                t["current_claim_id"] = None

    def _should_cancel() -> bool:
        with ss._RUN_TASK_LOCK:
            t = ss._RUN_TASK
        return bool(t is not None and t["run_id"] == run_id
                    and t["cancel_event"].is_set())

    def _set_status(status: str) -> None:
        with ss._RUN_TASK_LOCK:
            t = ss._RUN_TASK
            if t is not None and t["run_id"] == run_id:
                t["status"] = status

    try:
        # Runner 经 app 取名,单测 monkeypatch(appmod.Runner) 才能拦住真主链
        runner = appmod.Runner(appmod._store(),
                               checksum_fn=make_checksum_fn(appmod.CORPUS))
        if accept_bm25:
            # I-02(#679):预检知情降级——本跑整臂 bm25_fallback(轨迹字段),
            # 不改 PRODUCTION_RETRIEVAL_MODE,也不写 set_retrieval_switch 运维开关。
            runner.ctx.bm25_fallback_accepted = True
        ss._state["run_ctx"] = runner.ctx
        ss._state["budget"] = appmod._budget_from_ctx(runner.ctx)
        result = runner.run(list(ss._state["claims"]),
                            progress=_progress, should_cancel=_should_cancel)
        ss._state["trajectory"] = result.trajectory_path
        ss._state["budget"] = appmod._budget_from_ctx(runner.ctx)
        token_bucket = getattr(getattr(runner, "llm", None), "token_usage", None)
        if token_bucket is not None:
            ss._state["token_usage"] = token_bucket.to_dict()
        ss._state["retrieve_zero_hits"] = list(result.retrieve_zero_hits)
        with ss._RUN_TASK_LOCK:
            t = ss._RUN_TASK
            cancelled = bool(t is not None and t["run_id"] == run_id
                             and t["cancel_event"].is_set())
            done = t["done"] if (t is not None and t["run_id"] == run_id) else 0
        if cancelled and done < len(ss._state["claims"]):
            ss._state["latch"] = dict(ss.EMPTY_LATCH)
            ss._state["active_run_id"] = None
            ss._state["token_usage"] = None
            ss._prepublish.active_run_id = None
            appmod._write_run_snapshot()
            _set_status("cancelled")
        else:
            rnd = appmod._latch().enter_round(ss._state["claims"])
            ss._state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
            run_row = appmod._sync_prepublish(new_run=False)
            appmod._write_run_snapshot()
            store = appmod._store()
            extras = appmod._detail_extras(store)
            with ss._RUN_TASK_LOCK:
                t = ss._RUN_TASK
                if t is not None and t["run_id"] == run_id:
                    t["result"] = {
                        "claims": appmod._claims_for_ui(store),
                        "trajectory": str(result.trajectory_path),
                        "audit": appmod._audit_for_ui(),
                        "retrieval_used": result.retrieval_used,
                        "steps_by_claim": result.steps_by_claim,
                        "decoding": result.decoding.__dict__,
                        "latch": ss._state["latch"],
                        "retrieve_zero_hits": list(ss._state["retrieve_zero_hits"]),
                        "budget": dict(ss._state["budget"]),
                        "run": run_row,
                        **extras,
                    }
                    t["status"] = "done"
    except Exception as exc:  # noqa: BLE001 —— 跨线程边界,映射成中文可操作负载
        mapped = describe_llm_transport_error(exc)
        if mapped is None:
            logger.exception(
                "复验主链未捕获异常 claim_count=%s", len(ss._state["claims"])
            )
            mapped = {
                "error_code": "REVERIFY_INTERNAL",
                "error": ("复验执行失败(内部错误已记入服务端日志,界面不回显堆栈)。"
                          "怎么办:稍后重试;若反复出现,请记录时间与操作步骤后反馈。"),
            }
        with ss._RUN_TASK_LOCK:
            t = ss._RUN_TASK
            if t is not None and t["run_id"] == run_id:
                t["error"] = mapped
                t["status"] = "failed"
    finally:
        ss._state["running"] = False
        ss._state["run_ctx"] = None


@router.post("/api/reverify")
def api_reverify(req: ReverifyRequest | None = None) -> JSONResponse:
    """复验动作(由一键样例进入):异步任务化(I-10/#696),校验后立刻返回 run_id。"""
    appmod = _app()
    if ss._state["running"]:
        return JSONResponse({"error": "已有复验在进行中"}, status_code=409)
    if not appmod._t1_session().state.ready:
        return JSONResponse(
            {"error": "未选定合法 T1 来源,不得假装已有最新事实(请先完成 T1 来源三卡)"},
            status_code=400,
        )
    if not ss._state["claims"]:
        docket = load_docket(appmod.DEMO_DOCKET)
        ss._state["claims"] = docket.claims
        ss._state["question"] = docket.question
    ss._state["running"] = True
    ss._state["token_usage"] = None
    try:
        appmod._sync_prepublish(new_run=True)
    except Exception:
        ss._state["running"] = False
        raise
    run_id = ss._state["active_run_id"]
    ss._new_run_task(run_id, total=len(ss._state["claims"]),
                     accept_bm25=bool(req is not None and req.accept_bm25_fallback))
    try:
        threading.Thread(target=_run_reverify_task, args=(run_id,),
                         daemon=True).start()
    except Exception:
        ss._state["running"] = False
        ss._reset_run_task()
        raise
    return JSONResponse({"run_id": run_id, "status": "running"})


@router.get("/api/reverify/progress")
def api_reverify_progress(run_id: str = Query(...)) -> JSONResponse:
    """I-10(#696)轮询面:status ∈ {running, cancelling, cancelled, done, failed}。"""
    with ss._RUN_TASK_LOCK:
        task = ss._RUN_TASK
        if task is None or task["run_id"] != run_id:
            return JSONResponse({"error": f"未找到复验任务 {run_id}"},
                                status_code=404)
        body: dict = {"run_id": task["run_id"], "status": task["status"],
                      "done": task["done"], "total": task["total"],
                      "current_claim_id": task["current_claim_id"]}
        if task["status"] == "done" and task["result"]:
            body.update(task["result"])
        elif task["status"] == "failed" and task["error"]:
            body.update(task["error"])
    return JSONResponse(body)


@router.post("/api/reverify/cancel")
def api_reverify_cancel() -> JSONResponse:
    """I-10(#696)整轮取消:置 cancelling + cancel_event;协作点 = 主张边界。"""
    with ss._RUN_TASK_LOCK:
        task = ss._RUN_TASK
        if task is None or task["status"] in ("done", "failed", "cancelled"):
            return JSONResponse({"error": "当前没有可取消的复验"}, status_code=409)
        task["cancel_event"].set()
        task["status"] = "cancelling"
        run_id = task["run_id"]
    return JSONResponse({"run_id": run_id, "status": "cancelling"})
