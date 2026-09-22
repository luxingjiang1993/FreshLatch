"""假绿对照单测(§4.2,gate 1,零 LLM):JSON mode 契约机械解析 + prompt 红线机器盯死。

红线盯两层:模板常量本身 + **format 后的实际发送内容**(claim.statement 与 T0 摘录
若含「T1/金标」类词即泄题——「泄一句对照即废」,只盯模板不够)。
仪器 C 另测 CONTROL_PROMPT_C(禁蕴涵问法回潮;旁句与时间框锁定)。
"""

import json
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from freshlatch.eval.control import (
    CONTROL_C_T0_EVIDENCE_IDS,
    CONTROL_PROMPT,
    CONTROL_PROMPT_C,
    ControlCMissingChunkError,
    _build_c_excerpt,
    _parse_verdict,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCKET = json.loads((REPO_ROOT / "data" / "t0_docket.json").read_text(encoding="utf-8"))
DISTRACTOR = json.loads(
    (REPO_ROOT / "data" / "eval" / "distractor_docket.json").read_text(encoding="utf-8")
)

LEAK_TOKENS = ("T1", "快照", "金标", "gold", "must_stale", "复验")
# 蕴涵问法禁句(决议 #77 / 预登记 C):出现即对照构念作废
IMPLICATION_BANS = (
    "仅根据材料是否成立",
    "仅根据以上给定材料",
    "只依据给定材料",
    "不要引入材料之外",
)
JSON_OBJECT = re.compile(r"\{[^{}]*\"verdict\"[^{}]*\}")

# 预登记锁定旁句与时间框字面
C_SIDE_SENTENCE = "若缺少签发之后的更新材料,不要因此默认 unknown。"
C_TIMEFRAME = "数周前签发"
C_JUDGMENT = "现在是否仍然成立"


def _t0_excerpt(doc_id: str, limit: int = 2000) -> str:
    path = REPO_ROOT / "data" / "corpus" / "t0" / f"{doc_id}.md"
    return path.read_text(encoding="utf-8")[:limit]


def _assert_no_leak(text: str, where: str) -> None:
    hits = [tok for tok in LEAK_TOKENS if tok in text]
    assert not hits, f"{where} 泄题: {hits}"


def _assert_no_implication(text: str, where: str) -> None:
    hits = [ban for ban in IMPLICATION_BANS if ban in text]
    assert not hits, f"{where} 蕴涵问法禁句回潮: {hits}"


def test_control_prompt_template_redline():
    _assert_no_leak(CONTROL_PROMPT, "对照 prompt 模板")
    # 模板必须是合法 format 模板(双写花括号已正确转义)
    CONTROL_PROMPT.format(statement="s", t0_excerpt="e")


def test_control_prompt_redline_after_format():
    """format 后全文逐条扫:docket 主张 + 真实 T0 语料进模板,不得出现泄题词。"""
    for claim in DOCKET["claims"]:
        excerpt_parts = []
        for eid in claim.get("t0_evidence_ids", []):
            doc_id = eid.split("#", 1)[0]
            excerpt_parts.append(_t0_excerpt(doc_id))
        excerpt = "\n\n".join(excerpt_parts)
        formatted = CONTROL_PROMPT.format(statement=claim["statement"], t0_excerpt=excerpt)
        _assert_no_leak(formatted, f"format 后 prompt({claim['claim_id']})")


def test_control_prompt_c_template_redline_and_locks():
    """C 模板:无泄题、无蕴涵禁句;旁句与时间框/判断句逐字在场。"""
    _assert_no_leak(CONTROL_PROMPT_C, "对照 C prompt 模板")
    _assert_no_implication(CONTROL_PROMPT_C, "对照 C prompt 模板")
    assert C_SIDE_SENTENCE in CONTROL_PROMPT_C
    assert C_TIMEFRAME in CONTROL_PROMPT_C
    assert C_JUDGMENT in CONTROL_PROMPT_C
    CONTROL_PROMPT_C.format(statement="s", t0_excerpt="e")


def test_control_prompt_c_redline_after_format():
    """C:format 后扫泄题 + 蕴涵禁句(金标 12 + 干扰项)。"""
    all_claims = list(DOCKET["claims"]) + list(DISTRACTOR["claims"])
    for claim in all_claims:
        cid = claim["claim_id"]
        locked = CONTROL_C_T0_EVIDENCE_IDS[cid]
        excerpt_parts = []
        for eid in locked:
            doc_id = eid.split("#", 1)[0]
            excerpt_parts.append(_t0_excerpt(doc_id))
        excerpt = "\n\n".join(excerpt_parts)
        formatted = CONTROL_PROMPT_C.format(statement=claim["statement"], t0_excerpt=excerpt)
        _assert_no_leak(formatted, f"C format 后 prompt({cid})")
        _assert_no_implication(formatted, f"C format 后 prompt({cid})")


def test_control_c_multi_anchor_table_covers_all_claims():
    """多锚表覆盖金标 12 + 干扰项 c13/c14;每条恰 p1+p2+p3 源序。"""
    expected_ids = {c["claim_id"] for c in DOCKET["claims"]} | {"c13", "c14"}
    assert set(CONTROL_C_T0_EVIDENCE_IDS) == expected_ids
    for cid, ids in CONTROL_C_T0_EVIDENCE_IDS.items():
        assert len(ids) == 3, cid
        assert ids[0].endswith("#p1") and ids[1].endswith("#p2") and ids[2].endswith("#p3"), cid
        docs = {eid.split("#", 1)[0] for eid in ids}
        assert len(docs) == 1, cid


def test_build_c_excerpt_missing_chunk_raises():
    """缺 chunk 不得静默少拼 → ControlCMissingChunkError。"""
    store = MagicMock()
    store.get_chunk.return_value = None
    with pytest.raises(ControlCMissingChunkError, match="缺 chunk"):
        _build_c_excerpt(store, "c1")


def test_control_verdict_parse():
    assert _parse_verdict('{"verdict": "alive"}') == "alive"
    assert _parse_verdict('前言 {"verdict": "dead"} 后记') == "dead"
    assert _parse_verdict("成立") == "unparseable"
    assert _parse_verdict('{"verdict": "yes"}') == "unparseable"
    assert _parse_verdict("") == "unparseable"


def test_verdict_pattern_extracts_json_object():
    assert JSON_OBJECT.search('x {"verdict": "alive"} y').group(0) == '{"verdict": "alive"}'
