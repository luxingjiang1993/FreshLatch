"""路线 Y 正式入口骨架：激活守卫、旁路路径、默认不发、解码针。"""

from __future__ import annotations

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
    run_formal_y_primary,
    send_formal_y,
)


def test_prereg_y_not_activated_on_current_tree():
    assert prereg_y_activated() is False


def test_authorize_send_refuses_when_inactive(tmp_path, monkeypatch):
    """Acceptance: 未激活 + --authorize-send → 非零；不写 formal-generations-y。"""
    y_path = tmp_path / "formal-generations-y.jsonl"
    monkeypatch.setattr(formal_y, "generations_y_path", lambda root=None: y_path)
    monkeypatch.setattr(formal_y, "prereg_y_activated", lambda root=None: False)

    code = main(["--authorize-send"])
    assert code != 0
    assert not y_path.exists()


def test_authorize_send_module_cli_refuses_and_skips_write(tmp_path):
    """Acceptance CLI：真实 PREREG-Y 未激活时模块入口非零且不新建 y jsonl。"""
    target = Path("docs/evidence/patch-events/formal-generations-y.jsonl")
    existed = target.exists()
    before = target.read_bytes() if existed else None
    env = {**os.environ, "PYTHONPATH": "src"}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "freshlatch.eval.patch_events_formal_y",
            "--authorize-send",
        ],
        cwd=Path.cwd(),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "未激活" in proc.stderr or "未激活" in proc.stdout
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


def test_n400_loader_is_stub():
    """n=400 留给 PE-Y-03；不得假装已有名单。"""
    with pytest.raises(NotImplementedError, match="PE-Y-03"):
        load_pe_v2_formal_n400()


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


def test_send_refuses_when_inactive_api():
    with pytest.raises(RuntimeError, match="未激活"):
        send_formal_y(chat=lambda *a, **k: "x")
