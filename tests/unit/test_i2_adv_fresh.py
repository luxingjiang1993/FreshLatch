"""可选 #4：adv-fresh-t001 一条。不计入 I2 Exit，不升 adversarial INDEX。"""

from pathlib import Path

from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import Claim

PAGE = Path("docs/evidence/i2/adv-fresh-t001.md")
INDEX = Path("docs/research/adversarial/INDEX.md")
ACCEPTANCE = Path("docs/evidence/i2/ACCEPTANCE.md")

CLAIM_TEXT = "竞品席位标价仍为 120 元每月。"
T1_EXCERPT = "席位标价已改为 80 元每月。120 元标价被本快照取代。"
EXPIRED_CHECKSUM = "expired-t0-basis"
CURRENT_CHECKSUM = "t1-current-basis"


def test_adv_fresh_t001_page_exists_and_not_exit():
    """证据页存在，写明不计入 I2 Exit，并指出拦层。"""
    text = PAGE.read_text(encoding="utf-8")
    assert "adv-fresh-t001" in text
    assert "不计入 I2 Exit" in text
    assert "I2 ≠ #4" in text
    assert CLAIM_TEXT in text
    assert T1_EXCERPT in text
    assert "rule_gate" in text
    assert "CHECKSUM_MISMATCH" in text
    assert "catalog_version" in text


def test_adv_fresh_t001_blocked_at_rule_gate_checksum():
    """过期 checksum 伪装 fresh，被规则闸 checksum 项拦住，不发绿。"""
    claim = Claim(claim_id="adv-fresh-t001", statement=CLAIM_TEXT)
    decision = GateDecision(
        status="fresh",
        t1_evidence_ids=["adv-fresh-t001#p1@T1"],
        validity_basis={"doc_id": "adv-fresh-t001", "checksum": EXPIRED_CHECKSUM},
        auditor_verdict="fresh",
    )

    def checksum_fn(doc_id: str, as_of: str) -> str | None:
        if doc_id == "adv-fresh-t001" and as_of == "T1":
            return CURRENT_CHECKSUM
        return None

    result = rule_gate(claim, decision, GateContext(checksum_fn=checksum_fn))
    assert result.allowed is False
    assert result.green is False
    assert result.error_code == "CHECKSUM_MISMATCH"


def test_adv_fresh_does_not_bump_adversarial_index():
    """INDEX 仍是骨架 0.1.0，本条不写进目录、不宣称升版即 Done。"""
    text = INDEX.read_text(encoding="utf-8")
    assert "**catalog_version**: `0.1.0`" in text
    assert "adv-fresh-t001" not in text
    assert "I2 Done" not in text


def test_hard_exit_does_not_depend_on_adv_fresh():
    """ACCEPTANCE 若尚未落盘则跳过正文；若已存在，硬勾不得把本条写成必过。"""
    if not ACCEPTANCE.exists():
        return
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert "不计入 I2 Exit" in text or "可选" in text
    hard, _, optional = text.partition("可选")
    assert "adv-fresh-t001" not in hard
