"""RetrievalStore 接口 + 内存假实现(单测与 gates 测试零 LLM、零磁盘)。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from freshlatch.models import AsOf

# 生产默认臂。评测可强制其它枚举值,但未实装的臂不得把 BM25 结果误标过去(后续票再放开)。
PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"
RETRIEVAL_MODE_ENUM = frozenset(
    {"bm25", "dense", "hybrid", "hybrid+rerank", "bm25_fallback"}
)
EXECUTABLE_RETRIEVAL_MODES = frozenset(
    {"bm25", "dense", "hybrid", "hybrid+rerank", "bm25_fallback"}
)


def chunk_evidence_id(chunk: "Chunk") -> str:
    """对外主键:doc_id#anchor@as_of。chunk_id 不进轨迹。"""
    return f"{chunk.doc_id}#{chunk.clause_id}@{chunk.as_of}"


@dataclass
class Chunk:
    """chunk schema 定稿 13 列(§2.5):parent_id / hypo_questions / vec 本期留位。

    I2 可选信任列(ADR-0030):tenant_id 缺省 default;poison/untrusted 为真则不可引用。
    """

    doc_id: str
    chunk_id: str
    clause_id: str
    title: str
    text: str
    source_type: str
    as_of: AsOf
    doc_version: str
    checksum: str
    tokens: int
    parent_id: str | None = None
    hypo_questions: str | None = None
    vec: bytes | None = None
    tenant_id: str = "default"
    poison: bool = False
    untrusted: bool = False


@dataclass
class Document:
    doc_id: str
    as_of: AsOf
    source_type: str
    title: str
    doc_version: str
    checksum: str
    full_text: str
    tenant_id: str = "default"
    poison: bool = False
    untrusted: bool = False


def normalize_tenant_id(value: str | None) -> str:
    """缺省与空白都视为 default,供显式 tenant 过滤比较。"""
    if value is None:
        return "default"
    text = str(value).strip()
    return text or "default"


def filter_retrieve_pool(chunks: list[Chunk], *, tenant_id: str | None) -> list[Chunk]:
    """召回信任边界:poison/untrusted 永远剔除;仅显式 tenant_id 时硬过滤异租户。

    tenant_id is None 表示调用方未传该参数,不启租户过滤(无参兼容)。
    不看正文是否出现 poison 字样。
    """
    kept: list[Chunk] = []
    for chunk in chunks:
        if chunk.poison or chunk.untrusted:
            continue
        if tenant_id is not None and normalize_tenant_id(chunk.tenant_id) != tenant_id:
            continue
        kept.append(chunk)
    return kept


class RetrievalStore(ABC):
    """检索层抽象。as_of / source_type 过滤 = WHERE 语义(实装侧)。"""

    def bind_eval_retrieval_mode(self, mode: str | None) -> None:
        """评测夹具绑定检索臂。生产 retrieve 签名不含该参数,Agent 工具不调用。"""
        self._eval_retrieval_mode = mode

    def _requested_retrieval_mode(self) -> str | None:
        return getattr(self, "_eval_retrieval_mode", None)

    def _embed_query(self, query: str) -> list[float] | None:
        """未注入 embedder 或调用失败 = 断 embed,调用方降级。不在这里打网。"""
        embedder = getattr(self, "query_embedder", None)
        if embedder is None:
            return None
        try:
            vec = embedder(query)
        except Exception:
            return None
        if not vec:
            return None
        return [float(x) for x in vec]

    @abstractmethod
    def retrieve(
        self,
        query: str,
        *,
        as_of: AsOf | None = None,
        source_type: str | None = None,
        top_k: int = 10,
        tenant_id: str | None = None,
    ) -> list[Chunk]: ...

    @abstractmethod
    def read_source(self, doc_id: str, *, as_of: AsOf) -> str | None:
        """读原文全文兜底(ground truth 是原文,不是 chunk)。"""

    @abstractmethod
    def get_chunk(self, doc_id: str, clause_id: str, *, as_of: AsOf) -> Chunk | None: ...

    @abstractmethod
    def add_document(self, doc: Document, chunks: list[Chunk]) -> None: ...

    def list_invalidation(self) -> list[str]:
        """作废名单(claim_id)。内存假实现默认空。"""
        return []

    def list_reruns(self, claim_id: str) -> list[dict]:
        """重跑时间线。内存假实现默认空(T9 起 SQLite 实装)。"""
        return []

    def list_latch_events(self, claim_id: str) -> list[dict]:
        """人审动作时间线(作废/续命/重跑)。内存假实现默认空(#23 起 SQLite 实装)。"""
        return []

    def list_memories(self) -> list[dict]:
        """列出长期记忆条目。内存假实现默认空。"""
        return []


class InMemoryStore(RetrievalStore):
    """内存假实现:测试用,零磁盘零 LLM。"""

    def __init__(self) -> None:
        self._docs: dict[tuple[str, AsOf], Document] = {}
        self._chunks: list[Chunk] = []
        self._memories: list[dict] = []

    def add_document(self, doc: Document, chunks: list[Chunk]) -> None:
        self._docs[(doc.doc_id, doc.as_of)] = doc
        self._chunks.extend(chunks)

    def retrieve(
        self,
        query: str,
        *,
        as_of: AsOf | None = None,
        source_type: str | None = None,
        top_k: int = 10,
        tenant_id: str | None = None,
    ) -> list[Chunk]:
        from freshlatch.store.pipeline import recall_bm25

        pool = [
            c
            for c in self._chunks
            if (as_of is None or c.as_of == as_of)
            and (source_type is None or c.source_type == source_type)
        ]
        pool = filter_retrieve_pool(pool, tenant_id=tenant_id)
        from freshlatch.store.pipeline import RRF_K, rank_dense, rerank_lexical, rrf_fuse

        requested = self._requested_retrieval_mode()
        if requested == "dense":
            query_vec = self._embed_query(query)
            ranked = rank_dense(query_vec, pool, top_k=top_k) if query_vec else None
            if ranked is None:
                self.last_retrieval_mode = "bm25_fallback"
                return recall_bm25(query, pool, top_k=top_k)
            self.last_retrieval_mode = "dense"
            return ranked
        if requested == "hybrid":
            depth = max(top_k, len(pool))
            lexical = recall_bm25(query, pool, top_k=depth)
            query_vec = self._embed_query(query)
            dense = rank_dense(query_vec, pool, top_k=depth) if query_vec else None
            if dense is None:
                self.last_retrieval_mode = "bm25_fallback"
                return recall_bm25(query, pool, top_k=top_k)
            self.last_retrieval_mode = "hybrid"
            return rrf_fuse(lexical, dense, k=RRF_K, top_k=top_k)
        if requested == "hybrid+rerank":
            depth = max(top_k, len(pool))
            lexical = recall_bm25(query, pool, top_k=depth)
            query_vec = self._embed_query(query)
            dense = rank_dense(query_vec, pool, top_k=depth) if query_vec else None
            if dense is None:
                self.last_retrieval_mode = "bm25_fallback"
                return recall_bm25(query, pool, top_k=top_k)
            fused = rrf_fuse(lexical, dense, k=RRF_K, top_k=top_k)
            self.last_retrieval_mode = "hybrid+rerank"
            return rerank_lexical(query, fused, top_k=top_k)
        if requested == "bm25_fallback":
            self.last_retrieval_mode = "bm25_fallback"
            return recall_bm25(query, pool, top_k=top_k)
        self.last_retrieval_mode = "bm25"
        return recall_bm25(query, pool, top_k=top_k)

    def read_source(self, doc_id: str, *, as_of: AsOf) -> str | None:
        doc = self._docs.get((doc_id, as_of))
        return doc.full_text if doc else None

    def get_chunk(self, doc_id: str, clause_id: str, *, as_of: AsOf) -> Chunk | None:
        for c in self._chunks:
            if c.doc_id == doc_id and c.clause_id == clause_id and c.as_of == as_of:
                return c
        return None

    def list_memories(self) -> list[dict]:
        """返回内存中的记忆条目列表"""
        return self._memories.copy()
