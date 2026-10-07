"""#351:抽取 cost_note 与 claim_id 去重后，报告字节与抽取前相同。"""

import json
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_ablation import run_ablations
from freshlatch.eval.patch_events_arms import Decoding, run_arms
from freshlatch.eval.patch_events_metrics import SEED
from freshlatch.eval.patch_events_repro import (
    _fake_generator,
    _fake_verifier,
    _ingested,
    _load_candidates,
    _repo_root,
    build_report,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "patch_events" / "chk11"


def _canon(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _records() -> str:
    root = _repo_root()
    candidates = _load_candidates(root)
    ingested = _ingested(candidates)
    decoding = Decoding(temperature=0, seed=SEED)
    common = dict(
        generator=_fake_generator,
        verifier=_fake_verifier,
        decoding=decoding,
        ingested_t1=ingested,
    )
    payload = {
        "arms": _canon(run_arms(candidates, **common)),
        "ablations": _canon(run_ablations(candidates, **common)),
    }
    return _canon(payload) + "\n"


def _paid_notes() -> str:
    def paid(request):
        produced = dict(_fake_generator(request))
        produced["cost"] = 2
        return produced

    one = [
        {
            "claim_id": "paid-1",
            "edit_type": "数值",
            "arm": "T",
            "ablation": "",
            "construction_gold": "正确",
            "before_text": "修改前",
            "after_text": "构造后",
            "evidence_id": "doc#p1@T1",
            "evidence_text": "证据",
        }
    ]
    common = dict(
        generator=paid,
        verifier=_fake_verifier,
        decoding=Decoding(temperature=0, seed=SEED),
        ingested_t1={"doc#p1@T1"},
    )
    payload = {
        "arms": run_arms(one, **common)["cost_notes"],
        "ablations": run_ablations(one, **common)["cost_notes"],
    }
    return _canon(payload) + "\n"


def test_report_bytes_match_the_pre_extract_freeze():
    assert build_report(_repo_root()) == (FIXTURE / "dry-run.txt").read_text(encoding="utf-8")
    assert _records() == (FIXTURE / "records.json").read_text(encoding="utf-8")
    assert _paid_notes() == (FIXTURE / "paid-cost-notes.json").read_text(encoding="utf-8")


def test_duplicate_claim_id_message_stays():
    candidate = {
        "claim_id": "dup",
        "edit_type": "数值",
        "before_text": "前",
        "after_text": "后",
        "evidence_id": "doc#p1@T1",
        "evidence_text": "证据",
    }
    decoding = Decoding(temperature=0, seed=SEED)
    with pytest.raises(ValueError, match="claim_id 重复: dup"):
        run_arms(
            [candidate, dict(candidate)],
            generator=_fake_generator,
            verifier=_fake_verifier,
            decoding=decoding,
        )
    with pytest.raises(ValueError, match="claim_id 重复: dup"):
        run_ablations(
            [candidate, dict(candidate)],
            generator=_fake_generator,
            verifier=_fake_verifier,
            decoding=decoding,
        )


def test_cost_note_and_dedup_have_one_definition():
    shared = (ROOT / "src/freshlatch/eval/patch_events_rows.py").read_text(encoding="utf-8")
    arms = (ROOT / "src/freshlatch/eval/patch_events_arms.py").read_text(encoding="utf-8")
    ablation = (ROOT / "src/freshlatch/eval/patch_events_ablation.py").read_text(encoding="utf-8")
    assert "def cost_note" in shared
    assert "claim_id 重复" in shared
    assert "random" not in shared
    assert "named_streams" not in shared
    assert "def _cost_note" not in arms
    assert "def _cost_note" not in ablation
    assert "claim_id 重复" not in arms
    assert "claim_id 重复" not in ablation
