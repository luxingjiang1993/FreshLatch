"""仓外 GATE-Y 探针（可扔 · 非乙成立 · 不进主表 · 默认不发模型）。

跑前写死过门判据，禁止 HARKing。过门 = k≥10 ∧ T−C 固定 k 误放差点估计>0
（方向门；**不用**正式乙点>0.05）；T−B1 / T−B2 必报，**不**进 ``gate_passed``。

#530 / ADR-0041：真数据探针硬前置 = 敏感性闸通过 ∧ ``activation_prerequisite_met``
∧ 非 stub/夹具层。冒烟 / 夹具 / 敏感性本身均不构成 ``gate_passed``。

本模块最多把门闩打到「可建议人审激活」；不激活 ``PREREG-Y``，不开正式主跑，
不写 ``RESULT-Y`` 成立格。禁止把 ``#479`` / ``GATE-K-PROBE`` / ``GATE-C-FIXTURE``
升格为本页已过门。夹具绿 ≠ 真数据过门。

默认：落协议报告 + 停在可发送边界（等待探针人令）。
``--authorize-send``：须同时提供逐字探针人令
「授权路线 Y 仓外探针发模型；不得激活。」才允许发模型；旁路写入
``gate-y-probe-generations.jsonl``，不得污染 formal / formal-b / formal-y / formal-c。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
from freshlatch.eval.patch_events_sensitivity import (
    REPORT_LAYER_REAL,
    REPORT_LAYER_STUB,
    default_report_path as default_sensitivity_report_path,
)
from freshlatch.eval.patch_events_verify import verify_edit
from freshlatch.eval import patch_events_formal as _formal
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_K_FLOOR = 10
# 过门方向门：点估计 > 此值。正式乙成立尺 0.05 不得写入本 Cond。
_GATE_Y_POINT_FLOOR = 0.0
_PRIMARY_ORDER = ("T-C", "T-B1", "T-B2")
_DEFAULT_REPORT = Path("docs/evidence/patch-events/GATE-Y-PROBE.md")
_PROBE_GENERATIONS_REL = Path("docs/evidence/patch-events/gate-y-probe-generations.jsonl")
_FORMAL_GENERATIONS_REL = Path("docs/evidence/patch-events/formal-generations.jsonl")
_FORMAL_B_REL = Path("docs/evidence/patch-events/formal-generations-b.jsonl")
_FORMAL_Y_REL = Path("docs/evidence/patch-events/formal-generations-y.jsonl")
_FORMAL_C_REL = Path("docs/evidence/patch-events/formal-generations-c.jsonl")
# 探针发送：同 after 下 B1 不另发 rewrite；C/T rewrite + B2 claim，再补 B2 diff。
_PROBE_SEND: tuple[tuple[str, str], ...] = (
    ("C", "rewrite"),
    ("T", "rewrite"),
    ("B2", "claim"),
)
_AWAITING = "等待授权发模型"
_PROBE_AUTH_PHRASE = "授权路线 Y 仓外探针发模型；不得激活。"
_FORBIDDEN_PASS_EVIDENCE = (
    "#479",
    "GATE-K-PROBE",
    "GATE-C-FIXTURE",
)
_SENS_REFUSED = "敏感性前置未满足：拒绝真数据 GATE-Y 探针"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def probe_auth_phrase() -> str:
    """跑前写死的探针人令原文（逐字）。"""
    return _PROBE_AUTH_PHRASE


def probe_auth_ok(phrase: str | None) -> bool:
    """人令须与写死原文逐字相等。"""
    return phrase == _PROBE_AUTH_PHRASE


def probe_claim_ids(rows: Sequence[Mapping[str, Any]] | None = None) -> list[str]:
    """探针名单针：pe_v2 正式 n=30 的 claim_id 顺序（与正式同构造配额）。"""
    sample = list(rows) if rows is not None else load_pe_v2_formal_n30()
    return [str(row["claim_id"]) for row in sample]


def probe_requests(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """仓外探针发送队列。跳过 B1 rewrite（同 after：以 T 生成一次）。"""
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
    """机制缝针（须齐：R · 写 after · 软对齐 · ADR-0040 仪器）。"""
    return {
        "选取": "R（#437 / PR #458）",
        "同 after": "T/B1 共用 T rewrite after，再分叉（#469 / PR #476）",
        "生成对齐": "T/B1 提示软对齐（非 C 强制抄句）",
        "仪器 ADR-0040": (
            "非空 score；reject=−∞；主核验 mDeBERTa-v3 XNLI；"
            "B1/B2 拒识口径抄死（乙只记账）"
        ),
        "敏感性前置": (
            "GATE-Y-SENSITIVITY 通过 ∧ activation_prerequisite_met=真 ∧ 非 stub/夹具层；"
            "未过不得真数据探针/激活/正式跑"
        ),
        "T 闸": "绑定 ∧ 核验；不过 hard reject",
        "B1 闸": "仅核验；不过 hard reject",
        "禁止": (
            "金标/评委/用户裁决进 score；改 verify_edit 或放宽 reject 凑 k；"
            "加 n 伪抬 k；以 C 抄句当 Y 主路径；把 Cond 改成点>0.05；"
            "夹具/冒烟/敏感性升格 gate_passed"
        ),
    }


def mechanism_pins_complete(pins: Mapping[str, str] | None = None) -> bool:
    """机制针是否齐：R · 同 after · 软对齐 · ADR-0040。"""
    mech = mechanism_pins() if pins is None else dict(pins)
    required = ("选取", "同 after", "生成对齐", "仪器 ADR-0040")
    if any(key not in mech or not str(mech[key]).strip() for key in required):
        return False
    if "R" not in str(mech["选取"]):
        return False
    if "after" not in str(mech["同 after"]).lower() and "after" not in str(mech["同 after"]):
        return False
    if "软对齐" not in str(mech["生成对齐"]):
        return False
    if "ADR-0040" not in str(mech["仪器 ADR-0040"]) and "非空" not in str(
        mech["仪器 ADR-0040"]
    ):
        return False
    return True


def gate_pass_criteria() -> list[str]:
    """跑前写死的过门判据（须同时）。B1/B2 不在此列；不用正式乙点>0.05。"""
    return [
        f"T 自然放行 k ≥ {_K_FLOOR}",
        f"T−C 固定 k 误放差方向为正（点估计 > {_GATE_Y_POINT_FLOOR:g}）",
    ]


def gate_y_point_floor() -> float:
    """过门方向门地板（0）；正式乙 0.05 不得用于本 Cond。"""
    return _GATE_Y_POINT_FLOOR


def gate_y_conditions(
    report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """过门 = k≥10 ∧ T−C 点估计>0（方向门）。T−B1/T−B2 只报告，不进 passed。

    敏感性 / 冒烟 / 夹具布尔**不得**写入 ``passed``。
    """
    if report is None:
        return {
            "k": None,
            "t_c_positive": False,
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
    t_c = by_name.get("T-C")
    t_b1 = by_name.get("T-B1")
    t_b2 = by_name.get("T-B2")
    t_c_point = t_c.get("point") if t_c is not None else None
    t_b1_point = t_b1.get("point") if t_b1 is not None else None
    t_b2_point = t_b2.get("point") if t_b2 is not None else None
    t_c_pos = bool(
        t_c_point is not None and float(t_c_point) > _GATE_Y_POINT_FLOOR
    )
    t_b1_pos = bool(
        t_b1_point is not None and float(t_b1_point) > _GATE_Y_POINT_FLOOR
    )
    t_b2_pos = bool(
        t_b2_point is not None and float(t_b2_point) > _GATE_Y_POINT_FLOOR
    )
    return {
        "k": k,
        "t_c_positive": t_c_pos,
        "t_b1_positive": t_b1_pos,
        "t_b2_positive": t_b2_pos,
        "k_ok": k_ok,
        "passed": bool(t_c_pos and k_ok),
        "comparisons": by_name,
        "point_floor": _GATE_Y_POINT_FLOOR,
    }


def _yes_no_field(text: str, label: str) -> bool | None:
    """从敏感性报告正文解析「**label**：是/否」。"""
    pattern = rf"\*\*{re.escape(label)}[^*]*\*\*[：:]\s*([是否])"
    match = re.search(pattern, text)
    if match is None:
        return None
    return match.group(1) == "是"


def parse_sensitivity_prerequisite_text(text: str) -> dict[str, Any]:
    """解析 ``GATE-Y-SENSITIVITY.md`` 汇总字段（不把敏感性当作 gate_passed）。"""
    layer_match = re.search(r"\*\*层身份\*\*[：:]\s*(.+)", text)
    inference_layer = layer_match.group(1).strip() if layer_match else ""
    sensitivity_passed = _yes_no_field(text, "sensitivity_passed（S1∧S2∧S3∧S4）")
    if sensitivity_passed is None:
        sensitivity_passed = _yes_no_field(text, "sensitivity_passed")
    activation = _yes_no_field(text, "activation_prerequisite_met")
    return evaluate_sensitivity_prerequisite(
        sensitivity_passed=bool(sensitivity_passed),
        activation_prerequisite_met=bool(activation),
        inference_layer=inference_layer,
        source="GATE-Y-SENSITIVITY.md",
    )


def evaluate_sensitivity_prerequisite(
    *,
    sensitivity_passed: bool,
    activation_prerequisite_met: bool,
    inference_layer: str,
    source: str = "payload",
) -> dict[str, Any]:
    """判定是否允许真数据 GATE-Y 探针。

    stub/夹具层报告即使误标 ``activation_prerequisite_met`` 也不得放行。
    本结果的 ``gate_passed`` 恒为 False（敏感性永不单独过门）。
    """
    layer = str(inference_layer or "")
    stub_or_fixture = (
        layer == REPORT_LAYER_STUB
        or "stub" in layer.lower()
        or "夹具" in layer
        or layer == ""
    )
    # 真模型层须显式；缺层身份按拒绝处理
    real_layer = layer == REPORT_LAYER_REAL or (
        "真模型" in layer and "stub" not in layer.lower() and "夹具" not in layer
    )
    allows = bool(
        sensitivity_passed
        and activation_prerequisite_met
        and real_layer
        and not stub_or_fixture
        and mechanism_pins_complete()
    )
    reasons: list[str] = []
    if not sensitivity_passed:
        reasons.append("sensitivity_passed=否")
    if not activation_prerequisite_met:
        reasons.append("activation_prerequisite_met=否")
    if stub_or_fixture or not real_layer:
        reasons.append(f"层身份不可作真数据前置（{layer or '空'}）")
    if not mechanism_pins_complete():
        reasons.append("机制针未齐（R·写 after·软对齐·ADR-0040）")
    return {
        "sensitivity_passed": bool(sensitivity_passed),
        "activation_prerequisite_met": bool(activation_prerequisite_met),
        "inference_layer": layer,
        "stub_or_fixture_layer": bool(stub_or_fixture),
        "real_model_layer": bool(real_layer),
        "mechanism_pins_complete": mechanism_pins_complete(),
        "allows_real_probe": allows,
        "refusal_reasons": reasons,
        "gate_passed": False,
        "source": source,
    }


def load_sensitivity_prerequisite(
    path: Path | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """读取敏感性汇总；缺文件 → 不允许真数据探针。"""
    base = _repo_root() if root is None else Path(root)
    report = (
        default_sensitivity_report_path(base)
        if path is None
        else Path(path)
    )
    if not report.is_absolute():
        report = base / report
    if not report.is_file():
        return evaluate_sensitivity_prerequisite(
            sensitivity_passed=False,
            activation_prerequisite_met=False,
            inference_layer="",
            source=f"missing:{report}",
        )
    text = report.read_text(encoding="utf-8")
    payload = parse_sensitivity_prerequisite_text(text)
    payload["report_path"] = str(report)
    return payload


def assert_real_probe_allowed(
    prereq: Mapping[str, Any] | None = None,
    *,
    root: Path | None = None,
    sensitivity_report: Path | None = None,
) -> dict[str, Any]:
    """真数据探针硬闸：未过则抛 ``RuntimeError``（不得发探针）。"""
    checked = (
        dict(prereq)
        if prereq is not None
        else load_sensitivity_prerequisite(sensitivity_report, root=root)
    )
    if not checked.get("allows_real_probe"):
        reasons = "；".join(checked.get("refusal_reasons") or ("前置未满足",))
        raise RuntimeError(f"{_SENS_REFUSED}（{reasons}）")
    return checked


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
            "T-C": (by_name.get("T-C") or {}).get("point"),
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
    """只读旁路探针生成 → run_arms（同 after）→ compare_primary（R）→ Y 门闩判定。零 LLM。"""
    base = _repo_root() if root is None else Path(root)
    path = (
        base / _PROBE_GENERATIONS_REL
        if generations_file is None
        else Path(generations_file)
    )
    if not path.is_absolute():
        path = base / path
    if not path.is_file() or path.stat().st_size == 0:
        return {
            "status": "no_probe_generations",
            "arms": None,
            "primary": None,
            "gate": gate_y_conditions(None),
            "generations_path": path,
            "generations_sha256": None,
            "generations_n": 0,
        }
    text = path.read_text(encoding="utf-8")
    generations = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not generations:
        return {
            "status": "no_probe_generations",
            "arms": None,
            "primary": None,
            "gate": gate_y_conditions(None),
            "generations_path": path,
            "generations_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "generations_n": 0,
        }
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
    gate = gate_y_conditions(primary)
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


def _forbidden_write_targets(base: Path) -> set[Path]:
    targets = {
        generations_path().resolve(),
        (base / _FORMAL_GENERATIONS_REL).resolve(),
        (base / _FORMAL_B_REL).resolve(),
        (base / _FORMAL_Y_REL).resolve(),
        (base / _FORMAL_C_REL).resolve(),
    }
    return targets


def send_probe_generations(
    *,
    root: Path | None = None,
    generations_file: Path | None = None,
    chat: Callable[..., Any] = live_chat,
    probe_auth: str | None = None,
    sensitivity_prereq: Mapping[str, Any] | None = None,
    sensitivity_report: Path | None = None,
) -> dict[str, Any]:
    """向旁路 jsonl 发送探针生成。调用方须已确认探针人令与敏感性硬前置。"""
    if not probe_auth_ok(probe_auth):
        raise RuntimeError(
            f"拒绝发送：缺少逐字探针人令「{_PROBE_AUTH_PHRASE}」"
        )
    base = _repo_root() if root is None else Path(root)
    assert_real_probe_allowed(
        sensitivity_prereq,
        root=base,
        sensitivity_report=sensitivity_report,
    )
    path = (
        base / _PROBE_GENERATIONS_REL
        if generations_file is None
        else Path(generations_file)
    )
    if not path.is_absolute():
        path = base / path
    if path.resolve() in _forbidden_write_targets(base):
        raise RuntimeError("探针禁止写入 formal / formal-b / formal-y / formal-c jsonl")
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
            f"- **T−C** 固定 k 误放差 = {format_rate(item['T-C'])}（过门条件）",
            f"- **T−B1** 固定 k 误放差 = {format_rate(item['T-B1'])}（只报告 · 不过门）",
            f"- **T−B2** 固定 k 误放差 = {format_rate(item['T-B2'])}（只报告 · 不过门）",
            f"- **gate_passed** = `{item['gate_passed']}`",
            "",
        ]
    )
    return lines


def render_gate_y_probe_markdown(
    *,
    code_pin: str,
    baseline_note: str,
    authorize_send: bool,
    send_result: Mapping[str, Any] | None,
    probe_pack: Mapping[str, Any] | None,
    readonly_pack: Mapping[str, Any] | None,
    layer_note: str = "夹具/合成层",
    sensitivity_prereq: Mapping[str, Any] | None = None,
) -> str:
    """渲染可扔 GATE-Y 探针报告。文首标明可扔·非乙成立·不进主表。"""
    claim_ids = probe_claim_ids()
    pin = decoding_pin()
    mech = mechanism_pins()
    criteria = gate_pass_criteria()
    sens = (
        dict(sensitivity_prereq)
        if sensitivity_prereq is not None
        else load_sensitivity_prerequisite()
    )
    live_ran = bool(authorize_send and send_result and send_result.get("status") == "sent")
    recomputed = bool(probe_pack and probe_pack.get("status") == "recomputed")
    gate = (
        probe_pack["gate"]
        if recomputed
        else gate_y_conditions(None)
    )
    if not recomputed:
        gate = {
            **gate,
            "passed": False,
            "k_ok": False,
            "t_c_positive": False,
            "t_b1_positive": False,
            "t_b2_positive": False,
        }
    # 防火墙：敏感性/夹具永不升格过门
    if not recomputed:
        gate = {**gate, "passed": False}

    lines: list[str] = [
        "# 仓外 GATE-Y 探针报告（可扔）",
        "",
        "> **可扔 · 非乙成立 · 不进主表 · 不得升格为正式 RESULT-Y。**",
        "> 本页是路线 Y（只冲乙 · 仅锁 T−C）的**仓外门闩探针**旁路产物。",
        "> 本会话成功 ≠ 乙成立。最多「可建议人审激活」；**不**自行激活 `PREREG-Y`，**不**开正式主跑。",
        "> `#479` / `GATE-K-PROBE` / `GATE-C-FIXTURE` / 敏感性 / 冒烟 / 夹具绿 **不得**升格为本页已过门。",
        f"> **层身份**：{layer_note}。夹具绿 ≠ 真数据过门。",
        "",
        "## 探针协议（跑前写死 · 禁止 HARKing）",
        "",
        "### 敏感性硬前置（ADR-0041 · #530）",
        "",
        "- 报告：`docs/evidence/patch-events/GATE-Y-SENSITIVITY.md`（可扔；≠ `gate_passed`）。",
        "- 真数据探针须同时：`sensitivity_passed` ∧ `activation_prerequisite_met=真` ∧ 非 stub/夹具层 ∧ 机制针齐。",
        "- **stub 层绿不得当作可激活/可探针前置已满足**。",
        "- 未通过 → **硬拒绝**真数据探针（不得发探针、不得激活、不得正式跑）。",
        f"- 本页读取：`sensitivity_passed`="
        f"{'是' if sens.get('sensitivity_passed') else '否'}；"
        f"`activation_prerequisite_met`="
        f"{'是' if sens.get('activation_prerequisite_met') else '否'}；"
        f"层=`{sens.get('inference_layer') or '（缺）'}`；"
        f"允许真数据探针="
        f"{'是' if sens.get('allows_real_probe') else '否'}。",
        "",
        "### 过门判据（须同时 · 方向门 · 不用正式乙点>0.05）",
        "",
    ]
    for idx, item in enumerate(criteria, start=1):
        lines.append(f"{idx}. {item}")
    lines.extend(
        [
            "",
            "T−B1 / T−B2 差**必报**，**不**作过门条件。",
            "",
            "任一条过门条件不满足 → `gate_passed=false`；建议句必须写："
            "**不得激活 PREREG-Y；不得正式主跑。**",
            "",
            "### 机制约束（不得放松 · ADR-0040 仪器针）",
            "",
        ]
    )
    for key, value in mech.items():
        lines.append(f"- **{key}**：{value}")
    lines.extend(
        [
            "",
            f"- **机制针齐**：{'是' if mechanism_pins_complete(mech) else '否'}",
            "",
            "### 样本针",
            "",
            f"- **n** = {len(claim_ids)}（`load_pe_v2_formal_n30()`，与正式同构造配额）",
            f"- **claim_id 顺序**：`{','.join(claim_ids)}`",
            "- 旁路生成：`" + _PROBE_GENERATIONS_REL.as_posix() + "`（禁止写入 formal / formal-b / formal-y / formal-c）",
            "",
            "### 解码针",
            "",
            f"- model = `{pin['model']}`（登记 `{pin['registry_model']}`）",
            f"- temperature = `{pin['temperature']}`",
            f"- Decoding.seed = `{pin['decoding_seed']}`（run_arms 作废检查）",
            f"- API seed = `{pin['api_seed']}` — {pin['api_seed_note']}",
            "",
            "### 探针人令（真数据发模型）",
            "",
            f"- 逐字：`{_PROBE_AUTH_PHRASE}`",
            "- 无此令时 `--authorize-send` **拒绝**；本令不得当作 PE-Y-05 正式激活令。",
            "- 另须敏感性硬前置已通过；缺前置时即使有人令也**拒绝发探针**。",
            "",
            "## 基线与代码针",
            "",
            f"- **代码针**：{code_pin}",
            f"- **基线**：{baseline_note}",
            "- 机制缝：R + 同 after + 软对齐 + ADR-0040；过门 Cond 仍为 k≥10∧T−C点>0（方向门）",
            "",
            "## 发送状态",
            "",
            f"- **是否发模型**：`{'是' if live_ran else '否'}`",
            "",
        ]
    )
    if live_ran:
        lines.extend(
            [
                "- 已按探针人令向旁路路径发送探针生成。",
                f"- sent={send_result.get('sent')!r}；"
                f"b2_diff_added={send_result.get('b2_diff_added')!r}",
                f"- path=`{send_result.get('path')}`",
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
    elif send_result and send_result.get("status") == "refused_no_probe_auth":
        lines.extend(
            [
                "- `--authorize-send` 已请求，但**缺少逐字探针人令** → 拒绝发送。",
                f"- 需要：`{_PROBE_AUTH_PHRASE}`",
                "",
            ]
        )
    elif send_result and send_result.get("status") == "refused_sensitivity":
        lines.extend(
            [
                f"- **{_SENS_REFUSED}** → 未发探针、未激活、未正式跑。",
                f"- 原因：{'；'.join(send_result.get('refusal_reasons') or ())}",
                "",
            ]
        )
    elif recomputed:
        gens_path = probe_pack.get("generations_path") if probe_pack else None
        gens_n = probe_pack.get("generations_n") if probe_pack else None
        gens_sha = probe_pack.get("generations_sha256") if probe_pack else None
        lines.extend(
            [
                "- 旁路探针生成已存在；本次为复算（零 LLM），未再发送。",
                f"- path=`{gens_path}`；n_lines={gens_n!r}",
                f"- sha256=`{gens_sha}`",
                "",
            ]
        )
    elif authorize_send:
        lines.extend(["- 授权标志已开，但本次未执行发送或无新发送。", ""])
    else:
        lines.extend(
            [
                "- **本会话未获明文探针人令** → 停在可发送边界。",
                f"- 状态：**{_AWAITING}**",
                "- 入口已搭好：见文末「复算 / 发送入口」。",
                "",
            ]
        )

    lines.extend(_md_table_block(probe_pack if recomputed else None, title="探针主表（旁路生成）"))

    if readonly_pack is not None:
        lines.extend(
            [
                "## 只读冻结对照（非探针 · 非过门证据）",
                "",
                "> 回放 `"
                + _FORMAL_GENERATIONS_REL.as_posix()
                + "`：仅作机制后差方向对照。",
                "> **不得**把本对照升格为 GATE-Y 过门；亦不得把 `GATE-K-PROBE` / `GATE-C-FIXTURE` 升格为本页已过门。",
                "",
            ]
        )
        ro_primary = readonly_pack.get("primary")
        # 只读对照用 Y 判据重算，避免把甲三条件过门语义带进 Y 页
        ro_gate = gate_y_conditions(ro_primary)
        ro_table = {
            "arms": readonly_pack["arms"],
            "primary": ro_primary,
            "gate": ro_gate,
            "table": summary_table(
                readonly_pack["arms"], ro_primary, ro_gate
            ),
        }
        lines.extend(_md_table_block(ro_table, title="对照表（冻结 formal-generations）")[2:])

    by_name = gate.get("comparisons") or {}
    t_c_point = None
    t_b1_point = None
    t_b2_point = None
    t_c_item = by_name.get("T-C")
    t_b1_item = by_name.get("T-B1")
    t_b2_item = by_name.get("T-B2")
    if isinstance(t_c_item, Mapping):
        t_c_point = t_c_item.get("point")
    if isinstance(t_b1_item, Mapping):
        t_b1_point = t_b1_item.get("point")
    if isinstance(t_b2_item, Mapping):
        t_b2_point = t_b2_item.get("point")
    lines.extend(
        [
            "## 门闩判定表（探针主路径 · 冲乙）",
            "",
            "| # | 条件 | 观测 | 进 gate_passed？ | 满足？ |",
            "|---|---|---|---|---|",
            f"| 1 | T 自然放行 k ≥ {_K_FLOOR} | k = {gate.get('k')!r} | 是 | "
            f"{'是' if gate.get('k_ok') else '否'} |",
            f"| 2 | T−C 差方向为正 | 点估计 = {format_rate(t_c_point)} | 是 | "
            f"{'是' if gate.get('t_c_positive') else '否'} |",
            f"| — | T−B1 差（只报告） | 点估计 = {format_rate(t_b1_point)} | **否** | "
            f"{'是' if gate.get('t_b1_positive') else '否'} |",
            f"| — | T−B2 差（只报告） | 点估计 = {format_rate(t_b2_point)} | **否** | "
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
                f"> 注意：若本页层身份为夹具/合成，**夹具绿 ≠ 真数据过门**；不得据此激活。",
                "",
                "1. 人审本页数字与代码针 / 名单针 / 解码针；确认层身份为真数据探针。",
                "2. 人写 `PREREG-Y` 激活批注（日期、仓库针、本报告路径）。",
                "3. 人决定是否正式主跑（须另授 PE-Y-05 正式令）。",
                "4. **本 Cloud Agent 不激活、不正式主跑、不填 RESULT-Y 成立格。**",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- **gate_passed=false**。",
                "- **不得激活 PREREG-Y；不得正式主跑。**",
                "- 冲乙本波仍停在门闩前；禁止改乙定义续命。",
                "- 不得把夹具绿或敏感性/冒烟或 `#479` / `GATE-K-PROBE` / `GATE-C-FIXTURE` 升格为已过门。",
                "",
            ]
        )
        if not authorize_send and not recomputed:
            lines.append(f"- 本会话：**{_AWAITING}**（入口见下）。")
            lines.append("")

    lines.extend(
        [
            "## 复算 / 发送入口（零歧义）",
            "",
            "```bash",
            "# 默认：写本报告 + 只读对照 + 不发模型（停在可发送边界）",
            "PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe",
            "",
            "# 只打印判定，不写盘",
            "PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe --no-write",
            "",
            "# 若旁路生成已存在：只复算（零 LLM）",
            "PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe --recompute-only",
            "",
            "# 仅在敏感性硬前置已过 + 人明文探针人令之后（本窗默认不做真探针）：",
            "PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe \\",
            "  --authorize-send \\",
            f"  --probe-auth-phrase '{_PROBE_AUTH_PHRASE}'",
            "```",
            "",
            "## 边界",
            "",
            "- 可扔；非乙成立；不进主表；不得升格 RESULT-Y；未激活 PREREG-Y。",
            "- 不改甲/乙/丙定义；不复活路线 A；不回写 B/C 冻结归档。",
            "- 不金标打分；不放宽 hard reject；不加 n 凑 k；不把 Cond 改成点>0.05。",
            "- 禁止把 `#479` / `GATE-K-PROBE` / `GATE-C-FIXTURE` / 敏感性 / 冒烟当作本页已过门依据。",
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
    probe_auth: str | None = None,
    root: Path | None = None,
    chat: Callable[..., Any] = live_chat,
    layer_note: str = "夹具/合成层",
    sensitivity_report: Path | None = None,
    sensitivity_prereq: Mapping[str, Any] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """落盘可扔报告。默认不发模型。无探针人令或缺敏感性前置时拒绝发送。"""
    base = _repo_root() if root is None else Path(root)
    out = _DEFAULT_REPORT if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    sens = (
        dict(sensitivity_prereq)
        if sensitivity_prereq is not None
        else load_sensitivity_prerequisite(sensitivity_report, root=base)
    )
    send_result: dict[str, Any] | None = None
    if authorize_send:
        if not probe_auth_ok(probe_auth):
            send_result = {
                "status": "refused_no_probe_auth",
                "sent": 0,
                "required_phrase": _PROBE_AUTH_PHRASE,
            }
        elif not sens.get("allows_real_probe"):
            send_result = {
                "status": "refused_sensitivity",
                "sent": 0,
                "refusal_reasons": list(sens.get("refusal_reasons") or ()),
                "sensitivity": sens,
            }
        else:
            send_result = send_probe_generations(
                root=base,
                chat=chat,
                probe_auth=probe_auth,
                sensitivity_prereq=sens,
                sensitivity_report=sensitivity_report,
            )
    probe_pack = run_probe_recompute(root=base)
    readonly_pack = None
    try:
        readonly_pack = run_readonly_retest(root=base)
    except Exception:
        readonly_pack = None
    markdown = render_gate_y_probe_markdown(
        code_pin=code_pin,
        baseline_note=baseline_note,
        authorize_send=authorize_send,
        send_result=send_result,
        probe_pack=probe_pack,
        readonly_pack=readonly_pack,
        layer_note=layer_note,
        sensitivity_prereq=sens,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    gate = (
        probe_pack["gate"]
        if probe_pack.get("status") == "recomputed"
        else gate_y_conditions(None)
    )
    if probe_pack.get("status") != "recomputed":
        gate = {**gate, "passed": False}
    # 敏感性通过 ≠ gate_passed
    if sens.get("sensitivity_passed") and probe_pack.get("status") != "recomputed":
        gate = {**gate, "passed": False}
    refused_auth = bool(
        send_result and send_result.get("status") == "refused_no_probe_auth"
    )
    refused_sens = bool(
        send_result and send_result.get("status") == "refused_sensitivity"
    )
    return out, {
        "probe": probe_pack,
        "readonly": readonly_pack,
        "send": send_result,
        "gate": gate,
        "sensitivity": sens,
        "authorize_send": authorize_send,
        "awaiting": (not authorize_send) and probe_pack.get("status") != "recomputed",
        "refused_no_probe_auth": refused_auth,
        "refused_sensitivity": refused_sens,
    }


def main(argv: list[str] | None = None) -> int:
    """默认不发模型。无探针人令或缺敏感性前置时 ``--authorize-send`` 拒绝。"""
    parser = argparse.ArgumentParser(
        prog="python -m freshlatch.eval.patch_events_gate_y_probe"
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
        help="请求发模型；须探针人令 + 敏感性硬前置",
    )
    parser.add_argument(
        "--probe-auth-phrase",
        default=None,
        help=f"探针人令原文（须逐字等于「{_PROBE_AUTH_PHRASE}」）",
    )
    parser.add_argument(
        "--sensitivity-report",
        type=Path,
        default=None,
        help="GATE-Y-SENSITIVITY.md 路径（默认仓内证据页）",
    )
    parser.add_argument("--out", type=Path, default=_DEFAULT_REPORT, help="报告路径")
    parser.add_argument("--code-pin", default="local", help="代码针")
    parser.add_argument(
        "--baseline",
        default="cursor/528-pe-y-sens-01-gate-y-016f + PE-Y-02/#495 tip + #530",
        help="基线说明",
    )
    parser.add_argument(
        "--layer-note",
        default="夹具/合成层",
        help="层身份批注（夹具/合成 ≠ 真数据过门）",
    )
    args = parser.parse_args(argv)

    if args.authorize_send and args.recompute_only:
        sys.stderr.write("--authorize-send 与 --recompute-only 互斥\n")
        return 2

    if args.authorize_send and not probe_auth_ok(args.probe_auth_phrase):
        sys.stderr.write(
            f"--authorize-send 拒绝：缺少逐字探针人令「{_PROBE_AUTH_PHRASE}」\n"
        )
        return 2

    if args.authorize_send:
        sens = load_sensitivity_prerequisite(args.sensitivity_report)
        if not sens.get("allows_real_probe"):
            reasons = "；".join(sens.get("refusal_reasons") or ("前置未满足",))
            sys.stderr.write(f"--authorize-send 拒绝：{_SENS_REFUSED}（{reasons}）\n")
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
                f"t_c_pos={gate['t_c_positive']} "
                f"t_b1_pos={gate['t_b1_positive']} t_b2_pos={gate['t_b2_positive']}\n"
            )
        return 0

    out, pack = write_probe_report(
        args.out,
        code_pin=args.code_pin,
        baseline_note=args.baseline,
        authorize_send=bool(args.authorize_send) and not args.recompute_only,
        probe_auth=args.probe_auth_phrase,
        layer_note=args.layer_note,
        sensitivity_report=args.sensitivity_report,
    )
    gate = pack["gate"]
    awaiting = pack.get("awaiting")
    sys.stdout.write(
        f"gate_passed={bool(gate.get('passed'))} k={gate.get('k')!r} "
        f"awaiting={_AWAITING if awaiting else False}\n"
    )
    if awaiting:
        sys.stdout.write(f"{_AWAITING}\n")
    if pack.get("refused_no_probe_auth"):
        sys.stdout.write("refused_no_probe_auth\n")
    if pack.get("refused_sensitivity"):
        sys.stdout.write("refused_sensitivity\n")
    sys.stdout.write(f"wrote {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
