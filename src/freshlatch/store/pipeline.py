"""多 stage 打分管线:recall(BM25+jieba) → vector 融合 → rerank。

评测臂已可跑 dense / hybrid / rerank(不是本期空实现、后续票填实)。
生产默认是 hybrid+rerank(2026-10-07 真人拍板)。缺可用向量时调用方记 bm25_fallback。一键回退是 set_retrieval_switch("bm25")。
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
    """本地余弦。单个缺 vec 或维度不符的 chunk 跳过。

    没有任何可用 vec 时返回 None,由调用方记 bm25_fallback。
    不再因池中缺一块就把整池降级。
    """
    if not pool or not query_vec:
        return None
    dim = len(query_vec)
    scored: list[tuple[float, int, Chunk]] = []
    for i, chunk in enumerate(pool):
        if not chunk.vec:
            continue
        try:
            vec = unpack_vec(chunk.vec)
        except ValueError:
            continue
        if len(vec) != dim:
            continue
        scored.append((cosine(query_vec, vec), i, chunk))
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [chunk for _score, _i, chunk in scored[:top_k]]


# 预登记:RRF 常数取 Cormack 常用值,不按本轮指标回改。生产默认不走这条融合。
RRF_K = 60


def rrf_fuse(
    left: list[Chunk],
    right: list[Chunk],
    *,
    k: int = RRF_K,
    top_k: int = 10,
) -> list[Chunk]:
    """名次倒数融合。不把两路分数做 α 加权。rank 从 1 起。"""
    from freshlatch.store.base import chunk_evidence_id

    scores: dict[str, float] = {}
    seen: dict[str, Chunk] = {}
    first_seen: dict[str, int] = {}
    order = 0
    for ranked in (left, right):
        for rank, chunk in enumerate(ranked, start=1):
            eid = chunk_evidence_id(chunk)
            if eid not in seen:
                seen[eid] = chunk
                first_seen[eid] = order
                order += 1
                scores[eid] = 0.0
            scores[eid] += 1.0 / (k + rank)
    ranked_ids = sorted(scores, key=lambda eid: (-scores[eid], first_seen[eid]))
    return [seen[eid] for eid in ranked_ids[:top_k]]


def stage_vector_fuse(chunks: list[Chunk], *, top_k: int) -> list[Chunk]:
    """第 2 级:生产默认仍透传。dense 臂走 rank_dense,hybrid 臂走 rrf_fuse。"""
    return chunks[:top_k]


def stage_rerank(chunks: list[Chunk], *, top_k: int) -> list[Chunk]:
    """第 3 级:生产默认仍透传。对比臂走 rerank_lexical,无增益不改这里。"""
    return chunks[:top_k]


def rerank_lexical(query: str, chunks: list[Chunk], *, top_k: int) -> list[Chunk]:
    """本地词重叠精排,只重排已有候选。不是 bge,也不做 α 加权。"""
    query_tokens = set(tokenize(query))
    scored: list[tuple[int, int, Chunk]] = []
    for index, chunk in enumerate(chunks):
        overlap = len(query_tokens & set(tokenize(chunk.text))) if query_tokens else 0
        scored.append((overlap, -index, chunk))
    scored.sort(reverse=True)
    return [chunk for _overlap, _index, chunk in scored[:top_k]]


def run_pipeline(query: str, pool: list[Chunk], *, top_k: int = 10) -> list[Chunk]:
    hits = recall_bm25(query, pool, top_k=top_k)
    hits = stage_vector_fuse(hits, top_k=top_k)
    hits = stage_rerank(hits, top_k=top_k)
    return hits
