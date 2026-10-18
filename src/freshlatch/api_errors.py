"""API 错误统一契约(决议 #705 I-12 / #711)。

错误体统一形状:`ok=False` + `error_code`(STABLE_SNAKE) + `message`(中文)
+ `hint`(怎么办);可选 `fields`。英文 detail 只进日志,不进响应体。
`code` 为旧键兼容别名,与 `error_code` 同值,不另造近义词。

HTTP 状态码语义不变:本模块只统一错误载荷形状,不改放行规则。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# 横切错误码(STABLE_SNAKE;稳定,禁随文案漂移)
REQUEST_VALIDATION_FAILED = "REQUEST_VALIDATION_FAILED"
INTERNAL_ERROR = "INTERNAL_ERROR"

# 统一错误负载
ERROR_HINT_VALIDATION = "请检查请求体 JSON 格式与字段类型"
ERROR_HINT_INTERNAL = "请稍后重试;持续出现请联系运维"
ERROR_MESSAGE_VALIDATION = "请求参数校验失败"
ERROR_MESSAGE_INTERNAL = "服务内部错误"


def error_body(
    error_code: str,
    message: str,
    hint: str,
    *,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构造统一错误体。`code` 为旧键兼容别名,与 `error_code` 同值。"""
    body: dict[str, Any] = {
        "ok": False,
        "error_code": error_code,
        "message": message,
        "hint": hint,
        "code": error_code,
    }
    if fields:
        body["fields"] = fields
    return body


def install_error_handlers(app: FastAPI, *, log_prefix: str) -> None:
    """装配统一 422/500 handler(决议 #705 I-12),供 Serving 与 UI 两 app 复用。

    替换 FastAPI 默认英文 422(含请求体 JSON 解析失败);5xx 安全中文 +
    稳定 code,无堆栈,细节只进日志。HTTP 状态码语义不变。
    """

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        request: Request, exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            "%s 422 on %s %s: %s", log_prefix, request.method, request.url.path, exc,
        )
        return JSONResponse(
            error_body(
                REQUEST_VALIDATION_FAILED,
                ERROR_MESSAGE_VALIDATION,
                ERROR_HINT_VALIDATION,
            ),
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def _internal_error_handler(
        request: Request, exc: Exception,
    ) -> JSONResponse:
        logger.exception("%s 500 on %s %s", log_prefix, request.method, request.url.path)
        return JSONResponse(
            error_body(INTERNAL_ERROR, ERROR_MESSAGE_INTERNAL, ERROR_HINT_INTERNAL),
            status_code=500,
        )
