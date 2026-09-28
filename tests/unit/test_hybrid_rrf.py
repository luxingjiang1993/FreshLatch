"""#162:RRF 融合与三列通过线。合成向量,不打网。"""

from types import SimpleNamespace

from freshlatch.eval.retrieve_eval import A0_BM25_RECALL_TOLERANCE, arm_pass_line
from freshlatch.store.base import Chunk, InMemoryStore, chunk_evidence_id
from freshlatch.store.pipeline import RRF_K, pack_vec, rrf_fuse


def _chunk(doc_id: str, text: str, vec: list[float] | None) -> Chunk:
    return Chunk(
        doc_id=doc_id, chunk_id=f"{doc_id}-p1", clause_id="p1", title="t",
        text=text, source_type="public", as_of="T1", doc_version="v1",
        checksum="", tokens=4, vec=None if vec is None else pack_vec(vec),
    )


def test_rrf_k_is_locked_and_prefers_dual_hit():
    only_left = _chunk("left", "只在词法前列", [0.0, 1.0])
    both = _chunk("both", "两路都靠前", [1.0, 0.0])
    fused = rrf_fuse([both, only_left], [both], k=RRF_K, top_k=2)
    assert RRF_K == 60
    assert [chunk_evidence_id(c) for c in fused][0] == "both#p1@T1"


def test_hybrid_mode_fuses_and_missing_vec_is_not_hybrid():
    near = _chunk("near", "席位标价 八十", [1.0, 0.0])
    far = _chunk("far", "无关旁注", [0.0, 1.0])
    store = InMemoryStore()
    store.add_document(
        SimpleNamespace(doc_id="d", as_of="T1", source_type="public",
                        title="t", doc_version="v1", checksum="", full_text="x"),
        [far, near],
    )
    store.query_embedder = lambda _q: [1.0, 0.0]
    store.bind_eval_retrieval_mode("hybrid")
    hits = store.retrieve("席位标价", as_of="T1", top_k=2)
    assert store.last_retrieval_mode == "hybrid"
    assert chunk_evidence_id(hits[0]) == "near#p1@T1"

    bare = _chunk("bare", "席位标价 八十", None)
    store2 = InMemoryStore()
    store2.add_document(
        SimpleNamespace(doc_id="d", as_of="T1", source_type="public",
                        title="t", doc_version="v1", checksum="", full_text="x"),
        [bare],
    )
    store2.query_embedder = lambda _q: [1.0, 0.0]
    store2.bind_eval_retrieval_mode("hybrid")
    store2.retrieve("席位标价", as_of="T1", top_k=1)
    assert store2.last_retrieval_mode == "bm25_fallback"


def test_pass_line_is_explicit():
    assert A0_BM25_RECALL_TOLERANCE == 0.0
    ok = arm_pass_line(bm25=1.0, dense=0.8, hybrid=0.8, a0=1.0)
    assert ok["pass"] is True
    assert ok["hybrid_vs_min"] == "pass"
    assert ok["bm25_vs_a0"] == "pass"
    low_hybrid = arm_pass_line(bm25=1.0, dense=0.9, hybrid=0.8, a0=1.0)
    assert low_hybrid["hybrid_vs_min"] == "fail"
    assert low_hybrid["pass"] is False
    regressed = arm_pass_line(bm25=0.9, dense=0.9, hybrid=0.9, a0=1.0)
    assert regressed["bm25_vs_a0"] == "fail"


def test_rerank_default_stays_off_unless_both_gates_pass():
    from freshlatch.eval.retrieve_eval import RERANK_P95_BUDGET_MS, rerank_default_verdict
    from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
    from freshlatch.store.pipeline import rerank_lexical

    assert PRODUCTION_RETRIEVAL_MODE == "bm25"
    assert RERANK_P95_BUDGET_MS == 800.0
    assert rerank_default_verdict(hybrid=1.0, rerank=1.0, p95_ms=10) == "生产默认关"
    assert rerank_default_verdict(hybrid=0.5, rerank=0.8, p95_ms=900) == "生产默认关"
    assert rerank_default_verdict(hybrid=0.5, rerank=0.8, p95_ms=100) == "生产默认开"
    head = _chunk("head", "席位标价已经改写", [1.0, 0.0])
    tail = _chunk("tail", "无关旁注", [0.2, 0.8])
    ranked = rerank_lexical("席位标价", [tail, head], top_k=2)
    assert chunk_evidence_id(ranked[0]) == "head#p1@T1"
