"""#217：security.md 硬表三行 + i2 短索引。不测 LLM，不改过滤实现。"""

from pathlib import Path

SECURITY = Path("docs/security.md")
INDEX = Path("docs/evidence/i2/INDEX.md")
ADVERSARIAL = Path("docs/research/adversarial/INDEX.md")

COLUMNS = ("threat", "demo_id", "layer", "repro_cmd", "expected", "smoke_note")
HARD_IDS = ("acl-t001", "inj-t001", "poison-t001")


def _hard_section(text: str) -> str:
    head, _, _rest = text.partition("## 可选")
    return head


def test_security_md_exists_with_three_hard_rows():
    """硬表三行齐全，含规定列，并声明冒烟层。"""
    text = SECURITY.read_text(encoding="utf-8")
    hard = _hard_section(text)
    assert "冒烟" in hard
    assert "不是渗透认证" in hard
    for column in COLUMNS:
        assert column in hard
    for demo_id in HARD_IDS:
        assert demo_id in hard
    assert "adv-fresh-t001" not in hard
    assert "不计入 I2 Exit" in text
    assert "adv-fresh-t001" in text


def test_i2_index_points_at_three_demos():
    """短索引链到三例；#4 只出现在可选节。"""
    text = INDEX.read_text(encoding="utf-8")
    hard = _hard_section(text)
    assert "冒烟" in hard
    assert "acl-t001.json" in hard
    assert "inj-t001.md" in hard
    assert "poison-t001.json" in hard
    for demo_id in HARD_IDS:
        assert demo_id in hard
    assert "adv-fresh-t001" not in hard
    assert "不计入 I2 Exit" in text
    assert "adv-fresh-t001.md" in text


def test_security_pages_do_not_bump_adversarial_index():
    """本票不把对抗目录升版写成 I2 Done。"""
    text = ADVERSARIAL.read_text(encoding="utf-8")
    assert "**catalog_version**: `0.1.0`" in text
    assert "adv-fresh-t001" not in text
    assert "acl-t001" not in text
