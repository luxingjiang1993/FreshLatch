#!/usr/bin/env python3
"""SLO-07：复验主业观测 CLI（D1 multi-run · D3=0 挂接 · D4 分布）。

层身份：
  D1 = 离线评测层（金标不得进生产 score / 在线放行）
  D3 = 硬闸，复用 SLO-02 同一出口（目标 violations=0）
  D4 = 观测周报（可发 / 需补丁 / 勿发）

n 与次数写死默认 --runs 3；n 小时不报总体方差。

用法:
  python scripts/slo_d1_d4_observability.py
  python scripts/slo_d1_d4_observability.py --runs 3 --json
  python scripts/slo_d1_d4_observability.py --from-gold-report reports/report-xxx.json
  python scripts/slo_d1_d4_observability.py --write-report reports/slo/d1_d4_week.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from freshlatch.slo_d1_d4_observability import (  # noqa: E402
    DEFAULT_MULTI_RUN_N,
    acceptance_ok,
    build_week_observability,
    format_week_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SLO-07 复验主业观测（D1/D3/D4）")
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_MULTI_RUN_N,
        help=f"离线 multi-run 遍数（默认 {DEFAULT_MULTI_RUN_N}；写死于文档）",
    )
    parser.add_argument(
        "--gold",
        default="data/eval/gold.json",
        help="金标路径（只读）",
    )
    parser.add_argument(
        "--from-gold-report",
        default=None,
        help="可选：既有 gold_run 报告 JSON，提取 D1（离线）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出组合 JSON（stdout）",
    )
    parser.add_argument(
        "--write-report",
        default=None,
        help="可选：写入人读周报到该路径",
    )
    args = parser.parse_args(argv)

    gold_run = None
    if args.from_gold_report:
        gold_run = json.loads(Path(args.from_gold_report).read_text(encoding="utf-8"))

    payload = build_week_observability(
        gold_path=Path(args.gold),
        n_runs=args.runs,
        gold_run_report=gold_run,
        repo_root=ROOT,
    )

    text = format_week_report(payload)
    if args.write_report:
        out = Path(args.write_report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(text, end="")

    ok, errors = acceptance_ok(payload)
    if not ok:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
