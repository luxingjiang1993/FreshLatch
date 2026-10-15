"""MUM-S5：适配草稿脚本进程内退出码。不发网络请求，不要求 LM Studio。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from freshlatch.model_profile import (
    DEFAULT_LMS_MODEL,
    ENV_LMS_BASE_URL,
    ENV_LMS_MODEL,
    ENV_MODEL_PROFILE,
)
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_MOD_NAME = "model_fit_review_mum_s5"


def _load_review():
    path = REPO_ROOT / "scripts" / "model_fit_review.py"
    spec = importlib.util.spec_from_file_location(_SCRIPT_MOD_NAME, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


REVIEW = _load_review()


def _clear_profile_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_MODEL_PROFILE, raising=False)
    monkeypatch.delenv(ENV_LMS_MODEL, raising=False)
    monkeypatch.delenv(ENV_LMS_BASE_URL, raising=False)


def test_review_script_does_not_import_http_clients():
    text = (REPO_ROOT / "scripts" / "model_fit_review.py").read_text(encoding="utf-8")
    for banned in ("openai", "requests", "httpx", "urllib", "socket", "--live"):
        assert banned not in text


def test_review_offline_exit_zero(monkeypatch, capsys):
    _clear_profile_env(monkeypatch)
    assert REVIEW.main([]) == 0
    out = capsys.readouterr().out
    assert "model_fit_review http=none paid=none" in out
    assert "ok slots=10 verdicts=keep:6,prefer_local:1,must_cloud:3 c04=must_cloud http=none paid=none lms_required=no" in out
    assert "RTX 5070 Ti 12GB + 32GB RAM" in out
    assert "qwen3.5-9b" in out
    assert "65536" in out
    assert "qwen3.8-27b" in out
    assert "prefer_9b_for_drafts=yes" in out
    assert "registry_defaults: unchanged" in out
    assert out.count("lmstudio") == 2
    assert "qwen-flash" in out
    assert "qwen-plus" in out
    assert "text-embedding-v4" in out
    assert "BAAI/bge-small-zh-v1.5" in out
    assert "BAAI/bge-reranker-base" in out
    assert "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7" in out
    assert "qwen3-235b-a22b-instruct-2507" in out
    assert "deepseek-flash" in out
    assert "kimi-k2.6" in out
    assert "fit-verdict" not in out


def test_verdict_words_match_registry_and_docs():
    assert REVIEW.VERDICTS["default_llm"] == "prefer_local"
    assert REVIEW.VERDICTS["x1_draft"] == "keep"
    assert REVIEW.VERDICTS["x1_flag"] == "keep"
    assert REVIEW.VERDICTS["embed"] == "keep"
    assert REVIEW.VERDICTS["local_embed"] == "keep"
    assert REVIEW.VERDICTS["neural_rerank"] == "keep"
    assert REVIEW.VERDICTS["nli"] == "keep"
    assert REVIEW.VERDICTS["judge_qwen"] == "must_cloud"
    assert REVIEW.VERDICTS["judge_deepseek"] == "must_cloud"
    assert REVIEW.VERDICTS["judge_kimi"] == "must_cloud"
    assert REVIEW.C04_VERDICT == "must_cloud"
    assert DEFAULT_MODEL == "qwen-flash"
    assert MODEL_REGISTRY["default_llm"].model == "qwen-flash"
    assert DEFAULT_LMS_MODEL == "qwen3.5-9b"
    assert set(REVIEW.VERDICTS) == set(MODEL_REGISTRY)
    for path in REVIEW._VERDICT_DOCS:
        text = path.read_text(encoding="utf-8")
        for slot, verdict in REVIEW.VERDICTS.items():
            assert f"fit-verdict {slot} {verdict}" in text
        assert f"fit-verdict {REVIEW.C04_READ_POINT} {REVIEW.C04_VERDICT}" in text
        assert "RTX 5070 Ti 12GB" in text
        assert "65536" in text
        assert "qwen3.8-27b" in text
        assert "8–12k" in text


def test_scorecard_template_has_fixed_dimensions():
    text = (REPO_ROOT / "docs" / "ops" / "model-fit-scorecard.template.md").read_text(encoding="utf-8")
    for name in ("任务匹配", "质量下限", "上下文", "延迟与吞吐", "成本", "可复现", "运维摩擦"):
        assert name in text
    for word in ("keep", "prefer_local", "must_cloud"):
        assert f"`{word}`" in text


def test_unknown_flag_exits_two():
    with pytest.raises(SystemExit) as exc:
        REVIEW.main(["--live"])
    assert exc.value.code == 2


def test_empty_lms_model_exits_nonzero(monkeypatch, capsys):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_LMS_MODEL, "  ")
    assert REVIEW.main([]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "model_fit_review failed:" in captured.err


def test_profile_env_does_not_hide_cloud_row(monkeypatch, capsys):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-lms")
    assert REVIEW.main([]) == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert any(line.startswith("cloud ") and "default_llm" in line and "qwen-flash" in line for line in lines)
    assert any(
        line.startswith("local-lms ") and "default_llm" in line and "qwen3.5-9b" in line
        for line in lines
    )
    assert any(line.startswith("local-lms ") and "judge_qwen" in line and "dashscope" in line for line in lines)
