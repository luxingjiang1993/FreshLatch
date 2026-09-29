"""#186 I1 eval/轨迹评测挂标:字段对齐 + 生产语义未漂 + 枚举未扩。

层=答辩/冒烟。零 LLM、零网络。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch import i1_events as ie
from freshlatch.disposition import DISPOSITIONS
from freshlatch.eval.i1_labels import (
    CORE_LABEL_FIELDS,
    LABEL_EVENT_TYPE,
    append_i1_labels_to_trajectory,
    attach_i1_labels_to_detail,
    build_i1_label_fields,
    read_claim_finals,
    read_i1_label_events,
)
from freshlatch.eval.runner import label_eval_detail
from freshlatch.gates.human_latch import VALID_ACTIONS

# 三分法桶名——不得进入生产封闭集
TRIAD_BUCKETS = ("找不到", "找错", "没用上")

# claim_final 生产终态键（挂标前后必须一致）
CLAIM_FINAL_KEYS = (
    "type",
    "claim_id",
    "statement",
    "status",
    "reason",
    "evidence_ids",
    "auditor_verdict",
    "dissent",
    "schema_version",
)


def _sample_detail(**overrides):
    base = {
        "status": "fresh",
        "reason": "假绿对照",
        "evidence_ids": ["e1"],
        "trajectory": "reports/trajectories/run-demo.jsonl",
        "steps_used": 3,
        "lead_status": "fresh",
        "auditor_verdict": "fresh",
        "dissent": None,
    }
    base.update(overrides)
    return base


def _write_minimal_trajectory(path: Path, *, claim_id: str = "c2") -> dict:
    """写入一条最小 claim_final，模拟生产落盘。"""
    final = {
        "type": "claim_final",
        "claim_id": claim_id,
        "statement": "demo claim",
        "status": "fresh",
        "reason": "machine alive",
        "evidence_ids": ["e1"],
        "auditor_verdict": "fresh",
        "dissent": None,
        "schema_version": "1",
    }
    meta = {"type": "run_meta", "mode": "eval"}
    path.write_text(
        json.dumps(meta, ensure_ascii=False)
        + "\n"
        + json.dumps(final, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return final


def test_build_label_fields_align_jsonl_names():
    """挂标核心字段名与 I1 JSONL 同名。"""
    fields = build_i1_label_fields(fail_bucket="找错", err_kind="漏拦")
    for key in CORE_LABEL_FIELDS:
        assert key in fields
    assert fields["fail_bucket"] == "找错"
    assert fields["err_kind"] == "漏拦"
    # 与账本封闭枚举同源
    assert fields["fail_bucket"] in ie.FAIL_BUCKETS
    assert fields["err_kind"] in ie.ERR_KINDS
    for key in CORE_LABEL_FIELDS:
        assert key in ie.REQUIRED_FIELDS


def test_attach_to_eval_detail_hangs_same_named_fields():
    """Given 一条 eval 明细，When 挂标，Then 出现同名 fail_bucket/err_kind。"""
    detail = _sample_detail()
    before_status = detail["status"]
    before_ids = list(detail["evidence_ids"])
    labeled = attach_i1_labels_to_detail(
        detail, fail_bucket="找错", err_kind="漏拦"
    )
    assert labeled["fail_bucket"] == "找错"
    assert labeled["err_kind"] == "漏拦"
    # 生产终态键未漂
    assert labeled["status"] == before_status
    assert labeled["evidence_ids"] == before_ids
    assert labeled["lead_status"] == detail["lead_status"]
    # 原 detail 不被原地污染
    assert "fail_bucket" not in detail


def test_label_eval_detail_and_trajectory_append(tmp_path: Path):
    """detail 挂标 + 轨迹追加；claim_final 语义不变；可经 trajectory_ptr 进账本。"""
    traj = tmp_path / "run-186.jsonl"
    original_final = _write_minimal_trajectory(traj, claim_id="c2")
    before_finals = read_claim_finals(traj)
    assert len(before_finals) == 1
    assert before_finals[0] == original_final

    detail = _sample_detail(trajectory=str(traj))
    labeled = label_eval_detail(
        detail,
        fail_bucket="找错",
        err_kind="漏拦",
        extra={"layer": "答辩/冒烟", "sample_id": "i1-s001"},
        also_write_trajectory=True,
        claim_id="c2",
    )
    assert labeled["fail_bucket"] == "找错"
    assert labeled["err_kind"] == "漏拦"
    assert labeled["sample_id"] == "i1-s001"
    assert labeled["status"] == "fresh"
    assert labeled["evidence_ids"] == ["e1"]

    # 轨迹：挂标行出现；claim_final 逐字段不变
    after_finals = read_claim_finals(traj)
    assert after_finals == before_finals
    for key in CLAIM_FINAL_KEYS:
        assert after_finals[0][key] == original_final[key]
        assert key != "fail_bucket"  # claim_final 不含三分法
    assert "fail_bucket" not in after_finals[0]
    assert "err_kind" not in after_finals[0]

    label_rows = read_i1_label_events(traj)
    assert len(label_rows) == 1
    assert label_rows[0]["type"] == LABEL_EVENT_TYPE
    assert label_rows[0]["fail_bucket"] == "找错"
    assert label_rows[0]["err_kind"] == "漏拦"
    assert label_rows[0]["claim_id"] == "c2"
    assert label_rows[0]["label_layer"] == "答辩/冒烟"

    # 账本可经 trajectory_ptr 引用该轨迹
    events_dir = tmp_path / "i1"
    row = ie.append_i1_sample(
        sample_id="i1-test-186",
        claim_id="c2",
        gold_or_human="gold",
        machine_status="alive",
        fail_bucket="找错",
        err_kind="漏拦",
        layer="答辩/冒烟",
        trajectory_ptr=str(traj),
        evidence_md="docs/evidence/i1/i1-s001-c2-漏拦-找错.md",
        runnable="replay_trace_only",
        events_dir=events_dir,
    )
    assert row["trajectory_ptr"] == str(traj)
    assert row["fail_bucket"] == labeled["fail_bucket"]
    assert row["err_kind"] == labeled["err_kind"]
    # 指针指向的文件确有挂标行
    assert read_i1_label_events(row["trajectory_ptr"])


def test_append_rejects_invalid_bucket(tmp_path: Path):
    traj = tmp_path / "run.jsonl"
    _write_minimal_trajectory(traj)
    with pytest.raises(ie.I1EventError):
        append_i1_labels_to_trajectory(
            traj, "c2", fail_bucket="检索失败", err_kind="漏拦"
        )
    assert read_i1_label_events(traj) == []
    # claim_final 仍在且未脏写
    assert read_claim_finals(traj)[0]["status"] == "fresh"


def test_runner_dump_i1_eval_labels_does_not_mutate_claim_final(tmp_path: Path):
    """Runner.dump_i1_eval_labels：追加挂标，claim_final 键值不变。"""
    traj = tmp_path / "run-runner.jsonl"
    original = _write_minimal_trajectory(traj, claim_id="c2")

    # 轻量：直接测 append 路径（与 dump_i1_eval_labels 同源）
    from freshlatch.runner import Runner

    # 构造最小 Runner 桩：只挂轨迹路径与 dump 方法
    class _Stub:
        pass

    stub = _Stub()
    stub._trajectory_path = traj
    written = Runner.dump_i1_eval_labels(
        stub,  # type: ignore[arg-type]
        {"c2": {"fail_bucket": "找不到", "err_kind": "误拦"}},
    )
    assert written[0]["fail_bucket"] == "找不到"
    assert written[0]["err_kind"] == "误拦"
    finals = read_claim_finals(traj)
    assert finals[0] == original
    for key in CLAIM_FINAL_KEYS:
        assert key in finals[0]


def test_production_enums_not_extended_with_triad():
    """VALID_ACTIONS / DISPOSITIONS 仍为封闭生产集，无三分法桶名。"""
    for bucket in TRIAD_BUCKETS:
        assert bucket not in VALID_ACTIONS
        assert bucket not in DISPOSITIONS
    assert VALID_ACTIONS == ("discard", "renew")
    assert DISPOSITIONS == frozenset({"可发", "需补丁", "勿发"})
