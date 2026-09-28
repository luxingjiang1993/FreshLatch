"""#161:dense 本地余弦与 bm25_fallback。不打网。"""

from types import SimpleNamespace

from freshlatch.runner import RunContext
from freshlatch.store.base import Chunk, InMemoryStore, chunk_evidence_id
from freshlatch.store.pipeline import pack_vec


def _chunk(doc_id: str, text: str, vec: list[float] | None) -> Chunk:
    return Chunk(
        doc_id=doc_id, chunk_id=f"{doc_id}-p1", clause_id="p1", title="t",
        text=text, source_type="public", as_of="T1", doc_version="v1",
        checksum="", tokens=4, vec=None if vec is None else pack_vec(vec),
    )


def _store(chunks: list[Chunk]) -> InMemoryStore:
    store = InMemoryStore()
    store.add_document(
        SimpleNamespace(doc_id="d", as_of="T1", source_type="public",
                        title="t", doc_version="v1", checksum="", full_text="x"),
        chunks,
    )
    return store


def test_dense_returns_ordered_evidence_ids():
    near = _chunk("near", "近邻块", [1.0, 0.0])
    far = _chunk("far", "远块", [0.0, 1.0])
    mid = _chunk("mid", "中间块", [0.6, 0.8])
    store = _store([far, mid, near])
    store.query_embedder = lambda _q: [1.0, 0.0]
    store.bind_eval_retrieval_mode("dense")
    hits = store.retrieve("查询", as_of="T1", top_k=10)
    assert store.last_retrieval_mode == "dense"
    assert [chunk_evidence_id(c) for c in hits][:2] == [
        "near#p1@T1", "mid#p1@T1",
    ]


def test_missing_vec_falls_back_and_is_not_reported_as_dense():
    store = _store([
        _chunk("a", "竞品定价已变", None),
        _chunk("b", "市场杂项旁注", None),
        _chunk("c", "渠道访谈纪要", None),
    ])
    store.query_embedder = lambda _q: [1.0, 0.0]
    ctx = RunContext(store=store, mode="eval")
    ctx.arm_eval_retrieval_mode("dense")
    ctx.try_retrieve("竞品定价", as_of="T1", top_k=10)
    ev = ctx.events[-1]
    assert ev["retrieval_mode"] == "bm25_fallback"
    assert ev["retrieval_mode"] != "dense"
    assert ev["evidence_ids"]


def test_embedder_failure_is_fallback():
    store = _store([_chunk("near", "近邻块", [1.0, 0.0])])
    def _boom(_q):
        raise RuntimeError("断 embed")
    store.query_embedder = _boom
    store.bind_eval_retrieval_mode("dense")
    store.retrieve("查询", as_of="T1")
    assert store.last_retrieval_mode == "bm25_fallback"
