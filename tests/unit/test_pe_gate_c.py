"""#486：GATE-C 可扔门闩报告 + 过/不过夹具；禁升格 #479。"""

from __future__ import annotations

from pathlib import Path

import pytest

from freshlatch.eval.patch_events_gate_c import (
    activation_advice,
    ban_promote_gate_k_probe_sentences,
    gate_c_pass_criteria,
    main,
    render_gate_c_markdown,
    run_gate_c_fixture,
    write_gate_c_report,
)


def test_criteria_locked_and_ban_479():
    criteria = gate_c_pass_criteria()
    assert len(criteria) == 3
    assert any("k ≥ 10" in c for c in criteria)
    assert any("T−B1" in c for c in criteria)
    assert any("T−B2" in c for c in criteria)
    bans = ban_promote_gate_k_probe_sentences()
    assert any("#479" in s and "GATE-K-PROBE" in s for s in bans)
    assert any("不得" in s or "禁止" in s for s in bans)


def test_fixture_pass_and_fail_branches():
    passed = run_gate_c_fixture("pass")
    failed = run_gate_c_fixture("fail")
    assert passed["layer"] == "fixture"
    assert passed["gate_passed"] is True
    assert passed["gate"]["k_ok"] is True
    assert passed["gate"]["t_b1_positive"] is True
    assert passed["gate"]["t_b2_positive"] is True
    assert passed["sent_model"] is False
    assert failed["gate_passed"] is False
    assert failed["gate"]["k_ok"] is False
    # 同 after 绑定缝在 pass 夹具上可观测
    t_decisions = {r["claim_id"]: r["decision"] for r in passed["arms"]["T"]}
    b1_decisions = {r["claim_id"]: r["decision"] for r in passed["arms"]["B1"]}
    assert t_decisions["bad-unbound-00"] == "reject"
    assert b1_decisions["bad-unbound-00"] == "release"


def test_report_markdown_firewall_and_advice():
    pack = run_gate_c_fixture("pass")
    md = render_gate_c_markdown(pack, code_pin="test-pin")
    assert "可扔" in md and "非甲" in md and "不进主表" in md
    assert "RESULT-C" in md
    assert "#479" in md and "GATE-K-PROBE" in md
    assert "强制抄句" in md
    assert "gate_passed" in md
    assert "不得激活" in activation_advice(False)
    assert "不" in activation_advice(True) and "PREREG-C" in activation_advice(True)


def test_write_refuses_result_c_path(tmp_path):
    pack = run_gate_c_fixture("fail")
    with pytest.raises(RuntimeError, match="RESULT-C"):
        write_gate_c_report(
            pack,
            code_pin="t",
            path=tmp_path / "docs" / "evidence" / "patch-events" / "RESULT-C.md",
            root=tmp_path,
        )


def test_default_main_writes_fixture_report_zero_llm(monkeypatch, capsys):
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    code = main(["--code-pin", "unit-486"])
    assert code == 0
    out = capsys.readouterr().out
    assert '"pass"' in out and '"fail"' in out
    assert "gate_passed" in out
    report = Path("docs/evidence/patch-events/GATE-C-FIXTURE.md")
    assert report.is_file()
    text = report.read_text(encoding="utf-8")
    assert "可扔" in text
    assert "#479" in text
    assert "unit-486" in text
    # 门闩夹具不得改激活态语义：报告仍标明可扔；激活由人令另票
    assert "可扔" in text


def test_gate_c_report_must_not_be_promoted_into_result_c_path():
    """门闩模块禁止写入 RESULT-C；夹具绿 ≠ 成立格。"""
    result_c = Path("docs/evidence/patch-events/RESULT-C.md").read_text(encoding="utf-8")
    # 成立格不得出现 gate_passed 字样冒充甲
    assert "gate_passed" not in result_c.lower()
    assert "#480" in result_c and "效应偏小" in result_c
    # 激活态由 #490 人令管理；本断言只锁「门闩页仍可扔」
    fixture = Path("docs/evidence/patch-events/GATE-C-FIXTURE.md").read_text(
        encoding="utf-8"
    )
    assert "可扔" in fixture and "非甲" in fixture
