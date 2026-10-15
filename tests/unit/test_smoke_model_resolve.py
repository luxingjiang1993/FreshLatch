"""MUM-S3：冒烟脚本进程内退出码。不发网络请求，不要求 LM Studio。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from freshlatch.model_profile import (
    ENV_LMS_BASE_URL,
    ENV_LMS_MODEL,
    ENV_MODEL_PROFILE,
    LOCAL_LMS_OVERLAY_SLOTS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_MOD_NAME = "smoke_model_resolve_mum_s3"


def _load_smoke():
    path = REPO_ROOT / "scripts" / "smoke_model_resolve.py"
    spec = importlib.util.spec_from_file_location(_SCRIPT_MOD_NAME, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


SMOKE = _load_smoke()


def _clear_profile_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_MODEL_PROFILE, raising=False)
    monkeypatch.delenv(ENV_LMS_MODEL, raising=False)
    monkeypatch.delenv(ENV_LMS_BASE_URL, raising=False)


def test_smoke_script_does_not_import_http_clients():
    text = (REPO_ROOT / "scripts" / "smoke_model_resolve.py").read_text(encoding="utf-8")
    for banned in ("openai", "requests", "httpx", "urllib", "socket"):
        assert banned not in text


def test_smoke_both_profiles_exit_zero(monkeypatch, capsys):
    _clear_profile_env(monkeypatch)
    assert SMOKE.main([]) == 0
    out = capsys.readouterr().out
    assert "smoke_model_resolve http=none" in out
    assert "ok slots=10 profiles=cloud,local-lms http=none" in out
    assert out.count("lmstudio") == len(LOCAL_LMS_OVERLAY_SLOTS)
    assert "qwen-flash" in out
    assert "qwen3.5-9b" in out
    assert "http://127.0.0.1:1234/v1" in out
    assert "judge_qwen" in out
    assert "qwen3-235b-a22b-instruct-2507" in out
    assert "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7" in out


def test_explicit_both_ignores_unknown_env(monkeypatch, capsys):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-gpu")
    assert SMOKE.main(["--profile", "both"]) == 0
    err = capsys.readouterr().err
    assert err == ""


def test_unknown_env_profile_exits_nonzero(monkeypatch, capsys):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-gpu")
    assert SMOKE.main([]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "smoke_model_resolve failed:" in captured.err
    assert "local-gpu" in captured.err


def test_empty_lms_model_exits_nonzero(monkeypatch, capsys):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_LMS_MODEL, "  ")
    assert SMOKE.main(["--profile", "local-lms"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert ENV_LMS_MODEL in captured.err


def test_unknown_profile_flag_exits_two():
    with pytest.raises(SystemExit) as exc:
        SMOKE.main(["--profile", "local-gpu"])
    assert exc.value.code == 2
