"""SQLite 实装(ADR-0003):as_of / source_type / doc_id 全是列,过滤 = WHERE 子句。

四表(§2.5)+ rerun_log(T9 追加):chunks(13 列)/ documents / invalidation_list / latch_log /
rerun_log(重跑时间线取数,复验单卡片「重跑后仍红(第 N 次)」从这取)。
作废名单单一真相在 invalidation_list 表,Lead 上下文与规则闸都查它。
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from freshlatch.models import AsOf
from freshlatch.store.base import (
    Chunk,
    Document,
    RetrievalStore,
    filter_retrieve_pool,
    normalize_tenant_id,
)
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
    tenant_id TEXT NOT NULL DEFAULT 'default',  -- I2 可选;缺省 default
    poison INTEGER NOT NULL DEFAULT 0,          -- I2 显式投毒标签,非启发式
    untrusted INTEGER NOT NULL DEFAULT 0,
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
    tenant_id TEXT NOT NULL DEFAULT 'default',  -- I2 可选;缺省 default
    poison INTEGER NOT NULL DEFAULT 0,          -- I2 显式投毒标签
    untrusted INTEGER NOT NULL DEFAULT 0,
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
    actor TEXT NOT NULL DEFAULT 'human',
    machine_status_before TEXT,   -- 人审成功写入必填;旧行与 rerun 可空
    override INTEGER,             -- 人审成功写入 0/1;旧行与 rerun 可空。不是模型变好
    run_id TEXT,                  -- 可选,跨跑次串联留位
    reviewer_note TEXT            -- 可选,与 discard reason 对齐
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

# 旧库缺列时补齐。新写入的人审成功行必须自己填满契约;旧行缺省保持 NULL,不回填对抗语义。
_LATCH_LOG_ADDED_COLUMNS = (
    ("machine_status_before", "TEXT"),
    ("override", "INTEGER"),
    ("run_id", "TEXT"),
    ("reviewer_note", "TEXT"),
)

# 旧库缺 I2 信任列时补齐。已有行走列默认:tenant_id=default,poison/untrusted=0。
_TRUST_ADDED_COLUMNS = (
    ("tenant_id", "TEXT NOT NULL DEFAULT 'default'"),
    ("poison", "INTEGER NOT NULL DEFAULT 0"),
    ("untrusted", "INTEGER NOT NULL DEFAULT 0"),
)


class SQLiteStore(RetrievalStore):
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(SCHEMA)
            self._ensure_latch_log_columns(conn)
            self._ensure_trust_columns(conn)

    @staticmethod
    def _ensure_latch_log_columns(conn: sqlite3.Connection) -> None:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(latch_log)")}
        for name, decl in _LATCH_LOG_ADDED_COLUMNS:
            if name not in existing:
                conn.execute(f"ALTER TABLE latch_log ADD COLUMN {name} {decl}")

    @staticmethod
    def _ensure_trust_columns(conn: sqlite3.Connection) -> None:
        for table in ("documents", "chunks"):
            existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            for name, decl in _TRUST_ADDED_COLUMNS:
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """打开连接；退出时提交/回滚并关闭（sqlite3 的 with 不会 close）。"""
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    # -- 写入 -----------------------------------------------------------------

    def _forget_vec_if_text_changed(self, chunks: list[Chunk]) -> None:
        """正文变了就丢掉传入的 vec。旧向量不能跟着新正文继续参与 rank_dense。"""
        if not chunks:
            return
        with self._conn() as conn:
            for chunk in chunks:
                row = conn.execute(
                    "SELECT text FROM chunks WHERE chunk_id = ?",
                    (chunk.chunk_id,),
                ).fetchone()
                if row is not None and row["text"] != chunk.text:
                    chunk.vec = None

    def _vec_to_store(self, conn: sqlite3.Connection, chunk: Chunk) -> bytes | None:
        """同正文的空 vec 保留库内向量。正文已变则必须是新 vec，否则写 NULL。"""
        if chunk.vec:
            return chunk.vec
        row = conn.execute(
            "SELECT text, vec FROM chunks WHERE chunk_id = ?",
            (chunk.chunk_id,),
        ).fetchone()
        if row is None or not row["vec"]:
            return None
        if row["text"] == chunk.text:
            return row["vec"]
        return None

    def add_document(self, doc: Document, chunks: list[Chunk]) -> None:
        self._forget_vec_if_text_changed(chunks)
        embedder = getattr(self, "chunk_embedder", None)
        if embedder is not None:
            from freshlatch.store.local_embed import fill_chunk_vecs

            try:
                fill_chunk_vecs(chunks, embedder)
            except Exception:
                # embedder 不可用：正文已变的块保持 vec 为空，不退回旧向量。
                pass
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO documents "
                "(doc_id, as_of, source_type, title, doc_version, checksum, full_text, "
                "tenant_id, poison, untrusted) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (doc.doc_id, doc.as_of, doc.source_type, doc.title,
                 doc.doc_version, doc.checksum, doc.full_text,
                 normalize_tenant_id(doc.tenant_id), int(bool(doc.poison)),
                 int(bool(doc.untrusted))),
            )
            conn.executemany(
                "INSERT OR REPLACE INTO chunks ("
                "doc_id, chunk_id, clause_id, title, text, source_type, as_of, "
                "doc_version, checksum, tokens, parent_id, hypo_questions, vec, "
                "tenant_id, poison, untrusted) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (c.doc_id, c.chunk_id, c.clause_id, c.title, c.text,
                     c.source_type, c.as_of, c.doc_version, c.checksum,
                     c.tokens, c.parent_id, c.hypo_questions,
                     self._vec_to_store(conn, c),
                     normalize_tenant_id(c.tenant_id), int(bool(c.poison)),
                     int(bool(c.untrusted)))
                    for c in chunks
                ],
            )

    def add_invalidation(self, claim_id: str, voided_at: str, actor: str = "human", reason: str | None = None) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO invalidation_list VALUES (?,?,?,?)",
                (claim_id, voided_at, actor, reason),
            )

    def log_latch(
        self,
        ts: str,
        claim_id: str,
        action: str,
        evidence_id: str | None = None,
        actor: str = "human",
        *,
        machine_status_before: str | None = None,
        override: bool | None = None,
        run_id: str | None = None,
        reviewer_note: str | None = None,
    ) -> None:
        """人审/重跑审计行。成功 discard/renew 须带 machine_status_before 与 override。

        override 只标记人是否对抗落档前机器 status,不表示模型变好,也不作通过线。
        """
        override_val = None if override is None else int(bool(override))
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO latch_log "
                "(ts, claim_id, action, evidence_id, actor, "
                "machine_status_before, override, run_id, reviewer_note) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    ts, claim_id, action, evidence_id, actor,
                    machine_status_before, override_val, run_id, reviewer_note,
                ),
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
        tenant_id: str | None = None,
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
        pool = filter_retrieve_pool(
            [self._row_to_chunk(r) for r in rows],
            tenant_id=tenant_id,
        )
        from freshlatch.store.pipeline import RRF_K, rank_dense, recall_bm25, rerank_lexical, rrf_fuse

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
        return self.list_latch_rows(claim_id=claim_id)

    def list_latch_rows(
        self,
        *,
        claim_id: str | None = None,
        override: bool | None = None,
    ) -> list[dict]:
        """审计读取。override=True 时只返回对抗标记行,供审计过滤。

        过滤结果不是模型变好,也不作 Override Rate 通过线。
        """
        sql = (
            "SELECT ts, claim_id, action, evidence_id, actor, "
            "machine_status_before, override, run_id, reviewer_note "
            "FROM latch_log"
        )
        clauses: list[str] = []
        params: list[object] = []
        if claim_id is not None:
            clauses.append("claim_id = ?")
            params.append(claim_id)
        if override is True:
            clauses.append("override = 1")
        elif override is False:
            clauses.append("override = 0")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY ts, rowid"
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._normalize_latch_row(r) for r in rows]

    @staticmethod
    def _normalize_latch_row(row: sqlite3.Row) -> dict:
        item = dict(row)
        if item.get("override") is not None:
            item["override"] = bool(item["override"])
        return item

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
            tenant_id=normalize_tenant_id(r["tenant_id"]),
            poison=bool(r["poison"]),
            untrusted=bool(r["untrusted"]),
        )
