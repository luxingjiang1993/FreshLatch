"""主链抗假绿预登记红线单测(零 LLM):锁定件存在且关键字面未被漂改。

预登记:docs/evidence/w4/main-chain-anti-false-green-prereg.md(决议 #82 / 落盘 #84)。
本测不跑主链、不改 C / gold。
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PREREG = REPO_ROOT / "docs" / "evidence" / "w4" / "main-chain-anti-false-green-prereg.md"

# 锁定字面(与预登记 / #82 拍板一致;漂移 = 红线)
LOCKED_CLI = (
    "python -m freshlatch.eval run --gold data/eval/gold.json "
    "--runs 3 --temperature 0.0"
)
LOCKED_CLAIMS = ("c1", "c2", "c3", "c7")
SUCCESS_CITE_NEEDLES = (
    "must_stale（c1/c2/c3/c7）判 fresh 合计为 0",
    "以假绿仪器 C 对照成立为假绿可诱导前提",
    "不是产品已愈假绿的统计证明",
)
FAIL_CITE_NEEDLES = (
    "判 fresh 合计为 {k}>0",
    "不得放宽 fresh=0 通过线",
    "失败处置走修窗",
)
def test_prereg_file_exists_and_lock_banner():
    text = PREREG.read_text(encoding="utf-8")
    assert "锁定语" in text
    assert "ADR-0007" in text
    assert "HARKing" in text


def test_prereg_locks_claims_decoding_cli_and_pass_line():
    text = PREREG.read_text(encoding="utf-8")
    for cid in LOCKED_CLAIMS:
        assert cid in text
    assert "temperature | `0.0`" in text or "temperature | `0`" in text or "`0.0`" in text
    assert "n=3" in text
    assert "`qwen-flash`" in text
    assert LOCKED_CLI in text
    assert "must_stale→fresh` **合计 = 0**" in text or "must_stale→fresh **合计 = 0**" in text
    assert "run_gold" in text
    assert "control-c" in text  # 须显式禁止冒充


def test_prereg_locks_cite_templates():
    text = PREREG.read_text(encoding="utf-8")
    for needle in SUCCESS_CITE_NEEDLES:
        assert needle in text, f"成功仅表明句缺失: {needle}"
    for needle in FAIL_CITE_NEEDLES:
        assert needle in text, f"失败仅表明句缺失: {needle}"


def test_prereg_forbids_mutating_c_and_gold():
    text = PREREG.read_text(encoding="utf-8")
    assert "冻结只读" in text or "不改不删" in text
    assert "CONTROL_PROMPT_C" in text
    assert "不改 `gold.json`" in text or "不改了 `gold.json`" in text or "改了 `gold.json`" in text
    assert "不授权" in text
