"""UI 会话可变容器真相源(#755 UI-SPLIT-T1)。

进程内单桶:`_state` / `_RUN_TASK*` / `_WEIGHT_DOWNLOAD_*` / pack bind / 补丁暂存。
路由与投影助手一律 `from freshlatch.ui import session_state as ss` 读这里;
单测 monkeypatch 可变容器请改本模块(或同对象再导出)。
不做 create_app / 多用户分桶。
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

from freshlatch.evidence_bound import PatchDraftStore
from freshlatch.guardrails import Guardrails
from freshlatch.packs import PackPaths, resolve_pack
from freshlatch.prepublish import PrepublishRegistry
from freshlatch.t1_source import T1SourceSession

# 测试可 monkeypatch 指向 tmp;生产默认 None → data/patch_events/
_PATCH_EVENTS_DIR = None
# #200:Evidence-bound 草案暂存(按 Run 隔离;未 confirm 不改正文/不写正式账本)
_PATCH_DRAFTS = PatchDraftStore()

# I-10(#696):异步复验任务(整轮唯一;MVP 单并发,重入由 _state["running"] 挡)。
_RUN_TASK_LOCK = threading.Lock()
_RUN_TASK: dict | None = None


def _reset_run_task() -> None:
    """测试/洗态入口:退役当前任务记录(不打断已在跑的后台线程本身)。"""
    global _RUN_TASK
    with _RUN_TASK_LOCK:
        _RUN_TASK = None


def _new_run_task(run_id: str, *, total: int, accept_bm25: bool) -> None:
    """登记整轮异步任务;run_id 与 Phase 0 active_run_id 同线(不另开身份)。"""
    global _RUN_TASK
    with _RUN_TASK_LOCK:
        _RUN_TASK = {
            "run_id": run_id,
            "status": "running",
            "done": 0,
            "total": total,
            "current_claim_id": None,
            "cancel_event": threading.Event(),
            "accept_bm25": accept_bm25,
            "result": None,
            "error": None,
        }


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CORPUS = REPO_ROOT / "data" / "corpus"
DEMO_DOCKET = REPO_ROOT / "data" / "t0_docket.json"
CHECKPOINTS = REPO_ROOT / "data" / "checkpoints.db"

EMPTY_LATCH = {"thread_id": None, "pending": []}
_G = Guardrails()
EMPTY_BUDGET = {
    "steps_used": 0,
    "lead_max_steps": _G.lead_max_steps,
    "retrieval_used": 0,
    "retrieval_budget": _G.retrieval_budget,
}
del _G

_state: dict = {
    "claims": [],
    "question": "",
    "trajectory": None,
    "running": False,
    "latch": dict(EMPTY_LATCH),
    "budget": dict(EMPTY_BUDGET),
    "run_ctx": None,
    "retrieve_zero_hits": [],
    "active_run_id": None,
    "bound_t1_checksums": {},
    "token_usage": None,
}
_prepublish = PrepublishRegistry()
_t1: T1SourceSession | None = None
ACTIVE_PACK: PackPaths

_WEIGHT_DOWNLOAD_TIMEOUT_S = 1800.0
_WEIGHT_DOWNLOAD_LOCK = threading.Lock()
_WEIGHT_DOWNLOAD_JOB: dict = {
    "state": "idle",
    "error": None,
    "started_at": None,
    "started_monotonic": None,
}


def _warmup_local_weights_impl() -> None:
    """真实预热实现;app._warmup_local_weights 可被单测替换。"""
    from freshlatch.store.local_embed import embed_texts_local
    from freshlatch.store.neural_rerank import warmup_neural_rerank

    embed_texts_local(["预热"])
    warmup_neural_rerank()


def _run_weight_download_job() -> None:
    # 经 app 取名,单测 monkeypatch(appmod._warmup_local_weights) 才能拦住真实下载
    from freshlatch.ui.app import _warmup_local_weights as warmup

    try:
        warmup()
    except Exception as exc:  # noqa: BLE001
        message = f"下载/预热失败:{type(exc).__name__}: {exc}"[:500]
        with _WEIGHT_DOWNLOAD_LOCK:
            _WEIGHT_DOWNLOAD_JOB["state"] = "error"
            _WEIGHT_DOWNLOAD_JOB["error"] = message
    else:
        with _WEIGHT_DOWNLOAD_LOCK:
            _WEIGHT_DOWNLOAD_JOB["state"] = "ok"
            _WEIGHT_DOWNLOAD_JOB["error"] = None


def _weight_download_status() -> dict:
    """下载任务投影;running 超软上限时在本读取点判超时。"""
    with _WEIGHT_DOWNLOAD_LOCK:
        job = dict(_WEIGHT_DOWNLOAD_JOB)
    status = {"state": job["state"], "error": job["error"], "started_at": job["started_at"]}
    if job["state"] == "running":
        elapsed = time.monotonic() - (job["started_monotonic"] or time.monotonic())
        status["elapsed_s"] = int(elapsed)
        if elapsed > _WEIGHT_DOWNLOAD_TIMEOUT_S:
            status["state"] = "error"
            status["error"] = "下载超时(已超过 30 分钟)。请检查网络后点「重试下载」。"
            with _WEIGHT_DOWNLOAD_LOCK:
                _WEIGHT_DOWNLOAD_JOB["state"] = "error"
                _WEIGHT_DOWNLOAD_JOB["error"] = status["error"]
    return status


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
