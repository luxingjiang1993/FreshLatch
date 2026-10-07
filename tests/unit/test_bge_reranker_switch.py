"""#294: 生产精排切到 BAAI/bge-reranker-base。mock 编码器，不下载权重。"""

import logging
from pathlib import Path

import pytest

from freshlatch.runner import RETRIEVAL_SWITCH_MODES, RunContext
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE, Chunk, Document, InMemoryStore, chunk_evidence_id
from freshlatch.store.neural_rerank import (
    NEURAL_RERANK_K,
    NEURAL_RERANK_MODEL,
    RERANK_MODE_FALLBACK,
    RERANK_MODE_LEXICAL,
    RERANK_MODE_NEURAL,
    RERANK_MODE_NONE,
    NeuralRerankUnavailable,
    _load_encoder,
    neural_rerank_unavailable_message,
    rerank_hybrid_candidates,
)
from freshlatch.store.pipeline import pack_vec, rerank_lexical
from freshlatch.store.sqlite_store import SQLiteStore


def _chunk(doc_id: str, text: str, vec: list[float] | None, *, clause: str = "p1") -> Chunk:
    return Chunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}::chunk-{clause}@T1",
        clause_id=clause,
        title="t",
        text=text,
        source_type="private",
        as_of="T1",
        doc_version="v1",
        checksum="c",
        tokens=4,
        vec=None if vec is None else pack_vec(vec),
    )


def _doc() -> Document:
    return Document(
        doc_id="d",
        as_of="T1",
        source_type="private",
        title="t",
        doc_version="v1",
        checksum="c",
        full_text="x",
    )


def _store(chunks: list[Chunk]) -> InMemoryStore:
    store = InMemoryStore()
    store.add_document(_doc(), chunks)
    store.query_embedder = lambda _q: [1.0, 0.0]
    return store


class _PreferTail:
    def rerank(self, query: str, docs: list[str]) -> list[float]:
        return [1.0 if "旁注" in doc else 0.0 for doc in docs]


class _Recording:
    def __init__(self) -> None:
        self.docs: list[str] = []

    def rerank(self, query: str, docs: list[str]) -> list[float]:
        self.docs = list(docs)
        return [0.0 for _ in docs]


def _enable(monkeypatch, encoder) -> None:
    monkeypatch.setenv("FRESHLATCH_NEURAL_RERANK", "1")
    monkeypatch.setattr(
        "freshlatch.store.neural_rerank._load_encoder",
        lambda: encoder,
    )


def test_constants_and_switch_set():
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert NEURAL_RERANK_MODEL == "BAAI/bge-reranker-base"
    assert NEURAL_RERANK_K == 10
    assert "hybrid+rerank_lexical" in RETRIEVAL_SWITCH_MODES
    assert "bm25" in RETRIEVAL_SWITCH_MODES
    source = Path("src/freshlatch/store/neural_rerank.py").read_text(encoding="utf-8")
    assert "dashscope" not in source.lower()
    assert "text-embedding-v4" not in source.lower()


def test_neural_reorders_top10_and_records_mode(monkeypatch):
    _enable(monkeypatch, _PreferTail())
    head = _chunk("head", "席位标价已经改写", [1.0, 0.0])
    tail = _chunk("tail", "无关旁注", [0.0, 1.0], clause="p2")
    ranked, mode = rerank_hybrid_candidates(
        "席位标价",
        [head, tail],
        top_k=2,
        lexical_only=False,
    )
    assert mode == RERANK_MODE_NEURAL
    assert chunk_evidence_id(ranked[0]) == "tail#p2@T1"

    store = _store([head, tail])
    store.bind_eval_retrieval_mode("hybrid+rerank")
    hits = store.retrieve("席位标价", as_of="T1", top_k=2)
    assert store.last_retrieval_mode == "hybrid+rerank"
    assert store.last_rerank_mode == RERANK_MODE_NEURAL
    assert chunk_evidence_id(hits[0]) == "tail#p2@T1"


def test_encoder_input_is_capped_at_10(monkeypatch):
    recorder = _Recording()
    _enable(monkeypatch, recorder)
    chunks = [
        _chunk(f"d{i}", f"席位文本{i}", [1.0, 0.0], clause=f"p{i}")
        for i in range(12)
    ]
    ranked, mode = rerank_hybrid_candidates("席位", chunks, top_k=12, lexical_only=False)
    assert mode == RERANK_MODE_NEURAL
    assert len(recorder.docs) == 10
    assert len(ranked) == 12
    assert [chunk_evidence_id(c) for c in ranked[10:]] == [
        chunk_evidence_id(c) for c in chunks[10:]
    ]

    store = _store(chunks)
    store.bind_eval_retrieval_mode("hybrid+rerank")
    hits = store.retrieve("席位", as_of="T1", top_k=12)
    assert store.last_rerank_mode == RERANK_MODE_NEURAL
    assert len(hits) == 12


def test_inference_error_falls_back_to_lexical(monkeypatch, caplog):
    def _boom():
        raise RuntimeError("onnx failed")

    monkeypatch.setenv("FRESHLATCH_NEURAL_RERANK", "1")
    monkeypatch.setattr("freshlatch.store.neural_rerank._load_encoder", _boom)
    head = _chunk("head", "席位标价已经改写", [1.0, 0.0])
    tail = _chunk("tail", "无关旁注", [0.0, 1.0], clause="p2")
    lexical = rerank_lexical("席位标价", [tail, head], top_k=2)
    caplog.set_level(logging.WARNING)
    ranked, mode = rerank_hybrid_candidates(
        "席位标价",
        [tail, head],
        top_k=2,
        lexical_only=False,
    )
    assert mode == RERANK_MODE_FALLBACK
    assert [chunk_evidence_id(c) for c in ranked] == [chunk_evidence_id(c) for c in lexical]
    warning = caplog.text
    assert "last_rerank_mode=lexical_fallback" in warning
    assert NEURAL_RERANK_MODEL in warning
    assert "exc_type=RuntimeError" in warning

    store = _store([head, tail])
    store.bind_eval_retrieval_mode("hybrid+rerank")
    store.retrieve("席位标价", as_of="T1", top_k=2)
    assert store.last_retrieval_mode == "hybrid+rerank"
    assert store.last_rerank_mode == RERANK_MODE_FALLBACK


def test_disabled_env_does_not_load_encoder(monkeypatch, caplog):
    def _boom():
        raise AssertionError("不应加载 reranker")

    monkeypatch.setenv("FRESHLATCH_NEURAL_RERANK", "0")
    monkeypatch.setattr("freshlatch.store.neural_rerank._load_encoder", _boom)
    caplog.set_level(logging.WARNING)
    head = _chunk("head", "席位标价已经改写", [1.0, 0.0])
    _ranked, mode = rerank_hybrid_candidates("席位标价", [head], top_k=1, lexical_only=False)
    assert mode == RERANK_MODE_FALLBACK
    assert "FRESHLATCH_NEURAL_RERANK=0" in caplog.text
    assert NEURAL_RERANK_MODEL in caplog.text


def test_lexical_switch_and_bm25_rollback(monkeypatch):
    _enable(monkeypatch, _PreferTail())
    head = _chunk("head", "席位标价已经改写", [1.0, 0.0])
    tail = _chunk("tail", "无关旁注", [0.0, 1.0], clause="p2")
    store = _store([head, tail])
    ctx = RunContext(store=store, mode="online")
    ctx.set_retrieval_switch("hybrid+rerank_lexical")
    hits = ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert ctx.events[-1]["retrieval_mode"] == "hybrid+rerank_lexical"
    assert ctx.events[-1]["rerank_mode"] == RERANK_MODE_LEXICAL
    assert chunk_evidence_id(hits[0]) == "head#p1@T1"
    assert store.last_rerank_mode == RERANK_MODE_LEXICAL
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"

    ctx.set_retrieval_switch("bm25")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert ctx.events[-1]["retrieval_mode"] == "bm25"
    assert ctx.events[-1]["rerank_mode"] == RERANK_MODE_NONE
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"


def test_sqlite_records_neural_mode(monkeypatch, tmp_path):
    _enable(monkeypatch, _PreferTail())
    store = SQLiteStore(tmp_path / "r.db")
    head = _chunk("head", "席位标价已经改写", [1.0, 0.0])
    tail = _chunk("tail", "无关旁注", [0.0, 1.0], clause="p2")
    store.add_document(_doc(), [head, tail])
    store.query_embedder = lambda _q: [1.0, 0.0]
    store.bind_eval_retrieval_mode("hybrid+rerank")
    hits = store.retrieve("席位标价", as_of="T1", top_k=2)
    assert store.last_retrieval_mode == "hybrid+rerank"
    assert store.last_rerank_mode == RERANK_MODE_NEURAL
    assert chunk_evidence_id(hits[0]) == "tail#p2@T1"


def test_load_encoder_offline_names_model_and_cache(monkeypatch, tmp_path):
    import freshlatch.store.neural_rerank as mod

    monkeypatch.setattr(mod, "_encoder", None)
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path))
    monkeypatch.setenv("FRESHLATCH_EMBED_OFFLINE", "1")

    class _Boom:
        def __init__(self, **kwargs):
            assert kwargs["model_name"] == NEURAL_RERANK_MODEL
            assert kwargs["cache_dir"] == str(tmp_path)
            assert kwargs["cuda"] is False
            assert kwargs["local_files_only"] is True
            raise OSError("network unreachable")

    monkeypatch.setattr(mod, "_cross_encoder_cls", lambda: _Boom)
    with pytest.raises(NeuralRerankUnavailable) as raised:
        _load_encoder()
    message = str(raised.value)
    assert NEURAL_RERANK_MODEL in message
    assert str(tmp_path) in message
    assert "exc_type=OSError" in message
    assert "warmup_local_embed.py" in message
    assert message == neural_rerank_unavailable_message(OSError("network unreachable"))
    monkeypatch.setattr(mod, "_encoder", None)
