"""#751 LOCAL-P0-CACHE-ROOT:预检默认缓存根与 fastembed 未设 env 时的落点一致。"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from freshlatch.ui import weight_precheck as wp


def _plant_onnx(root: Path, model_short: str) -> None:
    d = root / f"models--BAAI--{model_short}" / "snapshots" / "rev" / "onnx"
    d.mkdir(parents=True)
    (d / "model.onnx").write_bytes(b"w")


@pytest.fixture()
def no_cache_env(monkeypatch):
    monkeypatch.delenv("FASTEMBED_CACHE_PATH", raising=False)


def test_default_root_is_tempdir_not_home(no_cache_env):
    """验收1:未设 env → gettempdir()/fastembed_cache,不是 ~/.cache。"""
    root = wp.fastembed_default_cache_root()
    expected = Path(tempfile.gettempdir()) / "fastembed_cache"
    assert root == expected
    assert root != Path.home() / ".cache" / "fastembed_cache"
    assert wp._cache_roots(None) == [expected]
    assert wp.FASTEMBED_DEFAULT_CACHE == expected


def test_weights_ready_when_only_in_temp_root(tmp_path, monkeypatch, no_cache_env):
    """验收2:快照只在临时根 → 预检 True(home .cache 空也不影响)。"""
    temp_parent = tmp_path / "tmpdir"
    temp_parent.mkdir()
    temp_root = temp_parent / "fastembed_cache"
    (tmp_path / "home" / ".cache" / "fastembed_cache").mkdir(parents=True)
    _plant_onnx(temp_root, "bge-small-zh-v1.5")
    _plant_onnx(temp_root, "bge-reranker-base")
    monkeypatch.setattr(wp.tempfile, "gettempdir", lambda: str(temp_parent))
    assert wp.local_embed_weights_ready() is True
    assert wp.neural_rerank_weights_ready() is True


def test_weights_missing_when_only_under_home_dot_cache(
    tmp_path, monkeypatch, no_cache_env,
):
    """验收3:仅假 home 下 .cache/fastembed_cache 有快照 → 预检 False。"""
    temp_parent = tmp_path / "tmpdir"
    temp_parent.mkdir()
    (temp_parent / "fastembed_cache").mkdir()
    fake_home = tmp_path / "home"
    home_cache = fake_home / ".cache" / "fastembed_cache"
    _plant_onnx(home_cache, "bge-small-zh-v1.5")
    _plant_onnx(home_cache, "bge-reranker-base")
    monkeypatch.setattr(wp.tempfile, "gettempdir", lambda: str(temp_parent))
    # 夹具:假 home 下确有快照;预检不得再扫该路径
    assert (fake_home / ".cache" / "fastembed_cache").is_dir()
    assert wp.fastembed_default_cache_root() == temp_parent / "fastembed_cache"
    assert wp.local_embed_weights_ready() is False
    assert wp.neural_rerank_weights_ready() is False


def test_explicit_env_only_scans_that_dir(tmp_path, monkeypatch):
    """验收4:设 FASTEMBED_CACHE_PATH 后只查该目录。"""
    explicit = tmp_path / "explicit"
    other = tmp_path / "fastembed_cache"
    _plant_onnx(other, "bge-small-zh-v1.5")
    _plant_onnx(other, "bge-reranker-base")
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(explicit))
    monkeypatch.setattr(wp.tempfile, "gettempdir", lambda: str(tmp_path))
    assert wp._cache_roots(None) == [explicit]
    assert wp.local_embed_weights_ready() is False
    _plant_onnx(explicit, "bge-small-zh-v1.5")
    _plant_onnx(explicit, "bge-reranker-base")
    assert wp.local_embed_weights_ready() is True
    assert wp.neural_rerank_weights_ready() is True
