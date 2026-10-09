"""#437：compare_primary 固定 k 选取 R（PREREG-B）。

零 LLM、零网络、不读密钥、不改 PREREG / RESULT 成立格。
"""

from __future__ import annotations

import inspect

from freshlatch.eval import patch_events_metrics as metrics


def _row(claim_id, arm, gold, decision, score=None, **overrides):
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


def _quad_by_release(
    claim_id: str,
    gold: str,
    *,
    release_arms: set[str],
    score=None,
):
    rows = []
    for arm in ("C", "T", "B1", "B2"):
        decision = "release" if arm in release_arms else "reject"
        rows.append(_row(claim_id, arm, gold, decision, score))
    return rows


def _identifiable_rows():
    """T/B1/B2 自然放行集不同；空分。k = |T 放行| = 2。"""
    # claim  gold   T   B1  B2  C
    # a      正确    ✓   ✓   ✓  ✓
    # b      正确    ✓   ·   ✓  ✓
    # c      坏      ·   ✓   ✓  ✓
    # d      正确    ·   ·   ✓  ✓
    specs = [
        ("a", "正确", {"C", "T", "B1", "B2"}),
        ("b", "正确", {"C", "T", "B2"}),
        ("c", "坏", {"C", "B1", "B2"}),
        ("d", "正确", {"C", "B2"}),
    ]
    rows = []
    for claim_id, gold, arms in specs:
        rows.extend(_quad_by_release(claim_id, gold, release_arms=arms, score=None))
    return rows


def test_fixed_k_sets_can_differ_across_arms():
    result = metrics.compare_primary(_identifiable_rows(), streams=metrics.named_streams())
    assert result["k"] == 2
    t_ids = result["arms"]["T"]["fixed"]["selected_claim_ids"]
    b1_ids = result["arms"]["B1"]["fixed"]["selected_claim_ids"]
    b2_ids = result["arms"]["B2"]["fixed"]["selected_claim_ids"]
    c_ids = result["arms"]["C"]["fixed"]["selected_claim_ids"]
    assert t_ids == ["a", "b"]
    assert b1_ids == ["a", "c"]
    assert b2_ids == ["a", "b"]
    assert c_ids == ["a", "b"]
    assert t_ids != b1_ids
    assert set(t_ids) != set(b1_ids)


def test_m_ge_k_takes_claim_id_ascending_inside_release_set():
    rows = []
    # T 放行 a,c → k=2；B2 放行 d,c,b,a → 集内升序取 a,b
    for claim_id, gold, arms in (
        ("d", "坏", {"C", "B2"}),
        ("c", "正确", {"C", "T", "B2"}),
        ("b", "坏", {"C", "B2"}),
        ("a", "正确", {"C", "T", "B2"}),
    ):
        rows.extend(_quad_by_release(claim_id, gold, release_arms=arms, score=None))
    result = metrics.compare_primary(rows, streams=metrics.named_streams())
    assert result["k"] == 2
    assert result["arms"]["T"]["fixed"]["selected_claim_ids"] == ["a", "c"]
    assert result["arms"]["B2"]["fixed"]["selected_claim_ids"] == ["a", "b"]
    b2_rows = [r for r in rows if r["arm"] == "B2"]
    positions = metrics.select_fixed_k_from_releases(b2_rows, 2)
    assert positions is not None
    assert [b2_rows[i]["claim_id"] for i in positions] == ["a", "b"]


def test_m_lt_k_makes_arm_undefined_and_not_established():
    rows = []
    # T 放行 3 条 → k=3；B1 只放行 1 条 → m<k
    for claim_id, gold, arms in (
        ("a", "正确", {"C", "T", "B1", "B2"}),
        ("b", "正确", {"C", "T", "B2"}),
        ("c", "坏", {"C", "T", "B2"}),
        ("d", "坏", {"C", "B2"}),
    ):
        rows.extend(_quad_by_release(claim_id, gold, release_arms=arms, score=None))
    result = metrics.compare_primary(rows, streams=metrics.named_streams())
    assert result["k"] == 3
    assert result["arms"]["B1"]["fixed"]["误放率"] is None
    assert result["arms"]["B1"]["fixed"]["selected_claim_ids"] is None
    assert metrics.format_rate(result["arms"]["B1"]["fixed"]["误放率"]) == "无定义"
    versus_b1 = next(item for item in result["comparisons"] if item["name"] == "T-B1")
    assert versus_b1["point"] is None
    assert versus_b1["established"] is False
    assert result["arms"]["T"]["fixed"]["selected_claim_ids"] == ["a", "b", "c"]
    assert result["arms"]["B2"]["fixed"]["selected_claim_ids"] == ["a", "b", "c"]


def test_legacy_empty_score_same_set_locks_diff_at_zero_but_primary_rejects_it():
    """再现旧病；主路径不得再走空分全体 claim_id top-k。"""
    rows = _identifiable_rows()
    # 空分 + legacy：T/B1/B2 全体按 claim_id 取同一 k 集 → 差恒 0
    by_arm: dict[str, list] = {"T": [], "B1": [], "B2": []}
    for row in rows:
        if row["arm"] in by_arm:
            by_arm[row["arm"]].append(row)
    k = sum(1 for row in by_arm["T"] if row["decision"] == "release")
    legacy_sets = {
        arm: [
            arm_rows[i]["claim_id"]
            for i in metrics.legacy_select_fixed_k_empty_score_topk(arm_rows, k)
        ]
        for arm, arm_rows in by_arm.items()
    }
    assert legacy_sets["T"] == legacy_sets["B1"] == legacy_sets["B2"] == ["a", "b"]
    # 同集上误放差恒 0（金标随 claim_id，与臂无关）
    gold = {row["claim_id"]: row["construction_gold"] for row in by_arm["T"]}
    legacy_far = {
        arm: sum(gold[cid] == "坏" for cid in ids) / k for arm, ids in legacy_sets.items()
    }
    assert legacy_far["B1"] - legacy_far["T"] == 0.0
    assert legacy_far["B2"] - legacy_far["T"] == 0.0

    primary_src = inspect.getsource(metrics.compare_primary)
    boot_src = inspect.getsource(metrics._bootstrap_fixed)
    assert "_top_positions" not in primary_src
    assert "_top_positions" not in boot_src
    assert "legacy_select_fixed_k_empty_score_topk" not in primary_src
    assert "_sample_positions" not in primary_src
    assert "coverage_c" not in primary_src

    result = metrics.compare_primary(rows, streams=metrics.named_streams())
    assert result["arms"]["T"]["fixed"]["selected_claim_ids"] != result["arms"]["B1"][
        "fixed"
    ]["selected_claim_ids"]
    versus_b1 = next(item for item in result["comparisons"] if item["name"] == "T-B1")
    assert versus_b1["point"] != 0.0


def test_bootstrap_reselects_fixed_k_via_r(monkeypatch):
    calls: list[tuple[int, int]] = []
    real = metrics._release_positions_r

    def wrapped(drawn, release, claim_ids, k):
        calls.append((len(drawn), k))
        return real(drawn, release, claim_ids, k)

    monkeypatch.setattr(metrics, "_release_positions_r", wrapped)
    streams = metrics.named_streams()
    coverage_before = streams["coverage_c"].getstate()
    metrics.compare_primary(_identifiable_rows(), streams=streams)
    assert streams["coverage_c"].getstate() == coverage_before
    # 点估计 4 臂各 1 次 + 3 比较 × 4 指标 × N_BOOT × 2 臂
    n = len(calls)
    assert n > metrics.N_BOOT
    # 重抽样调用里 drawn 长度等于原 n，且仍传入当时的 k
    assert any(length == 4 and k >= 0 for length, k in calls)
    assert "_top_positions" not in inspect.getsource(metrics._bootstrap_fixed)


def test_primary_does_not_consume_coverage_c():
    streams = metrics.named_streams()
    before = streams["coverage_c"].getstate()
    spot = streams["spotcheck"].getstate()
    abl = streams["bootstrap_ablation"].getstate()
    metrics.compare_primary(_identifiable_rows(), streams=streams)
    assert streams["coverage_c"].getstate() == before
    assert streams["spotcheck"].getstate() == spot
    assert streams["bootstrap_ablation"].getstate() == abl
    assert streams["bootstrap"].getstate() != before
