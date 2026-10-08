"""自动核验只锁已写明的逐字比较。score 为空。"""

from __future__ import annotations

from freshlatch.eval.patch_events_verify import verify_edit


def _request(after_text: str, evidence_text: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "arm": "T",
        "claim_id": "c-lock",
        "after_text": after_text,
        "evidence_id": "doc#anchor@T1",
        "evidence_text": evidence_text,
    }
    payload.update(extra)
    return payload


def test_identical_text_passes_and_score_stays_empty():
    verdict = verify_edit(_request("甲乙丙", "甲乙丙"))
    assert verdict == {"ok": True, "score": None, "reason": "一致"}


def test_different_text_fails_and_score_stays_empty():
    verdict = verify_edit(_request("甲乙丙", "甲乙丁"))
    assert verdict == {"ok": False, "score": None, "reason": "核验不过"}


def test_only_outer_whitespace_still_passes():
    verdict = verify_edit(_request(" \n\t甲乙丙\t \n", "甲乙丙"))
    assert verdict == {"ok": True, "score": None, "reason": "一致"}


def test_evidence_text_whitespace_is_not_stripped():
    verdict = verify_edit(_request("甲乙丙", " 甲乙丙 "))
    assert verdict["ok"] is False
    assert verdict["score"] is None


def test_arm_claim_and_evidence_id_do_not_change_the_comparison():
    same = verify_edit(_request("甲乙丙", "甲乙丙", arm="B1", claim_id="other", evidence_id=""))
    assert same["ok"] is True
    assert same["score"] is None
    ignored = verify_edit(_request("甲乙丙", "甲乙丙", ablation="soft_warning", ledger="hybrid+rerank"))
    assert ignored == same
