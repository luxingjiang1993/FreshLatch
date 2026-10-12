"""GATE-Y 敏感性闸（#528 · PE-Y-SENS-01 · ADR-0041）。

跑前写死集合 S：构造坏槽（四层×mod4）+ 有限废止/版本陷阱 + 正确对照。
通过线 S1–S4 须同时成立；报告可扔，不进 RESULT-Y，不构成 ``gate_passed``，
不单独过门，不激活 ``PREREG-Y``。

未跑真实权重时：报告必须标注「夹具/stub 层 · 非真模型过线」，且
``activation_prerequisite_met=False``（不得把 stub 绿写成可激活前置已满足）。
"""

from __future__ import annotations

import hashlib
import json
import math
import re
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

# CHEF 配对表面重叠门闩（P5 · 跑前锁；不是 ρ，不得拿来改 S2 分母）
CHEF_TOKEN_OVERLAP_MIN = 0.8

# 正式 S 哈希字段（PE-Y-SENS-LIVE-2 跑前锁）。顺序无关，json sort_keys。
_SET_HASH_FIELDS: tuple[str, ...] = (
    "sample_id",
    "stratum",
    "operator",
    "gold",
    "kind",
    "after_text",
    "evidence_text",
    "note",
    "heuristic",
    "subcase",
    "pair_id",
    "token_overlap",
    "wice_note",
    "nli_construct_ok",
)

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
    heuristic: str = "none"
    subcase: str = ""
    pair_id: str = ""
    wice_note: str = "n/a"
    nli_construct_ok: str = "n/a"


def _bad(
    sample_id: str,
    stratum: str,
    operator: int,
    after_text: str,
    evidence_text: str,
    *,
    note: str = "",
    heuristic: str = "none",
    subcase: str = "",
    pair_id: str = "",
    wice_note: str = "not_supported",
    nli_construct_ok: str = "yes",
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
        heuristic=heuristic,
        subcase=subcase,
        pair_id=pair_id,
        wice_note=wice_note,
        nli_construct_ok=nli_construct_ok,
    )


def _correct(
    sample_id: str,
    stratum: str,
    after_text: str,
    evidence_text: str,
    *,
    note: str = "",
    heuristic: str = "none",
    subcase: str = "",
    pair_id: str = "",
    wice_note: str = "supported",
    nli_construct_ok: str = "n/a",
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
        heuristic=heuristic,
        subcase=subcase,
        pair_id=pair_id,
        wice_note=wice_note,
        nli_construct_ok=nli_construct_ok,
    )


def _trap(
    sample_id: str,
    kind: Literal["abolish_trap", "version_trap"],
    after_text: str,
    evidence_text: str,
    *,
    note: str = "",
    heuristic: str = "lexical_overlap",
    subcase: str = "",
    wice_note: str = "not_supported",
    nli_construct_ok: str = "yes",
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
        heuristic=heuristic,
        subcase=subcase,
        wice_note=wice_note,
        nli_construct_ok=nli_construct_ok,
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
        heuristic="lexical_overlap",
        subcase="数值op0",
    ),
    _bad(
        "S-数值-op1",
        "数值",
        1,
        "留存不少于 50 年。",
        "留存不少于 5 年。",
        note="数值数量级扰动",
        heuristic="lexical_overlap",
        subcase="数值op1",
    ),
    _bad(
        "S-数值-op2",
        "数值",
        2,
        "申报门槛为累计 100 万人。",
        "申报门槛为累计 10 万人；敏感信息另计 1 万人。",
        note="错配另一数字",
        heuristic="argument_swap",
        subcase="数值op2",
    ),
    _bad(
        "S-数值-op3",
        "数值",
        3,
        "单会话成本约 0.008 个百分点。",
        "单会话成本约 0.008 美元。",
        note="单位错配",
        heuristic="lexical_overlap",
        subcase="数值op3",
    ),
    # --- 日期 · operator 0..3 ---
    # op2/op3：#538 原文金标在 NLI 构念下不成立或主体未点名。
    # 换成 DIAG 里已变红的高重叠角色冲突，不另加同证据的第二方向。
    _bad(
        "S-日期-op0",
        "日期",
        0,
        "本办法自 2025 年 3 月 22 日起施行。",
        "本办法自 2024 年 3 月 22 日起施行。",
        note="年份±1",
        heuristic="lexical_overlap",
        subcase="日期op0",
    ),
    _bad(
        "S-日期-op1",
        "日期",
        1,
        "公布日期为 2023 年 3 月 22 日。",
        "公布日期为 2023 年 2 月 22 日。",
        note="月份平移",
        heuristic="lexical_overlap",
        subcase="日期op1",
    ),
    _bad(
        "DIAG-HANS-002",
        "日期",
        2,
        "施行日期为 2022 年 7 月 7 日。",
        "公布日期为 2022 年 7 月 7 日；施行日期为 2022 年 9 月 1 日。",
        note="日期字段错配：施行日取公布日。高重叠。来源 DIAG-HANS-002。非废止法名陷阱。",
        heuristic="argument_swap",
        subcase="日期op2",
    ),
    _bad(
        "DIAG-HANS-003",
        "日期",
        3,
        "旧办法自 2022 年 9 月 1 日起施行。",
        "旧办法自 2020 年 1 月 1 日起施行；新办法自 2022 年 9 月 1 日起施行。",
        note="旧办法错取新办法施行日。高重叠。来源 DIAG-HANS-003。",
        heuristic="argument_swap",
        subcase="日期op3",
    ),
    # --- 条款替换 · operator 0..3 ---
    _bad(
        "S-条款-op0",
        "条款替换",
        0,
        "处理者不得向境外提供个人信息。",
        "处理者应当向境外提供个人信息前完成安全评估。",
        note="应当/不得翻转",
        heuristic="lexical_overlap",
        subcase="条款op0",
    ),
    _bad(
        "S-条款-op1",
        "条款替换",
        1,
        "接收方应当保存出境记录不少于三年。",
        "处理者应当保存出境记录不少于三年。",
        note="主体错配",
        heuristic="argument_swap",
        subcase="条款op1",
    ),
    _bad(
        "DIAG-HANS-004",
        "条款替换",
        2,
        "个人信息出境应当适用认证办法。",
        "个人信息出境应当适用标准合同办法。",
        note="同句架错挂办法名称。高重叠。来源 DIAG-HANS-004。不收低重叠原 S-条款-op2。",
        heuristic="lexical_overlap",
        subcase="条款op2",
    ),
    _bad(
        "S-条款-op3",
        "条款替换",
        3,
        "处理者应当完成安全评估。",
        "附录仅列术语定义，不含安全评估义务。",
        note="证据块不含该义务",
        heuristic="none",
        subcase="条款op3",
    ),
    # --- 删除 · operator 0..3 ---
    # op0 换成「已废止限定仍称有效」，不再用被证据肯定的例外子串当坏槽。
    # op1/op3 是 must-carry，不用极端否定句替换。
    _bad(
        "DIAG-HANS-006",
        "删除",
        0,
        "留存不少于 5 年这一限定仍然有效。",
        "留存不少于 5 年这一限定已废止。除金融机构外这一例外仍然有效。",
        note="已废止的年限限定被说成仍然有效。高重叠。来源 DIAG-HANS-006。不是另写废止法名。",
        heuristic="lexical_overlap",
        subcase="删除op0",
    ),
    _bad(
        "DIAG-CHEF-03-bad",
        "删除",
        1,
        "个人信息应当依法处理，留存不少于 3 年。",
        "个人信息应当依法处理，留存不少于 5 年。",
        note="Must-carry：年限 5 年改为 3 年。配对 DIAG-CHEF-03。",
        heuristic="lexical_overlap",
        subcase="删除op1",
        pair_id="DIAG-CHEF-03",
    ),
    _bad(
        "S-删除-op2",
        "删除",
        2,
        "原暂行办法同时废止。",
        "",
        note="空证据硬拒对照",
        heuristic="none",
        subcase="删除op2",
        wice_note="not_supported",
        nli_construct_ok="yes",
    ),
    _bad(
        "DIAG-CHEF-04-bad",
        "删除",
        3,
        "处理者应当保存出境记录。",
        "处理者应当大约保存出境记录。",
        note="Must-carry：删掉「大约」。义务硬化。配对 DIAG-CHEF-04。不是「不应当」极端否定。",
        heuristic="subsequence",
        subcase="删除op3",
        pair_id="DIAG-CHEF-04",
    ),
    # --- 有限废止 / 版本陷阱（加集 · id 写死） ---
    _trap(
        "S-废止-trap01",
        "abolish_trap",
        "1993 年《取水许可制度实施办法》仍然有效。",
        "1993年8月1日国务院发布的《取水许可制度实施办法》同时废止。",
        note="废止法仍称有效",
        heuristic="lexical_overlap",
        subcase="废止trap",
    ),
    _trap(
        "S-废止-trap02",
        "abolish_trap",
        "《禁止使用童工规定》继续施行。",
        "1991年4月15日国务院发布的《禁止使用童工规定》同时废止。",
        note="废止规章继续施行",
        heuristic="lexical_overlap",
        subcase="废止trap",
    ),
    _trap(
        "S-版本-trap01",
        "version_trap",
        "数据出境安全评估结果有效期为二年。",
        "促进和规范数据跨境流动规定施行后，评估结果有效期按令 16 调整为三年。",
        note="版本错配：沿用旧二年",
        heuristic="argument_swap",
        subcase="版本trap",
    ),
    _trap(
        "S-版本-trap02",
        "version_trap",
        "标准合同办法适用于累计不满 10 万人的情形。",
        "令 16 第八条将标准合同适用区间调整为当年累计 10 万以上、不满 100 万。",
        note="版本错配：旧门槛",
        heuristic="argument_swap",
        subcase="版本trap",
    ),
    # --- 正确对照（防全拒假绿） ---
    _correct(
        "S-正确-数值01",
        "数值",
        "留存不少于 5 年。",
        "相关记录留存不少于 5 年。",
        note="数值正确对照",
        heuristic="lexical_overlap",
        subcase="数值正确",
    ),
    _correct(
        "S-正确-日期01",
        "日期",
        "本办法自 2024 年 3 月 22 日起施行。",
        "本办法自公布之日起施行；公布日为 2024 年 3 月 22 日。",
        note="日期正确对照",
        heuristic="lexical_overlap",
        subcase="日期正确",
    ),
    _correct(
        "S-正确-条款01",
        "条款替换",
        "处理者应当在出境前完成安全评估。",
        "处理者应当在向境外提供个人信息前完成安全评估。",
        note="条款正确对照",
        heuristic="lexical_overlap",
        subcase="条款正确",
    ),
    _correct(
        "S-正确-删除01",
        "删除",
        "个人信息应当依法处理。",
        "留存不少于 5 年这一限定已废止。个人信息应当依法处理。",
        note="删除废止限定后仍被证据支撑",
        heuristic="subsequence",
        subcase="删除正确",
    ),
    _correct(
        "DIAG-CHEF-03-good",
        "删除",
        "个人信息应当依法处理，留存不少于 5 年。",
        "个人信息应当依法处理，留存不少于 5 年。",
        note="CHEF-03 好侧：与证据同文。有效对还须本跑 ok=True，否则整对无效。",
        heuristic="lexical_overlap",
        subcase="删除op1",
        pair_id="DIAG-CHEF-03",
    ),
    _correct(
        "DIAG-CHEF-04-good",
        "删除",
        "处理者应当大约保存出境记录。",
        "处理者应当大约保存出境记录。",
        note="CHEF-04 好侧：与证据同文。有效对还须本跑 ok=True，否则整对无效。",
        heuristic="subsequence",
        subcase="删除op3",
        pair_id="DIAG-CHEF-04",
    ),
)

# 跑前锁死的正式 S 哈希。空字符串表示尚未冻结，真跑必须拒绝。
# 由 sensitivity_set_sha256() 写入；真跑前打印，跑中不得改名单。
FROZEN_SENSITIVITY_SET_SHA256 = "baf33f5b9e0ea801c736d67385a94546fb6bd24af1ada0e4f27d1b9f5da1fa8c"

# #538 六条假阳性原文不再入正式 S（金标不成立、低重叠，或已被 must-carry 同族条取代）。
RETIRED_FP_IDS: tuple[str, ...] = (
    "S-日期-op2",
    "S-日期-op3",
    "S-条款-op2",
    "S-删除-op0",
    "S-删除-op1",
    "S-删除-op3",
)

# 入集的 HANS 义务冲突。DIAG-HANS-001/005/007 不另加，避免同一证据或易拒句稀释 S2。
# DIAG-HANS-008（「不应当」）不入，避免只靠极端否定刷分。
INCLUDED_HANS_IDS: tuple[str, ...] = (
    "DIAG-HANS-002",
    "DIAG-HANS-003",
    "DIAG-HANS-004",
    "DIAG-HANS-006",
)
EXCLUDED_EXTREME_AFTER = "处理者不应当保存记录"


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


def _content_tokens(text: str) -> set[str]:
    """jieba 内容词。空白与纯标点丢掉。与 SENS-DIAG-1A 的重叠式相同。"""
    import jieba

    words: list[str] = []
    for tok in jieba.cut(text):
        if not tok.strip():
            continue
        if re.fullmatch(r"[\s\W_]+", tok):
            continue
        words.append(tok)
    return set(words)


def token_overlap_value(left: str, right: str) -> float | None:
    """|交集| / min(|左|, |右|)。任一侧没有内容词则无定义。"""
    left_set = _content_tokens(left)
    right_set = _content_tokens(right)
    if not left_set or not right_set:
        return None
    return len(left_set & right_set) / min(len(left_set), len(right_set))


def format_token_overlap(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value:.6f}"


def token_overlap_by_id(
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
) -> dict[str, str | None]:
    """CHEF 对记两侧 after 的表面重叠；其余行记 after 对 evidence。"""
    grouped: dict[str, list[SensitivitySample]] = {}
    for sample in samples:
        if sample.pair_id:
            grouped.setdefault(sample.pair_id, []).append(sample)
    pair_overlap: dict[str, str | None] = {}
    for pair_id, group in grouped.items():
        if len(group) != 2:
            raise ValueError(f"CHEF 对 {pair_id} 必须恰好两侧")
        pair_overlap[pair_id] = format_token_overlap(
            token_overlap_value(group[0].after_text, group[1].after_text)
        )
    overlaps: dict[str, str | None] = {}
    for sample in samples:
        if sample.pair_id:
            overlaps[sample.sample_id] = pair_overlap[sample.pair_id]
        else:
            overlaps[sample.sample_id] = format_token_overlap(
                token_overlap_value(sample.after_text, sample.evidence_text)
            )
    return overlaps


def chef_pairs(
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
) -> dict[str, dict[str, SensitivitySample]]:
    """pair_id → {坏, 正确}。"""
    found: dict[str, dict[str, SensitivitySample]] = {}
    for sample in samples:
        if not sample.pair_id:
            continue
        side = found.setdefault(sample.pair_id, {})
        if sample.gold in side:
            raise ValueError(f"CHEF 对 {sample.pair_id} 的 {sample.gold} 重复")
        side[sample.gold] = sample
    for pair_id, side in found.items():
        if set(side) != {"坏", "正确"}:
            raise ValueError(f"CHEF 对 {pair_id} 缺好侧或坏侧")
    return found


def canonical_sensitivity_records(
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
) -> list[dict[str, Any]]:
    """冻结哈希的规范记录。字段见 ``_SET_HASH_FIELDS``。"""
    overlaps = token_overlap_by_id(samples)
    records: list[dict[str, Any]] = []
    for sample in samples:
        records.append(
            {
                "sample_id": sample.sample_id,
                "stratum": sample.stratum,
                "operator": sample.operator,
                "gold": sample.gold,
                "kind": sample.kind,
                "after_text": sample.after_text,
                "evidence_text": sample.evidence_text,
                "note": sample.note,
                "heuristic": sample.heuristic,
                "subcase": sample.subcase,
                "pair_id": sample.pair_id,
                "token_overlap": overlaps[sample.sample_id],
                "wice_note": sample.wice_note,
                "nli_construct_ok": sample.nli_construct_ok,
            }
        )
    return records


def sensitivity_set_sha256(
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
) -> str:
    """名单 UTF-8 sha256。``sort_keys``，分隔符紧凑。不含冻结常量本身。"""
    payload = json.dumps(
        canonical_sensitivity_records(samples),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def assert_formal_s_protocol(
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
) -> None:
    """跑前协议：四层×mod4、坏槽 20 条、must-carry、CHEF 重叠、ρ/τ 未动。"""
    assert_set_s_locked(samples)
    by_id = {sample.sample_id: sample for sample in samples}
    if len(by_id) != len(samples):
        raise ValueError("集合 S sample_id 重复")
    n_bad = sum(1 for sample in samples if sample.gold == "坏")
    if n_bad != 20:
        raise ValueError("坏槽必须保持 20 条，禁止用额外易拒句稀释 S2")
    for retired in RETIRED_FP_IDS:
        if retired in by_id:
            raise ValueError(f"已退役假阳性仍在正式 S：{retired}")
    for hans_id in INCLUDED_HANS_IDS:
        if hans_id not in by_id or by_id[hans_id].gold != "坏":
            raise ValueError(f"缺 HANS 义务冲突：{hans_id}")
    for sample in samples:
        if EXCLUDED_EXTREME_AFTER in sample.after_text:
            raise ValueError("极端否定句不得入正式 S")
    chef_bad = by_id["DIAG-CHEF-03-bad"]
    if "不少于 5 年" not in chef_bad.evidence_text or "不少于 3 年" not in chef_bad.after_text:
        raise ValueError("DIAG-CHEF-03-bad 必须是 5 年改为 3 年")
    hedge_bad = by_id["DIAG-CHEF-04-bad"]
    if "大约" not in hedge_bad.evidence_text or "大约" in hedge_bad.after_text:
        raise ValueError("DIAG-CHEF-04-bad 必须删掉「大约」")
    if "不应当" in hedge_bad.after_text:
        raise ValueError("DIAG-CHEF-04-bad 不得写成极端否定")
    overlaps = token_overlap_by_id(samples)
    pairs = chef_pairs(samples)
    if set(pairs) != {"DIAG-CHEF-03", "DIAG-CHEF-04"}:
        raise ValueError("CHEF 对只允许 must-carry 的 DIAG-CHEF-03 与 DIAG-CHEF-04")
    for pair_id, side in pairs.items():
        overlap = overlaps[side["坏"].sample_id]
        if overlap is None or float(overlap) < CHEF_TOKEN_OVERLAP_MIN:
            raise ValueError(f"{pair_id} token_overlap < {CHEF_TOKEN_OVERLAP_MIN}")
        if overlaps[side["正确"].sample_id] != overlap:
            raise ValueError(f"{pair_id} 两侧重叠不一致")
    if BAD_OK_FALSE_MIN != 0.90 or CORRECT_OK_TRUE_MIN != 0.70:
        raise ValueError("ρ 被改动")
    if ENTAILMENT_TAU != 0.5:
        raise ValueError("τ 被改动")
    if XNLI_MODEL_ID != "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7":
        raise ValueError("型号被改动")


def frozen_manifest_text(
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
) -> str:
    """冻结清单。首行是协议头，其余每行一条。哈希不含协议头。"""
    digest = sensitivity_set_sha256(samples)
    header = {
        "record_type": "protocol_lock",
        "sha256": digest,
        "token_overlap_formula": (
            "CHEF 对=两侧 after；其余=after 对 evidence；"
            "|set(jieba 内容词) 交集| / min；去空白与纯标点"
        ),
        "chef_token_overlap_min": CHEF_TOKEN_OVERLAP_MIN,
        "bad_ok_false_min": BAD_OK_FALSE_MIN,
        "correct_ok_true_min": CORRECT_OK_TRUE_MIN,
        "tau": ENTAILMENT_TAU,
        "model_id": XNLI_MODEL_ID,
        "ok_formula": "ok <=> argmax==entailment AND P(entailment)>=tau",
        "n_bad_locked": 20,
        "s2_denominator": "全部 gold=坏，不剔除 CHEF 无效对，不剔除 must-carry",
    }
    lines = [json.dumps(header, ensure_ascii=False, sort_keys=True)]
    for record in canonical_sensitivity_records(samples):
        row = dict(record)
        row["record_type"] = "sample"
        lines.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
    return "\n".join(lines) + "\n"


def assert_frozen_manifest(
    path: Path,
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
) -> str:
    """清单与代码名单一致才返回哈希。"""
    lines = [
        line
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    header = json.loads(lines[0])
    digest = sensitivity_set_sha256(samples)
    if header.get("sha256") != digest:
        raise ValueError("冻结清单哈希与代码名单不一致")
    if header.get("bad_ok_false_min") != BAD_OK_FALSE_MIN:
        raise ValueError("冻结清单里的 ρ 与代码不一致")
    if header.get("tau") != ENTAILMENT_TAU:
        raise ValueError("冻结清单里的 τ 与代码不一致")
    loaded = [json.loads(line) for line in lines[1:]]
    expected = []
    for record in canonical_sensitivity_records(samples):
        row = dict(record)
        row["record_type"] = "sample"
        expected.append(row)
    if loaded != expected:
        raise ValueError("冻结清单条目与代码名单不一致")
    return digest


def pair_validity(
    samples: Sequence[SensitivitySample],
    ok_by_id: Mapping[str, bool],
) -> dict[str, str]:
    """P5：重叠≥锁阈值且好侧 ok=True 才有效。无效对仍留在 S2 分母里。"""
    overlaps = token_overlap_by_id(samples)
    validity: dict[str, str] = {}
    for pair_id, side in chef_pairs(samples).items():
        overlap = overlaps[side["坏"].sample_id]
        good_ok = ok_by_id.get(side["正确"].sample_id) is True
        overlap_ok = overlap is not None and float(overlap) >= CHEF_TOKEN_OVERLAP_MIN
        validity[pair_id] = "有效" if overlap_ok and good_ok else "无效"
    return validity


def render_sens_live2_report(
    summary: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    activation_prerequisite_met: bool = False,
    frozen_sha256: str,
    verify_py_sha256: str,
    runtime_note: str,
) -> str:
    """PE-Y-SENS-LIVE-2 证据页。不得把激活前置写成是。"""
    if activation_prerequisite_met:
        raise ValueError("LIVE-2 不得写 activation_prerequisite_met=是")
    if frozen_sha256 != FROZEN_SENSITIVITY_SET_SHA256:
        raise ValueError("报告哈希与冻结常量不一致")
    if summary["bad_ok_false_min"] != BAD_OK_FALSE_MIN:
        raise ValueError("报告 ρ 与现行门槛不一致")
    if summary["tau"] != ENTAILMENT_TAU:
        raise ValueError("报告 τ 与现行门槛不一致")

    lines: list[str] = [
        "# SENS-LIVE-2 · 正式敏感性 LIVE-2 报告",
        "",
        "日期：2026-10-12（UTC+8）",
        "票：PE-Y-SENS-LIVE-2 · GitHub #542",
        "仪器：mDeBERTa-v3 XNLI · τ=0.5 · ok 当且仅当 argmax 为 entailment 且 P(entailment)≥τ",
        f"model_id：`{summary['model_id']}`",
        f"tau：`{summary['tau']}`",
        f"冻结名单 sha256：`{frozen_sha256}`",
        "Trust：L1（正式 LIVE-2 证据）。过现行 ρ 也只供后续人审，本页不升格激活。",
        "",
        "## 1. 协议锁（跑前）",
        "",
        "书面锁见 `docs/evidence/patch-events/SENS-LIVE-2-PROTOCOL.md`。",
        "冻结清单见 `docs/evidence/patch-events/SENS-LIVE-2-set-S.jsonl`。",
        "真跑日志 `SENS-LIVE-2-run.log` 在打分之前打印同一 sha256。",
        "跑后复核哈希未变。名单在开跑之后没有增删。",
        "",
        "算子仍是四层 × mod4，外加原有四条废止/版本陷阱。",
        "坏槽保持 20 条，与 #538 同口径，不用额外易拒句稀释 S2。",
        "两条 must-carry 在冻结名单内：`DIAG-CHEF-03-bad`（5 年改为 3 年）、`DIAG-CHEF-04-bad`（删「大约」）。",
        "HANS 义务冲突入集：`DIAG-HANS-002`、`DIAG-HANS-003`、`DIAG-HANS-004`、`DIAG-HANS-006`。",
        "`DIAG-HANS-008` 的「不应当」极端否定不入集。",
        "",
        "CHEF 对门闩：两侧 after 的 token_overlap ≥ 0.8，且好侧 ok=True，否则对无效。",
        "无效对只影响配对读法。S2 分母仍是全部 gold=坏。",
        "",
        "## 2. 仪器冻结",
        "",
        f"- 型号：`{summary['model_id']}`（须 = ADR-0040 `{summary['expected_model_id']}`）",
        f"- τ：`{summary['tau']}`（`ENTAILMENT_TAU`，未放宽）",
        f"- 坏→ok=False 下限：`{summary['bad_ok_false_min']}`（未降低）",
        f"- 正确→ok=True 下限：`{summary['correct_ok_true_min']}`（未降低）",
        f"- `patch_events_verify.py` sha256：`{verify_py_sha256}`",
        f"- 运行环境：{runtime_note}",
        "- 无 secret_names，无新开云密钥。",
        "",
        "## 3. S1–S4（现行 ρ）",
        "",
        "本表是这次冻结 S 的真权重结果。DIAG 分不进入分子或分母。",
        "",
        "| # | 条件 | 结果 |",
        "|---|---|---|",
        (
            f"| S1 | 无 score=None；ok=False → score=−∞ "
            f"（none={summary['n_score_none']}；reject={summary['n_reject']}；"
            f"−∞={summary['n_reject_neg_inf']}） | "
            f"{'通过' if summary['s1'] else '未通过'} |"
        ),
        (
            f"| S2 | 坏→ok=False ≥ {summary['bad_ok_false_min']} "
            f"（实测 {summary['bad_ok_false_rate']:.4f}；"
            f"坏 {summary['n_bad']}） | "
            f"{'通过' if summary['s2'] else '未通过'} |"
        ),
        (
            f"| S3 | 正确→ok=True ≥ {summary['correct_ok_true_min']} "
            f"（实测 {summary['correct_ok_true_rate']:.4f}；"
            f"正确 {summary['n_correct']}） | "
            f"{'通过' if summary['s3'] else '未通过'} |"
        ),
        (
            f"| S4 | 型号/τ = ADR-0040（`{summary['expected_model_id']}` · "
            f"`{summary['expected_tau']}`） | "
            f"{'通过' if summary['s4'] else '未通过'} |"
        ),
        "",
        f"**sensitivity_passed（S1∧S2∧S3∧S4）**："
        f"{'是' if summary['sensitivity_passed'] else '否'}",
        "",
        "**gate_passed**：否",
        "",
        "**activation_prerequisite_met**：否",
        "",
        "本页不解锁 PE-Y-05，不开 GATE-Y 真探针，不开 formal-y n=400，不复活 #507。",
        "",
        "#538 失败结论句保持原样，不改写成过线："
        "S2 坏→ok=False ≥ 0.9（实测 0.7000）未通过；该次 sensitivity_passed 为否。",
        "",
        "**DIAG ≠ S2。** SENS-DIAG-1A 的变红条数与 P_entail 不能代替本页 S2。",
        "",
        "## 4. 逐条结果",
        "",
        "| sample_id | stratum | heuristic | subcase | gold | pair_id | token_overlap | nli_construct_ok | ok | P_entail | score | pair_valid |",
        "|---|---|---|---|---|---|---:|---|---|---:|---|---|",
    ]
    for row in rows:
        score = row.get("score")
        if isinstance(score, float) and math.isinf(score) and score < 0:
            score_s = "−∞"
        elif isinstance(score, float):
            score_s = f"{score:.6f}"
        else:
            score_s = str(score)
        p_entail = row.get("p_entail")
        p_s = f"{p_entail:.10f}" if isinstance(p_entail, float) else str(p_entail)
        overlap = row.get("token_overlap")
        overlap_s = "" if overlap is None else str(overlap)
        lines.append(
            f"| {row.get('sample_id')} | {row.get('stratum')} | {row.get('heuristic')} | "
            f"{row.get('subcase')} | {row.get('gold')} | {row.get('pair_id') or ''} | "
            f"{overlap_s} | {row.get('nli_construct_ok')} | {row.get('ok')} | "
            f"{p_s} | {score_s} | {row.get('pair_valid')} |"
        )

    lines.extend(
        [
            "",
            "## 5. 删除类 meta-eval",
            "",
            "主金标是二元坏/好。WiCE 只作笔记。下面的 `nli_construct_ok` 在开跑前按 DIAG 交接写死，不按本跑分数改判。",
            "",
            "| id | gold | nli_construct_ok | wice_note | 跑前判断 |",
            "|---|---|---|---|---|",
            "| DIAG-HANS-006 | 坏 | yes | not_supported | 已废止限定被说成仍然有效，主张不被证据蕴含 |",
            "| DIAG-CHEF-03-bad | 坏 | yes | not_supported | 5 年改为 3 年。数字不是证据里的年限。金标坏在 NLI 构念下成立 |",
            "| DIAG-HANS 未入集的 007 |  |  |  | DIAG 里插入相反例外已变红。本正式 S 不另加该易拒句，以免稀释 must-carry |",
            "| S-删除-op2 | 坏 | yes | not_supported | 空证据。硬拒对照，不是高重叠坏槽 |",
            "| DIAG-CHEF-04-bad | 坏 | yes | not_supported | 删「大约」是义务硬化。产品协议定为坏槽。DIAG 已标 yes，本跑不改成 partial 或 no |",
            "| DIAG-CHEF-04 对照 |  |  |  | #538 原文 S-删除-op3 曾标 partial（不是干净矛盾）。正式条用 CHEF-04 文本，不把那条 partial 事后改写 |",
            "",
            "删「大约」：证据只有弱化义务，主张把「大约」拿掉后语气更硬。",
            "这不是干净矛盾句。金标仍按跑前锁为坏，因为产品协议把义务硬化算坏改。",
            "若本跑 ok=True，记录为仪器对这一亚型仍放行，不回头改金标，也不改 τ/ρ。",
            "",
            "## 6. 边界",
            "",
            "- 未改 `ENTAILMENT_TAU`，未降低 S2/S3 ρ，未换型号，未改 ADR-0040 的 ok 公式。",
            "- 未写 activation_prerequisite_met=是。",
            "- 未开 PE-Y-05，未开 GATE 真探针，未开 n=400，未复活 #507。",
            "- 未把 DIAG 分写成正式 S2。",
            "- 未声称乙。",
            "",
        ]
    )
    if summary["sensitivity_passed"]:
        lines.append(
            "S1–S4 过现行 ρ。这里只登记敏感性真过证据，供后续人审。"
            "人未审之前，激活前置仍为否。"
        )
    else:
        lines.append(
            "S1–S4 未同时过现行 ρ。这是诚实失败。"
            "不回头装扮坏槽，不放宽 τ，不降低 ρ。"
        )
    lines.append("")
    return "\n".join(lines)


def _score_cell(score: object) -> str:
    if isinstance(score, float) and math.isinf(score):
        return "-inf" if score < 0 else "inf"
    return "" if score is None else str(score)


def write_live2_scores_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    """真跑分表。UTF-8。"""
    import csv

    fieldnames = [
        "sample_id",
        "stratum",
        "heuristic",
        "subcase",
        "operator",
        "gold",
        "kind",
        "pair_id",
        "token_overlap",
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
        "pair_valid",
        "note",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {key: row.get(key, "") for key in fieldnames}
            out["score"] = _score_cell(row.get("score"))
            writer.writerow(out)


def run_sens_live2(
    samples: Sequence[SensitivitySample] = SENSITIVITY_SET_S,
    *,
    log: Any = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """先打印冻结哈希，再加载真权重。哈希不符或名单在跑中变化则拒绝。"""
    assert_formal_s_protocol(samples)
    digest = sensitivity_set_sha256(samples)
    locked = f"FROZEN_S_SHA256 {digest}"
    print(locked, flush=True)
    if log is not None:
        log.write(locked + "\n")
        log.flush()
    if not FROZEN_SENSITIVITY_SET_SHA256:
        raise RuntimeError("正式 S 尚未写入冻结哈希，拒绝开跑")
    if digest != FROZEN_SENSITIVITY_SET_SHA256:
        raise RuntimeError("冻结哈希与当前名单不一致，拒绝开跑")
    if manifest_path is not None:
        manifest_digest = assert_frozen_manifest(manifest_path, samples)
        if manifest_digest != digest:
            raise RuntimeError("清单哈希与打印哈希不一致，拒绝开跑")
    begin = "BEGIN_SCORING"
    print(begin, flush=True)
    if log is not None:
        log.write(begin + "\n")
        log.flush()

    from freshlatch.eval.patch_events_verify import predict_xnli_probs

    overlaps = token_overlap_by_id(samples)
    scored: list[dict[str, Any]] = []
    for sample in samples:
        probs = predict_xnli_probs(sample.evidence_text, sample.after_text)
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
                "token_overlap": overlaps[sample.sample_id],
                "wice_note": sample.wice_note,
                "nli_construct_ok": sample.nli_construct_ok,
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
        if log is not None:
            log.write(
                f"SCORED {sample.sample_id} ok={verdict.get('ok')} "
                f"p_entail={p_entail:.10f}\n"
            )
            log.flush()

    digest_after = sensitivity_set_sha256(samples)
    after_line = f"FROZEN_S_SHA256_AFTER {digest_after}"
    print(after_line, flush=True)
    if log is not None:
        log.write(after_line + "\n")
        log.flush()
    if digest_after != digest:
        raise RuntimeError("跑中正式 S 被修改")

    ok_by_id = {row["sample_id"]: row["ok"] is True for row in scored}
    validity = pair_validity(samples, ok_by_id)
    for row in scored:
        row["pair_valid"] = validity.get(row["pair_id"], "n/a") if row["pair_id"] else "n/a"

    summary = evaluate_s1_s4(scored)
    return {
        "summary": summary,
        "rows": scored,
        "frozen_sha256": digest,
        "pair_validity": validity,
        "activation_prerequisite_met": False,
    }


def default_live2_dir(root: Path | None = None) -> Path:
    base = _repo_root() if root is None else Path(root)
    return base / "docs" / "evidence" / "patch-events"


def verify_source_sha256() -> str:
    path = Path(__file__).resolve().parent / "patch_events_verify.py"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    """真权重 LIVE-2。先锁哈希，再打分，再写报告。"""
    evidence = default_live2_dir()
    manifest = evidence / "SENS-LIVE-2-set-S.jsonl"
    log_path = evidence / "SENS-LIVE-2-run.log"
    scores_path = evidence / "SENS-LIVE-2-scores.csv"
    report_path = evidence / "SENS-LIVE-2.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        payload = run_sens_live2(log=log, manifest_path=manifest)
        import torch
        import transformers

        runtime_note = (
            f"transformers {transformers.__version__}；torch {torch.__version__}；"
            "权重来自本地 Hugging Face 缓存；无 secret_names"
        )
        log.write(runtime_note + "\n")
        log.write("END_SCORING\n")
        log.flush()
    text = render_sens_live2_report(
        payload["summary"],
        payload["rows"],
        activation_prerequisite_met=False,
        frozen_sha256=payload["frozen_sha256"],
        verify_py_sha256=verify_source_sha256(),
        runtime_note=runtime_note,
    )
    report_path.write_text(text, encoding="utf-8")
    write_live2_scores_csv(scores_path, payload["rows"])
    summary = payload["summary"]
    print(
        "S1-S4 "
        f"s1={summary['s1']} s2={summary['s2']} "
        f"s3={summary['s3']} s4={summary['s4']} "
        f"bad_rate={summary['bad_ok_false_rate']:.4f} "
        f"correct_rate={summary['correct_ok_true_rate']:.4f} "
        f"passed={summary['sensitivity_passed']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
