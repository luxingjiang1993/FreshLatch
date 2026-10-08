"""仓外抬 k 探针（可扔 · 非甲 · 不进主表 · 默认不发模型）。

跑前写死过门判据，禁止 HARKing。本模块最多把门闩打到「可建议人审激活」；
不激活 ``PREREG-B``，不开 #440 正式主跑，不写 ``RESULT-B`` 成立格。

默认：落协议报告 + 只读冻结对照 + 停在可发送边界（等待授权发模型）。
``--authorize-send``：仅在人/编排器本会话明文授权后才向 ``DEFAULT_MODEL`` 发送；
旁路写入 ``gate-k-probe-generations.jsonl``，不得污染 ``formal-generations.jsonl``。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_ablation import primary_comparison_rows
from freshlatch.eval.patch_events_arms import Decoding, run_arms
from freshlatch.eval.patch_events_formal import (
    generations_path,
    ingested_t1,
    load_pe_v2_formal_n30,
)
from freshlatch.eval.patch_events_gate_retest import (
    arm_natural_stats,
    gate_conditions,
    run_readonly_retest,
)
from freshlatch.eval.patch_events_metrics import (
    SEED,
    compare_primary,
    format_rate,
    named_streams,
)
from freshlatch.eval.patch_events_send import (
    append_b2_diffs,
    append_sent,
    dispatch_prompt,
    live_chat,
    written_keys,
)
from freshlatch.eval.patch_events_verify import verify_edit
from freshlatch.eval import patch_events_formal as _formal
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_K_FLOOR = 10
_PRIMARY_ORDER = ("T-C", "T-B1", "T-B2")
_DEFAULT_REPORT = Path("docs/evidence/patch-events/GATE-K-PROBE.md")
_PROBE_GENERATIONS_REL = Path("docs/evidence/patch-events/gate-k-probe-generations.jsonl")
_FORMAL_GENERATIONS_REL = Path("docs/evidence/patch-events/formal-generations.jsonl")
# 探针发送：同 after 下 B1 不另发 rewrite；C/T rewrite + B2 claim，再补 B2 diff。
_PROBE_SEND: tuple[tuple[str, str], ...] = (
    ("C", "rewrite"),
    ("T", "rewrite"),
    ("B2", "claim"),
)
_AWAITING = "等待授权发模型"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def probe_claim_ids(rows: Sequence[Mapping[str, Any]] | None = None) -> list[str]:
    """探针名单针：pe_v2 正式 n=30 的 claim_id 顺序（与正式同构造配额）。"""
    sample = list(rows) if rows is not None else load_pe_v2_formal_n30()
    return [str(row["claim_id"]) for row in sample]


def probe_requests(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """仓外探针发送队列。跳过 B1 rewrite（#469 同 after：以 T 生成一次）。"""
    requests: list[dict[str, Any]] = []
    for row in rows:
        for arm, phase in _PROBE_SEND:
            requests.append(
                {
                    "arm": arm,
                    "phase": phase,
                    "claim_id": row["claim_id"],
                    "before_text": row["before_text"],
                    "evidence_text": row["evidence_text"],
                }
            )
    return requests


def decoding_pin() -> dict[str, Any]:
    """解码针：显式记录 model / temperature；API 层是否传 seed 如实写。"""
    entry = MODEL_REGISTRY["default_llm"]
    return {
        "model": DEFAULT_MODEL,
        "registry_model": entry.model,
        "temperature": entry.temperature,
        "decoding_seed": SEED,
        "api_seed": None,
        "api_seed_note": "live_chat / DecodingParams 未传 seed；Decoding.seed 仅供 run_arms 作废检查",
    }


def mechanism_pins() -> dict[str, str]:
    """机制缝针（本分支须齐）。"""
    return {
        "选取": "R（#437 / PR #458）",
        "同 after": "T/B1 共用 T rewrite after，再分叉（#469 / PR #476）",
        "生成对齐": "T/B1 提示要求 after 与 evidence 去空白逐字相同（#471 / PR #474）",
        "T 闸": "绑定 ∧ 核验；不过 hard reject",
        "B1 闸": "仅核验；不过 hard reject",
        "禁止": "金标/评委/用户裁决进 score；改 verify_edit 或放宽 reject 凑 k；加 n 伪抬 k",
    }


def gate_pass_criteria() -> list[str]:
    """跑前写死的过门判据（须同时）。"""
    return [
        f"T 自然放行 k ≥ {_K_FLOOR}",
        "T−B1 固定 k 误放差方向为正（点估计 > 0）",
        "T−B2 固定 k 误放差方向为正（点估计 > 0）",
    ]


def summary_table(
    arm_rows: Mapping[str, Sequence[Mapping[str, Any]]],
    primary: Mapping[str, Any] | None,
    gate: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """交付用表行：各臂自然放行/自然误放/固定 k 误放 + 差 + gate_passed。"""
    rows: list[dict[str, Any]] = []
    arm_block = (primary or {}).get("arms") or {}
    for arm in ("T", "B1", "B2", "C"):
        nat = arm_natural_stats(arm_rows.get(arm, ()))
        fixed = (arm_block.get(arm) or {}).get("fixed") or {}
        rows.append(
            {
                "臂": arm,
                "自然放行": nat["自然放行数"],
                "自然误放": nat["自然误放数"],
                "固定k误放": fixed.get("误放率"),
            }
        )
    by_name = gate.get("comparisons") or {}
    return [
        {
            "rows": rows,
            "k": gate.get("k"),
            "T-B1": (by_name.get("T-B1") or {}).get("point"),
            "T-B2": (by_name.get("T-B2") or {}).get("point"),
            "gate_passed": bool(gate.get("passed")),
        }
    ]


def run_probe_recompute(
    *,
    root: Path | None = None,
    generations_file: Path | None = None,
) -> dict[str, Any]:
    """只读旁路探针生成 → run_arms（同 after）→ compare_primary（R）→ 门闩判定。零 LLM。"""
    base = _repo_root() if root is None else Path(root)
    path = (
        base / _PROBE_GENERATIONS_REL
        if generations_file is None
        else Path(generations_file)
    )
    if not path.is_absolute():
        path = base / path
    if not path.is_file():
        return {
            "status": "no_probe_generations",
            "arms": None,
            "primary": None,
            "gate": gate_conditions(None),
            "generations_path": path,
            "generations_sha256": None,
            "generations_n": 0,
        }
    text = path.read_text(encoding="utf-8")
    generations = [json.loads(line) for line in text.splitlines() if line.strip()]
    candidates = load_pe_v2_formal_n30(base)
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
    gate = gate_conditions(primary)
    return {
        "status": "recomputed",
        "arms": arms,
        "primary": primary,
        "gate": gate,
        "generations_path": path,
        "generations_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "generations_n": len(generations),
        "table": summary_table(arms, primary, gate),
    }


def send_probe_generations(
    *,
    root: Path | None = None,
    generations_file: Path | None = None,
    chat: Callable[..., Any] = live_chat,
) -> dict[str, Any]:
    """向旁路 jsonl 发送探针生成。调用方须已确认明文授权。"""
    base = _repo_root() if root is None else Path(root)
    path = (
        base / _PROBE_GENERATIONS_REL
        if generations_file is None
        else Path(generations_file)
    )
    if not path.is_absolute():
        path = base / path
    # 防火墙：禁止写入正式 formal-generations.jsonl
    formal = generations_path()
    if path.resolve() == formal.resolve():
        raise RuntimeError("探针禁止写入 formal-generations.jsonl")
    rows = load_pe_v2_formal_n30(base)
    gaps = _formal.live_gaps()
    if gaps:
        return {"status": "live_gaps", "gaps": list(gaps), "sent": 0, "path": path}
    done = written_keys(path)
    sent = 0
    for request in probe_requests(rows):
        key = (str(request["claim_id"]), str(request["arm"]), str(request["phase"]))
        if key in done:
            continue
        result = dispatch_prompt(request, chat)
        if append_sent(path, result):
            done.add(key)
            sent += 1
    b2_added = append_b2_diffs(rows, path, chat)
    return {
        "status": "sent",
        "sent": sent,
        "b2_diff_added": b2_added,
        "path": path,
        "n": len(rows),
        "claim_ids": probe_claim_ids(rows),
        "decoding": decoding_pin(),
    }


def _md_table_block(table_pack: Mapping[str, Any] | None, *, title: str) -> list[str]:
    lines = [f"## {title}", ""]
    if table_pack is None:
        lines.extend(["（未跑 / 无旁路生成。）", ""])
        return lines
    item = table_pack["table"][0] if table_pack.get("table") else None
    if item is None and table_pack.get("arms") is not None:
        item = summary_table(
            table_pack["arms"], table_pack.get("primary"), table_pack["gate"]
        )[0]
    if item is None:
        lines.extend(["（无表。）", ""])
        return lines
    lines.extend(
        [
            "| 臂 | 自然放行 | 自然误放 | 固定 k 误放 |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in item["rows"]:
        lines.append(
            f"| {row['臂']} | {row['自然放行']} | {row['自然误放']} | "
            f"{format_rate(row['固定k误放'])} |"
        )
    lines.extend(
        [
            "",
            f"- **k** = {item['k']!r}",
            f"- **T−B1** 固定 k 误放差 = {format_rate(item['T-B1'])}",
            f"- **T−B2** 固定 k 误放差 = {format_rate(item['T-B2'])}",
            f"- **gate_passed** = `{item['gate_passed']}`",
            "",
        ]
    )
    return lines


def render_gate_k_probe_markdown(
    *,
    code_pin: str,
    baseline_note: str,
    authorize_send: bool,
    send_result: Mapping[str, Any] | None,
    probe_pack: Mapping[str, Any] | None,
    readonly_pack: Mapping[str, Any] | None,
) -> str:
    """渲染可扔抬 k 探针报告。文首标明可扔·非甲·不进主表。"""
    claim_ids = probe_claim_ids()
    pin = decoding_pin()
    mech = mechanism_pins()
    criteria = gate_pass_criteria()
    live_ran = bool(authorize_send and send_result and send_result.get("status") == "sent")
    recomputed = bool(probe_pack and probe_pack.get("status") == "recomputed")
    gate = (
        probe_pack["gate"]
        if recomputed
        else gate_conditions(None)
    )
    # 无探针生成时 gate_passed 必须为 false
    if not recomputed:
        gate = {
            **gate,
            "passed": False,
            "k_ok": False,
            "t_b1_positive": False,
            "t_b2_positive": False,
        }

    lines: list[str] = [
        "# 仓外抬 k 探针报告（可扔）",
        "",
        "> **可扔 · 非甲 · 不进主表 · 不得升格为正式 RESULT-B。**",
        "> 本页是机制缝（选取 R + T/B1 同 after + 生成对齐）齐备后的**仓外抬 k 探针**旁路产物。",
        "> 本会话成功 ≠ 甲成立。最多「可建议人审激活」；**不**自行激活 `PREREG-B`，**不**开 #440。",
        "> 旧 #438/#460/#470/#477 门闩页与夹具绿 **不得**升格为已过门。",
        "",
        "## 探针协议（跑前写死 · 禁止 HARKing）",
        "",
        "### 过门判据（须同时）",
        "",
    ]
    for idx, item in enumerate(criteria, start=1):
        lines.append(f"{idx}. {item}")
    lines.extend(
        [
            "",
            "任一条不满足 → `gate_passed=false`；建议句必须写："
            "**不得激活 PREREG-B；不得开 #440**。",
            "",
            "### 机制约束（不得放松）",
            "",
        ]
    )
    for key, value in mech.items():
        lines.append(f"- **{key}**：{value}")
    lines.extend(
        [
            "",
            "### 样本针",
            "",
            f"- **n** = {len(claim_ids)}（`load_pe_v2_formal_n30()`，与正式同构造配额）",
            f"- **claim_id 顺序**：`{','.join(claim_ids)}`",
            "- 旁路生成：`" + _PROBE_GENERATIONS_REL.as_posix() + "`（禁止写入 `"
            + _FORMAL_GENERATIONS_REL.as_posix() + "`）",
            "",
            "### 解码针",
            "",
            f"- model = `{pin['model']}`（登记 `{pin['registry_model']}`）",
            f"- temperature = `{pin['temperature']}`",
            f"- Decoding.seed = `{pin['decoding_seed']}`（run_arms 作废检查）",
            f"- API seed = `{pin['api_seed']}` — {pin['api_seed_note']}",
            "",
            "## 基线与代码针",
            "",
            f"- **代码针**：{code_pin}",
            f"- **基线**：{baseline_note}",
            "- 机制缝：#458（R）+ #476（同 after）+ #474（生成对齐）已合入本分支",
            "",
            "## 发送状态",
            "",
        ]
    )
    if not authorize_send:
        lines.extend(
            [
                f"- **本会话未获明文「授权发模型」** → 停在可发送边界。",
                f"- 状态：**{_AWAITING}**",
                "- 入口已搭好：见文末「复算 / 发送入口」。",
                "",
            ]
        )
    elif send_result and send_result.get("status") == "live_gaps":
        lines.extend(
            [
                "- 授权标志已开，但 `live_gaps` 非空，未发送。",
                f"- gaps：{send_result.get('gaps')!r}",
                "",
            ]
        )
    elif live_ran:
        lines.extend(
            [
                "- 已按授权向旁路路径发送探针生成。",
                f"- sent={send_result.get('sent')!r}；"
                f"b2_diff_added={send_result.get('b2_diff_added')!r}",
                f"- path=`{send_result.get('path')}`",
                "",
            ]
        )
    else:
        lines.extend(["- 授权标志已开，但本次未执行发送或无新发送。", ""])

    lines.extend(_md_table_block(probe_pack if recomputed else None, title="探针主表（旁路生成）"))

    # 只读冻结对照：明示非探针、非过门证据
    if readonly_pack is not None:
        lines.extend(
            [
                "## 只读冻结对照（非探针 · 非过门证据）",
                "",
                "> 回放 `"
                + _FORMAL_GENERATIONS_REL.as_posix()
                + "`：旧生成**吃不到** #471 对齐提示；仅作机制后差方向对照。",
                "> **不得**把本对照升格为抬 k 过门。",
                "",
            ]
        )
        ro_gate = readonly_pack["gate"]
        ro_table = {
            "arms": readonly_pack["arms"],
            "primary": readonly_pack["primary"],
            "gate": ro_gate,
            "table": summary_table(
                readonly_pack["arms"], readonly_pack["primary"], ro_gate
            ),
        }
        lines.extend(_md_table_block(ro_table, title="对照表（冻结 formal-generations）")[2:])

    by_name = gate.get("comparisons") or {}
    t_b1_point = None
    t_b2_point = None
    t_b1_item = by_name.get("T-B1")
    t_b2_item = by_name.get("T-B2")
    if isinstance(t_b1_item, Mapping):
        t_b1_point = t_b1_item.get("point")
    if isinstance(t_b2_item, Mapping):
        t_b2_point = t_b2_item.get("point")
    lines.extend(
        [
            "## 门闩三条件判定（探针主路径）",
            "",
            "| # | 条件 | 观测 | 满足？ |",
            "|---|---|---|---|",
            f"| 1 | T 自然放行 k ≥ {_K_FLOOR} | k = {gate.get('k')!r} | "
            f"{'是' if gate.get('k_ok') else '否'} |",
            f"| 2 | T−B1 差方向为正 | 点估计 = {format_rate(t_b1_point)} | "
            f"{'是' if gate.get('t_b1_positive') else '否'} |",
            f"| 3 | T−B2 差方向为正 | 点估计 = {format_rate(t_b2_point)} | "
            f"{'是' if gate.get('t_b2_positive') else '否'} |",
            "",
            f"**gate_passed = `{bool(gate.get('passed'))}`**",
            "",
            "## 结论与建议",
            "",
        ]
    )
    if gate.get("passed"):
        lines.extend(
            [
                "### 可建议人审激活（清单 · 本缝仍不激活）",
                "",
                "1. 人审本页数字与代码针 / 名单针 / 解码针。",
                "2. 人写 `PREREG-B` 激活批注（日期、仓库针、本报告路径）。",
                "3. 人决定是否开 #440 正式主跑。",
                "4. **本 Cloud Agent 不激活、不正式主跑、不填 RESULT-B 成立格。**",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- **gate_passed=false**。",
                "- **不得激活 PREREG-B；不得开 #440。**",
                "- 冲甲本波仍停在丁；禁止改甲定义续命。",
                "- 不得把夹具绿或旧 #460/#477 升格为已过门。",
                "",
            ]
        )
        if not authorize_send:
            lines.append(f"- 本会话：**{_AWAITING}**（入口见下）。")
            lines.append("")

    lines.extend(
        [
            "## 复算 / 发送入口（零歧义）",
            "",
            "```bash",
            "# 默认：写本报告 + 只读对照 + 不发模型（停在可发送边界）",
            "PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_k_probe",
            "",
            "# 只打印判定，不写盘",
            "PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_k_probe --no-write",
            "",
            "# 若旁路生成已存在：只复算（零 LLM）",
            "PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_k_probe --recompute-only",
            "",
            "# 仅在人/编排器本会话明文「授权发模型」之后：",
            "PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_k_probe --authorize-send",
            "```",
            "",
            "## 边界",
            "",
            "- 可扔；非甲；不进主表；不得升格 RESULT-B。",
            "- 不改甲/乙/丙定义；不复活路线 A；不改主 compare_primary 成立语义。",
            "- 不金标打分；不放宽 hard reject；不加 n 凑 k。",
            "",
        ]
    )
    return "\n".join(lines)


def write_probe_report(
    path: Path | None = None,
    *,
    code_pin: str,
    baseline_note: str,
    authorize_send: bool = False,
    root: Path | None = None,
    chat: Callable[..., Any] = live_chat,
) -> tuple[Path, dict[str, Any]]:
    """落盘可扔报告。默认不发模型。"""
    base = _repo_root() if root is None else Path(root)
    out = _DEFAULT_REPORT if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    send_result: dict[str, Any] | None = None
    if authorize_send:
        send_result = send_probe_generations(root=base, chat=chat)
    probe_pack = run_probe_recompute(root=base)
    readonly_pack = run_readonly_retest(root=base)
    markdown = render_gate_k_probe_markdown(
        code_pin=code_pin,
        baseline_note=baseline_note,
        authorize_send=authorize_send,
        send_result=send_result,
        probe_pack=probe_pack,
        readonly_pack=readonly_pack,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    gate = probe_pack["gate"] if probe_pack.get("status") == "recomputed" else gate_conditions(None)
    if probe_pack.get("status") != "recomputed":
        gate = {**gate, "passed": False}
    return out, {
        "probe": probe_pack,
        "readonly": readonly_pack,
        "send": send_result,
        "gate": gate,
        "authorize_send": authorize_send,
        "awaiting": (not authorize_send) and probe_pack.get("status") != "recomputed",
    }


def main(argv: list[str] | None = None) -> int:
    """默认不发模型。无 ``--authorize-send`` 时停在可发送边界并报告等待授权。"""
    parser = argparse.ArgumentParser(
        prog="python -m freshlatch.eval.patch_events_gate_k_probe"
    )
    parser.add_argument("--no-write", action="store_true", help="只打印判定，不写盘")
    parser.add_argument(
        "--recompute-only",
        action="store_true",
        help="只复算旁路生成（零 LLM）；不发送",
    )
    parser.add_argument(
        "--authorize-send",
        action="store_true",
        help="明文授权后才允许发模型；默认关闭",
    )
    parser.add_argument("--out", type=Path, default=_DEFAULT_REPORT, help="报告路径")
    parser.add_argument("--code-pin", default="local", help="代码针")
    parser.add_argument(
        "--baseline",
        default=(
            "cursor/470-gate-separation-remeasure-b867（R+#469）"
            "+ cherry-pick #471/#474 生成对齐"
        ),
        help="基线说明",
    )
    args = parser.parse_args(argv)

    if args.authorize_send and args.recompute_only:
        sys.stderr.write("--authorize-send 与 --recompute-only 互斥\n")
        return 2

    if args.no_write:
        if args.authorize_send:
            sys.stderr.write("--no-write 下拒绝 --authorize-send（避免静默发送）\n")
            return 2
        pack = run_probe_recompute()
        gate = pack["gate"]
        if pack.get("status") != "recomputed":
            sys.stdout.write(
                f"gate_passed=False k={gate.get('k')!r} status={pack['status']} "
                f"awaiting={_AWAITING}\n"
            )
        else:
            sys.stdout.write(
                f"gate_passed={gate['passed']} k={gate['k']!r} "
                f"t_b1_pos={gate['t_b1_positive']} t_b2_pos={gate['t_b2_positive']}\n"
            )
        return 0

    out, pack = write_probe_report(
        args.out,
        code_pin=args.code_pin,
        baseline_note=args.baseline,
        authorize_send=bool(args.authorize_send) and not args.recompute_only,
    )
    gate = pack["gate"]
    awaiting = pack.get("awaiting")
    sys.stdout.write(
        f"gate_passed={bool(gate.get('passed'))} k={gate.get('k')!r} "
        f"awaiting={_AWAITING if awaiting else False}\n"
    )
    if awaiting:
        sys.stdout.write(f"{_AWAITING}\n")
    sys.stdout.write(f"wrote {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
