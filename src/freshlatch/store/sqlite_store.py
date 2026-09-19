"""SQLite 实装(ADR-0003):as_of / source_type / doc_id 全是列,过滤 = WHERE 子句。

四表(§2.5):chunks(13 列)/ documents / invalidation_list / latch_log。
作废名单单一真相在 invalidation_list 表,Lead 上下文与规则闸都查它。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from freshlatch.models import AsOf
from freshlatch.store.base import Chunk, Document, RetrievalStore
from freshlatch.store.pipeline import run_pipeline

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT NOT NULL,
    as_of TEXT NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    doc_version TEXT NOT NULL DEFAULT '1.0',
    checksum TEXT NOT NULL DEFAULT '',   -- 三处留位之二,本期为空
    full_text TEXT NOT NULL,
    PRIMARY KEY (doc_id, as_of)
);
CREATE TABLE IF NOT EXISTS chunks (
    doc_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    clause_id TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    source_type TEXT NOT NULL,
    as_of TEXT NOT NULL,
    doc_version TEXT NOT NULL DEFAULT '1.0',
    checksum TEXT NOT NULL DEFAULT '',
    tokens INTEGER NOT NULL DEFAULT 0,
    parent_id TEXT,        -- 留位
    hypo_questions TEXT,     -- 留位
    vec BLOB,                -- 留位
    PRIMARY KEY (chunk_id)
);
CREATE INDEX IF NOT EXISTS idx_chunks_filter ON chunks (as_of, source_type, doc_id);
CREATE TABLE IF NOT EXISTS invalidation_list (
    claim_id TEXT PRIMARY KEY,
    voided_at TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'human',
    reason TEXT
);
CREATE TABLE IF NOT EXISTS latch_log (
    ts TEXT NOT NULL,
    claim_id TEXT NOT NULL,
    action TEXT NOT NULL,
    evidence_id TEXT,
    actor TEXT NOT NULL DEFAULT 'human'
);
"""


class SQLiteStore(RetrievalStore):
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    # -- 写入 -----------------------------------------------------------------

    def add_document(self, doc: Document, chunks: list[Chunk]) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO documents "
                "(doc_id, as_of, source_type, title, doc_version, checksum, full_text) "
                "VALUES (?,?,?,?,?,?,?)",
                (doc.doc_id, doc.as_of, doc.source_type, doc.title,
                 doc.doc_version, doc.checksum, doc.full_text),
            )
            conn.executemany(
                "INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (c.doc_id, c.chunk_id, c.clause_id, c.title, c.text,
                     c.source_type, c.as_of, c.doc_version, c.checksum,
                     c.tokens, c.parent_id, c.hypo_questions, c.vec)
                    for c in chunks
                ],
            )

    def add_invalidation(self, claim_id: str, voided_at: str, actor: str = "human", reason: str | None = None) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO invalidation_list VALUES (?,?,?,?)",
                (claim_id, voided_at, actor, reason),
            )

    def log_latch(self, ts: str, claim_id: str, action: str, evidence_id: str | None = None, actor: str = "human") -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO latch_log VALUES (?,?,?,?,?)",
                (ts, claim_id, action, evidence_id, actor),
            )

    # -- 读取 -----------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        *,
        as_of: AsOf | None = None,
        source_type: str | None = None,
        top_k: int = 10,
    ) -> list[Chunk]:
        sql, params = "SELECT * FROM chunks", []
        if as_of is not None:
            sql += " WHERE as_of = ?"
            params.append(as_of)
        if source_type is not None:
            sql += " AND source_type = ?" if params else " WHERE source_type = ?"
            params.append(source_type)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        pool = [self._row_to_chunk(r) for r in rows]
        return run_pipeline(query, pool, top_k=top_k)

    def read_source(self, doc_id: str, *, as_of: AsOf) -> str | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT full_text FROM documents WHERE doc_id = ? AND as_of = ?",
                (doc_id, as_of),
            ).fetchone()
        return row["full_text"] if row else None

    def get_chunk(self, doc_id: str, clause_id: str, *, as_of: AsOf) -> Chunk | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM chunks WHERE doc_id = ? AND clause_id = ? AND as_of = ?",
                (doc_id, clause_id, as_of),
            ).fetchone()
        return self._row_to_chunk(row) if row else None

    def list_invalidation(self) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT claim_id FROM invalidation_list").fetchall()
        return [r["claim_id"] for r in rows]

    @staticmethod
    def _row_to_chunk(r: sqlite3.Row) -> Chunk:
        return Chunk(
            doc_id=r["doc_id"], chunk_id=r["chunk_id"], clause_id=r["clause_id"],
            title=r["title"], text=r["text"], source_type=r["source_type"],
            as_of=r["as_of"], doc_version=r["doc_version"], checksum=r["checksum"],
            tokens=r["tokens"], parent_id=r["parent_id"],
            hypo_questions=r["hypo_questions"], vec=r["vec"],
        )
