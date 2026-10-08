"""#466 复测协议：门闩可扔报告（默认零 LLM · 不激活）。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_gate_retest import (
    gate_conditions,
    main,
    render_full_retest_markdown,
    run_readonly_retest,
)
from freshlatch.eval.patch_events_formal import generations_path

_GENERATIONS_SHA256 = (
    "36b79124f2102e7d033a65aedf9b3f7ce54d6c9ade2291b15c60a72ac764093b"
)


def test_readonly_retest_zero_llm_and_gate_not_passed(monkeypatch):
    """只读旧生成 + #467 同 after：T−B1/T−B2 差为正，k=3<10 ⇒ 未过门。"""
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    path = generations_path()
    assert path.is_file()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 150

    pack = run_readonly_retest()
    assert pack["generations_sha256"] == _GENERATIONS_SHA256
    assert pack["b2_count"] == 30
    gate = pack["gate"]
    assert gate["k"] == 3
    assert gate["t_b1_positive"] is True
    assert gate["t_b2_positive"] is True
    assert gate["k_ok"] is False
    assert gate["passed"] is False

    t_ids = [r["claim_id"] for r in pack["arms"]["T"] if r["decision"] == "release"]
    b1_ids = [r["claim_id"] for r in pack["arms"]["B1"] if r["decision"] == "release"]
    assert sorted(t_ids) == ["c006", "c010", "d009"]
    assert "b007" in b1_ids
    assert "b007" not in t_ids
    # 同 after
    for left, right in zip(pack["arms"]["T"], pack["arms"]["B1"], strict=True):
        assert left["after_text"] == right["after_text"]

    primary = pack["primary"]
    assert primary is not None
    assert primary["arms"]["T"]["fixed"]["误放率"] == 0.0
    assert primary["arms"]["B1"]["fixed"]["误放率"] == pytest.approx(1 / 3)
    assert primary["arms"]["B2"]["fixed"]["误放率"] == pytest.approx(2 / 3)

    md = render_full_retest_markdown(
        pack,
        code_pin="test",
        baseline_note="cursor/467-tb1-shared-after-gate-fork-174d",
    )
    assert "可扔" in md and "未激活" in md and "复测" in md
    assert "不进主表" in md and "非甲" in md
    assert "不得建议激活" in md
    assert "不得**升格" in md or "不得升格" in md
    assert gate_conditions(primary)["passed"] is False


def test_main_no_write_exits_zero(monkeypatch, capsys):
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    assert main(["--no-write"]) == 0
    out = capsys.readouterr().out
    assert "gate_passed=False" in out
    assert "k=3" in out
