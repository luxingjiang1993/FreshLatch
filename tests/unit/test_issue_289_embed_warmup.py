"""#289: 离线报错与预热脚本。不下载权重。"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.store.local_embed import (
    LOCAL_EMBED_MODEL,
    LocalEmbedUnavailable,
    _load_model,
    local_embed_cache_dir,
)


def test_production_default_unchanged():
    assert PRODUCTION_RETRIEVAL_MODE == "bm25"


def test_cache_dir_comes_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path))
    assert local_embed_cache_dir() == str(tmp_path)
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", "  ")
    assert local_embed_cache_dir() is None


def test_offline_load_reports_cache_and_exception_type(monkeypatch, tmp_path):
    import freshlatch.store.local_embed as mod

    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path))
    monkeypatch.setenv("FRESHLATCH_EMBED_OFFLINE", "1")
    monkeypatch.setattr(mod, "_model", None)

    class _Boom:
        def __init__(self, **kwargs):
            assert kwargs["model_name"] == LOCAL_EMBED_MODEL
            assert kwargs["cache_dir"] == str(tmp_path)
            assert kwargs["local_files_only"] is True
            raise OSError("network unreachable")

    monkeypatch.setattr("fastembed.TextEmbedding", _Boom)
    with pytest.raises(LocalEmbedUnavailable) as raised:
        _load_model()
    message = str(raised.value)
    assert LOCAL_EMBED_MODEL in message
    assert str(tmp_path) in message
    assert "exc_type=OSError" in message
    assert "warmup_local_embed.py" in message
    assert "FASTEMBED_CACHE_PATH" in message
    monkeypatch.setattr(mod, "_model", None)


def test_warmup_script_refuses_offline(tmp_path):
    env = os.environ.copy()
    env["FRESHLATCH_EMBED_OFFLINE"] = "1"
    env["FASTEMBED_CACHE_PATH"] = str(tmp_path)
    env.pop("HF_HUB_OFFLINE", None)
    root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [sys.executable, "scripts/warmup_local_embed.py"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert LOCAL_EMBED_MODEL in proc.stderr
    assert "FASTEMBED_CACHE_PATH" in proc.stderr
    assert "ok model=" not in proc.stdout
