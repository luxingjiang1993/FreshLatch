"""PE-Y-SMOKE-01：n=30 冒烟报告写入器（可扔 · 不作过门 · 不保证乙）。

只读消费既有 ``compare_primary`` / 固定 k 选取缝。本层身份写死：

- 冒烟层 ≠ 过门 ≠ 乙成立
- 禁止升格 ``gate_passed``
- 禁止改正式 n / 成立尺（点>0.05）
- 禁止激活 ``PREREG-Y``、填 ``RESULT-Y`` 成立格、另开 Z、金标进 score

必看字段：T 自然 k；T−C 固定 k 差点估计方向；T/B1/B2 fixed-k ``claim_id``
集是否完全相同（``collapse=true`` → 停）；score 卫生；B1/B2 差必报且不过条件。

本票可用确定性合成三臂记录生成报告；不发正式主跑、不要求真模型 n30。
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_metrics import (
    SEED,
    compare_primary,
    format_rate,
    named_streams,
    select_scored_positions,
)

# 冒烟层防火墙常量（跑前写死 · 禁止升格）
_SMOKE_N = 30
_DEFAULT_REPORT = Path("docs/evidence/patch-events/SMOKE-Y-N30.md")
_LAYER = "冒烟"
_FIREWALL = (
    "n=30 冒烟只描述本 30 条上的仪器与方向可读性；区间只描述这 30 条重抽样噪声，"
    "**不**写成总体结论，**不**进 RESULT-Y 成立格，**不**单独构成 `gate_passed`，"
    "**不**保证乙。"
)
_EDIT_CYCLE = ("数值", "日期", "条款替换", "删除")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def smoke_n() -> int:
    """冒烟样本量针（可扔；非正式 n=400）。"""
    return _SMOKE_N


def firewall_sentence() -> str:
    """层身份固定句（须原样入报告）。"""
    return _FIREWALL


def _neg_inf(value: object) -> bool:
    return isinstance(value, float) and math.isinf(value) and value < 0


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(
        float(value)
    )


def build_synthetic_smoke_rows(
    *,
    n: int = _SMOKE_N,
    collapse: bool = False,
) -> list[dict[str, Any]]:
    """确定性合成三臂记录（C/T/B1/B2），供冒烟报告与单测。

    ``collapse=True`` 时 T/B1/B2 分数完全相同 → fixed-k 集相同。
    ``collapse=False`` 时三臂分数错开 → fixed-k 集不同。
    不读密钥、不连网、不调模型。
    """
    if n <= 0:
        raise ValueError("n 必须为正")
    rows: list[dict[str, Any]] = []
    for i in range(n):
        claim_id = f"smoke-{i:03d}"
        gold = "正确" if i % 2 == 0 else "坏"
        edit_type = _EDIT_CYCLE[i % 4]
        evidence_id = f"doc#{claim_id}@T1"
        evidence_text = f"证据-{claim_id}"
        before = f"原文-{claim_id}"
        # C：自然全放行；无核验分（coverage_c 路径）
        rows.append(
            {
                "claim_id": claim_id,
                "edit_type": edit_type,
                "arm": "C",
                "ablation": "",
                "construction_gold": gold,
                "before_text": before,
                "after_text": f"c-after-{claim_id}",
                "evidence_id": evidence_id,
                "evidence_text": evidence_text,
                "decision": "release",
                "reject_reason": "",
                "score": None,
                "latency_ms": 1,
                "cost": 0,
            }
        )
        # T：优先放行「正确」条，压低坏条自然放行 → 固定 k 误放低于 C，方向可读
        t_release = gold == "正确" or i < n // 10
        if collapse:
            t_score = float(n - i) if t_release else float("-inf")
            b1_score = t_score
            b2_score = t_score if t_release else float(i) * 0.01
        else:
            t_score = float(1000 - i) if t_release else float("-inf")
            # B1：与 T 错开放行/分数，制造不同 fixed-k 集
            b1_release_flag = i % 3 != 0
            b1_score = float(500 - i * 3) if b1_release_flag else float("-inf")
            # B2：分数递增，top-k 偏向高编号
            b2_score = float(100 + i * 7)
        rows.append(
            {
                "claim_id": claim_id,
                "edit_type": edit_type,
                "arm": "T",
                "ablation": "",
                "construction_gold": gold,
                "before_text": before,
                "after_text": evidence_text if t_release else f"t-bad-{claim_id}",
                "evidence_id": evidence_id,
                "evidence_text": evidence_text,
                "decision": "release" if t_release else "reject",
                "reject_reason": "" if t_release else "核验不过",
                "score": t_score,
                "latency_ms": 1,
                "cost": 0,
                "reverify_ok": t_release,
            }
        )
        b1_release = _finite_number(b1_score)
        rows.append(
            {
                "claim_id": claim_id,
                "edit_type": edit_type,
                "arm": "B1",
                "ablation": "",
                "construction_gold": gold,
                "before_text": before,
                "after_text": evidence_text if b1_release else f"b1-bad-{claim_id}",
                "evidence_id": evidence_id,
                "evidence_text": evidence_text,
                "decision": "release" if b1_release else "reject",
                "reject_reason": "" if b1_release else "核验不过",
                "score": b1_score,
                "latency_ms": 1,
                "cost": 0,
                "reverify_ok": b1_release,
            }
        )
        # B2：核验不过不因此 hard reject；分数有限
        rows.append(
            {
                "claim_id": claim_id,
                "edit_type": edit_type,
                "arm": "B2",
                "ablation": "",
                "construction_gold": gold,
                "before_text": before,
                "after_text": f"b2-after-{claim_id}",
                "evidence_id": evidence_id,
                "evidence_text": evidence_text,
                "decision": "release",
                "reject_reason": "",
                "score": b2_score if _finite_number(b2_score) else float(i + 1),
                "latency_ms": 1,
                "cost": 0,
                "reverify_ok": False,
            }
        )
    return rows


def fixed_k_claim_id_sets(
    rows: Sequence[Mapping[str, Any]],
    *,
    k: int,
) -> dict[str, list[str]]:
    """T/B1/B2 固定 k 选取的 ``claim_id`` 有序列表（与 ``select_scored_positions`` 同序）。

    C 走 ``coverage_c``，不参与坍缩检测。
    """
    by_arm: dict[str, list[Mapping[str, Any]]] = {"T": [], "B1": [], "B2": []}
    for row in rows:
        if row.get("ablation", "") != "":
            continue
        arm = str(row["arm"])
        if arm in by_arm:
            by_arm[arm].append(row)
    out: dict[str, list[str]] = {}
    for arm, items in by_arm.items():
        ordered = sorted(items, key=lambda item: str(item["claim_id"]))
        positions = select_scored_positions(ordered, k)
        out[arm] = [str(ordered[pos]["claim_id"]) for pos in positions]
    return out


def score_hygiene_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """score 卫生：T/B1/B2 禁止 None 混池；reject 须 −∞；released 须有限非空。

    C 无核验分，允许 None。不把金标当 score（结构断言：score 只能是数或 None）。
    """
    none_in_pool: list[str] = []
    reject_not_neg_inf: list[str] = []
    release_not_finite: list[str] = []
    for row in rows:
        if row.get("ablation", "") != "":
            continue
        arm = str(row["arm"])
        if arm == "C":
            continue
        claim_id = str(row["claim_id"])
        score = row.get("score")
        decision = row.get("decision")
        key = f"{arm}:{claim_id}"
        if score is None:
            none_in_pool.append(key)
            continue
        if decision == "reject":
            if not _neg_inf(score):
                reject_not_neg_inf.append(key)
        elif decision == "release":
            if not _finite_number(score):
                release_not_finite.append(key)
    ok = not none_in_pool and not reject_not_neg_inf and not release_not_finite
    return {
        "ok": ok,
        "none_in_sortable_pool": none_in_pool,
        "reject_not_neg_inf": reject_not_neg_inf,
        "release_not_finite": release_not_finite,
    }


def _direction(point: float | None) -> str:
    if point is None:
        return "undefined"
    if point > 0:
        return "positive"
    return "non_positive"


def analyze_smoke(
    rows: Sequence[Mapping[str, Any]],
    *,
    streams: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """冒烟分析：只读 ``compare_primary`` + 坍缩 + score 卫生。

    返回结构永含层身份防火墙字段；``constitutes_gate_passed`` 恒为 False。
    """
    primary = compare_primary(
        rows,
        streams=streams if streams is not None else named_streams(),
    )
    k = int(primary["k"])
    by_name = {item["name"]: item for item in primary["comparisons"]}
    t_c = by_name.get("T-C") or {}
    t_b1 = by_name.get("T-B1") or {}
    t_b2 = by_name.get("T-B2") or {}
    t_c_point = t_c.get("point")
    t_b1_point = t_b1.get("point")
    t_b2_point = t_b2.get("point")
    claim_sets = fixed_k_claim_id_sets(rows, k=k)
    collapse = (
        claim_sets["T"] == claim_sets["B1"] == claim_sets["B2"]
        and k > 0
    )
    hygiene = score_hygiene_report(rows)
    stop = bool(collapse)
    return {
        "layer": _LAYER,
        "n": len({str(row["claim_id"]) for row in rows if row.get("ablation", "") == ""}),
        "k": k,
        "t_c_point": t_c_point,
        "t_c_direction": _direction(t_c_point if isinstance(t_c_point, (int, float)) else None),
        "t_b1_point": t_b1_point,
        "t_b2_point": t_b2_point,
        "fixed_k_claim_ids": claim_sets,
        "collapse": collapse,
        "score_hygiene": hygiene,
        "stop": stop,
        # 防火墙写死：冒烟永不构成过门 / 永不进 RESULT-Y / 不保证乙
        "constitutes_gate_passed": False,
        "enters_result_y": False,
        "guarantees_yi": False,
        "writes_population_ci": False,
        "primary": primary,
        "seed": SEED,
    }


def render_smoke_y_n30_markdown(
    analysis: Mapping[str, Any],
    *,
    code_pin: str,
    source_note: str,
) -> str:
    """渲染可扔 ``SMOKE-Y-N30.md``。不含 RESULT-Y 成立格、不含 gate_passed=true。"""
    claim_sets = analysis["fixed_k_claim_ids"]
    hygiene = analysis["score_hygiene"]
    collapse = bool(analysis["collapse"])
    stop = bool(analysis["stop"])

    def _ids(arm: str) -> str:
        ids = claim_sets.get(arm) or []
        return ", ".join(ids) if ids else "（空）"

    lines: list[str] = [
        "# SMOKE-Y-N30 冒烟报告（可扔）",
        "",
        "> **可扔 · 冒烟层 · 不作过门 · 不保证乙 · 不进 RESULT-Y。**",
        f"> {_FIREWALL}",
        "> 本页**不**激活 `PREREG-Y`；**不**填 RESULT-Y 成立格；**不**升格 `gate_passed`。",
        f"> **层身份**：{_LAYER}（合成/夹具可；本票不发正式主跑）。",
        "",
        "## 协议针（跑前写死）",
        "",
        f"- **n** = {analysis['n']}（冒烟；非正式 n=400）",
        f"- **bootstrap seed** = `{analysis['seed']}`（只描述这 {analysis['n']} 条重抽样噪声）",
        f"- **代码针**：{code_pin}",
        f"- **输入来源**：{source_note}",
        "- **选取**：R（固定 k = T 自然放行数；T/B1/B2 按 score；C 走 coverage_c）",
        "",
        "## 必看字段",
        "",
        "### T 自然 k",
        "",
        f"- **k** = `{analysis['k']}`",
        "",
        "### T−C 固定 k 差点估计方向",
        "",
        f"- **点估计** = {format_rate(analysis['t_c_point'])}",
        f"- **方向** = `{analysis['t_c_direction']}`"
        "（`positive` 表示点估计 > 0；冒烟只报方向，**不**构成 `gate_passed`）",
        "",
        "### T/B1/B2 fixed-k claim_id 集（坍缩检测）",
        "",
        f"- **T**：`{_ids('T')}`",
        f"- **B1**：`{_ids('B1')}`",
        f"- **B2**：`{_ids('B2')}`",
        f"- **collapse** = `{str(collapse).lower()}`"
        "（三臂 fixed-k `claim_id` 集完全相同则为 true）",
        f"- **stop** = `{str(stop).lower()}`（`collapse=true` → 停；不得激活 / 不得进探针升格）",
        "",
        "### score 卫生",
        "",
        f"- **ok** = `{str(bool(hygiene['ok'])).lower()}`",
        f"- None 混进可排序池：`{hygiene['none_in_sortable_pool']}`",
        f"- reject 非 −∞：`{hygiene['reject_not_neg_inf']}`",
        f"- release 非有限：`{hygiene['release_not_finite']}`",
        "",
        "### B1/B2 差（必报 · 不过条件）",
        "",
        "| 对比 | 点估计 | 进冒烟停条件？ | 进 gate_passed？ |",
        "|---|---:|---|---|",
        f"| T−C | {format_rate(analysis['t_c_point'])} | 否（只报方向） | **否** |",
        f"| T−B1 | {format_rate(analysis['t_b1_point'])} | **否** | **否** |",
        f"| T−B2 | {format_rate(analysis['t_b2_point'])} | **否** | **否** |",
        "",
        "> B1/B2 差**必报**，**不**作冒烟通过/停条件以外的过门条件；"
        "停条件仅 `collapse=true`。",
        "",
        "## 层身份断言（防火墙）",
        "",
        "| 断言 | 值 |",
        "|---|---|",
        f"| `constitutes_gate_passed` | `{analysis['constitutes_gate_passed']}` |",
        f"| `enters_result_y` | `{analysis['enters_result_y']}` |",
        f"| `guarantees_yi` | `{analysis['guarantees_yi']}` |",
        f"| `writes_population_ci` | `{analysis['writes_population_ci']}` |",
        "| PREREG-Y 激活 | 否（本页不写激活批注） |",
        "| RESULT-Y 成立格 | 未写 |",
        "",
        "## 结论",
        "",
    ]
    if stop:
        lines.extend(
            [
                "- **collapse=true → 停**。",
                "- 不得激活 `PREREG-Y`；不得把本页升格为 `gate_passed`；不得进正式主跑。",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- 本页未检出三臂 fixed-k 坍缩（`collapse=false`）。",
                "- 即便方向可读，本页**仍不**构成 `gate_passed`，**不**保证乙。",
                "- 后续仍须敏感性 ∧ 真数据 GATE-Y ∧ 人令；本 Cloud Agent 不激活。",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 可扔；不进 RESULT-Y；不单独构成 `gate_passed`；区间不写总体；不保证乙。",
            "- 不改正式 n / 成立尺（点>0.05）；不回写 B/C；不另开 Z；金标不进 score。",
            "- 入口：`PYTHONPATH=src python -m freshlatch.eval.patch_events_smoke_y`",
            "",
        ]
    )
    return "\n".join(lines)


def write_smoke_y_n30_report(
    path: Path | None = None,
    *,
    rows: Sequence[Mapping[str, Any]] | None = None,
    code_pin: str = "local",
    source_note: str = "确定性合成三臂记录（本票不发正式主跑）",
    collapse_fixture: bool = False,
    root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """写出可扔报告。默认用合成夹具；永不写 RESULT-Y / 永不升格 gate_passed。"""
    base = _repo_root() if root is None else Path(root)
    out = _DEFAULT_REPORT if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    # 防火墙：禁止把冒烟报告写进 RESULT-Y 路径
    forbidden = {
        (base / "docs/evidence/patch-events/RESULT-Y.md").resolve(),
        (base / "docs/evidence/patch-events/RESULT.md").resolve(),
        (base / "docs/evidence/patch-events/PREREG-Y.md").resolve(),
    }
    if out.resolve() in forbidden:
        raise RuntimeError("冒烟报告禁止写入 RESULT-Y / RESULT / PREREG-Y")
    sample = (
        list(rows)
        if rows is not None
        else build_synthetic_smoke_rows(n=_SMOKE_N, collapse=collapse_fixture)
    )
    analysis = analyze_smoke(sample)
    # 硬闸：分析结构不得把构成过门标成 true
    if analysis["constitutes_gate_passed"] is not False:
        raise RuntimeError("防火墙违例：冒烟不得构成 gate_passed")
    if analysis["enters_result_y"] is not False:
        raise RuntimeError("防火墙违例：冒烟不得进入 RESULT-Y")
    markdown = render_smoke_y_n30_markdown(
        analysis,
        code_pin=code_pin,
        source_note=source_note,
    )
    # 报告正文不得出现 gate_passed=true / RESULT-Y 成立
    if "gate_passed=true" in markdown.lower().replace(" ", ""):
        raise RuntimeError("防火墙违例：报告不得写 gate_passed=true")
    if "成立格" in markdown and "未写" not in markdown:
        # 允许「不进 RESULT-Y 成立格」「未写」，禁止填成立
        pass
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    return out, analysis


def main(argv: Sequence[str] | None = None) -> int:
    """CLI：默认写合成冒烟报告；``--no-write`` 只打印摘要。"""
    parser = argparse.ArgumentParser(description="PE-Y-SMOKE-01 写出 SMOKE-Y-N30.md")
    parser.add_argument("--no-write", action="store_true", help="只分析，不写盘")
    parser.add_argument(
        "--collapse-fixture",
        action="store_true",
        help="使用坍缩合成夹具（collapse=true）",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="报告路径（默认 docs/evidence/patch-events/SMOKE-Y-N30.md）",
    )
    parser.add_argument("--code-pin", default="local", help="代码针字符串")
    args = parser.parse_args(list(argv) if argv is not None else None)
    rows = build_synthetic_smoke_rows(n=_SMOKE_N, collapse=bool(args.collapse_fixture))
    analysis = analyze_smoke(rows)
    summary = (
        f"k={analysis['k']} direction={analysis['t_c_direction']} "
        f"collapse={analysis['collapse']} stop={analysis['stop']} "
        f"score_hygiene_ok={analysis['score_hygiene']['ok']} "
        f"gate_passed={analysis['constitutes_gate_passed']}"
    )
    print(summary)
    if args.no_write:
        return 0
    path, _ = write_smoke_y_n30_report(
        args.out,
        rows=rows,
        code_pin=str(args.code_pin),
        collapse_fixture=bool(args.collapse_fixture),
    )
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
