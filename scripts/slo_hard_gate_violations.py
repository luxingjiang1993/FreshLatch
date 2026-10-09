#!/usr/bin/env python3
"""SLO-02：硬闸不变量违例计数/清单 CLI（B6/B7/C5/D3/C3）。

验收层=硬闸机检/纪律层，不是实验乙成立格。
默认跑 Acceptance 探针并打印周报字段；退出码 0=探针完成且违例计数均为 0。

用法:
  python scripts/slo_hard_gate_violations.py
  python scripts/slo_hard_gate_violations.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from freshlatch.slo_hard_gate_violations import (  # noqa: E402
    HARD_GATE_IDS,
    format_report_text,
    run_acceptance_probes,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SLO-02 硬闸违例计数/清单")
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 week_fields JSON（stdout）",
    )
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="slo02-events-") as tmp:
        report = run_acceptance_probes(tmp_events_dir=Path(tmp))

    fields = report.week_fields()
    if args.json:
        print(json.dumps(fields, ensure_ascii=False, indent=2))
    else:
        print(format_report_text(report), end="")

    viol = fields["hard_gate_violation_counts"]
    bad = [sid for sid in HARD_GATE_IDS if viol.get(sid, 0) != 0]
    # B6/C3 须能观察到至少 1 次拒拦（Acceptance）
    if report.blocks("B6") < 1:
        print("FAIL: B6 拒拦计数 < 1", file=sys.stderr)
        return 1
    if report.blocks("C3") < 1:
        print("FAIL: C3 拒拦计数 < 1", file=sys.stderr)
        return 1
    if report.count("B7", "scan_pass") < 1 or report.violations("B7") != 0:
        print("FAIL: B7 扫描未通过", file=sys.stderr)
        return 1
    if bad:
        print(f"FAIL: 硬闸违例非零: {bad}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
