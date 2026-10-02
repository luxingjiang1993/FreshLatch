"""I3 #250 · 闸分布一页：从轨迹 JSONL 聚合闸码/结果计数（CLI 或 MD）。

合成夹具 · 非真事故复盘。输出供面试「说清闸」，非产品主 UI。
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

GATE_CODE_RE = re.compile(r"\[闸打回:([A-Z0-9_]+)\]")
POLICY_CODE_RE = re.compile(r"政策拒[^：:]*[：:]?\s*|error_code[=: ]+([A-Z0-9_]+)")


def _iter_events(path: Path) -> list[dict]:
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        events.append(json.loads(line))
    return events


def collect_gate_distribution(events: list[dict]) -> dict:
    """从轨迹事件收集 status / 闸打回码计数。"""
    status_counts: Counter[str] = Counter()
    gate_codes: Counter[str] = Counter()
    event_types: Counter[str] = Counter()

    for ev in events:
        et = str(ev.get("type") or "")
        event_types[et] += 1
        if et in ("claim_result", "claim_final"):
            status = str(ev.get("status") or "")
            if status:
                status_counts[status] += 1
            reason = str(ev.get("reason") or "")
            for match in GATE_CODE_RE.finditer(reason):
                gate_codes[match.group(1)] += 1
            # 政策拒等旁路码：reason 内直接出现 ERR 形码
            if "POLICY_SOURCE_BAN" in reason:
                gate_codes["POLICY_SOURCE_BAN"] += 1
            if "AGENT_TIMEOUT" in reason:
                gate_codes["AGENT_TIMEOUT"] += 1
            if "SYNTHETIC_FALSE_GREEN" in reason:
                gate_codes["SYNTHETIC_FALSE_GREEN"] += 1
            code = ev.get("error_code") or ev.get("gate_error_code")
            if code:
                gate_codes[str(code)] += 1

    return {
        "status_counts": dict(sorted(status_counts.items())),
        "gate_codes": dict(sorted(gate_codes.items())),
        "event_types": dict(sorted(event_types.items())),
        "n_events": len(events),
    }


def render_gate_distribution_md(
    dist: dict,
    *,
    source: str = "",
    title: str = "闸分布一页",
) -> str:
    """渲染可读 MD（含闸码/结果计数）。"""
    lines = [
        f"# {title}",
        "",
        "> 合成夹具 · 非真事故复盘（I3 B′）。本页不是真生产事故复盘，不做 Memory/多 Agent。",
        "",
    ]
    if source:
        lines += [f"- 来源轨迹: `{source}`", ""]
    lines += ["## 主张终态 / 结果计数", ""]
    status = dist.get("status_counts") or {}
    if status:
        for k, v in status.items():
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("- （无 claim_result/claim_final status）")
    lines += ["", "## 闸码 / 旁路码计数", ""]
    codes = dist.get("gate_codes") or {}
    if codes:
        for k, v in codes.items():
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("- （本轨迹无闸打回码；计数栏仍可读）")
    lines += ["", "## 事件类型计数", ""]
    for k, v in (dist.get("event_types") or {}).items():
        lines.append(f"- `{k}`: {v}")
    lines += ["", f"- 事件总行数: {dist.get('n_events', 0)}", ""]
    return "\n".join(lines)


def render_gate_distribution(
    trajectory: str | Path,
    *,
    out_md: str | Path | None = None,
) -> str:
    """读轨迹 → MD 字符串；若 out_md 给定则落盘。"""
    path = Path(trajectory)
    dist = collect_gate_distribution(_iter_events(path))
    md = render_gate_distribution_md(dist, source=str(path))
    if out_md is not None:
        out = Path(out_md)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
    return md


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m freshlatch.i3_gate_dist",
        description="I3 闸分布一页（合成夹具 · 非真事故复盘）",
    )
    ap.add_argument("trajectory", help="轨迹 JSONL 路径")
    ap.add_argument("--out", default="", help="可选：写出 MD 路径")
    args = ap.parse_args(argv)
    md = render_gate_distribution(
        args.trajectory,
        out_md=args.out or None,
    )
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
