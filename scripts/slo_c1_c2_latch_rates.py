#!/usr/bin/env python3
"""SLO-06：人审作废率(C1)与 override rate(C2)只读周报聚合。

真源：`latch_log`（discard/renew）+ `invalidation_list`（作废名单只读交叉）。
层身份：观测 / Watch（`docs/ops/生产补丁放行SLO.md` §3.3）。**不是**验收绿灯。

纪律（ADR-0023）：
- override 是派生标签，不新增 HumanLatch 动词；
- **override 不作模型变好 / 不作验收绿灯**；
- 本脚本不锁 Override Rate 通过线。

用法::

    python scripts/slo_c1_c2_latch_rates.py --db path/to.db
    python scripts/slo_c1_c2_latch_rates.py --db path/to.db --week-start 2026-09-22 --json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# 周报声明：输出头与文档互指必须保留此句意（验收）
DISCLAIMER = (
    "override 不作模型变好 / 不作验收绿灯（ADR-0023；"
    "docs/ops/生产补丁放行SLO.md C2）"
)

HUMAN_ACTIONS = frozenset({"discard", "renew"})


@dataclass(frozen=True)
class Window:
    start: str | None  # ISO date inclusive, or None = 不限
    end: str | None  # ISO date exclusive, or None = 不限


@dataclass
class C1Report:
    id: str
    name: str
    layer: str
    discard_claim_n: int
    denominator_n: int
    rate: float | None
    definition: str
    invalidation_list_n: int
    discard_of_fresh_n: int


@dataclass
class C2Report:
    id: str
    name: str
    layer: str
    override_true_n: int
    denominator_n: int
    rate: float | None
    definition: str
    not_model_improvement: bool
    not_acceptance_green: bool


@dataclass
class WeeklyReport:
    disclaimer: str
    layer: str
    window: dict[str, Any]
    C1: dict[str, Any]
    C2: dict[str, Any]
    ops_fields: dict[str, Any]


def _parse_ts(ts: str) -> datetime | None:
    """解析 latch_log.ts（isoformat 或紧凑 YYYYMMDD-HHMMSS）。"""
    if not ts:
        return None
    raw = str(ts).strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        pass
    for fmt in ("%Y%m%d-%H%M%S", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _in_window(ts: str, window: Window) -> bool:
    if window.start is None and window.end is None:
        return True
    dt = _parse_ts(ts)
    if dt is None:
        return False
    d = dt.date()
    if window.start is not None and d < date.fromisoformat(window.start):
        return False
    if window.end is not None and d >= date.fromisoformat(window.end):
        return False
    return True


def load_latch_rows(db_path: str | Path) -> list[dict[str, Any]]:
    """只读拉取 latch_log；不经 HumanLatch 写路径。"""
    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError(f"数据库不存在: {path}")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(latch_log)")}
        if "latch_log" not in {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }:
            return []
        select = (
            "SELECT ts, claim_id, action, evidence_id, actor, "
            "machine_status_before, override, run_id, reviewer_note "
            "FROM latch_log ORDER BY ts, rowid"
            if "override" in cols
            else "SELECT ts, claim_id, action, evidence_id, actor "
            "FROM latch_log ORDER BY ts, rowid"
        )
        rows = [dict(r) for r in conn.execute(select).fetchall()]
        for row in rows:
            if "override" not in row:
                row["override"] = None
                row["machine_status_before"] = None
            elif row["override"] is not None:
                row["override"] = bool(row["override"])
        return rows
    finally:
        conn.close()


def load_invalidation_ids(db_path: str | Path) -> list[str]:
    path = Path(db_path)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "invalidation_list" not in tables:
            return []
        rows = conn.execute("SELECT claim_id FROM invalidation_list").fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def _human_rows(rows: list[dict[str, Any]], window: Window) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("action") not in HUMAN_ACTIONS:
            continue
        if not _in_window(str(row.get("ts") or ""), window):
            continue
        out.append(row)
    return out


def aggregate_c1(
    rows: list[dict[str, Any]],
    invalidation_ids: list[str],
    window: Window,
) -> C1Report:
    """C1 用户作废率：discard 去重 claim / 人审(discard|renew)去重 claim。"""
    human = _human_rows(rows, window)
    reviewed = {str(r["claim_id"]) for r in human if r.get("claim_id")}
    discarded = {
        str(r["claim_id"])
        for r in human
        if r.get("action") == "discard" and r.get("claim_id")
    }
    discard_of_fresh = {
        str(r["claim_id"])
        for r in human
        if r.get("action") == "discard"
        and r.get("machine_status_before") == "fresh"
        and r.get("claim_id")
    }
    den = len(reviewed)
    num = len(discarded)
    rate = (num / den) if den else None
    return C1Report(
        id="C1",
        name="用户作废率",
        layer="观测/Watch",
        discard_claim_n=num,
        denominator_n=den,
        rate=rate,
        definition=(
            "时间窗内 latch_log.action=discard 的去重 claim_id "
            "/ action∈{discard,renew} 的去重 claim_id（分母=人审主张数）"
        ),
        invalidation_list_n=len(invalidation_ids),
        discard_of_fresh_n=len(discard_of_fresh),
    )


def aggregate_c2(rows: list[dict[str, Any]], window: Window) -> C2Report:
    """C2 Override rate：override=1 行 / override 非空的人审行。"""
    human = _human_rows(rows, window)
    labeled = [r for r in human if r.get("override") is not None]
    true_n = sum(1 for r in labeled if r.get("override") is True)
    den = len(labeled)
    rate = (true_n / den) if den else None
    return C2Report(
        id="C2",
        name="Override rate",
        layer="观测/Watch",
        override_true_n=true_n,
        denominator_n=den,
        rate=rate,
        definition=(
            "时间窗内 latch_log.override=1 的人审行数 "
            "/ override∈{0,1} 的人审行数（分母=带派生标签的成功人审事件）"
        ),
        not_model_improvement=True,
        not_acceptance_green=True,
    )


def build_report(
    db_path: str | Path,
    *,
    week_start: str | None = None,
    week_end: str | None = None,
) -> WeeklyReport:
    if week_start and not week_end:
        start_d = date.fromisoformat(week_start)
        week_end = (start_d + timedelta(days=7)).isoformat()
    window = Window(start=week_start, end=week_end)
    rows = load_latch_rows(db_path)
    voids = load_invalidation_ids(db_path)
    c1 = aggregate_c1(rows, voids, window)
    c2 = aggregate_c2(rows, window)
    return WeeklyReport(
        disclaimer=DISCLAIMER,
        layer="观测/Watch（非硬闸；非实验乙成立格）",
        window={
            "start_inclusive": week_start,
            "end_exclusive": week_end,
            "note": "未指定则全库；指定 --week-start 时默认 +7 天半开区间",
        },
        C1=asdict(c1),
        C2=asdict(c2),
        ops_fields={
            "C1_作废率": c1.rate,
            "C1_分子_discard_claim_n": c1.discard_claim_n,
            "C1_分母_reviewed_claim_n": c1.denominator_n,
            "C2_override_rate": c2.rate,
            "C2_分子_override_true_n": c2.override_true_n,
            "C2_分母_override_labeled_n": c2.denominator_n,
            "可填周报": "docs/ops/生产补丁放行SLO.md §6 · C1 作废率 · C2 override rate",
        },
    )


def format_text(report: WeeklyReport) -> str:
    c1 = report.C1
    c2 = report.C2
    lines = [
        "# SLO 周报字段 · C1/C2（人审）",
        "",
        f"> {report.disclaimer}",
        f"> 层：{report.layer}",
        "",
        "## 时间窗",
        "",
        f"- start_inclusive: {report.window.get('start_inclusive')}",
        f"- end_exclusive: {report.window.get('end_exclusive')}",
        "",
        "## C1 用户作废率",
        "",
        f"- 定义: {c1['definition']}",
        f"- 分子 discard_claim_n: {c1['discard_claim_n']}",
        f"- 分母 reviewed_claim_n: {c1['denominator_n']}",
        f"- 作废率: {_fmt_rate(c1['rate'])}",
        f"- 其中 discard∧machine_status_before=fresh: {c1['discard_of_fresh_n']}",
        f"- invalidation_list 全库条数（交叉）: {c1['invalidation_list_n']}",
        "",
        "## C2 Override rate",
        "",
        f"- 定义: {c2['definition']}",
        f"- 分子 override_true_n: {c2['override_true_n']}",
        f"- 分母 override_labeled_n: {c2['denominator_n']}",
        f"- override rate: {_fmt_rate(c2['rate'])}",
        f"- not_model_improvement: {c2['not_model_improvement']}",
        f"- not_acceptance_green: {c2['not_acceptance_green']}",
        "",
        "## 对照 ops 周报最小字段",
        "",
        f"- C1 作废率 = {_fmt_rate(c1['rate'])} "
        f"({c1['discard_claim_n']}/{c1['denominator_n']})",
        f"- C2 override rate = {_fmt_rate(c2['rate'])} "
        f"({c2['override_true_n']}/{c2['denominator_n']})",
        "",
    ]
    return "\n".join(lines)


def _fmt_rate(rate: float | None) -> str:
    if rate is None:
        return "n/a（分母为 0）"
    return f"{rate:.4f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SLO-06 C1/C2 人审作废率与 override rate 只读周报"
    )
    parser.add_argument("--db", required=True, help="SQLite 库路径（只读）")
    parser.add_argument(
        "--week-start",
        default=None,
        help="周起始日 YYYY-MM-DD（含）；省略则全库",
    )
    parser.add_argument(
        "--week-end",
        default=None,
        help="周结束日 YYYY-MM-DD（不含）；省略且有 week-start 时为 +7 天",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON（默认 Markdown 文本）",
    )
    parser.add_argument(
        "-o",
        "--out",
        default=None,
        help="写入文件；默认 stdout",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(
            args.db, week_start=args.week_start, week_end=args.week_end
        )
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    payload = (
        json.dumps(asdict(report), ensure_ascii=False, indent=2)
        if args.json
        else format_text(report)
    )
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + ("" if payload.endswith("\n") else "\n"), encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
