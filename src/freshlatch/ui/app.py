"""复验单 UI:FastAPI 薄壳 + 手写 HTML/JS 双栏(左主张卡片,右原文面板)。

形态红线(§5.1):主界面是复验单,不是聊天框;主按钮 =「开始复验」;界面标注 SYNTHETIC。
HumanLatch 端点(W3 起,§5.5)为同步 def 端点:FastAPI 线程池执行,同步 SqliteSaver
不阻塞事件循环(ADR-0006 §8);写路径唯一 = gates/human_latch.py,核心包零 Web 依赖。
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from freshlatch.claim_import import ClaimImportError, parse_claim_import_draft  # noqa: E402
from freshlatch.claim_ledger import (  # noqa: E402
    export_claim_ledger_md,
    get_claim_ledger,
)
from freshlatch.evidence_bound import (  # noqa: E402
    PatchDraftStore,
    confirm_patch,
    discard_patch_draft,
    propose_patch,
    single_claim_reverify,
)
from freshlatch.models import Claim  # noqa: E402
from freshlatch.guardrails import Guardrails  # noqa: E402
from freshlatch.packs import PackPaths, resolve_pack  # noqa: E402
from freshlatch.latch import HumanLatch, HumanLatchError  # noqa: E402
from freshlatch.prepublish import (  # noqa: E402
    PrepublishRegistry,
    derive_run_status,
    disposition_for_claims,
    list_archived_t1_evidence_ids,
    list_t1_checksums,
    project_gate_results,
)
import uuid  # noqa: E402
from freshlatch.patch_events import record_human_review_events  # noqa: E402
from freshlatch.publish_hook import (  # noqa: E402
    HOOK_BIND_HOST_ENV,
    HOOK_DEFAULT_BIND_HOST,
    HOOK_TOKEN_ENV,
    HOOK_TOKEN_HEADER,
    HOOK_UNAUTHORIZED,
    deny_http_status,
    evaluate_publish_hook,
)
from freshlatch.runner import RunContext, Runner, load_docket  # noqa: E402
from freshlatch.publish_hook import (  # noqa: E402
    HOOK_CHECKSUM_DRIFT,
    checksums_fresh,
)
from freshlatch.sheet import (  # noqa: E402
    export_client_memo_gated,
    project_claim,
)
from freshlatch.store.checksum import make_checksum_fn  # noqa: E402
from freshlatch.gates.basis_rot import rot_claims  # noqa: E402
from freshlatch.store.ingest import parse_document  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402
from freshlatch.t1_source import T1SourceSession  # noqa: E402

# 测试可 monkeypatch 指向 tmp;生产默认 None → data/patch_events/
_PATCH_EVENTS_DIR = None
# #200:Evidence-bound 草案暂存(按 Run 隔离;未 confirm 不改正文/不写正式账本)
_PATCH_DRAFTS = PatchDraftStore()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# 占位与切换前第一课题路径一致;import 末尾 bind_active_pack 按 active_pack 覆盖
CORPUS = REPO_ROOT / "data" / "corpus"
DEMO_DOCKET = REPO_ROOT / "data" / "t0_docket.json"
CHECKPOINTS = REPO_ROOT / "data" / "checkpoints.db"

BADGE = {
    "fresh": ("绿 · 仍成立", "#1a7f37"),
    "stale": ("红 · 已失效", "#cf222e"),
    "unknown": ("灰 · 证据不足", "#6e7781"),
    "void": ("void · 已作废", "#8250df"),
}
MAIN_BUTTON_TEXT = "开始复验"  # 文案白名单(红线 2):主按钮唯一合法文案
VIEW_MODE_DEFAULT = "craftsman"  # DEM-6:默认职人视图(去角色化成交面)
# HTML 模板占位:index() 注入 VIEW_MODE_DEFAULT,避免 Python/JS 默认值漂移
_VIEW_MODE_TOKEN = "__VIEW_MODE_DEFAULT__"
EMPTY_LATCH = {"thread_id": None, "pending": []}  # 人审轮状态收口(不各处字面造 dict)
# DEM-4:步数/检索预算进度;天花板与 Guardrails 默认对齐(α-demo 可见性 ≠ latch 证明)
_G = Guardrails()
EMPTY_BUDGET = {
    "steps_used": 0,
    "lead_max_steps": _G.lead_max_steps,
    "retrieval_used": 0,
    "retrieval_budget": _G.retrieval_budget,
}
del _G

app = FastAPI(title="FreshLatch 复验单")
_state: dict = {"claims": [], "question": "", "trajectory": None, "running": False,
                "latch": dict(EMPTY_LATCH),
                "budget": dict(EMPTY_BUDGET),
                "run_ctx": None,
                "retrieve_zero_hits": [],  # DEM-5:本轮 retrieve 空命中;仅提示,不改写判定
                "active_run_id": None,  # 发前列表当前绑定 Run(#173)
                # #229:Run 绑定瞬间的 T1 checksum 快照;导出时与当前比对机械新鲜度
                "bound_t1_checksums": {}}
_prepublish = PrepublishRegistry()
_t1: T1SourceSession | None = None
ACTIVE_PACK: PackPaths


def bind_active_pack(pack_id: str | None = None) -> PackPaths:
    """把 UI 路径钉到 active_pack 解析结果。显式 pack_id 供测试切换,不改闸。"""
    global CORPUS, DEMO_DOCKET, CHECKPOINTS, ACTIVE_PACK, _t1
    pack = resolve_pack(pack_id)
    ACTIVE_PACK = pack
    CORPUS = pack.corpus
    DEMO_DOCKET = pack.docket
    CHECKPOINTS = pack.checkpoints
    _t1 = None
    return pack


bind_active_pack()


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
    if _state.get("running") and _state.get("run_ctx") is not None:
        return _budget_from_ctx(_state["run_ctx"])
    return dict(_state.get("budget") or EMPTY_BUDGET)


def _store() -> SQLiteStore:
    from freshlatch.store.local_embed import attach_local_embedder

    store = SQLiteStore(ACTIVE_PACK.sqlite)
    attach_local_embedder(store)
    return store


def _pack_payload() -> dict:
    """只读展示当前包。问题句优先用本会话已导入的 docket。"""
    pack = ACTIVE_PACK
    question = _state["question"] or pack.question
    return {
        "pack_id": pack.pack_id,
        "label": pack.label,
        "synthetic": pack.synthetic,
        "question": question,
    }


def _t1_session() -> T1SourceSession:
    """进程内 T1 来源三卡会话;测试可通过 _reset_t1_source 换店。"""
    global _t1
    if _t1 is None:
        _t1 = T1SourceSession(_store(), corpus_root=CORPUS)
    return _t1


def _reset_t1_source(store: SQLiteStore | None = None) -> T1SourceSession:
    """测试/重启入口:清空三卡状态并绑到给定 store。"""
    global _t1
    _t1 = T1SourceSession(store or _store(), corpus_root=CORPUS)
    return _t1


def _latch() -> HumanLatch:
    # Batch 2 档 2:renew 半边真 checksum_fn(语料现算,禁读库列);不升格为 latch 证明
    return HumanLatch(_store(), CHECKPOINTS, mode="online",
                      checksum_fn=make_checksum_fn(CORPUS))


def _claim_to_dict(store: SQLiteStore, c) -> dict:
    """薄委托:与导出/对账单测同吃核心包 project_claim(K4)。"""
    return project_claim(store, c)


def _source_label() -> str:
    """发前来源短标签(包 id + T1 入口;非编排角色名)。"""
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
    """当前库 T1 doc_id→checksum 映射(供发前钩子机械新鲜度)。"""
    s = store if store is not None else _store()
    return {
        str(row["doc_id"]): str(row.get("checksum") or "")
        for row in list_t1_checksums(s)
    }


def _bind_run_checksums(store: SQLiteStore | None = None) -> None:
    """把当前 T1 checksum 钉到 active Run(新 Run / 首次绑定时)。"""
    _state["bound_t1_checksums"] = _current_t1_checksum_map(store)


def _run_checksum_fresh(store: SQLiteStore | None = None) -> bool:
    """Run 绑定 checksum 相对当前是否未漂。"""
    recorded = _state.get("bound_t1_checksums") or {}
    current = _current_t1_checksum_map(store)
    return checksums_fresh(recorded, current)


def _sync_prepublish(*, new_run: bool = False) -> dict:
    """把当前会话投影进发前列表注册表;详情仍是既有复验单。"""
    claims = list(_state["claims"])
    running = bool(_state["running"])
    latch = _state.get("latch") or EMPTY_LATCH
    status = derive_run_status(running=running, latch=latch)
    if status == "已落档" and not claims and not _state.get("trajectory"):
        status = "未复验"
    if new_run:
        run_id = f"run-{uuid.uuid4().hex[:10]}"
        _state["active_run_id"] = run_id
        _bind_run_checksums()
    else:
        run_id = _state.get("active_run_id")
        # 尚无绑定快照时补钉一次(不覆盖已有,避免把漂移洗成未漂)
        if not (_state.get("bound_t1_checksums") or {}):
            _bind_run_checksums()
    traj = str(_state["trajectory"]) if _state.get("trajectory") else None
    summary = _prepublish.upsert(
        run_id=run_id,
        title=_state["question"] or ACTIVE_PACK.question or ACTIVE_PACK.label,
        source=_source_label(),
        claims=claims,
        status=status,
        pack_id=ACTIVE_PACK.pack_id,
        trajectory=traj,
    )
    _state["active_run_id"] = summary.run_id
    return summary.to_dict()


def _patch_run_id() -> str:
    """补丁草案隔离键:优先当前发前 Run,否则 session。"""
    return str(_state.get("active_run_id") or "session")


def _patch_drafts_payload() -> dict[str, dict]:
    """本 Run 暂存草案投影(claim_id → draft dict)。"""
    return {
        cid: d.to_dict()
        for cid, d in _PATCH_DRAFTS.list_for_run(_patch_run_id()).items()
    }


def _detail_extras(store: SQLiteStore) -> dict:
    """复验单增量包:包结论条 + T1 checksum + 逐条闸结果(#173) + 补丁条带(#200) + 主张台账(#228)。"""
    claims = list(_state["claims"])
    # 台账旁路:全库只读投影(作废名单跨 Run);不按发前 run_id 截断作废名单语义
    ledger = get_claim_ledger(store, run_id=None)
    return {
        "disposition": disposition_for_claims(claims),
        "run_status": derive_run_status(
            running=bool(_state["running"]), latch=_state.get("latch")),
        "active_run_id": _state.get("active_run_id"),
        "t1_checksums": list_t1_checksums(store),
        "gate_results": project_gate_results(claims),
        # #200:本 Run 已入库 evidence_id 多选源 + 暂存草案(无 C|T / 无薄对话)
        "archived_t1_ids": list_archived_t1_evidence_ids(store),
        "patch_drafts": _patch_drafts_payload(),
        # #228:主张台账旁路(invalidation_list ∪ latch_log discard/renew);与 patch_events 分缝
        "claim_ledger": ledger,
    }


@app.get("/api/claims")
def api_claims() -> dict:
    """拉复验单:对可见 fresh∧basis 主张跑与复验入口同一腐烂路径并真写库(ADR-0025)。"""
    store = _store()
    # 档 3b UI 触发:禁止只改展示;与 Runner 共用 check_basis/apply_rot
    rot_claims(store, list(_state["claims"]), make_checksum_fn(CORPUS))
    extras = _detail_extras(store)
    return {
        "question": _state["question"],
        "claims": [_claim_to_dict(store, c) for c in _state["claims"]],
        "trajectory": str(_state["trajectory"]) if _state["trajectory"] else None,
        "running": _state["running"],
        "latch": _state["latch"],
        # DEM-5:零命中告警投影;UI 只展示,不得据此改写 status
        "retrieve_zero_hits": list(_state.get("retrieve_zero_hits") or []),
        "budget": _current_budget(),  # DEM-4:复验中/完成后可见
        "pack": _pack_payload(),
        **extras,
    }


@app.get("/api/claim-ledger")
def api_claim_ledger(run_id: str | None = Query(default=None)) -> dict:
    """#228 主张台账只读投影 API:discard ∪ renew;renew∉作废名单。"""
    return get_claim_ledger(_store(), run_id=run_id or None)


@app.get("/api/claim-ledger/export.md")
def api_claim_ledger_export(run_id: str | None = Query(default=None)) -> Response:
    """#228 主张台账 Markdown 导出(只读;零新写表)。"""
    md = export_claim_ledger_md(_store(), run_id=run_id or None)
    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="claim-ledger.md"'},
    )


@app.post("/api/client-memo/export")
def api_client_memo_export(
    ack_needs_patch: bool = Query(default=False),
) -> Response:
    """#229 导出客户备忘:与 CLI 共用 export_client_memo_gated。

    deny → 403 + JSON(零写 Memo);allow → Markdown 附件。
    需补丁须显式 ack_needs_patch;页眉强制「需补丁」。
    """
    from datetime import datetime, timezone

    store = _store()
    # 确保有 active Run 绑定(无则新建并钉 checksum)
    if not _state.get("active_run_id"):
        _sync_prepublish(new_run=True)
    else:
        _sync_prepublish(new_run=False)

    claims = list(_state["claims"])
    projections = [project_claim(store, c) for c in claims]
    disposition = disposition_for_claims(claims)
    hook, md = export_client_memo_gated(
        run_id=_state.get("active_run_id"),
        disposition=disposition,
        projections=projections,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ack_needs_patch=bool(ack_needs_patch),
        checksum_fresh=_run_checksum_fresh(store),
        question=str(_state.get("question") or ""),
        synthetic=bool(getattr(ACTIVE_PACK, "synthetic", False)),
        out_path=None,  # HTTP 响应体交付;服务端不落盘
    )
    if not hook.allow:
        # deny 零写:不返回 Markdown 体
        status = 403
        if hook.code == HOOK_CHECKSUM_DRIFT:
            status = 409
        return JSONResponse(hook.to_dict(), status_code=status)

    assert md is not None
    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="client-memo.md"',
            # HTTP 头仅 ASCII:中文 disposition 走响应体页眉,不进 header
            "X-FreshLatch-Hook-Code": hook.code,
            "X-FreshLatch-Needs-Patch-Banner": (
                "1" if hook.requires_needs_patch_banner else "0"
            ),
        },
    )


@app.get("/api/prepublish/runs")
def api_prepublish_runs() -> dict:
    """发前列表:标题/来源、disposition、更新时间、Run 状态(#173)。"""
    if _state.get("claims") or _state.get("trajectory") or _state.get("active_run_id"):
        _sync_prepublish(new_run=False)
    return {"runs": _prepublish.list_runs(), "active_run_id": _state.get("active_run_id")}


@app.get("/api/prepublish/runs/{run_id}")
def api_prepublish_run(run_id: str) -> JSONResponse:
    """发前 Run 摘要;详情 UI 仍走既有复验单(增量包结论条)。"""
    row = _prepublish.get(run_id)
    if row is None:
        return JSONResponse({"error": f"未找到 Run {run_id}"}, status_code=404)
    return JSONResponse({"run": row.to_dict(), "detail_path": "/"})


class PublishHookCheckRequest(BaseModel):
    """入站 publish-hook check 请求体(#230):必填 run_id;可选 ack_needs_patch。"""

    run_id: str | None = None
    ack_needs_patch: bool = False


def _hook_token_denied(request: Request) -> JSONResponse | None:
    """可选共享密钥头:仅当环境变量已配置时强制校验;缺失配置则本机冒烟可测。"""
    expected = (os.environ.get(HOOK_TOKEN_ENV) or "").strip()
    if not expected:
        return None
    provided = (request.headers.get(HOOK_TOKEN_HEADER) or "").strip()
    if provided == expected:
        return None
    body = {
        "allow": False,
        "disposition": None,
        "code": HOOK_UNAUTHORIZED,
        "message": "入站 check 共享密钥头校验失败",
        "requires_needs_patch_banner": False,
    }
    return JSONResponse(body, status_code=403)


@app.post("/api/publish-hook/check")
def api_publish_hook_check(
    req: PublishHookCheckRequest, request: Request,
) -> JSONResponse:
    """入站 publish-hook check(#230):与 Memo 同闸;deny → 403/409;非插件平台。

    体:必填 run_id、可选 ack_needs_patch。缺 run_id fail-closed。
    可选头 `X-FreshLatch-Hook-Token`(环境变量 `FRESHLATCH_HOOK_TOKEN` 已设时强制)。
    """
    denied = _hook_token_denied(request)
    if denied is not None:
        return denied

    rid = req.run_id
    disposition = None
    if rid is not None and str(rid).strip():
        row = _prepublish.get(str(rid).strip())
        if row is not None:
            disposition = row.disposition

    # 入站探闸:只读 Registry 包结论 + 当前会话未漂默认;不触发整包再验
    result = evaluate_publish_hook(
        run_id=rid,
        disposition=disposition,
        ack_needs_patch=bool(req.ack_needs_patch),
        checksum_fresh=True,
    )
    body = result.to_dict()
    if result.allow:
        return JSONResponse(body, status_code=200)
    return JSONResponse(body, status_code=deny_http_status(result.code))


@app.post("/api/import")
def api_import() -> dict:
    """JSON docket 高级入口(Workflow):只读 statement 与 t0_evidence_ids,不做新调查。"""
    docket = load_docket(DEMO_DOCKET)
    _state["claims"] = docket.claims
    _state["question"] = docket.question  # 单一真相:当前课题包 docket
    _state["latch"] = dict(EMPTY_LATCH)
    _state["trajectory"] = None
    _state["active_run_id"] = None
    row = _sync_prepublish(new_run=True)
    return {"imported": len(docket.claims), "run": row}


class PasteDraftRequest(BaseModel):
    text: str


class ThinUrlRequest(BaseModel):
    """薄 URL 入库请求:单条白名单 URL(ADR-0027 / #171)。"""

    url: str


class DraftImportRequest(BaseModel):
    text: str
    question: str | None = None


@app.get("/api/t1-source")
def api_t1_source() -> dict:
    """T1 来源三卡状态投影(ADR-0016 / DEM-2)。"""
    return _t1_session().snapshot()


@app.post("/api/t1-source/paste")
def api_t1_paste(req: PasteDraftRequest) -> JSONResponse:
    """粘贴变更要点 → 仅草稿,未确认不得 retrieve / 续命。"""
    result = _t1_session().save_paste_draft(req.text)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=400)
    return JSONResponse(_t1_session().snapshot())


@app.post("/api/t1-source/confirm")
def api_t1_confirm() -> JSONResponse:
    """人点「确认入库」后才 ingest。"""
    result = _t1_session().confirm_paste()
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=400)
    return JSONResponse(_t1_session().snapshot())


@app.post("/api/t1-source/synthetic")
def api_t1_synthetic() -> JSONResponse:
    """选用内置合成评测包(界面标明 synthetic)。"""
    result = _t1_session().select_synthetic(CORPUS)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=400)
    return JSONResponse(_t1_session().snapshot())


@app.post("/api/t1-source/upload")
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
    result = _t1_session().ingest_upload_texts(payload)
    if not result.ok:
        return JSONResponse({"error": result.error}, status_code=400)
    return JSONResponse(_t1_session().snapshot())


@app.post("/api/t1-source/url")
def api_t1_url(req: ThinUrlRequest) -> JSONResponse:
    """薄 URL 入库:仅 www.mckinsey.com;失败四态零写(ADR-0027 / #171)。"""
    result = _t1_session().ingest_from_url(req.url)
    if not result.ok:
        body: dict = {"error": result.error, "error_code": result.error_code}
        return JSONResponse(body, status_code=400)
    snap = _t1_session().snapshot()
    return JSONResponse(snap)

@app.post("/api/import/draft")
def api_import_draft(req: DraftImportRequest) -> JSONResponse:
    """主张导入稿(MD/粘贴):按 ## claim_id 切条;缺 id → c-import-N。不做散文抽主张/LLM 切分。"""
    try:
        docket, assigned = parse_claim_import_draft(req.text, question=req.question)
    except ClaimImportError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    _state["claims"] = docket.claims
    _state["question"] = docket.question
    _state["latch"] = dict(EMPTY_LATCH)
    _state["trajectory"] = None
    _state["active_run_id"] = None
    row = _sync_prepublish(new_run=True)
    return JSONResponse({
        "imported": len(docket.claims),
        "assigned_ids": assigned,
        "question": docket.question,
        "claim_ids": [c.claim_id for c in docket.claims],
        "run": row,
    })


@app.post("/api/reverify")
def api_reverify() -> JSONResponse:
    """主按钮「开始复验」:端到端真主链(Lead 裸循环 + 规则闸),轨迹落盘。

    整轮跑完(W3 起)进 HumanLatch:图在收尾节点 interrupt,红/黄灯主张进待审清单,
    复验单顶部出「待人工」横幅(轮次级单 interrupt,一次 resume 传整个决定列表)。
    """
    if _state["running"]:
        return JSONResponse({"error": "已有复验在进行中"}, status_code=409)
    if not _t1_session().state.ready:
        return JSONResponse(
            {"error": "未选定合法 T1 来源,不得假装已有最新事实(请先完成 T1 来源三卡)"},
            status_code=400,
        )
    if not _state["claims"]:
        api_import()
    _state["running"] = True
    try:
        runner = Runner(_store(), checksum_fn=make_checksum_fn(CORPUS))
        _state["run_ctx"] = runner.ctx
        _state["budget"] = _budget_from_ctx(runner.ctx)
        _sync_prepublish(new_run=True)  # 新 Run 进发前列表;状态=复验中
        result = runner.run(list(_state["claims"]))
        _state["trajectory"] = result.trajectory_path
        _state["budget"] = _budget_from_ctx(runner.ctx)  # 会话内保留用量摘要(DEM-4)
        # DEM-5:记录零命中清单供 UI 强提示;不改写任何主张 status
        _state["retrieve_zero_hits"] = list(result.retrieve_zero_hits)
        rnd = _latch().enter_round(_state["claims"])  # 无红/黄灯则 thread_id=None 直接完成
        _state["latch"] = {"thread_id": rnd.thread_id, "pending": rnd.pending}
        run_row = _sync_prepublish(new_run=False)
    finally:
        _state["running"] = False
        _state["run_ctx"] = None
    store = _store()
    extras = _detail_extras(store)
    return JSONResponse({
        "claims": [_claim_to_dict(store, c) for c in _state["claims"]],
        "trajectory": str(result.trajectory_path),
        "retrieval_used": result.retrieval_used,
        "steps_by_claim": result.steps_by_claim,
        "decoding": result.decoding.__dict__,
        "latch": _state["latch"],
        "retrieve_zero_hits": list(_state["retrieve_zero_hits"]),
        "budget": dict(_state["budget"]),
        "run": run_row,
        **extras,
    })


class DecideRequest(BaseModel):
    thread_id: str
    decisions: list[dict] = []


@app.post("/api/latch/decide")
def api_latch_decide(req: DecideRequest) -> JSONResponse:
    """人审批量提交(同步 def):Command(resume=整个决定列表)恢复 interrupt,execute 落档。

    成功决定追加 patch_events(ADR-0027 / #174 主缝记账);arm 后台固定,不进发前 UX。
    """
    if _state["latch"].get("thread_id") != req.thread_id:
        return JSONResponse({"error": "该轮人审不存在或已提交(刷新复验单查看最新状态)"}, status_code=409)
    # 人审前包结论快照(写入 patch_events.before_disp)
    before_disp = disposition_for_claims(list(_state["claims"]))
    store = _store()
    t1_ids = [
        f"{row['doc_id']}#{row.get('checksum') or ''}@T1"
        for row in list_t1_checksums(store)
        if row.get("doc_id")
    ]
    try:
        latch = _latch()
        results = latch.decide(req.thread_id, req.decisions, claims=list(_state["claims"]))
        latch.prune_rounds()  # 轮次 checkpoint 留最近 5 个(ADR-0006 §9,业务侧删行)
    except HumanLatchError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    # 贯通记账:至少一条人审相关事件可读(#174)
    patch_rows = record_human_review_events(
        results,
        before_disp=before_disp,
        t1_ids=t1_ids,
        arm="C",
        actor="human",
        events_dir=_PATCH_EVENTS_DIR,
    )
    _state["latch"] = dict(EMPTY_LATCH)
    run_row = _sync_prepublish(new_run=False)
    extras = _detail_extras(store)
    return JSONResponse({
        "results": results,
        "claims": [_claim_to_dict(store, c) for c in _state["claims"]],
        "latch": _state["latch"],
        "run": run_row,
        "patch_events_written": len(patch_rows),
        **extras,
    })


class RerunRequest(BaseModel):
    claim_id: str


@app.post("/api/latch/rerun")
def api_latch_rerun(req: RerunRequest) -> JSONResponse:
    """人点「重跑作废主张」(同步 def,不自动):新 thread 单主张迷你复验,结果挂时间线。"""
    claim = next((c for c in _state["claims"] if c.claim_id == req.claim_id), None)
    if claim is None:
        return JSONResponse({"error": f"未找到主张 {req.claim_id}"}, status_code=404)
    try:
        entry = _latch().rerun(claim)
    except HumanLatchError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return JSONResponse({"entry": entry, "claim": _claim_to_dict(_store(), claim)})


@app.get("/api/latch/status")
def api_latch_status() -> dict:
    """人审轮状态;进程重启后可用 thread_id 从 checkpoint 恢复待审清单(#11 §5.10)。"""
    return {"latch": _state["latch"]}


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


@app.post("/api/patch/propose")
def api_patch_propose(req: ProposePatchRequest) -> JSONResponse:
    """提案暂存(ADR-0029 / #200):走 propose_patch;零改正文、零写正式账本。"""
    result = propose_patch(
        claim_id=req.claim_id,
        after_text=req.after_text,
        t1_ids=req.t1_ids,
        claims=list(_state["claims"]),
        drafts=_PATCH_DRAFTS,
        run_id=_patch_run_id(),
    )
    if not result.ok:
        return JSONResponse(result.to_dict(), status_code=400)
    store = _store()
    extras = _detail_extras(store)
    return JSONResponse({
        **result.to_dict(),
        "claims": [_claim_to_dict(store, c) for c in _state["claims"]],
        **extras,
    })


def _confirm_patch_reverify(claim: Claim) -> tuple[str, str]:
    """产品路径单条再验(#199);测试可 monkeypatch 为确定性 noop 以保持零 LLM。"""
    return single_claim_reverify(
        claim,
        store=_store(),
        checksum_fn=make_checksum_fn(CORPUS),
    )


@app.post("/api/patch/confirm")
def api_patch_confirm(req: ConfirmPatchRequest) -> JSONResponse:
    """确认改稿(#200):confirm_patch 硬闸;产品路径恒 arm=T;发前无 C|T 开关。"""
    store = _store()
    archived = list_archived_t1_evidence_ids(store)
    # #199 后 confirm 须触发单条再验;经可测钩子注入(CI 零 LLM 可 monkeypatch)
    result = confirm_patch(
        claim_id=req.claim_id,
        claims={c.claim_id: c for c in _state["claims"]},
        claim_list=_state["claims"],
        archived_t1_ids=archived,
        minutes=req.minutes,
        after_text=req.after_text,
        t1_ids=req.t1_ids,
        patch_span=req.patch_span,
        drafts=_PATCH_DRAFTS,
        run_id=_patch_run_id(),
        events_dir=_PATCH_EVENTS_DIR,
        actor="human",
        reverify_fn=_confirm_patch_reverify,
    )
    if not result.ok:
        return JSONResponse(result.to_dict(), status_code=400)
    run_row = _sync_prepublish(new_run=False)
    extras = _detail_extras(store)
    return JSONResponse({
        **result.to_dict(),
        "claims": [_claim_to_dict(store, c) for c in _state["claims"]],
        "run": run_row,
        **extras,
    })


@app.post("/api/patch/discard-draft")
def api_patch_discard_draft(req: DiscardPatchDraftRequest) -> JSONResponse:
    """丢弃未确认改稿草案(#200);不影响主张正文与正式账本。"""
    discarded = discard_patch_draft(
        claim_id=req.claim_id,
        drafts=_PATCH_DRAFTS,
        run_id=_patch_run_id(),
    )
    store = _store()
    extras = _detail_extras(store)
    return JSONResponse({
        "ok": True,
        "claim_id": req.claim_id,
        "discarded": discarded,
        "claims": [_claim_to_dict(store, c) for c in _state["claims"]],
        **extras,
    })


@app.get("/api/source/{doc_id}")
def api_source(doc_id: str, as_of: str = Query("T1", pattern="^(T0|T1)$")) -> dict:
    """点回原文:返回条款级锚点段落,前端定位 + 高亮。"""
    path = CORPUS / as_of.lower() / f"{doc_id}.md"
    if not path.exists():
        return JSONResponse({"error": f"未找到 {doc_id} 的 {as_of} 快照"}, status_code=404)
    doc, chunks = parse_document(path)
    return {
        "doc_id": doc_id,
        "as_of": as_of,
        "title": doc.title,
        "source_type": doc.source_type,
        "sections": [{"anchor": c.clause_id, "text": c.text} for c in chunks],
    }


_UI_STATIC = Path(__file__).resolve().parent / "static"
HTML_PAGE = (_UI_STATIC / "reverify.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    # 注入单一真相默认视图,避免 Python 常量与 JS 初值漂移
    html = HTML_PAGE.replace(_VIEW_MODE_TOKEN, VIEW_MODE_DEFAULT)
    if VIEW_MODE_DEFAULT == "craftsman":
        # 职人默认:审计钮无 on;职人钮保持模板内 class="on"
        pass
    else:
        html = html.replace('id="view-craftsman" class="on"', 'id="view-craftsman"')
        html = html.replace('id="view-audit"', 'id="view-audit" class="on"', 1)
    return html


# 发前列表壳:改编 mission_control 列表→详情 IA;字段换 Run/disposition(#173)
PREPUBLISH_HTML = (_UI_STATIC / "prepublish.html").read_text(encoding="utf-8")


@app.get("/prepublish", response_class=HTMLResponse)
def prepublish_index() -> str:
    """发前列表页(#173):mission_control 列表壳改编,业务字段换 Run/disposition。"""
    return PREPUBLISH_HTML


if __name__ == "__main__":
    import uvicorn

    # #230:入站 check 默认仅本机回环;可用 FRESHLATCH_BIND_HOST 覆盖,禁止把 0.0.0.0 无鉴权当 Done
    _bind = (os.environ.get(HOOK_BIND_HOST_ENV) or "").strip() or HOOK_DEFAULT_BIND_HOST
    uvicorn.run(app, host=_bind, port=8000)
