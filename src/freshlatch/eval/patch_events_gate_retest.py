"""门闩复测报告缝（可扔 · 不进主表 · 默认零 LLM）。

对齐 #438 / ``GATE-SEPARATION.md`` 口径：自然放行 / 自然误放 / 按 R 的固定 k 误放差；
文首标明不进主表、可扔、非甲；写明三条件是否过门。未过门不得建议激活。

本模块不发模型、不写 ``RESULT`` / ``RESULT-B`` 成立格、不改 ``PREREG-B`` 激活态。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from freshlatch.eval.patch_events_metrics import format_rate

_K_FLOOR = 10
_PRIMARY_ORDER = ("T-C", "T-B1", "T-B2")


def natural_release_claim_ids(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """决策为放行的 ``claim_id``，按升序。"""
    ids = [str(row["claim_id"]) for row in rows if row.get("decision") == "release"]
    return sorted(ids)


def arm_natural_stats(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """单臂自然放行数 / 自然误放数 / 自然误放率（放行 0 → 无定义）。"""
    releases = [row for row in rows if row.get("decision") == "release"]
    release_n = len(releases)
    false_n = sum(1 for row in releases if row.get("construction_gold") == "坏")
    false_rate: float | None = None if release_n == 0 else false_n / release_n
    return {
        "自然放行数": release_n,
        "自然误放数": false_n,
        "自然误放率": false_rate,
        "自然放行 claim_id": natural_release_claim_ids(rows),
    }


def gate_conditions(
    report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """门闩三条件：T−B1 差>0、T−B2 差>0、k≥10。未过不得建议激活。"""
    if report is None:
        return {
            "k": None,
            "t_b1_positive": False,
            "t_b2_positive": False,
            "k_ok": False,
            "passed": False,
            "comparisons": {},
        }
    k = report.get("k")
    k_ok = type(k) is int and k >= _K_FLOOR
    by_name: dict[str, Mapping[str, Any]] = {}
    for item in report.get("comparisons") or ():
        name = item.get("name")
        if isinstance(name, str):
            by_name[name] = item
    t_b1 = by_name.get("T-B1")
    t_b2 = by_name.get("T-B2")
    t_b1_pos = bool(t_b1 is not None and (t_b1.get("point") or 0) > 0)
    t_b2_pos = bool(t_b2 is not None and (t_b2.get("point") or 0) > 0)
    return {
        "k": k,
        "t_b1_positive": t_b1_pos,
        "t_b2_positive": t_b2_pos,
        "k_ok": k_ok,
        "passed": bool(t_b1_pos and t_b2_pos and k_ok),
        "comparisons": by_name,
    }


def render_gate_separation_markdown(
    *,
    arm_rows: Mapping[str, Sequence[Mapping[str, Any]]],
    primary_report: Mapping[str, Any] | None,
    source_note: str,
) -> str:
    """渲染可扔门闩复测报告。不写盘；调用方决定是否落 ``GATE-SEPARATION.md``。"""
    stats = {
        arm: arm_natural_stats(arm_rows.get(arm, ()))
        for arm in ("T", "B1", "B2", "C")
    }
    gate = gate_conditions(primary_report)
    lines: list[str] = [
        "# 仓外试分离门闩报告（可扔）",
        "",
        "> **不进主表 · 可扔 · 非甲**。本页不是冲甲成立证据。",
        f"> 数据源：{source_note}",
        "> 默认零 LLM；未过人授不得发模型。",
        "",
        "## 门闩三条件",
        "",
        f"- T 相对 B1 固定 k 误放差方向为正：{'是' if gate['t_b1_positive'] else '否'}",
        f"- T 相对 B2 固定 k 误放差方向为正：{'是' if gate['t_b2_positive'] else '否'}",
        f"- T 的 k ≥ {_K_FLOOR}：{'是' if gate['k_ok'] else '否'}（k={gate['k']!r}）",
        f"- **同时满足（过门）**：{'是' if gate['passed'] else '否'}",
        "",
    ]
    if gate["passed"]:
        lines.append("过门后才允许人写 `PREREG-B` 激活批注；本缝不自动激活。")
    else:
        lines.append("**未过门：不得建议激活 `PREREG-B`；不得开正式生成进主表。**")
    lines.extend(
        [
            "",
            "## 自然放行 / 自然误放",
            "",
            "| 臂 | 自然放行数 | 自然误放数 | 自然误放率 | 自然放行 claim_id |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for arm in ("T", "B1", "B2", "C"):
        item = stats[arm]
        ids = ", ".join(item["自然放行 claim_id"]) or "（空）"
        lines.append(
            f"| {arm} | {item['自然放行数']} | {item['自然误放数']} | "
            f"{format_rate(item['自然误放率'])} | `{ids}` |"
        )
    lines.extend(["", "## 按 R 的固定 k 误放差", ""])
    if primary_report is None:
        lines.append("（无 `compare_primary` 报告：主比较未产出。）")
    else:
        lines.append(f"k := T 自然放行数 = {primary_report.get('k')!r}")
        lines.append("")
        lines.append("| 比较 | 点估计 | 95% 下界 | 95% 上界 | 成立 |")
        lines.append("|---|---:|---:|---:|---|")
        by_name = gate["comparisons"]
        for name in _PRIMARY_ORDER:
            item = by_name.get(name)
            if item is None:
                lines.append(f"| {name} | — | — | — | — |")
                continue
            established = "成立" if item.get("established") is True else "不成立"
            lines.append(
                f"| {name} | {format_rate(item.get('point'))} | "
                f"{format_rate(item.get('ci95_low'))} | "
                f"{format_rate(item.get('ci95_high'))} | {established} |"
            )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 不进主表；可扔。",
            "- 不改成立定义；不金标进 score；不削弱 B1 凑差。",
            "- 不填冲甲 RESULT 成立格称甲。",
            "",
        ]
    )
    return "\n".join(lines)
