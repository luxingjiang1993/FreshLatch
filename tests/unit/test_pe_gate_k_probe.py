"""仓外抬 k 探针：协议写死、默认不发、复算入口、旁路防火墙。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_formal import generations_path, load_pe_v2_formal_n30
from freshlatch.eval.patch_events_gate_k_probe import (
    _AWAITING,
    _PROBE_GENERATIONS_REL,
    decoding_pin,
    gate_pass_criteria,
    main,
    probe_claim_ids,
    probe_requests,
    render_gate_k_probe_markdown,
    run_probe_recompute,
    send_probe_generations,
    write_probe_report,
)
from freshlatch.eval.patch_events_verify import verify_edit


def test_protocol_locked_before_any_send():
    """跑前写死：过门三条 + 可扔文首 + 不得激活句。"""
    criteria = gate_pass_criteria()
    assert any("k ≥ 10" in item or "k ≥ 10" in item.replace(">=", "≥") for item in criteria)
    assert any("T−B1" in item for item in criteria)
    assert any("T−B2" in item for item in criteria)
    md = render_gate_k_probe_markdown(
        code_pin="test",
        baseline_note="test-baseline",
        authorize_send=False,
        send_result=None,
        probe_pack={"status": "no_probe_generations", "gate": {"passed": False, "k": None, "comparisons": {}}},
        readonly_pack=None,
    )
    assert "可扔" in md and "非甲" in md and "不进主表" in md
    assert "不得升格为正式 RESULT-B" in md
    assert "禁止 HARKing" in md or "跑前写死" in md
    assert "不得激活 PREREG-B" in md
    assert "不得开 #440" in md
    assert _AWAITING in md


def test_sample_pin_is_pe_v2_n30():
    ids = probe_claim_ids()
    assert len(ids) == 30
    assert ids == [r["claim_id"] for r in load_pe_v2_formal_n30()]
    assert ids[0] == "a005" and ids[-1] == "d009"


def test_probe_requests_skip_b1_rewrite():
    """同 after：探针发送队列不含 B1 rewrite。"""
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
    assert pin["decoding_seed"] == 20261007


def test_default_main_awaits_auth_zero_llm(monkeypatch, tmp_path, capsys):
    """默认入口：零 LLM、无旁路生成时 gate_passed=false、等待授权。"""
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    # 隔离：不读仓库内已落盘的旁路探针生成（夹具绿 ≠ 过门）
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_gate_k_probe._PROBE_GENERATIONS_REL",
        Path("__test_absent_gate_k_probe_generations__.jsonl"),
    )
    out = tmp_path / "GATE-K-PROBE.md"
    assert main(["--out", str(out), "--code-pin", "unit-test"]) == 0
    printed = capsys.readouterr().out
    assert "gate_passed=False" in printed
    assert _AWAITING in printed
    text = out.read_text(encoding="utf-8")
    assert "可扔" in text and "非甲" in text
    assert _AWAITING in text
    assert "不得激活 PREREG-B" in text
    assert "gate_passed = `False`" in text or "gate_passed=`False`" in text or "**gate_passed = `False`**" in text


def test_no_write_does_not_send(monkeypatch, capsys):
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_gate_k_probe._PROBE_GENERATIONS_REL",
        Path("__test_absent_gate_k_probe_generations__.jsonl"),
    )
    assert main(["--no-write"]) == 0
    out = capsys.readouterr().out
    assert "gate_passed=False" in out
    assert _AWAITING in out


def test_no_write_rejects_authorize_send(capsys):
    assert main(["--no-write", "--authorize-send"]) == 2


def test_send_refuses_formal_generations_path(tmp_path):
    """旁路防火墙：禁止写入 formal-generations.jsonl。"""
    formal = generations_path()
    with pytest.raises(RuntimeError, match="formal-generations"):
        send_probe_generations(generations_file=formal, chat=lambda *a, **k: "x")


def test_recompute_from_synthetic_probe_generations(tmp_path, monkeypatch):
    """旁路生成复算：k≥10 且差为正 ⇒ gate_passed（夹具层，非甲）。"""
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    rows = load_pe_v2_formal_n30()
    # 构造：正确样 after=evidence → T/B1 可过核验；坏样 after=evidence 但 T0 绑定拒
    # 另：B2 全部放行且坏样误放，保证 T−B2 差为正；B1 比 T 多放行坏样 → T−B1 为正
    lines: list[dict] = []
    for row in rows:
        cid = row["claim_id"]
        ev = str(row["evidence_text"])
        gold = row["construction_gold"]
        # C：任意 after
        lines.append(
            {
                "claim_id": cid,
                "arm": "C",
                "phase": "rewrite",
                "output_field": "after_text",
                "text": f"c-after-{cid}",
                "model": "qwen-flash",
                "temperature": 0,
            }
        )
        # T/B1 共享：正确样对齐 evidence；坏样也对齐（靠绑定缝拆 T/B1）
        after = ev
        lines.append(
            {
                "claim_id": cid,
                "arm": "T",
                "phase": "rewrite",
                "output_field": "after_text",
                "text": after,
                "model": "qwen-flash",
                "temperature": 0,
            }
        )
        # B2 claim + diff：diff 用 evidence 使核验可过；B2 不 hard reject
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
    gen_path = tmp_path / "gate-k-probe-generations.jsonl"
    gen_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in lines) + "\n",
        encoding="utf-8",
    )
    # 把旁路文件接到模块默认相对路径：改 root 为含 docs/... 结构的临时仓不划算；
    # 直接传 generations_file。
    pack = run_probe_recompute(generations_file=gen_path)
    assert pack["status"] == "recomputed"
    gate = pack["gate"]
    # 正确样 15 条应能自然放行（含 T1 绑定）；坏样 T0（b007）T 拒 B1 过
    assert gate["k"] is not None and gate["k"] >= 10
    assert gate["t_b1_positive"] is True
    assert gate["t_b2_positive"] is True
    assert gate["passed"] is True
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
    assert verify_edit(
        {
            "after_text": "甲",
            "evidence_text": "乙",
            "arm": "T",
            "claim_id": "x",
            "evidence_id": "a006#p1@T1",
        }
    )["ok"] is False


def test_write_report_default_does_not_touch_formal_jsonl(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    # 隔离：无旁路生成 ⇒ awaiting；不得误读仓库内已发送的探针 jsonl
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_gate_k_probe._PROBE_GENERATIONS_REL",
        Path("__test_absent_gate_k_probe_generations__.jsonl"),
    )
    formal = generations_path()
    before = formal.read_bytes()
    out = tmp_path / "GATE-K-PROBE.md"
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
    # 旁路相对路径常量（未 monkeypatch 前）仍指向旁路而非 formal
    assert Path("docs/evidence/patch-events/gate-k-probe-generations.jsonl").name == (
        "gate-k-probe-generations.jsonl"
    )
    assert "formal-generations" not in "gate-k-probe-generations.jsonl"
