"""patch_events JSONL 账本(ADR-0027 / roadmap 预登记字段)。

自 V1 起每次改稿相关事件追加写入 data/patch_events/。
C vs T 对照只经后台/脚本记账,不进正式发前 UX;人手补丁走同一 schema。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

# 相对本模块定位仓根:src/freshlatch/patch_events.py → 上三级
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

REQUIRED_FIELDS: tuple[str, ...] = (
    "claim_id",
    "before_disp",
    "patch_span",
    "t1_ids",
    "human_confirm",
    "reverify",
    "minutes",
    "arm",
    "ts",
    "actor",
)

VALID_ARMS: frozenset[str] = frozenset({"C", "T"})
DEFAULT_FILENAME = "events.jsonl"


class PatchEventError(ValueError):
    """schema / arm 校验失败。"""


def default_events_dir() -> Path:
    """约定账本目录:仓内 data/patch_events/。"""
    return _REPO_ROOT / "data" / "patch_events"


def _events_file(events_dir: Path | None, filename: str) -> Path:
    root = events_dir if events_dir is not None else default_events_dir()
    return Path(root) / filename


def _normalize(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = [k for k in REQUIRED_FIELDS if k not in payload]
    if missing:
        raise PatchEventError(f"缺必填字段: {', '.join(missing)}")

    arm = payload["arm"]
    if arm not in VALID_ARMS:
        raise PatchEventError(f"arm 须为 C 或 T,收到: {arm!r}")

    t1_ids = payload["t1_ids"]
    if not isinstance(t1_ids, list):
        raise PatchEventError("t1_ids 须为 list")

    return {
        "claim_id": str(payload["claim_id"]),
        "before_disp": str(payload["before_disp"]),
        "patch_span": payload["patch_span"],
        "t1_ids": list(t1_ids),
        "human_confirm": bool(payload["human_confirm"]),
        "reverify": bool(payload["reverify"]),
        "minutes": float(payload["minutes"]),
        "arm": str(arm),
        "ts": str(payload["ts"]),
        "actor": str(payload["actor"]),
    }


def append_event(
    payload: Mapping[str, Any],
    *,
    events_dir: Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> dict[str, Any]:
    """追加一行 JSONL;返回规范化后的事件 dict。"""
    event = _normalize(payload)
    path = _events_file(events_dir, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def append_human_patch(
    *,
    claim_id: str,
    before_disp: str,
    patch_span: Any,
    t1_ids: list,
    human_confirm: bool,
    reverify: bool,
    minutes: float,
    arm: str,
    actor: str = "human",
    ts: str | None = None,
    events_dir: Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> dict[str, Any]:
    """人手补丁入口:与后台 C/T 同一 schema;arm 须调用方显式传入。"""
    if ts is None:
        ts = datetime.now(timezone.utc).isoformat()
    return append_event(
        {
            "claim_id": claim_id,
            "before_disp": before_disp,
            "patch_span": patch_span,
            "t1_ids": t1_ids,
            "human_confirm": human_confirm,
            "reverify": reverify,
            "minutes": minutes,
            "arm": arm,
            "ts": ts,
            "actor": actor,
        },
        events_dir=events_dir,
        filename=filename,
    )


def record_human_review_events(
    results: Iterable[Mapping[str, Any]],
    *,
    before_disp: str,
    t1_ids: list | None = None,
    arm: str = "C",
    actor: str = "human",
    minutes: float = 0.0,
    events_dir: Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> list[dict[str, Any]]:
    """人审落档后追加 patch_events(发前主缝记账)。

    仅对 ok=True 的决定写一行;arm 由后台固定传入(默认 C),不进发前 UX 开关。
    before_disp 须为人审前提交的包结论快照。
    """
    ids = list(t1_ids or [])
    written: list[dict[str, Any]] = []
    for row in results:
        if not row.get("ok"):
            continue
        claim_id = str(row.get("claim_id") or "")
        if not claim_id:
            continue
        action = str(row.get("action") or "human")
        written.append(
            append_human_patch(
                claim_id=claim_id,
                before_disp=before_disp,
                patch_span=f"人审{action}",
                t1_ids=ids,
                human_confirm=True,
                reverify=False,
                minutes=minutes,
                arm=arm,
                actor=actor,
                events_dir=events_dir,
                filename=filename,
            )
        )
    return written


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
