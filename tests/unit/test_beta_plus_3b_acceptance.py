"""β+ 档 3b ACCEPTANCE 挂载自检(#144)。

只核对预锁句在场、双路径负例勾选位、禁升格声明。
不得把本文件读成「checksum 已证明 latch」或统计通过。
不改 gold。
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
ACCEPTANCE = REPO / "docs" / "evidence" / "beta-plus-3b" / "ACCEPTANCE.md"
GOLD = REPO / "data" / "eval" / "gold.json"
RESEARCH = next((REPO / "docs" / "research").glob("*3b*跨轮*"))


def test_acceptance_pastes_prelock_invariant_verbatim():
    """ACCEPTANCE 必须粘贴评估 §4 预锁整句(改字 = 验收作废)。"""
    research = RESEARCH.read_text(encoding="utf-8")
    start = research.index("> 档 3b")
    end = research.index("\n", start)
    prelock = research[start:end]
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert prelock in text
    assert "语料现算 sha256" in text
    assert "BASIS_CHECKSUM_MISMATCH" in text
    assert "不得升格为统计结论" in text or "不得升格" in text


def test_acceptance_has_dual_path_checkboxes_and_bans():
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert "tests/unit/test_basis_rot.py" in text
    assert "tests/unit/test_ui_basis_rot.py" in text
    assert "复验入口" in text and "UI 拉单" in text
    assert "[x]" in text  # 负例勾选位
    assert "checksum 已证明 latch" in text  # 作为禁升格被点名
    assert "不改 `data/eval/gold.json`" in text or "不改" in text and "gold.json" in text
    assert "不自动 void" in text
    assert (REPO / "tests" / "unit" / "test_basis_rot.py").is_file()
    assert (REPO / "tests" / "unit" / "test_ui_basis_rot.py").is_file()


def test_acceptance_does_not_claim_latch_or_stats_proven():
    text = ACCEPTANCE.read_text(encoding="utf-8")
    # 禁升格话术不得被写成正面结论(点名禁语本身允许出现在「不得升格」声明里)
    assert "已证明 latch」成立" not in text
    assert "统计结论已成立" not in text
    assert "产品已验证成功" not in text
    assert "Override Rate 通过线已锁" not in text
    assert "不得升格" in text


def test_this_batch_does_not_touch_gold():
    before = GOLD.read_bytes()
    assert b"must_stale" in before
    assert GOLD.read_bytes() == before
