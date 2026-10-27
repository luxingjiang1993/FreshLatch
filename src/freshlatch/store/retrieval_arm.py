"""检索臂分派与缺向量降级(InMemory / SQLite 共用)。

字面量契约禁止变:
- last_retrieval_mode: dense | hybrid | hybrid+rerank | hybrid+rerank_lexical
  | bm25 | bm25_fallback
- last_rerank_mode: none | 由 rerank_hybrid_candidates 回传
  (lexical / lexical_fallback / bge-reranker-base 等)

缺可用 dense 向量时不得把结果标成 dense/hybrid/hybrid+rerank*,必须记 bm25_fallback。
本模块不碰 PRODUCTION_RETRIEVAL_MODE,也不引入 ui 依赖。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from freshlatch.store.base import Chunk
from freshlatch.store.neural_rerank import RERANK_MODE_NONE, rerank_hybrid_candidates
from freshlatch.store.pipeline import RRF_K, rank_dense, recall_bm25, rrf_fuse

# 知情降级 / 缺向量降级共用同一字面量(与轨迹、预检面板契约对齐)。
BM25_FALLBACK_MODE = "bm25_fallback"
HYBRID_RERANK_MODES = frozenset({"hybrid+rerank", "hybrid+rerank_lexical"})

EmbedQuery = Callable[[str], list[float] | None]
# (query, pool, top_k) -> hits;SQLite 默认臂可注入 run_pipeline。
DefaultBm25 = Callable[[str, list[Chunk], int], list[Chunk]]


@dataclass(frozen=True)
class RetrievalArmResult:
    """一次分派的命中与可观测模式字面量。"""

    hits: list[Chunk]
    retrieval_mode: str
    rerank_mode: str


def _bm25_only(query: str, pool: list[Chunk], top_k: int) -> list[Chunk]:
    return recall_bm25(query, pool, top_k=top_k)


def dispatch_retrieval_arm(
    query: str,
    pool: list[Chunk],
    *,
    top_k: int,
    requested: str | None,
    embed_query: EmbedQuery,
    default_bm25: DefaultBm25 | None = None,
) -> RetrievalArmResult:
    """按 requested 臂跑召回;写死降级与模式字面量,供两处 store.retrieve 共用。

    default_bm25:未绑臂 / 显式 bm25 时的默认词法路径。缺省 = recall_bm25
    (内存假实现);SQLite 传入 run_pipeline 以保留其既有默认臂管线。
    """
    bm25_default = default_bm25 or _bm25_only

    if requested == "dense":
        query_vec = embed_query(query)
        ranked = rank_dense(query_vec, pool, top_k=top_k) if query_vec else None
        if ranked is None:
            return RetrievalArmResult(
                recall_bm25(query, pool, top_k=top_k),
                BM25_FALLBACK_MODE,
                RERANK_MODE_NONE,
            )
        return RetrievalArmResult(ranked, "dense", RERANK_MODE_NONE)

    if requested == "hybrid":
        depth = max(top_k, len(pool))
        lexical = recall_bm25(query, pool, top_k=depth)
        query_vec = embed_query(query)
        dense = rank_dense(query_vec, pool, top_k=depth) if query_vec else None
        if dense is None:
            return RetrievalArmResult(
                recall_bm25(query, pool, top_k=top_k),
                BM25_FALLBACK_MODE,
                RERANK_MODE_NONE,
            )
        return RetrievalArmResult(
            rrf_fuse(lexical, dense, k=RRF_K, top_k=top_k),
            "hybrid",
            RERANK_MODE_NONE,
        )

    if requested in HYBRID_RERANK_MODES:
        depth = max(top_k, len(pool))
        lexical = recall_bm25(query, pool, top_k=depth)
        query_vec = embed_query(query)
        dense = rank_dense(query_vec, pool, top_k=depth) if query_vec else None
        if dense is None:
            return RetrievalArmResult(
                recall_bm25(query, pool, top_k=top_k),
                BM25_FALLBACK_MODE,
                RERANK_MODE_NONE,
            )
        fused = rrf_fuse(lexical, dense, k=RRF_K, top_k=top_k)
        hits, rerank_mode = rerank_hybrid_candidates(
            query,
            fused,
            top_k=top_k,
            lexical_only=requested == "hybrid+rerank_lexical",
        )
        # 请求臂字面量原样回写(含 hybrid+rerank_lexical);精排模式单独记。
        return RetrievalArmResult(hits, requested, rerank_mode)

    if requested == BM25_FALLBACK_MODE:
        return RetrievalArmResult(
            recall_bm25(query, pool, top_k=top_k),
            BM25_FALLBACK_MODE,
            RERANK_MODE_NONE,
        )

    # 未绑臂 / 显式 bm25 / 其它未知:记 bm25(不是 bm25_fallback)。
    return RetrievalArmResult(
        bm25_default(query, pool, top_k),
        "bm25",
        RERANK_MODE_NONE,
    )
