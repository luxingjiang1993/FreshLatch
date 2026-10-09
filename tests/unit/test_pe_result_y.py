"""PE-Y-04：RESULT-Y 抄表口径（仅 T−C · 禁甲）。"""

from __future__ import annotations

from pathlib import Path

from freshlatch.eval.patch_events_formal_y import (
    outcome_tier,
    outcome_tier_y,
    render_result_y,
    tc_established_y,
    verdict_sentence,
)

ROOT = Path(__file__).resolve().parents[2]
RESULT_Y = ROOT / "docs" / "evidence" / "patch-events" / "RESULT-Y.md"
FORBIDDEN_FILL_SOURCES = (
    ROOT / "docs" / "evidence" / "patch-events" / "RESULT-B.md",
    ROOT / "docs" / "evidence" / "patch-events" / "GATE-K-PROBE.md",
)


def _cmp(
    name: str,
    *,
    point: float,
    low: float,
    high: float = 0.5,
    established: bool | None = None,
) -> dict:
    """伪造 compare_primary 单行。established 可与 Y 尺脱钩（只读消费、不改写）。"""
    if established is None:
        # 经典尺：point>0 且 low>0（与 metrics.compare_primary 一致）
        established = point > 0 and low > 0
    return {
        "name": name,
        "point": point,
        "ci95_low": low,
        "ci95_high": high,
        "established": established,
    }


def test_point_004_classic_pass_is_bing_not_yi_or_jia():
    """Acceptance: T−C 点=0.04 且下界>0，三行经典过 → 丙（非乙、非甲）。"""
    primary = {
        "k": 40,
        "comparisons": [
            _cmp("T-C", point=0.04, low=0.01, established=True),
            _cmp("T-B1", point=0.08, low=0.02, established=True),
            _cmp("T-B2", point=0.07, low=0.01, established=True),
        ],
    }
    # 经典 established 三行均 True，但 Y 尺点地板卡住
    assert all(row["established"] is True for row in primary["comparisons"])
    assert tc_established_y(primary["comparisons"][0]) is False
    assert outcome_tier(primary) == "丙"
    assert outcome_tier_y(primary) == "丙"
    assert outcome_tier(primary) not in ("乙", "甲")
    text = verdict_sentence("丙", primary)
    assert "结果丙" in text
    assert "结果甲" not in text
    assert "结果乙" not in text
    assert "称甲" not in text


def test_only_tc_passes_y_floor_is_yi_render_forbids_jia():
    """Acceptance: 仅 T−C 点=0.06 且下界>0，B1/B2 下界≤0 → 乙；文面无结果甲/称甲。"""
    primary = {
        "k": 55,
        "comparisons": [
            _cmp("T-C", point=0.06, low=0.01, established=True),
            _cmp("T-B1", point=0.02, low=-0.01, established=False),
            _cmp("T-B2", point=0.0, low=0.0, established=False),
        ],
    }
    assert outcome_tier_y(primary) == "乙"
    assert outcome_tier(primary) == "乙"
    verdict = verdict_sentence("乙", primary)
    pack = {
        "primary": primary,
        "b2_count": 400,
        "n": 400,
        "tier": "乙",
        "verdict": verdict,
        "generations_n": 1200,
        "generations_sha256": "deadbeef",
        "decoding": {
            "model": "qwen-flash",
            "temperature": 0,
            "decoding_seed": 20261007,
            "api_seed": None,
        },
    }
    md = render_result_y(pack, code_pin="test-pin", activated_note="单测伪造 primary")
    assert "结果乙" in md
    assert "结果甲" not in md
    assert "称甲" not in md
    assert "报告-only（不参与成立）" in md
    # T−C 按 Y 尺成立；B1/B2 不参与
    assert "| T 对 C | false-accept rate |" in md
    assert "成立" in md
    assert md.count("报告-only（不参与成立）") == 2


def test_copies_only_forged_primary_never_gate_bc_paths():
    """Acceptance: 只消费同一次 primary dict；禁止从 GATE/B/C 路径读数写入成立格。"""
    primary = {
        "k": 12,
        "comparisons": [
            _cmp("T-C", point=0.11, low=0.02),
            _cmp("T-B1", point=-0.01, low=-0.05),
            _cmp("T-B2", point=0.03, low=-0.02),
        ],
    }
    for path in FORBIDDEN_FILL_SOURCES:
        assert path.is_file()
    pack = {
        "primary": primary,
        "b2_count": 400,
        "n": 400,
        "tier": outcome_tier_y(primary),
        "verdict": verdict_sentence(outcome_tier_y(primary), primary),
        "generations_n": 1,
        "generations_sha256": "abc",
        "decoding": {},
    }
    md = render_result_y(pack, code_pin="x", activated_note="y")
    # 数字来自伪造 primary，不是 B/C 附录主数字冒充成立格
    assert "0.11" in md
    before_appendix = md.split("## B / C 负结果附录")[0]
    assert "GATE-K-PROBE" not in before_appendix
    # 附录动机句可保留 B/C 负结果，但不写入 T−C 成立数字格为 B 的 −0.05556
    table = [line for line in md.splitlines() if line.startswith("| T 对 C |")][0]
    assert "−0.05556" not in table and "-0.05556" not in table
    assert "0.1190476" not in table


def test_result_y_shell_keeps_blank_and_bc_appendix():
    """Acceptance: RESULT-Y.md 保留 B/C 负结果附录；未主跑成立格保持未填。"""
    text = RESULT_Y.read_text(encoding="utf-8")
    assert "未激活" in text or "未跑" in text
    assert "| T 对 C | false-accept rate | 未填 | 未填 | 未填 | 未填 |" in text
    assert "报告-only（不参与成立）" in text
    assert "路线 B（#480）" in text
    assert "路线 C" in text
    assert "不得" in text and "判甲" in text


def test_jia_firewall_never_returns_jia():
    """即便三行经典均成立且点>0.05，分层仍不得甲。"""
    primary = {
        "k": 20,
        "comparisons": [
            _cmp("T-C", point=0.12, low=0.03, established=True),
            _cmp("T-B1", point=0.09, low=0.02, established=True),
            _cmp("T-B2", point=0.08, low=0.01, established=True),
        ],
    }
    assert outcome_tier_y(primary) == "乙"
    assert outcome_tier_y(primary) != "甲"
    # 误传 tier=甲 时文案仍降为丙且无「结果甲」「称甲」
    forced = verdict_sentence("甲", primary)
    assert "结果甲" not in forced
    assert "称甲" not in forced
    assert "结果丙" in forced
