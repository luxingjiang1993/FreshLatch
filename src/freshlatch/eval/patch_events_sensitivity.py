"""GATE-Y 敏感性闸（#528 · PE-Y-SENS-01 · ADR-0041）。

跑前写死集合 S：构造坏槽（四层×mod4）+ 有限废止/版本陷阱 + 正确对照。
通过线 S1–S4 须同时成立；报告可扔，不进 RESULT-Y，不构成 ``gate_passed``，
不单独过门，不激活 ``PREREG-Y``。

未跑真实权重时：报告必须标注「夹具/stub 层 · 非真模型过线」，且
``activation_prerequisite_met=False``（不得把 stub 绿写成可激活前置已满足）。
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

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
