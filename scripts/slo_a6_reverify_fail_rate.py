#!/usr/bin/env python3
"""SLO-04：A6 confirm 后再验失败率周报聚合 CLI。

只读 patch_events（及可选 outcomes JSONL），不改再验语义、不冲乙。

用法示例：
  python scripts/slo_a6_reverify_fail_rate.py \\
    --events-dir data/patch_events \\
    --outcomes path/to/outcomes.jsonl \\
    --window-start 2026-10-02T00:00:00+00:00 \\
    --window-end 2026-10-09T00:00:00+00:00 \\
    --out-dir reports/slo

窗内 0 条 confirm → 输出诚实空态「本周无 confirm」，禁止 0% 伪装完美。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freshlatch.slo_a6 import (  # noqa: E402
    A6Window,
    aggregate_a6,
    aggregate_a6_from_events_dir,
    default_week_window,
    load_outcomes_jsonl,
    load_rows_from_jsonl,
    parse_ts,
    write_report,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="聚合 A6 再验失败率（confirm 后仍失败占比）",
    )
    p.add_argument(
        "--events-dir",
        type=Path,
        default=None,
        help="patch_events 目录（默认仓内 data/patch_events）",
    )
    p.add_argument(
        "--events-file",
        type=Path,
        default=None,
        help="直接指定 events JSONL（优先于 --events-dir）",
    )
    p.add_argument(
        "--outcomes",
        type=Path,
        default=None,
        help="旁路 outcomes JSONL：claim_id/ts/reverify_verdict",
    )
    p.add_argument(
        "--window-start",
        type=str,
        default=None,
        help="窗起点 ISO-8601（含）",
    )
    p.add_argument(
        "--window-end",
        type=str,
        default=None,
        help="窗终点 ISO-8601（不含）；缺省=now UTC",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "reports" / "slo",
        help="输出目录（默认 reports/slo）",
    )
    p.add_argument(
        "--stem",
        type=str,
        default=None,
        help="输出文件名 stem（默认 a6-<start>-<end>）",
    )
    p.add_argument(
        "--no-write",
        action="store_true",
        help="只打印周报句，不写文件",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.window_start and args.window_end:
        window = A6Window(
            start=parse_ts(args.window_start),
            end=parse_ts(args.window_end),
        )
    elif args.window_end and not args.window_start:
        end = parse_ts(args.window_end)
        window = default_week_window(now=end)
    elif args.window_start and not args.window_end:
        start = parse_ts(args.window_start)
        end = datetime.now(timezone.utc)
        window = A6Window(start=start, end=end)
    else:
        window = default_week_window()

    outcomes = load_outcomes_jsonl(args.outcomes) if args.outcomes else None

    if args.events_file is not None:
        rows = load_rows_from_jsonl(args.events_file)
        report = aggregate_a6(rows, window=window, outcomes=outcomes)
    else:
        report = aggregate_a6_from_events_dir(
            events_dir=args.events_dir,
            window=window,
            outcomes_path=args.outcomes,
        )

    line = report.weekly_fill_line()
    print(line)

    if not args.no_write:
        json_path, md_path = write_report(
            report, Path(args.out_dir), stem=args.stem
        )
        print(f"wrote {json_path}")
        print(f"wrote {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
