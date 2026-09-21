"""
W9-W12 MemoryForensics 演示(demo 层,不是 must_quarantine 评测)。

合成记忆按立项切片 §11.3:2 条 dead、1 对 contradictory、2 条 unverified,
其余为可召回对照,且不与问题条共享「同对象同属性」,避免全隔离假绿。
source_ref 使用语料真实 doc_id(t0-competitor-notes 等)。
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from freshlatch.roles.forensic import ForensicAgent
from freshlatch.forensic_tools import create_forensic_tools
from freshlatch.store.ingest import ingest_into
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.tools import FORENSIC_TOOLS


def _now() -> str:
    return datetime.now().isoformat()


async def setup_test_environment():
    db_path = Path("test_memory_forensics.db")
    if db_path.exists():
        os.remove(db_path)

    store = SQLiteStore(db_path)
    chunk_count = ingest_into(store, project_root / "data" / "corpus")
    print(f"[OK] 已入库语料 chunk 数: {chunk_count}")

    # 2 dead:T0 结论,T1 已改
    store.add_memory_item(
        "mem_dead_price",
        "竞品 SeaDesk 标准版报价 99 美元/月/店,显著高于我方拟定的 59 美元/月/店",
        _now(),
        source_ref="t0-competitor-notes#p2",
        checksum="chk_dead_price",
    )
    store.add_memory_item(
        "mem_dead_reg",
        "截至目前印尼与泰国均未出台客服对话数据本地化强制要求,一般行业客服 SaaS 数据可存储在境外",
        _now(),
        source_ref="t0-regulatory-memo#p2",
        checksum="chk_dead_reg",
    )

    # 1 对 contradictory:同对象同属性,T1 并不偏袒其中一条的「相对关系」表述
    store.add_memory_item(
        "mem_cx_high",
        "竞品月费仍高于我们",
        _now(),
        source_ref="t0-competitor-notes#p2",
        checksum="chk_cx_high",
    )
    store.add_memory_item(
        "mem_cx_low",
        "竞品月费已降到我们的 70%",
        _now(),
        source_ref="t0-competitor-notes#p2",
        checksum="chk_cx_low",
    )

    # 2 unverified
    store.add_memory_item(
        "mem_uv_interview",
        "客户访谈显示 90% 愿意支付溢价",
        _now(),
        source_ref=None,
        checksum="chk_uv_interview",
    )
    store.add_memory_item(
        "mem_uv_missing_doc",
        "内部备忘称渠道返点将维持 30%",
        _now(),
        source_ref="doc-does-not-exist#p1",
        checksum="chk_uv_missing",
    )

    # 可召回对照:其他维度,避免与 dead/cx 同对象同属性
    store.add_memory_item(
        "mem_ok_market",
        "六国同口径可服务目标市场约 830 万家,结构无显著变化",
        _now(),
        source_ref="t0-market-census#p2",
        checksum="chk_ok_market",
    )
    store.add_memory_item(
        "mem_ok_cost",
        "我方单会话全成本约 0.009 美元,仍约为竞品的 47%",
        _now(),
        source_ref="t0-cost-model#p2",
        checksum="chk_ok_cost",
    )
    store.add_memory_item(
        "mem_ok_tech",
        "本地语言小模型幻觉率 15% 与 22%,意图识别最高 81%,生态仍不成熟",
        _now(),
        source_ref="t0-tech-ecosystem#p2",
        checksum="chk_ok_tech",
    )
    store.add_memory_item(
        "mem_ok_support",
        "复访中商户对 SeaDesk 支持响应慢的抱怨依旧,未见改善",
        _now(),
        source_ref="t0-competitor-notes#p3",
        checksum="chk_ok_support",
    )

    print(f"[OK] 测试数据库已创建: {db_path}")
    print(f"[OK] 已添加 {len(store.list_memories())} 个记忆条目")
    return store


async def run_forensic_analysis(store):
    print("\n[INFO] 启动 Forensic 记忆审核...")
    forensic_tools = create_forensic_tools(store)
    list_result = await forensic_tools["list_memories"]()
    print(f"[STAT] 发现 {list_result['count']} 个记忆条目")
    if list_result["count"] == 0:
        print("[WARN] 没有找到记忆条目")
        return None

    available_tools = {}
    for tool_name in FORENSIC_TOOLS:
        if tool_name in forensic_tools:
            available_tools[tool_name] = forensic_tools[tool_name]
    available_tools["get_chunk"] = forensic_tools["get_chunk"]

    forensic_agent = ForensicAgent()
    memory_items = []
    for mem in list_result["memories"]:
        memory_items.append({
            "memory_id": mem["memory_id"],
            "content": mem["content"],
            "written_at": mem["written_at"],
            "last_confirmed_at": mem["last_confirmed_at"],
            "source_ref": mem["source_ref"],
            "checksum": mem["checksum"],
            "status": mem["status"],
        })

    print(f"[RUN] 启动 Forensic Agent 处理 {len(memory_items)} 个记忆条目...")
    results = await forensic_agent.run(memory_items, available_tools)

    print("\n[DONE] Forensic 分析完成!")
    print(f"[FOUND] 发现 {len(results['dead'])} 个死亡记忆")
    print(f"[FOUND] 发现 {len(results['contradictory'])} 对互斥记忆")
    print(f"[FOUND] 发现 {len(results['unverified'])} 个未验证记忆")
    print(f"[FOUND] 提出 {len(results['quarantine_proposals'])} 个隔离建议")

    if results["dead"]:
        print("\n[DEAD] 死亡记忆:")
        for item in results["dead"]:
            print(f"   - {item['memory_id']}: {item.get('flag_reason', item['content'][:50])}")
            print(f"     evidence: {item.get('evidence_ids')}")

    if results["unverified"]:
        print("\n[UNVERIFIED] 未验证记忆:")
        for item in results["unverified"]:
            print(f"   - {item['memory_id']}: {item.get('flag_reason', item['content'][:50])}")

    if results["contradictory"]:
        print("\n[CONTRADICTIONS] 互斥记忆对:")
        for pair in results["contradictory"]:
            item_a = pair["item_a"]
            item_b = pair["item_b"]
            print(f"   - {item_a['memory_id']} vs {item_b['memory_id']}")
            print(f"     '{item_a['content'][:40]}...' vs '{item_b['content'][:40]}...'")

    if results["quarantine_proposals"]:
        print("\n[QUARANTINE] 隔离建议记忆ID:")
        for memory_id in results["quarantine_proposals"]:
            print(f"   - {memory_id}")

    return results


async def demonstrate_quarantine_process(store, results):
    print("\n[LOCK] 演示隔离确认流程...")
    if not results or not results["quarantine_proposals"]:
        print("[WARN] 无隔离建议,跳过确认")
        return

    forensic_tools = create_forensic_tools(store)
    quarantine_result = await forensic_tools["propose_quarantine"](
        results["quarantine_proposals"],
        "确认 Forensic 本轮提议的隔离名单",
    )
    print(f"[LIST] 提交隔离提议 #{quarantine_result['proposal_id']}")
    print(f"[LIST] 涉及记忆: {quarantine_result['memory_ids']}")

    print("\n[USER] 模拟人工确认隔离提议...")
    confirm_result = store.confirm_quarantine(quarantine_result["proposal_id"], "test_user")
    if confirm_result:
        print("[DONE] 隔离提议已确认")
        remaining_memories = store.list_memories()
        print(f"[STAT] 现有活跃记忆: {len(remaining_memories)} 个")
        quarantined_ids = store.list_quarantined_memory_ids()
        print(f"[STAT] 已隔离记忆: {len(quarantined_ids)} 个 -> {quarantined_ids}")
        remaining_ids = {m["memory_id"] for m in remaining_memories}
        expected_keep = {"mem_ok_market", "mem_ok_cost", "mem_ok_tech", "mem_ok_support"}
        if not expected_keep.issubset(remaining_ids):
            print(f"[WARN] 对照条目被误隔离: 期望保留 {expected_keep}, 实际 {remaining_ids}")
        else:
            print("[OK] 对照条目仍在召回集")
    else:
        print("[ERROR] 隔离确认失败")


async def main():
    print(">>> 开始 W9-W12 MemoryForensics 模块演示(demo 层)")
    print("=" * 60)
    store = await setup_test_environment()
    results = await run_forensic_analysis(store)
    await demonstrate_quarantine_process(store, results)
    print("\n" + "=" * 60)
    print("[NOTE] 本脚本是 demo 层:合成 10 条记忆,验证操作定义闩能否点回 T1。")
    print("[NOTE] 不是 must_quarantine 金标评测,不得写成准确率或论文结果。")


if __name__ == "__main__":
    asyncio.run(main())
