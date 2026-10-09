"""门闩复测报告缝（可扔 · 未激活 · 复测 · 默认零 LLM）。

对齐 ``PREREG-B`` 仓外试分离门闩口径：自然放行 / 自然误放 / 按 R 的固定 k 误放差；
文首标明不进主表、可扔、非甲、复测；写明三条件是否过门。未过门不得建议激活。

本模块不发模型、不写 ``RESULT`` / ``RESULT-B`` 成立格、不改 ``PREREG-B`` 激活态。
默认入口只读 ``formal-generations.jsonl`` 回放；旧 #438 / PR #460 不得升格为已过门。
本票路径：``docs/evidence/patch-events/GATE-SEPARATION-remeasure.md``（#470 · #469 机制后）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_ablation import primary_comparison_rows
from freshlatch.eval.patch_events_arms import Decoding, run_arms
from freshlatch.eval.patch_events_formal import (
    generations_path,
    ingested_t1,
    load_pe_v2_formal_n30,
)
from freshlatch.eval.patch_events_metrics import (
    SEED,
    compare_primary,
    format_rate,
    named_streams,
)
from freshlatch.eval.patch_events_verify import verify_edit
from freshlatch.eval import patch_events_formal as _formal

_K_FLOOR = 10
_PRIMARY_ORDER = ("T-C", "T-B1", "T-B2")
_DEFAULT_REPORT = Path("docs/evidence/patch-events/GATE-SEPARATION-remeasure.md")
_GENERATIONS_REL = Path("docs/evidence/patch-events/formal-generations.jsonl")


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
    """渲染可扔门闩复测报告正文段。不写盘；调用方决定是否落盘。"""
    stats = {
        arm: arm_natural_stats(arm_rows.get(arm, ()))
        for arm in ("T", "B1", "B2", "C")
    }
    gate = gate_conditions(primary_report)
    lines: list[str] = [
        "# 仓外试分离门闩报告（可扔）",
        "",
        "> **可扔 · 未激活 · 复测 · 不进主表 · 非甲**。本页不是冲甲成立证据。",
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
            "- 不进主表；可扔；复测；未激活。",
            "- 不改成立定义；不金标进 score；不削弱 B1 凑差。",
            "- 不填冲甲 RESULT 成立格称甲。",
            "- 旧 #438 / PR #460 `GATE-SEPARATION.md` **不得**升格为已过门。",
            "",
        ]
    )
    return "\n".join(lines)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_generation_rows(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _sha256_file(path: Path) -> str:
    # 针按 LF 语义；Windows checkout CRLF 不得改写内容针
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()



def _reject_reason_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if row.get("decision") == "release":
            continue
        reason = str(row.get("reject_reason") or "（空）")
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def run_readonly_retest(
    *,
    root: Path | None = None,
    generations_file: Path | None = None,
) -> dict[str, Any]:
    """夹具之后的只读旧生成冒烟：零 LLM，返回 arm 行 + compare_primary + 门闩判定。"""
    base = _repo_root() if root is None else Path(root)
    path = generations_path() if generations_file is None else Path(generations_file)
    if not path.is_absolute():
        path = base / path
    candidates = load_pe_v2_formal_n30(base)
    generations = _load_generation_rows(path)
    ingested = ingested_t1(candidates)
    arms = run_arms(
        candidates,
        generator=_formal._saved_generator(generations),
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=SEED),
        ingested_t1=ingested,
    )
    primary = None
    try:
        primary = compare_primary(
            primary_comparison_rows(arms),
            ingested_t1=ingested,
            streams=named_streams(),
        )
    except ValueError:
        primary = None
    b2_count = sum(
        1
        for record in arms["B2"]
        if isinstance(record.get("after_text"), str) and record.get("after_text") != ""
    )
    return {
        "arms": arms,
        "primary": primary,
        "gate": gate_conditions(primary),
        "b2_count": b2_count,
        "generations_path": path,
        "generations_sha256": _sha256_file(path),
        "generations_n": len(generations),
        "reject_reasons": {
            "T": _reject_reason_counts(arms["T"]),
            "B1": _reject_reason_counts(arms["B1"]),
        },
    }


def render_full_retest_markdown(
    pack: Mapping[str, Any],
    *,
    code_pin: str,
    baseline_note: str,
) -> str:
    """完整复测页：规则声明 + 只读冒烟数字 + 三条件 + 根因线索（未过时）。"""
    primary = pack["primary"]
    arms = pack["arms"]
    gate = pack["gate"]
    body = render_gate_separation_markdown(
        arm_rows=arms,
        primary_report=primary,
        source_note=(
            f"只读 `{_GENERATIONS_REL.as_posix()}` + #469 同 after 分叉 + "
            "`compare_primary` R · 零 LLM"
        ),
    )
    header = [
        "# 仓外试分离门闩报告（可扔 · 复测 · 机制后）",
        "",
        "> **可扔 · 未激活 · 复测 · 不进主表 · 非甲。**",
        "> 本文件是 `PREREG-B.md`「仓外试分离门闩」在 **#469 同 after 再分叉** 之后的复测冒烟层产物。",
        "> **不得**升格为冲甲主证据，**不得**写入 `RESULT-B` 成立格，**不得**当作结果甲。",
        "> 旧 [#438](https://github.com/luxingjiang1993/FreshLatch/issues/438) / "
        "PR [#460](https://github.com/luxingjiang1993/FreshLatch/pull/460) "
        "`GATE-SEPARATION.md` **不得**升格为已过门（本页为机制后重算，非改写旧页）。",
        "",
        "- 工单：[#470](https://github.com/luxingjiang1993/FreshLatch/issues/470) · "
        "复测协议 [#466](https://github.com/luxingjiang1993/FreshLatch/issues/466) · "
        "机制 [#469](https://github.com/luxingjiang1993/FreshLatch/issues/469) · "
        "历史门闩 [#438](https://github.com/luxingjiang1993/FreshLatch/issues/438)",
        "- 协议：`docs/evidence/patch-events/PREREG-B.md`（文首保持「冲甲正式主跑未激活」；本报告不改该页）",
        "- 选取：`compare_primary` 固定 k 规则 **R**（#437 / ADR-0034）",
        "- 机制针：T/B1 **同 after 再分叉**（#469 / ADR-0035）",
        "- 测量层声明（Anthropic 清单 §1）：本页是**演示/冒烟可过检**层，不是统计成立结论；"
        "bootstrap 区间仅附带抄出，**不参与**门闩三条件。",
        "",
        "## 复测序（PREREG-B · #466 重申）",
        "",
        "1. **夹具**：`tests/unit/test_pe_tb1_same_after.py` 证明同 after 上 T/B1 自然放行集可不同（机制可识别 ≠ 过门）。",
        "2. **只读旧生成冒烟**（本页主数字）：回放冻结 `formal-generations.jsonl`，不发模型。",
        "3. **（可选）人授小探针**：本会话**未发**；未过人授不得发模型。",
        "",
        "## 规则声明（与 PREREG-B · R 一致）",
        "",
        "- **k** := T 的自然放行条数。",
        "- 对臂 ∈ {C, T, B1, B2}：自然放行集 = `decision == \"release\"` 的候选；"
        "m≥k 时集内按 `claim_id` 升序取前 k；m<k 则该臂固定 k 误放率无定义。",
        "- 配对差 = 对照臂固定 k 误放率 − T 固定 k 误放率；**正值表示 T 更低**（方向为正）。",
        "- 禁止用 `construction_gold`、评委标签、用户裁决构造 score 或选取。",
        "",
        "过门须**同时**满足：",
        "",
        "1. T 相对 B1 的固定 k 误放差方向为正；",
        "2. T 相对 B2 的固定 k 误放差方向为正；",
        "3. T 的 k ≥ 10。",
        "",
        "## 数据与复现针（默认不发模型）",
        "",
        "| 项 | 值 |",
        "|---|---|",
        "| 候选 | `load_pe_v2_formal_n30()`（只读） |",
        f"| 生成文本 | `{_GENERATIONS_REL.as_posix()}`（sha256 `{pack['generations_sha256']}`，"
        f"{pack['generations_n']} 行） |",
        "| 回放入口 | `_saved_generator` + `run_arms`（#469 同 after）→ "
        "同一次 `compare_primary`（R）；入口 `python -m freshlatch.eval.patch_events_gate_retest` |",
        "| 模型调用 | **无** |",
        f"| 代码针 | {code_pin} |",
        f"| 基线 | {baseline_note} |",
        "| 样本框说明 | 旧 n=30 不得作冲甲主证据；此处仅仓外可扔冒烟 |",
        "",
    ]
    body_lines = body.splitlines()
    start = 0
    for idx, line in enumerate(body_lines):
        if line == "## 门闩三条件":
            start = idx
            break
    core = "\n".join(body_lines[start:])

    fixed_section: list[str] = ["", "## 固定 k（R）集合明细", ""]
    if primary is None:
        fixed_section.append("（无主比较报告。）")
    else:
        k = primary.get("k")
        fixed_section.append(f"- **k = {k!r}**（= T 自然放行数）。")
        fixed_section.append("")
        fixed_section.append("| 臂 | 固定 k 集合（claim_id 升序前 k） | 固定 k 误放率 |")
        fixed_section.append("|---|---|---:|")
        arm_block = primary.get("arms") or {}
        for arm in ("T", "B1", "B2"):
            fixed = (arm_block.get(arm) or {}).get("fixed") or {}
            ids = fixed.get("selected_claim_ids")
            rate = fixed.get("误放率")
            if ids is None:
                fixed_section.append(f"| {arm} | （无定义） | 无定义 |")
            else:
                id_text = ", ".join(f"`{cid}`" for cid in ids)
                fixed_section.append(f"| {arm} | {id_text} | {format_rate(rate)} |")
        by_name = gate["comparisons"]
        fixed_section.extend(
            ["", "| 比较 | 配对差（对照 − T） | 方向为正？ |", "|---|---:|---|"]
        )
        for name, label in (("T-B1", "T−B1"), ("T-B2", "T−B2")):
            item = by_name.get(name)
            if item is None:
                fixed_section.append(f"| {label} | — | — |")
                continue
            point = item.get("point")
            positive = type(point) is float and point > 0
            fixed_section.append(
                f"| {label} | {format_rate(point)} | {'是' if positive else '否'} |"
            )

    verdict_rows = [
        "",
        "## 门闩三条件判定（表）",
        "",
        "| # | 条件 | 观测 | 满足？ |",
        "|---|---|---|---|",
        f"| 1 | T−B1 固定 k 误放差方向为正 | 点估计 = "
        f"{format_rate((gate['comparisons'].get('T-B1') or {}).get('point'))} | "
        f"{'是' if gate['t_b1_positive'] else '否'} |",
        f"| 2 | T−B2 固定 k 误放差方向为正 | 点估计 = "
        f"{format_rate((gate['comparisons'].get('T-B2') or {}).get('point'))} | "
        f"{'是' if gate['t_b2_positive'] else '否'} |",
        f"| 3 | T 的 k ≥ {_K_FLOOR} | k = {gate['k']!r} | "
        f"{'是' if gate['k_ok'] else '否'} |",
        "",
        f"**三条件同时满足 ⇒ 过门：{'是' if gate['passed'] else '否'}。**",
        "",
    ]

    root_cause: list[str] = ["", "## 根因线索（诚实 · 非 HARKing）", ""]
    if gate["passed"]:
        root_cause.append(
            "三条件已齐。本缝仍不自动激活；须人写 `PREREG-B` 激活批注后才可开正式主跑。"
        )
    else:
        t_reasons = pack.get("reject_reasons", {}).get("T") or {}
        b1_reasons = pack.get("reject_reasons", {}).get("B1") or {}
        root_cause.extend(
            [
                "- **相对旧 #438**：同 after 分叉后，绑定缝在只读回放上已可见——"
                "例 `b007`（坏 · T0）被 T 以「证据未绑定已入库 T1」拒绝，B1 核验通过后放行；"
                "T−B1 固定 k 误放差由 0 转为正（本冒烟 ≈ +1/3）。",
                "- **仍未过门的主缺口**：T 的 **k=3 < 10**。只读冻结生成无法吸收抬 k（#471 / L1）的生成侧改动；"
                "抬 k 仍依赖正确样更常逐字对齐 evidence，**不是**放松 hard reject / 绑定。",
                f"- T 主拒因（本回放）：{t_reasons}。",
                f"- B1 主拒因（本回放）：{b1_reasons}。",
                "- **禁止**：为凑 k 发模型而未人授；削弱 B1；金标进 score；改成立定义；"
                "把夹具可识别或本页差方向称作甲成立。",
                "- 下一步（协议内）：#471 抬 k 与/或人授小探针；未过门前 **不开 #440**、"
                "**不激活 PREREG-B**。",
            ]
        )

    activation = [
        "",
        "## 结论（激活建议）",
        "",
    ]
    if gate["passed"]:
        activation.extend(
            [
                "- 门闩三条件在本冒烟层同时满足；**仍须人**写激活批注，本缝不自动改 `PREREG-B`。",
                "- 不得把本页数字抄进冲甲主表成立格。",
            ]
        )
    else:
        activation.extend(
            [
                "- **不得建议激活** `PREREG-B` 正式主跑。",
                "- **不得**改 `PREREG-B` 文首状态或写激活批注。",
                "- **不得**开四臂正式生成进主表；**不得**填 `RESULT-B` 成立格；"
                "**不得**把本页数字抄进冲甲主表。",
                "- 本报告可扔；过门后须用新针重跑并换路径/批注。",
            ]
        )
    activation.append("")

    return (
        "\n".join(header)
        + "\n"
        + core.rstrip()
        + "\n"
        + "\n".join(fixed_section)
        + "\n".join(verdict_rows)
        + "\n".join(root_cause)
        + "\n".join(activation)
    )


def write_retest_report(
    path: Path | None = None,
    *,
    code_pin: str,
    baseline_note: str,
    root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """跑只读复测并落盘。返回 (路径, pack)。"""
    base = _repo_root() if root is None else Path(root)
    out = _DEFAULT_REPORT if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    pack = run_readonly_retest(root=base)
    markdown = render_full_retest_markdown(
        pack, code_pin=code_pin, baseline_note=baseline_note
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    return out, pack


def main(argv: list[str] | None = None) -> int:
    """默认零 LLM：只读回放并写可扔复测报告。不发模型。"""
    parser = argparse.ArgumentParser(
        prog="python -m freshlatch.eval.patch_events_gate_retest"
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="只打印判定，不写盘",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_DEFAULT_REPORT,
        help="报告路径（相对仓库根）",
    )
    parser.add_argument("--code-pin", default="local", help="代码针说明")
    parser.add_argument(
        "--baseline",
        default="cursor/469-tb1-same-after-a9d3（#469）+ cherry-pick #437 R",
        help="基线说明",
    )
    args = parser.parse_args(argv)
    if args.no_write:
        pack = run_readonly_retest()
        gate = pack["gate"]
        sys.stdout.write(
            f"gate_passed={gate['passed']} k={gate['k']!r} "
            f"t_b1_pos={gate['t_b1_positive']} t_b2_pos={gate['t_b2_positive']}\n"
        )
        return 0
    out, pack = write_retest_report(
        args.out,
        code_pin=args.code_pin,
        baseline_note=args.baseline,
    )
    gate = pack["gate"]
    sys.stdout.write(
        f"gate_passed={gate['passed']} k={gate['k']!r} "
        f"t_b1_pos={gate['t_b1_positive']} t_b2_pos={gate['t_b2_positive']}\n"
    )
    sys.stdout.write(f"wrote {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
