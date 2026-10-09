"""SLO-04：A6 confirm 后再验失败率聚合。

验收：
- 有 confirm + 可查询再验结果 → 失败率/分数 + 时间窗
- 0 confirm → 诚实空态（非 0%）
- 输出可直接填 ops A6 周报字段
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from freshlatch import patch_events as pe
from freshlatch.slo_a6 import (
    EMPTY_WEEKLY_LINE,
    A6Window,
    aggregate_a6,
    aggregate_a6_from_events_dir,
    is_still_failed,
    parse_ts,
    render_markdown,
    rows_from_confirm_results,
    write_report,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_a6_cli():
    path = _REPO_ROOT / "scripts" / "slo_a6_reverify_fail_rate.py"
    spec = importlib.util.spec_from_file_location("slo_a6_reverify_fail_rate", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ts(day: int, hour: int = 12) -> str:
    return f"2026-10-{day:02d}T{hour:02d}:00:00+00:00"


def _confirm_row(
    *,
    claim_id: str,
    ts: str,
    verdict: str | None,
    human_confirm: bool = True,
    reverify: bool = True,
) -> dict:
    row = {
        "claim_id": claim_id,
        "before_disp": "需补丁",
        "patch_span": f"{claim_id}·正文替换",
        "t1_ids": ["t1-a"],
        "human_confirm": human_confirm,
        "reverify": reverify,
        "minutes": 5.0,
        "arm": "T",
        "ts": ts,
        "actor": "human",
        "before_text": "旧",
        "after_text": "新",
    }
    if verdict is not None:
        row["reverify_verdict"] = verdict
    return row


WINDOW = A6Window(
    start=parse_ts("2026-10-02T00:00:00+00:00"),
    end=parse_ts("2026-10-09T00:00:00+00:00"),
)


def test_aggregate_with_confirms_reports_fraction_and_window():
    """Given ≥1 条已 confirm 且再验可查询, When 聚合, Then 失败率=分数并标明时间窗。"""
    rows = [
        _confirm_row(claim_id="c1", ts=_ts(3), verdict="stale"),
        _confirm_row(claim_id="c2", ts=_ts(4), verdict="fresh"),
        _confirm_row(claim_id="c3", ts=_ts(5), verdict="unknown"),
        # 窗外
        _confirm_row(claim_id="c4", ts=_ts(1), verdict="stale"),
        # 非 confirm 产品路径
        _confirm_row(
            claim_id="c5",
            ts=_ts(6),
            verdict="stale",
            human_confirm=True,
            reverify=False,
        ),
    ]
    report = aggregate_a6(rows, window=WINDOW)
    assert report.empty is False
    assert report.confirm_count == 3
    assert report.queryable_count == 3
    assert report.still_failed_count == 2
    assert report.fraction_label == "2/3"
    assert report.fail_rate == pytest.approx(2 / 3)
    assert "2026-10-02" in report.window.label()
    assert "2026-10-09" in report.window.label()
    line = report.weekly_fill_line()
    assert line.startswith("A6 再验失败率:")
    assert "2/3" in line
    assert "66.67%" in line
    assert "2026-10-02" in line


def test_zero_confirms_honest_empty_not_zero_percent():
    """Given 窗口内 0 条 confirm, When 聚合, Then 诚实空态（非 0%）。"""
    rows = [
        _confirm_row(claim_id="out", ts=_ts(1), verdict="stale"),
        {
            "claim_id": "hr",
            "before_disp": "勿发",
            "patch_span": "人审",
            "t1_ids": [],
            "human_confirm": True,
            "reverify": False,
            "minutes": 0.0,
            "arm": "C",
            "ts": _ts(5),
            "actor": "human",
        },
    ]
    report = aggregate_a6(rows, window=WINDOW)
    assert report.empty is True
    assert report.confirm_count == 0
    assert report.fail_rate is None
    assert report.weekly_fill_line() == EMPTY_WEEKLY_LINE
    assert "0%" not in report.weekly_fill_line()
    assert "0.00%" not in render_markdown(report)


def test_weekly_fill_line_matches_ops_a6_field():
    """Given 聚合输出, When 对照 ops 周报字段, Then 可直接填 A6。"""
    rows = [
        _confirm_row(claim_id="c1", ts=_ts(7), verdict="fresh"),
        _confirm_row(claim_id="c2", ts=_ts(7, 13), verdict="stale"),
    ]
    report = aggregate_a6(rows, window=WINDOW)
    line = report.weekly_fill_line()
    # ops §6 字段名「A6 再验失败率」
    assert "A6 再验失败率" in line
    assert report.to_dict()["metric_id"] == "A6"
    assert report.to_dict()["weekly_fill_line"] == line


def test_outcomes_sidecar_joins_bare_patch_events(tmp_path: Path):
    """账本无 verdict 时，outcomes 旁路可查询再验结果。"""
    events_dir = tmp_path / "patch_events"
    pe.append_product_confirm(
        claim_id="mck-3",
        before_disp="需补丁",
        patch_span="mck-3·正文替换",
        t1_ids=["t1-a"],
        minutes=3.0,
        before_text="旧",
        after_text="新",
        reverify=True,
        ts=_ts(4),
        events_dir=events_dir,
    )
    # 读回 ts 与写入一致
    written = pe.read_events(events_dir=events_dir)[0]
    outcomes_path = tmp_path / "outcomes.jsonl"
    outcomes_path.write_text(
        json.dumps(
            {
                "claim_id": written["claim_id"],
                "ts": written["ts"],
                "reverify_verdict": "unknown",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    report = aggregate_a6_from_events_dir(
        events_dir=events_dir,
        window=WINDOW,
        outcomes_path=outcomes_path,
    )
    assert report.empty is False
    assert report.queryable_count == 1
    assert report.still_failed_count == 1
    assert report.fraction_label == "1/1"


def test_write_report_artifacts(tmp_path: Path):
    rows = [_confirm_row(claim_id="c1", ts=_ts(3), verdict="stale")]
    report = aggregate_a6(rows, window=WINDOW)
    json_path, md_path = write_report(report, tmp_path / "slo", stem="a6-test")
    assert json_path.is_file()
    assert md_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["weekly_fill_line"].startswith("A6 再验失败率:")
    assert "A6 再验失败率" in md_path.read_text(encoding="utf-8")


def test_is_still_failed_predicate_unchanged():
    """不放宽：仅 fresh 算救回；stale/unknown 均仍失败。"""
    assert is_still_failed("stale")
    assert is_still_failed("unknown")
    assert not is_still_failed("fresh")
    assert not is_still_failed("FRESH")


def test_rows_from_confirm_results_projection():
    results = [
        {
            "ok": True,
            "claim_id": "mck-3",
            "reverify_triggered": True,
            "reverify_verdict": "stale",
            "event": {"ts": _ts(5), "arm": "T", "claim_id": "mck-3"},
        },
        {"ok": False, "claim_id": "x", "reverify_verdict": "stale"},
    ]
    rows = rows_from_confirm_results(results)
    report = aggregate_a6(rows, window=WINDOW)
    assert report.confirm_count == 1
    assert report.still_failed_count == 1


def test_cli_empty_window(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """CLI：空窗打印诚实空态。"""
    cli = _load_a6_cli()
    events = tmp_path / "empty.jsonl"
    events.write_text("", encoding="utf-8")
    out_dir = tmp_path / "out"
    code = cli.main(
        [
            "--events-file",
            str(events),
            "--window-start",
            "2026-10-02T00:00:00+00:00",
            "--window-end",
            "2026-10-09T00:00:00+00:00",
            "--out-dir",
            str(out_dir),
        ]
    )
    assert code == 0
    captured = capsys.readouterr().out
    assert EMPTY_WEEKLY_LINE in captured
    assert "0%" not in captured.splitlines()[0]
