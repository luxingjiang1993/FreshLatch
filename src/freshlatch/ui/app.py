"""复验单 UI:FastAPI 薄壳 + 手写 HTML/JS 双栏(左主张卡片,右原文面板)。

形态红线(§5.1):主界面是复验单,不是聊天框;主按钮 =「开始复验」;界面标注 SYNTHETIC。
HumanLatch 端点(W3 起,§5.5)为同步 def 端点:FastAPI 线程池执行,同步 SqliteSaver
不阻塞事件循环(ADR-0006 §8);写路径唯一 = gates/human_latch.py,核心包零 Web 依赖。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI, File, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

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


HTML_PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>FreshLatch 复验单 — SYNTHETIC</title>
<style>
 body{font-family:system-ui,"Microsoft YaHei",sans-serif;margin:0;background:#f6f8fa}
 header{background:#0a2540;color:#fff;padding:12px 24px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
 header .syn{background:#b45309;color:#fff;font-size:12px;padding:2px 10px;border-radius:10px}
 main{display:grid;grid-template-columns:44% 56%;gap:0;height:calc(100vh - 53px)}
 #claims{overflow-y:auto;border-right:1px solid #d0d7de;padding:12px 16px}
 #pane{overflow-y:auto;padding:12px 16px}
 .claim{border:1px solid #d0d7de;border-left:6px solid #999;border-radius:6px;padding:8px 12px;
        margin-bottom:8px;cursor:pointer;background:#fff}
 .claim.sel{outline:2px solid #0969da}
 .claim.voided{opacity:.55;background:#f0f0f2}
 .badge{font-size:12px;font-weight:600;margin-left:8px}
 .reason{font-size:13px;color:#57606a;margin-top:4px;white-space:pre-wrap}
 .ev{font-size:12px;margin-top:4px}
 .ev a{color:#0969da;cursor:pointer;text-decoration:none;margin-right:8px}
 .ev a:hover{text-decoration:underline}
 button.big{background:#1f883d;color:#fff;border:0;border-radius:6px;padding:8px 18px;font-size:15px;cursor:pointer}
 button.big:disabled{background:#9e9e9e;cursor:wait}
 .latch button{margin-right:8px;padding:6px 14px;border-radius:6px;border:1px solid #d0d7de;cursor:pointer}
 .latch button.void{background:#8250df;color:#fff;border-color:#8250df}
 .latch button.rerun{background:#fff;color:#8250df}
 .latch button.renew{background:#1a7f37;color:#fff;border-color:#1a7f37}
 /* 已选待提交态:与 .renew 同特异性且靠后,才能盖过按钮本色(卡片在 .latch 内) */
 .latch button.picked,#banner button.picked{background:#fff8c5;border-color:#d4a72c;color:#8250df;cursor:default}
 #banner{background:#fff8c5;border:1px solid #d4a72c;border-radius:6px;padding:10px 12px;margin-bottom:10px}
 #banner .pend{border-top:1px dashed #d4a72c;margin-top:8px;padding-top:8px}
 #banner .pend .picked{color:#8250df;font-weight:600}
 .doc{background:#fff;border:1px solid #d0d7de;border-radius:6px;padding:10px 14px;margin-bottom:10px}
 .doc .clause{margin:8px 0;padding:6px 8px;border-radius:4px;cursor:pointer}
 .doc .clause:hover{background:#f6f8fa}
 .doc .clause.hit{background:#fff8c5;outline:2px solid #d4a72c}
 mark{background:#fff8c5;padding:1px 3px;border-radius:3px}
 .asof{font-size:11px;color:#fff;background:#57606a;border-radius:4px;padding:1px 6px;margin-right:6px}
 .tabs button{padding:4px 12px;border:1px solid #d0d7de;background:#fff;cursor:pointer}
 .tabs button.on{background:#0a2540;color:#fff}
 .view-toggle{display:inline-flex;gap:0;margin-left:8px}
 .view-toggle button{padding:4px 12px;border:1px solid #d0d7de;background:#fff;color:#0a2540;
                     cursor:pointer;font-size:13px}
 .view-toggle button:first-child{border-radius:6px 0 0 6px}
 .view-toggle button:last-child{border-radius:0 6px 6px 0;border-left:0}
 .view-toggle button.on{background:#1f6feb;color:#fff;border-color:#1f6feb}
 #status{font-size:13px;color:#57606a}
 #audit-panel{display:none;margin:0 16px 10px;background:#fff;border:1px solid #d0d7de;
              border-radius:6px;padding:10px 14px;font-size:13px;color:#57606a}
 #audit-panel.visible{display:block}
 #audit-panel code{word-break:break-all}
 #how-to-read{margin:0 16px 10px;background:#fff;border:1px solid #d0d7de;border-radius:6px;
              padding:8px 12px;font-size:13px;color:#57606a}
 #how-to-read strong{color:#0a2540}
 #audit-override-filter{display:block;margin-top:8px}
 details{margin-top:12px;background:#fff;border:1px solid #d0d7de;border-radius:6px;padding:8px 12px}
 code{background:#eff1f3;padding:1px 5px;border-radius:4px}
 .timeline{font-size:12px;color:#57606a;margin-top:6px;border-top:1px dashed #d0d7de;padding-top:4px}
 .timeline div{margin:2px 0}
 .modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:10}
 .modal .box{background:#fff;border-radius:8px;max-width:520px;margin:14vh auto;padding:18px 22px}
 .modal button{margin-right:10px;padding:8px 16px;border-radius:6px;border:1px solid #d0d7de;cursor:pointer}
 .modal .ok{background:#8250df;color:#fff;border-color:#8250df}          /* 作废确认 */
 .modal .renew-ok{background:#1a7f37;color:#fff;border-color:#1a7f37}     /* 续命确认 */
 .modal select{width:100%;margin-top:6px;padding:6px 8px;border-radius:6px;border:1px solid #d0d7de;
               font-family:ui-monospace,monospace;font-size:12px}
 #t1-source{background:#fff;border:1px solid #d0d7de;border-radius:6px;padding:10px 12px;margin-bottom:12px}
 #t1-source h3{margin:0 0 8px;font-size:15px}
 #t1-source .hint{font-size:12px;color:#57606a;margin-bottom:8px}
 #t1-source .cards{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
 #t1-source .card{border:1px solid #d0d7de;border-radius:6px;padding:8px;background:#f6f8fa}
 #t1-source .card.sel{outline:2px solid #0969da;background:#ddf4ff}
 #t1-source .card h4{margin:0 0 6px;font-size:13px}
 #t1-source .card .syn-tag{background:#b45309;color:#fff;font-size:11px;padding:1px 6px;border-radius:8px}
 #t1-source textarea{width:100%;min-height:72px;font-family:ui-monospace,Consolas,monospace;font-size:12px;
                     border:1px solid #d0d7de;border-radius:4px;padding:6px;box-sizing:border-box}
 #t1-source button{margin-top:6px;padding:5px 10px;border-radius:6px;border:1px solid #d0d7de;cursor:pointer;background:#fff}
 #t1-source button.primary{background:#1f883d;color:#fff;border-color:#1f883d}
 #t1-source .net{font-size:12px;color:#57606a;margin-top:8px}
 #t1-source .msg{font-size:12px;margin-top:6px;color:#0969da}
 #t1-source .thin-url{margin-top:10px;padding-top:8px;border-top:1px dashed #d0d7de}
 #t1-source .thin-url input[type=url]{width:100%;font-size:12px;padding:5px 8px;
  border:1px solid #d0d7de;border-radius:6px;box-sizing:border-box}
 #t1-source .thin-url .hint{margin-top:4px}
 /* DEM-5:检索零命中强提示(非判定闸;不改写 status) */
 #retrieve-zero-hit{background:#fff1f0;border:2px solid #cf222e;border-radius:6px;
   padding:10px 12px;margin-bottom:10px;color:#82071e}
 #retrieve-zero-hit b{font-size:14px}
 #retrieve-zero-hit .note{font-size:12px;margin-top:6px;color:#57606a}
 #retrieve-zero-hit ul{margin:6px 0 0;padding-left:18px;font-size:12px;font-family:ui-monospace,Consolas,monospace}
 #retrieve-unknown-note{font-size:12px;color:#57606a;margin:0 0 10px;padding:6px 8px;
   border-left:3px solid #d0d7de;background:#f6f8fa}
 #import-panel{display:none;background:#fff;border:1px solid #d0d7de;border-radius:6px;
               padding:10px 12px;margin-bottom:10px}
 #import-panel.open{display:block}
 #import-panel textarea{width:100%;min-height:140px;font-family:ui-monospace,Consolas,monospace;
                        font-size:12px;padding:8px;border:1px solid #d0d7de;border-radius:6px;
                        box-sizing:border-box;resize:vertical}
 #import-panel .hint{font-size:12px;color:#57606a;margin:6px 0}
 header button.ghost{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.45);
                     border-radius:6px;padding:6px 12px;font-size:13px;cursor:pointer}
 #budget-progress{display:flex;flex-direction:column;gap:4px;min-width:200px;font-size:12px;color:#fff}
 .budget-row{display:flex;align-items:center;gap:8px}
 .budget-label{width:2.5em;opacity:.9}
 .budget-track{flex:1;height:6px;background:rgba(255,255,255,.25);border-radius:3px;overflow:hidden}
 .budget-fill{height:100%;background:#3fb950;width:0%;transition:width .2s linear}
 .budget-text{font-variant-numeric:tabular-nums;min-width:3.5em;text-align:right;opacity:.95}
 /* #173 发前增量:包结论条 + checksum/闸可见(不造第三套详情) */
 #disposition-bar{margin:0 16px 10px;background:#fff;border:1px solid #d0d7de;border-radius:6px;
                  padding:10px 14px;display:flex;gap:16px;flex-wrap:wrap;align-items:center}
 #disposition-bar .disp{font-size:18px;font-weight:700}
 #disposition-bar .meta{font-size:12px;color:#57606a}
 #disposition-bar .disp.ok{color:#1a7f37}
 #disposition-bar .disp.patch{color:#9a6700}
 #disposition-bar .disp.block{color:#cf222e}
 /* #229 Client Memo 套闸导出入口(对照 mission_control 导出形态;禁第二 UI 栈) */
 #disposition-bar button.export-memo{padding:5px 12px;border-radius:6px;border:1px solid #d0d7de;
                                    cursor:pointer;background:#fff;font-size:13px}
 #disposition-bar label.ack-needs-patch{font-size:12px;color:#57606a;display:inline-flex;
                                       align-items:center;gap:4px}
 #disposition-bar #memo-export-msg{font-size:12px;color:#cf222e}
 #t1-checksums,#gate-results{margin:0 16px 10px;background:#fff;border:1px solid #d0d7de;
                             border-radius:6px;padding:8px 12px;font-size:12px;color:#57606a}
 #t1-checksums code,#gate-results code{word-break:break-all}
 #t1-checksums.craftsman-hide,#gate-results.craftsman-hide{display:none}
 /* #228 主张台账旁路:默认可折叠;与 patch_events 分缝 */
 #claim-ledger{margin:0 16px 10px;background:#fff;border:1px solid #d0d7de;border-radius:6px;
               padding:8px 12px;font-size:13px;color:#57606a}
 #claim-ledger summary{cursor:pointer;font-weight:600;color:#0a2540}
 #claim-ledger .hint{font-size:12px;margin:6px 0;color:#57606a}
 #claim-ledger ul{margin:6px 0 0;padding-left:18px}
 #claim-ledger button.export-md{margin-top:8px;padding:5px 12px;border-radius:6px;
                               border:1px solid #d0d7de;cursor:pointer;background:#fff;font-size:13px}
 #t1-checksums.craftsman-soft{display:block}
 a.nav-prepublish{color:#fff;font-size:13px;margin-left:8px}
 /* #200 Evidence-bound 改稿条带:挂在主张卡内增量区(表单闭环) */
 .patch-strip{margin-top:8px;padding:8px 10px;border:1px dashed #d0d7de;border-radius:6px;
              background:#f6f8fa;font-size:13px}
 .patch-strip .patch-title{font-weight:600;color:#0a2540;margin-bottom:6px}
 .patch-strip .patch-hint{font-size:12px;color:#57606a;margin:0 0 8px}
 .patch-strip label{display:block;font-size:12px;color:#57606a;margin:6px 0 2px}
 .patch-strip textarea{width:100%;min-height:56px;font-family:ui-monospace,Consolas,monospace;
                       font-size:12px;padding:6px 8px;border:1px solid #d0d7de;border-radius:4px;
                       box-sizing:border-box;resize:vertical}
 .patch-strip .t1-multi{max-height:110px;overflow-y:auto;border:1px solid #d0d7de;border-radius:4px;
                        background:#fff;padding:4px 8px}
 .patch-strip .t1-multi label{display:block;margin:3px 0;color:#24292f;font-size:12px;
                              font-family:ui-monospace,Consolas,monospace}
 .patch-strip input[type=number]{width:100px;padding:4px 6px;border:1px solid #d0d7de;
                                 border-radius:4px;font-size:12px}
 .patch-strip .actions{margin-top:8px}
 .patch-strip button{margin-right:8px;padding:5px 12px;border-radius:6px;border:1px solid #d0d7de;
                     cursor:pointer;background:#fff;font-size:13px}
 .patch-strip button.confirm{background:#0969da;color:#fff;border-color:#0969da}
 .patch-strip button.draft{background:#fff;color:#0969da;border-color:#0969da}
 .patch-strip .draft-note{font-size:12px;color:#9a6700;margin-top:4px}
 .latch button.patch-open{background:#0969da;color:#fff;border-color:#0969da}
</style>
</head>
<body>
<header>
 <strong>FreshLatch 复验单</strong>
 <span class="syn">SYNTHETIC · 合成语料,非真实客户数据</span>
 <span id="pack-badge" class="syn"></span>
 <a class="nav-prepublish" href="/prepublish">发前列表</a>
 <span class="view-toggle" role="group" aria-label="视图密度">
  <button type="button" id="view-craftsman" class="on" onclick="setViewMode(&quot;craftsman&quot;)">职人视图</button>
  <button type="button" id="view-audit" onclick="setViewMode(&quot;audit&quot;)">审计视图</button>
 </span>
 <div id="budget-progress" aria-live="polite" title="护栏预算进度(α-demo)">
  <div class="budget-row">
   <span class="budget-label">步数</span>
   <div class="budget-track"><div id="bar-steps" class="budget-fill"></div></div>
   <span id="budget-steps-text" class="budget-text" title="当前 Lead 会话 / lead_max_steps">0/0</span>
  </div>
  <div class="budget-row">
   <span class="budget-label">检索</span>
   <div class="budget-track"><div id="bar-retrieval" class="budget-fill"></div></div>
   <span id="budget-retrieval-text" class="budget-text" title="本轮 Run / retrieval_budget">0/0</span>
  </div>
 </div>
 <span id="status"></span>
 <span style="flex:1"></span>
 <button class="ghost" type="button" onclick="toggleImportPanel()">主张导入稿</button>
 <button class="ghost" type="button" onclick="importDocket()">导入合成 docket(高级)</button>
 <button class="big" id="btn-run" onclick="runReverify()">开始复验</button>
</header>
<div id="audit-panel" aria-live="polite">
 <b>审计视图</b> · Lead / Critic 工具轨迹与工程角色信息(排障/面试用;不改变作废·续命·闸语义)
 <div id="audit-body" style="margin-top:6px">尚无本轮轨迹。完成复验后此处显示轨迹路径与解码参数。</div>
 <label id="audit-override-filter">
  <input type="checkbox" id="filter-override" onchange="renderClaims()">
  只看 override=true(人对抗落档前机器判定;不是模型变好,不作通过线)
 </label>
</div>
<aside id="how-to-read">
 <strong>如何读</strong>
 <p>如何读本复验单:【身份】卖作废。【机器】fresh/stale/unknown 是机器判定。【人】void 是人的决定,void≠stale。【边界】非法律意见、非自动决策。</p>
</aside>
<div id="disposition-bar" aria-live="polite">
 <span>包结论 · <span id="disp-value" class="disp">—</span></span>
 <span class="meta" id="disp-run-meta"></span>
 <label class="ack-needs-patch" id="ack-needs-patch-wrap" hidden>
  <input type="checkbox" id="ack-needs-patch">
  确认需补丁仍导出
 </label>
 <button type="button" class="export-memo" onclick="exportClientMemo()">导出客户备忘</button>
 <span id="memo-export-msg" role="status"></span>
</div>
<div id="t1-checksums" class="craftsman-soft" aria-live="polite">
 <b>T1 checksum</b>
 <div id="t1-checksums-body">尚无 T1 文档指纹。</div>
</div>
<div id="gate-results" class="craftsman-soft" aria-live="polite">
 <b>逐条闸结果</b>
 <div id="gate-results-body">尚无闸结果。</div>
</div>
<details id="claim-ledger" aria-live="polite">
 <summary>主张台账(作废 / 续命)</summary>
 <p class="hint">只读投影:invalidation_list ∪ latch_log(discard/renew)。renew 不进作废名单。与 patch_events 分缝。写路径仍唯一经 HumanLatch。</p>
 <div id="claim-ledger-body">尚无人审作废/续命记录。</div>
 <button type="button" class="export-md" onclick="exportClaimLedgerMd()">导出台账 Markdown</button>
</details>
<main>
 <section id="claims"><p style="color:#57606a">加载中……</p></section>
 <section id="pane"><p style="color:#57606a">← 点击主张的证据 id,这里显示 T0/T1 原文并高亮锚点段落</p></section>
</main>
<div id="modal" class="modal"><div class="box">
  <p><b>作废确认</b></p>
  <p id="modal-claim" style="color:#57606a"></p>
  <p>作废后重跑不得再绿,确认?</p>
  <button class="ok" onclick="confirmVoid()">确认作废</button>
  <button onclick="closeModal()">取消</button>
</div></div>
<div id="renew-modal" class="modal"><div class="box">
  <p><b>续命确认</b></p>
  <p id="renew-claim" style="color:#57606a"></p>
  <p>续命 = 人主张「该主张在 T1 仍然成立」。必须锚 T1 原文证据(ADR-0006 §4),
     证据从<b>本轮已检索的 T1 块</b>下拉选择,不接受自由填写:</p>
  <select id="renew-evidence"></select>
  <div style="margin-top:12px">
    <button class="renew-ok" onclick="confirmRenew()">确认续命</button>
    <button onclick="previewRenewEvidence()">点回原文核对</button>
    <button onclick="closeRenew()">取消</button>
  </div>
</div></div>
<script>
let STATE = {claims: [], question: "", latch: {thread_id: null, pending: []},
             retrieve_zero_hits: [],
             trajectory: null, retrieval_used: null, decoding: null,
             budget: null, disposition: null, run_status: null,
             active_run_id: null, t1_checksums: [], gate_results: [],
             archived_t1_ids: [], patch_drafts: {}};
let T1SRC = {kind:'none', ready:false, paste_status:'none', synthetic:false,
             network_enabled:false, message:'', cards:[]};
let PASTE_DRAFT_TEXT = '';  // 重绘三卡时保留粘贴框内容
let CURRENT_ANCHOR = null;  // 用户在右栏当前选中的小节(手动选择优先于证据锚点)
let PENDING_DECISIONS = []; // 本轮已选的人审决定(批量提交)
let MODAL_CLAIM = null;
let RENEW_CLAIM = null;
let IMPORT_PANEL_OPEN = false;  // 主张导入稿面板展开态(跨 renderClaims 保留)
let PATCH_OPEN = {};  // #200:主张级改稿条带展开态(跨重绘保留表单)
let PATCH_FORM = {};  // claim_id → {after_text, t1_ids, minutes}
let budgetPoll = null;  // DEM-4:复验中轮询预算
// DEM-6:同一复验单两密度;默认职人;切换只改呈现,不碰 Latch/Gate
let VIEW_MODE = "__VIEW_MODE_DEFAULT__";
const STATUS_RUNNING_CRAFTSMAN = "复验中……";
const STATUS_DONE_CRAFTSMAN = "复验完成";
const STATUS_RUNNING_AUDIT = "复验中(端到端真主链:Lead 循环 + 规则闸)……";
const STATUS_DONE_AUDIT = "复验完成";  // 详情拼在 audit 面板,状态栏保持短句
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
const BADGE = {fresh:["绿 · 仍成立","#1a7f37"],stale:["红 · 已失效","#cf222e"],
               unknown:["灰 · 证据不足","#6e7781"],void:["void · 已作废","#8250df"]};

function renderBudget(b){
  // DEM-4:steps_used/lead_max_steps 与 retrieval_used/retrieval_budget
  if(!b) return;
  STATE.budget = b;
  const su = Number(b.steps_used)||0, sm = Number(b.lead_max_steps)||0;
  const ru = Number(b.retrieval_used)||0, rm = Number(b.retrieval_budget)||0;
  const sp = sm > 0 ? Math.min(100, Math.round(100 * su / sm)) : 0;
  const rp = rm > 0 ? Math.min(100, Math.round(100 * ru / rm)) : 0;
  document.getElementById('budget-steps-text').textContent = su + '/' + sm;
  document.getElementById('budget-retrieval-text').textContent = ru + '/' + rm;
  document.getElementById('bar-steps').style.width = sp + '%';
  document.getElementById('bar-retrieval').style.width = rp + '%';
}
async function pollBudget(){
  try{
    const j = await (await fetch('/api/claims')).json();
    if(j.budget) renderBudget(j.budget);
    // 拉单路径会跑跨轮腐烂;同步主张状态,避免语料变更后卡片仍显示 fresh
    if(j.claims){ STATE.claims = j.claims; renderClaims(); }
  }catch(e){}
}

async function reloadClaimsFromServer(){
  // 打开/渲染复验单的统一拉单口:服务端 rot_claims 真写库后再投影
  const j = await (await fetch('/api/claims')).json();
  if(j.claims) STATE.claims = j.claims;
  if(j.latch) STATE.latch = j.latch;
  if(j.budget) renderBudget(j.budget);
  absorbDetailExtras(j);
  renderClaims();
}

function setViewMode(mode){
  // 只改呈现密度:不提交人审、不触发复验端点
  VIEW_MODE = (mode === "audit") ? "audit" : "craftsman";
  document.getElementById("view-craftsman").classList.toggle("on", VIEW_MODE === "craftsman");
  document.getElementById("view-audit").classList.toggle("on", VIEW_MODE === "audit");
  renderViewChrome();
  renderClaims();  // 切出审计时清掉 override 过滤后的卡片子集,只改呈现
  // 切回职人时收起状态栏工程细节;有本轮结果则按密度重写短状态
  if(STATE.trajectory){
    document.getElementById("status").textContent =
      (VIEW_MODE === "audit")
        ? (STATUS_DONE_AUDIT + " · 见下方 Agent 轨迹")
        : STATUS_DONE_CRAFTSMAN;
  } else if(document.getElementById("status").textContent.indexOf("复验中") === 0){
    // 复验进行中切视图:同步 running 文案密度
    document.getElementById("status").textContent =
      (VIEW_MODE === "audit") ? STATUS_RUNNING_AUDIT : STATUS_RUNNING_CRAFTSMAN;
  }
}
function renderViewChrome(){
  const panel = document.getElementById("audit-panel");
  if(VIEW_MODE === "audit") panel.classList.add("visible");
  else panel.classList.remove("visible");
  const body = document.getElementById("audit-body");
  if(!STATE.trajectory){
    body.innerHTML = "尚无本轮轨迹。完成复验后此处显示 Agent 轨迹路径与 Lead/Critic 工程信息。";
    return;
  }
  let h = '<div>工具轨迹路径:<code>'+esc(String(STATE.trajectory))+'</code></div>';
  if(STATE.retrieval_used != null)
    h += '<div style="margin-top:4px">检索次数(本轮): '+esc(String(STATE.retrieval_used))+'</div>';
  if(STATE.decoding){
    const d = STATE.decoding;
    h += '<div style="margin-top:4px">解码: '+esc(String(d.model||''))
       +' temp='+esc(String(d.temperature))+' '+esc(String(d.recorded_at||''))+'</div>';
  }
  h += '<div style="margin-top:6px;color:#8250df">角色信息仅审计视图可见;'
     + '职人视图成交面只用主张状态与作废/续命/重跑。</div>';
  body.innerHTML = h;
}

async function boot(){
  await fetch('/api/import',{method:'POST'});
  const j = await (await fetch('/api/claims')).json();
  STATE = Object.assign(STATE, j);
  if(!STATE.retrieve_zero_hits) STATE.retrieve_zero_hits = [];
  absorbDetailExtras(j);
  if(j.budget) renderBudget(j.budget);
  await refreshT1Source();
  renderViewChrome();
  renderClaims();
}
async function refreshT1Source(){
  T1SRC = await (await fetch('/api/t1-source')).json();
}
function renderT1Source(){
  // T1 来源三卡(ADR-0016):合法入口全集;粘贴须确认入库;合成标明 synthetic
  // 薄 URL(ADR-0027/#171):白名单增量入口,不进三卡 cards
  const sel = T1SRC.kind || 'none';
  const host = T1SRC.allowed_url_host || 'www.mckinsey.com';
  let h = '<div id="t1-source"><h3>T1 来源三卡</h3>'
        + '<div class="hint">复验前须选定合法 T1 来源。未选定不得假装已有最新事实。</div>'
        + '<div class="cards">'
        + '<div class="card'+(sel==='upload'?' sel':'')+'" id="t1-card-upload">'
        + '<h4>上传 T1 语料包</h4>'
        + '<input type="file" id="t1-upload-input" accept=".md,text/markdown" multiple>'
        + '<button class="primary" onclick="uploadT1()">上传并入库</button></div>'
        + '<div class="card'+(sel==='paste'?' sel':'')+'" id="t1-card-paste">'
        + '<h4>粘贴变更要点</h4>'
        + '<textarea id="t1-paste-draft" aria-label="粘贴变更要点" placeholder="粘贴变更要点(先成草稿)"></textarea>'
        + '<button onclick="savePasteDraft()">保存草稿</button> '
        + '<button class="primary" onclick="confirmPasteIngest()">确认入库</button>'
        + '<div class="hint">未确认不可 retrieve、不可作续命证据</div></div>'
        + '<div class="card'+(sel==='synthetic'?' sel':'')+'" id="t1-card-synthetic">'
        + '<h4>内置合成评测包 <span class="syn-tag">synthetic</span></h4>'
        + '<button class="primary" onclick="selectSynthetic()">选用合成评测包</button></div>'
        + '</div>'
        + '<div class="thin-url" id="t1-thin-url">'
        + '<h4 style="margin:0 0 6px;font-size:13px">薄 URL(白名单)</h4>'
        + '<input type="url" id="t1-url-input" placeholder="https://'+esc(host)+'/..." '
        + 'aria-label="薄 URL 白名单入库">'
        + '<button class="primary" onclick="ingestThinUrl()">抓取并入库</button>'
        + '<div class="hint">仅主机名精确匹配 '+esc(host)
        + '。失败不入库,可回落上方粘贴确认。开放联网插座仍默认关。</div></div>'
        + '<div class="net">联网插座:默认关闭(不进本批主路径)</div>'
        + '<div class="msg" id="t1-msg">'+esc(T1SRC.message||'')+'</div></div>';
  return h;
}
function restorePasteDraftBox(){
  const box = document.getElementById('t1-paste-draft');
  if(box) box.value = PASTE_DRAFT_TEXT;
}
async function uploadT1(){
  const input = document.getElementById('t1-upload-input');
  if(!input || !input.files || !input.files.length){
    document.getElementById('status').textContent = '请先选择要上传的 T1 markdown 文件';
    return;
  }
  const fd = new FormData();
  for(const f of input.files) fd.append('files', f);
  const j = await (await fetch('/api/t1-source/upload',{method:'POST', body:fd})).json();
  if(j.error){ document.getElementById('status').textContent = j.error; return; }
  T1SRC = j; await reloadClaimsFromServer();
  document.getElementById('status').textContent = j.message || 'T1 语料包已入库';
}
async function savePasteDraft(){
  const text = document.getElementById('t1-paste-draft').value;
  PASTE_DRAFT_TEXT = text;
  const j = await (await fetch('/api/t1-source/paste',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({text: text})})).json();
  if(j.error){ document.getElementById('status').textContent = j.error; return; }
  T1SRC = j; renderClaims();
  document.getElementById('status').textContent = j.message || '草稿已保存';
}
async function confirmPasteIngest(){
  // 主路径:可直接点「确认入库」;若框内有文且尚未存草稿,先自动保存再确认
  const box = document.getElementById('t1-paste-draft');
  const text = box ? box.value : '';
  if(text && text.trim() && T1SRC.paste_status !== 'draft'){
    PASTE_DRAFT_TEXT = text;
    const saved = await (await fetch('/api/t1-source/paste',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({text: text})})).json();
    if(saved.error){ document.getElementById('status').textContent = saved.error; return; }
    T1SRC = saved;
  }
  const j = await (await fetch('/api/t1-source/confirm',{method:'POST'})).json();
  if(j.error){ document.getElementById('status').textContent = j.error; return; }
  T1SRC = j; await reloadClaimsFromServer();
  document.getElementById('status').textContent = j.message || '已确认入库';
}
async function selectSynthetic(){
  const j = await (await fetch('/api/t1-source/synthetic',{method:'POST'})).json();
  if(j.error){ document.getElementById('status').textContent = j.error; return; }
  T1SRC = j; await reloadClaimsFromServer();
  document.getElementById('status').textContent = j.message || '已选用合成评测包';
}
async function ingestThinUrl(){
  // ADR-0027:仅白名单 Host;失败四态零写,错误码/短中文上屏,可回落粘贴
  const box = document.getElementById('t1-url-input');
  const url = box ? box.value : '';
  if(!url || !url.trim()){
    document.getElementById('status').textContent = '请填写白名单薄 URL';
    return;
  }
  const r = await fetch('/api/t1-source/url',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({url: url.trim()})});
  const j = await r.json();
  if(!r.ok || j.error){
    const code = j.error_code ? ('['+j.error_code+'] ') : '';
    document.getElementById('status').textContent = code + (j.error || '薄 URL 入库失败');
    return;
  }
  T1SRC = j; await reloadClaimsFromServer();
  document.getElementById('status').textContent = j.message || '薄 URL 已入库';
}
function toggleImportPanel(){
  IMPORT_PANEL_OPEN = !IMPORT_PANEL_OPEN;
  const p = document.getElementById('import-panel');
  if(p) p.classList.toggle('open', IMPORT_PANEL_OPEN);
}
async function importClaimDraft(){
  const text = document.getElementById('claim-import-draft').value;
  const r = await fetch('/api/import/draft',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({text: text})});
  const j = await r.json();
  if(!r.ok){ document.getElementById('status').textContent = j.error; return; }
  PENDING_DECISIONS = [];
  const claims = await (await fetch('/api/claims')).json();
  STATE = Object.assign(STATE, claims);
  IMPORT_PANEL_OPEN = false;
  renderViewChrome();
  renderClaims();
  let msg = '已导入主张导入稿 '+j.imported+' 条';
  if(j.assigned_ids && j.assigned_ids.length)
    msg += ' · 系统分配 id: '+j.assigned_ids.join(', ');
  document.getElementById('status').textContent = msg;
}
async function importDocket(){
  await fetch('/api/import',{method:'POST'});
  PENDING_DECISIONS = [];
  const j = await (await fetch('/api/claims')).json();
  STATE = Object.assign(STATE, j);
  renderViewChrome();
  renderClaims();
  document.getElementById('status').textContent =
    '已导入合成 JSON docket(高级入口) '+j.claims.length+' 条';
}
function pickedAction(cid){
  const d = PENDING_DECISIONS.find(x=>x.claim_id===cid);
  return d ? d.action : null;
}
function renewOptions(cid){
  // 续命证据来源 = 本轮已检索的 T1 块(ADR-0006 §4 下拉选择,非自由文本)
  const c = STATE.claims.find(x=>x.claim_id===cid);
  return ((c && c.t1_evidence_ids) || []).filter(e=>e.endsWith('@T1'));
}
function renewButton(cid){
  // §5.4 + ADR-0006 §6 交互层:无 evidence_id 续命不可用(前端拦截,后端闸兜底)
  if(pickedAction(cid)==='renew') return '<button class="renew picked" disabled>已选:续命(待提交)</button>';
  if(!renewOptions(cid).length)
    return '<button disabled title="本轮无已检索 T1 原文块,续命不可用">续命</button>';
  return '<button class="renew" onclick="event.stopPropagation();openRenew(&quot;'+cid+'&quot;)">续命</button>';
}
function renderZeroHitBanner(){
  // DEM-5:retrieve 空命中 → 强提示「没搜到」;不改写任何主张判定
  const hits = STATE.retrieve_zero_hits || [];
  if(!hits.length) return '';
  let h = '<div id="retrieve-zero-hit" role="alert">'
        + '<b>检索零命中</b> · 本轮有 '+hits.length
        + ' 次 retrieve 返回空结果——这是「没搜到」,不是静默成功。'
        + '<ul>';
  for(const z of hits){
    h += '<li>'+esc(String(z.as_of||''))+' · '+esc(String(z.query||''))+'</li>';
  }
  h += '</ul>'
     + '<div class="note">本提示不改写主张判定,也不冒充判定闸。</div></div>';
  return h;
}
function renderUnknownPathNote(){
  // DEM-5 旁注:unknown 仍须 Lead 显式落档(与 UI 提示解耦)
  return '<div id="retrieve-unknown-note">'
       + '缺口(unknown)仍须 Lead 经 <code>mark_gap</code> / '
       + '<code>reverify_claim(unknown)</code> 显式落档;'
       + 'UI 零命中提示不得自动改写判定。</div>';
}
function renderBanner(){
  const el = document.getElementById('banner-wrap');
  const L = STATE.latch || {};
  if(!L.thread_id){ el.innerHTML=''; return; }
  let h = '<div id="banner"><b>待人工</b> · 本轮复验已跑完,'
        + L.pending.length + ' 条红/黄灯主张待人审(轮次级批量审批)';
  for(const p of L.pending){
    const act = pickedAction(p.claim_id);
    h += '<div class="pend"><b>'+esc(p.claim_id)+'</b> '
       + '<span class="badge" style="color:'+(BADGE[p.status]?BADGE[p.status][1]:'#6e7781')+'">'
       + (BADGE[p.status]?BADGE[p.status][0]:p.status)+'</span> '
       + esc(p.statement);
    if(act==='discard'){
      h += ' <span class="picked">已选:作废(待提交)</span>';
    } else {
      h += ' <button class="void" onclick="openVoidConfirm(&quot;'+p.claim_id+'&quot;)">作废</button>';
    }
    h += ' ' + renewButton(p.claim_id) + '</div>';
  }
  h += '<div style="margin-top:10px">'
     + '<button class="void" onclick="submitDecisions()">提交人审决定('
     + PENDING_DECISIONS.length + ' 项)</button> '
     + '<button onclick="submitDecisions(true)">全部搁置,结束本轮</button></div></div>';
  el.innerHTML = h;
}
function renderPackBadge(){
  const el = document.getElementById('pack-badge');
  if(!el) return;
  const p = STATE.pack || {};
  const bits = [];
  if(p.pack_id) bits.push(p.pack_id);
  if(p.label) bits.push(p.label);
  if(p.synthetic) bits.push('synthetic');
  el.textContent = bits.join(' · ');
}
function renderDispositionBar(){
  // #173:包结论条增量注入既有复验单;职人只看三值,不堆工程词
  const val = document.getElementById('disp-value');
  const meta = document.getElementById('disp-run-meta');
  if(!val || !meta) return;
  const d = STATE.disposition || '—';
  val.textContent = d;
  val.className = 'disp' + (d==='可发'?' ok':(d==='需补丁'?' patch':(d==='勿发'?' block':'')));
  const bits = [];
  if(STATE.run_status) bits.push('Run 状态 '+STATE.run_status);
  if(STATE.active_run_id) bits.push('id '+STATE.active_run_id);
  meta.textContent = bits.join(' · ');
  // #229:仅需补丁时展示 ack 确认(对齐 ack_needs_patch)
  const ackWrap = document.getElementById('ack-needs-patch-wrap');
  if(ackWrap){ ackWrap.hidden = (d !== '需补丁'); }
}
async function exportClientMemo(){
  // #229:UI 导出客户备忘;与 CLI 同闸;deny 不下载文件
  const msg = document.getElementById('memo-export-msg');
  if(msg) msg.textContent = '';
  const ackEl = document.getElementById('ack-needs-patch');
  const ack = !!(ackEl && ackEl.checked);
  const r = await fetch('/api/client-memo/export?ack_needs_patch='+(ack?'true':'false'), {
    method: 'POST'
  });
  if(!r.ok){
    let detail = '拒绝导出';
    try{
      const j = await r.json();
      detail = (j.code||'') + (j.message?(' · '+j.message):'');
    }catch(e){}
    if(msg) msg.textContent = detail;
    return;
  }
  const text = await r.text();
  const blob = new Blob([text], {type: 'text/markdown;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'client-memo.md';
  a.click();
  URL.revokeObjectURL(a.href);
  if(msg) msg.textContent = '';
}
function renderT1Checksums(){
  const box = document.getElementById('t1-checksums');
  const body = document.getElementById('t1-checksums-body');
  if(!box || !body) return;
  // 职人视图保留短列表(可追责);审计视图同数据,不另造栈
  const rows = STATE.t1_checksums || [];
  if(!rows.length){ body.textContent = '尚无 T1 文档指纹。'; return; }
  let h = '<ul style="margin:6px 0 0;padding-left:18px">';
  for(const r of rows){
    h += '<li>'+esc(r.doc_id||'')
       + (r.title?(' · '+esc(r.title)):'')
       + ' · <code>'+esc(r.checksum||'(空)')+'</code></li>';
  }
  h += '</ul>';
  body.innerHTML = h;
}
function renderGateResults(){
  const body = document.getElementById('gate-results-body');
  if(!body) return;
  const rows = STATE.gate_results || [];
  if(!rows.length){ body.textContent = '尚无闸结果。'; return; }
  let h = '<ul style="margin:6px 0 0;padding-left:18px">';
  for(const r of rows){
    h += '<li><b>'+esc(r.claim_id||'')+'</b> · '+esc(r.status||'')
       + (r.gate_rejected?(' · 闸打回 <code>'+esc(r.error_code||'')+'</code>'):' · 闸侧已落档')
       + (r.reason?(' — '+esc(r.reason)):'')
       + '</li>';
  }
  h += '</ul>';
  // 审计视图可链轨迹(既有 audit-panel);此处只挂闸摘要
  if(STATE.trajectory && VIEW_MODE === 'audit'){
    h += '<div style="margin-top:6px">轨迹:<code>'+esc(String(STATE.trajectory))+'</code></div>';
  }
  body.innerHTML = h;
}
function renderClaimLedger(){
  // #228:Run 详情旁路;默认可折叠(<details>);只读展示 discard/renew
  const body = document.getElementById('claim-ledger-body');
  if(!body) return;
  const ledger = STATE.claim_ledger || {};
  const entries = ledger.entries || [];
  const discardIds = ledger.discard_claim_ids || [];
  const renewIds = ledger.renew_claim_ids || [];
  const voidIds = ledger.invalidation_claim_ids || [];
  if(!entries.length && !voidIds.length){
    body.textContent = '尚无人审作废/续命记录。';
    return;
  }
  let h = '<div>作废 claim_id: '
        + (discardIds.length ? discardIds.map(c=>'<code>'+esc(c)+'</code>').join(' ') : '(无)')
        + '</div>';
  h += '<div>续命 claim_id: '
     + (renewIds.length ? renewIds.map(c=>'<code>'+esc(c)+'</code>').join(' ') : '(无)')
     + '</div>';
  h += '<div>作废名单(renew 不在此列): '
     + (voidIds.length ? voidIds.map(c=>'<code>'+esc(c)+'</code>').join(' ') : '(无)')
     + '</div>';
  if(entries.length){
    h += '<ul>';
    for(const e of entries){
      h += '<li><code>'+esc(e.claim_id||'')+'</code> · '+esc(e.label||e.action||'')
         + (e.ts?(' · '+esc(e.ts)):'')
         + (e.evidence_id?(' · evidence <code>'+esc(e.evidence_id)+'</code>'):'')
         + '</li>';
    }
    h += '</ul>';
  }
  body.innerHTML = h;
}
async function exportClaimLedgerMd(){
  // #228:旁路导出 Markdown;只读,不写库
  const r = await fetch('/api/claim-ledger/export.md');
  const text = await r.text();
  const blob = new Blob([text], {type: 'text/markdown;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'claim-ledger.md';
  a.click();
  URL.revokeObjectURL(a.href);
}
function absorbDetailExtras(j){
  if(!j) return;
  if(j.disposition != null) STATE.disposition = j.disposition;
  if(j.run_status != null) STATE.run_status = j.run_status;
  if(j.active_run_id != null) STATE.active_run_id = j.active_run_id;
  if(j.t1_checksums) STATE.t1_checksums = j.t1_checksums;
  if(j.gate_results) STATE.gate_results = j.gate_results;
  if(j.archived_t1_ids) STATE.archived_t1_ids = j.archived_t1_ids;
  if(j.patch_drafts) STATE.patch_drafts = j.patch_drafts;
  if(j.claim_ledger) STATE.claim_ledger = j.claim_ledger;
}
function overrideFilterOn(){
  const box = document.getElementById('filter-override');
  return VIEW_MODE === 'audit' && !!(box && box.checked);
}
function patchFormState(cid){
  // 跨重绘保留表单;若服务端有草案则首次灌入
  if(!PATCH_FORM[cid]){
    const d = (STATE.patch_drafts || {})[cid];
    PATCH_FORM[cid] = {
      after_text: d ? (d.after_text || '') : '',
      t1_ids: d ? (d.t1_ids || []).slice() : [],
      minutes: '0'
    };
  }
  return PATCH_FORM[cid];
}
function isPatchEligible(c){
  // 与后端 is_patch_eligible 同口径:未 discard 的 unknown|stale
  if(c.patch_eligible != null) return !!c.patch_eligible;
  return !c.voided && (c.status==='unknown' || c.status==='stale');
}
function togglePatchStrip(cid){
  PATCH_OPEN[cid] = !PATCH_OPEN[cid];
  patchFormState(cid);
  renderClaims();
}
function readPatchInputs(cid){
  const ta = document.getElementById('patch-after-'+cid);
  const mins = document.getElementById('patch-minutes-'+cid);
  const boxes = document.querySelectorAll('input.patch-t1-'+cid+':checked');
  const form = patchFormState(cid);
  form.after_text = ta ? ta.value : form.after_text;
  form.minutes = mins ? mins.value : form.minutes;
  form.t1_ids = Array.from(boxes).map(b=>b.value);
  return form;
}
function renderPatchOpenButton(c){
  // #200:仅可提案主张显示「改稿」入口(与 discard/renew 并存)
  if(!isPatchEligible(c)) return '';
  const cid = c.claim_id;
  const open = !!PATCH_OPEN[cid];
  return '<button class="patch-open" type="button" '
       + 'onclick="event.stopPropagation();togglePatchStrip(&quot;'+cid+'&quot;)">'
       + (open?'收起改稿':'改稿')+'</button>';
}
function renderPatchStrip(c){
  // #200:职人用语改稿/确认/再验;挂在主张卡内增量区;表单闭环(无臂开关)
  if(!isPatchEligible(c) || !PATCH_OPEN[c.claim_id]) return '';
  const cid = c.claim_id;
  const form = patchFormState(cid);
  const archived = STATE.archived_t1_ids || [];
  const draft = (STATE.patch_drafts || {})[cid];
  let h = '<div class="patch-strip" id="patch-strip-'+cid+'" onclick="event.stopPropagation()">'
        + '<div class="patch-title">改稿 · 确认 · 再验</div>'
        + '<p class="patch-hint">须勾选本 Run 已入库 T1;确认后覆盖主张正文并记账(attested)。'
        + '不作废/续命语义;无臂开关。</p>'
        + '<label for="patch-after-'+cid+'">改稿正文(after_text)</label>'
        + '<textarea id="patch-after-'+cid+'" aria-label="改稿正文">'
        + esc(form.after_text||'')+'</textarea>'
        + '<label>本 Run 已入库 T1(多选)</label>'
        + '<div class="t1-multi">';
  if(!archived.length){
    h += '<div style="color:#57606a;font-size:12px">尚无已入库 T1 evidence_id。</div>';
  } else {
    for(const eid of archived){
      const checked = (form.t1_ids||[]).indexOf(eid)>=0 ? ' checked' : '';
      h += '<label><input type="checkbox" class="patch-t1-'+cid+'" value="'+esc(eid)+'"'
         + checked+'> '+esc(eid)+'</label>';
    }
  }
  h += '</div>'
     + '<label for="patch-minutes-'+cid+'">工时 minutes</label>'
     + '<input type="number" id="patch-minutes-'+cid+'" min="0" step="0.1" '
     + 'value="'+esc(String(form.minutes||'0'))+'">'
     + '<div class="actions">'
     + '<button type="button" class="draft" onclick="proposePatchDraft(&quot;'+cid+'&quot;)">暂存草案</button>'
     + '<button type="button" class="confirm" onclick="confirmPatchClaim(&quot;'+cid+'&quot;)">确认改稿</button>'
     + '<button type="button" onclick="discardPatchDraft(&quot;'+cid+'&quot;)">丢弃草案</button>'
     + '</div>';
  if(draft){
    h += '<div class="draft-note">已有暂存草案 · '+esc(draft.proposed_at||'')+'</div>';
  }
  h += '</div>';
  return h;
}
async function proposePatchDraft(cid){
  const form = readPatchInputs(cid);
  const r = await fetch('/api/patch/propose',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({claim_id: cid, after_text: form.after_text,
                          t1_ids: form.t1_ids})});
  const j = await r.json();
  if(!r.ok || j.ok === false){
    document.getElementById('status').textContent =
      (j.error_code?('['+j.error_code+'] '):'') + (j.detail || j.error || '暂存草案失败');
    return;
  }
  if(j.claims) STATE.claims = j.claims;
  absorbDetailExtras(j);
  renderClaims();
  document.getElementById('status').textContent = '改稿草案已暂存(未改正文、未写正式账本): '+cid;
}
async function confirmPatchClaim(cid){
  const form = readPatchInputs(cid);
  const minutes = parseFloat(form.minutes);
  const r = await fetch('/api/patch/confirm',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({claim_id: cid, after_text: form.after_text,
                          t1_ids: form.t1_ids,
                          minutes: isNaN(minutes)?0:minutes})});
  const j = await r.json();
  if(!r.ok || j.ok === false){
    document.getElementById('status').textContent =
      (j.error_code?('['+j.error_code+'] '):'') + (j.detail || j.error || '确认改稿失败');
    return;
  }
  if(j.claims) STATE.claims = j.claims;
  absorbDetailExtras(j);
  delete PATCH_FORM[cid];
  PATCH_OPEN[cid] = false;
  renderClaims();
  let msg = '改稿已确认 · '+cid;
  if(j.disposition) msg += ' · 包结论 '+j.disposition;
  if(j.reverify_requested) msg += ' · 再验已请求';
  document.getElementById('status').textContent = msg;
}
async function discardPatchDraft(cid){
  readPatchInputs(cid);
  const r = await fetch('/api/patch/discard-draft',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({claim_id: cid})});
  const j = await r.json();
  if(!r.ok){
    document.getElementById('status').textContent = j.error || '丢弃草案失败';
    return;
  }
  if(j.claims) STATE.claims = j.claims;
  absorbDetailExtras(j);
  delete PATCH_FORM[cid];
  renderClaims();
  document.getElementById('status').textContent = '已丢弃改稿草案: '+cid;
}
function renderClaims(){
  renderPackBadge();
  renderDispositionBar();
  renderT1Checksums();
  renderGateResults();
  renderClaimLedger();
  const el = document.getElementById('claims');
  if(!el) return;
  let h = '<div id="import-panel" class="'+(IMPORT_PANEL_OPEN?'open':'')+'">'
        + '<b>主张导入稿</b>'
        + '<div class="hint">每条以 <code>## claim_id</code> 起头、其后正文一段;'
        + '缺 id 时系统分配 <code>c-import-N</code>。只导入已签发主张,不做散文抽取或模型切分。</div>'
        + '<textarea id="claim-import-draft" '
        + 'aria-label="主张导入稿"></textarea>'
        + '<div style="margin-top:8px">'
        + '<button type="button" onclick="importClaimDraft()">导入主张导入稿</button> '
        + '<button type="button" onclick="toggleImportPanel()">收起</button>'
        + '</div></div>';
  h += renderT1Source();
  h += renderZeroHitBanner();
  h += renderUnknownPathNote();
  h += '<div id="banner-wrap"></div>';
  h += '<h3 style="margin:4px 0 10px">主张复验单 <span style="font-weight:400;font-size:13px;color:#57606a">'
        + esc(STATE.question||'') + '</span></h3>';
  for(const c of STATE.claims){
    if(overrideFilterOn() && !(c.timeline||[]).some(t => t.override === true)) continue;
    const [label,color] = BADGE[c.status] || BADGE.unknown;
    h += '<div class="claim'+(c.voided?' voided':'')+'" id="c-'+c.claim_id+'" style="border-left-color:'+color+'" '
       + 'onclick="pickClaim(&quot;'+c.claim_id+'&quot;)">'
       + '<b>'+c.claim_id+'</b><span class="badge" style="color:'+color+'">'+label+'</span>';
    if(c.voided) h += '<span class="badge" style="color:#8250df">'+BADGE.void[0]
                    + (c.voided_at?(' · '+esc(c.voided_at)):'') + '</span>';
    if(c.last_confirmed_at) h += '<span class="badge" style="color:#1a7f37">续命 · '
                    + esc(c.last_confirmed_at)+'</span>';
    h += '<div>'+esc(c.statement)+'</div>';
    if(c.reason) h += '<div class="reason">'+esc(c.reason)+'</div>';
    h += '<div class="ev">';
    for(const e of c.t0_evidence_ids||[]) {
      const bare=(e.split('@')[0]||'').split('#'); const asOf=e.split('@')[1]||'T0';
      h += '<a onclick="event.stopPropagation();showSource(&quot;'+bare[0]+'&quot;,&quot;'+bare[1]+'&quot;,&quot;'+asOf+'&quot;)">'+esc(e)+'</a>';
    }
    for(const e of c.t1_evidence_ids||[]) {
      const bare=(e.split('@')[0]||'').split('#'); const asOf=e.split('@')[1]||'T1';
      h += '<a onclick="event.stopPropagation();showSource(&quot;'+bare[0]+'&quot;,&quot;'+bare[1]+'&quot;,&quot;'+asOf+'&quot;)">'+esc(e)+'</a>';
    }
    h += '</div>';
    h += '<div class="latch" style="margin-top:6px">';
    if(c.voided){
      h += '<button class="rerun" onclick="event.stopPropagation();rerunClaim(&quot;'+c.claim_id+'&quot;)">重跑作废主张</button>';
    } else if(c.status==='stale' || c.status==='unknown'){
      h += renewButton(c.claim_id);  // 续命只对人审范围内的红/黄灯主张(fresh 无需续命)
      h += ' ' + renderPatchOpenButton(c);  // #200:改稿入口与 discard/renew 并存
    }
    h += '</div>';
    h += renderPatchStrip(c);  // 条带挂在 latch 区外,仍在主张卡内
    if(c.timeline && c.timeline.length){
      h += '<div class="timeline">';
      for(const t of c.timeline){
        h += '<div>· '+esc(t.ts)+' '+esc(t.label)
           + (t.override===true?' · override':'')
           + (t.evidence_id?(' · 依据 <code>'+esc(t.evidence_id)+'</code>'):'')
           + (t.note?(' — '+esc(t.note)):'')
           + (t.thread_id?(' <code>'+esc(t.thread_id)+'</code>'):'')+'</div>';
      }
      h += '</div>';
    }
    h += '</div>';  // 闭合 .claim 卡片(T9 加时间线时丢了这行,卡片互相嵌套堆积)
  }
  el.innerHTML = h;
  restorePasteDraftBox();
  renderBanner();
}
function pickClaim(cid){
  document.querySelectorAll('.claim').forEach(e=>e.classList.remove('sel'));
  document.getElementById('c-'+cid)?.classList.add('sel');
}
function pickClause(anchor){
  document.querySelectorAll('#pane .clause').forEach(e=>e.classList.remove('hit'));
  document.getElementById('anchor-'+anchor)?.classList.add('hit');
  CURRENT_ANCHOR = anchor;
}
async function showSource(docId, anchor, asOf){
  const j = await (await fetch('/api/source/'+encodeURIComponent(docId)+'?as_of='+(asOf||'T1'))).json();
  if(j.error){ document.getElementById('pane').innerHTML = '<p>'+esc(j.error)+'</p>'; return; }
  let h = '<h3>'+esc(j.title)+' <span class="asof">'+j.as_of+'</span> <span class="asof">'+esc(j.source_type)+'</span></h3>';
  h += '<div class="tabs" style="margin-bottom:8px">'
     + '<button class="'+((asOf||'T1')==='T0'?'on':'')+'" onclick="showSource(&quot;'+docId+'&quot;,CURRENT_ANCHOR,&quot;T0&quot;)">T0 签发时</button>'
     + '<button class="'+((asOf||'T1')==='T1'?'on':'')+'" onclick="showSource(&quot;'+docId+'&quot;,CURRENT_ANCHOR,&quot;T1&quot;)">T1 复验时刻</button></div>';
  h += '<div class="doc">';
  for(const s of j.sections){
    const hit = s.anchor === anchor;
    h += '<div class="clause'+(hit?' hit':'')+'" id="anchor-'+s.anchor+'" onclick="pickClause(&quot;'+s.anchor+'&quot;)">'
       + '<code>## '+esc(s.anchor)+'</code>' + esc(s.text.replace('## '+s.anchor,'')) + '</div>';
  }
  h += '</div>';
  CURRENT_ANCHOR = anchor;
  document.getElementById('pane').innerHTML = h;
  const target = document.getElementById('anchor-'+anchor);
  if(target) target.scrollIntoView({behavior:'smooth', block:'center'});
}
async function runReverify(){
  const btn = document.getElementById('btn-run');
  btn.disabled = true;
  // DEM-6:职人默认成交面不用 Lead/轨迹作状态文案;审计视图才露工程角色
  document.getElementById('status').textContent =
    (VIEW_MODE === "audit") ? STATUS_RUNNING_AUDIT : STATUS_RUNNING_CRAFTSMAN;
  if(budgetPoll) clearInterval(budgetPoll);
  budgetPoll = setInterval(pollBudget, 400);
  try{
    const j = await (await fetch('/api/reverify',{method:'POST'})).json();
    if(j.error){ document.getElementById('status').textContent = j.error; return; }
    STATE.claims = j.claims; STATE.latch = j.latch; PENDING_DECISIONS = [];
    STATE.retrieve_zero_hits = j.retrieve_zero_hits || [];
    STATE.trajectory = j.trajectory; STATE.retrieval_used = j.retrieval_used;
    STATE.decoding = j.decoding;
    absorbDetailExtras(j);
    if(j.budget) renderBudget(j.budget);
    renderViewChrome();
    renderClaims();
    const zc = (STATE.retrieve_zero_hits||[]).length;
    const b = j.budget || STATE.budget || {};
    if(VIEW_MODE === "audit"){
      document.getElementById('status').textContent =
        STATUS_DONE_AUDIT + ' · 步数 '+b.steps_used+'/'+b.lead_max_steps
        +' · 检索 '+b.retrieval_used+'/'+b.retrieval_budget
        +(zc?(' · 零命中 '+zc+' 次'):'')
        +' · 见下方 Agent 轨迹';
    } else {
      document.getElementById('status').textContent =
        STATUS_DONE_CRAFTSMAN
        +' · 步数 '+b.steps_used+'/'+b.lead_max_steps
        +' · 检索 '+b.retrieval_used+'/'+b.retrieval_budget
        +(zc?(' · 零命中 '+zc+' 次'):'');
    }
  } finally {
    if(budgetPoll){ clearInterval(budgetPoll); budgetPoll = null; }
    btn.disabled = false;
  }
}
function openVoidConfirm(cid){
  MODAL_CLAIM = cid;
  const c = STATE.claims.find(x=>x.claim_id===cid);
  document.getElementById('modal-claim').textContent = cid + ': ' + (c?c.statement:'');
  document.getElementById('modal').style.display = 'block';
}
function closeModal(){ document.getElementById('modal').style.display = 'none'; MODAL_CLAIM = null; }
function confirmVoid(){  // 双重确认弹窗的第二重(§5.3:点作废 → 弹窗「作废后重跑不得再绿,确认?」)
  if(MODAL_CLAIM){
    PENDING_DECISIONS = PENDING_DECISIONS.filter(x=>x.claim_id!==MODAL_CLAIM);
    PENDING_DECISIONS.push({claim_id: MODAL_CLAIM, action: 'discard'});
  }
  closeModal(); renderBanner();
}
function openRenew(cid){
  const opts = renewOptions(cid);
  if(!opts.length) return;  // 前端拦截:无 T1 证据不开放(后端闸兜底,§5.4)
  RENEW_CLAIM = cid;
  const c = STATE.claims.find(x=>x.claim_id===cid);
  document.getElementById('renew-claim').textContent = cid + ': ' + (c?c.statement:'');
  document.getElementById('renew-evidence').innerHTML =
    opts.map(e=>'<option value="'+esc(e)+'">'+esc(e)+'</option>').join('');
  document.getElementById('renew-modal').style.display = 'block';
}
function closeRenew(){ document.getElementById('renew-modal').style.display='none'; RENEW_CLAIM=null; }
function previewRenewEvidence(){  // 续命证据 id 必须可点回(#23 红线:不得凭印象续命)
  const eid = document.getElementById('renew-evidence').value;
  const bare = (eid.split('@')[0]||'').split('#');
  showSource(bare[0], bare[1], eid.split('@')[1]||'T1');
}
function confirmRenew(){
  if(RENEW_CLAIM){
    PENDING_DECISIONS = PENDING_DECISIONS.filter(x=>x.claim_id!==RENEW_CLAIM);
    PENDING_DECISIONS.push({claim_id: RENEW_CLAIM, action:'renew',
                            evidence_id: document.getElementById('renew-evidence').value});
  }
  closeRenew(); renderClaims();
}
async function submitDecisions(settleAll){
  const decisions = settleAll ? [] : PENDING_DECISIONS;
  const j = await (await fetch('/api/latch/decide',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({thread_id: STATE.latch.thread_id, decisions: decisions})})).json();
  if(j.error){ document.getElementById('status').textContent = j.error; return; }
  STATE.claims = j.claims; STATE.latch = j.latch; PENDING_DECISIONS = [];
  absorbDetailExtras(j);
  renderClaims();
  // 单条被闸打回不拖垮其余(apply_decisions 语义);打回项带 error_code 如实上屏
  const bad = (j.results||[]).filter(r=>!r.ok);
  document.getElementById('status').textContent = bad.length
    ? '部分人审决定被规则闸打回(该条零写): '+bad.map(r=>r.claim_id+' → '+r.error_code).join('; ')
    : '人审决定已落档(写路径唯一:invalidation_list + latch_log)';
}
async function rerunClaim(cid){
  document.getElementById('status').textContent = '重跑中(新 thread 单主张迷你复验:'+cid +')……';
  const j = await (await fetch('/api/latch/rerun',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({claim_id: cid})})).json();
  if(j.error){ document.getElementById('status').textContent = j.error; return; }
  const idx = STATE.claims.findIndex(x=>x.claim_id===cid);
  if(idx>=0) STATE.claims[idx] = j.claim;
  renderClaims();
  document.getElementById('status').textContent = '重跑完成:'+j.entry.label
    + (j.entry.note?(' — '+j.entry.note):'') + ' · thread '+j.entry.thread_id;
}
boot();
</script>
</body></html>"""


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
PREPUBLISH_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>FreshLatch 发前列表</title>
<style>
 body{font-family:system-ui,"Microsoft YaHei",sans-serif;margin:0;background:#f6f8fa;color:#24292f}
 header{background:#0a2540;color:#fff;padding:14px 24px;display:flex;gap:16px;align-items:center}
 header a{color:#fff;font-size:13px}
 main{max-width:960px;margin:24px auto;padding:0 16px}
 h1{font-size:22px;margin:0 0 8px}
 .hint{font-size:13px;color:#57606a;margin-bottom:16px}
 table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d0d7de;border-radius:6px;overflow:hidden}
 th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #d0d7de;font-size:14px}
 th{background:#f6f8fa;font-weight:600;color:#57606a}
 tr:last-child td{border-bottom:0}
 .disp{font-weight:700}
 .disp.ok{color:#1a7f37}.disp.patch{color:#9a6700}.disp.block{color:#cf222e}
 .empty{padding:24px;color:#57606a;background:#fff;border:1px solid #d0d7de;border-radius:6px}
 a.open{color:#0969da;text-decoration:none}
 a.open:hover{text-decoration:underline}
 .syn{background:#b45309;color:#fff;font-size:12px;padding:2px 10px;border-radius:10px}
</style>
</head>
<body>
<header>
 <strong>FreshLatch 发前列表</strong>
 <span class="syn">SYNTHETIC</span>
 <span style="flex:1"></span>
 <a href="/">打开复验单详情</a>
</header>
<main>
 <h1>发前 Run</h1>
 <p class="hint">列表壳只投影标题/来源、包结论、更新时间、Run 状态。点「打开」进入既有复验单(增量包结论条);不另造第三套详情 UI。</p>
 <div id="list"><p class="empty">加载中……</p></div>
</main>
<script>
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function dispCls(d){return d==='可发'?'ok':(d==='需补丁'?'patch':(d==='勿发'?'block':''))}
async function loadList(){
  const j = await (await fetch('/api/prepublish/runs')).json();
  const runs = j.runs || [];
  const el = document.getElementById('list');
  if(!runs.length){
    el.innerHTML = '<p class="empty">暂无发前 Run。请先在<a href="/">复验单</a>导入主张并复验。</p>';
    return;
  }
  let h = '<table><thead><tr>'
        + '<th>标题 / 来源</th><th>包结论</th><th>更新时间</th><th>Run 状态</th><th></th>'
        + '</tr></thead><tbody>';
  for(const r of runs){
    h += '<tr>'
       + '<td><b>'+esc(r.title||'')+'</b><div style="font-size:12px;color:#57606a">'
       + esc(r.source||'')+'</div></td>'
       + '<td><span class="disp '+dispCls(r.disposition)+'">'+esc(r.disposition||'')+'</span></td>'
       + '<td>'+esc(r.updated_at||'')+'</td>'
       + '<td>'+esc(r.status||'')+'</td>'
       + '<td><a class="open" href="/">打开详情</a></td>'
       + '</tr>';
  }
  h += '</tbody></table>';
  el.innerHTML = h;
}
loadList();
</script>
</body></html>"""


@app.get("/prepublish", response_class=HTMLResponse)
def prepublish_index() -> str:
    """发前列表页(#173):mission_control 列表壳改编,业务字段换 Run/disposition。"""
    return PREPUBLISH_HTML


if __name__ == "__main__":
    import uvicorn

    # #230:入站 check 默认仅本机回环;可用 FRESHLATCH_BIND_HOST 覆盖,禁止把 0.0.0.0 无鉴权当 Done
    _bind = (os.environ.get(HOOK_BIND_HOST_ENV) or "").strip() or HOOK_DEFAULT_BIND_HOST
    uvicorn.run(app, host=_bind, port=8000)
