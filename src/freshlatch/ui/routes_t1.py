"""T1 来源 / 主张导入 / 检索预检路由(#756 UI-SPLIT-T2)。

路径字符串与契约零变更;可变容器真相源仍为 session_state。
助手(_t1_session / _store / conflict 等)经 app 延迟取,兼容单测 monkeypatch。
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from freshlatch.claim_import import ClaimImportError, parse_claim_import_draft
from freshlatch.runner import load_docket
from freshlatch.ui import session_state as ss

router = APIRouter(tags=["t1-source"])


class PasteDraftRequest(BaseModel):
    text: str


class ThinUrlRequest(BaseModel):
    """薄 URL 入库请求:单条白名单 URL(ADR-0027 / #171)。"""

    url: str


class DraftImportRequest(BaseModel):
    text: str
    question: str | None = None


def _app():
    """延迟取 app 模块,避免与 include_router 循环导入,并吃 monkeypatch。"""
    from freshlatch.ui import app as appmod

    return appmod


@router.post("/api/import")
def api_import():
    """JSON docket 高级入口(Workflow):只读 statement 与 t0_evidence_ids,不做新调查。

    #678(I-01):非空 active_run 时硬 409 + 高级重置指引——breaking vs #669 的
    200+preserved;确认重置后才可导入。成功导入后写 run snapshot(判定面与磁盘一致)。
    """
    appmod = _app()
    conflict = appmod._active_run_conflict()
    if conflict is not None:
        return conflict
    docket = load_docket(appmod.DEMO_DOCKET)
    ss._state["claims"] = docket.claims
    ss._state["question"] = docket.question  # 单一真相:当前课题包 docket
    ss._state["latch"] = dict(ss.EMPTY_LATCH)
    ss._state["trajectory"] = None
    ss._state["active_run_id"] = None
    row = appmod._sync_prepublish(new_run=True)
    appmod._write_run_snapshot()
    return {"imported": len(docket.claims), "run": row}


@router.get("/api/t1-source")
def api_t1_source() -> dict:
    """T1 来源三卡状态投影(ADR-0016 / DEM-2)。"""
    return _app()._t1_session().snapshot()


@router.post("/api/t1-source/paste")
def api_t1_paste(req: PasteDraftRequest) -> JSONResponse:
    """粘贴变更要点 → 仅草稿,未确认不得 retrieve / 续命。"""
    result = _app()._t1_session().save_paste_draft(req.text)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=400)
    return JSONResponse(_app()._t1_session().snapshot())


@router.post("/api/t1-source/confirm")
def api_t1_confirm() -> JSONResponse:
    """人点「确认入库」后才 ingest。"""
    result = _app()._t1_session().confirm_paste()
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=400)
    return JSONResponse(_app()._t1_session().snapshot())


@router.post("/api/t1-source/synthetic")
def api_t1_synthetic() -> JSONResponse:
    """选用内置合成评测包(界面标明 synthetic)。"""
    appmod = _app()
    result = appmod._t1_session().select_synthetic(appmod.CORPUS)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=400)
    return JSONResponse(appmod._t1_session().snapshot())


@router.post("/api/t1-source/upload")
async def api_t1_upload(files: list[UploadFile] = File(...)) -> JSONResponse:
    """上传 T1 语料包 → ingest 后可检索。"""
    payload: list[tuple[str, str]] = []
    for f in files:
        raw = await f.read()
        try:
            payload.append((f.filename or "upload.md", raw.decode("utf-8")))
        except UnicodeDecodeError:
            return JSONResponse(
                {"error": f"{f.filename or 'upload'}:须为 UTF-8 文本 markdown"},
                status_code=400,
            )
    result = _app()._t1_session().ingest_upload_texts(payload)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=400)
    return JSONResponse(_app()._t1_session().snapshot())


@router.post("/api/t1-source/url")
def api_t1_url(req: ThinUrlRequest) -> JSONResponse:
    """薄 URL 入库:仅 www.mckinsey.com;失败四态零写(ADR-0027 / #171)。"""
    result = _app()._t1_session().ingest_from_url(req.url)
    if not result.ok:
        body: dict = {"error": result.error, "error_code": result.error_code}
        return JSONResponse(body, status_code=400)
    snap = _app()._t1_session().snapshot()
    return JSONResponse(snap)


@router.post("/api/import/draft")
def api_import_draft(req: DraftImportRequest) -> JSONResponse:
    """主张导入稿(MD/粘贴):按 ## claim_id 切条;缺 id → c-import-N。不做散文抽主张/LLM 切分。"""
    appmod = _app()
    try:
        docket, assigned = parse_claim_import_draft(req.text, question=req.question)
    except ClaimImportError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    # #678(I-01):非空 active_run 时硬 409(breaking vs #665/#669 的 200+preserved)
    conflict = appmod._active_run_conflict()
    if conflict is not None:
        return conflict
    ss._state["claims"] = docket.claims
    ss._state["question"] = docket.question
    ss._state["latch"] = dict(ss.EMPTY_LATCH)
    ss._state["trajectory"] = None
    ss._state["active_run_id"] = None
    row = appmod._sync_prepublish(new_run=True)
    appmod._write_run_snapshot()
    return JSONResponse({
        "imported": len(docket.claims),
        "assigned_ids": assigned,
        "question": docket.question,
        "claim_ids": [c.claim_id for c in docket.claims],
        "run": row,
    })


@router.get("/api/retrieval/precheck")
def api_retrieval_precheck() -> JSONResponse:
    """I-02(#679):开始复验前的本地权重预检(纯文件层 stat,毫秒级,不加载模型不触网)。

    缺权重时 UI 出可操作面板:约 1.1GB 说明、下载进度/失败原因,
    并列「重试下载」与「先用 BM25(精度降级)」。
    """
    from freshlatch.store.local_embed import embed_offline_requested
    from freshlatch.ui.weight_precheck import (
        local_embed_weights_ready,
        neural_rerank_weights_ready,
        resolved_cache_dir,
    )

    # #753:未设 FASTEMBED_CACHE_PATH 时仍返回解析后的绝对路径,不得为 null
    cache_dir = resolved_cache_dir()
    embedding = local_embed_weights_ready()
    reranker = neural_rerank_weights_ready()
    return JSONResponse({
        "ok": embedding and reranker,
        "embedding": embedding,
        "reranker": reranker,
        "offline": embed_offline_requested(),
        "cache_dir": cache_dir,
        "reranker_size_hint": "约 1.1GB",
        "download": ss._weight_download_status(),
    })


@router.post("/api/retrieval/precheck/download")
def api_retrieval_precheck_download() -> JSONResponse:
    """后台下载/预热两份本地权重;进度与失败原因经 GET 预检轮询。离线模式拒绝。"""
    from freshlatch.store.local_embed import embed_offline_requested

    if embed_offline_requested():
        return JSONResponse(
            {"error_code": "EMBED_OFFLINE",
             "error": ("离线模式已启用(HF_HUB_OFFLINE=1 或 FRESHLATCH_EMBED_OFFLINE=1),"
                       "不会发起下载。请在有网环境运行 python scripts/warmup_local_embed.py,"
                       "再用 FASTEMBED_CACHE_PATH 指向该缓存。")},
            status_code=409,
        )
    with ss._WEIGHT_DOWNLOAD_LOCK:
        already_running = ss._WEIGHT_DOWNLOAD_JOB["state"] == "running"
        if not already_running:
            ss._WEIGHT_DOWNLOAD_JOB.update({
                "state": "running",
                "error": None,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "started_monotonic": time.monotonic(),
            })
    if already_running:
        # 锁外取状态:_weight_download_status 内部自取同一把非可重入锁,
        # 在锁内调用会自死锁(#679 单测 test_download_rejects_double_start 钉住)。
        return JSONResponse(
            {"error": "下载已在进行中", "download": ss._weight_download_status()},
            status_code=409,
        )
    threading.Thread(target=ss._run_weight_download_job, daemon=True).start()
    return JSONResponse({"download": ss._weight_download_status()})
