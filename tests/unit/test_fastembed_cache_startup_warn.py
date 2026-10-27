"""P0 余量:UI 启动未设/已设 FASTEMBED_CACHE_PATH 的硬警告分支。"""

from __future__ import annotations

import logging

from freshlatch.store.local_embed import EMBED_CACHE_ENV
from freshlatch.ui.weight_precheck import (
    resolved_cache_dir,
    warn_if_fastembed_cache_path_unset,
)


def test_warn_when_fastembed_cache_path_unset(monkeypatch, capsys, caplog):
    """未设 env → stderr/日志含 FASTEMBED_CACHE_PATH,并带当前解析根(临时目录)。"""
    monkeypatch.delenv(EMBED_CACHE_ENV, raising=False)
    with caplog.at_level(logging.WARNING, logger="freshlatch.ui.weight_precheck"):
        msg = warn_if_fastembed_cache_path_unset()
    assert msg is not None
    assert EMBED_CACHE_ENV in msg
    assert "临时目录" in msg
    resolved = resolved_cache_dir()
    assert resolved in msg
    err = capsys.readouterr().err
    assert EMBED_CACHE_ENV in err
    assert resolved in err
    assert any(EMBED_CACHE_ENV in r.message for r in caplog.records)


def test_no_warn_when_fastembed_cache_path_set(monkeypatch, capsys, tmp_path, caplog):
    """已设 FASTEMBED_CACHE_PATH → 不刷该警告。"""
    monkeypatch.setenv(EMBED_CACHE_ENV, str(tmp_path))
    with caplog.at_level(logging.WARNING, logger="freshlatch.ui.weight_precheck"):
        msg = warn_if_fastembed_cache_path_unset()
    assert msg is None
    err = capsys.readouterr().err
    assert EMBED_CACHE_ENV not in err
    assert not any(EMBED_CACHE_ENV in r.message for r in caplog.records)
