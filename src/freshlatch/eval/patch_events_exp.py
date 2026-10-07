"""patch_events 主实验记录。

只给实验脚本用。产品账本仍在 patch_events.py，arm 只接受 C 与 T。
construction_gold 是构造金标，在系统输出和评委打分之前写死，不是评委标签。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[3]

EDIT_TYPES: frozenset[str] = frozenset({"数值", "日期", "条款替换", "删除"})
EXPERIMENT_ARMS: frozenset[str] = frozenset({"C", "T", "B1", "B2"})
ABLATION_TAGS: frozenset[str] = frozenset(
    {"no_chunk_bind", "no_auto_verify", "soft_warning", "retrieval_bm25"}
)
CONSTRUCTION_GOLD: frozenset[str] = frozenset({"正确", "坏"})
DECISIONS: frozenset[str] = frozenset({"release", "reject"})

REQUIRED_FIELDS: tuple[str, ...] = (
    "claim_id",
    "edit_type",
    "arm",
    "ablation",
    "construction_gold",
    "before_text",
    "after_text",
    "evidence_id",
    "evidence_text",
)
OPTIONAL_FIELDS: tuple[str, ...] = (
    "decision",
    "reject_reason",
    "score",
    "latency_ms",
    "cost",
    "reverify_ok",
    "ledger",
)
LEDGER_VALUES: frozenset[str] = frozenset({"", "hybrid+rerank"})
DEFAULT_FILENAME = "experiment.jsonl"


class ExperimentRecordError(ValueError):
    """实验记录校验失败。"""


def default_experiment_dir() -> Path:
    """实验记录目录。不使用产品账本 data/patch_events/。"""
    return _REPO_ROOT / "data" / "exp" / "patch-events"


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def normalize_experiment_record(payload: Mapping[str, Any]) -> dict[str, Any]:
    """校验并返回实验记录。构造阶段可以不带跑完才填的字段。"""
    missing = [key for key in REQUIRED_FIELDS if key not in payload]
    if missing:
        raise ExperimentRecordError(f"缺必填字段: {', '.join(missing)}")

    unknown = [key for key in payload if key not in REQUIRED_FIELDS and key not in OPTIONAL_FIELDS]
    if unknown:
        raise ExperimentRecordError(f"未知字段: {', '.join(unknown)}")

    edit_type = payload["edit_type"]
    if edit_type not in EDIT_TYPES:
        raise ExperimentRecordError(f"edit_type 非法: {edit_type!r}")

    arm = payload["arm"]
    if arm not in EXPERIMENT_ARMS:
        raise ExperimentRecordError(f"arm 非法: {arm!r}")

    ablation = payload["ablation"]
    if not isinstance(ablation, str) or (ablation != "" and ablation not in ABLATION_TAGS):
        raise ExperimentRecordError(f"ablation 非法: {ablation!r}")
    if ablation != "" and arm != "T":
        raise ExperimentRecordError("ablation 非空时 arm 必须是 T")

    construction_gold = payload["construction_gold"]
    if construction_gold not in CONSTRUCTION_GOLD:
        raise ExperimentRecordError(f"construction_gold 非法: {construction_gold!r}")

    text_fields = ("claim_id", "before_text", "after_text", "evidence_id", "evidence_text")
    for key in text_fields:
        if not isinstance(payload[key], str):
            raise ExperimentRecordError(f"{key} 须为字符串")

    record: dict[str, Any] = {
        "claim_id": payload["claim_id"],
        "edit_type": edit_type,
        "arm": arm,
        "ablation": ablation,
        "construction_gold": construction_gold,
        "before_text": payload["before_text"],
        "after_text": payload["after_text"],
        "evidence_id": payload["evidence_id"],
        "evidence_text": payload["evidence_text"],
    }

    if "decision" in payload:
        decision = payload["decision"]
        if decision not in DECISIONS:
            raise ExperimentRecordError(f"decision 非法: {decision!r}")
        record["decision"] = decision

    if "reject_reason" in payload:
        reject_reason = payload["reject_reason"]
        if not isinstance(reject_reason, str):
            raise ExperimentRecordError("reject_reason 须为字符串")
        record["reject_reason"] = reject_reason

    if "score" in payload:
        score = payload["score"]
        if score is not None and not _is_number(score):
            raise ExperimentRecordError(f"score 须为数字或空,收到: {score!r}")
        record["score"] = score

    if "latency_ms" in payload:
        latency_ms = payload["latency_ms"]
        if not _is_number(latency_ms):
            raise ExperimentRecordError(f"latency_ms 须为数字,收到: {latency_ms!r}")
        record["latency_ms"] = latency_ms

    if "cost" in payload:
        cost = payload["cost"]
        if not _is_number(cost):
            raise ExperimentRecordError(f"cost 须为数字,收到: {cost!r}")
        record["cost"] = cost

    if "reverify_ok" in payload:
        reverify_ok = payload["reverify_ok"]
        if not isinstance(reverify_ok, bool):
            raise ExperimentRecordError(f"reverify_ok 须为布尔值,收到: {reverify_ok!r}")
        record["reverify_ok"] = reverify_ok

    if "ledger" in payload:
        ledger = payload["ledger"]
        if not isinstance(ledger, str) or ledger not in LEDGER_VALUES:
            raise ExperimentRecordError(f"ledger 非法: {ledger!r}")
        if ledger != "":
            record["ledger"] = ledger

    return record


def _events_file(events_dir: Path | None, filename: str) -> Path:
    root = events_dir if events_dir is not None else default_experiment_dir()
    return Path(root) / filename


def append_experiment_record(
    payload: Mapping[str, Any],
    *,
    events_dir: Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> dict[str, Any]:
    """追加一行实验 JSONL。不写入产品账本。"""
    record = normalize_experiment_record(payload)
    path = _events_file(events_dir, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def read_experiment_records(
    *,
    events_dir: Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> list[dict[str, Any]]:
    """按行读实验 JSONL。文件不存在时返回空列表。"""
    path = _events_file(events_dir, filename)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows
