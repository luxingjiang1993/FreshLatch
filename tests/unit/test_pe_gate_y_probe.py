"""GATE-Y-PROBE：过门仅 k∧T−C；B1/B2 只报；默认不发；无探针人令拒发。

#530：敏感性硬前置；Cond 仍为方向门（不用点>0.05）；冒烟/夹具/敏感性 ≠ gate_passed。
"""

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
    _SENS_REFUSED,
    assert_real_probe_allowed,
    decoding_pin,
    evaluate_sensitivity_prerequisite,
    gate_pass_criteria,
    gate_y_conditions,
    gate_y_point_floor,
    load_sensitivity_prerequisite,
    main,
    mechanism_pins,
    mechanism_pins_complete,
    probe_auth_ok,
    probe_auth_phrase,
    probe_claim_ids,
    probe_requests,
    render_gate_y_probe_markdown,
    run_probe_recompute,
    send_probe_generations,
    write_probe_report,
)
from freshlatch.eval.patch_events_sensitivity import (
    REPORT_LAYER_REAL,
    REPORT_LAYER_STUB,
)
from freshlatch.eval.patch_events_verify import verify_edit


def _allowing_sensitivity() -> dict:
    """测试用：显式真模型层 + 前置齐（不得用 stub 绿冒充）。"""
    return evaluate_sensitivity_prerequisite(
        sensitivity_passed=True,
        activation_prerequisite_met=True,
        inference_layer=REPORT_LAYER_REAL,
        source="unit-allow",
    )


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
    # Cond 未改矮：方向门 >0，不得写成正式乙点>0.05
    assert gate_y_point_floor() == 0.0
    assert not any("0.05" in item for item in criteria)
    assert probe_auth_phrase() == _PROBE_AUTH_PHRASE
    pins = mechanism_pins()
    assert "仪器 ADR-0040" in pins
    assert "敏感性前置" in pins
    assert mechanism_pins_complete(pins) is True
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
        sensitivity_prereq=evaluate_sensitivity_prerequisite(
            sensitivity_passed=False,
            activation_prerequisite_met=False,
            inference_layer=REPORT_LAYER_STUB,
        ),
    )
    assert "可扔" in md and "非乙成立" in md and "不进主表" in md
    assert "不得升格为正式 RESULT-Y" in md
    assert "禁止 HARKing" in md or "跑前写死" in md
    assert "不得激活 PREREG-Y" in md
    assert "夹具绿 ≠ 真数据过门" in md
    assert "敏感性硬前置" in md
    assert "ADR-0040" in md
    assert "不用正式乙点>0.05" in md or "点>0.05" in md
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
    assert "GATE-K-PROBE" in md
    assert "GATE-C-FIXTURE" in md
    assert "夹具" in md
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
    import freshlatch.eval.patch_events_verify as verify_mod

    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda p, h: {
            "entailment": 0.91 if p == h else 0.05,
            "neutral": 0.05,
            "contradiction": 0.04 if p == h else 0.85,
        },
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
    assert "敏感性硬前置" in text
    assert "ADR-0040" in text


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
    allow = _allowing_sensitivity()
    with pytest.raises(RuntimeError, match="formal"):
        send_probe_generations(
            generations_file=formal,
            chat=lambda *a, **k: "x",
            probe_auth=_PROBE_AUTH_PHRASE,
            sensitivity_prereq=allow,
        )
    with pytest.raises(RuntimeError, match="探针人令"):
        send_probe_generations(
            generations_file=tmp_path / "ok.jsonl",
            chat=lambda *a, **k: "x",
            probe_auth=None,
            sensitivity_prereq=allow,
        )


def test_sensitivity_hard_reject_blocks_real_probe(tmp_path, monkeypatch, capsys):
    """敏感性未通过 / stub 层 → 硬拒绝真数据探针（不得发）。"""
    import freshlatch.eval.patch_events_verify as verify_mod

    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda p, h: {
            "entailment": 0.91 if p == h else 0.05,
            "neutral": 0.05,
            "contradiction": 0.04 if p == h else 0.85,
        },
    )
    # 仓内 stub 报告：activation_prerequisite_met=否
    repo_sens = load_sensitivity_prerequisite()
    assert repo_sens["gate_passed"] is False
    assert repo_sens["allows_real_probe"] is False
    with pytest.raises(RuntimeError, match="敏感性前置未满足"):
        assert_real_probe_allowed(repo_sens)

    # stub 绿 + 误标 activation=真 → 仍拒绝
    stub_forged = evaluate_sensitivity_prerequisite(
        sensitivity_passed=True,
        activation_prerequisite_met=True,
        inference_layer=REPORT_LAYER_STUB,
    )
    assert stub_forged["allows_real_probe"] is False
    assert stub_forged["gate_passed"] is False

    # 敏感性未过
    failed = evaluate_sensitivity_prerequisite(
        sensitivity_passed=False,
        activation_prerequisite_met=True,
        inference_layer=REPORT_LAYER_REAL,
    )
    assert failed["allows_real_probe"] is False

    # CLI：有人令但缺前置 → 拒绝（exit 2），不发 LLM
    assert (
        main(
            [
                "--authorize-send",
                "--probe-auth-phrase",
                _PROBE_AUTH_PHRASE,
            ]
        )
        == 2
    )
    err = capsys.readouterr().err
    assert _SENS_REFUSED in err or "敏感性前置未满足" in err

    # write_probe_report：authorize + 缺前置 → refused_sensitivity，gate 仍 false
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_gate_y_probe._PROBE_GENERATIONS_REL",
        Path("__test_absent_gate_y_probe_generations__.jsonl"),
    )
    out = tmp_path / "GATE-Y-PROBE.md"
    path, pack = write_probe_report(
        out,
        code_pin="unit",
        baseline_note="unit",
        authorize_send=True,
        probe_auth=_PROBE_AUTH_PHRASE,
        sensitivity_prereq=failed,
    )
    assert path == out
    assert pack["refused_sensitivity"] is True
    assert pack["gate"]["passed"] is False
    assert pack["sensitivity"]["gate_passed"] is False
    text = out.read_text(encoding="utf-8")
    assert "敏感性硬前置" in text
    assert "ADR-0040" in text


def test_sensitivity_passed_does_not_imply_gate_passed():
    """冒烟/夹具/敏感性均不构成 gate_passed。"""
    allow = _allowing_sensitivity()
    assert allow["sensitivity_passed"] is True
    assert allow["allows_real_probe"] is True
    assert allow["gate_passed"] is False
    # Cond 本身：无探针生成时 passed 仍 false
    gate = gate_y_conditions(None)
    assert gate["passed"] is False
    # 即使 T−C 点>0.05 也不改地板（Cond 仍是 >0）
    gate_hi = gate_y_conditions(
        {
            "k": 12,
            "comparisons": [
                {"name": "T-C", "point": 0.06},
                {"name": "T-B1", "point": 0.01},
                {"name": "T-B2", "point": 0.01},
            ],
        }
    )
    assert gate_hi["passed"] is True
    assert gate_hi["point_floor"] == 0.0
    assert gate_y_point_floor() == 0.0
    # 点=0.04 仍过方向门（若改成 0.05 则会错拒）
    gate_lo = gate_y_conditions(
        {
            "k": 12,
            "comparisons": [{"name": "T-C", "point": 0.04}],
        }
    )
    assert gate_lo["t_c_positive"] is True
    assert gate_lo["passed"] is True


def test_recompute_pass_and_fail_branches(tmp_path, monkeypatch):
    """夹具可分别构造过/不过；夹具绿 ≠ 真数据过门（文面另测）。"""
    import freshlatch.eval.patch_events_verify as verify_mod

    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    # #527：本测不拉真 NLI；表驱动 stub（夹具层 · 不得升格过门）
    def _fake_nli(premise: str, hypothesis: str) -> dict[str, float]:
        if premise == hypothesis:
            return {"entailment": 0.91, "neutral": 0.05, "contradiction": 0.04}
        return {"entailment": 0.05, "neutral": 0.10, "contradiction": 0.85}

    monkeypatch.setattr(verify_mod, "predict_xnli_probs", _fake_nli)
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
    import freshlatch.eval.patch_events_verify as verify_mod

    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    monkeypatch.setattr(
        verify_mod,
        "predict_xnli_probs",
        lambda p, h: {
            "entailment": 0.91 if p == h else 0.05,
            "neutral": 0.05,
            "contradiction": 0.04 if p == h else 0.85,
        },
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
    assert pack["sensitivity"]["gate_passed"] is False
    assert formal.read_bytes() == before
    assert _PROBE_GENERATIONS_REL.name == "gate-y-probe-generations.jsonl"
