"""主张句与 T1 句 id 的绑定。纯函数,零 I/O。

偏移方案只认句 id:块内从 s0 起编号。不写字符偏移。
支撑句必须与主张句去空白后逐字相同。对不上不挂支撑,避免把相关块涂成支撑。
"""

from __future__ import annotations

import re
from typing import Any

# 本票钉死的方案名。其它方案(字符偏移)不投影。
SENTENCE_SCHEME = "sentence_id"
_HEADING_RE = re.compile(r"##\s+p\d+\s*")
_SENTENCE_ID_RE = re.compile(r"^s\d+$")
_WS_RE = re.compile(r"\s+")


def strip_clause_heading(text: str) -> str:
    """去掉块首 `## pN` 标题行。标题不是句子。"""
    lines = text.splitlines()
    if lines and _HEADING_RE.fullmatch(lines[0]):
        return "\n".join(lines[1:]).strip()
    return text.strip()


def _keep_sentence(sentence: str) -> bool:
    """纯标点不成句,避免把句号单独编成 s0。"""
    for ch in sentence:
        if ch.isalnum() or "\u4e00" <= ch <= "\u9fff":
            return True
    return False


def split_sentences(text: str) -> list[str]:
    """按句末标点切句。序号即句 id,不是字符偏移。

    句末:。！？!? ,以及前面不是数字的英文句点(12.5 不切)。
    块首 `## pN` 不进入句子。换行不另切。
    """
    body = strip_clause_heading(text)
    if not body:
        return []
    sentences: list[str] = []
    buf: list[str] = []
    for index, ch in enumerate(body):
        buf.append(ch)
        ended = ch in "。！？!?"
        if ch == ".":
            prev_digit = index > 0 and body[index - 1].isdigit()
            next_boundary = index + 1 == len(body) or body[index + 1].isspace()
            ended = (not prev_digit) and next_boundary
        if not ended:
            continue
        sentence = "".join(buf).strip()
        buf = []
        if sentence and _keep_sentence(sentence):
            sentences.append(sentence)
    tail = "".join(buf).strip()
    if tail and _keep_sentence(tail):
        sentences.append(tail)
    return sentences


def sentence_id_for(index: int) -> str:
    """0 起的句 id。"""
    return f"s{index}"


def span_anchor(evidence_id: str, sentence_id: str) -> str:
    """可见锚:`evidence_id#sentence_id`,例如 fix-memo#p1@T1#s0。"""
    return f"{evidence_id}#{sentence_id}"


def _norm(text: str) -> str:
    return _WS_RE.sub("", text)


def _t1_ids(evidence_ids: list[str]) -> list[str]:
    seen: list[str] = []
    for evidence_id in evidence_ids:
        if not isinstance(evidence_id, str) or not evidence_id.endswith("@T1"):
            continue
        if evidence_id not in seen:
            seen.append(evidence_id)
    return seen


def _span_row(role: str, evidence_id: str, sentence_id: str, text: str) -> dict[str, str]:
    return {
        "role": role,
        "evidence_id": evidence_id,
        "sentence_id": sentence_id,
        "anchor": span_anchor(evidence_id, sentence_id),
        "text": text,
    }


def _verbatim_support(
    claim_text: str,
    evidence_ids: list[str],
    blocks: dict[str, str],
) -> list[dict[str, str]]:
    """主张句与所引 @T1 块中某一句去空白后逐字相同才算支撑。"""
    claim_norms = {_norm(sentence) for sentence in split_sentences(claim_text)}
    if not claim_norms:
        return []
    support: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for evidence_id in _t1_ids(evidence_ids):
        raw = blocks.get(evidence_id)
        if not isinstance(raw, str):
            continue
        for index, sentence in enumerate(split_sentences(raw)):
            if _norm(sentence) not in claim_norms:
                continue
            sentence_id = sentence_id_for(index)
            key = (evidence_id, sentence_id)
            if key in seen:
                continue
            seen.add(key)
            support.append(_span_row("support", evidence_id, sentence_id, sentence))
    return support


def _single_sentence_oppose(
    evidence_ids: list[str],
    blocks: dict[str, str],
    support: list[dict[str, str]],
) -> list[dict[str, str]]:
    """stale 且所引块恰好一句、又不是支撑句时,这一句是反对句。

    多句块不挑选,避免把相邻句涂成反对。
    """
    support_keys = {(row["evidence_id"], row["sentence_id"]) for row in support}
    oppose: list[dict[str, str]] = []
    for evidence_id in _t1_ids(evidence_ids):
        raw = blocks.get(evidence_id)
        if not isinstance(raw, str):
            continue
        sentences = split_sentences(raw)
        if len(sentences) != 1:
            continue
        sentence_id = sentence_id_for(0)
        if (evidence_id, sentence_id) in support_keys:
            continue
        oppose.append(_span_row("oppose", evidence_id, sentence_id, sentences[0]))
    return oppose


def build_claim_span_event(
    *,
    claim_id: str,
    claim_text: str,
    status: str,
    evidence_ids: list[str],
    blocks: dict[str, str],
) -> dict[str, Any]:
    """与 cite_registry_judgment 同一次判定写出的句锚事件。

    不改 cite 事件的字段。支撑为空则 unsupported 为真。
    """
    support = _verbatim_support(claim_text, evidence_ids, blocks)
    oppose: list[dict[str, str]] = []
    if status == "stale":
        oppose = _single_sentence_oppose(evidence_ids, blocks, support)
    return {
        "type": "claim_span",
        "claim_id": claim_id,
        "claim_text": claim_text,
        "status": status,
        "sentence_scheme": SENTENCE_SCHEME,
        "unsupported": not support,
        "support": support,
        "oppose": oppose,
    }


def _valid_span(raw: object, role: str) -> dict[str, str] | None:
    """只收句 id 形状。缺句 id 或不是 @T1 的条目丢掉,不另编锚。"""
    if not isinstance(raw, dict):
        return None
    evidence_id = raw.get("evidence_id")
    sentence_id = raw.get("sentence_id")
    text = raw.get("text")
    if not isinstance(evidence_id, str) or not evidence_id.endswith("@T1"):
        return None
    if not isinstance(sentence_id, str) or _SENTENCE_ID_RE.fullmatch(sentence_id) is None:
        return None
    if not isinstance(text, str) or not text.strip():
        return None
    return _span_row(role, evidence_id, sentence_id, text)


def project_claim_spans(events: list[dict]) -> list[dict[str, Any]]:
    """从轨迹读回主张句锚。字符偏移方案整条丢弃。

    unsupported 为真时丢掉支撑列表,页面不得画出支撑高亮。
    同一锚同时出现在两边时,留在支撑,反对侧去掉。
    """
    cards: list[dict[str, Any]] = []
    for event in events:
        if event.get("type") != "claim_span":
            continue
        scheme = event.get("sentence_scheme", SENTENCE_SCHEME)
        if scheme != SENTENCE_SCHEME:
            continue
        claim_id = event.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            continue
        claim_text = event.get("claim_text")
        if not isinstance(claim_text, str):
            claim_text = ""
        support = [
            row
            for item in (event.get("support") or [])
            if (row := _valid_span(item, "support")) is not None
        ]
        oppose = [
            row
            for item in (event.get("oppose") or [])
            if (row := _valid_span(item, "oppose")) is not None
        ]
        unsupported = event.get("unsupported") is True or not support
        if unsupported:
            support = []
        support_keys = {(row["evidence_id"], row["sentence_id"]) for row in support}
        oppose = [
            row
            for row in oppose
            if (row["evidence_id"], row["sentence_id"]) not in support_keys
        ]
        cards.append({
            "claim_id": claim_id,
            "claim_text": claim_text,
            "unsupported": unsupported,
            "support": support,
            "oppose": oppose,
        })
    return cards
