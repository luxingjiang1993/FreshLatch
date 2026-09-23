"""Batch 5 收口:对抗目录纪律 + 验收挂主缝/非缝。

目录存在 ≠ 仪器已过 / 对抗成立。本文件不报通过率,不锁 Override Rate,不改 gold。
禁止升格:override⇒模型变好;demo 可读⇒验证成功;目录⇒仪器已过。
"""

from __future__ import annotations

from pathlib import Path

from freshlatch.reading_source import ACCEPTANCE_SENTENCE

REPO = Path(__file__).resolve().parent.parent.parent
CATALOG = REPO / "docs" / "research" / "adversarial"
ACCEPTANCE = REPO / "docs" / "evidence" / "batch5" / "ACCEPTANCE.md"
GOLD = REPO / "data" / "eval" / "gold.json"


def test_catalog_skeleton_has_no_pass_rate():
    readme = (CATALOG / "README.md").read_text(encoding="utf-8")
    index = (CATALOG / "INDEX.md").read_text(encoding="utf-8")
    assert "catalog_version" in readme
    assert "0.1.0" in readme
    assert "0.1.0" in index
    assert "目录存在 ≠ 仪器已过" in readme
    assert "pass_rate" not in index.lower()
    for token in ("ATK-FG-01", "ATK-FG-02", "ATK-FG-03", "ATK-CS-01", "ATK-CS-04"):
        assert token in index
    assert "skeleton" in index


def test_acceptance_hangs_seam_copy_and_catalog():
    """Batch 5 验收同时挂主缝真值表、读法源预锁句与目录纪律。"""
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert ACCEPTANCE_SENTENCE in text
    assert "tests/unit/test_override_latch.py" in text
    assert "tests/unit/test_reading_source.py" in text
    assert "tests/unit/test_batch5_acceptance.py" in text
    assert "目录存在 ≠ 仪器已过" in text
    assert "pass_rate" in text  # 只作为禁列被点名,INDEX 本体不得出现该字样
    assert "不锁 Override Rate" in text
    assert "不改 `data/eval/gold.json`" in text
    assert "override⇒模型变好" in text
    assert "demo 可读 ⇒ 付费或验证成功" in text
    assert "文案在场 ⇒ 对抗仪器已过" in text
    assert (REPO / "tests" / "unit" / "test_override_latch.py").is_file()
    assert (REPO / "tests" / "unit" / "test_reading_source.py").is_file()


def test_acceptance_does_not_claim_catalog_or_demo_passed():
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert "对抗套件已通过" not in text
    assert "目录存在 = 仪器已过" not in text
    assert "override 表明模型变好" not in text
    assert "产品已验证成功" not in text


def test_this_batch_does_not_touch_gold_from_acceptance_runner():
    """本测试只读 gold 是否仍在,不改写。禁改 gold 凑绿。"""
    before = GOLD.read_bytes()
    assert b"must_stale" in before
    assert GOLD.read_bytes() == before
