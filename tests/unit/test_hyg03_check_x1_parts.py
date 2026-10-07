"""HYG-03：check_x1 拆成可测纯函数。既有消息断言留在 test_x1_checks。"""

import inspect
from pathlib import Path

from freshlatch.eval.x1_checks import (
    LOCKED_CONFIG,
    check_x1,
    check_x1_question,
    scan_x1_corpus,
    summarize_x1,
    validate_x1_config,
)
from tests.unit.test_x1_checks import SMALL_FLOORS, _ok_body, _write_doc


def test_check_x1_signature_stays_frozen():
    sig = inspect.signature(check_x1)
    assert list(sig.parameters) == [
        "corpus_dir",
        "traps_dir",
        "questions",
        "config",
        "floor_overrides",
    ]
    floor = sig.parameters["floor_overrides"]
    assert floor.kind is inspect.Parameter.KEYWORD_ONLY
    assert floor.default is None


def test_validate_x1_config_missing_or_null_does_not_fill_threshold():
    missing = validate_x1_config(dict(LOCKED_CONFIG), None)
    assert missing.threshold_unlocked is True
    assert missing.decontam_max is None
    assert "decontam_8gram_max 缺键或为 null，不代入阈值" in missing.messages

    null_cfg = dict(LOCKED_CONFIG)
    null_cfg["decontam_8gram_max"] = None
    null = validate_x1_config(null_cfg, None)
    assert null.threshold_unlocked is True
    assert null.decontam_max is None
    assert "decontam_8gram_max 缺键或为 null，不代入阈值" in null.messages


def test_scan_x1_corpus_bad_license_message(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(
        corpus,
        "t1",
        "T1",
        "doc-a",
        _ok_body("无污染叙述十二字以上。"),
        license="not-a-license",
        provenance="public",
    )
    scanned = scan_x1_corpus(corpus, traps, SMALL_FLOORS)
    assert scanned.license_violations == 1
    assert "许可违规 chunk=1" in scanned.messages


def test_check_x1_question_empty_arm_relevant_message():
    item = {
        "id": "a-empty",
        "query": "臂对比题十二字以上",
        "qtype": "paraphrase",
        "category": "hard",
        "relevant": [],
        "distractors": [],
        "eval_intent": "单测",
        "as_of": "T1",
        "score_role": "arm",
    }
    verdict = check_x1_question(item, chunks=[], by_eid={}, decontam_max=None)
    assert any("a-empty arm 题 relevant 不得为空" == msg for msg in verdict.messages)
    assert verdict.record.startswith("q a-empty ")
    assert "score_role=arm" in verdict.record


def test_summarize_x1_exit_codes_keep_priority():
    unlocked = summarize_x1(
        [],
        floors=SMALL_FLOORS,
        threshold_unlocked=True,
        prior_violation=True,
    )
    assert unlocked.exit_code == 2

    violation = summarize_x1(
        [],
        floors=SMALL_FLOORS,
        threshold_unlocked=False,
        prior_violation=True,
    )
    assert violation.exit_code == 1

    clean = summarize_x1(
        [],
        floors={
            "min_chunks": 0,
            "min_per_qtype": 0,
            "min_trap_adversarial_ratio": 0.0,
            "min_synthetic_ratio": 0.0,
            "max_public_ratio": 1.0,
        },
        threshold_unlocked=False,
        prior_violation=False,
    )
    assert clean.exit_code == 0
