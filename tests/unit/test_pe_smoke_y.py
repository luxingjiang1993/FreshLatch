"""#529 PE-Y-SMOKE-01：SMOKE-Y-N30 冒烟报告（可扔 · 不作过门）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from freshlatch.eval import patch_events_smoke_y as smoke
from freshlatch.eval.patch_events_smoke_y import (
    analyze_smoke,
    build_synthetic_smoke_rows,
    firewall_sentence,
    fixed_k_claim_id_sets,
    render_smoke_y_n30_markdown,
    score_hygiene_report,
    smoke_n,
    write_smoke_y_n30_report,
)

_ROOT = Path(__file__).resolve().parents[2]
_RESULT_Y = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT-Y.md"
_PREREG_Y = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG-Y.md"
_SMOKE_REPORT = _ROOT / "docs" / "evidence" / "patch-events" / "SMOKE-Y-N30.md"


def test_smoke_n_and_firewall_locked():
    assert smoke_n() == 30
    text = firewall_sentence()
    assert "不" in text and "RESULT-Y" in text
    assert "gate_passed" in text
    assert "不保证乙" in text or "保证乙" in text


def test_synthetic_rows_have_four_arms_and_n30():
    rows = build_synthetic_smoke_rows(n=30, collapse=False)
    assert len(rows) == 30 * 4
    arms = {row["arm"] for row in rows}
    assert arms == {"C", "T", "B1", "B2"}
    ids = {row["claim_id"] for row in rows}
    assert len(ids) == 30


def test_analyze_smoke_reports_required_fields_and_firewall():
    rows = build_synthetic_smoke_rows(n=30, collapse=False)
    pack = analyze_smoke(rows)
    assert pack["layer"] == "冒烟"
    assert pack["n"] == 30
    assert isinstance(pack["k"], int) and pack["k"] > 0
    assert pack["t_c_direction"] in {"positive", "non_positive", "undefined"}
    assert set(pack["fixed_k_claim_ids"]) == {"T", "B1", "B2"}
    assert pack["collapse"] is False
    assert pack["stop"] is False
    assert pack["score_hygiene"]["ok"] is True
    # B1/B2 差点必须存在于分析里（可报 None，但键必须有）
    assert "t_b1_point" in pack and "t_b2_point" in pack
    # 防火墙写死
    assert pack["constitutes_gate_passed"] is False
    assert pack["enters_result_y"] is False
    assert pack["guarantees_yi"] is False
    assert pack["writes_population_ci"] is False


def test_collapse_true_stops():
    rows = build_synthetic_smoke_rows(n=30, collapse=True)
    pack = analyze_smoke(rows)
    assert pack["collapse"] is True
    assert pack["stop"] is True
    sets = pack["fixed_k_claim_ids"]
    assert sets["T"] == sets["B1"] == sets["B2"]
    # 坍缩仍不构成过门
    assert pack["constitutes_gate_passed"] is False


def test_score_hygiene_flags_none_in_pool():
    rows = build_synthetic_smoke_rows(n=4, collapse=False)
    # 污染一条 T release 的 score
    for row in rows:
        if row["arm"] == "T" and row["decision"] == "release":
            row["score"] = None
            break
    report = score_hygiene_report(rows)
    assert report["ok"] is False
    assert report["none_in_sortable_pool"]


def test_render_contains_required_sections_and_forbids_upgrade():
    rows = build_synthetic_smoke_rows(n=30, collapse=False)
    pack = analyze_smoke(rows)
    md = render_smoke_y_n30_markdown(
        pack, code_pin="test-pin", source_note="合成夹具"
    )
    assert "SMOKE-Y-N30" in md
    assert "**k**" in md or "k**" in md
    assert "collapse" in md
    assert "score 卫生" in md
    assert "T−B1" in md and "T−B2" in md
    assert "不过条件" in md or "不过门" in md or "进 gate_passed" in md
    assert firewall_sentence().split("；")[0] in md or "不进 RESULT-Y" in md
    assert "constitutes_gate_passed" in md
    assert "`False`" in md or "False" in md
    # 禁止升格
    compact = md.lower().replace(" ", "")
    assert "gate_passed=true" not in compact
    assert "保证乙" in md  # 出现在「不保证乙」
    assert "不保证乙" in md or "**不**保证乙" in md


def test_write_report_to_tmp_and_refuse_result_y(tmp_path: Path):
    out = tmp_path / "SMOKE-Y-N30.md"
    path, pack = write_smoke_y_n30_report(
        out,
        code_pin="unit",
        source_note="单测合成",
        root=tmp_path,
    )
    assert path == out
    text = out.read_text(encoding="utf-8")
    assert "collapse" in text
    assert pack["constitutes_gate_passed"] is False
    # 禁止写入 RESULT-Y / PREREG-Y（相对 root 的协议路径）
    forbidden = tmp_path / "docs" / "evidence" / "patch-events" / "RESULT-Y.md"
    with pytest.raises(RuntimeError, match="禁止写入"):
        write_smoke_y_n30_report(
            forbidden,
            rows=build_synthetic_smoke_rows(n=4),
            root=tmp_path,
        )


def test_checked_in_smoke_report_fields():
    """仓内可扔报告须含 Acceptance 必看字段；且未激活/未填成立格。"""
    assert _SMOKE_REPORT.is_file(), "须写出 docs/evidence/patch-events/SMOKE-Y-N30.md"
    text = _SMOKE_REPORT.read_text(encoding="utf-8")
    assert "k" in text
    assert "collapse" in text
    assert "score" in text or "score 卫生" in text
    assert "T−B1" in text and "T−B2" in text
    assert "gate_passed" in text
    assert "False" in text or "false" in text
    assert "RESULT-Y" in text
    assert "不保证乙" in text or "**不**保证乙" in text
    assert "总体" in text or "不写成总体" in text or "不**写成总体" in text
    # 未激活：若存在 PREREG-Y 则不得被本票改成已激活（本票默认不创建该文件）
    if _PREREG_Y.is_file():
        prereg = _PREREG_Y.read_text(encoding="utf-8")
        assert "未激活" in prereg or "状态：协议可锁" in prereg
    # 不得把成立格填成「成立」冒充乙
    assert "| 成立 |" not in text
    assert "乙成立" not in text or "不保证乙" in text


def test_fixed_k_sets_helper_matches_analyze():
    rows = build_synthetic_smoke_rows(n=12, collapse=False)
    pack = analyze_smoke(rows)
    sets = fixed_k_claim_id_sets(rows, k=pack["k"])
    assert sets == pack["fixed_k_claim_ids"]


def test_main_no_write(capsys):
    code = smoke.main(["--no-write"])
    assert code == 0
    out = capsys.readouterr().out
    assert "k=" in out
    assert "collapse=" in out
    assert "gate_passed=False" in out
