"""PE-05 risk-coverage 与配对 bootstrap。

零 LLM、零网络、不读密钥、不改 PREREG。
"""

from __future__ import annotations

import inspect
import random

import pytest

from freshlatch.eval import patch_events_metrics as metrics


def _row(claim_id, arm, gold, decision, score, **overrides):
    base = {
        "claim_id": claim_id,
        "edit_type": "数值",
        "arm": arm,
        "ablation": "",
        "construction_gold": gold,
        "before_text": "修改前",
        "after_text": "修改后",
        "evidence_id": f"doc#{claim_id}@T1",
        "evidence_text": "证据原文",
        "decision": decision,
        "score": score,
        "latency_ms": 10,
        "cost": 0,
        "reverify_ok": decision == "release",
    }
    base.update(overrides)
    return base


def _quad(claim_id, gold, *, release_scored: bool, score: float | None):
    """四臂同决策（路线 B：C 也走自然放行集 R，不再随机抽 k）。"""
    rows = []
    decision = "release" if release_scored else "reject"
    for arm in ("C", "T", "B1", "B2"):
        rows.append(_row(claim_id, arm, gold, decision, score))
    return rows


def _success_rows():
    """前 10 条坏、后 10 条正确。T/B1 只放行正确；C/B2 全放行 → R 下 T-C 差可识别。"""
    rows = []
    for i in range(20):
        cid = f"c{i:02d}"
        if i < 10:
            gold = "坏"
            for arm in ("C", "T", "B1", "B2"):
                decision = "reject" if arm in ("T", "B1") else "release"
                rows.append(_row(cid, arm, gold, decision, None))
        else:
            gold = "正确"
            for arm in ("C", "T", "B1", "B2"):
                rows.append(_row(cid, arm, gold, "release", None))
    return rows


def _rejected_rows():
    rows = []
    for i, gold in enumerate(("正确", "正确", "坏", "坏")):
        rows.extend(_quad(f"c{i}", gold, release_scored=False, score=0.2))
    return rows


def _one_release_rows():
    """6 条里只有 1 条自然放行。重抽样放行数为 0 的比例约 (5/6)^6 > 5%。"""
    rows = []
    for i in range(6):
        release = i == 0
        rows.extend(
            _quad(
                f"c{i}",
                "坏" if release else "正确",
                release_scored=release,
                score=1.0 if release else 0.0,
            )
        )
    return rows


def test_format_undefined_has_no_zero_and_defined_zero_stays_numeric():
    assert metrics.format_rate(None) == "无定义"
    assert "0" not in metrics.format_rate(None)
    assert "0" in metrics.format_rate(0.0)


def test_zero_releases_are_undefined_not_zero():
    rows = [
        {
            "construction_gold": "坏",
            "decision": "reject",
            "evidence_id": "",
            "reverify_ok": False,
        },
        {
            "construction_gold": "正确",
            "decision": "reject",
            "evidence_id": "doc#a@T1",
            "reverify_ok": True,
        },
    ]
    rates = metrics.natural_rates(rows, ingested_t1={"doc#a@T1"})
    assert rates["放行数"] == 0
    assert rates["放行率"] == 0.0
    assert rates["误放率"] is None
    assert rates["可复验率"] is None
    assert rates["错改率"] == 0.0
    assert rates["误拒率"] == 1.0
    assert metrics.format_rate(rates["误放率"]) == "无定义"
    assert metrics.format_rate(rates["可复验率"]) == "无定义"
    assert "0" not in metrics.format_rate(rates["误放率"])
    assert "0" not in metrics.format_rate(rates["可复验率"])


def test_reverify_needs_parsed_ingested_t1_and_a_record():
    rows = [
        {
            "construction_gold": "坏",
            "decision": "release",
            "evidence_id": "doc#a@T1",
            "reverify_ok": True,
        },
        {
            "construction_gold": "正确",
            "decision": "release",
            "evidence_id": "doc#b@T0",
            "reverify_ok": True,
        },
        {
            "construction_gold": "正确",
            "decision": "release",
            "evidence_id": "nope",
            "reverify_ok": True,
        },
        {
            "construction_gold": "正确",
            "decision": "release",
            "evidence_id": "doc#c@T1",
            "reverify_ok": False,
        },
        {
            "construction_gold": "正确",
            "decision": "reject",
            "evidence_id": "doc#d@T1",
            "reverify_ok": True,
        },
    ]
    rates = metrics.natural_rates(
        rows,
        ingested_t1={"doc#a@T1", "doc#c@T1", "doc#d@T1"},
    )
    assert rates["放行数"] == 4
    assert rates["可复验率"] == 0.25
    assert rates["误放率"] == 0.25


def test_linear_percentile_and_exact_five_percent_drop():
    kept = [1.0] * 9500
    within = metrics.interval_from_draws(kept, dropped=500)
    assert within["defined"] is True
    assert within["low"] == 1.0
    assert within["high"] == 1.0
    assert within["dropped"] == 500
    over = metrics.interval_from_draws([1.0] * 9499, dropped=501)
    assert over["defined"] is False
    assert over["low"] is None
    assert over["high"] is None
    sample = metrics.interval_from_draws([0.0, 10.0, 20.0, 30.0], dropped=0, n_boot=4)
    assert sample["defined"] is True
    assert sample["low"] == 0.7500000000000001
    assert sample["high"] == 29.249999999999996


def test_scored_ties_break_by_claim_id_and_missing_score_ranks_last():
    rows = [
        {"claim_id": "c-b", "score": 0.5},
        {"claim_id": "c-a", "score": None},
        {"claim_id": "c-c", "score": 0.5},
        {"claim_id": "c-d", "score": 0.0},
    ]
    assert metrics.select_scored_positions(rows, 1) == [0]
    assert metrics.select_scored_positions(rows, 2) == [0, 2]
    assert 1 not in metrics.select_scored_positions(rows, 3)


def test_named_streams_are_independent_and_do_not_touch_global_rng():
    before = random.getstate()
    streams = metrics.named_streams()
    assert set(streams) == {"coverage_c", "bootstrap", "bootstrap_ablation", "spotcheck"}
    fresh = random.Random(metrics.SEED).getstate()
    for rng in streams.values():
        assert rng.getstate() == fresh
    streams["coverage_c"].random()
    assert streams["bootstrap"].getstate() == fresh
    assert streams["bootstrap_ablation"].getstate() == fresh
    assert streams["spotcheck"].getstate() == fresh
    assert random.getstate() == before


def test_duplicate_arm_claim_is_rejected_before_streams_move():
    rows = _success_rows()
    duplicate = dict(next(row for row in rows if row["arm"] == "T"))
    rows.append(duplicate)
    streams = metrics.named_streams()
    before = {name: rng.getstate() for name, rng in streams.items()}
    with pytest.raises(ValueError, match=r"\(arm, claim_id\)"):
        metrics.compare_primary(rows, streams=streams)
    for name, rng in streams.items():
        assert rng.getstate() == before[name]


def test_k_zero_primary_comparison_is_not_established(monkeypatch):
    for key in ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    before = random.getstate()
    streams = metrics.named_streams()
    spot = streams["spotcheck"].getstate()
    abl = streams["bootstrap_ablation"].getstate()
    result = metrics.compare_primary(_rejected_rows(), streams=streams)
    assert result["k"] == 0
    first = result["comparisons"][0]
    assert first["name"] == "T-C"
    assert first["point"] is None
    assert first["established"] is False
    assert first["intervals"]["误放率"]["defined"] is False
    assert first["intervals"]["误放率"]["dropped"] == metrics.N_BOOT
    assert first["intervals"]["误放率"]["low"] is None
    arm_t = result["arms"]["T"]
    assert arm_t["fixed"]["误放率"] is None
    assert arm_t["natural"]["误放率"] is None
    assert arm_t["natural"]["可复验率"] is None
    assert arm_t["fixed"]["错改率"] == 0.0
    assert arm_t["cost"] == 0
    assert arm_t["cost_note"] == "没有调用"
    assert metrics.format_rate(arm_t["fixed"]["误放率"]) == "无定义"
    assert "0" not in metrics.format_rate(arm_t["natural"]["误放率"])
    assert all(item["established"] is False for item in result["comparisons"])
    assert streams["spotcheck"].getstate() == spot
    assert streams["bootstrap_ablation"].getstate() == abl
    assert random.getstate() == before


def test_established_iff_point_and_lower_bound_are_positive():
    ingested = {f"doc#c{i:02d}@T1" for i in range(20)}
    first = metrics.compare_primary(_success_rows(), ingested_t1=ingested)
    second = metrics.compare_primary(_success_rows(), ingested_t1=ingested)
    assert first == second
    assert first["k"] == 10
    assert first["arms"]["T"]["fixed"]["selected_claim_ids"] == [f"c{i:02d}" for i in range(10, 20)]
    assert first["arms"]["C"]["fixed"]["selected_claim_ids"] == [f"c{i:02d}" for i in range(10)]

    versus_c = first["comparisons"][0]
    assert versus_c["name"] == "T-C"
    assert versus_c["point"] == 1.0
    assert versus_c["ci95_low"] is not None and versus_c["ci95_low"] > 0
    assert versus_c["intervals"]["误放率"]["dropped"] == 0
    assert versus_c["established"] is True
    assert first["arms"]["T"]["fixed"]["误放率"] == 0.0
    assert first["arms"]["C"]["fixed"]["误放率"] == 1.0
    assert first["arms"]["C"]["natural"]["误放率"] == 0.5

    versus_b1 = first["comparisons"][1]
    assert versus_b1["name"] == "T-B1"
    assert versus_b1["point"] == 0.0
    assert versus_b1["ci95_low"] is not None
    assert versus_b1["ci95_low"] <= 0
    assert versus_b1["established"] is False
    versus_b2 = first["comparisons"][2]
    assert versus_b2["name"] == "T-B2"
    assert versus_b2["point"] == 1.0
    assert versus_b2["established"] is True
    assert first["arms"]["T"]["cost"] == 0
    assert first["arms"]["T"]["cost_note"] == "没有调用"

    changed = _success_rows()
    for row in changed:
        row["latency_ms"] = 999
        row["cost"] = 3
    retimed = metrics.compare_primary(changed, ingested_t1=ingested)
    assert retimed["comparisons"] == first["comparisons"]
    assert retimed["arms"]["T"]["latency_median"] == 999
    assert retimed["arms"]["T"]["cost"] == 60
    assert retimed["arms"]["T"]["cost_note"] == ""


def test_drop_fraction_above_five_percent_undefines_the_interval():
    result = metrics.compare_primary(_one_release_rows())
    assert result["k"] == 1
    assert result["arms"]["T"]["fixed"]["误放率"] == 1.0
    interval = result["comparisons"][0]["intervals"]["误放率"]
    assert interval["dropped"] / metrics.N_BOOT > 0.05
    assert interval["defined"] is False
    assert interval["low"] is None
    assert result["comparisons"][0]["established"] is False
    assert result["comparisons"][0]["point"] is not None


def test_ablation_intervals_use_their_own_stream_and_natural_rules():
    rows = []
    for i in range(4):
        cid = f"c{i}"
        rows.append(_row(cid, "T", "正确", "release", 1.0))
        rows.append(
            _row(
                cid,
                "T",
                "坏",
                "release",
                1.0,
                ablation="no_chunk_bind",
            )
        )
        rows.append(
            _row(
                cid,
                "T",
                "坏",
                "reject",
                0.0,
                ablation="soft_warning",
            )
        )
    forward = metrics.ablation_intervals(rows, rng=random.Random(metrics.SEED))
    backward = metrics.ablation_intervals(
        list(reversed(rows)),
        rng=random.Random(metrics.SEED),
    )
    assert [item["ablation"] for item in forward] == ["no_chunk_bind", "soft_warning"]
    assert forward == backward
    assert all(item["participates"] is False for item in forward)
    assert forward[1]["point"]["误放率"] is None
    bind = forward[0]
    assert bind["point"]["误放率"] == 1.0
    assert bind["intervals"]["误放率"]["defined"] is True

    streams = metrics.named_streams()
    boot_before = streams["bootstrap"].getstate()
    spot_before = streams["spotcheck"].getstate()
    metrics.ablation_intervals(rows, rng=streams["bootstrap_ablation"])
    assert streams["bootstrap"].getstate() == boot_before
    assert streams["spotcheck"].getstate() == spot_before
    assert streams["bootstrap_ablation"].getstate() != boot_before


def test_module_does_not_draw_from_unstable_rng_or_the_environment():
    text = inspect.getsource(metrics)
    for banned in (
        "randrange",
        "randint",
        "shuffle",
        "urandom",
        "getenv",
        "sample(",
        "choice(",
        "seed(",
        "spotcheck",
    ):
        assert banned not in inspect.getsource(metrics.compare_primary)
        assert banned not in inspect.getsource(metrics.ablation_intervals)
    for banned in ("randrange", "randint", "getenv", "urandom", "seed("):
        assert banned not in text
