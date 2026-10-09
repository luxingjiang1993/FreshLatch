"""路线 C 仓外门闩（GATE-C · 可扔 · 非甲 · 不进主表 · 默认不发）。

三条件与选取 R 同构（k≥10 且 T−B1 / T−B2 固定 k 误放差方向为正）。
本模块测的是 **C 强制抄句机制**；**禁止**把 #479 ``GATE-K-PROBE`` 升格为 C 已过门。

默认：夹具驱动过/不过分支 + 落可扔报告；零 LLM；不激活 ``PREREG-C``；
不写 ``RESULT-C`` 成立格；不写 ``formal-generations-c`` 正式主跑。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from freshlatch.eval.patch_events_ablation import primary_comparison_rows
from freshlatch.eval.patch_events_arms import Decoding
from freshlatch.eval.patch_events_copy_constrained import run_arms_c
from freshlatch.eval.patch_events_formal_c import prereg_c_activated
from freshlatch.eval.patch_events_gate_retest import (
    arm_natural_stats,
    gate_conditions,
)
from freshlatch.eval.patch_events_metrics import (
    SEED,
    compare_primary,
    format_rate,
    named_streams,
)
from freshlatch.eval.patch_events_verify import verify_edit

_K_FLOOR = 10
_DEFAULT_REPORT = Path("docs/evidence/patch-events/GATE-C-FIXTURE.md")
_PROBE_B_REL = Path("docs/evidence/patch-events/GATE-K-PROBE.md")
_RESULT_C = Path("docs/evidence/patch-events/RESULT-C.md")
_FixtureMode = Literal["pass", "fail"]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def gate_c_pass_criteria() -> list[str]:
    """跑前写死的过门三条（与 PREREG-C / B 门闩同构）。"""
    return [
        f"T 自然放行 k ≥ {_K_FLOOR}",
        "T−B1 固定 k 误放差方向为正（点估计 > 0）",
        "T−B2 固定 k 误放差方向为正（点估计 > 0）",
    ]


def ban_promote_gate_k_probe_sentences() -> list[str]:
    """防火墙：#479 不得当 C 过门。"""
    return [
        "禁止把 #479 `GATE-K-PROBE`（或 `gate-k-probe-generations.jsonl`）升格为路线 C 已过门。",
        "B 探针绿只证明 B 机制曾过门；C 须对强制抄句机制另出可扔 GATE-C 报告。",
        f"B 报告路径 `{_PROBE_B_REL.as_posix()}` 不得抄进 `RESULT-C` 成立格，不得当作本页 `gate_passed=true` 的证据。",
    ]


def build_fixture_candidates(mode: _FixtureMode) -> tuple[list[dict[str, Any]], set[str]]:
    """夹具候选：强制抄句 + 同 after 下可分开 T/B1；不冒充真数据正式过门。

    pass：≥10 条正确且已绑定 → k 够；若干未绑定坏样 → B1 多误放；B2 全放行坏样。
    fail：仅少量正确绑定 → k<10（其它差方向仍可正，专测 k 门槛）。
    """
    ingested: set[str] = set()
    rows: list[dict[str, Any]] = []
    n_correct = 12 if mode == "pass" else 3
    for i in range(n_correct):
        eid = f"fix#p{i}@T1"
        ingested.add(eid)
        text = f"正确证据句-{i}"
        rows.append(
            {
                "claim_id": f"ok-{i:02d}",
                "before_text": f"旧文-{i}",
                "evidence_id": eid,
                "evidence_text": text,
                "edit_type": "数值",
                "construction_gold": "正确",
            }
        )
    # 未绑定坏样：T 拒 / B1 放 → 抬 T−B1
    for i in range(6):
        text = f"坏样未绑证据-{i}"
        rows.append(
            {
                "claim_id": f"bad-unbound-{i:02d}",
                "before_text": f"坏旧-{i}",
                "evidence_id": f"miss#p{i}@T1",
                "evidence_text": text,
                "edit_type": "数值",
                "construction_gold": "坏",
            }
        )
    return rows, ingested


def _inner_generator(request: Mapping[str, Any]) -> dict[str, Any]:
    """夹具 inner：C 自由改写；B2 claim/diff 放行取向；T 由 copy-constrained 硬抄覆盖。"""
    arm = str(request.get("arm") or "")
    phase = str(request.get("phase") or "")
    claim_id = str(request.get("claim_id") or "")
    if arm == "C" and phase == "rewrite":
        return {"after_text": f"无证改写-{claim_id}", "latency_ms": 0, "cost": 0}
    if arm == "B2" and phase == "claim":
        return {"claim_text": f"主张-{claim_id}", "latency_ms": 0, "cost": 0}
    if arm == "B2" and phase == "diff":
        # 故意与证据不同 → reverify 失败仍 release（B2 语义）
        return {
            "after_text": f"B2松放行-{claim_id}",
            "evidence_id": str(request.get("evidence_id") or ""),
            "latency_ms": 0,
            "cost": 0,
        }
    # T/B1 rewrite 若走到 inner（不应）：返回偏文，由硬契约覆盖
    return {
        "after_text": "应被强制抄覆盖",
        "evidence_id": str(request.get("evidence_id") or ""),
        "latency_ms": 0,
        "cost": 0,
    }


def run_gate_c_fixture(mode: _FixtureMode) -> dict[str, Any]:
    """跑夹具 → run_arms_c → compare_primary（R）→ gate_conditions。零 LLM。"""
    candidates, ingested = build_fixture_candidates(mode)
    arms = run_arms_c(
        candidates,
        generator=_inner_generator,
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
    gate = gate_conditions(primary)
    return {
        "mode": mode,
        "layer": "fixture",
        "arms": arms,
        "primary": primary,
        "gate": gate,
        "gate_passed": bool(gate.get("passed")),
        "n_candidates": len(candidates),
        "prereg_c_activated": prereg_c_activated(),
        "sent_model": False,
    }


def activation_advice(gate_passed: bool) -> str:
    if gate_passed:
        return (
            "夹具层 gate_passed=true：最多「可建议人审对 C 机制做真数据探针/激活评估」；"
            "**不**自行激活 `PREREG-C`；**不**把夹具绿写成甲或正式过门。"
        )
    return (
        "**gate_passed=false**：不得激活 `PREREG-C`；不得开正式 `formal-generations-c` 主跑进主表。"
    )


def render_gate_c_markdown(
    pack: Mapping[str, Any],
    *,
    code_pin: str,
) -> str:
    """可扔 GATE-C 报告正文。"""
    gate = pack.get("gate") or gate_conditions(None)
    primary = pack.get("primary")
    arms = pack.get("arms") or {}
    mode = pack.get("mode")
    lines: list[str] = [
        "# 路线 C 仓外门闩报告（GATE-C · 可扔）",
        "",
        "> **可扔 · 非甲 · 不进主表 · 不得升格为正式 RESULT-C。**",
        "> 本页只服务路线 C **强制抄句**机制的门闩复测/夹具。",
        "> 夹具或探针成功 ≠ 甲成立。最多建议人审；**不**自行激活 `PREREG-C`。",
        "",
        "## 防火墙（相对路线 B）",
        "",
    ]
    for sentence in ban_promote_gate_k_probe_sentences():
        lines.append(f"- {sentence}")
    lines.extend(
        [
            "",
            "## 探针/夹具协议（跑前写死 · 禁止 HARKing）",
            "",
            "### 过门判据（须同时）",
            "",
        ]
    )
    for i, item in enumerate(gate_c_pass_criteria(), start=1):
        lines.append(f"{i}. {item}")
    lines.extend(
        [
            "",
            "任一条不满足 → `gate_passed=false`；建议句必须写：**不得激活 PREREG-C**。",
            "",
            "### 机制约束（不得放松）",
            "",
            "- **选取**：R",
            "- **同 after**：T/B1 共用 after 再分叉",
            "- **强制抄句**：T after 硬契约 = evidence_text（非 B 软提示）",
            "- **T 闸**：绑定 ∧ 核验；不过 hard reject",
            "- **B1 闸**：仅核验；不过 hard reject",
            "- **禁止**：金标/评委进 score；放宽 reject 凑 k；复用 #479 当 C 过门",
            "",
            "## 本跑身份",
            "",
            f"- **层**：`{pack.get('layer')}`（fixture=夹具冒烟，非真数据正式过门）",
            f"- **夹具模式**：`{mode}`",
            f"- **代码针**：`{code_pin}`",
            f"- **是否发模型**：`{bool(pack.get('sent_model'))}`",
            f"- **PREREG-C 激活**：`{bool(pack.get('prereg_c_activated'))}`（本缝不得改）",
            f"- **候选 n**：{pack.get('n_candidates')!r}",
            "",
            "## 门闩三条件",
            "",
            f"- T 相对 B1 固定 k 误放差方向为正：{'是' if gate.get('t_b1_positive') else '否'}",
            f"- T 相对 B2 固定 k 误放差方向为正：{'是' if gate.get('t_b2_positive') else '否'}",
            f"- T 的 k ≥ {_K_FLOOR}：{'是' if gate.get('k_ok') else '否'}（k={gate.get('k')!r}）",
            f"- **同时满足（过门）**：{'是' if gate.get('passed') else '否'}",
            f"- **gate_passed** = `{bool(gate.get('passed'))}`",
            "",
            f"**激活建议**：{activation_advice(bool(gate.get('passed')))}",
            "",
            "## 自然放行 / 自然误放",
            "",
            "| 臂 | 自然放行数 | 自然误放数 | 自然误放率 |",
            "|---|---:|---:|---:|",
        ]
    )
    for arm in ("T", "B1", "B2", "C"):
        stats = arm_natural_stats(list(arms.get(arm) or ()))
        lines.append(
            f"| {arm} | {stats['自然放行数']} | {stats['自然误放数']} | "
            f"{format_rate(stats['自然误放率'])} |"
        )
    lines.extend(["", "## 按 R 的固定 k 误放差", ""])
    if primary is None:
        lines.append("（无 `compare_primary` 报告：主比较未产出。）")
    else:
        lines.append(f"k := T 自然放行数 = {primary.get('k')!r}")
        lines.append("")
        lines.append("| 比较 | 点估计 | 95% 下界 | 95% 上界 | 成立 |")
        lines.append("|---|---:|---:|---:|---|")
        by_name = {item.get("name"): item for item in (primary.get("comparisons") or [])}
        for name in ("T-C", "T-B1", "T-B2"):
            item = by_name.get(name) or {}
            est = "成立" if item.get("established") is True else "不成立"
            lines.append(
                f"| {name} | {format_rate(item.get('point'))} | "
                f"{format_rate(item.get('ci95_low'))} | "
                f"{format_rate(item.get('ci95_high'))} | {est} |"
            )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 本页不进 `RESULT-C` 成立格。",
            "- 不改 `PREREG-B` / `RESULT-B` / `formal-generations-b`。",
            "- 不保证甲；夹具绿 ≠ 真数据过门 ≠ 甲。",
            "",
        ]
    )
    return "\n".join(lines)


def write_gate_c_report(
    pack: Mapping[str, Any],
    *,
    code_pin: str,
    path: Path | None = None,
    root: Path | None = None,
) -> Path:
    base = _repo_root() if root is None else Path(root)
    out = base / _DEFAULT_REPORT if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    # 禁止误写 RESULT-C
    if out.resolve() == (base / _RESULT_C).resolve():
        raise RuntimeError("禁止把 GATE-C 报告写入 RESULT-C")
    text = render_gate_c_markdown(pack, code_pin=code_pin)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    """默认跑 fail+pass 夹具并写 GATE-C-FIXTURE.md（以 pass 包为主文，附 fail 摘要）。零 LLM。"""
    parser = argparse.ArgumentParser(prog="python -m freshlatch.eval.patch_events_gate_c")
    parser.add_argument(
        "--mode",
        choices=("pass", "fail", "both"),
        default="both",
        help="夹具分支；默认 both（测绿过/不过）",
    )
    parser.add_argument("--code-pin", default="local")
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="只打印 JSON，不写 GATE-C-FIXTURE.md",
    )
    args = parser.parse_args(argv)

    modes: Sequence[_FixtureMode]
    if args.mode == "both":
        modes = ("fail", "pass")
    else:
        modes = (args.mode,)  # type: ignore[assignment]

    results: dict[str, Any] = {}
    for mode in modes:
        results[mode] = run_gate_c_fixture(mode)

    # 主文用 pass（若有），否则 fail
    primary_mode: _FixtureMode = "pass" if "pass" in results else "fail"
    pack = results[primary_mode]
    summary = {
        "modes": {
            name: {
                "gate_passed": bool(item.get("gate_passed")),
                "k": (item.get("gate") or {}).get("k"),
                "t_b1_positive": (item.get("gate") or {}).get("t_b1_positive"),
                "t_b2_positive": (item.get("gate") or {}).get("t_b2_positive"),
            }
            for name, item in results.items()
        },
        "primary_report_mode": primary_mode,
        "ban_promote_479": ban_promote_gate_k_probe_sentences(),
        "prereg_c_activated": prereg_c_activated(),
        "sent_model": False,
    }
    sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")

    if not args.no_write:
        # 报告正文 = primary_mode；文末附另一分支摘要
        md = render_gate_c_markdown(pack, code_pin=args.code_pin)
        if len(results) > 1:
            other = "fail" if primary_mode == "pass" else "pass"
            other_pack = results[other]
            md += (
                "\n## 附录：对照夹具分支\n\n"
                f"- 模式 `{other}`：gate_passed=`{bool(other_pack.get('gate_passed'))}`；"
                f"k={(other_pack.get('gate') or {}).get('k')!r}\n"
            )
        out = _repo_root() / _DEFAULT_REPORT
        out.write_text(md, encoding="utf-8")
        sys.stdout.write(f"wrote {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
