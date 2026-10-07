"""PE-07：用户抽检与三家评委分歧的裁决导出。

抽检单独构造 ``random.Random(20261007)``，按层先打乱正确 ``claim_id`` 再打乱坏 ``claim_id``。
用户表只含修改和证据。身份是模型评委加单人抽检，角色是用户单人抽检。
本模块不调用评委接口，不改构造金标，也不删样本。
"""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from typing import Any

from freshlatch.eval.patch_events_construct import STRATA

SPOTCHECK_SEED = 20261007
IDENTITY = "模型评委加单人抽检"
SPOTCHECK_ROLE = "用户单人抽检"
ALREADY = "已有抽检答案，不再第二次看"
SOURCE_JUDGES = "三评委一致"
SOURCE_USER = "用户裁决"

_GOLD_ORDER = ("正确", "坏")
_JUDGE_IDS = ("qwen", "deepseek", "kimi")
_QUESTIONS = ("A", "B")
_LABELS = frozenset({"是", "否"})
_USER_KEYS = ("claim_id", "before_text", "after_text", "evidence_text", "evidence_id")
_QUOTAS: dict[int, dict[str, int]] = {
    30: {"正确": 1, "坏": 1},
    100: {"正确": 2, "坏": 3},
}


class SpotcheckError(ValueError):
    """抽检配额、记录或标签表不成立。"""


def _shuffle(items: Sequence[Any], rng: random.Random) -> list[Any]:
    """全量打乱。只调用 ``random()``，再取前缀，3.11 与 3.12 的顺序一致。"""
    out = list(items)
    for index in range(len(out) - 1, 0, -1):
        swap = int(rng.random() * (index + 1))
        out[index], out[swap] = out[swap], out[index]
    return out


def select_spotcheck(
    records: Sequence[Mapping[str, Any]],
    *,
    n: int,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    """按 PREREG 配额抽出抽检记录。不接收评委标签。"""
    if n not in _QUOTAS:
        raise SpotcheckError(f"抽检规模只接受 30 或 100，收到 {n}")
    quotas = _QUOTAS[n]
    stream = random.Random(SPOTCHECK_SEED) if rng is None else rng
    pools: dict[tuple[str, str], list[dict[str, Any]]] = {}
    seen: set[str] = set()
    for record in records:
        if "claim_id" not in record:
            raise SpotcheckError("记录缺 claim_id")
        claim_id = str(record["claim_id"])
        if claim_id in seen:
            raise SpotcheckError(f"claim_id 重复: {claim_id}")
        seen.add(claim_id)
        edit_type = record.get("edit_type")
        gold = record.get("construction_gold")
        if edit_type not in STRATA:
            raise SpotcheckError(f"edit_type 非法: {edit_type!r}")
        if gold not in _GOLD_ORDER:
            raise SpotcheckError(f"construction_gold 非法: {gold!r}")
        missing = [key for key in _USER_KEYS if key not in record]
        if missing:
            raise SpotcheckError(f"{claim_id} 缺字段: {', '.join(missing)}")
        pools.setdefault((str(edit_type), str(gold)), []).append(dict(record))

    selected: list[dict[str, Any]] = []
    for edit_type in STRATA:
        for gold in _GOLD_ORDER:
            need = quotas[gold]
            bucket = pools.get((edit_type, gold), [])
            if len(bucket) < need:
                raise SpotcheckError(f"{edit_type} 的{gold}只有 {len(bucket)} 条，抽检需要 {need} 条")
            ordered = sorted(bucket, key=lambda row: str(row["claim_id"]))
            selected.extend(_shuffle(ordered, stream)[:need])
    return selected


def _cell(block: object, question: str) -> str | None:
    if not isinstance(block, Mapping):
        return None
    value = block.get(question)
    if value in _LABELS:
        return str(value)
    return None


def _classify(row: Mapping[str, Any] | None) -> tuple[str, list[str]]:
    gaps: list[str] = []
    present: dict[tuple[str, str], str] = {}
    for judge in _JUDGE_IDS:
        block = row.get(judge) if isinstance(row, Mapping) else None
        for question in _QUESTIONS:
            value = _cell(block, question)
            if value is None:
                gaps.append(f"{judge}:{question}")
            else:
                present[(judge, question)] = value
    if gaps:
        return "missing", gaps
    answers_a = {present[(judge, "A")] for judge in _JUDGE_IDS}
    answers_b = {present[(judge, "B")] for judge in _JUDGE_IDS}
    if len(answers_a) == 1 and len(answers_b) == 1:
        return "same", []
    return "disagree", []


def _index_labels(labels: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for row in labels:
        if "claim_id" not in row:
            raise SpotcheckError("标签行缺 claim_id")
        claim_id = str(row["claim_id"])
        if claim_id in indexed:
            raise SpotcheckError(f"评委标签 claim_id 重复: {claim_id}")
        indexed[claim_id] = row
    return indexed


def _user_row(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: record[key] for key in _USER_KEYS}


def _written_answer(claim_id: str, answers: Mapping[str, Any], spot_ids: set[str]) -> Any:
    if claim_id not in spot_ids:
        return None
    answer = answers.get(claim_id)
    if answer is None or answer == "" or answer == {}:
        return None
    if isinstance(answer, Mapping):
        return dict(answer)
    return answer


def _render_row(row: Mapping[str, Any], *, with_decision: bool) -> str:
    lines = [str(row[key]) for key in _USER_KEYS]
    if with_decision:
        decision = row.get("裁决")
        if decision:
            if isinstance(decision, Mapping):
                lines.append(json.dumps(dict(decision), ensure_ascii=False, sort_keys=True))
            else:
                lines.append(str(decision))
        note = row.get("备注") or ""
        if note:
            lines.append(str(note))
    return "\n".join(lines)


def _render(
    spotcheck: Sequence[Mapping[str, Any]],
    adjudication: Sequence[Mapping[str, Any]],
    missing: Sequence[Mapping[str, Any]],
) -> str:
    parts = [IDENTITY, SPOTCHECK_ROLE, "抽检表"]
    parts.extend(_render_row(row, with_decision=False) for row in spotcheck)
    parts.append("不一致裁决表")
    parts.extend(_render_row(row, with_decision=True) for row in adjudication)
    parts.append("缺失清单")
    for row in missing:
        gaps = " ".join(str(item) for item in row["缺失"])
        parts.append(f"{row['claim_id']} {gaps}".rstrip())
    return "\n".join(parts)


def export_spotcheck(
    records: Sequence[Mapping[str, Any]],
    labels: Sequence[Mapping[str, Any]] | None = None,
    *,
    n: int,
    answers: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """导出抽检表、不一致裁决表和缺失清单。抽检选择不读取 ``labels``。"""
    selected = select_spotcheck(records, n=n)
    spotcheck = [_user_row(row) for row in selected]
    spot_ids = {str(row["claim_id"]) for row in spotcheck}
    written = answers or {}
    adjudication: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    if labels is not None:
        indexed = _index_labels(labels)
        for record in sorted(records, key=lambda row: str(row["claim_id"])):
            claim_id = str(record["claim_id"])
            kind, gaps = _classify(indexed.get(claim_id))
            if kind == "missing":
                missing.append({"claim_id": claim_id, "缺失": gaps})
            elif kind == "disagree":
                item = _user_row(record)
                answer = _written_answer(claim_id, written, spot_ids)
                if answer is None:
                    item["裁决"] = ""
                    item["备注"] = ""
                else:
                    item["裁决"] = answer
                    item["备注"] = ALREADY
                adjudication.append(item)
    text = _render(spotcheck, adjudication, missing)
    return {
        "identity": IDENTITY,
        "spotcheck_role": SPOTCHECK_ROLE,
        "spotcheck": spotcheck,
        "adjudication": adjudication,
        "missing": missing,
        "text": text,
    }


def _pair(answer: object) -> tuple[str, str] | None:
    if not isinstance(answer, Mapping):
        return None
    left = answer.get("A")
    right = answer.get("B")
    if left in _LABELS and right in _LABELS:
        return str(left), str(right)
    return None


def _mapped(left: str, right: str) -> str:
    """A 与 B 都是「是」才映成正确。任一为否映成坏。"""
    if left == "是" and right == "是":
        return "正确"
    return "坏"


def _conflict_row(record: Mapping[str, Any], mapped: str, source: str) -> dict[str, Any]:
    return {
        "claim_id": record["claim_id"],
        "before_text": record["before_text"],
        "after_text": record["after_text"],
        "evidence_text": record["evidence_text"],
        "evidence_id": record["evidence_id"],
        "construction_gold": record["construction_gold"],
        "最终标签": mapped,
        "最终标签来源": source,
    }


def _render_conflicts(
    conflicts: Sequence[Mapping[str, Any]],
    missing: Sequence[Mapping[str, Any]],
) -> str:
    parts = [IDENTITY, SPOTCHECK_ROLE, "冲突清单"]
    for row in conflicts:
        parts.append(
            "\n".join(
                [
                    str(row["claim_id"]),
                    str(row["before_text"]),
                    str(row["after_text"]),
                    str(row["evidence_text"]),
                    str(row["evidence_id"]),
                    str(row["construction_gold"]),
                    str(row["最终标签"]),
                    str(row["最终标签来源"]),
                ]
            )
        )
    parts.append("缺失清单")
    for row in missing:
        gaps = " ".join(str(item) for item in row["缺失"])
        parts.append(f"{row['claim_id']} {gaps}".rstrip())
    return "\n".join(parts)


def export_conflicts(
    records: Sequence[Mapping[str, Any]],
    labels: Sequence[Mapping[str, Any]] | None = None,
    *,
    answers: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """列出最终标签与构造金标不同的条目。未完成裁决时不给出冲突结论。

    三家在 A、B 上都一致时，最终标签用共同答案。否则用用户裁决。
    缺评委标签的条目只进缺失清单。不改构造金标，不抽随机数。
    """
    written = answers or {}
    indexed = _index_labels(labels or [])
    pending: list[str] = []
    conflicts: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    seen: set[str] = set()
    ordered = sorted(records, key=lambda row: str(row["claim_id"]))
    prepared: list[tuple[Mapping[str, Any], str, str]] = []
    for record in ordered:
        if "claim_id" not in record or "construction_gold" not in record:
            raise SpotcheckError("冲突清单缺 claim_id 或 construction_gold")
        claim_id = str(record["claim_id"])
        if claim_id in seen:
            raise SpotcheckError(f"claim_id 重复: {claim_id}")
        seen.add(claim_id)
        gold = record["construction_gold"]
        if gold not in _GOLD_ORDER:
            raise SpotcheckError(f"construction_gold 非法: {gold!r}")
        kind, gaps = _classify(indexed.get(claim_id))
        if kind == "missing":
            missing.append({"claim_id": claim_id, "缺失": gaps})
            continue
        label_row = indexed[claim_id]
        if kind == "same":
            common = label_row[_JUDGE_IDS[0]]
            pair = _pair(common)
            if pair is None:
                raise SpotcheckError(f"共同答案无法映射: {claim_id}")
            prepared.append((record, _mapped(*pair), SOURCE_JUDGES))
            continue
        pair = _pair(written.get(claim_id))
        if pair is None:
            pending.append(claim_id)
            continue
        prepared.append((record, _mapped(*pair), SOURCE_USER))
    if pending:
        raise SpotcheckError("裁决未完成: " + ", ".join(pending))
    for record, mapped, source in prepared:
        if mapped == record["construction_gold"]:
            continue
        conflicts.append(_conflict_row(record, mapped, source))
    return {
        "identity": IDENTITY,
        "spotcheck_role": SPOTCHECK_ROLE,
        "conflicts": conflicts,
        "missing": missing,
        "text": _render_conflicts(conflicts, missing),
    }
