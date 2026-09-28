"""多 stage 打分管线:recall(BM25+jieba) → [vector 融合,空实现] → [rerank,空实现]。

后两级本期空实现(透传):vec 列已在 schema。生产默认仍是 BM25;
评测可跑 dense/hybrid/rerank 由后续票填实,无增益不得改生产默认(ADR-0003 修订 #156)。
"""

from __future__ import annotations

import jieba
from rank_bm25 import BM25Okapi

from freshlatch.store.base import Chunk


def tokenize(text: str) -> list[str]:
    return [t for t in jieba.lcut(text) if t.strip()]


def recall_bm25(query: str, pool: list[Chunk], *, top_k: int = 10) -> list[Chunk]:
    """第 1 级:BM25Okapi 词法召回。空池安全返回空列表。"""
    if not pool:
        return []
    corpus = [tokenize(c.text) for c in pool]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(scores, pool), key=lambda x: x[0], reverse=True)
    return [c for s, c in ranked[:top_k] if s > 0]


def stage_vector_fuse(chunks: list[Chunk], *, top_k: int) -> list[Chunk]:
    """第 2 级:vector 融合,本期空实现(透传)。熔断条件见 §8.5。"""
    return chunks[:top_k]


def stage_rerank(chunks: list[Chunk], *, top_k: int) -> list[Chunk]:
    """第 3 级:rerank,本期空实现(透传)。"""
    return chunks[:top_k]


def run_pipeline(query: str, pool: list[Chunk], *, top_k: int = 10) -> list[Chunk]:
    hits = recall_bm25(query, pool, top_k=top_k)
    hits = stage_vector_fuse(hits, top_k=top_k)
    hits = stage_rerank(hits, top_k=top_k)
    return hits
