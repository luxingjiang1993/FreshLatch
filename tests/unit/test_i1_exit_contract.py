"""#188 I1 Exit 契约:短索引计数门槛 + ACCEPTANCE 冒烟口径 + 贡献清单 + 生产枚举未扩。

层=答辩/冒烟。零 LLM、零网络。不报方差。
生产 Gate / disposition / HumanLatch 枚举只读断言,不改定义。
"""

from __future__ import annotations

from pathlib import Path

from freshlatch import i1_events as ie
from freshlatch.disposition import DISPOSITIONS
from freshlatch.gates.human_latch import VALID_ACTIONS
from freshlatch.gates.rule_gate import GREEN_STATUSES

REPO = Path(__file__).resolve().parents[2]
I1_DIR = REPO / "docs" / "evidence" / "i1"
INDEX = I1_DIR / "INDEX.md"
ACCEPTANCE = I1_DIR / "ACCEPTANCE.md"
BOUNDARY = REPO / "docs" / "contribution-boundary.md"

# 三分法与漏拦/误拦——不得进入生产封闭集
TRIAD_AND_ERR = ("找不到", "找错", "没用上", "漏拦", "误拦")


def _labeled_rows() -> list[dict]:
    """漏拦/误拦且三分法桶齐全的账本行。"""
    return [
        r
        for r in ie.read_events()
        if r.get("err_kind") in ie.ERR_KINDS and r.get("fail_bucket") in ie.FAIL_BUCKETS
    ]


def test_short_index_glance_miss_false_ge_3_and_runnable_true_ge_1():
    """Given 短索引 + events.jsonl,When 计数,Then 漏/误 ≥3 且 runnable=true ≥1,且一眼句与账本一致。"""
    labeled = _labeled_rows()
    runnable_true = [r for r in labeled if r.get("runnable") == "true"]
    assert len(labeled) >= 3
    assert len(runnable_true) >= 1
    assert any(r.get("sample_id") == "i1-s005" for r in runnable_true)

    text = INDEX.read_text(encoding="utf-8")
    assert "冒烟" in text
    assert "不报方差" in text
    assert "≥3" in text
    assert "≥1" in text
    assert "runnable=true" in text
    # 一眼句锁当前清点,防索引与账本漂移
    assert f"漏拦/误拦 **{len(labeled)}** 条" in text
    assert f"`runnable=true` **{len(runnable_true)}** 条" in text
    assert "`i1-s005`" in text
    for row in labeled:
        assert row["sample_id"] in text
        assert row["err_kind"] in text
        assert row["fail_bucket"] in text


def test_acceptance_opens_with_smoke_and_points_at_index_and_gold():
    """Given ACCEPTANCE.md,When 打开,Then 文首冒烟、指向索引与金样,且无方差/统计显著声明。"""
    text = ACCEPTANCE.read_text(encoding="utf-8")
    head = "\n".join(text.splitlines()[:6])
    assert "冒烟" in head
    assert "不报方差" in head
    assert "INDEX.md" in text
    assert "i1-s005" in text
    assert "events.jsonl" in text
    assert "不作统计显著" in text
    # 禁升格:不得把本批写成统计结论
    assert "统计显著优于" not in text
    assert "标准差" not in text
    assert "置信区间" not in text
    lowered = text.lower()
    assert "p-value" not in lowered
    assert "p<" not in lowered
    assert "p <" not in lowered


def test_contribution_boundary_i1_row_names_triad_corpus_and_smoke():
    """Given 贡献清单,When 查 I1 行,Then 含失败三分法句并带冒烟口径。"""
    text = BOUNDARY.read_text(encoding="utf-8")
    i1_rows = [ln for ln in text.splitlines() if ln.startswith("| I1 |")]
    assert len(i1_rows) == 1
    row = i1_rows[0]
    assert "失败三分法 + 可复盘误判样本" in row
    assert "冒烟" in row
    assert "不报方差" in row
    assert "ACCEPTANCE.md" in text


def test_production_enums_not_extended():
    """只读:Gate / disposition / HumanLatch 封闭集未被三分法或漏拦/误拦扩写。"""
    assert VALID_ACTIONS == ("discard", "renew")
    assert DISPOSITIONS == frozenset({"可发", "需补丁", "勿发"})
    assert GREEN_STATUSES == ("fresh", "renew")
    for name in TRIAD_AND_ERR:
        assert name not in VALID_ACTIONS
        assert name not in DISPOSITIONS
        assert name not in GREEN_STATUSES
