"""I1 评测挂标面(#186 / ADR-0028)。

在 eval detail 与轨迹 JSONL 上挂与 `docs/evidence/i1/events.jsonl` **同名**的
`fail_bucket` / `err_kind`(及可选的同名对齐字段)。

**层身份：答辩 / 冒烟。** 这些字段是评测/复盘标签，不是生产 status；
禁止写入 `claim_final`，禁止扩进 Gate / disposition / HumanLatch 枚举。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from freshlatch.i1_events import ERR_KINDS, FAIL_BUCKETS, I1EventError

# 轨迹侧独立事件类型；与 claim_final 并列，互不改写
LABEL_EVENT_TYPE = "i1_eval_labels"

# 与 JSONL 同名的挂标核心字段（Acceptance 最低集）
CORE_LABEL_FIELDS: tuple[str, ...] = ("fail_bucket", "err_kind")

# 允许一并挂上的、与 I1 JSONL 同名的可选对齐字段（评测侧）
OPTIONAL_ALIGNED_FIELDS: tuple[str, ...] = (
    "sample_id",
    "gold_or_human",
    "machine_status",
    "layer",
    "trajectory_ptr",
    "evidence_md",
    "runnable",
    "package_disp",
)

# claim_final / eval detail 上不得被挂标改写的生产终态键
PRODUCTION_FINAL_KEYS: frozenset[str] = frozenset({
    "type",
    "claim_id",
    "statement",
    "status",
    "reason",
    "evidence_ids",
    "auditor_verdict",
    "dissent",
    "schema_version",
    "lead_status",
    "trajectory",
    "steps_used",
})


def validate_i1_label_enums(*, fail_bucket: str, err_kind: str) -> None:
    """封闭枚举校验；非法则拒绝（不写脏标）。"""
    if fail_bucket not in FAIL_BUCKETS:
        raise I1EventError(
            f"fail_bucket 须为 {{{', '.join(sorted(FAIL_BUCKETS))}}},收到: {fail_bucket!r}"
        )
    if err_kind not in ERR_KINDS:
        raise I1EventError(
            f"err_kind 须为 {{{', '.join(sorted(ERR_KINDS))}}},收到: {err_kind!r}"
        )


def build_i1_label_fields(
    *,
    fail_bucket: str,
    err_kind: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """构造与 I1 JSONL 同名的挂标字段 dict（评测层，非生产 status）。"""
    validate_i1_label_enums(fail_bucket=fail_bucket, err_kind=err_kind)
    out: dict[str, Any] = {
        "fail_bucket": str(fail_bucket),
        "err_kind": str(err_kind),
    }
    if extra:
        for key in OPTIONAL_ALIGNED_FIELDS:
            if key in extra and extra[key] is not None:
                out[key] = str(extra[key])
    return out


def attach_i1_labels_to_detail(
    detail: Mapping[str, Any],
    *,
    fail_bucket: str,
    err_kind: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """在 eval 明细副本上挂同名字段；不改 status / evidence_ids 等生产终态键。"""
    labels = build_i1_label_fields(
        fail_bucket=fail_bucket, err_kind=err_kind, extra=extra
    )
    # 浅拷贝：生产键原样保留，再叠挂标字段
    merged = dict(detail)
    for key in PRODUCTION_FINAL_KEYS:
        if key in detail:
            merged[key] = detail[key]
    merged.update(labels)
    return merged


def build_trajectory_label_event(
    claim_id: str,
    *,
    fail_bucket: str,
    err_kind: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """构造轨迹 JSONL 用的挂标事件（type=i1_eval_labels）；不含生产 claim_final 字段。"""
    labels = build_i1_label_fields(
        fail_bucket=fail_bucket, err_kind=err_kind, extra=extra
    )
    return {
        "type": LABEL_EVENT_TYPE,
        "claim_id": str(claim_id),
        **labels,
        # 显式层声明：机读可辨「评测挂标 ≠ 生产 status」
        "label_layer": "答辩/冒烟",
    }


def append_i1_labels_to_trajectory(
    trajectory_path: str | Path,
    claim_id: str,
    *,
    fail_bucket: str,
    err_kind: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """向既有轨迹 JSONL **追加**挂标行；不改写任何既有 claim_final 行。"""
    path = Path(trajectory_path)
    event = build_trajectory_label_event(
        claim_id, fail_bucket=fail_bucket, err_kind=err_kind, extra=extra
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def read_claim_finals(trajectory_path: str | Path) -> list[dict[str, Any]]:
    """只读抽出 claim_final 行（供挂标前后语义对比）。"""
    path = Path(trajectory_path)
    finals: list[dict[str, Any]] = []
    if not path.is_file():
        return finals
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("type") == "claim_final":
            finals.append(row)
    return finals


def read_i1_label_events(trajectory_path: str | Path) -> list[dict[str, Any]]:
    """只读抽出 i1_eval_labels 挂标行。"""
    path = Path(trajectory_path)
    labels: list[dict[str, Any]] = []
    if not path.is_file():
        return labels
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("type") == LABEL_EVENT_TYPE:
            labels.append(row)
    return labels
