"""RetrievalStore 接口 + 内存假实现(单测与 gates 测试零 LLM、零磁盘)。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from freshlatch.models import AsOf


@dataclass
class Chunk:
    """chunk schema 定稿 13 列(§2.5):parent_id / hypo_questions / vec 本期留位。"""

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


@dataclass
class Document:
    doc_id: str
    as_of: AsOf
    source_type: str
    title: str
    doc_version: str
    checksum: str
    full_text: str


class RetrievalStore(ABC):
    """检索层抽象。as_of / source_type 过滤 = WHERE 语义(实装侧)。"""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        *,
        as_of: AsOf | None = None,
        source_type: str | None = None,
        top_k: int = 10,
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


class InMemoryStore(RetrievalStore):
    """内存假实现:测试用,零磁盘零 LLM。"""

    def __init__(self) -> None:
        self._docs: dict[tuple[str, AsOf], Document] = {}
        self._chunks: list[Chunk] = []

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
    ) -> list[Chunk]:
        from freshlatch.store.pipeline import recall_bm25

        pool = [
            c
            for c in self._chunks
            if (as_of is None or c.as_of == as_of)
            and (source_type is None or c.source_type == source_type)
        ]
        return recall_bm25(query, pool, top_k=top_k)

    def read_source(self, doc_id: str, *, as_of: AsOf) -> str | None:
        doc = self._docs.get((doc_id, as_of))
        return doc.full_text if doc else None

    def get_chunk(self, doc_id: str, clause_id: str, *, as_of: AsOf) -> Chunk | None:
        for c in self._chunks:
            if c.doc_id == doc_id and c.clause_id == clause_id and c.as_of == as_of:
                return c
        return None
