"""路线 Y 正式入口骨架：激活守卫、旁路路径、默认不发、解码针。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_formal_y as formal_y
from freshlatch.eval.patch_events_formal_y import (
    FORBIDDEN_GENERATION_PATHS,
    decoding_pin,
    generations_y_path,
    load_pe_v2_formal_n400,
    main,
    prereg_y_activated,
    render_result_y,
    run_formal_y_primary,
    send_formal_y,
)


def test_prereg_y_activated_on_current_tree():
    """PE-Y-05：现行 PREREG-Y 状态行已含激活标记。"""
    assert prereg_y_activated() is True


def test_authorize_send_refuses_when_inactive(tmp_path, monkeypatch):
    """Acceptance: 未激活 + --authorize-send → 非零；不写 formal-generations-y。"""
    y_path = tmp_path / "formal-generations-y.jsonl"
    monkeypatch.setattr(formal_y, "generations_y_path", lambda root=None: y_path)
    monkeypatch.setattr(formal_y, "prereg_y_activated", lambda root=None: False)

    code = main(["--authorize-send"])
    assert code != 0
    assert not y_path.exists()


def test_default_module_cli_does_not_send_on_live_tree():
    """默认入口不发模型。已激活后无 flag 仍不得写 formal-generations-y。"""
    target = Path("docs/evidence/patch-events/formal-generations-y.jsonl")
    existed = target.exists()
    before = target.read_bytes() if existed else None
    env = {**os.environ, "PYTHONPATH": "src"}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "freshlatch.eval.patch_events_formal_y",
        ],
        cwd=Path.cwd(),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert proc.returncode == 0
    assert "formal-y default: no send" in (proc.stdout or "")
    assert "activated=True" in (proc.stdout or "")

    if existed:
        assert target.read_bytes() == before
    else:
        assert not target.exists()


def test_default_entry_no_send_zero_llm(monkeypatch):
    """Acceptance: 默认入口不发模型。"""
    calls: list[object] = []

    def _boom(*_a, **_k):
        calls.append(1)
        raise AssertionError("不得发模型")

    monkeypatch.setattr(formal_y, "send_formal_y", _boom)
    monkeypatch.setattr(formal_y, "live_chat", _boom)
    code = main([])
    assert code == 0
    assert calls == []


def test_recompute_only_empty_safe_zero_llm(monkeypatch, tmp_path):
    """Acceptance: --recompute-only 无生成文件时安全空跑且零 LLM。"""
    y_path = tmp_path / "missing-y.jsonl"
    monkeypatch.setattr(formal_y, "generations_y_path", lambda root=None: y_path)
    calls: list[object] = []

    def _boom(*_a, **_k):
        calls.append(1)
        raise AssertionError("零 LLM")

    monkeypatch.setattr(formal_y, "live_chat", _boom)
    monkeypatch.setattr(formal_y, "send_formal_y", _boom)
    pack = run_formal_y_primary(generations_file=y_path)
    assert pack["status"] == "no_generations"
    assert pack["primary"] is None
    code = main(["--recompute-only", "--no-write"])
    assert code == 0
    assert calls == []


def test_generation_path_constants_isolated():
    """Acceptance: 成功写盘路径不得触及 b/c/旧 formal jsonl。"""
    y = generations_y_path()
    assert y.name == "formal-generations-y.jsonl"
    forbidden_names = {p.name for p in FORBIDDEN_GENERATION_PATHS}
    assert forbidden_names == {
        "formal-generations-b.jsonl",
        "formal-generations-c.jsonl",
        "formal-generations.jsonl",
    }
    assert y.name not in forbidden_names
    for forbidden in FORBIDDEN_GENERATION_PATHS:
        assert y.resolve() != (Path.cwd() / forbidden).resolve()


def test_decoding_pin_matches_prereg():
    """Acceptance: model=qwen-flash · temp=0 · Decoding.seed=20261007 · API seed=None。"""
    pin = decoding_pin()
    assert pin["model"] == "qwen-flash"
    assert pin["temperature"] == 0
    assert pin["decoding_seed"] == 20261007
    assert pin["api_seed"] is None


def test_n400_loader_wired_to_route_y_pin_full():
    """PE-Y-CORPUS-02：loader 接满额名单针，返回恰好 400（非 NotImplemented 桩）。"""
    rows = load_pe_v2_formal_n400()
    assert len(rows) == 400
    assert len({row["claim_id"] for row in rows}) == 400
    assert not isinstance(rows, type(None))


def test_n400_loader_still_refuses_artificial_shortfall(tmp_path, monkeypatch):
    """缺额 fail-closed 语义保留：人为缺额针仍拒 <400。"""
    path = tmp_path / "SPLIT-pe-v2-route-y.json"
    path.write_text(
        json.dumps(
            {
                "status": "不可激活",
                "activation": {"ready": False},
                "gaps": {"n400": 400},
                "n400": [],
                "pilot": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_formal_y.route_y_split_path",
        lambda root=None: path,
    )
    with pytest.raises(RuntimeError, match="不可激活.*语料缺额") as exc:
        load_pe_v2_formal_n400(tmp_path)
    assert "不得静默改小" in str(exc.value)
    assert not isinstance(exc.value, NotImplementedError)


def test_send_refuses_when_path_is_forbidden(monkeypatch, tmp_path):
    monkeypatch.setattr(formal_y, "prereg_y_activated", lambda root=None: True)
    legacy = Path("docs/evidence/patch-events/formal-generations.jsonl")
    monkeypatch.setattr(
        formal_y,
        "generations_y_path",
        lambda root=None: Path.cwd() / legacy,
    )
    with pytest.raises(RuntimeError, match="禁止写入"):
        send_formal_y(chat=lambda *a, **k: "x")


def test_send_refuses_when_inactive_api(monkeypatch):
    """未激活守卫仍拒绝发送。不读现行已激活文首，避免误写正式 jsonl。"""
    monkeypatch.setattr(formal_y, "prereg_y_activated", lambda root=None: False)
    with pytest.raises(RuntimeError, match="未激活"):
        send_formal_y(chat=lambda *a, **k: "x")


def test_content_inspection_records_void_and_continues(monkeypatch, tmp_path):
    """审查拒绝记作废并继续同一文件；不得把空回文记成 C 放行。其它异常仍抛出。"""
    from freshlatch.eval.patch_events_formal import _saved_generator

    y_path = tmp_path / "formal-generations-y.jsonl"
    monkeypatch.setattr(formal_y, "generations_y_path", lambda root=None: y_path)
    monkeypatch.setattr(formal_y, "prereg_y_activated", lambda root=None: True)
    monkeypatch.setattr(formal_y, "live_gaps", lambda: ())
    monkeypatch.setattr(
        formal_y,
        "load_pe_v2_formal_n400",
        lambda root=None: [
            {
                "claim_id": "c1",
                "before_text": "before",
                "evidence_text": "evidence",
                "evidence_id": "doc#p1#T1",
                "edit_type": "删除",
                "construction_gold": "坏",
            }
        ],
    )

    def _boom(*_a, **_k):
        raise RuntimeError("connection reset")

    with pytest.raises(RuntimeError, match="connection reset"):
        send_formal_y(chat=_boom)
    assert not y_path.exists()

    calls = {"n": 0}

    def _chat(*_a, **_k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("Error code: 400 data_inspection_failed")
        return "ok-text"

    result = send_formal_y(chat=_chat)
    assert result["blocked"] == 1
    assert result["sent"] >= 1
    lines = [
        json.loads(line)
        for line in y_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    blocked = [row for row in lines if row.get("output_field") == "blocked"]
    assert len(blocked) == 1
    assert blocked[0]["arm"] == "C"
    assert blocked[0]["blocked_reason"] == "data_inspection_failed"
    replay = _saved_generator(lines)
    assert replay({"claim_id": "c1", "arm": "C", "phase": "rewrite"}).get("void") is True
    produced_t = replay({"claim_id": "c1", "arm": "T", "phase": "rewrite"})
    assert produced_t.get("after_text") == "ok-text"


def test_render_copies_primary_when_roster_complete_despite_b2_shortfall():
    """名单已齐且主比较有定义时抄表。不得因一条作废把成立格留成未填，也不得改尺。"""
    pack = {
        "primary": {
            "k": 11,
            "comparisons": [
                {
                    "name": "T-C",
                    "point": 0.0927152317880795,
                    "ci95_low": -0.006493506493506496,
                    "ci95_high": 0.2,
                },
                {
                    "name": "T-B1",
                    "point": 0.01,
                    "ci95_low": 0.0,
                    "ci95_high": 0.1,
                },
                {
                    "name": "T-B2",
                    "point": 0.02,
                    "ci95_low": 0.0,
                    "ci95_high": 0.1,
                },
            ],
        },
        "b2_count": 399,
        "n": 400,
        "generations_n": 1599,
        "generations_sha256": "abc",
        "blocked_n": 3,
        "blocked_ids": ["d030"],
        "roster_complete": True,
        "status": "recomputed",
        "tier": "丙",
        "verdict": "判定：结果丙。",
        "decoding": decoding_pin(),
    }
    text = render_result_y(pack, code_pin="pin", activated_note="已激活")
    table = text.split("## 主比较", 1)[1].split("## 甲 / 乙 / 丙判定", 1)[0]
    assert "未填" not in table
    assert "不成立" in table
    assert "报告-only（不参与成立）" in table
    assert "结果丙" in text
    assert "结果乙" not in text
    assert "-0.006493506493506496" in table
