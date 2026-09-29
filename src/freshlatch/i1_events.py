"""I1 失败事件薄账本(ADR-0028 / #184)。

评测侧 corpus:每次复盘样本追加写入 docs/evidence/i1/events.jsonl。
形态对标 patch_events(JSONL 校验/追加/读回),字段与封闭枚举独立;
禁止把三分法桶名扩进生产 Gate / disposition / HumanLatch 枚举。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

# 相对本模块定位仓根:src/freshlatch/i1_events.py → 上三级
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

REQUIRED_FIELDS: tuple[str, ...] = (
    "sample_id",
    "claim_id",
    "gold_or_human",
    "machine_status",
    "fail_bucket",
    "err_kind",
    "layer",
    "trajectory_ptr",
    "evidence_md",
    "runnable",
    "ts",
    "actor",
)

OPTIONAL_FIELDS: tuple[str, ...] = ("package_disp",)

# 封闭枚举(评测标签;非生产 status)
FAIL_BUCKETS: frozenset[str] = frozenset({"找不到", "找错", "没用上"})
ERR_KINDS: frozenset[str] = frozenset({"漏拦", "误拦"})
RUNNABLES: frozenset[str] = frozenset({"true", "false", "replay_trace_only"})

DEFAULT_FILENAME = "events.jsonl"


class I1EventError(ValueError):
    """schema / 封闭枚举校验失败。"""


def default_events_dir() -> Path:
    """约定账本目录:仓内 docs/evidence/i1/。"""
    return _REPO_ROOT / "docs" / "evidence" / "i1"


def _events_file(events_dir: Path | None, filename: str) -> Path:
    root = events_dir if events_dir is not None else default_events_dir()
    return Path(root) / filename


def _normalize(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = [k for k in REQUIRED_FIELDS if k not in payload]
    if missing:
        raise I1EventError(f"缺必填字段: {', '.join(missing)}")

    fail_bucket = payload["fail_bucket"]
    if fail_bucket not in FAIL_BUCKETS:
        raise I1EventError(
            f"fail_bucket 须为 {{{', '.join(sorted(FAIL_BUCKETS))}}},收到: {fail_bucket!r}"
        )

    err_kind = payload["err_kind"]
    if err_kind not in ERR_KINDS:
        raise I1EventError(
            f"err_kind 须为 {{{', '.join(sorted(ERR_KINDS))}}},收到: {err_kind!r}"
        )

    runnable = payload["runnable"]
    # 允许 bool 入参,统一写成字符串封闭枚举
    if isinstance(runnable, bool):
        runnable = "true" if runnable else "false"
    else:
        runnable = str(runnable)
    if runnable not in RUNNABLES:
        raise I1EventError(
            f"runnable 须为 {{{', '.join(sorted(RUNNABLES))}}},收到: {runnable!r}"
        )

    event: dict[str, Any] = {
        "sample_id": str(payload["sample_id"]),
        "claim_id": str(payload["claim_id"]),
        "gold_or_human": str(payload["gold_or_human"]),
        "machine_status": str(payload["machine_status"]),
        "fail_bucket": str(fail_bucket),
        "err_kind": str(err_kind),
        "layer": str(payload["layer"]),
        "trajectory_ptr": str(payload["trajectory_ptr"]),
        "evidence_md": str(payload["evidence_md"]),
        "runnable": runnable,
        "ts": str(payload["ts"]),
        "actor": str(payload["actor"]),
    }

    if "package_disp" in payload and payload["package_disp"] is not None:
        event["package_disp"] = str(payload["package_disp"])

    return event


def append_event(
    payload: Mapping[str, Any],
    *,
    events_dir: Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> dict[str, Any]:
    """追加一行 JSONL;返回规范化后的事件 dict。非法枚举拒绝且不写脏行。"""
    event = _normalize(payload)
    path = _events_file(events_dir, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def append_i1_sample(
    *,
    sample_id: str,
    claim_id: str,
    gold_or_human: str,
    machine_status: str,
    fail_bucket: str,
    err_kind: str,
    layer: str,
    trajectory_ptr: str,
    evidence_md: str,
    runnable: str | bool,
    actor: str = "script",
    ts: str | None = None,
    package_disp: str | None = None,
    events_dir: Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> dict[str, Any]:
    """具名入口:与 append_event 同一 schema。"""
    if ts is None:
        ts = datetime.now(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "sample_id": sample_id,
        "claim_id": claim_id,
        "gold_or_human": gold_or_human,
        "machine_status": machine_status,
        "fail_bucket": fail_bucket,
        "err_kind": err_kind,
        "layer": layer,
        "trajectory_ptr": trajectory_ptr,
        "evidence_md": evidence_md,
        "runnable": runnable,
        "ts": ts,
        "actor": actor,
    }
    if package_disp is not None:
        payload["package_disp"] = package_disp
    return append_event(payload, events_dir=events_dir, filename=filename)


def iter_events(
    *,
    events_dir: Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> Iterable[dict[str, Any]]:
    """按行迭代 JSONL;空文件或不存在 → 空迭代。"""
    path = _events_file(events_dir, filename)
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)


def read_events(
    *,
    events_dir: Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> list[dict[str, Any]]:
    """读回全部事件行。"""
    return list(iter_events(events_dir=events_dir, filename=filename))
