"""SQLite 实装(ADR-0003):as_of / source_type / doc_id 全是列,过滤 = WHERE 子句。

四表(§2.5)+ rerun_log(T9 追加):chunks(13 列)/ documents / invalidation_list / latch_log /
rerun_log(重跑时间线取数,复验单卡片「重跑后仍红(第 N 次)」从这取)。
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
CREATE TABLE IF NOT EXISTS rerun_log (
    ts TEXT NOT NULL,
    claim_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    nth INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_rerun_log_claim ON rerun_log (claim_id);

-- 长期记忆表（W9-W12新增）
CREATE TABLE IF NOT EXISTS long_term_memory (
    memory_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    written_at TEXT NOT NULL,
    last_confirmed_at TEXT,
    source_ref TEXT,
    checksum TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
);

-- 记忆标记表（W9-W12新增）
CREATE TABLE IF NOT EXISTS memory_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT NOT NULL,
    flag_type TEXT NOT NULL,  -- 'dead', 'contradiction', 'unverified'
    reason TEXT NOT NULL,
    flagged_at TEXT NOT NULL,
    evidence_ids TEXT,  -- JSON array of evidence IDs
    FOREIGN KEY(memory_id) REFERENCES long_term_memory(memory_id)
);

-- 隔离提议表（W9-W12新增）
CREATE TABLE IF NOT EXISTS quarantine_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_ids TEXT NOT NULL,  -- JSON array of memory IDs
    reason TEXT NOT NULL,
    proposed_at TEXT NOT NULL,
    confirmed_at TEXT,
    confirmed_by TEXT
);

-- 索引优化查询
CREATE INDEX IF NOT EXISTS idx_memory_status ON long_term_memory (status);
CREATE INDEX IF NOT EXISTS idx_memory_source ON long_term_memory (source_ref);
CREATE INDEX IF NOT EXISTS idx_memory_flags_memory ON memory_flags (memory_id);
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

    def log_rerun(self, ts: str, claim_id: str, thread_id: str, verdict: str, nth: int, note: str = "") -> None:
        """重跑时间线条目(§5.3):结果挂主张卡片时间线「重跑后仍红(第 N 次)」。"""
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO rerun_log VALUES (?,?,?,?,?,?)",
                (ts, claim_id, thread_id, verdict, nth, note),
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

    def list_reruns(self, claim_id: str) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM rerun_log WHERE claim_id = ? ORDER BY ts, rowid",
                (claim_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def list_latch_events(self, claim_id: str) -> list[dict]:
        """人审动作时间线(latch_log 单一真相:谁、何时、什么决定、凭什么证据)。"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT ts, action, evidence_id, actor FROM latch_log "
                "WHERE claim_id = ? ORDER BY ts, rowid",
                (claim_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def list_memories(self) -> list[dict]:
        """列出长期记忆条目（W9-W12新增）"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM long_term_memory WHERE status = 'active' ORDER BY written_at DESC"
            ).fetchall()

        memories = []
        for row in rows:
            memories.append({
                'memory_id': row['memory_id'],
                'content': row['content'],
                'written_at': row['written_at'],
                'last_confirmed_at': row['last_confirmed_at'],
                'source_ref': row['source_ref'],
                'checksum': row['checksum'],
                'status': row['status']
            })
        return memories

    def add_memory_item(self, memory_id: str, content: str, written_at: str,
                       source_ref: str = None, checksum: str = "",
                       last_confirmed_at: str = None) -> None:
        """添加记忆条目（W9-W12新增）"""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO long_term_memory
                (memory_id, content, written_at, last_confirmed_at, source_ref, checksum, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
                """,
                (memory_id, content, written_at, last_confirmed_at, source_ref, checksum)
            )

    def flag_memory_item(self, memory_id: str, flag_type: str, reason: str,
                        evidence_ids: list[str] = None, flagged_at: str = None) -> None:
        """标记记忆条目有问题（W9-W12新增）"""
        import json
        from datetime import datetime

        if not flagged_at:
            flagged_at = datetime.now().isoformat()

        evidence_str = json.dumps(evidence_ids) if evidence_ids else "[]"

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO memory_flags (memory_id, flag_type, reason, flagged_at, evidence_ids)
                VALUES (?, ?, ?, ?, ?)
                """,
                (memory_id, flag_type, reason, flagged_at, evidence_str)
            )

    def propose_quarantine(self, memory_ids: list[str], reason: str,
                          proposed_at: str = None) -> int:
        """提议隔离某些记忆条目（W9-W12新增）"""
        import json
        from datetime import datetime

        if not proposed_at:
            proposed_at = datetime.now().isoformat()

        memory_ids_str = json.dumps(memory_ids)

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO quarantine_proposals (memory_ids, reason, proposed_at)
                VALUES (?, ?, ?)
                """,
                (memory_ids_str, reason, proposed_at)
            )
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def confirm_quarantine(self, proposal_id: int, confirmed_by: str,
                          confirmed_at: str = None) -> bool:
        """确认隔离提议（W9-W12新增）"""
        import json
        from datetime import datetime

        if not confirmed_at:
            confirmed_at = datetime.now().isoformat()

        with self._conn() as conn:
            # 获取提议的ID列表
            proposal_row = conn.execute(
                "SELECT memory_ids FROM quarantine_proposals WHERE id = ?",
                (proposal_id,)
            ).fetchone()

            if not proposal_row:
                return False

            memory_ids = json.loads(proposal_row["memory_ids"])

            # 更新记忆条目的状态
            placeholders = ','.join(['?' for _ in memory_ids])
            conn.execute(
                f"UPDATE long_term_memory SET status = 'quarantined' WHERE memory_id IN ({placeholders})",
                memory_ids
            )

            # 更新提议状态
            conn.execute(
                """
                UPDATE quarantine_proposals
                SET confirmed_at = ?, confirmed_by = ?
                WHERE id = ?
                """,
                (confirmed_at, confirmed_by, proposal_id)
            )

            return True

    def list_quarantined_memory_ids(self) -> list[str]:
        """已隔离、不再进入召回集的 memory_id。"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT memory_id FROM long_term_memory WHERE status = 'quarantined' ORDER BY memory_id"
            ).fetchall()
        return [r["memory_id"] for r in rows]

    @staticmethod
    def _row_to_chunk(r: sqlite3.Row) -> Chunk:
        return Chunk(
            doc_id=r["doc_id"], chunk_id=r["chunk_id"], clause_id=r["clause_id"],
            title=r["title"], text=r["text"], source_type=r["source_type"],
            as_of=r["as_of"], doc_version=r["doc_version"], checksum=r["checksum"],
            tokens=r["tokens"], parent_id=r["parent_id"],
            hypo_questions=r["hypo_questions"], vec=r["vec"],
        )
