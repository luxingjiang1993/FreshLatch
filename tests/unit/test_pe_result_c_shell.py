"""#488：RESULT-C 抄表壳与 B 负结果附录句；未激活不得填成立格。"""

from __future__ import annotations

from pathlib import Path

from freshlatch.eval.patch_events_formal_c import prereg_c_activated

_RESULT_C = Path("docs/evidence/patch-events/RESULT-C.md")
_PREREG_C = Path("docs/evidence/patch-events/PREREG-C.md")


def test_result_c_shell_fields_align_prereg_and_stay_unrun():
    """壳字段与 PREREG-C 对齐；成立格保持未跑。"""
    assert _RESULT_C.is_file()
    assert _PREREG_C.is_file()
    assert prereg_c_activated() is False
    text = _RESULT_C.read_text(encoding="utf-8")
    assert "PREREG-C" in text
    assert "未激活" in text
    assert "formal-generations-c.jsonl" in text
    # 三行主比较成立格不得手填数字
    for label in ("T 对 C", "T 对 B1", "T 对 B2"):
        assert label in text
    assert "| T 对 C | false-accept rate | 未跑 |" in text
    assert "| T 对 B1 | false-accept rate | 未跑 |" in text
    assert "| T 对 B2 | false-accept rate | 未跑 |" in text
    assert "**固定放行数 k** = 未跑" in text
    # 禁止把 GATE/B 探针数字冒充成立
    assert "gate_passed" not in text.lower()
    assert "GATE-K-PROBE" not in text or "禁止" in text


def test_result_c_contains_b_negative_appendix_fixed_quote():
    """文面含 B 负结果附录固定引用句（#480 丙 · 效应偏小）。"""
    text = _RESULT_C.read_text(encoding="utf-8")
    assert "#480" in text
    assert "结果丙" in text
    assert "效应偏小" in text
    assert "PREREG-B" in text or "RESULT-B" in text
    # 附录不得写成 C 成立格数字
    assert "k=42" in text  # B 史实附录可引用
    assert "**固定放行数 k** = 未跑" in text  # C 成立格仍未跑
