"""多 stage 打分管线:recall(BM25+jieba) → vector 融合 → rerank。

评测臂已可跑 dense / hybrid / rerank(不是本期空实现、后续票填实)。
生产默认是 hybrid+rerank。精排是本地 BAAI/bge-reranker-base，只重排 hybrid 的前 10 条（见 store/neural_rerank.py）。
缺可用向量时调用方记 bm25_fallback。权重或推理失败时退回 rerank_lexical，记 last_rerank_mode=lexical_fallback。
一键回退 BM25 是 set_retrieval_switch("bm25")。只切回词重叠精排是 set_retrieval_switch("hybrid+rerank_lexical")。
HitScoreBook 只抄当次已经算出的分,不进入排序键,不改 RRF 公式。
"""

from __future__ import annotations

import math
import struct
from contextvars import ContextVar, Token
from dataclasses import dataclass, field

import jieba
from rank_bm25 import BM25Okapi

from freshlatch.store.base import Chunk, chunk_evidence_id

# 工具观察与 manifest 上每个 hit 的四个分字段。没算过的 stage 留空。
HIT_SCORE_FIELDS = ("bm25", "dense", "rrf", "rerank")


def blank_hit_scores() -> dict[str, float | None]:
    """四个可区分字段都在,缺席的 stage 为 None。"""
    return {name: None for name in HIT_SCORE_FIELDS}


@dataclass
class HitScoreBook:
    """一次检索里已经算出的分。调用方按 evidence_id 回读,排序仍用原列表。"""

    bm25: dict[str, float] = field(default_factory=dict)
    dense: dict[str, float] = field(default_factory=dict)
    rrf: dict[str, float] = field(default_factory=dict)
    rerank: dict[str, float] = field(default_factory=dict)

    def clear(self) -> None:
        self.bm25.clear()
        self.dense.clear()
        self.rrf.clear()
        self.rerank.clear()

    def row(self, evidence_id: str) -> dict[str, float | None]:
        out = blank_hit_scores()
        for name in HIT_SCORE_FIELDS:
            bucket: dict[str, float] = getattr(self, name)
            if evidence_id in bucket:
                out[name] = float(bucket[evidence_id])
        return out


def index_hit_scores(
    hits: list[Chunk], book: HitScoreBook,
) -> dict[str, dict[str, float | None]]:
    """只给本次返回的 hit 建表。book 里多出来的候选不进观察。"""
    return {chunk_evidence_id(chunk): book.row(chunk_evidence_id(chunk)) for chunk in hits}


# try_retrieve 在调用 store.retrieve 前放入。打分函数没收到 book 时写到这里。
# 这样不必改 InMemoryStore.retrieve(base.py 在 L4-RAG-02 的不动清单里)。
_active_book: ContextVar[HitScoreBook | None] = ContextVar(
    "freshlatch_hit_score_book", default=None,
)


def activate_hit_score_book(book: HitScoreBook) -> Token:
    return _active_book.set(book)


def reset_hit_score_book(token: Token) -> None:
    _active_book.reset(token)


def target_hit_score_book(book: HitScoreBook | None) -> HitScoreBook | None:
    """显式 book 优先;否则用当前 retrieve 激活的本。都没有则不记分。"""
    if book is not None:
        return book
    return _active_book.get()


def tokenize(text: str) -> list[str]:
    return [t for t in jieba.lcut(text) if t.strip()]


def meta_text(value: str | None) -> str | None:
    """空白视为未填写。补丁过滤器只认非空文本。"""
    if value is None:
        return None
    text = value.strip()
    return text or None


def filter_patch_metadata(
    chunks: list[Chunk],
    *,
    patch_id: str | None = None,
    valid_at: str | None = None,
) -> list[Chunk]:
    """补丁身份与有效期。必须在 BM25、dense 与 RRF 之前收窄候选池。

    查询未给 patch_id 与 valid_at 时返回原列表。
    块上 patch_id、valid_from、valid_to 皆空时该块保留。
    指定 patch_id 时,只剔除 patch_id 非空且不相等的块。
    指定 valid_at 时,valid_from / valid_to 按 YYYY-MM-DD 字符串闭区间比较。
    不读 doc_version,不读 as_of。
    """
    wanted = meta_text(patch_id)
    moment = meta_text(valid_at)
    if wanted is None and moment is None:
        return chunks
    kept: list[Chunk] = []
    for chunk in chunks:
        got_patch = meta_text(chunk.patch_id)
        start = meta_text(chunk.valid_from)
        end = meta_text(chunk.valid_to)
        if got_patch is None and start is None and end is None:
            kept.append(chunk)
            continue
        if wanted is not None and got_patch is not None and got_patch != wanted:
            continue
        if moment is not None and start is not None and moment < start:
            continue
        if moment is not None and end is not None and moment > end:
            continue
        kept.append(chunk)
    return kept


def recall_bm25(
    query: str,
    pool: list[Chunk],
    *,
    top_k: int = 10,
    book: HitScoreBook | None = None,
) -> list[Chunk]:
    """第 1 级:BM25Okapi 词法召回。空池安全返回空列表。"""
    if not pool:
        return []
    corpus = [tokenize(c.text) for c in pool]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(scores, pool), key=lambda x: x[0], reverse=True)
    kept = [(s, c) for s, c in ranked[:top_k] if s > 0]
    target = target_hit_score_book(book)
    if target is not None:
        for score, chunk in kept:
            target.bm25[chunk_evidence_id(chunk)] = float(score)
    return [c for _score, c in kept]


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


def rank_dense(
    query_vec: list[float],
    pool: list[Chunk],
    *,
    top_k: int,
    book: HitScoreBook | None = None,
) -> list[Chunk] | None:
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
    chosen = scored[:top_k]
    target = target_hit_score_book(book)
    if target is not None:
        for score, _i, chunk in chosen:
            target.dense[chunk_evidence_id(chunk)] = float(score)
    return [chunk for _score, _i, chunk in chosen]


# 预登记:RRF 常数取 Cormack 常用值,不按本轮指标回改。生产默认不走这条融合。
RRF_K = 60


def rrf_fuse(
    left: list[Chunk],
    right: list[Chunk],
    *,
    k: int = RRF_K,
    top_k: int = 10,
    book: HitScoreBook | None = None,
) -> list[Chunk]:
    """名次倒数融合。不把两路分数做 α 加权。rank 从 1 起。"""
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
    chosen = ranked_ids[:top_k]
    target = target_hit_score_book(book)
    if target is not None:
        for eid in chosen:
            target.rrf[eid] = float(scores[eid])
    return [seen[eid] for eid in chosen]


def stage_vector_fuse(chunks: list[Chunk], *, top_k: int) -> list[Chunk]:
    """第 2 级:生产默认仍透传。dense 臂走 rank_dense,hybrid 臂走 rrf_fuse。"""
    return chunks[:top_k]


def stage_rerank(chunks: list[Chunk], *, top_k: int) -> list[Chunk]:
    """第 3 级占位。生产 hybrid+rerank 不走这里，走 neural_rerank.rerank_hybrid_candidates。"""
    return chunks[:top_k]


def rerank_lexical(
    query: str,
    chunks: list[Chunk],
    *,
    top_k: int,
    book: HitScoreBook | None = None,
) -> list[Chunk]:
    """词重叠精排,只重排已有候选。生产默认不再走这里;它是显式开关和 lexical_fallback。"""
    query_tokens = set(tokenize(query))
    scored: list[tuple[int, int, Chunk]] = []
    for index, chunk in enumerate(chunks):
        overlap = len(query_tokens & set(tokenize(chunk.text))) if query_tokens else 0
        scored.append((overlap, -index, chunk))
    scored.sort(reverse=True)
    chosen = scored[:top_k]
    target = target_hit_score_book(book)
    if target is not None:
        for overlap, _index, chunk in chosen:
            target.rerank[chunk_evidence_id(chunk)] = float(overlap)
    return [chunk for _overlap, _index, chunk in chosen]


def run_pipeline(
    query: str,
    pool: list[Chunk],
    *,
    top_k: int = 10,
    book: HitScoreBook | None = None,
) -> list[Chunk]:
    hits = recall_bm25(query, pool, top_k=top_k, book=book)
    hits = stage_vector_fuse(hits, top_k=top_k)
    hits = stage_rerank(hits, top_k=top_k)
    return hits


def rerank_switch_value(retrieval_mode: str | None, rerank_mode: str | None) -> str:
    """小夹具 manifest 的 rerank 字段。

    on: 神经精排成功。off: 显式词面精排。fallback: 权重或推理失败退回词面。
    显式 BM25 与其它无精排臂记 off,不记成 on。
    """
    from freshlatch.models import RERANK_MODE_NEURAL
    from freshlatch.store.neural_rerank import RERANK_MODE_FALLBACK, RERANK_MODE_LEXICAL

    if retrieval_mode == "hybrid+rerank" and rerank_mode == RERANK_MODE_NEURAL:
        return "on"
    if retrieval_mode == "hybrid+rerank_lexical" and rerank_mode == RERANK_MODE_LEXICAL:
        return "off"
    if rerank_mode == RERANK_MODE_FALLBACK:
        return "fallback"
    return "off"


def build_retrieval_manifest(
    hits: list[Chunk],
    *,
    retrieval_mode: str | None,
    rerank_mode: str | None,
    hit_scores: dict[str, dict[str, float | None]] | None,
) -> dict:
    """一次检索的 manifest。production_retrieval_mode 只读常量,本函数不改它。"""
    from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

    table = hit_scores or {}
    rows = []
    for chunk in hits:
        eid = chunk_evidence_id(chunk)
        rows.append({
            "evidence_id": eid,
            "scores": dict(table.get(eid) or blank_hit_scores()),
        })
    return {
        "rerank": rerank_switch_value(retrieval_mode, rerank_mode),
        "retrieval_mode": retrieval_mode,
        "rerank_mode": rerank_mode,
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "hits": rows,
    }
