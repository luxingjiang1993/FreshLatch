"""#185 I1 重标语料契约:≥3 条 err_kind×fail_bucket + 短索引互指 + 轨迹锚存在。

零 LLM、零网络;只读 docs/evidence/i1 与既有轨迹/对照路径。
"""

from __future__ import annotations

from pathlib import Path

from freshlatch import i1_events as ie
from freshlatch.disposition import DISPOSITIONS
from freshlatch.gates.human_latch import VALID_ACTIONS

REPO = Path(__file__).resolve().parents[2]
I1_DIR = REPO / "docs" / "evidence" / "i1"
INDEX = I1_DIR / "INDEX.md"
VOID_CONTROL = REPO / "docs" / "evidence" / "w4" / "false-green-control.md"

# 作废假绿原始摘录——仅允许作 replay 挂标锚,不得当「有效对照读数」叙事源
VOID_MARKER = "作废"


def test_corpus_at_least_three_rows_with_err_kind_and_fail_bucket():
    """Given events.jsonl,When 统计双字段齐全行,Then ≥3。"""
    rows = ie.read_events()
    labeled = [
        r
        for r in rows
        if r.get("err_kind") in ie.ERR_KINDS and r.get("fail_bucket") in ie.FAIL_BUCKETS
    ]
    assert len(labeled) >= 3
    sample_ids = {r["sample_id"] for r in labeled}
    for sid in ("i1-s001", "i1-s002", "i1-s003"):
        assert sid in sample_ids


def test_index_lists_sample_ids_and_each_evidence_has_smoke_banner():
    """短索引列出 sample_id;每条 evidence 页文首含答辩/冒烟。"""
    text = INDEX.read_text(encoding="utf-8")
    assert "答辩" in text or "冒烟" in text
    rows = [
        r
        for r in ie.read_events()
        if r.get("err_kind") in ie.ERR_KINDS and r.get("fail_bucket") in ie.FAIL_BUCKETS
    ]
    assert len(rows) >= 3
    for row in rows:
        sid = row["sample_id"]
        assert sid in text
        assert f"{row['err_kind']}" in text
        assert f"{row['fail_bucket']}" in text
        md = REPO / row["evidence_md"]
        assert md.is_file(), row["evidence_md"]
        body = md.read_text(encoding="utf-8")
        assert "答辩" in body or "冒烟" in body
        assert sid in body
        assert row["err_kind"] in body
        assert row["fail_bucket"] in body


def test_each_sample_trajectory_ptr_resolves_and_void_not_valid_source():
    """trajectory_ptr 指向仓内既有文件;作废假绿页若被引用须带作废印且样例声明非有效源。"""
    rows = ie.read_events()
    labeled = [
        r
        for r in rows
        if r.get("err_kind") in ie.ERR_KINDS and r.get("fail_bucket") in ie.FAIL_BUCKETS
    ]
    assert len(labeled) >= 3
    void_rel = str(VOID_CONTROL.relative_to(REPO)).replace("\\", "/")
    for row in labeled:
        ptr = row["trajectory_ptr"].replace("\\", "/")
        path = REPO / ptr
        assert path.is_file(), f"缺失轨迹/对照锚: {ptr}"
        if ptr == void_rel or path.resolve() == VOID_CONTROL.resolve():
            # 作废页可作挂标锚,但 evidence 页须声明不作有效对照读数
            stamp = VOID_CONTROL.read_text(encoding="utf-8")
            assert VOID_MARKER in stamp
            md = (REPO / row["evidence_md"]).read_text(encoding="utf-8")
            assert "有效" in md and ("不作" in md or "不把" in md or "升格" in md or "不可" in md)


def test_production_enums_still_untouched_after_relabel():
    """重标语料不得扩生产封闭集。"""
    for bucket in ("找不到", "找错", "没用上"):
        assert bucket not in VALID_ACTIONS
        assert bucket not in DISPOSITIONS
    assert VALID_ACTIONS == ("discard", "renew")
    assert DISPOSITIONS == frozenset({"可发", "需补丁", "勿发"})
