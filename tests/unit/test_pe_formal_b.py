"""路线 B 正式入口：激活守卫、旁路路径、n=100、同 after 发送、判定分层。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_formal_b import (
    formal_b_requests,
    load_pe_v2_formal_n100,
    outcome_tier,
    prereg_b_activated,
    render_result_b,
    send_formal_b,
    verdict_sentence,
)
from freshlatch.eval.patch_events_formal import generations_path


def test_prereg_b_activated_on_current_tree():
    assert prereg_b_activated() is True


def test_n100_loader_excludes_pilot():
    rows = load_pe_v2_formal_n100()
    assert len(rows) == 100
    ids = [r["claim_id"] for r in rows]
    assert len(set(ids)) == 100
    payload = json.loads(
        Path("docs/evidence/patch-events/SPLIT-pe-v2.json").read_text(encoding="utf-8")
    )
    pilot = {str(r["claim_id"]) for r in payload["pilot"]}
    assert set(ids).isdisjoint(pilot)
    assert ids == [str(r["claim_id"]) for r in payload["n100"]]


def test_formal_b_requests_skip_b1_rewrite():
    rows = load_pe_v2_formal_n100()[:2]
    reqs = formal_b_requests(rows)
    assert ("B1", "rewrite") not in {(r["arm"], r["phase"]) for r in reqs}
    assert ("T", "rewrite") in {(r["arm"], r["phase"]) for r in reqs}


def test_send_refuses_legacy_formal_path(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_formal_b.generations_b_path",
        lambda root=None: generations_path(),
    )
    with pytest.raises(RuntimeError, match="formal-generations"):
        send_formal_b(chat=lambda *a, **k: "x")


def test_outcome_tier_jia_yi_bing():
    def _cmp(name: str, established: bool, point: float = 0.1, low: float = 0.01):
        return {
            "name": name,
            "point": point,
            "ci95_low": low,
            "ci95_high": 0.5,
            "established": established,
        }

    jia = {
        "k": 12,
        "comparisons": [
            _cmp("T-C", True),
            _cmp("T-B1", True),
            _cmp("T-B2", True),
        ],
    }
    yi = {
        "k": 12,
        "comparisons": [
            _cmp("T-C", True),
            _cmp("T-B1", False, point=0.0, low=0.0),
            _cmp("T-B2", True),
        ],
    }
    bing = {
        "k": 12,
        "comparisons": [
            _cmp("T-C", False, point=-0.1, low=-0.2),
            _cmp("T-B1", True),
            _cmp("T-B2", True),
        ],
    }
    assert outcome_tier(jia) == "甲"
    assert outcome_tier(yi) == "乙"
    assert outcome_tier(bing) == "丙"
    assert "结果甲" in verdict_sentence("甲", jia)
    assert "不得称甲" in verdict_sentence("乙", yi)
    assert "结果丙" in verdict_sentence("丙", bing)


def test_result_b_refuses_fill_when_b2_short():
    md = render_result_b(
        {
            "primary": {
                "k": 11,
                "comparisons": [
                    {
                        "name": "T-C",
                        "point": 0.1,
                        "ci95_low": 0.01,
                        "ci95_high": 0.2,
                        "established": True,
                    },
                    {
                        "name": "T-B1",
                        "point": 0.1,
                        "ci95_low": 0.01,
                        "ci95_high": 0.2,
                        "established": True,
                    },
                    {
                        "name": "T-B2",
                        "point": 0.1,
                        "ci95_low": 0.01,
                        "ci95_high": 0.2,
                        "established": True,
                    },
                ],
            },
            "b2_count": 30,
            "n": 100,
            "tier": "甲",
            "verdict": "判定：结果甲。",
            "generations_n": 10,
            "generations_sha256": "x",
            "decoding": {
                "model": "qwen-flash",
                "temperature": 0,
                "decoding_seed": 20261007,
                "api_seed": None,
            },
        },
        code_pin="t",
        activated_note="t",
    )
    assert "未填" in md
    assert "成立" not in md.split("主比较")[1].split("甲 / 乙 / 丙")[0] or "未填" in md
