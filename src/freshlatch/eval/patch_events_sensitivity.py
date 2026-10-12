"""GATE-Y 敏感性闸（#528 · PE-Y-SENS-01 · ADR-0041）。

跑前写死集合 S：构造坏槽（四层×mod4）+ 有限废止/版本陷阱 + 正确对照。
通过线 S1–S4 须同时成立；报告可扔，不进 RESULT-Y，不构成 ``gate_passed``，
不单独过门，不激活 ``PREREG-Y``。

未跑真实权重时：报告必须标注「夹具/stub 层 · 非真模型过线」，且
``activation_prerequisite_met=False``（不得把 stub 绿写成可激活前置已满足）。
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TextIO

from freshlatch.eval.patch_events_construct import STRATA
from freshlatch.eval.patch_events_verify import (
    ENTAILMENT_TAU,
    XNLI_MODEL_ID,
    verify_edit,
)

# 通过线 ρ（ADR-0041 · 跑前锁死；禁止事后放宽凑绿）
BAD_OK_FALSE_MIN = 0.90
CORRECT_OK_TRUE_MIN = 0.70

# 层身份：本报告永不为 gate_passed / 乙成立
REPORT_LAYER_STUB = "夹具/stub 层 · 非真模型过线"
REPORT_LAYER_REAL = "真模型推理层"

GoldLabel = Literal["坏", "正确"]
SampleKind = Literal["construct_bad", "abolish_trap", "version_trap", "correct"]


@dataclass(frozen=True)
class SensitivitySample:
    """集合 S 单条（跑前写死）。"""

    sample_id: str
    stratum: str
    operator: int | None
    gold: GoldLabel
    kind: SampleKind
    after_text: str
    evidence_text: str
    note: str = ""
    heuristic: str = ""
    subcase: str = ""
    pair_id: str = ""
    pair_role: str = ""
    token_overlap: str | None = None
    token_overlap_role: str = ""
    wice_note: str = ""
    nli_construct_ok: str = ""
    must_carry: bool = False
    replaces: str = ""
    canonical_index: int = -1


def _bad(
    sample_id: str,
    stratum: str,
    operator: int,
    after_text: str,
    evidence_text: str,
    *,
    note: str = "",
) -> SensitivitySample:
    return SensitivitySample(
        sample_id=sample_id,
        stratum=stratum,
        operator=operator,
        gold="坏",
        kind="construct_bad",
        after_text=after_text,
        evidence_text=evidence_text,
        note=note,
    )


def _correct(
    sample_id: str,
    stratum: str,
    after_text: str,
    evidence_text: str,
    *,
    note: str = "",
) -> SensitivitySample:
    return SensitivitySample(
        sample_id=sample_id,
        stratum=stratum,
        operator=None,
        gold="正确",
        kind="correct",
        after_text=after_text,
        evidence_text=evidence_text,
        note=note,
    )


def _trap(
    sample_id: str,
    kind: Literal["abolish_trap", "version_trap"],
    after_text: str,
    evidence_text: str,
    *,
    note: str = "",
) -> SensitivitySample:
    return SensitivitySample(
        sample_id=sample_id,
        stratum="条款替换",
        operator=None,
        gold="坏",
        kind=kind,
        after_text=after_text,
        evidence_text=evidence_text,
        note=note,
    )


# ---------------------------------------------------------------------------
# 集合 S（跑前写死 · 名单不可事后增删改算子语义）
# 四层 × mod4 坏槽各 ≥1；废止/版本陷阱有限条；正确对照防全拒假绿。
# ---------------------------------------------------------------------------
SENSITIVITY_SET_S: tuple[SensitivitySample, ...] = (
    # --- 数值 · operator 0..3 ---
    _bad(
        "S-数值-op0",
        "数值",
        0,
        "个人信息出境评估结果有效期为三年。",
        "个人信息出境评估结果有效期为二年。",
        note="数值±10% 扰动",
    ),
    _bad(
        "S-数值-op1",
        "数值",
        1,
        "留存不少于 50 年。",
        "留存不少于 5 年。",
        note="数值数量级扰动",
    ),
    _bad(
        "S-数值-op2",
        "数值",
        2,
        "申报门槛为累计 100 万人。",
        "申报门槛为累计 10 万人；敏感信息另计 1 万人。",
        note="错配另一数字",
    ),
    _bad(
        "S-数值-op3",
        "数值",
        3,
        "单会话成本约 0.008 个百分点。",
        "单会话成本约 0.008 美元。",
        note="单位错配",
    ),
    # --- 日期 · operator 0..3 ---
    _bad(
        "S-日期-op0",
        "日期",
        0,
        "本办法自 2025 年 3 月 22 日起施行。",
        "本办法自 2024 年 3 月 22 日起施行。",
        note="年份±1",
    ),
    _bad(
        "S-日期-op1",
        "日期",
        1,
        "公布日期为 2023 年 3 月 22 日。",
        "公布日期为 2023 年 2 月 22 日。",
        note="月份平移",
    ),
    _bad(
        "S-日期-op2",
        "日期",
        2,
        "施行日期为 2022 年 9 月 1 日。",
        "公布日期为 2022 年 7 月 7 日；施行日期为 2022 年 9 月 1 日。",
        note="错配另一日期字段",
    ),
    _bad(
        "S-日期-op3",
        "日期",
        3,
        "本办法自 2022 年 9 月 1 日起施行。",
        "旧办法自 2020 年 1 月 1 日起施行；新办法自 2022 年 9 月 1 日起施行。",
        note="绑到过期 T0 证据面",
    ),
    # --- 条款替换 · operator 0..3 ---
    _bad(
        "S-条款-op0",
        "条款替换",
        0,
        "处理者不得向境外提供个人信息。",
        "处理者应当向境外提供个人信息前完成安全评估。",
        note="应当/不得翻转",
    ),
    _bad(
        "S-条款-op1",
        "条款替换",
        1,
        "接收方应当保存出境记录不少于三年。",
        "处理者应当保存出境记录不少于三年。",
        note="主体错配",
    ),
    _bad(
        "S-条款-op2",
        "条款替换",
        2,
        "关键个人信息出境认证办法适用于本条。",
        "个人信息出境应当适用标准合同办法。",
        note="错挂另一条款",
    ),
    _bad(
        "S-条款-op3",
        "条款替换",
        3,
        "处理者应当完成安全评估。",
        "附录仅列术语定义，不含安全评估义务。",
        note="证据块不含该义务",
    ),
    # --- 删除 · operator 0..3 ---
    _bad(
        "S-删除-op0",
        "删除",
        0,
        "除金融机构外这一例外仍然有效。",
        "留存不少于 5 年这一限定已废止。除金融机构外这一例外仍然有效。",
        note="删错：删掉仍有效例外",
    ),
    _bad(
        "S-删除-op1",
        "删除",
        1,
        "个人信息应当依法处理。",
        "个人信息应当依法处理，留存不少于 5 年。",
        note="删掉证据仍支持的阈值",
    ),
    _bad(
        "S-删除-op2",
        "删除",
        2,
        "原暂行办法同时废止。",
        "",
        note="空证据硬拒对照",
    ),
    _bad(
        "S-删除-op3",
        "删除",
        3,
        "处理者应当保存记录。",
        "处理者应当大约保存记录。",
        note="仅删修饰词伪装更新",
    ),
    # --- 有限废止 / 版本陷阱（加集 · id 写死） ---
    _trap(
        "S-废止-trap01",
        "abolish_trap",
        "1993 年《取水许可制度实施办法》仍然有效。",
        "1993年8月1日国务院发布的《取水许可制度实施办法》同时废止。",
        note="废止法仍称有效",
    ),
    _trap(
        "S-废止-trap02",
        "abolish_trap",
        "《禁止使用童工规定》继续施行。",
        "1991年4月15日国务院发布的《禁止使用童工规定》同时废止。",
        note="废止规章继续施行",
    ),
    _trap(
        "S-版本-trap01",
        "version_trap",
        "数据出境安全评估结果有效期为二年。",
        "促进和规范数据跨境流动规定施行后，评估结果有效期按令 16 调整为三年。",
        note="版本错配：沿用旧二年",
    ),
    _trap(
        "S-版本-trap02",
        "version_trap",
        "标准合同办法适用于累计不满 10 万人的情形。",
        "令 16 第八条将标准合同适用区间调整为当年累计 10 万以上、不满 100 万。",
        note="版本错配：旧门槛",
    ),
    # --- 正确对照（防全拒假绿） ---
    _correct(
        "S-正确-数值01",
        "数值",
        "留存不少于 5 年。",
        "相关记录留存不少于 5 年。",
        note="数值正确对照",
    ),
    _correct(
        "S-正确-日期01",
        "日期",
        "本办法自 2024 年 3 月 22 日起施行。",
        "本办法自公布之日起施行；公布日为 2024 年 3 月 22 日。",
        note="日期正确对照",
    ),
    _correct(
        "S-正确-条款01",
        "条款替换",
        "处理者应当在出境前完成安全评估。",
        "处理者应当在向境外提供个人信息前完成安全评估。",
        note="条款正确对照",
    ),
    _correct(
        "S-正确-删除01",
        "删除",
        "个人信息应当依法处理。",
        "留存不少于 5 年这一限定已废止。个人信息应当依法处理。",
        note="删除废止限定后仍被证据支撑",
    ),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_report_path(root: Path | None = None) -> Path:
    base = _repo_root() if root is None else Path(root)
    return base / "docs" / "evidence" / "patch-events" / "GATE-Y-SENSITIVITY.md"


def assert_set_s_locked(samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S) -> None:
    """跑前不变量：四层×mod4 坏槽齐全；含陷阱与正确对照。"""
    ids = [s.sample_id for s in samples]
    if len(ids) != len(set(ids)):
        raise ValueError("集合 S sample_id 重复")
    for stratum in STRATA:
        for op in range(4):
            hit = [
                s
                for s in samples
                if s.kind == "construct_bad" and s.stratum == stratum and s.operator == op
            ]
            if not hit:
                raise ValueError(f"集合 S 缺坏槽：{stratum}×op{op}")
    if not any(s.kind == "abolish_trap" for s in samples):
        raise ValueError("集合 S 缺废止陷阱")
    if not any(s.kind == "version_trap" for s in samples):
        raise ValueError("集合 S 缺版本陷阱")
    if not any(s.gold == "正确" for s in samples):
        raise ValueError("集合 S 缺正确对照")


def _verify_request(sample: SensitivitySample) -> dict[str, Any]:
    return {
        "arm": "T",
        "claim_id": sample.sample_id,
        "after_text": sample.after_text,
        "evidence_id": f"sens#{sample.sample_id}",
        "evidence_text": sample.evidence_text,
    }


def run_sensitivity_cases(
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
    *,
    verify: Callable[[Mapping[str, Any]], Mapping[str, Any]] = verify_edit,
) -> list[dict[str, Any]]:
    """对集合 S 逐条跑 ``verify_edit``，返回逐条结果表。"""
    assert_set_s_locked(samples)
    rows: list[dict[str, Any]] = []
    for sample in samples:
        verdict = dict(verify(_verify_request(sample)))
        rows.append(
            {
                "sample_id": sample.sample_id,
                "stratum": sample.stratum,
                "operator": sample.operator,
                "gold": sample.gold,
                "kind": sample.kind,
                "ok": verdict.get("ok"),
                "score": verdict.get("score"),
                "reason": verdict.get("reason"),
                "note": sample.note,
            }
        )
    return rows


def evaluate_s1_s4(
    rows: Sequence[Mapping[str, Any]],
    *,
    model_id: str = XNLI_MODEL_ID,
    tau: float = ENTAILMENT_TAU,
    expected_model_id: str = XNLI_MODEL_ID,
    expected_tau: float = ENTAILMENT_TAU,
) -> dict[str, Any]:
    """计算 S1–S4 通过布尔与汇总比例。"""
    none_scores = [r for r in rows if r.get("score") is None]
    reject_rows = [r for r in rows if r.get("ok") is False]
    reject_neg_inf = [
        r
        for r in reject_rows
        if isinstance(r.get("score"), float)
        and math.isinf(r["score"])
        and r["score"] < 0
    ]
    s1 = len(none_scores) == 0 and len(reject_rows) == len(reject_neg_inf)

    bad_rows = [r for r in rows if r.get("gold") == "坏"]
    correct_rows = [r for r in rows if r.get("gold") == "正确"]
    bad_reject = sum(1 for r in bad_rows if r.get("ok") is False)
    correct_accept = sum(1 for r in correct_rows if r.get("ok") is True)
    bad_rate = (bad_reject / len(bad_rows)) if bad_rows else 0.0
    correct_rate = (correct_accept / len(correct_rows)) if correct_rows else 0.0
    s2 = bad_rate >= BAD_OK_FALSE_MIN
    s3 = correct_rate >= CORRECT_OK_TRUE_MIN
    s4 = model_id == expected_model_id and tau == expected_tau

    sensitivity_passed = bool(s1 and s2 and s3 and s4)
    return {
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "s4": s4,
        "sensitivity_passed": sensitivity_passed,
        "n_total": len(rows),
        "n_bad": len(bad_rows),
        "n_correct": len(correct_rows),
        "n_score_none": len(none_scores),
        "n_reject": len(reject_rows),
        "n_reject_neg_inf": len(reject_neg_inf),
        "bad_ok_false_rate": bad_rate,
        "correct_ok_true_rate": correct_rate,
        "bad_ok_false_min": BAD_OK_FALSE_MIN,
        "correct_ok_true_min": CORRECT_OK_TRUE_MIN,
        "model_id": model_id,
        "tau": tau,
        "expected_model_id": expected_model_id,
        "expected_tau": expected_tau,
    }


def render_sensitivity_report(
    summary: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    inference_layer: str,
    activation_prerequisite_met: bool,
) -> str:
    """渲染可扔报告正文（不进 RESULT-Y · 不构成 gate_passed）。"""
    if activation_prerequisite_met and inference_layer == REPORT_LAYER_STUB:
        raise ValueError("stub 层不得声称可激活前置已满足")

    lines: list[str] = [
        "# GATE-Y-SENSITIVITY（可扔 · 敏感性闸）",
        "",
        f"**层身份**：{inference_layer}",
        "",
        "> 本报告不进 `RESULT-Y` 成立格；不构成 `gate_passed`；不单独过门；",
        "> 不保证乙；不激活 `PREREG-Y`。夹具/stub 绿 ≠ 可激活前置已满足。",
        "",
        "## Pin",
        "",
        f"- 型号：`{summary['model_id']}`（须 = ADR-0040 / #527 `{summary['expected_model_id']}`）",
        f"- τ：`{summary['tau']}`（须 = `ENTAILMENT_TAU`；失败仅允许未激活收紧一次并整闸重测；**禁止放宽**凑绿）",
        f"- 坏→`ok=False` 下限：`{summary['bad_ok_false_min']}`",
        f"- 正确→`ok=True` 下限：`{summary['correct_ok_true_min']}`",
        f"- 集合 S 条数：{summary['n_total']}（坏 {summary['n_bad']} · 正确 {summary['n_correct']}）",
        "",
        "## S1–S4",
        "",
        "| # | 条件 | 结果 |",
        "|---|---|---|",
        f"| S1 | 无 `score=None`；reject/`ok=False` → `score=−∞` "
        f"（none={summary['n_score_none']}；reject={summary['n_reject']}；"
        f"−∞={summary['n_reject_neg_inf']}） | "
        f"{'通过' if summary['s1'] else '未通过'} |",
        f"| S2 | 坏→`ok=False` ≥ {summary['bad_ok_false_min']} "
        f"（实测 {summary['bad_ok_false_rate']:.4f}） | "
        f"{'通过' if summary['s2'] else '未通过'} |",
        f"| S3 | 正确→`ok=True` ≥ {summary['correct_ok_true_min']} "
        f"（实测 {summary['correct_ok_true_rate']:.4f}） | "
        f"{'通过' if summary['s3'] else '未通过'} |",
        f"| S4 | 型号/τ = ADR-0040（`{summary['expected_model_id']}` · "
        f"`{summary['expected_tau']}`） | "
        f"{'通过' if summary['s4'] else '未通过'} |",
        "",
        f"**sensitivity_passed（S1∧S2∧S3∧S4）**："
        f"{'是' if summary['sensitivity_passed'] else '否'}",
        "",
        f"**gate_passed**：否（敏感性报告永不单独过门）",
        "",
        f"**activation_prerequisite_met**："
        f"{'是' if activation_prerequisite_met else '否'}",
        "",
        "## τ 收紧纪律（未激活）",
        "",
        "- 失败时仅允许未激活收紧 τ **一次**并整闸重测。",
        "- 禁止放宽 τ / ρ 凑绿。",
        "- 本票未改 `ENTAILMENT_TAU`；未激活 `PREREG-Y`。",
        "",
        "## 逐条结果",
        "",
        "| sample_id | stratum | op | gold | kind | ok | score | reason |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for row in rows:
        score = row.get("score")
        if score is None:
            score_s = "None"
        elif isinstance(score, float) and math.isinf(score) and score < 0:
            score_s = "−∞"
        else:
            score_s = f"{score:.6f}" if isinstance(score, float) else str(score)
        op = row.get("operator")
        op_s = "" if op is None else str(op)
        lines.append(
            f"| {row.get('sample_id')} | {row.get('stratum')} | {op_s} | "
            f"{row.get('gold')} | {row.get('kind')} | {row.get('ok')} | "
            f"{score_s} | {row.get('reason')} |"
        )
    lines.extend(
        [
            "",
            "## 防火墙复述",
            "",
            "- 不进 RESULT-Y；≠ 乙；≠ `gate_passed`。",
            "- 未通过 → 不得真数据探针、不得激活、不得正式跑。",
            "- 禁止：金标进 score；夹具升格过门；放宽凑绿。",
            "",
        ]
    )
    return "\n".join(lines)


def write_sensitivity_report(
    path: Path | None = None,
    *,
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
    verify: Callable[[Mapping[str, Any]], Mapping[str, Any]] = verify_edit,
    inference_layer: str = REPORT_LAYER_STUB,
    activation_prerequisite_met: bool | None = None,
    model_id: str = XNLI_MODEL_ID,
    tau: float = ENTAILMENT_TAU,
) -> dict[str, Any]:
    """跑集合 S、写报告，返回汇总（含路径）。"""
    if activation_prerequisite_met is None:
        # stub 层默认不可作激活前置；真模型层仍须人审，本票默认 False
        activation_prerequisite_met = False

    rows = run_sensitivity_cases(samples, verify=verify)
    summary = evaluate_s1_s4(rows, model_id=model_id, tau=tau)
    text = render_sensitivity_report(
        summary,
        rows,
        inference_layer=inference_layer,
        activation_prerequisite_met=activation_prerequisite_met,
    )
    out = default_report_path() if path is None else Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    payload = dict(summary)
    payload.update(
        {
            "report_path": str(out),
            "inference_layer": inference_layer,
            "activation_prerequisite_met": activation_prerequisite_met,
            "gate_passed": False,
            "rows": rows,
        }
    )
    return payload


def make_table_driven_nli_stub(
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
) -> Callable[[str, str], dict[str, float]]:
    """表驱动可控 stub：坏→低 entail；正确→高 entail。

    用于单测断言通过线布尔；**不得**把该 stub 绿写成真模型过线。
    """
    table: dict[tuple[str, str], dict[str, float]] = {}
    for sample in samples:
        if sample.gold == "正确":
            probs = {"entailment": 0.91, "neutral": 0.05, "contradiction": 0.04}
        else:
            probs = {"entailment": 0.08, "neutral": 0.12, "contradiction": 0.80}
        table[(sample.evidence_text, sample.after_text)] = probs

    def predict(premise: str, hypothesis: str) -> dict[str, float]:
        hit = table.get((premise, hypothesis))
        if hit is None:
            # 未知对：保守拒识，避免假绿
            return {"entailment": 0.05, "neutral": 0.10, "contradiction": 0.85}
        return dict(hit)

    return predict


# ---------------------------------------------------------------------------
# PE-Y-SENS-LIVE-2（#542）
# 正式 S 是冻结 jsonl，不是代码里的 24 条 SENSITIVITY_SET_S。
# 打分仍走 verify_edit / evaluate_s1_s4。不改 τ、ρ、ADR-0040。
# ---------------------------------------------------------------------------

FORMAL_FREEZE_SHA256 = "e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19"
# #543 过早产物。不得当作本冻结，不得据此开跑。
PREMATURE_PR543_SHA256 = "baf33f5b9e0ea801c736d67385a94546fb6bd24af1ada0e4f27d1b9f5da1fa8c"
# #538 代码内 24 条口径。本票不把它当成正式 S，也不改 SENSITIVITY_SET_S。
OLD_INCODE_SET_SHA256 = "958638ca0f3dc51323db710a69f4eacacc2fcff10186a99b07aecc47821d838b"
VERIFY_PY_SHA256 = "58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918"
CHEF_TOKEN_OVERLAP_MIN = 0.8
MUST_CARRY_IDS = ("DIAG-CHEF-03-bad", "DIAG-CHEF-04-bad")
RETIRED_NOT_IN_FORMAL_S = (
    "S-日期-op2",
    "S-日期-op3",
    "S-条款-op2",
    "S-删除-op0",
    "S-删除-op1",
    "S-删除-op3",
)
EXCLUDED_NOT_IN_FORMAL_S = (
    "DIAG-HANS-001",
    "DIAG-HANS-005",
    "DIAG-HANS-007",
    "DIAG-HANS-008",
)
_DIAG_ARCHIVED_P_ENTAIL: dict[str, float] = {
    "DIAG-HANS-002": 0.0004841118,
    "DIAG-HANS-003": 0.0011600856,
    "DIAG-HANS-004": 0.1859738678,
    "DIAG-HANS-006": 0.0104973661,
    "DIAG-CHEF-03-bad": 0.8668648601,
    "DIAG-CHEF-03-good": 0.9216354489,
    "DIAG-CHEF-04-bad": 0.9547298551,
    "DIAG-CHEF-04-good": 0.9086972475,
}


def formal_freeze_path(root: Path | None = None) -> Path:
    """正式冻结名单。#544 / #545 落盘，本票只读。"""
    base = _repo_root() if root is None else Path(root)
    return base / "docs" / "evidence" / "patch-events" / "SENS-S-FREEZE-formal-S.jsonl"


def live2_evidence_dir(root: Path | None = None) -> Path:
    base = _repo_root() if root is None else Path(root)
    return base / "docs" / "evidence" / "patch-events"


def load_formal_freeze(
    path: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], bytes]:
    """读冻结 jsonl。不调用 NLI。返回 header、sample 行、文件字节。"""
    freeze = formal_freeze_path() if path is None else Path(path)
    raw = freeze.read_bytes()
    header: dict[str, Any] | None = None
    samples: list[dict[str, Any]] = []
    for line in raw.decode("utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        record_type = obj.get("record_type")
        if record_type == "freeze_header":
            if header is not None:
                raise ValueError("冻结文件出现重复 freeze_header")
            header = obj
        elif record_type == "sample":
            samples.append(obj)
        else:
            raise ValueError(f"冻结文件含未知 record_type：{record_type}")
    if header is None:
        raise ValueError("冻结文件缺 freeze_header")
    return header, samples, raw


def formal_freeze_sha256(samples: Sequence[Mapping[str, Any]]) -> str:
    """协议 §7：26 条 sample 按 canonical_index 排序后的规范 JSON UTF-8 sha256。"""
    rows = [dict(row) for row in samples]
    rows.sort(key=lambda row: row["canonical_index"])
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(blob).hexdigest()


def _verify_py_sha256() -> str:
    path = Path(__file__).resolve().parent / "patch_events_verify.py"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def samples_from_freeze(records: Sequence[Mapping[str, Any]]) -> list[SensitivitySample]:
    """把冻结 sample 行转成现有 SensitivitySample。不改写文本。"""
    ordered = sorted(records, key=lambda row: row["canonical_index"])
    samples: list[SensitivitySample] = []
    for row in ordered:
        operator = row["operator"]
        overlap = row["token_overlap"]
        samples.append(
            SensitivitySample(
                sample_id=str(row["sample_id"]),
                stratum=str(row["stratum"]),
                operator=None if operator is None else int(operator),
                gold=row["gold"],
                kind=row["kind"],
                after_text=str(row["after_text"]),
                evidence_text=str(row["evidence_text"]),
                note=str(row.get("note") or ""),
                heuristic=str(row.get("heuristic") or ""),
                subcase=str(row.get("subcase") or ""),
                pair_id=str(row.get("pair_id") or ""),
                pair_role=str(row.get("pair_role") or ""),
                token_overlap=None if overlap is None else str(overlap),
                token_overlap_role=str(row.get("token_overlap_role") or ""),
                wice_note=str(row.get("wice_note") or ""),
                nli_construct_ok=str(row.get("nli_construct_ok") or ""),
                must_carry=bool(row.get("must_carry")),
                replaces=str(row.get("replaces") or ""),
                canonical_index=int(row["canonical_index"]),
            )
        )
    return samples


def assert_formal_freeze_structure(
    header: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
) -> list[SensitivitySample]:
    """跑前结构锁。不加载权重，不改 ρ/τ。"""
    if header.get("frozen_set_sha256") != FORMAL_FREEZE_SHA256:
        raise RuntimeError("冻结 header 的 sha256 不是正式冻结")
    if header.get("premature_pr_sha256_not_this_freeze") == FORMAL_FREEZE_SHA256:
        raise RuntimeError("正式冻结被写成了过早哈希")
    if float(header.get("bad_ok_false_min")) != BAD_OK_FALSE_MIN:
        raise RuntimeError("冻结 header 的 S2 ρ 与代码常量不一致")
    if float(header.get("correct_ok_true_min")) != CORRECT_OK_TRUE_MIN:
        raise RuntimeError("冻结 header 的 S3 ρ 与代码常量不一致")
    if float(header.get("tau")) != ENTAILMENT_TAU:
        raise RuntimeError("冻结 header 的 τ 与 ENTAILMENT_TAU 不一致")
    if header.get("model_id") != XNLI_MODEL_ID:
        raise RuntimeError("冻结 header 的 model_id 与 ADR-0040 不一致")
    if BAD_OK_FALSE_MIN != 0.90 or CORRECT_OK_TRUE_MIN != 0.70:
        raise RuntimeError("ρ 被改动，拒绝开跑")
    if ENTAILMENT_TAU != 0.5:
        raise RuntimeError("τ 被改动，拒绝开跑")
    if XNLI_MODEL_ID != "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7":
        raise RuntimeError("型号被改动，拒绝开跑")
    if _verify_py_sha256() != VERIFY_PY_SHA256:
        raise RuntimeError("patch_events_verify.py 字节与冻结仪器不一致，拒绝开跑")

    samples = samples_from_freeze(records)
    assert_set_s_locked(samples)
    by_id = {sample.sample_id: sample for sample in samples}
    if len(by_id) != 26:
        raise RuntimeError("正式 S 必须是 26 条")
    n_bad = sum(1 for sample in samples if sample.gold == "坏")
    n_correct = sum(1 for sample in samples if sample.gold == "正确")
    if n_bad != 20 or n_correct != 6:
        raise RuntimeError("正式 S 必须是 20 条坏槽 + 6 条正确对照")
    for retired in RETIRED_NOT_IN_FORMAL_S:
        if retired in by_id:
            raise RuntimeError(f"已退役槽仍在正式 S：{retired}")
    for excluded in EXCLUDED_NOT_IN_FORMAL_S:
        if excluded in by_id:
            raise RuntimeError(f"刻意不入集的刺激出现在正式 S：{excluded}")
    for sample_id in MUST_CARRY_IDS:
        sample = by_id.get(sample_id)
        if sample is None or sample.gold != "坏" or not sample.must_carry:
            raise RuntimeError(f"缺 must-carry：{sample_id}")

    chef03 = by_id["DIAG-CHEF-03-bad"]
    if "不少于 5 年" not in chef03.evidence_text or "不少于 3 年" not in chef03.after_text:
        raise RuntimeError("DIAG-CHEF-03-bad 必须是 5 年改为 3 年")
    if "不少于 3 年" in chef03.evidence_text:
        raise RuntimeError("DIAG-CHEF-03-bad 的证据侧年限被改动")
    chef03_good = by_id["DIAG-CHEF-03-good"]
    if chef03_good.after_text != "个人信息应当依法处理，留存不少于 5 年。":
        raise RuntimeError("DIAG-CHEF-03-good 年限被扰动")
    if chef03_good.after_text != chef03_good.evidence_text:
        raise RuntimeError("DIAG-CHEF-03-good 必须与证据同文")
    chef04 = by_id["DIAG-CHEF-04-bad"]
    if "大约" not in chef04.evidence_text or "大约" in chef04.after_text:
        raise RuntimeError("DIAG-CHEF-04-bad 必须删掉「大约」")
    if "不应当" in chef04.after_text:
        raise RuntimeError("DIAG-CHEF-04-bad 不得写成极端否定")

    pairs: dict[str, dict[str, SensitivitySample]] = {}
    for sample in samples:
        if not sample.pair_id:
            continue
        side = pairs.setdefault(sample.pair_id, {})
        if sample.gold in side:
            raise RuntimeError(f"CHEF 对 {sample.pair_id} 的 {sample.gold} 重复")
        side[sample.gold] = sample
    if set(pairs) != {"DIAG-CHEF-03", "DIAG-CHEF-04"}:
        raise RuntimeError("正式 S 只允许 DIAG-CHEF-03 与 DIAG-CHEF-04 两对")
    for pair_id, side in pairs.items():
        if set(side) != {"坏", "正确"}:
            raise RuntimeError(f"CHEF 对 {pair_id} 缺侧")
        if side["坏"].token_overlap != side["正确"].token_overlap:
            raise RuntimeError(f"{pair_id} 两侧冻结重叠不一致")
        overlap = side["坏"].token_overlap
        if overlap is None or float(overlap) < CHEF_TOKEN_OVERLAP_MIN:
            raise RuntimeError(f"{pair_id} 冻结 token_overlap < {CHEF_TOKEN_OVERLAP_MIN}")
    return samples


def chef_pair_validity(
    samples: Sequence[SensitivitySample],
    ok_by_id: Mapping[str, bool],
) -> dict[str, str]:
    """重叠用冻结值。好侧 ok 用本跑。无效对不从 S2 分母剔除。"""
    grouped: dict[str, dict[str, SensitivitySample]] = {}
    for sample in samples:
        if not sample.pair_id:
            continue
        grouped.setdefault(sample.pair_id, {})[sample.gold] = sample
    validity: dict[str, str] = {}
    for pair_id, side in grouped.items():
        overlap = side["坏"].token_overlap
        overlap_ok = overlap is not None and float(overlap) >= CHEF_TOKEN_OVERLAP_MIN
        good_ok = ok_by_id.get(side["正确"].sample_id) is True
        validity[pair_id] = "有效" if overlap_ok and good_ok else "无效"
    return validity


def _emit(log: TextIO | None, line: str) -> None:
    print(line, flush=True)
    if log is not None:
        log.write(line + "\n")
        log.flush()


def run_sens_live2(
    *,
    freeze_path: Path | None = None,
    log: TextIO | None = None,
) -> dict[str, Any]:
    """先打印正式冻结 sha256，再加载权重打分，跑后再哈希。

    正式 S 只来自冻结 jsonl。哈希不符则不调用 predict_xnli_probs。
    """
    header, records, raw_before = load_formal_freeze(freeze_path)
    samples = assert_formal_freeze_structure(header, records)
    digest = formal_freeze_sha256(records)
    _emit(log, f"FROZEN_S_SHA256 {digest}")
    if digest == PREMATURE_PR543_SHA256 or digest == OLD_INCODE_SET_SHA256:
        raise RuntimeError("打印到的哈希不是正式冻结，拒绝开跑")
    if digest != FORMAL_FREEZE_SHA256:
        raise RuntimeError("冻结 sha256 与正式冻结不一致，拒绝开跑")

    _emit(log, "BEGIN_SCORING")
    from freshlatch.eval import patch_events_verify as verify_mod

    scored: list[dict[str, Any]] = []
    for sample in samples:
        probs = verify_mod.predict_xnli_probs(sample.evidence_text, sample.after_text)
        verdict = dict(verify_edit(_verify_request(sample)))
        p_entail = float(probs["entailment"])
        argmax_label = max(probs, key=probs.__getitem__)
        ok_formula = argmax_label == "entailment" and p_entail >= ENTAILMENT_TAU
        if bool(verdict.get("ok")) != ok_formula:
            raise RuntimeError(f"{sample.sample_id} 的 ok 与公式不一致")
        scored.append(
            {
                "sample_id": sample.sample_id,
                "stratum": sample.stratum,
                "operator": sample.operator,
                "gold": sample.gold,
                "kind": sample.kind,
                "heuristic": sample.heuristic,
                "subcase": sample.subcase,
                "pair_id": sample.pair_id,
                "pair_role": sample.pair_role,
                "token_overlap": sample.token_overlap if sample.token_overlap is not None else "",
                "token_overlap_role": sample.token_overlap_role,
                "wice_note": sample.wice_note,
                "nli_construct_ok": sample.nli_construct_ok,
                "must_carry": sample.must_carry,
                "replaces": sample.replaces,
                "evidence_text": sample.evidence_text,
                "after_text": sample.after_text,
                "note": sample.note,
                "p_entail": p_entail,
                "p_neutral": float(probs["neutral"]),
                "p_contradiction": float(probs["contradiction"]),
                "argmax": argmax_label,
                "ok": verdict.get("ok"),
                "score": verdict.get("score"),
                "reason": verdict.get("reason"),
                "tau": ENTAILMENT_TAU,
                "model_id": XNLI_MODEL_ID,
            }
        )
        _emit(
            log,
            f"SCORED {sample.sample_id} ok={verdict.get('ok')} p_entail={p_entail:.10f}",
        )

    header_after, records_after, raw_after = load_formal_freeze(freeze_path)
    digest_after = formal_freeze_sha256(records_after)
    _emit(log, f"FROZEN_S_SHA256_AFTER {digest_after}")
    if raw_after != raw_before or digest_after != digest:
        raise RuntimeError("跑后冻结哈希与跑前不一致，整跑作废")
    if header_after.get("frozen_set_sha256") != FORMAL_FREEZE_SHA256:
        raise RuntimeError("跑后 header 哈希被改写，整跑作废")

    ok_by_id = {str(row["sample_id"]): row.get("ok") is True for row in scored}
    validity = chef_pair_validity(samples, ok_by_id)
    for row in scored:
        pair_id = str(row.get("pair_id") or "")
        row["pair_valid"] = validity.get(pair_id, "n/a") if pair_id else "n/a"

    summary = evaluate_s1_s4(scored)
    bad_ids = [str(row["sample_id"]) for row in scored if row.get("gold") == "坏"]
    if summary["n_bad"] != 20 or len(bad_ids) != 20:
        raise RuntimeError("S2 分母不是全部 20 条 gold=坏")
    for sample_id in MUST_CARRY_IDS:
        if sample_id not in bad_ids:
            raise RuntimeError(f"must-carry 被移出 S2 分母：{sample_id}")
    return {
        "summary": summary,
        "rows": scored,
        "frozen_sha256": digest,
        "pair_validity": validity,
        "activation_prerequisite_met": False,
        "gate_passed": False,
    }


def _fmt_prob(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.10f}"
    return ""


def _fmt_score(score: object) -> str:
    if isinstance(score, float) and math.isinf(score) and score < 0:
        return "−∞"
    if isinstance(score, float):
        return f"{score:.6f}"
    return "" if score is None else str(score)


def render_sens_live2_report(
    summary: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    frozen_sha256: str,
    pair_validity: Mapping[str, str],
    activation_prerequisite_met: bool,
    runtime_note: str,
    verify_py_sha256: str,
) -> str:
    """LIVE-2 证据页。activation_prerequisite_met 不得为真。"""
    if activation_prerequisite_met:
        raise ValueError("LIVE-2 不得写 activation_prerequisite_met=是")
    if frozen_sha256 != FORMAL_FREEZE_SHA256:
        raise ValueError("报告哈希不是正式冻结")
    if frozen_sha256 == PREMATURE_PR543_SHA256:
        raise ValueError("报告不得使用过早哈希")
    if summary["bad_ok_false_min"] != BAD_OK_FALSE_MIN or summary["tau"] != ENTAILMENT_TAU:
        raise ValueError("报告里的 τ/ρ 与现行门槛不一致")

    bad_rows = [row for row in rows if row.get("gold") == "坏"]
    correct_rows = [row for row in rows if row.get("gold") == "正确"]
    bad_reject = sum(1 for row in bad_rows if row.get("ok") is False)
    correct_accept = sum(1 for row in correct_rows if row.get("ok") is True)
    passed = bool(summary["sensitivity_passed"])
    if passed:
        outcome = (
            "S1–S4 在现行 ρ 下同时成立。这只是 L1 证据，供人审。"
            "不自动解锁激活，不开 PE-Y-05，不开 GATE 真探针，不开 n=400。"
        )
    else:
        outcome = (
            "未过现行 ρ。诚实失败。不放宽 τ，不降低 ρ，不把 must-carry 移出分母，不凑绿。"
        )

    lines: list[str] = [
        "# SENS-LIVE-2 · 正式敏感性 LIVE-2",
        "",
        "日期：2026-10-12（UTC+8）",
        "票：PE-Y-SENS-LIVE-2 · GitHub #542",
        "层身份：真模型推理层（非 stub）",
        "仪器：mDeBERTa-v3 XNLI · τ=0.5 · ok 当且仅当 argmax 为 entailment 且 P(entailment)≥τ",
        f"model_id：`{summary['model_id']}`",
        f"tau：`{summary['tau']}`",
        f"冻结名单 sha256：`{frozen_sha256}`",
        "正式 S：`docs/evidence/patch-events/SENS-S-FREEZE-formal-S.jsonl`（26 条 sample）",
        "跑前协议：`docs/evidence/patch-events/SENS-S-FREEZE-PROTOCOL.md`",
        "本跑协议：`docs/evidence/patch-events/SENS-LIVE-2-PROTOCOL.md`",
        "Trust：L1（正式 LIVE-2 证据）。过现行 ρ 也只供人审。本页不升格激活。",
        "",
        "## 1. 跑前锁",
        "",
        f"- 打分前打印的 sha256 = `{frozen_sha256}`，与 #544/#545 正式冻结相同。",
        "- 打分后再哈希，与跑前相同。冻结文件字节未改。",
        f"- 禁止把过早哈希 `{PREMATURE_PR543_SHA256}` 当作本冻结。未合 #543。",
        f"- 代码内 24 条 `SENSITIVITY_SET_S` 的旧哈希 `{OLD_INCODE_SET_SHA256}` 不是本页正式 S。该元组未改。",
        f"- `patch_events_verify.py` sha256：`{verify_py_sha256}`。",
        f"- 运行环境：{runtime_note}",
        "- 无 secret_names。未改 ADR-0040，未改 `ENTAILMENT_TAU`，未改 S2/S3 ρ。",
        "",
        "## 2. S1–S4（主读法）",
        "",
        "S2 分母是全部 `gold=坏` 的 20 条，含 must-carry `DIAG-CHEF-03-bad` 与 `DIAG-CHEF-04-bad`。",
        "CHEF 对无效时，坏侧仍留在分母里。",
        "",
        "| # | 条件 | 计数 | 结果 |",
        "|---|---|---|---|",
        (
            f"| S1 | 无 `score=None`；`ok=False` → `score=−∞` | "
            f"none={summary['n_score_none']}；reject={summary['n_reject']}；"
            f"−∞={summary['n_reject_neg_inf']} | "
            f"{'通过' if summary['s1'] else '未通过'} |"
        ),
        (
            f"| S2 | 坏→`ok=False` ≥ {summary['bad_ok_false_min']} | "
            f"{bad_reject}/{summary['n_bad']} = {summary['bad_ok_false_rate']:.4f} | "
            f"{'通过' if summary['s2'] else '未通过'} |"
        ),
        (
            f"| S3 | 正确→`ok=True` ≥ {summary['correct_ok_true_min']} | "
            f"{correct_accept}/{summary['n_correct']} = {summary['correct_ok_true_rate']:.4f} | "
            f"{'通过' if summary['s3'] else '未通过'} |"
        ),
        (
            f"| S4 | 型号/τ = ADR-0040 | `{summary['model_id']}` · `{summary['tau']}` | "
            f"{'通过' if summary['s4'] else '未通过'} |"
        ),
        "",
        f"**sensitivity_passed（S1∧S2∧S3∧S4）**：{'是' if passed else '否'}",
        "",
        "**gate_passed**：否",
        "",
        "**activation_prerequisite_met**：否",
        "",
        outcome,
        "",
        "## 3. 分层与 heuristic（描述，不是第二条通过线）",
        "",
        "| stratum | gold=坏 | 其中 ok=False | heuristic 分布（坏槽） |",
        "|---|---:|---:|---|",
    ]
    strata_seen: list[str] = []
    for row in bad_rows:
        stratum = str(row.get("stratum"))
        if stratum not in strata_seen:
            strata_seen.append(stratum)
    for stratum in strata_seen:
        group = [row for row in bad_rows if row.get("stratum") == stratum]
        rejected = sum(1 for row in group if row.get("ok") is False)
        heuristics: list[str] = []
        for row in group:
            name = str(row.get("heuristic") or "")
            if name not in heuristics:
                heuristics.append(name)
        lines.append(
            f"| {stratum} | {len(group)} | {rejected} | {', '.join(heuristics)} |"
        )
    lines.extend(
        [
            "",
            "## 4. CHEF 对",
            "",
            "好侧 `ok` 在本冻结文本上重测。冻结 `token_overlap` 不重算。",
            "好侧不为 `ok=True` 则整对无效。坏侧不移出 S2 分母。",
            "",
            "| pair_id | 冻结 token_overlap | 好侧 id | 好侧 ok | 坏侧 id | 坏侧 ok | 对 |",
            "|---|---:|---|---|---|---|---|",
        ]
    )
    by_id = {str(row.get("sample_id")): row for row in rows}
    for pair_id in ("DIAG-CHEF-03", "DIAG-CHEF-04"):
        bad = by_id[f"{pair_id}-bad"]
        good = by_id[f"{pair_id}-good"]
        lines.append(
            f"| {pair_id} | {bad.get('token_overlap')} | {good.get('sample_id')} | "
            f"{good.get('ok')} | {bad.get('sample_id')} | {bad.get('ok')} | "
            f"{pair_validity.get(pair_id, '')} |"
        )
    lines.extend(
        [
            "",
            "`DIAG-CHEF-03-good` 的 after 与 evidence 仍是「留存不少于 5 年」，年限未改成 3 年。",
            "",
            "## 5. 删除类 nli_construct_ok（meta-eval，不进主读法）",
            "",
            "下表只回显冻结时写下的 `nli_construct_ok` / `wice_note`。",
            "它不改 `gold`，不改 S2 分母，不改 τ，不改 ρ。",
            "",
            "| sample_id | gold | ok | nli_construct_ok | wice_note | 进入主读法 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        if row.get("stratum") != "删除":
            continue
        lines.append(
            f"| {row.get('sample_id')} | {row.get('gold')} | {row.get('ok')} | "
            f"{row.get('nli_construct_ok')} | {row.get('wice_note')} | 否 |"
        )
    lines.extend(
        [
            "",
            "## 6. DIAG ≠ S2",
            "",
            "SENS-DIAG-1A 的 P_entail 不是本页 S2。下表只复核同文刺激的仪器读数。",
            "S2 只用本跑 `ok`，分母是本冻结集的 20 条坏槽。",
            "",
            "| id | 本跑 P_entail | 本跑 ok | DIAG 页 P_entail | 绝对差 |",
            "|---|---:|---|---:|---:|",
        ]
    )
    for sample_id, archived in _DIAG_ARCHIVED_P_ENTAIL.items():
        row = by_id.get(sample_id)
        if row is None or not isinstance(row.get("p_entail"), float):
            continue
        got = float(row["p_entail"])
        lines.append(
            f"| {sample_id} | {got:.10f} | {row.get('ok')} | {archived:.10f} | "
            f"{abs(got - archived):.10f} |"
        )
    lines.extend(
        [
            "",
            "#538 的 `GATE-Y-SENSITIVITY.md` 仍写 S2 实测 0.7000、未通过。",
            "本页不改写那句，也不把那次失败改成过线。",
            "",
            "## 7. 逐条",
            "",
            "| sample_id | stratum | heuristic | op | gold | ok | P_entail | score | pair_valid | must_carry |",
            "|---|---|---|---:|---|---|---:|---|---|---|",
        ]
    )
    for row in rows:
        operator = row.get("operator")
        op_s = "" if operator is None else str(operator)
        lines.append(
            f"| {row.get('sample_id')} | {row.get('stratum')} | {row.get('heuristic')} | "
            f"{op_s} | {row.get('gold')} | {row.get('ok')} | {_fmt_prob(row.get('p_entail'))} | "
            f"{_fmt_score(row.get('score'))} | {row.get('pair_valid')} | {row.get('must_carry')} |"
        )
    lines.extend(
        [
            "",
            "## 8. 未做",
            "",
            "- 未写 `activation_prerequisite_met=是`。",
            "- 未解锁 PE-Y-05，未开 GATE 真探针，未开 n=400。",
            "- 未改 τ，未改 ρ，未改 ADR-0040，未改 `SENSITIVITY_SET_S`。",
            "- 未合并 #543，未沿用其过早哈希。",
            "- 无 secret_names。",
            "",
        ]
    )
    return "\n".join(lines)


def write_live2_scores_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    """真跑分表。UTF-8。"""
    fieldnames = [
        "sample_id",
        "stratum",
        "heuristic",
        "subcase",
        "operator",
        "gold",
        "kind",
        "pair_id",
        "pair_role",
        "pair_valid",
        "token_overlap",
        "token_overlap_role",
        "must_carry",
        "replaces",
        "wice_note",
        "nli_construct_ok",
        "evidence_text",
        "after_text",
        "p_entail",
        "p_neutral",
        "p_contradiction",
        "argmax",
        "ok",
        "score",
        "reason",
        "tau",
        "model_id",
        "note",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {}
            for key in fieldnames:
                value = row.get(key, "")
                out[key] = "" if value is None else value
            if isinstance(row.get("p_entail"), float):
                out["p_entail"] = f"{row['p_entail']:.10f}"
                out["p_neutral"] = f"{float(row['p_neutral']):.10f}"
                out["p_contradiction"] = f"{float(row['p_contradiction']):.10f}"
            score = row.get("score")
            if isinstance(score, float) and math.isinf(score):
                out["score"] = "-inf" if score < 0 else "inf"
            writer.writerow(out)


def assert_live2_protocol_file(path: Path) -> None:
    """本跑协议必须回显正式冻结，并点名禁止的过早哈希。"""
    text = path.read_text(encoding="utf-8")
    if FORMAL_FREEZE_SHA256 not in text:
        raise RuntimeError("LIVE-2 协议未回显正式冻结 sha256")
    if PREMATURE_PR543_SHA256 not in text:
        raise RuntimeError("LIVE-2 协议未标明禁止的过早哈希")
    if "BEGIN_SCORING" not in text:
        raise RuntimeError("LIVE-2 协议未写打分顺序")
    if "activation_prerequisite_met=否" not in text:
        raise RuntimeError("LIVE-2 协议未锁 activation_prerequisite_met=否")


def main() -> None:
    """真权重 LIVE-2。先锁哈希，再打分，再写报告。"""
    evidence = live2_evidence_dir()
    protocol = evidence / "SENS-LIVE-2-PROTOCOL.md"
    assert_live2_protocol_file(protocol)
    log_path = evidence / "SENS-LIVE-2-run.log"
    scores_path = evidence / "SENS-LIVE-2-scores.csv"
    report_path = evidence / "SENS-LIVE-2.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        payload = run_sens_live2(log=log)
        import torch
        import transformers

        runtime_note = (
            f"transformers {transformers.__version__}；torch {torch.__version__}；"
            f"cuda_available={torch.cuda.is_available()}；"
            "verify_edit 与 predict_xnli_probs 同一 ADR-0040 函数；"
            "权重来自本地 Hugging Face 缓存；无 secret_names"
        )
        _emit(log, runtime_note)
        _emit(log, "END_SCORING")
    text = render_sens_live2_report(
        payload["summary"],
        payload["rows"],
        frozen_sha256=payload["frozen_sha256"],
        pair_validity=payload["pair_validity"],
        activation_prerequisite_met=False,
        runtime_note=runtime_note,
        verify_py_sha256=_verify_py_sha256(),
    )
    if "activation_prerequisite_met**：是" in text:
        raise RuntimeError("报告写成了激活前置已满足")
    report_path.write_text(text, encoding="utf-8", newline="\n")
    write_live2_scores_csv(scores_path, payload["rows"])
    summary = payload["summary"]
    print(
        "S1-S4 "
        f"s1={summary['s1']} s2={summary['s2']} "
        f"s3={summary['s3']} s4={summary['s4']} "
        f"bad_rate={summary['bad_ok_false_rate']:.4f} "
        f"correct_rate={summary['correct_ok_true_rate']:.4f} "
        f"passed={summary['sensitivity_passed']} "
        f"activation_prerequisite_met=否",
        flush=True,
    )


if __name__ == "__main__":
    main()
