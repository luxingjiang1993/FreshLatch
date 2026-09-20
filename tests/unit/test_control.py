"""假绿对照单测(§4.2,gate 1,零 LLM):JSON mode 契约机械解析 + prompt 红线机器盯死。

红线盯两层:模板常量本身 + **format 后的实际发送内容**(claim.statement 与 T0 摘录
若含「T1/金标」类词即泄题——「泄一句对照即废」,只盯模板不够)。
"""

import json
import re
from pathlib import Path

from freshlatch.eval.control import CONTROL_PROMPT, _parse_verdict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCKET = json.loads((REPO_ROOT / "data" / "t0_docket.json").read_text(encoding="utf-8"))

LEAK_TOKENS = ("T1", "快照", "金标", "gold", "must_stale", "复验")
JSON_OBJECT = re.compile(r"\{[^{}]*\"verdict\"[^{}]*\}")


def _t0_excerpt(doc_id: str, limit: int = 2000) -> str:
    path = REPO_ROOT / "data" / "corpus" / "t0" / f"{doc_id}.md"
    return path.read_text(encoding="utf-8")[:limit]


def _assert_no_leak(text: str, where: str) -> None:
    hits = [tok for tok in LEAK_TOKENS if tok in text]
    assert not hits, f"{where} 泄题: {hits}"


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


def test_control_verdict_parse():
    assert _parse_verdict('{"verdict": "alive"}') == "alive"
    assert _parse_verdict('前言 {"verdict": "dead"} 后记') == "dead"
    assert _parse_verdict("成立") == "unparseable"
    assert _parse_verdict('{"verdict": "yes"}') == "unparseable"
    assert _parse_verdict("") == "unparseable"


def test_verdict_pattern_extracts_json_object():
    assert JSON_OBJECT.search('x {"verdict": "alive"} y').group(0) == '{"verdict": "alive"}'
