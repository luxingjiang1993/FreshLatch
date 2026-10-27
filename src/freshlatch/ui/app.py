"""复验单 UI 组装壳(#754/#758):FastAPI() + include_router + 会话助手再导出。

形态红线(§5.1 / #663):主界面是复验单,不是聊天框;主 CTA =「一键样例」。
HumanLatch 写路径唯一 = gates/human_latch.py;本模块不做 create_app / 多用户分桶。
业务路由见 routes_*.py;可变容器真相源 = session_state;投影 = projections。
"""

from __future__ import annotations

import logging
import os
import uuid

from fastapi import FastAPI

from freshlatch.api_errors import install_error_handlers  # noqa: E402
from freshlatch.models import Claim  # noqa: E402
from freshlatch.latch import HumanLatch  # noqa: E402
from freshlatch.prepublish import derive_run_status  # noqa: E402
from freshlatch.runner import RunContext  # noqa: E402  # 单测 appmod.RunContext
from freshlatch.runner import Runner  # noqa: E402  # 单测 monkeypatch appmod.Runner
from freshlatch.store.checksum import make_checksum_fn  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402
from freshlatch.t1_source import T1SourceSession  # noqa: E402

from freshlatch.ui import session_state as ss  # noqa: E402
from freshlatch.ui.projections import (  # noqa: E402
    RUN_SNAPSHOT_VERSION,
    _RESET_LEDGER_NOTE,
    _CRAFTSMAN_BADGES_TOKEN,
    _audit_for_ui,
    _bind_run_checksums,
    _budget_from_ctx,
    _claim_ledger_for_ui,
    _claim_to_dict,
    _claims_for_ui,
    _current_budget,
    _current_t1_checksum_map,
    _detail_extras,
    _one_claim_for_ui,
    _pack_payload,
    _patch_drafts_payload,
    _patch_run_id,
    _read_run_snapshot,
    _render_craftsman_badges,
    _run_checksum_fresh,
    _run_metrics,
    _source_label,
    _ui_badge_rows,
    _write_run_snapshot,
)

# 同对象再导出(dict/锁/注册表);单测过渡期仍可 appmod._state
_PATCH_EVENTS_DIR = ss._PATCH_EVENTS_DIR
_PATCH_DRAFTS = ss._PATCH_DRAFTS
_RUN_TASK_LOCK = ss._RUN_TASK_LOCK
_reset_run_task = ss._reset_run_task
_new_run_task = ss._new_run_task
REPO_ROOT = ss.REPO_ROOT
EMPTY_LATCH = ss.EMPTY_LATCH
EMPTY_BUDGET = ss.EMPTY_BUDGET
_state = ss._state
_prepublish = ss._prepublish
_WEIGHT_DOWNLOAD_TIMEOUT_S = ss._WEIGHT_DOWNLOAD_TIMEOUT_S
_WEIGHT_DOWNLOAD_LOCK = ss._WEIGHT_DOWNLOAD_LOCK
_WEIGHT_DOWNLOAD_JOB = ss._WEIGHT_DOWNLOAD_JOB
_run_weight_download_job = ss._run_weight_download_job
_weight_download_status = ss._weight_download_status

BADGE = {
    "fresh": ("有效 · 仍成立", "#1a7f37"),
    "stale": ("失效", "#cf222e"),
    "unknown": ("灰 · 证据不足", "#6e7781"),
    "void": ("void · 已作废", "#8250df"),
}
MAIN_BUTTON_TEXT = "一键样例"
SYN_BADGE_FULL_TEXT = "SYNTHETIC · 合成语料,非真实客户数据"
SYN_BADGE_SHORT_TEXT = "当前为演示合成包"
VIEW_MODE_DEFAULT = "craftsman"
_VIEW_MODE_TOKEN = "__VIEW_MODE_DEFAULT__"
_AUDIT_BODY_TOKEN = "__AUDIT_BODY__"

app = FastAPI(title="FreshLatch 复验单")
install_error_handlers(app, log_prefix="ui")
logger = logging.getLogger(__name__)


def _sync_pack_aliases() -> None:
    """把 ss 上的 pack 路径别名同步到本模块,兼容 monkeypatch(appmod.CORPUS)。"""
    global CORPUS, DEMO_DOCKET, CHECKPOINTS, ACTIVE_PACK, _PATCH_EVENTS_DIR
    CORPUS = ss.CORPUS
    DEMO_DOCKET = ss.DEMO_DOCKET
    CHECKPOINTS = ss.CHECKPOINTS
    ACTIVE_PACK = ss.ACTIVE_PACK
    _PATCH_EVENTS_DIR = ss._PATCH_EVENTS_DIR


def bind_active_pack(pack_id: str | None = None):
    """把 UI 路径钉到 active_pack 解析结果。显式 pack_id 供测试切换,不改闸。"""
    pack = ss.bind_active_pack(pack_id)
    _sync_pack_aliases()
    return pack


_sync_pack_aliases()


def _warmup_local_weights() -> None:
    """下载并预热两份本地权重;单测 monkeypatch 本函数即可拦住真实下载。"""
    ss._warmup_local_weights_impl()


def _store() -> SQLiteStore:
    from freshlatch.store.local_embed import attach_local_embedder

    store = SQLiteStore(ACTIVE_PACK.sqlite)
    attach_local_embedder(store)
    return store


def _t1_session() -> T1SourceSession:
    """进程内 T1 来源三卡会话;测试可通过 _reset_t1_source 换店。"""
    if ss._t1 is None:
        ss._t1 = T1SourceSession(_store(), corpus_root=CORPUS)
    return ss._t1


def _reset_t1_source(store: SQLiteStore | None = None) -> T1SourceSession:
    """测试/重启入口:清空三卡状态并绑到给定 store。"""
    ss._t1 = T1SourceSession(store or _store(), corpus_root=CORPUS)
    return ss._t1


def _latch() -> HumanLatch:
    return HumanLatch(_store(), CHECKPOINTS, mode="online",
                      checksum_fn=make_checksum_fn(CORPUS))


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


def _restore_run_snapshot(snap: dict) -> None:
    """进程重启后从 snapshot 恢复判定面,不洗成 demo。"""
    _state["claims"] = [Claim(**c) for c in (snap.get("claims") or [])]
    _state["question"] = snap.get("question") or ""
    _state["latch"] = snap.get("latch") or dict(EMPTY_LATCH)
    _state["trajectory"] = snap.get("trajectory")
    _state["active_run_id"] = snap.get("active_run_id")
    _state["retrieve_zero_hits"] = list(snap.get("retrieve_zero_hits") or [])
    _state["budget"] = snap.get("budget") or dict(EMPTY_BUDGET)
    _state["bound_t1_checksums"] = dict(snap.get("bound_t1_checksums") or {})
    _state["token_usage"] = snap.get("token_usage")
    if _state["active_run_id"]:
        _sync_prepublish(new_run=False)


def _active_run_conflict():
    """I-01(#678):非空 active_run 时 import 硬 409。"""
    from fastapi.responses import JSONResponse

    if not _state.get("active_run_id"):
        return None
    if not _state.get("claims") and not (_state.get("latch") or {}).get("pending"):
        return None
    return JSONResponse({
        "error": "当前复验单已绑定非空 Run,导入会覆盖判定面,已阻止",
        "code": "ACTIVE_RUN_CONFLICT",
        "active_run_id": _state.get("active_run_id"),
        "reset_hint": "请先走高级「重置」(POST /api/session/reset)确认洗态后再导入",
    }, status_code=409)


def _clear_live_sheet() -> None:
    """显式重置:只清当前复验单。历史发前行留在注册表里。"""
    _state["claims"] = []
    _state["question"] = ""
    _state["latch"] = dict(EMPTY_LATCH)
    _state["trajectory"] = None
    _state["active_run_id"] = None
    _state["retrieve_zero_hits"] = []
    _state["budget"] = dict(EMPTY_BUDGET)
    _state["bound_t1_checksums"] = {}
    _state["token_usage"] = None
    _state["run_ctx"] = None
    _prepublish.active_run_id = None
    _reset_run_task()


# ---------------------------------------------------------------------------
# 路由组装(#756/#757/#758):路径字符串不变;契约零变更
# ---------------------------------------------------------------------------
from freshlatch.ui.routes_t1 import (  # noqa: E402
    DraftImportRequest,
    PasteDraftRequest,
    ThinUrlRequest,
    router as routes_t1,
)
from freshlatch.ui.routes_reverify import (  # noqa: E402
    ReverifyRequest,
    _run_reverify_task,
    router as routes_reverify,
)
from freshlatch.ui.routes_latch import (  # noqa: E402
    DecideRequest,
    RerunRequest,
    router as routes_latch,
)
from freshlatch.ui.routes_patch import (  # noqa: E402
    ConfirmPatchRequest,
    DiscardPatchDraftRequest,
    ProposePatchRequest,
    _confirm_patch_reverify,
    router as routes_patch,
)
from freshlatch.publish_hook import evaluate_publish_hook  # noqa: E402
from freshlatch.ui.routes_publish import (  # noqa: E402
    HOOK_HINTS,
    PublishHookCheckRequest,
    _hook_token_denied,
    hook_error_body,
    router as routes_publish,
)
from freshlatch.ui.routes_sheet import (  # noqa: E402
    HTML_PAGE,
    PREPUBLISH_HTML,
    _format_audit_score,
    _patch_visibility_html,
    _render_audit_body,
    _render_claim_spans,
    _span_link,
    router as routes_sheet,
)

app.include_router(routes_t1)
app.include_router(routes_reverify)
app.include_router(routes_latch)
app.include_router(routes_patch)
app.include_router(routes_publish)
app.include_router(routes_sheet)


if __name__ == "__main__":
    import uvicorn

    from freshlatch.publish_hook import HOOK_BIND_HOST_ENV, HOOK_DEFAULT_BIND_HOST
    from freshlatch.ui.weight_precheck import warn_if_fastembed_cache_path_unset

    warn_if_fastembed_cache_path_unset()
    _bind = (os.environ.get(HOOK_BIND_HOST_ENV) or "").strip() or HOOK_DEFAULT_BIND_HOST
    uvicorn.run(app, host=_bind, port=8000)
