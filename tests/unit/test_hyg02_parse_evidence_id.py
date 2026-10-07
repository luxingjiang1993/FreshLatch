"""HYG-02 预锁解析契约。期望先于实现写入，实现 commit 不得改这些期望。"""

from pathlib import Path

import pytest

from freshlatch.eval.checks import parse_evidence_id as checks_parse
from freshlatch.eval.x1_checks import check_x1
from freshlatch.eval.x1_checks import parse_evidence_id as x1_parse
from freshlatch.evidence_id import parse_evidence_id as canonical
from freshlatch.gates.human_latch import parse_evidence_id as latch_parse

# 五行契约，外加 None / 非 str。禁止事后改期望。
CASES = [
    ("doc-a#p2@T1", ("doc-a", "p2", "T1")),
    ("a#b#c@T1", ("a#b", "c", "T1")),
    ("doc#p2@T2", None),
    ("no-hash@T1", None),
    ("doc#p2", None),
    ("#p2@T1", None),
    ("doc#@T1", None),
    (None, None),
    (123, None),
]


@pytest.mark.parametrize("parse", [canonical, checks_parse, latch_parse, x1_parse])
@pytest.mark.parametrize("eid,expected", CASES)
def test_parse_evidence_id_contract(parse, eid, expected):
    assert parse(eid) == expected


def test_x1_rejects_illegal_as_of_as_empty_doc(tmp_path: Path):
    """``doc#p2@T2`` 得到 None，调用处不把它当成 doc_id。"""
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    for doc_id, body in (
        ("doc-a", "## p1\n只有甲点在这里。\n"),
        ("doc-b", "## p1\n只有乙点在这里。\n"),
    ):
        folder = corpus / "t1"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{doc_id}.md").write_text(
            "\n".join(
                [
                    "---",
                    f"doc_id: {doc_id}",
                    "as_of: T1",
                    "source_type: private",
                    f"title: {doc_id}",
                    "provenance: synthetic",
                    "license: synthetic",
                    "domain: D0",
                    "genre: S1",
                    "---",
                    body,
                ]
            ),
            encoding="utf-8",
        )
    questions = [
        {
            "id": "mh-t2",
            "query": "两跳里有一条非法时点",
            "qtype": "multi_hop",
            "category": "hard",
            "relevant": ["doc-a#p1@T2", "doc-b#p1@T1"],
            "distractors": [],
            "eval_intent": "单测",
            "as_of": "T1",
            "answer_points": ["只有甲点在这里", "只有乙点在这里"],
            "score_role": "arm",
        }
    ]
    result = check_x1(
        corpus,
        traps,
        questions,
        {
            "top_k": 10,
            "rrf_k": 60,
            "embed_model": "text-embedding-v4",
            "embed_dim": 1024,
            "draft_model": "qwen-flash",
            "flag_model": "qwen-plus",
            "flag_thinking": False,
            "decontam_8gram_max": 0.2,
            "lead_delta": 0.10,
            "budget_cny_max": 10,
        },
        floor_overrides={
            "min_chunks": 0,
            "min_per_qtype": 0,
            "min_trap_adversarial_ratio": 0.0,
            "min_synthetic_ratio": 0.0,
            "max_public_ratio": 1.0,
        },
    )
    assert any("须跨至少两个 doc_id" in msg for msg in result.messages)
