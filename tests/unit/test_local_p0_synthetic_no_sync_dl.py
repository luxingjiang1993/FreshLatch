"""#752 LOCAL-P0-SYNTHETIC-NO-SYNC-DL:入库缺快照不得同步下载权重。"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.store.local_embed as local_embed
import freshlatch.ui.app as appmod
from freshlatch.store.base import Chunk, Document
from freshlatch.store.local_embed import (
    LOCAL_EMBED_DIM,
    embed_texts_local,
    fill_chunk_vecs,
)
from freshlatch.store.pipeline import unpack_vec
from freshlatch.store.sqlite_store import SQLiteStore


def _doc(text: str = "席位标价八十") -> Document:
    return Document(
        doc_id="d",
        as_of="T1",
        source_type="private",
        title="t",
        doc_version="v1",
        checksum="c",
        full_text=text,
    )


def _chunk(text: str = "席位标价八十") -> Chunk:
    return Chunk(
        doc_id="d",
        chunk_id="d::chunk-p1@T1",
        clause_id="p1",
        title="t",
        text=text,
        source_type="private",
        as_of="T1",
        doc_version="v1",
        checksum="c",
        tokens=4,
        vec=None,
    )


def _plant_embed_onnx(root: Path) -> None:
    d = root / "models--BAAI--bge-small-zh-v1.5" / "snapshots" / "rev" / "onnx"
    d.mkdir(parents=True)
    (d / "model.onnx").write_bytes(b"w")


class _FakeEmbedModel:
    def embed(self, texts):
        for _ in texts:
            yield [0.1] * LOCAL_EMBED_DIM


def test_add_document_cold_cache_skips_download_and_keeps_writing(
    tmp_path, monkeypatch, caplog,
):
    """验收1/2:缺快照时不调 _load_model,正文仍入库,vec 为空。"""
    cache = tmp_path / "empty_cache"
    cache.mkdir()
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(cache))
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    monkeypatch.delenv("FRESHLATCH_EMBED_OFFLINE", raising=False)
    load_calls: list[str] = []

    def _boom_load():
        load_calls.append("load")
        raise AssertionError("冷缓存不得加载/下载模型")

    monkeypatch.setattr(local_embed, "_load_model", _boom_load)
    local_embed._model = None

    store = SQLiteStore(tmp_path / "cold.db")
    store.chunk_embedder = embed_texts_local
    with caplog.at_level("WARNING"):
        store.add_document(_doc(), [_chunk()])
    stored = store.get_chunk("d", "p1", as_of="T1")
    assert stored is not None
    assert stored.text == "席位标价八十"
    assert stored.vec is None
    assert load_calls == []
    assert not any(cache.rglob("*.onnx"))
    assert any("LocalEmbedUnavailable" in r.message for r in caplog.records)


def test_add_document_hot_cache_still_fills_vecs(tmp_path, monkeypatch):
    """验收3:文件层快照就绪时仍可经 embed_texts_local 补 vec。"""
    cache = tmp_path / "hot_cache"
    _plant_embed_onnx(cache)
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(cache))
    local_embed._model = None
    monkeypatch.setattr(local_embed, "_load_model", lambda: _FakeEmbedModel())

    store = SQLiteStore(tmp_path / "hot.db")
    store.chunk_embedder = embed_texts_local
    store.add_document(_doc(), [_chunk()])
    stored = store.get_chunk("d", "p1", as_of="T1")
    assert stored is not None
    assert unpack_vec(stored.vec) == pytest.approx([0.1] * LOCAL_EMBED_DIM)


def test_injected_embedder_unaffected_by_cold_gate(tmp_path, monkeypatch):
    """注入 embedder 不走快照门闩(与 #286 热路径一致)。"""
    cache = tmp_path / "empty"
    cache.mkdir()
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(cache))
    store = SQLiteStore(tmp_path / "inj.db")
    store.chunk_embedder = lambda texts: [[0.2, 0.8] for _ in texts]
    bare = _chunk()
    fill_chunk_vecs([bare], store.chunk_embedder)
    store.add_document(_doc(), [bare])
    assert unpack_vec(store.get_chunk("d", "p1", as_of="T1").vec) == pytest.approx(
        [0.2, 0.8]
    )


def test_synthetic_api_cold_cache_returns_within_5s(tmp_path, monkeypatch):
    """验收1:POST synthetic 冷缓存 ≤5s,不触下载。"""
    cache = tmp_path / "api_cache"
    cache.mkdir()
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(cache))
    monkeypatch.setenv("FRESHLATCH_LOCAL_EMBED", "1")
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    monkeypatch.delenv("FRESHLATCH_EMBED_OFFLINE", raising=False)
    monkeypatch.setattr(
        local_embed, "_load_model",
        lambda: (_ for _ in ()).throw(AssertionError("synthetic 不得同步下载")),
    )
    local_embed._model = None

    store = SQLiteStore(tmp_path / "api.db")
    local_embed.attach_local_embedder(store)
    assert store.chunk_embedder is embed_texts_local

    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "CORPUS", appmod.REPO_ROOT / "data" / "corpus")
    appmod._state.update({
        "claims": [], "question": "", "trajectory": None,
        "running": False, "latch": dict(appmod.EMPTY_LATCH),
    })
    appmod._reset_t1_source(store)
    client = TestClient(appmod.app)

    t0 = time.perf_counter()
    r = client.post("/api/t1-source/synthetic")
    elapsed = time.perf_counter() - t0
    assert r.status_code == 200
    body = r.json()
    assert body["ready"] is True
    assert body["synthetic"] is True
    assert body["ingested_chunks"] > 0
    assert elapsed <= 5.0
    assert not any(cache.rglob("*.onnx"))
    assert store.count_missing_vecs() > 0


def test_production_retrieval_mode_untouched():
    """验收4:本票不改检索默认臂常量。"""
    from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
