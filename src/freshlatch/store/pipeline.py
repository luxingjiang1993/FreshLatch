"""多 stage 打分管线:recall(BM25+jieba) → [vector 融合,空实现] → [rerank,空实现]。

后两级本期空实现(透传):vec 列已在 schema。生产默认仍是 BM25;
评测可跑 dense/hybrid/rerank 由后续票填实,无增益不得改生产默认(ADR-0003 修订 #156)。
"""

from __future__ import annotations

import math
import struct

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


def pack_vec(values: list[float]) -> bytes:
    """float32 小端,SQLite vec 列的存储形态。不用 FAISS。"""
    return struct.pack("<" + "f" * len(values), *[float(v) for v in values])


def unpack_vec(blob: bytes) -> list[float]:
    if not blob or len(blob) % 4:
        raise ValueError("vec 长度非法")
    return list(struct.unpack("<" + "f" * (len(blob) // 4), blob))


def cosine(a: list[float], b: list[float]) -> float:
    if not a or len(a) != len(b):
        return 0.0
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / math.sqrt(na * nb)


def rank_dense(query_vec: list[float], pool: list[Chunk], *, top_k: int) -> list[Chunk] | None:
    """本地余弦。池中任一缺 vec 或维度不符则返回 None,由调用方降级。"""
    if not pool or not query_vec:
        return None
    scored: list[tuple[float, int, Chunk]] = []
    for i, chunk in enumerate(pool):
        if not chunk.vec:
            return None
        try:
            vec = unpack_vec(chunk.vec)
        except ValueError:
            return None
        scored.append((cosine(query_vec, vec), i, chunk))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [chunk for _score, _i, chunk in scored[:top_k]]


def stage_vector_fuse(chunks: list[Chunk], *, top_k: int) -> list[Chunk]:
    """第 2 级:生产默认仍透传。dense 臂走 rank_dense,不在这里把 BM25 结果改标成 dense。"""
    return chunks[:top_k]


def stage_rerank(chunks: list[Chunk], *, top_k: int) -> list[Chunk]:
    """第 3 级:rerank,本期空实现(透传)。"""
    return chunks[:top_k]


def run_pipeline(query: str, pool: list[Chunk], *, top_k: int = 10) -> list[Chunk]:
    hits = recall_bm25(query, pool, top_k=top_k)
    hits = stage_vector_fuse(hits, top_k=top_k)
    hits = stage_rerank(hits, top_k=top_k)
    return hits
