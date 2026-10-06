"""长期记忆存储模块 - 用于存储和管理项目的长期记忆条目"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator, List, Optional


class MemoryStatus(Enum):
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    CONFIRMED_DEAD = "confirmed_dead"


@dataclass
class MemoryItem:
    """记忆条目数据结构"""
    memory_id: str
    content: str
    written_at: str
    last_confirmed_at: Optional[str]
    source_ref: Optional[str]  # 指向原始来源的引用
    checksum: str
    status: MemoryStatus = MemoryStatus.ACTIVE


class LongTermMemoryStore:
    """长期记忆存储 - 专门用于存储和管理项目的记忆条目"""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        with self._conn() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                memory_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                written_at TEXT NOT NULL,
                last_confirmed_at TEXT,
                source_ref TEXT,
                checksum TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY(status) REFERENCES memory_status_enum(status)
            );

            CREATE TABLE IF NOT EXISTS memory_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                flag_type TEXT NOT NULL,  -- 'dead', 'contradiction', 'unverified'
                reason TEXT NOT NULL,
                flagged_at TEXT NOT NULL,
                evidence_ids TEXT,  -- JSON array of evidence IDs
                FOREIGN KEY(memory_id) REFERENCES long_term_memory(memory_id)
            );

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
            """)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """打开连接；退出时提交/回滚并关闭（sqlite3 的 with 不会 close）。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def add_memory_item(self, item: MemoryItem) -> None:
        """添加记忆条目"""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO long_term_memory
                (memory_id, content, written_at, last_confirmed_at, source_ref, checksum, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.memory_id,
                    item.content,
                    item.written_at,
                    item.last_confirmed_at,
                    item.source_ref,
                    item.checksum,
                    item.status.value
                ),
            )

    def get_memory_item(self, memory_id: str) -> Optional[MemoryItem]:
        """获取指定的记忆条目"""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM long_term_memory WHERE memory_id = ?",
                (memory_id,)
            ).fetchone()

        if not row:
            return None

        return MemoryItem(
            memory_id=row["memory_id"],
            content=row["content"],
            written_at=row["written_at"],
            last_confirmed_at=row["last_confirmed_at"],
            source_ref=row["source_ref"],
            checksum=row["checksum"],
            status=MemoryStatus(row["status"])
        )

    def list_memory_items(self, status: MemoryStatus = None) -> List[MemoryItem]:
        """列出记忆条目，可按状态筛选"""
        where_clause = ""
        params = []
        if status:
            where_clause = "WHERE status = ?"
            params = [status.value]

        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM long_term_memory {where_clause} ORDER BY written_at DESC",
                params
            ).fetchall()

        return [
            MemoryItem(
                memory_id=row["memory_id"],
                content=row["content"],
                written_at=row["written_at"],
                last_confirmed_at=row["last_confirmed_at"],
                source_ref=row["source_ref"],
                checksum=row["checksum"],
                status=MemoryStatus(row["status"])
            )
            for row in rows
        ]

    def get_active_memory_items(self) -> List[MemoryItem]:
        """获取活跃的记忆条目（排除被隔离的）"""
        return self.list_memory_items(status=MemoryStatus.ACTIVE)

    def update_memory_status(self, memory_id: str, status: MemoryStatus) -> bool:
        """更新记忆条目的状态"""
        with self._conn() as conn:
            result = conn.execute(
                "UPDATE long_term_memory SET status = ? WHERE memory_id = ?",
                (status.value, memory_id)
            )
            return result.rowcount > 0

    def flag_memory_item(self, memory_id: str, flag_type: str, reason: str,
                        evidence_ids: List[str] = None, flagged_at: str = None) -> None:
        """标记记忆条目有问题"""
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

    def propose_quarantine(self, memory_ids: List[str], reason: str,
                          proposed_at: str = None) -> int:
        """提议隔离某些记忆条目"""
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
        """确认隔离提议"""
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
            for memory_id in memory_ids:
                self.update_memory_status(memory_id, MemoryStatus.QUARANTINED)

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

    def get_memory_flags(self, memory_id: str = None) -> List[dict]:
        """获取记忆条目的标记信息"""
        import json

        where_clause = ""
        params = []
        if memory_id:
            where_clause = "WHERE memory_id = ?"
            params = [memory_id]

        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM memory_flags {where_clause} ORDER BY flagged_at DESC",
                params
            ).fetchall()

        result = []
        for row in rows:
            result.append({
                'id': row['id'],
                'memory_id': row['memory_id'],
                'flag_type': row['flag_type'],
                'reason': row['reason'],
                'flagged_at': row['flagged_at'],
                'evidence_ids': json.loads(row['evidence_ids']) if row['evidence_ids'] else []
            })

        return result

    def get_quarantine_proposals(self, confirmed: bool = None) -> List[dict]:
        """获取隔离提议列表"""
        import json

        where_clause = ""
        params = []

        if confirmed is True:
            where_clause = "WHERE confirmed_at IS NOT NULL"
        elif confirmed is False:
            where_clause = "WHERE confirmed_at IS NULL"

        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM quarantine_proposals {where_clause} ORDER BY proposed_at DESC",
                params
            ).fetchall()

        result = []
        for row in rows:
            result.append({
                'id': row['id'],
                'memory_ids': json.loads(row['memory_ids']),
                'reason': row['reason'],
                'proposed_at': row['proposed_at'],
                'confirmed_at': row['confirmed_at'],
                'confirmed_by': row['confirmed_by']
            })

        return result