"""#184 I1 失败事件薄账本:写后读、封闭枚举拒绝、生产枚举未扩。

零 LLM、零网络;只测 docs/evidence/i1 账本缝与生产枚举隔离。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from freshlatch import i1_events as ie
from freshlatch.disposition import DISPOSITIONS
from freshlatch.gates.human_latch import VALID_ACTIONS

REQUIRED = (
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

# 三分法桶名——不得进入生产封闭集
TRIAD_BUCKETS = ("找不到", "找错", "没用上")


def _sample_event(**overrides):
    base = {
        "sample_id": "i1-test-001",
        "claim_id": "c2",
        "gold_or_human": "gold",
        "machine_status": "alive",
        "fail_bucket": "找错",
        "err_kind": "漏拦",
        "layer": "答辩/冒烟",
        "trajectory_ptr": "docs/evidence/w4/false-green-control.md",
        "evidence_md": "docs/evidence/i1/i1-s001-c2-漏拦-找错.md",
        "runnable": "replay_trace_only",
        "ts": "2026-09-29T06:45:00+00:00",
        "actor": "script",
    }
    base.update(overrides)
    return base


def test_append_then_read_roundtrip_fields_complete(tmp_path: Path):
    """Given 一次合法 append,When 读 JSONL,Then 最少字段齐全且值一致。"""
    events_dir = tmp_path / "i1"
    written = ie.append_event(_sample_event(package_disp="勿发"), events_dir=events_dir)
    rows = ie.read_events(events_dir=events_dir)
    assert len(rows) == 1
    row = rows[0]
    for key in REQUIRED:
        assert key in row
        assert row[key] == written[key]
    assert row["fail_bucket"] in ie.FAIL_BUCKETS
    assert row["err_kind"] in ie.ERR_KINDS
    assert row["runnable"] in ie.RUNNABLES
    assert row["package_disp"] == "勿发"


def test_append_rejects_invalid_fail_bucket(tmp_path: Path):
    """Given 非法 fail_bucket,When append,Then 拒绝且不写脏行。"""
    events_dir = tmp_path / "i1"
    with pytest.raises(ie.I1EventError):
        ie.append_event(_sample_event(fail_bucket="检索失败"), events_dir=events_dir)
    assert ie.read_events(events_dir=events_dir) == []
    assert not (events_dir / ie.DEFAULT_FILENAME).exists()


def test_append_rejects_invalid_err_kind(tmp_path: Path):
    events_dir = tmp_path / "i1"
    with pytest.raises(ie.I1EventError):
        ie.append_event(_sample_event(err_kind="半拦"), events_dir=events_dir)
    assert ie.read_events(events_dir=events_dir) == []


def test_append_rejects_invalid_runnable(tmp_path: Path):
    events_dir = tmp_path / "i1"
    with pytest.raises(ie.I1EventError):
        ie.append_event(_sample_event(runnable="maybe"), events_dir=events_dir)
    assert ie.read_events(events_dir=events_dir) == []


def test_append_rejects_missing_fail_bucket(tmp_path: Path):
    """缺桶的漏/误行拒绝。"""
    events_dir = tmp_path / "i1"
    bad = _sample_event()
    del bad["fail_bucket"]
    with pytest.raises(ie.I1EventError):
        ie.append_event(bad, events_dir=events_dir)
    assert ie.read_events(events_dir=events_dir) == []


def test_bool_runnable_normalized_to_string(tmp_path: Path):
    events_dir = tmp_path / "i1"
    row = ie.append_event(_sample_event(runnable=True), events_dir=events_dir)
    assert row["runnable"] == "true"
    assert ie.read_events(events_dir=events_dir)[0]["runnable"] == "true"


def test_default_repo_dir_is_docs_evidence_i1():
    """约定目录落在仓内 docs/evidence/i1/(相对模块解析)。"""
    assert ie.default_events_dir().name == "i1"
    assert ie.default_events_dir().parent.name == "evidence"
    assert ie.default_events_dir().parent.parent.name == "docs"


def test_repo_sample_events_jsonl_roundtrip_readable():
    """仓内样例 events.jsonl 可读回且含最少字段 + 封闭枚举。"""
    rows = ie.read_events()
    assert len(rows) >= 1
    row = next(r for r in rows if r.get("sample_id") == "i1-s001")
    for key in REQUIRED:
        assert key in row
    assert row["fail_bucket"] in ie.FAIL_BUCKETS
    assert row["err_kind"] in ie.ERR_KINDS
    assert row["runnable"] in ie.RUNNABLES
    md_path = Path(__file__).resolve().parents[2] / row["evidence_md"]
    assert md_path.is_file()
    text = md_path.read_text(encoding="utf-8")
    assert "答辩" in text or "冒烟" in text
    assert "i1-s001" in text


def test_production_enums_not_extended_with_triad_buckets():
    """VALID_ACTIONS / DISPOSITIONS 不含三分法桶名。"""
    for bucket in TRIAD_BUCKETS:
        assert bucket not in VALID_ACTIONS
        assert bucket not in DISPOSITIONS
    # HumanLatch 仍只有 discard|renew
    assert VALID_ACTIONS == ("discard", "renew")
    # disposition 仍只有三值包结论
    assert DISPOSITIONS == frozenset({"可发", "需补丁", "勿发"})
