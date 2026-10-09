"""SLO-07 复验主业观测回归（D1 multi-run · D3 挂接 · D4 分布 · 金标防火墙）。

Acceptance:
- D1 离线层 + n 小时不报总体方差 + must_stale 命中汇总 + 金标门
- 生产放行路径无 gold 放行特征
- D4 三值计数/占比
- D3 引用 SLO-02 同一出口且 violations=0
"""

from __future__ import annotations

from pathlib import Path

from freshlatch.disposition import ClaimDispositionInput
from freshlatch.slo_d1_d4_observability import (
    DEFAULT_MULTI_RUN_N,
    GOLD_FLOOR_STATEMENT,
    LAYER_OFFLINE_EVAL,
    VARIANCE_REPORT_MIN_N,
    acceptance_ok,
    build_week_observability,
    d3_from_hard_gate_report,
    distribute_dispositions,
    distribute_from_claim_batches,
    format_d1_report,
    load_gold_readonly,
    run_d3_via_slo02,
    scan_production_paths_no_gold_release,
    smoke_multirun_decisions,
    summarize_from_gold_run_report,
    summarize_must_stale_multirun,
)
from freshlatch.slo_hard_gate_violations import run_acceptance_probes


REPO = Path(__file__).resolve().parents[2]
GOLD = REPO / "data" / "eval" / "gold.json"


# ---------------------------------------------------------------------------
# D1
# ---------------------------------------------------------------------------


def test_d1_smoke_multirun_meets_gold_floor_and_offline_banner():
    """Given 离线 gold 评测入口, When multi-run n=3, Then must_stale 汇总过门且文首离线层。"""
    gold = load_gold_readonly(GOLD)
    decisions = smoke_multirun_decisions(gold, n_runs=DEFAULT_MULTI_RUN_N)
    summary = summarize_must_stale_multirun(gold, decisions, source="smoke_fixture")
    assert summary.layer == LAYER_OFFLINE_EVAL
    assert summary.n_runs == DEFAULT_MULTI_RUN_N == 3
    assert summary.meets_floor_all_runs
    assert summary.report_population_variance is False
    assert "不报总体方差" in summary.variance_note
    assert summary.n_runs < VARIANCE_REPORT_MIN_N
    assert GOLD_FLOOR_STATEMENT in summary.gold_floor_statement
    text = format_d1_report(summary)
    assert text.startswith(f"【{LAYER_OFFLINE_EVAL}】")
    assert "不报总体方差" in text
    assert "金标不得进生产 score" in text
    for cid in gold["must_stale"]:
        assert summary.pass_at_k[cid] == DEFAULT_MULTI_RUN_N


def test_d1_miss_fails_gold_floor():
    gold = load_gold_readonly(GOLD)
    miss_cid = gold["must_stale"][0]
    decisions = smoke_multirun_decisions(
        gold,
        n_runs=3,
        inject_miss_run=2,
        inject_miss_claim=miss_cid,
    )
    summary = summarize_must_stale_multirun(gold, decisions, source="smoke_fixture")
    assert not summary.meets_floor_all_runs
    assert summary.runs_meeting_floor == 2
    assert summary.per_run[1].misses == (miss_cid,)


def test_d1_from_gold_run_report_shape():
    gold = load_gold_readonly(GOLD)
    # 最小 gold_run 形：两遍全 stale
    raw = {
        "kind": "gold_run",
        "runs": 2,
        "per_run": [
            {"run": 1, "decisions": {cid: "stale" for cid in gold["must_stale"]}},
            {"run": 2, "decisions": {cid: "stale" for cid in gold["must_stale"]}},
        ],
    }
    summary = summarize_from_gold_run_report(raw, gold)
    assert summary.source == "gold_run_report"
    assert summary.meets_floor_all_runs
    assert summary.n_runs == 2


def test_gold_json_not_modified_by_loader():
    """Do-not-touch: 加载不得改写金标文件。"""
    before = GOLD.read_bytes()
    load_gold_readonly(GOLD)
    assert GOLD.read_bytes() == before


# ---------------------------------------------------------------------------
# D3 → SLO-02
# ---------------------------------------------------------------------------


def test_d3_same_exit_as_slo02(tmp_path: Path):
    """Given D3, When 对照 SLO-02 仪表, Then 同一出口且目标 violations=0。"""
    report = run_acceptance_probes(tmp_events_dir=tmp_path / "pe")
    d3 = d3_from_hard_gate_report(report)
    assert d3["same_exit_as"] == "SLO-02"
    assert d3["source_module"] == "freshlatch.slo_hard_gate_violations"
    assert d3["target_violations"] == 0
    assert d3["violations"] == 0
    # 与 week_fields 硬闸计数一致
    assert d3["violations"] == report.week_fields()["hard_gate_violation_counts"]["D3"]
    via = run_d3_via_slo02(tmp_events_dir=tmp_path / "pe2")
    assert via["violations"] == 0
    assert via["same_exit_as"] == "SLO-02"


# ---------------------------------------------------------------------------
# D4
# ---------------------------------------------------------------------------


def test_d4_three_value_distribution():
    """Given 一组 Run disposition, When 聚合 D4, Then 可发/需补丁/勿发计数与占比。"""
    dist = distribute_dispositions(["可发", "可发", "需补丁", "勿发"])
    assert dist.total_runs == 4
    assert dist.counts["可发"] == 2
    assert dist.counts["需补丁"] == 1
    assert dist.counts["勿发"] == 1
    assert abs(dist.ratios["可发"] - 0.5) < 1e-9
    batches = [
        [ClaimDispositionInput(status="fresh")],
        [ClaimDispositionInput(status="unknown")],
        [ClaimDispositionInput(status="stale")],
    ]
    from_batches = distribute_from_claim_batches(batches)
    assert from_batches.counts["可发"] == 1
    assert from_batches.counts["需补丁"] == 1
    assert from_batches.counts["勿发"] == 1


# ---------------------------------------------------------------------------
# 防火墙 + 组合 Acceptance
# ---------------------------------------------------------------------------


def test_production_paths_have_no_gold_release_features():
    """Given 生产放行/score 路径扫描, When 检查, Then 无读取 gold 标签作放行特征。"""
    scan = scan_production_paths_no_gold_release(REPO)
    assert scan.ok, scan.hits
    assert len(scan.scanned_files) >= 5


def test_week_observability_acceptance(tmp_path: Path):
    payload = build_week_observability(
        gold_path=GOLD,
        n_runs=DEFAULT_MULTI_RUN_N,
        repo_root=REPO,
        tmp_events_dir=tmp_path / "events",
    )
    assert payload["kind"] == "slo07_week_observability"
    assert payload["d1"]["layer"] == LAYER_OFFLINE_EVAL
    assert payload["d1"]["report_population_variance"] is False
    ok, errors = acceptance_ok(payload)
    assert ok, errors


def test_cli_main_exit_zero(tmp_path: Path):
    """CLI Acceptance：默认 --runs 3 退出 0。"""
    import subprocess
    import sys

    report_path = tmp_path / "week.md"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/slo_d1_d4_observability.py",
            "--runs",
            "3",
            "--write-report",
            str(report_path),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    text = report_path.read_text(encoding="utf-8")
    assert "离线评测层" in text
    assert "不报总体方差" in text
    assert "SLO-02" in text
    assert "可发" in text
