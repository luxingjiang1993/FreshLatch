"""SLO A6：confirm 后再验失败率（只读聚合）。

对齐 docs/ops/生产补丁放行SLO.md §A6：
confirm 后单条再验仍失败占比（观测 / 周报）。

本模块不改 evidence_bound 再验谓词、不写 patch_events、不碰 RESULT-Y。
分母=时间窗内已 human_confirm 且再验结果可查询的行；
分子=再验 verdict 非 fresh（仍 stale/unknown 等）。
窗内 0 条 confirm → 诚实空态，禁止用 0% 伪装完美。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from freshlatch.patch_events import iter_events

# 再验「成功救回」判定：与 confirm 后 claim.status 词表对齐；不放宽谓词
REVERIFY_SUCCESS: frozenset[str] = frozenset({"fresh"})
# 常见仍失败态（其它非 fresh 亦计失败，见 is_still_failed）
REVERIFY_STILL_FAILED_KNOWN: frozenset[str] = frozenset({"stale", "unknown"})

EMPTY_WEEKLY_LINE = "A6 再验失败率: 本周无 confirm"
METRIC_ID = "A6"


@dataclass(frozen=True)
class A6Window:
    """聚合时间窗（含起、不含止；UTC）。"""

    start: datetime
    end: datetime

    def label(self) -> str:
        return f"{_fmt_ts(self.start)} .. {_fmt_ts(self.end)}"


@dataclass(frozen=True)
class A6Report:
    """可写入周报的 A6 聚合结果。"""

    window: A6Window
    confirm_count: int
    queryable_count: int
    still_failed_count: int
    empty: bool

    @property
    def fail_rate(self) -> float | None:
        if self.empty or self.queryable_count == 0:
            return None
        return self.still_failed_count / self.queryable_count

    @property
    def fraction_label(self) -> str | None:
        if self.empty or self.queryable_count == 0:
            return None
        return f"{self.still_failed_count}/{self.queryable_count}"

    def weekly_fill_line(self) -> str:
        """对照 ops §6「A6 再验失败率」可直接粘贴的一句。"""
        if self.empty:
            return EMPTY_WEEKLY_LINE
        if self.queryable_count == 0:
            return (
                f"A6 再验失败率: 窗内有 confirm={self.confirm_count} "
                f"但再验结果不可查询（诚实空态；非 0%）"
            )
        pct = 100.0 * float(self.fail_rate or 0.0)
        return (
            f"A6 再验失败率: {pct:.2f}% ({self.fraction_label})；"
            f"窗 {self.window.label()}"
        )

    def to_dict(self) -> dict[str, Any]:
        rate = self.fail_rate
        return {
            "metric_id": METRIC_ID,
            "window_start": _fmt_ts(self.window.start),
            "window_end": _fmt_ts(self.window.end),
            "window_label": self.window.label(),
            "confirm_count": self.confirm_count,
            "queryable_count": self.queryable_count,
            "still_failed_count": self.still_failed_count,
            "fail_rate": rate,
            "fraction": self.fraction_label,
            "empty": self.empty,
            "weekly_fill_line": self.weekly_fill_line(),
            # 禁止空窗报 0%：显式标记
            "forbid_zero_percent_when_empty": True,
        }


def _fmt_ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def parse_ts(value: str | datetime) -> datetime:
    """解析 ISO-8601 或 datetime；无 tz 视为 UTC。"""
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def default_week_window(*, now: datetime | None = None) -> A6Window:
    """默认周窗：以 now 为终点的过去 7 天（含起不含止）。"""
    end = now if now is not None else datetime.now(timezone.utc)
    end = parse_ts(end)
    start = end - timedelta(days=7)
    return A6Window(start=start, end=end)


def is_product_confirm(row: Mapping[str, Any]) -> bool:
    """产品 confirm 行：人确认且强制再验标记为 true（ADR-0029 成功路径）。"""
    return bool(row.get("human_confirm")) and bool(row.get("reverify"))


def extract_reverify_verdict(row: Mapping[str, Any]) -> str | None:
    """从行或 confirm 结果 dict 取再验 verdict；不可查询 → None。"""
    for key in ("reverify_verdict", "claim_status_after", "status_after"):
        raw = row.get(key)
        if raw is None:
            continue
        text = str(raw).strip().lower()
        if text:
            return text
    return None


def is_still_failed(verdict: str) -> bool:
    """仍失败：再验后非 fresh（不放宽；unknown/stale 均计失败）。"""
    return str(verdict).strip().lower() not in REVERIFY_SUCCESS


def _in_window(ts: datetime, window: A6Window) -> bool:
    return window.start <= ts < window.end


def _outcome_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (str(row.get("claim_id") or ""), str(row.get("ts") or ""))


def load_outcomes_jsonl(path: Path) -> dict[tuple[str, str], str]:
    """outcomes JSONL：每行至少 claim_id/ts/reverify_verdict，按 (claim_id, ts) 索引。"""
    out: dict[tuple[str, str], str] = {}
    if not path.is_file():
        return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, Mapping):
                continue
            verdict = extract_reverify_verdict(row)
            if verdict is None:
                continue
            key = _outcome_key(row)
            if key[0] and key[1]:
                out[key] = verdict
    return out


def merge_verdict(
    row: Mapping[str, Any],
    outcomes: Mapping[tuple[str, str], str] | None = None,
) -> str | None:
    """行内字段优先，其次 outcomes 旁路。"""
    direct = extract_reverify_verdict(row)
    if direct is not None:
        return direct
    if not outcomes:
        return None
    return outcomes.get(_outcome_key(row))


def iter_confirm_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    window: A6Window,
) -> list[dict[str, Any]]:
    """窗内产品 confirm 行（只读过滤）。"""
    selected: list[dict[str, Any]] = []
    for row in rows:
        if not is_product_confirm(row):
            continue
        ts_raw = row.get("ts")
        if not ts_raw:
            continue
        try:
            ts = parse_ts(str(ts_raw))
        except ValueError:
            continue
        if not _in_window(ts, window):
            continue
        selected.append(dict(row))
    return selected


def aggregate_a6(
    rows: Iterable[Mapping[str, Any]],
    *,
    window: A6Window,
    outcomes: Mapping[tuple[str, str], str] | None = None,
) -> A6Report:
    """从 confirm(+可选 outcomes) 聚合 A6。"""
    confirms = iter_confirm_rows(rows, window=window)
    if not confirms:
        return A6Report(
            window=window,
            confirm_count=0,
            queryable_count=0,
            still_failed_count=0,
            empty=True,
        )

    queryable = 0
    still_failed = 0
    for row in confirms:
        verdict = merge_verdict(row, outcomes)
        if verdict is None:
            continue
        queryable += 1
        if is_still_failed(verdict):
            still_failed += 1

    return A6Report(
        window=window,
        confirm_count=len(confirms),
        queryable_count=queryable,
        still_failed_count=still_failed,
        empty=False,
    )


def aggregate_a6_from_events_dir(
    *,
    events_dir: Path | None = None,
    filename: str = "events.jsonl",
    window: A6Window | None = None,
    outcomes_path: Path | None = None,
    now: datetime | None = None,
) -> A6Report:
    """读 patch_events 目录 + 可选 outcomes，产出 A6。"""
    win = window if window is not None else default_week_window(now=now)
    outcomes = load_outcomes_jsonl(outcomes_path) if outcomes_path else {}
    rows = list(iter_events(events_dir=events_dir, filename=filename))
    return aggregate_a6(rows, window=win, outcomes=outcomes or None)


def render_markdown(report: A6Report) -> str:
    """人读周报片段（UTF-8）。"""
    d = report.to_dict()
    lines = [
        f"# {METRIC_ID} 再验失败率",
        "",
        f"- 指标: {METRIC_ID}",
        f"- 时间窗: {d['window_label']}",
        f"- 窗内 confirm 数: {d['confirm_count']}",
        f"- 再验结果可查询分母: {d['queryable_count']}",
        f"- 仍失败分子: {d['still_failed_count']}",
    ]
    if report.empty:
        lines.append("- 失败率: （空态，不报 0%）")
    elif report.queryable_count == 0:
        lines.append("- 失败率: （再验结果不可查询，不报 0%）")
    else:
        pct = 100.0 * float(report.fail_rate or 0.0)
        lines.append(f"- 失败率: {pct:.2f}%（{report.fraction_label}）")
    lines.extend(
        [
            f"- 周报填写: `{report.weekly_fill_line()}`",
            "",
            "> 层身份：观测/周报。不是实验乙成立格；不改 RESULT-Y。",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    report: A6Report,
    out_dir: Path,
    *,
    stem: str | None = None,
) -> tuple[Path, Path]:
    """写入 reports/slo 约定：同 stem 的 .json + .md。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    if stem is None:
        stem = (
            f"a6-{report.window.start.strftime('%Y%m%d')}"
            f"-{report.window.end.strftime('%Y%m%d')}"
        )
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def load_rows_from_jsonl(path: Path) -> list[dict[str, Any]]:
    """通用 JSONL 读取（夹具 / 旁路账本）。"""
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, Mapping):
                rows.append(dict(obj))
    return rows


def rows_from_confirm_results(
    results: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """把 ConfirmPatchResult.to_dict() 列表投影为可聚合行。

    成功且再验触发的行才计入；事件 ts 优先取 event.ts。
    """
    rows: list[dict[str, Any]] = []
    for item in results:
        if not item.get("ok"):
            continue
        if not item.get("reverify_triggered") and not item.get("reverify"):
            continue
        event = item.get("event") if isinstance(item.get("event"), Mapping) else {}
        ts = str(event.get("ts") or item.get("ts") or "")
        claim_id = str(item.get("claim_id") or event.get("claim_id") or "")
        verdict = extract_reverify_verdict(item)
        if not ts or not claim_id or verdict is None:
            continue
        rows.append(
            {
                "claim_id": claim_id,
                "ts": ts,
                "human_confirm": True,
                "reverify": True,
                "reverify_verdict": verdict,
                "arm": str(event.get("arm") or "T"),
            }
        )
    return rows
