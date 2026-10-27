"""发前列表与 publish-hook 入站探闸(#758 UI-SPLIT-T4)。

`/api/prepublish/runs*` · `/api/publish-hook/check`。
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from freshlatch.api_errors import error_body
from freshlatch.publish_hook import (
    HOOK_CHECKSUM_DRIFT,
    HOOK_DO_NOT_PUBLISH,
    HOOK_MISSING_RUN_ID,
    HOOK_NEEDS_PATCH_NO_ACK,
    HOOK_TOKEN_ENV,
    HOOK_TOKEN_HEADER,
    HOOK_UNAUTHORIZED,
    HOOK_UNBOUND_RUN,
    deny_http_status,
)
from freshlatch.ui import session_state as ss

router = APIRouter(tags=["publish"])


class PublishHookCheckRequest(BaseModel):
    """入站 publish-hook check 请求体(#230):必填 run_id;可选 ack_needs_patch。"""

    run_id: str | None = None
    ack_needs_patch: bool = False


# 决议 #705 I-12:deny 载荷带「怎么办」hint(职人向中文);码不变、状态码语义不变
HOOK_HINTS: dict[str, str] = {
    HOOK_MISSING_RUN_ID: "请在请求体里带上本次发前 Run 的 run_id 后重试",
    HOOK_UNBOUND_RUN: "请确认 run_id 对应一次已生成的发前 Run;无包结论时需先在复验单收口再导出",
    HOOK_DO_NOT_PUBLISH: "请先在复验单完成人审收口(作废/续命/改账),使包结论变为可发后再导出",
    HOOK_CHECKSUM_DRIFT: "T1 语料或 Run 状态已变化:请重跑一轮复验后再导出",
    HOOK_NEEDS_PATCH_NO_ACK: "如接受「需补丁」页眉约束,请带 ack_needs_patch=true 重试",
    HOOK_UNAUTHORIZED: f"请携带正确的 {HOOK_TOKEN_HEADER} 头(对应 {HOOK_TOKEN_ENV} 配置)",
}


def hook_error_body(result_code: str, message: str) -> dict:
    """publish-hook deny 的统一错误载荷(决议 #705 I-12)。"""
    return error_body(
        result_code,
        message,
        HOOK_HINTS.get(result_code, "请按提示修正后重试;仍失败请联系运维"),
    )


def _hook_token_denied(request: Request) -> JSONResponse | None:
    """可选共享密钥头:仅当环境变量已配置时强制校验;缺失配置则本机冒烟可测。"""
    expected = (os.environ.get(HOOK_TOKEN_ENV) or "").strip()
    if not expected:
        return None
    provided = (request.headers.get(HOOK_TOKEN_HEADER) or "").strip()
    if provided == expected:
        return None
    body = hook_error_body(HOOK_UNAUTHORIZED, "入站 check 共享密钥头校验失败")
    body.update({
        "allow": False,
        "disposition": None,
        "requires_needs_patch_banner": False,
    })
    return JSONResponse(body, status_code=403)


def _app():
    from freshlatch.ui import app as appmod

    return appmod


@router.get("/api/prepublish/runs")
def api_prepublish_runs() -> dict:
    """发前列表:标题/来源、disposition、更新时间、Run 状态(#173)。"""
    appmod = _app()
    if ss._state.get("claims") or ss._state.get("trajectory") or ss._state.get("active_run_id"):
        appmod._sync_prepublish(new_run=False)
    return {
        "runs": ss._prepublish.list_runs(),
        "active_run_id": ss._state.get("active_run_id"),
    }


@router.get("/api/prepublish/runs/{run_id}")
def api_prepublish_run(run_id: str) -> JSONResponse:
    """发前 Run 摘要;详情 UI 仍走既有复验单(增量包结论条)。"""
    row = ss._prepublish.get(run_id)
    if row is None:
        return JSONResponse({"error": f"未找到 Run {run_id}"}, status_code=404)
    return JSONResponse({"run": row.to_dict(), "detail_path": "/"})


@router.post("/api/publish-hook/check")
def api_publish_hook_check(
    req: PublishHookCheckRequest, request: Request,
) -> JSONResponse:
    """入站 publish-hook check(#230):与 Memo 同闸;deny → 403/409;非插件平台。"""
    appmod = _app()
    # 经 app 取名,单测 monkeypatch(appmod._hook_token_denied / evaluate_publish_hook)
    denied = appmod._hook_token_denied(request)
    if denied is not None:
        return denied

    rid = req.run_id
    disposition = None
    if rid is not None and str(rid).strip():
        row = ss._prepublish.get(str(rid).strip())
        if row is not None:
            disposition = row.disposition

    result = appmod.evaluate_publish_hook(
        run_id=rid,
        disposition=disposition,
        ack_needs_patch=bool(req.ack_needs_patch),
        checksum_fresh=True,
    )
    body = result.to_dict()
    if result.allow:
        return JSONResponse(body, status_code=200)
    body.update(hook_error_body(result.code, result.message))
    return JSONResponse(body, status_code=deny_http_status(result.code))
