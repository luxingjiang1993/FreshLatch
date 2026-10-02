"""I3 #252：ACCEPTANCE 文首层标签与三轨分节在场（文档契约）。"""

from pathlib import Path

ACC = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "i3" / "ACCEPTANCE.md"


def test_acceptance_layer_banner_and_three_tracks():
    body = ACC.read_text(encoding="utf-8")
    assert ACC.is_file()
    assert "层身份" in body
    assert "冒烟" in body and "面试加固" in body
    assert "不报方差" in body
    assert "不是改生产默认臂授权" in body
    assert "不是政策平台" in body
    assert "不是已修真生产事故" in body or "真生产事故" in body
    # 三轨分节
    assert "Policy-as-code" in body or "#8" in body
    assert "B′" in body or "B'" in body
    assert "Hard-Gold" in body
    assert "未授权改臂" in body
    assert "互不顶替" in body
    assert "test_i3_policy_gate.py" in body
    assert "test_i3_agent_hardening.py" in body
    assert "test_i3_hard_gold.py" in body
