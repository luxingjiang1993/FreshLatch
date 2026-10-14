"""两条 @T1 对同一可判定前提是否互斥。纯函数,零 I/O。

判定出口在 fresh 交给执行器之前调用。命中则 conflicting_evidence,不得 fresh。
不挑选其中一侧,不把两块合并成一条结论,也不读 CRAG grade。
Ambiguous 是「这份观察不够支持继续写判定」,不是本闸。

可判定前提只认两种字面绑定,容差为空:
- 正文里的前提「键」：取值。取值按去空白后的字符串比较。
- 同一属性词窗口内的数字字面量,或封闭反义对。数字字面量与 verbatim
  数字闸同一抽出规则。不把 12.5 当成 12.50,不把 1,299 当成 1299。

两边都点名了具体对象且对象不同,不是同一前提。一条 span 里同时写出
两个数时,不与另一条只含其中一数的 span 互斥。
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from freshlatch.numeric_gate import extract_numeric_tokens

# 轨迹与工具回执共用这一枚拒因码。不是 grade_ambiguous,也不是 numeric_mismatch。
REASON_CONFLICTING_EVIDENCE = "conflicting_evidence"

# 票内容差。None 表示数字只接受字面量相同,不另设 SESOI。
CONFLICT_NUMERIC_TOLERANCE = None

_VALUE_WINDOW = 18
_ENTITY_PREFIX = 16

# 较长的词放前面,重叠时留给扫描后的贪心去重。
_ATTRIBUTES: tuple[str, ...] = (
    "客单价",
    "月费",
    "年费",
    "定价",
    "报价",
    "售价",
    "价格",
    "费用",
    "成本",
    "收费",
    "金额",
)

# 封闭反义对。只在属性词窗口内生效,不扫整段。
_POLARITY_PAIRS: tuple[tuple[str, str], ...] = (
    ("高于", "低于"),
    ("高于", "降至"),
    ("高于", "降到"),
    ("增加", "减少"),
    ("上调", "下调"),
    ("仍为", "不再"),
)
_CUES: tuple[str, ...] = tuple(
    dict.fromkeys(cue for pair in _POLARITY_PAIRS for cue in pair)
)

_EXPLICIT_PREMISE = re.compile(
    r"前提「([^」]{1,40})」[：:]\s*([^，。；;\n]{1,40})"
)
_ENTITY = re.compile(
    r"竞品[A-Za-z0-9]+|SeaDesk|专业版|免费版|标准版|企业版|基础版|"
    r"印尼|泰国|越南|菲律宾|PDP",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class T1Span:
    """一条可引用的 @T1 块。"""

    evidence_id: str
    text: str


@dataclass(frozen=True)
class ConflictPair:
    """同一前提上的一对互斥取值。没有获胜侧。"""

    premise: str
    left_id: str
    right_id: str
    left_value: str
    right_value: str


@dataclass(frozen=True)
class ConflictScan:
    """ok 为真时本闸不拒。pairs 保持 span 的出现顺序。"""

    ok: bool
    reason_code: str | None
    pairs: tuple[ConflictPair, ...]


class _SlotBuilder:
    """同一 span 里同一对象、同一属性的取值累积。"""

    def __init__(self, entity: str, attr: str) -> None:
        self.entity = entity
        self.attr = attr
        self.numbers: set[str] = set()
        self.cues: set[str] = set()


@dataclass(frozen=True)
class _Slot:
    entity: str
    attr: str
    numbers: frozenset[str]
    cues: frozenset[str]


def t1_spans_from_tool_trace(tool_trace: Iterable[object]) -> tuple[T1Span, ...]:
    """从本轮 retrieve 观察收集 @T1 块。同一 evidence_id 只保留第一次。"""
    found: dict[str, str] = {}
    order: list[str] = []
    for record in tool_trace:
        if not isinstance(record, dict) or record.get("tool") != "retrieve":
            continue
        result = record.get("result")
        if not isinstance(result, dict):
            continue
        blocks = result.get("blocks")
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict):
                continue
            evidence_id = block.get("evidence_id")
            text = block.get("text")
            if not isinstance(evidence_id, str) or not evidence_id.endswith("@T1"):
                continue
            if not isinstance(text, str) or evidence_id in found:
                continue
            order.append(evidence_id)
            found[evidence_id] = text
    return tuple(T1Span(evidence_id=eid, text=found[eid]) for eid in order)


def find_conflicting_evidence(spans: Iterable[T1Span]) -> ConflictScan:
    """两块 @T1 对同一可判定前提互斥则给出 conflicting_evidence。

    不读 grade,不调用模型,不返回应采纳的那一侧。
    """
    usable: list[T1Span] = []
    seen: set[str] = set()
    for span in spans:
        evidence_id = span.evidence_id
        if not isinstance(evidence_id, str) or not evidence_id.endswith("@T1"):
            continue
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        usable.append(span)
    found: list[ConflictPair] = []
    seen_pairs: set[tuple[str, str, str, str, str]] = set()
    for index, left in enumerate(usable):
        for right in usable[index + 1:]:
            for pair in _pairs_between(left, right):
                key = (
                    pair.premise,
                    pair.left_id,
                    pair.right_id,
                    pair.left_value,
                    pair.right_value,
                )
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                found.append(pair)
    if not found:
        return ConflictScan(ok=True, reason_code=None, pairs=())
    return ConflictScan(
        ok=False,
        reason_code=REASON_CONFLICTING_EVIDENCE,
        pairs=tuple(found),
    )


def conflicting_evidence_message(pairs: Iterable[ConflictPair]) -> str:
    """回给模型的观察。reason_code 另字段携带,文案本身不是原因码。"""
    shown = "、".join(
        f"{pair.left_id}↔{pair.right_id}"
        f"[{pair.premise}:{pair.left_value}|{pair.right_value}]"
        for pair in pairs
    )
    return (
        "reverify_claim(fresh) 拒绝: 两条 @T1 对同一可判定前提互斥,"
        f"reason_code={REASON_CONFLICTING_EVIDENCE}。"
        "不得写 fresh,不得挑选其中一侧,不得静默合并。须人审。"
        f"互斥对: {shown}"
    )


def fresh_refusal_for_conflicting_evidence(tool_trace: Iterable[object]) -> dict | None:
    """本轮观察里已有互斥对时,返回 fresh 拒答。没有互斥对则返回 None。"""
    scan = find_conflicting_evidence(t1_spans_from_tool_trace(tool_trace))
    if scan.ok:
        return None
    return {
        "abstain": True,
        "error": conflicting_evidence_message(scan.pairs),
        "reason_code": scan.reason_code,
        "pairs": [
            {
                "premise": pair.premise,
                "left_id": pair.left_id,
                "right_id": pair.right_id,
                "left_value": pair.left_value,
                "right_value": pair.right_value,
            }
            for pair in scan.pairs
        ],
    }


def _pairs_between(left: T1Span, right: T1Span) -> list[ConflictPair]:
    found: list[ConflictPair] = []
    found.extend(_explicit_pairs(left, right))
    found.extend(_attribute_pairs(left, right))
    return found


def _explicit_pairs(left: T1Span, right: T1Span) -> list[ConflictPair]:
    left_map = _explicit_map(left.text)
    right_map = _explicit_map(right.text)
    found: list[ConflictPair] = []
    for key, left_value in left_map.items():
        right_value = right_map.get(key)
        if right_value is None or right_value == left_value:
            continue
        found.append(ConflictPair(
            premise=key,
            left_id=left.evidence_id,
            right_id=right.evidence_id,
            left_value=left_value,
            right_value=right_value,
        ))
    return found


def _explicit_map(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for key, value in _EXPLICIT_PREMISE.findall(text or ""):
        premise = key.strip()
        bound = value.strip()
        if premise and bound and premise not in found:
            found[premise] = bound
    return found


def _attribute_pairs(left: T1Span, right: T1Span) -> list[ConflictPair]:
    found: list[ConflictPair] = []
    for left_slot in _slots(left.text):
        for right_slot in _slots(right.text):
            if left_slot.attr != right_slot.attr:
                continue
            if not _same_premise_entity(left_slot.entity, right_slot.entity):
                continue
            premise = _premise_label(left_slot, right_slot)
            if (
                left_slot.numbers
                and right_slot.numbers
                and left_slot.numbers.isdisjoint(right_slot.numbers)
            ):
                found.append(ConflictPair(
                    premise=premise,
                    left_id=left.evidence_id,
                    right_id=right.evidence_id,
                    left_value=_join_values(left_slot.numbers),
                    right_value=_join_values(right_slot.numbers),
                ))
            polarity = _polarity_values(left_slot.cues, right_slot.cues)
            if polarity is not None:
                left_value, right_value = polarity
                found.append(ConflictPair(
                    premise=premise,
                    left_id=left.evidence_id,
                    right_id=right.evidence_id,
                    left_value=left_value,
                    right_value=right_value,
                ))
    return found


def _slots(text: str) -> list[_Slot]:
    merged: dict[tuple[str, str], _SlotBuilder] = {}
    order: list[tuple[str, str]] = []
    for start, end, attr in _attribute_hits(text or ""):
        entity = _nearest_entity(text[max(0, start - _ENTITY_PREFIX):start])
        key = (entity.casefold(), attr)
        window = text[end:end + _VALUE_WINDOW]
        builder = merged.get(key)
        if builder is None:
            builder = _SlotBuilder(entity=entity, attr=attr)
            merged[key] = builder
            order.append(key)
        builder.numbers.update(extract_numeric_tokens(window))
        for cue in _CUES:
            if _has_cue(window, cue):
                builder.cues.add(cue)
    return [
        _Slot(
            entity=merged[key].entity,
            attr=merged[key].attr,
            numbers=frozenset(merged[key].numbers),
            cues=frozenset(merged[key].cues),
        )
        for key in order
    ]


def _attribute_hits(text: str) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    for attr in _ATTRIBUTES:
        start = 0
        while True:
            index = text.find(attr, start)
            if index < 0:
                break
            found.append((index, index + len(attr), attr))
            start = index + 1
    found.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    taken: list[tuple[int, int, str]] = []
    occupied_until = -1
    for start, end, attr in found:
        if start < occupied_until:
            continue
        taken.append((start, end, attr))
        occupied_until = end
    return taken


def _nearest_entity(prefix: str) -> str:
    found = list(_ENTITY.finditer(prefix))
    if not found:
        return ""
    return found[-1].group(0)


def _same_premise_entity(left: str, right: str) -> bool:
    if left and right and left.casefold() != right.casefold():
        return False
    return True


def _premise_label(left: _Slot, right: _Slot) -> str:
    entity = left.entity or right.entity
    if entity:
        return f"{entity}{left.attr}"
    return left.attr


def _join_values(values: frozenset[str]) -> str:
    return "、".join(sorted(values))


def _has_cue(window: str, cue: str) -> bool:
    """「不低于」里的「低于」不是反义断言。"""
    start = 0
    while True:
        index = window.find(cue, start)
        if index < 0:
            return False
        if index == 0 or window[index - 1] != "不":
            return True
        start = index + len(cue)


def _polarity_values(
    left_cues: frozenset[str],
    right_cues: frozenset[str],
) -> tuple[str, str] | None:
    for pos, neg in _POLARITY_PAIRS:
        left_pos = pos in left_cues
        left_neg = neg in left_cues
        right_pos = pos in right_cues
        right_neg = neg in right_cues
        if (left_pos and left_neg) or (right_pos and right_neg):
            continue
        if left_pos and right_neg:
            return pos, neg
        if left_neg and right_pos:
            return neg, pos
    return None
