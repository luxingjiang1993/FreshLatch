"""Forensic工具处理器 - 处理与Forensic相关的工具调用"""

from typing import Dict, Any, Callable, Awaitable
from freshlatch.store.sqlite_store import SQLiteStore
import json
from datetime import datetime


def create_forensic_tools(store: SQLiteStore) -> Dict[str, Callable[..., Awaitable[Dict[str, Any]]]]:
    """创建Forensic相关的工具集合

    Args:
        store: SQLite存储实例

    Returns:
        包含Forensic相关工具的字典
    """

    async def list_memories(as_of: str = None) -> Dict[str, Any]:
        """获取本课题长期记忆条目召回集。as_of 保留签名以对齐工具 schema,本期召回不按 as_of 切记忆。"""
        try:
            memories = store.list_memories()
            return {
                "status": "success",
                "memories": memories,
                "count": len(memories)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取记忆条目失败: {str(e)}"
            }

    async def retrieve(
        query: str,
        as_of: str = "T1",
        source_type: str = None,
        top_k: int = 10,
        tenant_id: str | None = None,
    ) -> Dict[str, Any]:
        """按 as_of 检索语料,供 Forensic 对照 T1。过滤与 store.retrieve 同一实现。"""
        try:
            kwargs = {
                "as_of": as_of if as_of in ("T0", "T1") else "T1",
                "source_type": source_type or None,
                "top_k": top_k,
            }
            if tenant_id:
                kwargs["tenant_id"] = tenant_id
            hits = store.retrieve(query, **kwargs)
            blocks = [
                {
                    "evidence_id": f"{c.doc_id}#{c.clause_id}@{c.as_of}",
                    "as_of": c.as_of,
                    "source_type": c.source_type,
                    "text": c.text,
                }
                for c in hits
            ]
            return {"status": "success", "blocks": blocks, "count": len(blocks)}
        except Exception as e:
            return {"status": "error", "message": f"检索失败: {str(e)}"}

    async def read_source(doc_id: str, as_of: str = "T1") -> Dict[str, Any]:
        """读指定快照的原文全文。"""
        try:
            if as_of not in ("T0", "T1"):
                as_of = "T1"
            text = store.read_source(doc_id, as_of=as_of)
            if text is None:
                return {"status": "error", "error": f"未找到文档 {doc_id} 的 {as_of} 快照"}
            return {"status": "success", "doc_id": doc_id, "as_of": as_of, "full_text": text}
        except Exception as e:
            return {"status": "error", "error": f"读取原文失败: {str(e)}"}

    async def get_chunk(doc_id: str, clause_id: str, as_of: str = "T1") -> Dict[str, Any]:
        """读指定条款块(内部对照用,不进模型白名单)。"""
        try:
            if as_of not in ("T0", "T1"):
                as_of = "T1"
            chunk = store.get_chunk(doc_id, clause_id, as_of=as_of)
            if chunk is None:
                return {"status": "error", "error": f"未找到 {doc_id}#{clause_id}@{as_of}"}
            return {
                "status": "success",
                "text": chunk.text,
                "chunk": {
                    "doc_id": chunk.doc_id,
                    "clause_id": chunk.clause_id,
                    "as_of": chunk.as_of,
                    "text": chunk.text,
                },
            }
        except Exception as e:
            return {"status": "error", "error": f"读取条款失败: {str(e)}"}

    async def flag_contradiction(memory_id_a: str, memory_id_b: str, reason: str) -> Dict[str, Any]:
        """标记两条记忆条目互斥"""
        try:
            # 标记这两条记忆为互斥
            store.flag_memory_item(memory_id_a, "contradiction",
                                 f"与 {memory_id_b} 互斥: {reason}")
            store.flag_memory_item(memory_id_b, "contradiction",
                                 f"与 {memory_id_a} 互斥: {reason}")

            return {
                "status": "success",
                "message": f"已标记记忆 {memory_id_a} 与 {memory_id_b} 互斥",
                "reason": reason
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"标记互斥失败: {str(e)}"
            }

    async def flag_dead(memory_id: str, reason: str, evidence_ids: list = None) -> Dict[str, Any]:
        """标记记忆条目已死"""
        try:
            if evidence_ids is None:
                evidence_ids = []

            store.flag_memory_item(memory_id, "dead", reason, evidence_ids)

            return {
                "status": "success",
                "message": f"已标记记忆 {memory_id} 为已死",
                "reason": reason,
                "evidence_ids": evidence_ids
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"标记死亡失败: {str(e)}"
            }

    async def flag_unverified(memory_id: str, reason: str) -> Dict[str, Any]:
        """标记记忆条目未经证实"""
        try:
            store.flag_memory_item(memory_id, "unverified", reason)

            return {
                "status": "success",
                "message": f"已标记记忆 {memory_id} 为未经证实",
                "reason": reason
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"标记未证实失败: {str(e)}"
            }

    async def propose_quarantine(memory_ids: list, reason: str = None) -> Dict[str, Any]:
        """提议将记忆条目移出召回集"""
        try:
            if reason is None:
                reason = "Automated quarantine proposal"

            proposal_id = store.propose_quarantine(memory_ids, reason)

            return {
                "status": "success",
                "message": f"已提交隔离提议 #{proposal_id}",
                "proposal_id": proposal_id,
                "memory_ids": memory_ids,
                "reason": reason
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"提议隔离失败: {str(e)}"
            }

    return {
        "list_memories": list_memories,
        "retrieve": retrieve,
        "read_source": read_source,
        "get_chunk": get_chunk,
        "flag_contradiction": flag_contradiction,
        "flag_dead": flag_dead,
        "flag_unverified": flag_unverified,
        "propose_quarantine": propose_quarantine
    }