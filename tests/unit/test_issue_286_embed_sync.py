"""#286: 入库补向量、正文变化作废旧 vec、单块缺失不整池 fallback、运维开关。

不下载 BAAI 权重，不调用 DashScope。embedder 全部注入。
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.runner import RunContext
from freshlatch.store.base import (
    PRODUCTION_RETRIEVAL_MODE,
    Chunk,
    Document,
    InMemoryStore,
    chunk_evidence_id,
)
from freshlatch.store.ingest import parse_document_text
from freshlatch.store.local_embed import (
    LOCAL_EMBED_DIM,
    LOCAL_EMBED_MODEL,
    attach_local_embedder,
    embed_texts_local,
    fill_chunk_vecs,
)
from freshlatch.store.pipeline import pack_vec, rank_dense, unpack_vec
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.t1_source import T1SourceSession


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


def _doc(doc_id: str = "d", text: str = "x") -> Document:
    return Document(
        doc_id=doc_id,
        as_of="T1",
        source_type="private",
        title="t",
        doc_version="v1",
        checksum="c",
        full_text=text,
    )


def _mem(chunks: list[Chunk]) -> InMemoryStore:
    store = InMemoryStore()
    store.add_document(_doc(), chunks)
    return store


def test_injected_embedder_fills_only_missing_vecs():
    seen: list[str] = []

    def embedder(texts: list[str]) -> list[list[float]]:
        seen.extend(texts)
        return [[1.0, 0.0] for _ in texts]

    bare = _chunk("d", "新块", None)
    kept = _chunk("d", "旧块", [0.0, 1.0], clause="p2")
    fill_chunk_vecs([bare, kept], embedder)
    assert seen == ["新块"]
    assert unpack_vec(bare.vec) == [1.0, 0.0]
    assert unpack_vec(kept.vec) == [0.0, 1.0]


def test_parse_then_add_document_writes_vec_via_chunk_embedder(tmp_path):
    md = (
        "---\n"
        "doc_id: paste-change\n"
        "as_of: T1\n"
        "source_type: private\n"
        "title: 粘贴\n"
        "---\n"
        "## p1\n"
        "席位标价八十\n"
    )
    doc, chunks = parse_document_text(md)
    assert chunks[0].vec is None
    store = SQLiteStore(tmp_path / "parse.db")
    store.chunk_embedder = lambda texts: [[0.2, 0.8] for _ in texts]
    store.add_document(doc, chunks)
    stored = store.get_chunk("paste-change", "p1", as_of="T1")
    assert unpack_vec(stored.vec) == pytest.approx([0.2, 0.8])


def test_confirm_paste_uses_store_embedder(tmp_path):
    store = SQLiteStore(tmp_path / "paste.db")
    store.chunk_embedder = lambda texts: [[0.4, 0.6] for _ in texts]
    session = T1SourceSession(store)
    session.save_paste_draft("席位标价八十")
    result = session.confirm_paste()
    assert result.ok
    stored = store.get_chunk(session.draft_doc_id, "p1", as_of="T1")
    assert unpack_vec(stored.vec) == pytest.approx([0.4, 0.6])


def test_same_text_keeps_vec_and_text_change_reembeds(tmp_path):
    store = SQLiteStore(tmp_path / "sync.db")
    store.add_document(_doc(text="旧正文"), [_chunk("d", "旧正文", [1.0, 0.0])])

    store.add_document(_doc(text="旧正文"), [_chunk("d", "旧正文", None)])
    kept = store.get_chunk("d", "p1", as_of="T1")
    assert unpack_vec(kept.vec) == [1.0, 0.0]

    store.chunk_embedder = lambda texts: [[0.0, 1.0] for _ in texts]
    store.add_document(_doc(text="再次替换"), [_chunk("d", "再次替换", [1.0, 0.0])])
    updated = store.get_chunk("d", "p1", as_of="T1")
    assert updated.text == "再次替换"
    assert unpack_vec(updated.vec) == [0.0, 1.0]


def test_text_change_without_embedder_drops_stale_vec(tmp_path):
    store = SQLiteStore(tmp_path / "stale.db")
    near = _chunk("d", "席位标价", [1.0, 0.0], clause="p1")
    other = _chunk("d", "旁注", [0.0, 1.0], clause="p2")
    store.add_document(_doc(text="席位标价"), [near, other])
    store.query_embedder = lambda _q: [1.0, 0.0]
    store.bind_eval_retrieval_mode("dense")
    hits = store.retrieve("席位标价", as_of="T1", top_k=5)
    assert store.last_retrieval_mode == "dense"
    assert chunk_evidence_id(hits[0]) == "d#p1@T1"

    store.add_document(
        _doc(text="渠道访谈纪要"),
        [_chunk("d", "渠道访谈纪要", [1.0, 0.0], clause="p1")],
    )
    stored = store.get_chunk("d", "p1", as_of="T1")
    assert stored.text == "渠道访谈纪要"
    assert stored.vec is None

    store.bind_eval_retrieval_mode("dense")
    hits = store.retrieve("席位标价", as_of="T1", top_k=5)
    assert store.last_retrieval_mode == "dense"
    assert [chunk_evidence_id(c) for c in hits] == ["d#p2@T1"]

    store.add_document(
        _doc(text="旁注已改"),
        [_chunk("d", "旁注已改", None, clause="p2")],
    )
    store.bind_eval_retrieval_mode("hybrid")
    fallback = store.retrieve("席位标价", as_of="T1", top_k=5)
    assert store.last_retrieval_mode == "bm25_fallback"
    assert all(c.vec is None for c in fallback)


def test_embedder_failure_logs_and_counts_missing_vecs(tmp_path, caplog):
    import logging

    store = SQLiteStore(tmp_path / "boom.db")
    store.add_document(
        _doc(text="旧正文"),
        [
            _chunk("d", "旧正文", [1.0, 0.0], clause="p1"),
            _chunk("d", "旁注仍在", [0.0, 1.0], clause="p2"),
        ],
    )
    assert store.count_missing_vecs() == 0

    def _boom(_texts: list[str]) -> list[list[float]]:
        raise RuntimeError("embed 断了")

    store.chunk_embedder = _boom
    with caplog.at_level(logging.WARNING):
        store.add_document(
            _doc(text="新正文"),
            [_chunk("d", "新正文", [1.0, 0.0], clause="p1")],
        )
    stored = store.get_chunk("d", "p1", as_of="T1")
    assert stored.text == "新正文"
    assert stored.vec is None
    assert store.count_missing_vecs() == 1
    warning = next(r for r in caplog.records if r.levelno >= logging.WARNING)
    assert "doc_id=d" in warning.message
    assert "exc_type=RuntimeError" in warning.message
    assert "missing_vecs=1" in warning.message
    assert "except Exception: pass" not in Path(
        "src/freshlatch/store/sqlite_store.py"
    ).read_text(encoding="utf-8")


def test_add_invalidation_does_not_clear_vec(tmp_path):
    store = SQLiteStore(tmp_path / "inv.db")
    store.add_document(_doc(), [_chunk("d", "正文", [0.3, 0.7])])
    store.add_invalidation("claim-1", "2026-10-07T00:00:00Z", actor="human", reason="作废")
    stored = store.get_chunk("d", "p1", as_of="T1")
    assert unpack_vec(stored.vec) == pytest.approx([0.3, 0.7])
    assert store.list_invalidation() == ["claim-1"]


def test_one_missing_chunk_does_not_fallback_the_pool():
    near = _chunk("near", "席位标价", [1.0, 0.0])
    bare = _chunk("bare", "缺向量", None, clause="p2")
    ranked = rank_dense([1.0, 0.0], [bare, near], top_k=2)
    assert ranked is not None
    assert [chunk_evidence_id(c) for c in ranked] == ["near#p1@T1"]

    store = _mem([bare, near])
    store.query_embedder = lambda _q: [1.0, 0.0]
    store.bind_eval_retrieval_mode("hybrid")
    store.retrieve("席位标价", as_of="T1", top_k=2)
    assert store.last_retrieval_mode == "hybrid"

    store.bind_eval_retrieval_mode("dense")
    store.retrieve("席位标价", as_of="T1", top_k=2)
    assert store.last_retrieval_mode == "dense"


def test_all_missing_and_bad_dim_only_pool_still_fallback():
    store = _mem([
        _chunk("a", "竞品定价已变", None),
        _chunk("b", "旁注", None, clause="p2"),
    ])
    store.query_embedder = lambda _q: [1.0, 0.0]
    store.bind_eval_retrieval_mode("dense")
    store.retrieve("竞品定价", as_of="T1", top_k=2)
    assert store.last_retrieval_mode == "bm25_fallback"

    wrong = _chunk("w", "维度不符", [1.0, 0.0, 0.0])
    assert rank_dense([1.0, 0.0], [wrong], top_k=1) is None


def test_online_switch_roundtrip_does_not_change_default():
    near = _chunk("near", "席位标价", [1.0, 0.0])
    far = _chunk("far", "无关旁注", [0.0, 1.0], clause="p2")
    store = _mem([far, near])
    store.query_embedder = lambda _q: [1.0, 0.0]
    ctx = RunContext(store=store, mode="online")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert ctx.events[-1]["retrieval_mode"] == "hybrid+rerank"
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"

    ctx.set_retrieval_switch("hybrid")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert ctx.events[-1]["retrieval_mode"] == "hybrid"

    ctx.set_retrieval_switch("hybrid+rerank")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert ctx.events[-1]["retrieval_mode"] == "hybrid+rerank"

    ctx.set_retrieval_switch("bm25")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert ctx.events[-1]["retrieval_mode"] == "bm25"
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"

    bare = RunContext(
        store=_mem([_chunk("bare", "竞品定价已变", None)]),
        mode="online",
    )
    bare.try_retrieve("竞品定价", as_of="T1", top_k=2)
    assert bare.events[-1]["retrieval_mode"] == "bm25_fallback"
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"

    with pytest.raises(RuntimeError, match="生产路径不可强制 retrieval_mode"):
        ctx.arm_eval_retrieval_mode("hybrid")
    with pytest.raises(ValueError):
        ctx.set_retrieval_switch("dense")
    with pytest.raises(ValueError):
        ctx.set_retrieval_switch("faiss")


def test_eval_arm_still_overrides_operator_switch():
    store = _mem([_chunk("near", "席位标价", [1.0, 0.0])])
    store.query_embedder = lambda _q: [1.0, 0.0]
    ctx = RunContext(store=store, mode="eval")
    ctx.set_retrieval_switch("hybrid")
    ctx.arm_eval_retrieval_mode("bm25")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=1)
    assert ctx.events[-1]["retrieval_mode"] == "bm25"
    ctx.arm_eval_retrieval_mode("hybrid+rerank")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=1)
    assert ctx.events[-1]["retrieval_mode"] == "hybrid+rerank"


def test_local_embed_source_has_no_dashscope_and_requirements_pin_fastembed():
    source = Path("src/freshlatch/store/local_embed.py").read_text(encoding="utf-8")
    lowered = source.lower()
    assert "dashscope" not in lowered
    assert "text-embedding-v4" not in lowered
    assert "embeddings" not in lowered
    assert LOCAL_EMBED_MODEL == "BAAI/bge-small-zh-v1.5"
    assert LOCAL_EMBED_DIM == 512
    req = Path("requirements.txt").read_text(encoding="utf-8")
    assert "fastembed==0.7.1" in req
    assert "jieba==0.42.1" in req
    assert "bge-reranker" not in req
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in Path(
        "src/freshlatch/store/base.py"
    ).read_text(encoding="utf-8")


def test_attach_respects_env_and_does_not_call_model(monkeypatch):
    store = SimpleNamespace()
    monkeypatch.setenv("FRESHLATCH_LOCAL_EMBED", "0")
    attach_local_embedder(store)
    assert not hasattr(store, "chunk_embedder")

    monkeypatch.setenv("FRESHLATCH_LOCAL_EMBED", "1")

    def _boom():
        raise AssertionError("不应加载模型")

    monkeypatch.setattr("freshlatch.store.local_embed._load_model", _boom)
    attach_local_embedder(store)
    assert store.chunk_embedder is embed_texts_local
    assert store.query_embedder.__name__ == "embed_query_local"


def test_embed_texts_local_checks_dim_without_network(monkeypatch):
    class _Fake:
        def embed(self, texts):
            return [[0.0, 0.0, 0.0] for _ in texts]

    monkeypatch.setattr(
        "freshlatch.store.local_embed._load_model", lambda: _Fake()
    )
    with pytest.raises(ValueError, match="512"):
        embed_texts_local(["席位"])
