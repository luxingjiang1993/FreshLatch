"""轨迹目录聚合 SLI 5 一行（L4-EV-03 / A-EV-03）。

纯函数：读一个轨迹目录，按 ``docs/ops/延迟与检索回退周报.md`` §1 / §9
的列名产出**一行**。至少含 ``e2e_p95_ms``、``retrieval_fallback_rate``，
并带上 ``N_request_ok``、``N_retrieve``、``fallback_n``、``notes``、``window``。
内存入口 ``aggregate_trajectory_runs`` 使用同一套计数。目录函数读完文件后调用它。

本模块**不计入**注册 G1/A1/T1/R1。不写 ``RESULT-Y`` / ``PREREG-Y``，
不发明 SESOI，不改地板，不改生产检索臂，不把夹具读数当成注册分变好。
``SLI_MANIFEST["counted_in_registered_g1_a1_t1_r1"]`` 恒为 False。

夹具 schema（只读目录，不新增生产写入器）
------------------------------------------
目录顶层的 ``*.jsonl`` / ``*.json``。不递归。一个文件 = 一次 ``Runner.run``
（``src/freshlatch/runner.py`` 的 ``_dump_trajectory`` 一次写一个 JSONL）。

JSONL：一行一个事件对象，形状对齐生产轨迹。空行跳过。
JSON：事件对象列表，或 ``{"events": [...]}``，或单个带 ``type`` 的事件对象。

计入分母的生产字段：

- ``type=retrieve`` 且同时有非空字符串 ``retrieval_mode`` 与 ``rerank_mode``
  → ``N_retrieve``。这是 ``try_retrieve`` 走到 ``store.retrieve`` 之后的事件。
- ``type=budget`` 且 ``kind=retrieval_exhausted`` 不是完成的检索，不进分母。
- 没有 ``retrieval_mode`` / ``rerank_mode`` 的旧 retrieve 行不进 ``N_retrieve``。
- ``type=claim_final``：复验单主张落档，该文件进入 ``N_request_ok``。
- ``type=publish_exit`` 且 ``allow`` 为布尔：发前出口写下 allow 或 deny。
  生产轨迹目前不写这一行；夹具用它对齐周报「发前出口」终态。
  ``allow`` 为真或假都算终态。
- ``run_meta.mode == "eval"`` 的文件整份排除（金标 / canary，不进两个分母）。
  缺 ``mode`` 或 ``mode=online`` 按生产夹具计入。

``duration_ms`` 是夹具字段（生产 ``run_meta`` / ``claim_final`` 没有墙钟）。
非负 int 或 float，单位毫秒，不再乘 1000。布尔不算数。

一次请求的墙钟：优先该文件 ``run_meta.duration_ms``；否则各终态事件的
``duration_ms`` 必须齐全且彼此相等。缺墙钟或互相冲突 → 该请求没有时长。

回退分子（一条 retrieve 至多一次）：``retrieval_mode=bm25_fallback``
**或** ``rerank_mode=lexical_fallback``。
显式运维开关 ``retrieval_mode=bm25``（通常配 ``rerank_mode=none``）
**不是** ``bm25_fallback``，不进分子。``hybrid+rerank_lexical`` + ``lexical``、
``hybrid+rerank`` + ``bge-reranker-base``、``hybrid`` / ``dense`` + ``none``
同样不进分子。

占位：``N_request_ok=0`` → ``e2e_p95_ms=样本不足``（禁止 0 / 0 ms）。
有终态但不是每条都有墙钟 → ``未计``。``N_retrieve=0`` →
``retrieval_fallback_rate=样本不足``（禁止 0、0.0、0%、``0 / 0``）。
分母大于 0 且 ``fallback_n=0`` 时比率写 ``0 / N_retrieve``，这是回退计数。

P95：有 n 条且每条都有墙钟时，毫秒升序，下标 ``ceil(0.95 * n) - 1``（从 0 数）。
n=1 时 P95 就是这一条，notes 写明 n=1。这是冒烟读数，不报总体方差。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import TypedDict

# 周报占位。禁止用 0 / 0.0 / 0% / 0 ms 代替这两句。
PLACEHOLDER_INSUFFICIENT = "样本不足"
PLACEHOLDER_UNMEASURED = "未计"

# 与 runner.try_retrieve 写入的 retrieve 事件对齐。
# type=budget 且 kind=retrieval_exhausted 是另一种事件，不会走进这个常量。
RETRIEVE_EVENT = "retrieve"

# 主张落档。runner._dump_trajectory 在事件流之后写 type=claim_final。
CLAIM_FINAL_EVENT = "claim_final"
# 发前出口夹具。生产 JSONL 尚无此行；allow 为布尔时 allow / deny 都算终态。
PUBLISH_EXIT_EVENT = "publish_exit"

# 周报 §1.3：缺向量，或精排缺失回退。显式 bm25 不在此列。
BM25_FALLBACK = "bm25_fallback"
LEXICAL_FALLBACK = "lexical_fallback"

# 金标 / canary。RunContext.mode == "eval" 时 run_meta 写成这个值。
EVAL_MODE = "eval"

SLI_MANIFEST: dict[str, object] = {
    "ticket": "L4-EV-03",
    "protocol": "docs/ops/延迟与检索回退周报.md",
    # 本行是观测 / Watch。不进入注册 G1/A1/T1/R1，也不回写 RESULT-Y。
    "counted_in_registered_g1_a1_t1_r1": False,
    "writes_result_y": False,
    "invents_sesoi": False,
}


class TrajectorySliRow(TypedDict):
    """与周报 §9 同一组列。比率与占位都是字符串，避免把未计写成 0。"""

    window: str
    N_request_ok: int
    e2e_p95_ms: int | float | str
    N_retrieve: int
    fallback_n: int
    retrieval_fallback_rate: str
    notes: str


def aggregate_trajectory_runs(
    runs: list[list[dict]],
    *,
    window: str,
) -> TrajectorySliRow:
    """聚合已经在内存里的轨迹。每一项是一次 run 的事件列表。不读目录。

    计数规则与 ``aggregate_trajectory_sli`` 相同：eval 整份排除，
    P95 与 fallback 的占位句不变。``window`` 由调用方给出。
    """
    durations: list[float] = []
    n_request_ok = 0
    n_retrieve = 0
    fallback_n = 0

    for events in runs:
        if _is_eval_run(events):
            continue
        for event in events:
            if not _is_retrieve_completion(event):
                continue
            n_retrieve += 1
            if _is_fallback(event):
                fallback_n += 1
        if not _has_terminal(events):
            continue
        n_request_ok += 1
        duration = _request_duration_ms(events)
        if duration is not None:
            durations.append(duration)

    e2e = _e2e_p95_ms(n_request_ok, durations)
    rate = _fallback_rate(fallback_n, n_retrieve)
    return TrajectorySliRow(
        window=window,
        N_request_ok=n_request_ok,
        e2e_p95_ms=e2e,
        N_retrieve=n_retrieve,
        fallback_n=fallback_n,
        retrieval_fallback_rate=rate,
        notes=_notes(
            n_request_ok=n_request_ok,
            e2e=e2e,
            n_retrieve=n_retrieve,
            fallback_n=fallback_n,
        ),
    )


def aggregate_trajectory_sli(
    trajectory_dir: str | Path,
    *,
    window: str | None = None,
) -> TrajectorySliRow:
    """读轨迹目录，返回一行 SLI。不写盘，不改调用方传入的文件。

    ``window`` 缺省时用目录路径，表示这一目录就是观测窗口。
    调用方要写周报起止时，传入 Asia/Shanghai 的窗口标签。
    目录不存在或不是目录时拒绝，避免把打错的路径报成样本不足。
    读入后交给 ``aggregate_trajectory_runs``，计数规则不另写一套。
    """
    root = Path(trajectory_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"轨迹目录不存在: {root}")
    label = root.as_posix() if window is None else window
    runs = [_load_events(path) for path in _trajectory_files(root)]
    return aggregate_trajectory_runs(runs, window=label)


def _trajectory_files(root: Path) -> list[Path]:
    """只取顶层 json / jsonl，按文件名排序。子目录不是一次 run。"""
    files = [
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl"}
    ]
    return sorted(files, key=lambda path: path.name)


def _load_events(path: Path) -> list[dict]:
    """按后缀读事件。坏 JSON 直接抛出，不把半截文件当成空样本。"""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        events: list[dict] = []
        for line in text.splitlines():
            body = line.strip()
            if not body:
                continue
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                events.append(parsed)
        return events
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        inner = parsed.get("events")
        if isinstance(inner, list):
            return [item for item in inner if isinstance(item, dict)]
        if "type" in parsed:
            return [parsed]
    return []


def _is_eval_run(events: list[dict]) -> bool:
    """run_meta.mode=eval 是评测臂 / 金标跑，两个分母都不进。"""
    for event in events:
        if event.get("type") == "run_meta" and event.get("mode") == EVAL_MODE:
            return True
    return False


def _is_retrieve_completion(event: dict) -> bool:
    """完成的检索：type=retrieve，且两个模式字段都在。

    type=budget（含 kind=retrieval_exhausted）不是 retrieve，这里直接排除。
    """
    if event.get("type") != RETRIEVE_EVENT:
        return False
    mode = event.get("retrieval_mode")
    rerank = event.get("rerank_mode")
    return isinstance(mode, str) and bool(mode) and isinstance(rerank, str) and bool(rerank)


def _is_fallback(event: dict) -> bool:
    """一条调用至多由调用方计一次。显式 bm25 不等于 bm25_fallback。"""
    return (
        event.get("retrieval_mode") == BM25_FALLBACK
        or event.get("rerank_mode") == LEXICAL_FALLBACK
    )


def _has_terminal(events: list[dict]) -> bool:
    return any(_is_terminal(event) for event in events)


def _is_terminal(event: dict) -> bool:
    """主张落档，或发前出口的 allow/deny。lead_loop_end 与 claim_result 不算。"""
    if event.get("type") == CLAIM_FINAL_EVENT:
        return True
    return event.get("type") == PUBLISH_EXIT_EVENT and isinstance(event.get("allow"), bool)


def _nonneg_ms(value: object) -> float | None:
    """墙钟毫秒。布尔、负数、非数都不是时长。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value < 0:
        return None
    return float(value)


def _request_duration_ms(events: list[dict]) -> float | None:
    """一次 run 的墙钟。没有单一读数就返回 None，交给「未计」。"""
    for event in events:
        if event.get("type") != "run_meta":
            continue
        duration = _nonneg_ms(event.get("duration_ms"))
        if duration is not None:
            return duration
    terminals = [event for event in events if _is_terminal(event)]
    present: list[float] = []
    for event in terminals:
        duration = _nonneg_ms(event.get("duration_ms"))
        if duration is None:
            return None
        present.append(duration)
    if not present:
        return None
    if len(set(present)) == 1:
        return present[0]
    return None


def _e2e_p95_ms(n_request_ok: int, durations: list[float]) -> int | float | str:
    """n=0 写样本不足。有终态但墙钟不齐写未计。禁止用 0 填这两格。"""
    if n_request_ok == 0:
        return PLACEHOLDER_INSUFFICIENT
    if len(durations) != n_request_ok:
        return PLACEHOLDER_UNMEASURED
    return _p95(durations)


def _p95(samples: list[float]) -> int | float:
    """升序后取 ceil(0.95 * n) - 1。整数毫秒保持 int。"""
    ordered = sorted(samples)
    index = math.ceil(0.95 * len(ordered)) - 1
    chosen = ordered[index]
    if float(chosen).is_integer():
        return int(chosen)
    return chosen


def _fallback_rate(fallback_n: int, n_retrieve: int) -> str:
    """分母为 0 写样本不足。否则保留 fallback_n / N_retrieve，不约分。"""
    if n_retrieve == 0:
        return PLACEHOLDER_INSUFFICIENT
    return f"{fallback_n} / {n_retrieve}"


def _notes(
    *,
    n_request_ok: int,
    e2e: int | float | str,
    n_retrieve: int,
    fallback_n: int,
) -> str:
    """备注格。cost 只留 phase-2 指针，不填 token / CNY / gpu_s。"""
    parts = [
        "cost → phase-2",
        "P95 不单独构成放行成功",
        "本行不是放行成功",
        "不计注册 G1/A1/T1/R1",
        "不写 RESULT-Y",
    ]
    if n_request_ok == 0 and n_retrieve == 0:
        parts.append("成功完成请求与检索调用都不足。不把 P95 写成 0 ms。样本不足的回退率不能当成 0")
    if e2e == PLACEHOLDER_UNMEASURED:
        parts.append("有终态、没有逐请求墙钟，P95 写未计")
    if isinstance(e2e, (int, float)) and not isinstance(e2e, bool) and n_request_ok == 1:
        parts.append("n=1。冒烟读数，不报总体方差")
    if n_retrieve > 0 and fallback_n == n_retrieve:
        parts.append("全在 fallback")
    elif n_retrieve > 0 and fallback_n == 0:
        parts.append("这是回退计数，不是放行已经成功，也不是 P95 已经过线")
    if e2e != PLACEHOLDER_INSUFFICIENT and n_retrieve == 0:
        parts.append("retrieval_fallback_rate 样本不足，不能把旁边的 P95 读成放行成功")
    return "。".join(parts) + "。"
