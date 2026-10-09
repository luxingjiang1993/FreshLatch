"""#488/#490：RESULT-C 壳字段、B 附录句；成立格只许同一次主比较。"""

from __future__ import annotations

from pathlib import Path

from freshlatch.eval.patch_events_formal_c import prereg_c_activated

_RESULT_C = Path("docs/evidence/patch-events/RESULT-C.md")
_PREREG_C = Path("docs/evidence/patch-events/PREREG-C.md")
_RESULT_B = Path("docs/evidence/patch-events/RESULT-B.md")


def test_result_c_exists_and_keeps_b_negative_appendix():
    """文面含 B 负结果附录固定引用句（#480 丙 · 效应偏小）。"""
    assert _RESULT_C.is_file()
    assert _PREREG_C.is_file()
    text = _RESULT_C.read_text(encoding="utf-8")
    assert "PREREG-C" in text
    assert "formal-generations-c.jsonl" in text
    for label in ("T 对 C", "T 对 B1", "T 对 B2"):
        assert label in text
    assert "#480" in text
    assert "结果丙" in text
    assert "效应偏小" in text
    assert "PREREG-B" in text or "RESULT-B" in text


def test_result_b_archive_untouched_by_c_paths():
    """禁止改 B 归档：RESULT-B 仍为路线 B 丙抄表。"""
    text = _RESULT_B.read_text(encoding="utf-8")
    assert "路线 B" in text or "RESULT-B" in text
    assert "k** = 42" in text or "k** =42" in text or "= 42" in text


def test_prereg_c_activation_line_locked():
    assert prereg_c_activated() is True
    head = "\n".join(_PREREG_C.read_text(encoding="utf-8").splitlines()[:8])
    assert "冲甲正式主跑已激活" in head
    assert "未激活" not in head


def test_result_c_formal_fill_is_prop_not_jia():
    """#490 一次主跑抄表：结果丙；成立格非未跑；含 k 与 generations-c 针。"""
    text = _RESULT_C.read_text(encoding="utf-8")
    assert "结果丙" in text
    assert "不得称甲" in text or "不保证甲" in text
    assert "**固定放行数 k** = 93" in text
    assert "formal-generations-c.jsonl" in text
    assert "n_lines=400" in text
    assert "| T 对 C | false-accept rate | 未跑 |" not in text
    assert "gate_passed" not in text.lower()
    # B 附录史实 k=42 可在附录出现，但不得冒充 C 成立格
    assert "k=42" in text
    assert "**固定放行数 k** = 93" in text
