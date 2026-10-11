"""patch_events 主实验的构造器。

只读 thesis-1 主张和语料，按 PREREG 的配额与算子写出实验记录。
不调用模型，不写产品账本，不改配额表。共形预留不从这三档配额里取。

组别要等后续实验组票才跑。实验记录 schema 要求 arm，这里先写 T、ablation 为空，
不代表已经跑过 T。构造阶段不填 decision。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from freshlatch.eval.patch_events_exp import normalize_experiment_record
from freshlatch.store.ingest import parse_document

STRATA: tuple[str, ...] = ("数值", "日期", "条款替换", "删除")

# (正确条数, 坏条数)。数字来自 PREREG 配额表，本模块不改那一页。
QUOTAS: dict[str, dict[str, tuple[int, int]]] = {
    "pilot": {
        "数值": (2, 2),
        "日期": (2, 2),
        "条款替换": (2, 2),
        "删除": (1, 2),
    },
    "n30": {
        "数值": (4, 4),
        "日期": (4, 4),
        "条款替换": (4, 4),
        "删除": (3, 3),
    },
    "n100": {
        "数值": (12, 13),
        "日期": (12, 13),
        "条款替换": (12, 13),
        "删除": (12, 13),
    },
}

_UNIT_CYCLE: tuple[str, ...] = ("%", "个百分点", "元", "万元")
_NUM_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(个百分点|万元|美元|元|%)")
_DATE_RE = re.compile(r"(\d{4})\s*年\s*(\d{1,2})\s*月(?:\s*(\d{1,2})\s*日)?")
_OB_RE = re.compile(r"([^。\n]{0,80}?)(应当|不得)([^。\n]*)")
_QUAL_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"除[^，。；\n]{1,30}外"),
    re.compile(r"留存不少于\s*\d+\s*年"),
    re.compile(r"不少于\s*\d+\s*[^，。；\n]{0,12}"),
    re.compile(r"不超过\s*\d+\s*[^，。；\n]{0,12}"),
    re.compile(r"至少\s*\d+\s*[^，。；\n]{0,12}"),
    re.compile(r"至多\s*\d+\s*[^，。；\n]{0,12}"),
)
_MODIFIERS: tuple[str, ...] = ("大约", "约", "显著", "明显", "初步", "大致", "基本")
_VERBS: tuple[str, ...] = (
    "存储",
    "保存",
    "留存",
    "导出",
    "删除",
    "更新",
    "提供",
    "披露",
    "传输",
    "处理",
    "使用",
    "遵守",
    "要求",
)
_ABOLISH = ("废止", "不再存在", "不再要求", "不再")
_AFFIRM = ("仍然", "仍", "继续")
_SCHEMA_ARM = "T"


class ConstructError(ValueError):
    """这个槽做不出来。structural 为真时，该主张在本层后面的槽位不再重试。"""

    def __init__(self, reason: str, *, structural: bool) -> None:
        super().__init__(reason)
        self.reason = reason
        self.structural = structural


@dataclass(frozen=True)
class ChunkRef:
    anchor: str
    evidence_id: str
    body: str


@dataclass(frozen=True)
class ClaimView:
    claim_id: str
    statement: str
    doc_id: str
    anchor: str
    t1: ChunkRef | None
    t0: ChunkRef | None
    t1_chunks: tuple[ChunkRef, ...]
    t0_chunks: tuple[ChunkRef, ...]


@dataclass(frozen=True)
class ConstructedEdit:
    record: dict[str, Any]
    operator: int | None
    sign: str | None
    edit_note: str


@dataclass(frozen=True)
class Shortfall:
    claim_id: str
    edit_type: str
    reason: str
    operator: int | None


@dataclass(frozen=True)
class ConstructResult:
    pilot: tuple[ConstructedEdit, ...]
    n30: tuple[ConstructedEdit, ...]
    n100: tuple[ConstructedEdit, ...]
    shortfalls: tuple[Shortfall, ...]


@dataclass(frozen=True)
class _NumTok:
    start: int
    end: int
    value: Decimal
    unit: str
    integer: bool


@dataclass(frozen=True)
class _DateTok:
    start: int
    end: int
    year: int
    month: int
    day: int | None
    raw: str


@dataclass(frozen=True)
class _Obligation:
    subject: str
    marker: str
    sentence: str


def round_half_away_from_zero(value: Decimal, places: int) -> Decimal:
    """0.5 远离 0。places=0 取整数，否则保留相应小数位。"""
    quant = Decimal(10) ** -places
    return value.quantize(quant, rounding=ROUND_HALF_UP)


def shift_month(year: int, month: int, day: int | None, delta: int) -> tuple[int, int, int | None]:
    """月份 ±delta，跨年进位。目标月没有这一天则该槽作废。"""
    month_index = month - 1 + delta
    year += month_index // 12
    month = month_index % 12 + 1
    if day is not None and day > _days_in_month(year, month):
        raise ConstructError("日期无效", structural=False)
    return year, month, day


def construct_samples(docket_path: Path, corpus_root: Path) -> ConstructResult:
    """按 claim_id 字典序构造 pilot、n=30、n=100。不使用随机数，重复构造逐位一致。"""
    views = load_claims(docket_path, corpus_root)
    pilot: list[ConstructedEdit] = []
    n30: list[ConstructedEdit] = []
    rest: list[ConstructedEdit] = []
    shortfalls: list[Shortfall] = []
    pool = list(views)
    for edit_type in STRATA:
        pilot_slots, n30_slots, rest_slots = _slot_labels(edit_type)
        bad_index = 0
        structural_skip: set[str] = set()
        for tier, slots in (
            ("pilot", pilot_slots),
            ("n30", n30_slots),
            ("rest", rest_slots),
        ):
            bucket = {"pilot": pilot, "n30": n30, "rest": rest}[tier]
            for gold in slots:
                edit, pool, bad_index, skipped = _take_slot(
                    pool,
                    edit_type,
                    gold,
                    bad_index,
                    structural_skip,
                )
                shortfalls.extend(skipped)
                if edit is not None:
                    bucket.append(edit)
    return ConstructResult(
        pilot=tuple(pilot),
        n30=tuple(n30),
        n100=tuple(n30 + rest),
        shortfalls=tuple(shortfalls),
    )


def construct_from_pins(
    docket_path: Path,
    corpus_root: Path,
    pins: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """按名单针 (claim_id, edit_type, construction_gold) 确定性构造实验记录。

    供路线 Y n=400 等超出 pilot/n30/n100 配额的正式名单使用。
    层内坏槽的算子编号按针内出现序递增（同 ``construct_samples`` 的 bad_index 语义）。
    构造失败则抛 ``ConstructError``，不得静默跳过冒充满额。
    """
    views = {view.claim_id: view for view in load_claims(docket_path, corpus_root)}
    bad_index_by_stratum: dict[str, int] = {name: 0 for name in STRATA}
    records: list[dict[str, Any]] = []
    for pin in pins:
        claim_id = str(pin["claim_id"])
        edit_type = str(pin["edit_type"])
        gold = str(pin["construction_gold"])
        view = views.get(claim_id)
        if view is None:
            raise ConstructError(f"名单针主张不在 docket：{claim_id}", structural=True)
        if edit_type not in STRATA:
            raise ConstructError(f"未知层: {edit_type}", structural=True)
        if gold == "坏":
            bad_index = bad_index_by_stratum[edit_type]
            operator = bad_index % 4
            sign = _sign(bad_index)
            bad_index_by_stratum[edit_type] = bad_index + 1
        elif gold == "正确":
            operator = None
            sign = None
        else:
            raise ConstructError(f"construction_gold 非法: {gold!r}", structural=True)
        edit = _build(view, edit_type, gold, operator, sign)
        records.append(dict(edit.record))
    return records


def load_claims(docket_path: Path, corpus_root: Path) -> list[ClaimView]:
    payload = json.loads(Path(docket_path).read_text(encoding="utf-8"))
    claims = list(payload.get("claims") or [])
    claims.sort(key=lambda row: str(row.get("claim_id", "")))
    index = _chunk_index(corpus_root)
    views: list[ClaimView] = []
    for row in claims:
        views.append(_view_from_row(row, index))
    return views


def _slot_labels(edit_type: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    pilot_c, pilot_b = QUOTAS["pilot"][edit_type]
    n30_c, n30_b = QUOTAS["n30"][edit_type]
    n100_c, n100_b = QUOTAS["n100"][edit_type]
    pilot = tuple(_alternate(pilot_b, pilot_c))
    n30 = tuple(_alternate(n30_b, n30_c))
    rest = tuple(_alternate(n100_b - n30_b, n100_c - n30_c))
    return pilot, n30, rest


def _alternate(n_bad: int, n_correct: int) -> list[str]:
    """坏、正确交替。坏比正确多一条时，多出的坏放在段尾。"""
    labels: list[str] = []
    bad = correct = 0
    while bad < n_bad or correct < n_correct:
        if bad < n_bad and (bad == correct or correct >= n_correct):
            labels.append("坏")
            bad += 1
        else:
            labels.append("正确")
            correct += 1
    return labels


def _take_slot(
    pool: list[ClaimView],
    edit_type: str,
    gold: str,
    bad_index: int,
    structural_skip: set[str],
) -> tuple[ConstructedEdit | None, list[ClaimView], int, list[Shortfall]]:
    operator = bad_index % 4 if gold == "坏" else None
    sign = _sign(bad_index) if gold == "坏" else None
    skipped: list[Shortfall] = []
    tried: set[str] = set()
    for view in pool:
        if view.claim_id in structural_skip or view.claim_id in tried:
            continue
        try:
            edit = _build(view, edit_type, gold, operator, sign)
        except ConstructError as exc:
            skipped.append(
                Shortfall(view.claim_id, edit_type, exc.reason, operator)
            )
            tried.add(view.claim_id)
            if exc.structural:
                structural_skip.add(view.claim_id)
            continue
        kept = [item for item in pool if item.claim_id != view.claim_id]
        next_index = bad_index + 1 if gold == "坏" else bad_index
        return edit, kept, next_index, skipped
    skipped.append(Shortfall("", edit_type, "语料不足", operator))
    return None, pool, bad_index, skipped


def _sign(bad_index: int) -> str:
    return "plus" if (bad_index // 4) % 2 == 0 else "minus"


def _build(
    view: ClaimView,
    edit_type: str,
    gold: str,
    operator: int | None,
    sign: str | None,
) -> ConstructedEdit:
    if view.t1 is None:
        raise ConstructError("没有对应的 T1 chunk", structural=True)
    if edit_type == "数值":
        after, evidence_id, evidence_text, note = _numeric(view, gold, operator, sign)
    elif edit_type == "日期":
        after, evidence_id, evidence_text, note = _date(view, gold, operator, sign)
    elif edit_type == "条款替换":
        after, evidence_id, evidence_text, note = _clause(view, gold, operator, sign)
    elif edit_type == "删除":
        after, evidence_id, evidence_text, note = _deletion(view, gold, operator, sign)
    else:
        raise ConstructError(f"未知层: {edit_type}", structural=True)
    record = normalize_experiment_record(
        {
            "claim_id": view.claim_id,
            "edit_type": edit_type,
            "arm": _SCHEMA_ARM,
            "ablation": "",
            "construction_gold": gold,
            "before_text": view.statement,
            "after_text": after,
            "evidence_id": evidence_id,
            "evidence_text": evidence_text,
        }
    )
    return ConstructedEdit(record=record, operator=operator, sign=sign, edit_note=note)


def _numeric(
    view: ClaimView,
    gold: str,
    operator: int | None,
    sign: str | None,
) -> tuple[str, str, str, str]:
    assert view.t1 is not None
    claim_nums = _find_numbers(view.statement)
    chunk_nums = _find_numbers(view.t1.body)
    pair = _pair_number(claim_nums, chunk_nums)
    if pair is None:
        raise ConstructError("没有可配对的数值", structural=True)
    claim_tok, correct_tok = pair
    correct_raw = _format_number(correct_tok.value, correct_tok.integer)
    correct_text = _replace_span(
        view.statement,
        claim_tok.start,
        claim_tok.end,
        _join_number_unit(correct_raw, claim_tok.unit, view.statement[claim_tok.start:claim_tok.end]),
    )
    evidence_id = view.t1.evidence_id
    evidence_text = view.t1.body
    if gold == "正确":
        return correct_text, evidence_id, evidence_text, ""
    assert operator is not None and sign is not None
    plus = sign == "plus"
    if operator == 0:
        after = _numeric_percent(correct_text, correct_raw, correct_tok, plus)
    elif operator == 1:
        after = _numeric_scale(correct_text, correct_raw, correct_tok, plus)
    elif operator == 2:
        after = _numeric_other(correct_text, correct_raw, correct_tok, chunk_nums, plus)
    else:
        after = _numeric_unit(correct_text, correct_raw, correct_tok.unit, plus)
    _reject_if_same(after, correct_text, evidence_id, evidence_id)
    return after, evidence_id, evidence_text, ""


def _numeric_percent(correct_text: str, correct_raw: str, tok: _NumTok, plus: bool) -> str:
    factor = Decimal("1.1") if plus else Decimal("0.9")
    raw = tok.value * factor
    places = 0 if tok.integer else 2
    rounded = round_half_away_from_zero(raw, places)
    if rounded == tok.value:
        raise ConstructError("扰动结果与正确值相同", structural=False)
    shown = f"{rounded:.2f}" if places else str(int(rounded))
    return correct_text.replace(correct_raw, shown, 1)


def _numeric_scale(correct_text: str, correct_raw: str, tok: _NumTok, plus: bool) -> str:
    raw = tok.value * 10 if plus else tok.value / Decimal(10)
    if raw == tok.value:
        raise ConstructError("扰动结果与正确值相同", structural=False)
    shown = _format_number(raw, raw == raw.to_integral_value())
    return correct_text.replace(correct_raw, shown, 1)


def _numeric_other(
    correct_text: str,
    correct_raw: str,
    tok: _NumTok,
    chunk_nums: list[_NumTok],
    plus: bool,
) -> str:
    distinct = []
    seen: set[Decimal] = set()
    for item in chunk_nums:
        if item.value in seen:
            continue
        seen.add(item.value)
        distinct.append(item.value)
    others = [value for value in distinct if value != tok.value]
    if len(distinct) < 2 or not others:
        raise ConstructError("chunk 里少于两个不同数字", structural=False)
    picked = max(others) if plus else min(others)
    shown = _format_number(picked, picked == picked.to_integral_value())
    return correct_text.replace(correct_raw, shown, 1)


def _numeric_unit(correct_text: str, correct_raw: str, unit: str, plus: bool) -> str:
    if unit not in _UNIT_CYCLE:
        raise ConstructError("单位不在循环里", structural=False)
    index = _UNIT_CYCLE.index(unit)
    step = 1 if plus else -1
    nxt = _UNIT_CYCLE[(index + step) % len(_UNIT_CYCLE)]
    swapped = correct_text.replace(f"{correct_raw}{unit}", f"{correct_raw}{nxt}", 1)
    if swapped == correct_text:
        swapped = correct_text.replace(f"{correct_raw} {unit}", f"{correct_raw} {nxt}", 1)
    if swapped == correct_text:
        raise ConstructError("换完与原文相同", structural=False)
    return swapped


def _date(
    view: ClaimView,
    gold: str,
    operator: int | None,
    sign: str | None,
) -> tuple[str, str, str, str]:
    assert view.t1 is not None
    claim_dates = _find_dates(view.statement)
    chunk_dates = _find_dates(view.t1.body)
    if not claim_dates or not chunk_dates:
        raise ConstructError("没有可配对的日期", structural=True)
    claim_tok = claim_dates[0]
    correct = chunk_dates[0]
    correct_raw = _format_date(correct.year, correct.month, correct.day)
    correct_text = view.statement.replace(claim_tok.raw, correct_raw, 1)
    evidence_id = view.t1.evidence_id
    evidence_text = view.t1.body
    if gold == "正确":
        return correct_text, evidence_id, evidence_text, ""
    assert operator is not None and sign is not None
    plus = sign == "plus"
    if operator == 0:
        year = correct.year + (1 if plus else -1)
        after = correct_text.replace(
            correct_raw, _format_date(year, correct.month, correct.day), 1
        )
        _reject_if_same(after, correct_text, evidence_id, evidence_id)
        return after, evidence_id, evidence_text, ""
    if operator == 1:
        year, month, day = shift_month(
            correct.year, correct.month, correct.day, 1 if plus else -1
        )
        after = correct_text.replace(correct_raw, _format_date(year, month, day), 1)
        _reject_if_same(after, correct_text, evidence_id, evidence_id)
        return after, evidence_id, evidence_text, ""
    if operator == 2:
        others = _other_dates(view, correct)
        if not others:
            raise ConstructError("没有另一个日期", structural=False)
        picked = max(others) if plus else min(others)
        after = correct_text.replace(
            correct_raw, _format_date(picked[0], picked[1], picked[2]), 1
        )
        _reject_if_same(after, correct_text, evidence_id, evidence_id)
        return after, evidence_id, evidence_text, ""
    if view.t0 is None:
        raise ConstructError("没有 T0", structural=False)
    return correct_text, view.t0.evidence_id, view.t0.body, ""


def _clause(
    view: ClaimView,
    gold: str,
    operator: int | None,
    sign: str | None,
) -> tuple[str, str, str, str]:
    assert view.t1 is not None
    bound = _obligations(view.t1.body)
    if not bound:
        raise ConstructError("没有可配对的条款", structural=True)
    claim_obs = _obligations(view.statement)
    chosen = bound[0]
    if claim_obs:
        for item in bound:
            if item.subject == claim_obs[0].subject:
                chosen = item
                break
    correct_text = chosen.sentence.strip()
    evidence_id = view.t1.evidence_id
    evidence_text = view.t1.body
    if gold == "正确":
        return correct_text, evidence_id, evidence_text, ""
    assert operator is not None and sign is not None
    plus = sign == "plus"
    if operator == 0:
        after = _flip_obligation(correct_text, plus)
        _reject_if_same(after, correct_text, evidence_id, evidence_id)
        return after, evidence_id, evidence_text, ""
    if operator == 1:
        subjects = _subjects(view)
        others = [name for name in subjects if name and name != chosen.subject]
        if not others:
            raise ConstructError("没有另一个主体", structural=False)
        after = correct_text.replace(chosen.subject, others[0], 1)
        _reject_if_same(after, correct_text, evidence_id, evidence_id)
        return after, evidence_id, evidence_text, ""
    if operator == 2:
        sentences = _doc_obligations(view)
        others = [item.sentence.strip() for item in sentences if item.sentence.strip() != correct_text]
        if not others:
            raise ConstructError("没有另一条条款", structural=False)
        return others[0], evidence_id, evidence_text, ""
    nxt = _next_chunk(view)
    if nxt is None:
        raise ConstructError("没有下一块", structural=False)
    if correct_text and correct_text in nxt.body:
        raise ConstructError("下一块仍含该条款", structural=False)
    return correct_text, nxt.evidence_id, nxt.body, ""


def _deletion(
    view: ClaimView,
    gold: str,
    operator: int | None,
    sign: str | None,
) -> tuple[str, str, str, str]:
    del sign
    assert view.t1 is not None
    abolished = _matching_quals(view.statement, view.t1.body, abolish=True)
    if not abolished:
        raise ConstructError("没有可删除的废止限定", structural=True)
    target = max(abolished, key=len)
    correct_text = _remove_span(view.statement, target)
    evidence_id = view.t1.evidence_id
    evidence_text = view.t1.body
    if gold == "正确":
        return correct_text, evidence_id, evidence_text, ""
    assert operator is not None
    if operator == 0:
        affirmed = _matching_quals(view.statement, view.t1.body, abolish=False)
        options = [span for span in affirmed if _remove_span(view.statement, span) != correct_text]
        if not options:
            if not affirmed:
                raise ConstructError("没有 T1 仍然肯定的限定", structural=False)
            raise ConstructError("扰动结果与正确值相同", structural=False)
        span = max(options, key=len)
        after = _remove_span(view.statement, span)
        return after, evidence_id, evidence_text, ""
    if operator == 1:
        span = _exception_or_threshold(view.statement)
        if span is None:
            raise ConstructError("没有可删的例外或阈值", structural=False)
        if _span_abolished(span, view.t1.body):
            raise ConstructError("证据支持该删除", structural=False)
        after = _remove_span(view.statement, span)
        _reject_if_same(after, correct_text, evidence_id, evidence_id)
        return after, evidence_id, evidence_text, ""
    if operator == 2:
        return correct_text, "", "", ""
    modifier = next((word for word in _MODIFIERS if word in view.statement), None)
    if modifier is None:
        raise ConstructError("没有不改变事实的修饰", structural=False)
    after = _remove_span(view.statement, modifier)
    _reject_if_same(after, correct_text, evidence_id, evidence_id)
    return after, evidence_id, evidence_text, "按新证据必须更新"


def _pair_number(
    claim_nums: list[_NumTok], chunk_nums: list[_NumTok]
) -> tuple[_NumTok, _NumTok] | None:
    for claim_tok in claim_nums:
        for chunk_tok in chunk_nums:
            if claim_tok.unit == chunk_tok.unit:
                return claim_tok, chunk_tok
    return None


def _find_numbers(text: str) -> list[_NumTok]:
    found: list[_NumTok] = []
    for match in _NUM_RE.finditer(text):
        raw = match.group(1)
        found.append(
            _NumTok(
                start=match.start(),
                end=match.end(),
                value=Decimal(raw),
                unit=match.group(2),
                integer="." not in raw,
            )
        )
    return found


def _format_number(value: Decimal, integer: bool) -> str:
    if integer:
        return str(int(value))
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _join_number_unit(number: str, unit: str, original: str) -> str:
    spaced = bool(re.search(r"\d\s+\S", original))
    return f"{number} {unit}" if spaced else f"{number}{unit}"


def _replace_span(text: str, start: int, end: int, repl: str) -> str:
    return text[:start] + repl + text[end:]


def _find_dates(text: str) -> list[_DateTok]:
    found: list[_DateTok] = []
    for match in _DATE_RE.finditer(text):
        day = int(match.group(3)) if match.group(3) else None
        found.append(
            _DateTok(
                start=match.start(),
                end=match.end(),
                year=int(match.group(1)),
                month=int(match.group(2)),
                day=day,
                raw=match.group(0),
            )
        )
    return found


def _format_date(year: int, month: int, day: int | None) -> str:
    if day is None:
        return f"{year} 年 {month} 月"
    return f"{year} 年 {month} 月 {day} 日"


def _other_dates(view: ClaimView, correct: _DateTok) -> list[tuple[int, int, int]]:
    found: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    correct_key = (correct.year, correct.month, correct.day or 0)
    for chunk in view.t1_chunks:
        for tok in _find_dates(chunk.body):
            key = (tok.year, tok.month, tok.day or 0)
            if key == correct_key or key in seen:
                continue
            seen.add(key)
            found.append(key)
    return found


def _days_in_month(year: int, month: int) -> int:
    if month in {1, 3, 5, 7, 8, 10, 12}:
        return 31
    if month in {4, 6, 9, 11}:
        return 30
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    return 29 if leap else 28


def _obligations(text: str) -> list[_Obligation]:
    found: list[_Obligation] = []
    for match in _OB_RE.finditer(text):
        subject = match.group(1).strip(" ，,;；")
        sentence = match.group(0).strip()
        found.append(_Obligation(subject=subject, marker=match.group(2), sentence=sentence))
    return found


def _doc_obligations(view: ClaimView) -> list[_Obligation]:
    found: list[_Obligation] = []
    for chunk in view.t1_chunks:
        found.extend(_obligations(chunk.body))
    return found


def _subjects(view: ClaimView) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for item in _doc_obligations(view):
        if item.subject and item.subject not in seen:
            seen.add(item.subject)
            names.append(item.subject)
    return names


def _flip_obligation(text: str, plus: bool) -> str:
    if "应当" in text or "不得" in text:
        swapped = text.replace("应当", "\0").replace("不得", "应当").replace("\0", "不得")
        if swapped == text:
            raise ConstructError("文本没有变化", structural=False)
        return swapped
    verb = next((word for word in _VERBS if word in text), None)
    if verb is None:
        raise ConstructError("文本没有变化", structural=False)
    negated = f"不{verb}"
    if plus:
        if negated in text:
            raise ConstructError("文本没有变化", structural=False)
        return text.replace(verb, negated, 1)
    if negated not in text:
        raise ConstructError("文本没有变化", structural=False)
    return text.replace(negated, verb, 1)


def _next_chunk(view: ClaimView) -> ChunkRef | None:
    if view.t1 is None:
        return None
    anchors = [chunk.anchor for chunk in view.t1_chunks]
    if view.anchor not in anchors:
        return None
    index = anchors.index(view.anchor)
    if index + 1 >= len(view.t1_chunks):
        return None
    return view.t1_chunks[index + 1]


def _qualifier_spans(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for pattern in _QUAL_RES:
        for match in pattern.finditer(text):
            span = match.group(0).strip()
            if span and span not in seen:
                seen.add(span)
                found.append(span)
    return found


def _matching_quals(statement: str, evidence: str, *, abolish: bool) -> list[str]:
    matched: list[str] = []
    for span in _qualifier_spans(statement):
        if abolish and _span_abolished(span, evidence):
            matched.append(span)
        if not abolish and _span_affirmed(span, evidence):
            matched.append(span)
    return matched


def _sentences(text: str) -> list[str]:
    return [part for part in re.split(r"[。\n]", text) if part]


def _span_abolished(span: str, evidence: str) -> bool:
    for sentence in _sentences(evidence):
        if span in sentence and any(marker in sentence for marker in _ABOLISH):
            return True
    return False


def _span_affirmed(span: str, evidence: str) -> bool:
    for sentence in _sentences(evidence):
        if span not in sentence:
            continue
        if any(marker in sentence for marker in _ABOLISH):
            continue
        if any(marker in sentence for marker in _AFFIRM):
            return True
    return False


def _exception_or_threshold(text: str) -> str | None:
    match = re.search(r"除[^，。；\n]{1,30}外", text)
    if match:
        return match.group(0)
    for pattern in _QUAL_RES[2:]:
        found = pattern.search(text)
        if found:
            return found.group(0).strip()
    return None


def _remove_span(text: str, span: str) -> str:
    updated = text.replace(span, "", 1)
    updated = re.sub(r"，{2,}", "，", updated)
    updated = re.sub(r"^[，\s]+|[，\s]+$", "", updated)
    return updated


def _reject_if_same(after: str, correct: str, evidence_id: str, correct_evidence_id: str) -> None:
    if after == correct and evidence_id == correct_evidence_id:
        raise ConstructError("扰动结果与正确值相同", structural=False)


def _chunk_index(corpus_root: Path) -> dict[tuple[str, str, str], list[ChunkRef]]:
    index: dict[tuple[str, str, str], list[ChunkRef]] = {}
    root = Path(corpus_root)
    for as_of, folder in (("T0", "t0"), ("T1", "t1")):
        directory = root / folder
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            _doc, chunks = parse_document(path)
            refs: list[ChunkRef] = []
            for chunk in chunks:
                if chunk.as_of != as_of:
                    continue
                refs.append(
                    ChunkRef(
                        anchor=chunk.clause_id,
                        evidence_id=f"{chunk.doc_id}#{chunk.clause_id}@{as_of}",
                        body=_chunk_body(chunk.text, chunk.clause_id),
                    )
                )
            if not refs:
                continue
            index[(refs[0].evidence_id.split("#", 1)[0], as_of)] = refs
    return index


def _chunk_body(text: str, anchor: str) -> str:
    prefix = f"## {anchor}"
    stripped = text.strip()
    if stripped.startswith(prefix):
        return stripped[len(prefix):].strip()
    return stripped


def _view_from_row(row: Mapping[str, Any], index: Mapping[tuple[str, str], Iterable[ChunkRef]]) -> ClaimView:
    claim_id = str(row.get("claim_id", ""))
    statement = str(row.get("statement", ""))
    raw_ids = row.get("t0_evidence_ids") or []
    doc_id, anchor = _split_evidence(str(raw_ids[0]) if raw_ids else "")
    t1_chunks = tuple(index.get((doc_id, "T1"), ()))
    t0_chunks = tuple(index.get((doc_id, "T0"), ()))
    return ClaimView(
        claim_id=claim_id,
        statement=statement,
        doc_id=doc_id,
        anchor=anchor,
        t1=_find_anchor(t1_chunks, anchor),
        t0=_find_anchor(t0_chunks, anchor),
        t1_chunks=t1_chunks,
        t0_chunks=t0_chunks,
    )


def _split_evidence(raw: str) -> tuple[str, str]:
    body = raw.split("@", 1)[0]
    if "#" not in body:
        return body, ""
    doc_id, anchor = body.rsplit("#", 1)
    return doc_id, anchor


def _find_anchor(chunks: tuple[ChunkRef, ...], anchor: str) -> ChunkRef | None:
    for chunk in chunks:
        if chunk.anchor == anchor:
            return chunk
    return None
