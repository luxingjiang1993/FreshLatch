"""Forensic:记忆刑侦(W9–W12;W1–W4 不挂载,仅 skill 文件在盘)。

检测顺序与 skills/memory_forensics/SKILL.md 工作流对齐:
1. 无 source_ref 或出处不可回溯 → unverified
2. 有出处则对照 T1 原文 → dead(无 T1 则不下死事实)
3. 其余条目做同对象同维度互斥 → contradictory

时效词表不得单独构成 dead。checksum 对不上的半边本期留位未启用,本模块不假装已启用。
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# 价格/费用维度词:互斥与死事实的同维度门闩,不是「任意数字不同即互斥」。
ATTRIBUTE_KEYWORDS = [
    "价格", "费用", "成本", "月费", "年费", "收费", "定价", "售价", "金额",
    "报价", "value", "price", "cost", "fee",
]
REGULATORY_KEYWORDS = ["监管", "本地化", "境内存储", "pdp", "强制"]
OPPOSITE_PAIRS = [
    ("高于", "低于"),
    ("高于", "降到"),
    ("高于", "降至"),
    ("增加", "减少"),
    ("支持", "反对"),
    ("有利", "不利"),
]
# 记忆侧否定口径 vs T1 强制口径:监管死事实用,不单独扫时效词。
MEMORY_NEGATION_CUES = ("暂无", "尚未", "未出台", "没有强制", "无需境内", "不要求")
T1_MANDATE_CUES = ("须在", "必须在", "强制", "生效", "明确规定", "境内存储")
# T1 把旧数字写成「从 X 降至 Y」时,X 仍出现在原文,不能再用子集判断。
_SUPERSEDE_PATTERNS = [
    re.compile(
        r"从\s*(\d+)\s*(?:美元|元)?(?:/\w+)*(?:.{0,24})(?:降至|降到|降为|下调至)\s*(\d+)"
    ),
    re.compile(r"(\d+)\s*(?:美元|元)\s*(?:降至|降到|降为)\s*(\d+)"),
]

# 具体对象:有具体对象且不相交时,不把两条记忆判互斥(竞品A的价 ≠ 竞品B的价)。
_ENTITY_PATTERNS = [
    re.compile(r"SeaDesk", re.IGNORECASE),
    re.compile(r"竞品[A-Za-z0-9]+"),
    re.compile(r"印尼|泰国|越南|菲律宾"),
    re.compile(r"PDP", re.IGNORECASE),
]


def parse_source_ref(source_ref: Optional[str]) -> Optional[tuple[str, Optional[str]]]:
    """把 source_ref 拆成 (doc_id, clause_id)。

    接受 doc_id、doc_id#p2、doc_id#p2@T0|T1。空串或 None 返回 None。
    """
    if not source_ref or not str(source_ref).strip():
        return None
    raw = str(source_ref).strip()
    if "@" in raw:
        raw, _at = raw.rsplit("@", 1)
    if "#" in raw:
        doc_id, clause_id = raw.split("#", 1)
        doc_id, clause_id = doc_id.strip(), clause_id.strip()
        if not doc_id:
            return None
        return doc_id, clause_id or None
    return raw, None


def extract_specific_entities(text: str) -> set[str]:
    """抽出可区分对象。裸「竞品」不算具体对象。"""
    found: set[str] = set()
    for pattern in _ENTITY_PATTERNS:
        for match in pattern.findall(text):
            found.add(match.lower() if isinstance(match, str) else str(match).lower())
    return found


def extract_fact_numbers(text: str) -> set[str]:
    """抽出事实数字;四位 20xx 年份不参与冲突比较。"""
    numbers = re.findall(r"\d+", text)
    return {n for n in numbers if not (len(n) == 4 and n.startswith("20"))}


def _contains_any(text: str, needles: tuple[str, ...] | list[str]) -> bool:
    return any(n.lower() in text for n in needles)


def _superseded_numbers(t1_text: str) -> dict[str, str]:
    """从 T1 抽出「从旧值覆盖为新值」的数字对。"""
    mapping: dict[str, str] = {}
    for pattern in _SUPERSEDE_PATTERNS:
        for old, new in pattern.findall(t1_text):
            if old != new:
                mapping[old] = new
    return mapping


def collect_t1_index(store, memory_items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """从 store 按 source_ref 取 T1 条款或全文,供 inspect 同步调用。"""
    cache: Dict[str, Dict[str, Any]] = {}
    for item in memory_items:
        parsed = parse_source_ref(item.get("source_ref"))
        if not parsed:
            continue
        doc_id, clause_id = parsed
        text = None
        if clause_id:
            chunk = store.get_chunk(doc_id, clause_id, as_of="T1")
            if chunk is not None:
                text = chunk.text
        if not text:
            text = store.read_source(doc_id, as_of="T1")
        cache[item["memory_id"]] = {
            "doc_id": doc_id,
            "clause_id": clause_id,
            "text": text,
            "evidence_id": f"{doc_id}#{clause_id or 'p2'}@T1",
        }
    return cache


def store_source_exists(store, doc_id: str) -> bool:
    """文档在 T0 或 T1 快照中是否存在。"""
    return (
        store.read_source(doc_id, as_of="T0") is not None
        or store.read_source(doc_id, as_of="T1") is not None
    )


class ForensicAgent:
    """Forensic:只审本课题长期记忆。形态可以是确定性闩,也可以被 Lead 派驻。

    本期 inspect() 是确定性操作定义执行体,不是 LLM ReAct 循环。
    真 Agent 循环(retrieve/read_source/flag_* ≤8 步)登记为中期实装,不在本函数里伪装。
    """

    def __init__(self, claim_id: str = None, focus: str = None):
        self.claim_id = claim_id
        self.focus = focus
        self.max_steps = 8

    def inspect(
        self,
        memory_items: List[Dict[str, Any]],
        *,
        t1_by_memory_id: Optional[Dict[str, Dict[str, Any]]] = None,
        source_exists: Optional[Callable[[str], bool]] = None,
    ) -> Dict[str, Any]:
        """按操作定义审核记忆,不写库、不调工具。

        t1_by_memory_id: memory_id → {doc_id, clause_id, text, evidence_id}
        source_exists: doc_id → 该文档在 T0 或 T1 是否存在
        """
        t1_by_memory_id = t1_by_memory_id or {}
        unverified = self._find_unverified_items(memory_items, source_exists=source_exists)
        unverified_ids = {item["memory_id"] for item in unverified}

        remaining_after_unverified = [
            item for item in memory_items if item.get("memory_id") not in unverified_ids
        ]
        dead = self._find_potentially_dead_items(
            remaining_after_unverified, t1_by_memory_id=t1_by_memory_id
        )
        dead_ids = {item["memory_id"] for item in dead}

        remaining_for_contradiction = [
            item for item in remaining_after_unverified
            if item.get("memory_id") not in dead_ids
        ]
        contradictory = self._find_contradictory_items(remaining_for_contradiction)

        quarantine_ids: List[str] = []
        for item in dead:
            quarantine_ids.append(item["memory_id"])
        for pair in contradictory:
            quarantine_ids.append(pair["item_a"]["memory_id"])
            quarantine_ids.append(pair["item_b"]["memory_id"])
        for item in unverified:
            quarantine_ids.append(item["memory_id"])
        # 保序去重
        seen: set[str] = set()
        unique_ids: List[str] = []
        for mid in quarantine_ids:
            if mid not in seen:
                seen.add(mid)
                unique_ids.append(mid)

        return {
            "dead": dead,
            "contradictory": contradictory,
            "unverified": unverified,
            "quarantine_ids": unique_ids,
        }

    async def run(self, memory_items: List[Dict[str, Any]], tools: Dict[str, callable]):
        """执行 Forensic 审核:先 inspect,再经工具落标与提议隔离。"""
        logger.info("Starting Forensic audit on %s memory items", len(memory_items))

        read_source = tools.get("read_source")
        get_chunk = tools.get("get_chunk")
        flag_dead = tools.get("flag_dead")
        flag_contradiction = tools.get("flag_contradiction")
        flag_unverified = tools.get("flag_unverified")
        propose_quarantine = tools.get("propose_quarantine")

        t1_by_memory_id = await self._load_t1_texts(
            memory_items, read_source=read_source, get_chunk=get_chunk
        )
        source_exists = await self._build_source_exists(memory_items, read_source=read_source)

        findings = self.inspect(
            memory_items,
            t1_by_memory_id=t1_by_memory_id,
            source_exists=source_exists,
        )

        results = {
            "dead": [],
            "contradictory": [],
            "unverified": [],
            "quarantine_proposals": [],
        }

        for item in findings["unverified"]:
            if flag_unverified:
                try:
                    await flag_unverified(
                        item["memory_id"],
                        item.get("flag_reason")
                        or f"Memory item has no source_ref: {item.get('content', '')[:100]}...",
                    )
                    results["unverified"].append(item)
                    logger.info("Flagged unverified memory item: %s", item["memory_id"])
                except Exception as e:
                    logger.error("Failed to flag unverified item %s: %s", item["memory_id"], e)

        for pair in findings["contradictory"]:
            if flag_contradiction:
                try:
                    await flag_contradiction(
                        pair["item_a"]["memory_id"],
                        pair["item_b"]["memory_id"],
                        f"Items contradict each other: '{pair['item_a']['content'][:50]}...' vs '{pair['item_b']['content'][:50]}...'",
                    )
                    results["contradictory"].append(pair)
                    logger.info(
                        "Flagged contradictory memory items: %s vs %s",
                        pair["item_a"]["memory_id"],
                        pair["item_b"]["memory_id"],
                    )
                except Exception as e:
                    logger.error(
                        "Failed to flag contradiction between %s and %s: %s",
                        pair["item_a"]["memory_id"],
                        pair["item_b"]["memory_id"],
                        e,
                    )

        for item in findings["dead"]:
            if flag_dead:
                try:
                    evidence_ids = item.get("evidence_ids") or []
                    await flag_dead(
                        item["memory_id"],
                        item.get("flag_reason")
                        or f"Memory conflicts with T1 source: {item.get('content', '')[:100]}...",
                        evidence_ids,
                    )
                    results["dead"].append(item)
                    logger.info("Flagged dead memory item: %s", item["memory_id"])
                except Exception as e:
                    logger.error("Failed to flag dead item %s: %s", item["memory_id"], e)

        if findings["quarantine_ids"] and propose_quarantine:
            try:
                await propose_quarantine(
                    findings["quarantine_ids"],
                    "Forensic:dead/contradictory/unverified 条目提议移出召回集",
                )
                results["quarantine_proposals"].extend(findings["quarantine_ids"])
                logger.info(
                    "Proposed quarantine for %s memory items",
                    len(findings["quarantine_ids"]),
                )
            except Exception as e:
                logger.error(
                    "Failed to propose quarantine for %s: %s",
                    findings["quarantine_ids"],
                    e,
                )

        logger.info(
            "Forensic audit completed. Found %s dead, %s contradictory, %s unverified items.",
            len(results["dead"]),
            len(results["contradictory"]),
            len(results["unverified"]),
        )
        return results

    async def _call_tool(self, fn, *args, **kwargs):
        result = fn(*args, **kwargs)
        if hasattr(result, "__await__"):
            result = await result
        return result

    async def _load_t1_texts(
        self,
        memory_items: List[Dict[str, Any]],
        *,
        read_source,
        get_chunk,
    ) -> Dict[str, Dict[str, Any]]:
        """按 source_ref 取 T1 原文。优先条款块,否则全文。读不到则该条不进入 dead。"""
        cache: Dict[str, Dict[str, Any]] = {}
        if not read_source and not get_chunk:
            return cache
        for item in memory_items:
            parsed = parse_source_ref(item.get("source_ref"))
            if not parsed:
                continue
            doc_id, clause_id = parsed
            text = None
            if get_chunk and clause_id:
                try:
                    chunk_result = await self._call_tool(
                        get_chunk, doc_id, clause_id, as_of="T1"
                    )
                    text = self._extract_text(chunk_result)
                except Exception as e:
                    logger.error("get_chunk failed for %s#%s: %s", doc_id, clause_id, e)
            if text is None and read_source:
                try:
                    src_result = await self._call_tool(
                        read_source, doc_id, as_of="T1"
                    )
                    text = self._extract_text(src_result)
                except Exception as e:
                    logger.error("read_source failed for %s: %s", doc_id, e)
            evidence_id = f"{doc_id}#{clause_id or 'p2'}@T1"
            cache[item["memory_id"]] = {
                "doc_id": doc_id,
                "clause_id": clause_id,
                "text": text,
                "evidence_id": evidence_id,
            }
        return cache

    async def _build_source_exists(
        self,
        memory_items: List[Dict[str, Any]],
        *,
        read_source,
    ) -> Optional[Callable[[str], bool]]:
        if not read_source:
            return None
        known: Dict[str, bool] = {}

        async def _probe(doc_id: str) -> bool:
            if doc_id in known:
                return known[doc_id]
            exists = False
            for as_of in ("T0", "T1"):
                try:
                    result = await self._call_tool(read_source, doc_id, as_of=as_of)
                    text = self._extract_text(result)
                    if text:
                        exists = True
                        break
                except Exception as exc:
                    logger.warning(
                        "read_source 探测失败 as_of=%s exc_type=%s",
                        as_of,
                        type(exc).__name__,
                    )
                    continue
            known[doc_id] = exists
            return exists

        # 预探测本批 source_ref,返回同步闭包给 inspect。
        for item in memory_items:
            parsed = parse_source_ref(item.get("source_ref"))
            if parsed:
                await _probe(parsed[0])

        return lambda doc_id: known.get(doc_id, False)

    @staticmethod
    def _extract_text(result: Any) -> Optional[str]:
        if result is None:
            return None
        if isinstance(result, str):
            text = result.strip()
            return text or None
        if isinstance(result, dict):
            if result.get("error"):
                return None
            for key in ("full_text", "text", "content"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            chunk = result.get("chunk")
            if isinstance(chunk, dict):
                value = chunk.get("text")
                if isinstance(value, str) and value.strip():
                    return value
        text = getattr(result, "text", None)
        if isinstance(text, str) and text.strip():
            return text
        return None

    def _find_unverified_items(
        self,
        memory_items: List[Dict[str, Any]],
        *,
        source_exists: Optional[Callable[[str], bool]] = None,
    ) -> List[Dict[str, Any]]:
        """无 source_ref,或 source_ref 指向的文档在 T0/T1 都不存在。"""
        unverified: List[Dict[str, Any]] = []
        for item in memory_items:
            ref = item.get("source_ref")
            parsed = parse_source_ref(ref)
            if parsed is None:
                flagged = dict(item)
                flagged["flag_reason"] = "无 source_ref,出处不可核"
                unverified.append(flagged)
                continue
            doc_id, _clause = parsed
            if source_exists is not None and not source_exists(doc_id):
                flagged = dict(item)
                flagged["flag_reason"] = f"source_ref 指向的文档不存在: {doc_id}"
                unverified.append(flagged)
        return unverified

    def _find_contradictory_items(
        self, memory_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """同对象、同维度、不可并存的一对记忆。"""
        contradictory_pairs: List[Dict[str, Any]] = []
        for i, item_a in enumerate(memory_items):
            for item_b in memory_items[i + 1:]:
                if self._check_basic_contradiction(item_a, item_b):
                    contradictory_pairs.append({"item_a": item_a, "item_b": item_b})
        return contradictory_pairs

    def _check_basic_contradiction(
        self, item_a: Dict[str, Any], item_b: Dict[str, Any]
    ) -> bool:
        """同对象同属性下的数值冲突或反义共现。

        保留原有「共同属性词 + 数字不同 / 反义词对」判断,外加具体对象门闩:
        两边都点名了具体对象且对象不相交时,不判互斥。
        """
        content_a = item_a.get("content", "").lower()
        content_b = item_b.get("content", "").lower()

        entities_a = extract_specific_entities(content_a)
        entities_b = extract_specific_entities(content_b)
        if entities_a and entities_b and entities_a.isdisjoint(entities_b):
            return False

        numbers_a = extract_fact_numbers(content_a)
        numbers_b = extract_fact_numbers(content_b)

        for keyword in ATTRIBUTE_KEYWORDS:
            if keyword.lower() in content_a and keyword.lower() in content_b:
                if numbers_a and numbers_b and numbers_a != numbers_b:
                    return True
                for pos, neg in OPPOSITE_PAIRS:
                    if (pos in content_a and neg in content_b) or (
                        neg in content_a and pos in content_b
                    ):
                        return True
        return False

    def _find_potentially_dead_items(
        self,
        memory_items: List[Dict[str, Any]],
        *,
        t1_by_memory_id: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """记忆与其 source_ref 对应的 T1 原文冲突才标 dead。

        无 T1 文本时不下死事实(不把「目前/当前」等时效词当判据,也不编空 evidence_ids)。
        """
        t1_by_memory_id = t1_by_memory_id or {}
        potentially_dead: List[Dict[str, Any]] = []
        for item in memory_items:
            t1_info = t1_by_memory_id.get(item.get("memory_id"), {})
            t1_text = (t1_info.get("text") or "").strip()
            if not t1_text:
                continue
            content = item.get("content", "")
            reason = self._t1_conflict_reason(content, t1_text)
            if not reason:
                continue
            flagged = dict(item)
            evidence_id = t1_info.get("evidence_id")
            flagged["evidence_ids"] = [evidence_id] if evidence_id else []
            flagged["flag_reason"] = reason
            potentially_dead.append(flagged)
        return potentially_dead

    def _t1_conflict_reason(self, memory_content: str, t1_text: str) -> Optional[str]:
        """返回冲突理由;无冲突返回 None。"""
        mem = memory_content.lower()
        t1 = t1_text.lower()
        mem_numbers = extract_fact_numbers(mem)
        t1_numbers = extract_fact_numbers(t1)
        shared_attr = [
            kw for kw in ATTRIBUTE_KEYWORDS
            if kw.lower() in mem and kw.lower() in t1
        ]
        shared_entity = extract_specific_entities(mem) & extract_specific_entities(t1)
        superseded = _superseded_numbers(t1)

        if (shared_attr or shared_entity) and mem_numbers and superseded:
            old_in_memory = mem_numbers & set(superseded.keys())
            if old_in_memory:
                mapped = {old: superseded[old] for old in old_in_memory}
                return f"记忆仍使用已被 T1 覆盖的数值 {mapped}"

        if (shared_attr or shared_entity) and mem_numbers and t1_numbers:
            live_t1_numbers = t1_numbers - set(superseded.keys())
            if live_t1_numbers and not mem_numbers.issubset(live_t1_numbers) and (
                live_t1_numbers - mem_numbers
            ):
                return (
                    f"记忆中的数值 {sorted(mem_numbers)} 与 T1 原文数值 "
                    f"{sorted(live_t1_numbers)} 冲突"
                )

        shared_reg = [
            kw for kw in REGULATORY_KEYWORDS
            if kw.lower() in mem and kw.lower() in t1
        ]
        if shared_reg or ("本地化" in mem and "本地化" in t1) or (
            "存储" in mem and "存储" in t1
        ):
            if _contains_any(mem, MEMORY_NEGATION_CUES) and _contains_any(
                t1, T1_MANDATE_CUES
            ):
                return "记忆称监管暂无强制要求,T1 原文已出现强制/生效口径"

        return None
