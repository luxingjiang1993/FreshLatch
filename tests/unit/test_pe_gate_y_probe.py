"""GATE-Y-PROBE：过门仅 k∧T−C；B1/B2 只报；默认不发；无探针人令拒发。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_formal import generations_path, load_pe_v2_formal_n30
from freshlatch.eval.patch_events_gate_y_probe import (
    _AWAITING,
    _FORBIDDEN_PASS_EVIDENCE,
    _PROBE_AUTH_PHRASE,
    _PROBE_GENERATIONS_REL,
    decoding_pin,
    gate_pass_criteria,
    gate_y_conditions,
    main,
    probe_auth_ok,
    probe_auth_phrase,
    probe_claim_ids,
    probe_requests,
    render_gate_y_probe_markdown,
    run_probe_recompute,
    send_probe_generations,
    write_probe_report,
)
from freshlatch.eval.patch_events_verify import verify_edit


def _synthetic_generations(*, mode: str) -> list[dict]:
    """构造旁路生成。

    mode=pass → T 对齐 evidence、C 任意 after ⇒ 通常 k≥10 且 T−C>0。
    mode=fail_low_k → T after 核验失败 ⇒ k 压低，gate_passed=false。
    """
    rows = load_pe_v2_formal_n30()
    lines: list[dict] = []
    for row in rows:
        cid = row["claim_id"]
        ev = str(row["evidence_text"])
        gold = row["construction_gold"]
        if mode == "pass":
            t_after = ev
            c_after = f"c-after-{cid}"
        elif mode == "fail_low_k":
            # T 核验不过 → 自然放行压低；C/B2 仍可报差（只报告）
            t_after = f"broken-t-{cid}"
            c_after = f"c-after-{cid}"
        else:
            raise ValueError(mode)
        lines.append(
            {
                "claim_id": cid,
                "arm": "C",
                "phase": "rewrite",
                "output_field": "after_text",
                "text": c_after,
                "model": "qwen-flash",
                "temperature": 0,
            }
        )
        lines.append(
            {
                "claim_id": cid,
                "arm": "T",
                "phase": "rewrite",
                "output_field": "after_text",
                "text": t_after,
                "model": "qwen-flash",
                "temperature": 0,
            }
        )
        lines.append(
            {
                "claim_id": cid,
                "arm": "B2",
                "phase": "claim",
                "output_field": "claim_text",
                "text": f"b2-claim-{cid}",
                "model": "qwen-flash",
                "temperature": 0,
            }
        )
        lines.append(
            {
                "claim_id": cid,
                "arm": "B2",
                "phase": "diff",
                "output_field": "after_text",
                "text": ev if gold == "正确" else f"bad-diff-{cid}",
                "model": "qwen-flash",
                "temperature": 0,
            }
        )
    return lines


def test_protocol_locked_y_criteria_and_layer():
    criteria = gate_pass_criteria()
    assert any("k ≥ 10" in item for item in criteria)
    assert any("T−C" in item for item in criteria)
    assert not any("T−B1" in item for item in criteria)
    assert not any("T−B2" in item for item in criteria)
    assert probe_auth_phrase() == _PROBE_AUTH_PHRASE
    md = render_gate_y_probe_markdown(
        code_pin="test",
        baseline_note="test-baseline",
        authorize_send=False,
        send_result=None,
        probe_pack={
            "status": "no_probe_generations",
            "gate": {"passed": False, "k": None, "comparisons": {}},
        },
        readonly_pack=None,
    )
    assert "可扔" in md and "非乙成立" in md and "不进主表" in md
    assert "不得升格为正式 RESULT-Y" in md
    assert "禁止 HARKing" in md or "跑前写死" in md
    assert "不得激活 PREREG-Y" in md
    assert "夹具绿 ≠ 真数据过门" in md
    assert "是否发模型" in md
    assert _AWAITING in md
    for token in _FORBIDDEN_PASS_EVIDENCE:
        assert token in md


def test_gate_y_conditions_tc_only_not_b1_b2():
    """过门只看 k 与 T−C；B1/B2 正负不改变 passed。"""
    # 过门：k≥10 且 T−C>0；即便 B1/B2 均为负
    primary_pass = {
        "k": 12,
        "comparisons": [
            {"name": "T-C", "point": 0.1},
            {"name": "T-B1", "point": -0.2},
            {"name": "T-B2", "point": -0.3},
        ],
    }
    gate = gate_y_conditions(primary_pass)
    assert gate["k_ok"] is True
    assert gate["t_c_positive"] is True
    assert gate["t_b1_positive"] is False
    assert gate["t_b2_positive"] is False
    assert gate["passed"] is True

    # 不过门：B1/B2 均正但 T−C≤0
    primary_fail_tc = {
        "k": 15,
        "comparisons": [
            {"name": "T-C", "point": 0.0},
            {"name": "T-B1", "point": 0.2},
            {"name": "T-B2", "point": 0.3},
        ],
    }
    gate2 = gate_y_conditions(primary_fail_tc)
    assert gate2["k_ok"] is True
    assert gate2["t_c_positive"] is False
    assert gate2["t_b1_positive"] is True
    assert gate2["t_b2_positive"] is True
    assert gate2["passed"] is False

    # 不过门：T−C>0 但 k<10
    primary_fail_k = {
        "k": 9,
        "comparisons": [
            {"name": "T-C", "point": 0.5},
            {"name": "T-B1", "point": 0.5},
            {"name": "T-B2", "point": 0.5},
        ],
    }
    gate3 = gate_y_conditions(primary_fail_k)
    assert gate3["k_ok"] is False
    assert gate3["t_c_positive"] is True
    assert gate3["passed"] is False


def test_forbidden_evidence_not_treated_as_passed():
    """不得把 #479 / GATE-K-PROBE / GATE-C-FIXTURE 路径当作本页已过门依据。"""
    md = render_gate_y_probe_markdown(
        code_pin="test",
        baseline_note="test",
        authorize_send=False,
        send_result=None,
        probe_pack={
            "status": "recomputed",
            "gate": {
                "passed": False,
                "k": 0,
                "k_ok": False,
                "t_c_positive": False,
                "t_b1_positive": True,
                "t_b2_positive": True,
                "comparisons": {
                    "T-B1": {"point": 0.1},
                    "T-B2": {"point": 0.2},
                },
            },
            "arms": {"T": [], "B1": [], "B2": [], "C": []},
            "primary": None,
            "generations_path": Path("x"),
            "generations_n": 0,
            "generations_sha256": "abc",
            "table": [
                {
                    "rows": [
                        {"臂": "T", "自然放行": 0, "自然误放": 0, "固定k误放": None},
                        {"臂": "B1", "自然放行": 0, "自然误放": 0, "固定k误放": None},
                        {"臂": "B2", "自然放行": 0, "自然误放": 0, "固定k误放": None},
                        {"臂": "C", "自然放行": 0, "自然误放": 0, "固定k误放": None},
                    ],
                    "k": 0,
                    "T-C": None,
                    "T-B1": 0.1,
                    "T-B2": 0.2,
                    "gate_passed": False,
                }
            ],
        },
        readonly_pack=None,
    )
    assert "gate_passed = `False`" in md or "**gate_passed = `False`**" in md
    assert "不得把夹具绿或 `#479`" in md or "GATE-K-PROBE" in md
    assert "GATE-C-FIXTURE" in md
    # 即使 B1/B2 报告为正，过门仍 false
    assert "只报告" in md
    assert "进 gate_passed？` | **否**" in md or "| **否** |" in md


def test_sample_pin_is_pe_v2_n30():
    ids = probe_claim_ids()
    assert len(ids) == 30
    assert ids == [r["claim_id"] for r in load_pe_v2_formal_n30()]


def test_probe_requests_skip_b1_rewrite():
    rows = load_pe_v2_formal_n30()[:2]
    reqs = probe_requests(rows)
    arms_phases = {(r["arm"], r["phase"]) for r in reqs}
    assert ("B1", "rewrite") not in arms_phases
    assert ("T", "rewrite") in arms_phases
    assert ("C", "rewrite") in arms_phases
    assert ("B2", "claim") in arms_phases


def test_decoding_pin_explicit():
    pin = decoding_pin()
    assert pin["model"] == "qwen-flash"
    assert pin["temperature"] == 0
    assert pin["api_seed"] is None


def test_default_main_awaits_auth_zero_llm(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_gate_y_probe._PROBE_GENERATIONS_REL",
        Path("__test_absent_gate_y_probe_generations__.jsonl"),
    )
    out = tmp_path / "GATE-Y-PROBE.md"
    assert main(["--out", str(out), "--code-pin", "unit-test"]) == 0
    printed = capsys.readouterr().out
    assert "gate_passed=False" in printed
    assert _AWAITING in printed
    text = out.read_text(encoding="utf-8")
    assert "可扔" in text and "非乙成立" in text
    assert "是否发模型" in text
    assert "`否`" in text or "是否发模型**：`否`" in text


def test_authorize_send_refuses_without_probe_auth(capsys):
    assert main(["--authorize-send"]) == 2
    err = capsys.readouterr().err
    assert "拒绝" in err
    assert _PROBE_AUTH_PHRASE in err
    assert not probe_auth_ok(None)
    assert not probe_auth_ok("授权发模型")
    assert probe_auth_ok(_PROBE_AUTH_PHRASE)


def test_no_write_rejects_authorize_send():
    assert main(["--no-write", "--authorize-send", "--probe-auth-phrase", _PROBE_AUTH_PHRASE]) == 2


def test_send_refuses_formal_paths(tmp_path):
    formal = generations_path()
    with pytest.raises(RuntimeError, match="formal"):
        send_probe_generations(
            generations_file=formal,
            chat=lambda *a, **k: "x",
            probe_auth=_PROBE_AUTH_PHRASE,
        )
    with pytest.raises(RuntimeError, match="探针人令"):
        send_probe_generations(
            generations_file=tmp_path / "ok.jsonl",
            chat=lambda *a, **k: "x",
            probe_auth=None,
        )


def test_recompute_pass_and_fail_branches(tmp_path, monkeypatch):
    """夹具可分别构造过/不过；夹具绿 ≠ 真数据过门（文面另测）。"""
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    # 过门分支：C 任意 after（高误放）→ T−C>0 且 k≥10
    pass_path = tmp_path / "pass.jsonl"
    pass_path.write_text(
        "\n".join(
            json.dumps(item, ensure_ascii=False)
            for item in _synthetic_generations(mode="pass")
        )
        + "\n",
        encoding="utf-8",
    )
    pack_pass = run_probe_recompute(generations_file=pass_path)
    assert pack_pass["status"] == "recomputed"
    gate_pass = pack_pass["gate"]
    assert gate_pass["k"] is not None and gate_pass["k"] >= 10
    assert gate_pass["t_c_positive"] is True
    assert gate_pass["passed"] is True
    # B1/B2 出现在 gate 报告字段（只报告）
    assert "t_b1_positive" in gate_pass and "t_b2_positive" in gate_pass

    # 不过门分支：压低 T 自然放行 → k_ok=false ⇒ gate_passed=false
    fail_path = tmp_path / "fail.jsonl"
    fail_path.write_text(
        "\n".join(
            json.dumps(item, ensure_ascii=False)
            for item in _synthetic_generations(mode="fail_low_k")
        )
        + "\n",
        encoding="utf-8",
    )
    pack_fail = run_probe_recompute(generations_file=fail_path)
    assert pack_fail["status"] == "recomputed"
    gate_fail = pack_fail["gate"]
    assert gate_fail["k_ok"] is False
    assert gate_fail["passed"] is False
    # 核验语义未放宽
    assert verify_edit(
        {
            "after_text": "甲",
            "evidence_text": "甲",
            "arm": "T",
            "claim_id": "x",
            "evidence_id": "a006#p1@T1",
        }
    )["ok"] is True


def test_write_report_default_does_not_send(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_gate_y_probe._PROBE_GENERATIONS_REL",
        Path("__test_absent_gate_y_probe_generations__.jsonl"),
    )
    formal = generations_path()
    before = formal.read_bytes()
    out = tmp_path / "GATE-Y-PROBE.md"
    path, pack = write_probe_report(
        out,
        code_pin="unit",
        baseline_note="unit",
        authorize_send=False,
    )
    assert path == out
    assert pack["awaiting"] is True
    assert pack["gate"]["passed"] is False
    assert formal.read_bytes() == before
    assert _PROBE_GENERATIONS_REL.name == "gate-y-probe-generations.jsonl"
