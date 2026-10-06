"""RET-01.2：x1 embedding 内容哈希缓存与重建脚本可选路径。

不调用 build_dense_index.main()，不读 DASHSCOPE_API_KEY，不发网络请求。
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest

from freshlatch.store.checksum import sha256_hex
from freshlatch.store.embed_cache import (
    EMBED_CACHE_TABLE,
    embed_texts_cached,
    make_embed_cache_key,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_rebuild_script():
    path = REPO_ROOT / "scripts" / "build_dense_index.py"
    spec = importlib.util.spec_from_file_location("build_dense_index_ret01_2", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # dataclass 在 from __future__ import annotations 下需要模块已登记
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _cache_has_key(cache_path: Path, key: str) -> bool:
    if not cache_path.is_file():
        return False
    conn = sqlite3.connect(cache_path)
    try:
        row = conn.execute(
            f"SELECT 1 FROM {EMBED_CACHE_TABLE} WHERE key = ?",
            (key,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def test_empty_argv_matches_module_constants_and_disables_cache():
    mod = _load_rebuild_script()
    paths = mod.parse_rebuild_paths([])
    assert paths.corpus == mod.CORPUS
    assert paths.traps == mod.TRAPS
    assert paths.db == mod.DB
    assert paths.report == mod.REPORT
    assert paths.cache is None
    assert mod.BATCH == 8


def test_explicit_db_equal_default_is_rejected(tmp_path):
    mod = _load_rebuild_script()
    default_db = str(mod.DB)
    with pytest.raises(mod.RebuildPathError):
        mod.parse_rebuild_paths(["--db", default_db])
    relative = "data/dense/index.sqlite"
    with pytest.raises(mod.RebuildPathError):
        mod.parse_rebuild_paths(["--db", relative, "--cache", str(tmp_path / "c.sqlite")])


def test_non_default_db_requires_cache(tmp_path):
    mod = _load_rebuild_script()
    other = str(tmp_path / "other-index.sqlite")
    with pytest.raises(mod.RebuildPathError):
        mod.parse_rebuild_paths(["--db", other])
    cache = str(tmp_path / "embed-cache.sqlite")
    paths = mod.parse_rebuild_paths(["--db", other, "--cache", cache])
    assert paths.db.resolve() == Path(other).resolve()
    assert paths.cache == Path(cache)
    assert paths.db.resolve() != mod.DB.resolve()


def test_cache_key_matches_locked_formula():
    model = "text-embedding-v4"
    dim = 1024
    text = "同一段正文"
    expected = sha256_hex((model + "\n" + str(dim) + "\n" + text).encode("utf-8"))
    assert make_embed_cache_key(model, dim, text) == expected


def test_model_or_dim_change_recalls_embed_fn(tmp_path):
    cache = tmp_path / "embed-cache.sqlite"
    n_calls = 0

    def fake_embed(texts: list[str], out_dim: int) -> list[list[float]]:
        nonlocal n_calls
        n_calls += 1
        return [[1.0] * out_dim for _ in texts]

    text = "同一文本"
    embed_texts_cached(
        [text], dim=4, cache_path=cache, model="m-a",
        embed_fn=lambda texts: fake_embed(texts, 4),
    )
    embed_texts_cached(
        [text], dim=4, cache_path=cache, model="m-a",
        embed_fn=lambda texts: fake_embed(texts, 4),
    )
    assert n_calls == 1
    embed_texts_cached(
        [text], dim=4, cache_path=cache, model="m-b",
        embed_fn=lambda texts: fake_embed(texts, 4),
    )
    assert n_calls == 2
    embed_texts_cached(
        [text], dim=8, cache_path=cache, model="m-a",
        embed_fn=lambda texts: fake_embed(texts, 8),
    )
    assert n_calls == 3


def test_dim_mismatch_errors_and_does_not_write_key(tmp_path):
    cache = tmp_path / "embed-cache.sqlite"
    text = "维度不符的文本"
    dim = 1024
    key = make_embed_cache_key("m", dim, text)

    def fake_embed(texts: list[str]) -> list[list[float]]:
        return [[1.0, 2.0] for _ in texts]

    with pytest.raises(ValueError, match="嵌入维度不符"):
        embed_texts_cached(
            [text], dim=dim, cache_path=cache, model="m", embed_fn=fake_embed
        )
    assert not _cache_has_key(cache, key)


def test_hit_skips_embed_fn(tmp_path):
    cache = tmp_path / "embed-cache.sqlite"
    calls = 0

    def fake_embed(texts: list[str]) -> list[list[float]]:
        nonlocal calls
        calls += 1
        return [[0.5, 0.25] for _ in texts]

    first = embed_texts_cached(
        ["命中"], dim=2, cache_path=cache, model="m", embed_fn=fake_embed
    )
    second = embed_texts_cached(
        ["命中"], dim=2, cache_path=cache, model="m", embed_fn=fake_embed
    )
    assert calls == 1
    assert first == second
    conn = sqlite3.connect(cache)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert EMBED_CACHE_TABLE in tables
    finally:
        conn.close()
