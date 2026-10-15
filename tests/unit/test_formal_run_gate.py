"""MUM-S7：正式跑前闸。不发网络，不写仓库里的 C-04 RESULT。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from freshlatch.formal_run_gate import (
    ENV_ALLOW_NON_RESULT_DEBUG,
    FormalRunGateError,
    assert_formal_run_allowed,
    non_result_debug_allowed,
)
from freshlatch.model_profile import (
    ENV_MODEL_PROFILE,
    PROFILE_LOCKED_SLOTS,
    UnknownModelProfileError,
    resolve_model,
)
from freshlatch.models import MODEL_REGISTRY

REPO = Path(__file__).resolve().parents[2]


def _clear_profile_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_MODEL_PROFILE, raising=False)
    monkeypatch.delenv(ENV_ALLOW_NON_RESULT_DEBUG, raising=False)
    monkeypatch.delenv("FRESHLATCH_LMS_MODEL", raising=False)
    monkeypatch.delenv("FRESHLATCH_LMS_BASE_URL", raising=False)


def test_unset_and_explicit_cloud_pass(monkeypatch):
    _clear_profile_env(monkeypatch)
    assert_formal_run_allowed()
    assert_formal_run_allowed(profile=None)
    assert_formal_run_allowed(profile="cloud")
    assert_formal_run_allowed(profile=" cloud ")
    assert non_result_debug_allowed() is False


def test_explicit_cloud_ignores_local_env(monkeypatch):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-lms")
    assert_formal_run_allowed(profile="cloud")
    with pytest.raises(FormalRunGateError, match="local-lms"):
        assert_formal_run_allowed()


def test_local_lms_fails_closed(monkeypatch):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, " local-lms ")
    with pytest.raises(FormalRunGateError, match="不得打开正式 RESULT"):
        assert_formal_run_allowed()
    with pytest.raises(FormalRunGateError, match="local-lms"):
        assert_formal_run_allowed(profile="local-lms")


def test_unknown_profile_fails(monkeypatch):
    _clear_profile_env(monkeypatch)
    with pytest.raises(UnknownModelProfileError, match="local-gpu"):
        assert_formal_run_allowed(profile="local-gpu")
    monkeypatch.setenv(ENV_MODEL_PROFILE, "LOCAL-LMS")
    with pytest.raises(UnknownModelProfileError, match="LOCAL-LMS"):
        assert_formal_run_allowed()


def test_unlock_env_does_not_open_formal_result(monkeypatch):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-lms")
    monkeypatch.setenv(ENV_ALLOW_NON_RESULT_DEBUG, "1")
    assert non_result_debug_allowed() is True
    assert non_result_debug_allowed(profile="local-lms") is True
    with pytest.raises(FormalRunGateError, match="不得打开正式 RESULT"):
        assert_formal_run_allowed()
    monkeypatch.setenv(ENV_ALLOW_NON_RESULT_DEBUG, "true")
    assert non_result_debug_allowed() is False
    with pytest.raises(FormalRunGateError):
        assert_formal_run_allowed()


def test_locked_slots_stay_registry_objects_under_local_lms(monkeypatch):
    _clear_profile_env(monkeypatch)
    assert set(PROFILE_LOCKED_SLOTS) >= {"judge_qwen", "judge_deepseek", "judge_kimi", "nli"}
    for slot in PROFILE_LOCKED_SLOTS:
        assert resolve_model(slot, profile="local-lms") is MODEL_REGISTRY[slot]
    assert_formal_run_allowed(profile="cloud")


def test_covered_locked_slot_fails_even_on_cloud(monkeypatch):
    _clear_profile_env(monkeypatch)
    real = resolve_model

    def covered(slot: str, profile: str | None = None):
        entry = real(slot, profile=profile)
        if slot == "nli" and profile == "local-lms":
            return replace(entry, model="not-the-registry-object")
        return entry

    monkeypatch.setattr("freshlatch.formal_run_gate.resolve_model", covered)
    with pytest.raises(FormalRunGateError, match="锁定槽位 nli"):
        assert_formal_run_allowed(profile="cloud")
    with pytest.raises(FormalRunGateError, match="锁定槽位 nli"):
        assert_formal_run_allowed(profile="local-lms")


def test_write_measured_blocks_local_lms_before_any_file(monkeypatch, tmp_path):
    from freshlatch.eval.patch_establishment_formal import write_measured

    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-lms")
    monkeypatch.setenv(ENV_ALLOW_NON_RESULT_DEBUG, "1")
    result = REPO / "docs" / "evidence" / "patch-establishment" / "RESULT.md"
    before = result.read_bytes()
    manifest = REPO / "docs" / "evidence" / "patch-establishment" / "manifest.json"
    manifest_before = manifest.read_bytes()
    with pytest.raises(FormalRunGateError, match="不得打开正式 RESULT"):
        write_measured(
            root=REPO,
            out_dir=tmp_path / "out",
            bundle={"primary": {"defined": True, "point": 0.0, "established": False}},
            code_pin="deadbeef",
            authorize_run=True,
        )
    assert result.read_bytes() == before
    assert manifest.read_bytes() == manifest_before
    assert not (tmp_path / "out").exists()


def test_write_measured_cloud_still_requires_authorize(monkeypatch, tmp_path):
    from freshlatch.eval.patch_establishment_formal import write_measured

    _clear_profile_env(monkeypatch)
    with pytest.raises(RuntimeError, match="authorize-run"):
        write_measured(
            root=tmp_path,
            out_dir=tmp_path / "out",
            bundle={},
            code_pin="x",
            authorize_run=False,
        )
    assert not (tmp_path / "out").exists()
    assert not (tmp_path / "docs" / "evidence" / "patch-establishment" / "RESULT.md").exists()
