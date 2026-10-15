"""MUM-S5 模型适配草稿。只读 MODEL_REGISTRY 与 resolve_model，打印槽位结论。

不发网络请求，不读付费密钥，不构造聊天客户端。不提供实网开关。
LM Studio 不必在跑，云端不必可达。CI 走进程内路径即可。

结论词与 docs/ops/model-fit-report.md、docs/evidence/model-fit/2026-10-15.md
里的 fit-verdict 行一致。本脚本不改 registry，不写 RESULT。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from freshlatch.model_profile import (
    DEFAULT_LMS_BASE_URL,
    DEFAULT_LMS_MODEL,
    LOCAL_LMS_OVERLAY_SLOTS,
    PROFILE_CLOUD,
    PROFILE_LOCAL_LMS,
    PROFILE_LOCKED_SLOTS,
    ModelProfileError,
    resolve_model,
)
from freshlatch.models import DEFAULT_MODEL, DRAFT_MODEL, MODEL_REGISTRY

# 与 scripts/smoke_model_resolve.py 同一顺序，stdout 才稳定。
SLOTS = (
    "default_llm",
    "x1_draft",
    "x1_flag",
    "embed",
    "local_embed",
    "neural_rerank",
    "nli",
    "judge_qwen",
    "judge_deepseek",
    "judge_kimi",
)

# 桌面结论。prefer_local 只描述日常草稿建议，不改 registry 模型 id。
VERDICTS: dict[str, str] = {
    "default_llm": "prefer_local",
    "x1_draft": "keep",
    "x1_flag": "keep",
    "embed": "keep",
    "local_embed": "keep",
    "neural_rerank": "keep",
    "nli": "keep",
    "judge_qwen": "must_cloud",
    "judge_deepseek": "must_cloud",
    "judge_kimi": "must_cloud",
}

# C-04 正式生成器不是 registry 槽位。它读 DEFAULT_MODEL。
C04_READ_POINT = "c04_generator"
C04_VERDICT = "must_cloud"

VERDICT_ALLOWED = frozenset({"keep", "prefer_local", "must_cloud"})

DESK_DATE = "2026-10-15"
DESK_MACHINE = "RTX 5070 Ti 12GB + 32GB RAM"
DESK_DRAFT_N_CTX = "65536"
DESK_27B_MODEL = "qwen3.8-27b"
DESK_27B_N_CTX = "8-12k"

_NOTES: dict[str, str] = {
    "default_llm": "日常 LLMClient 走 resolve_model；registry 模型 id 仍是云端默认，换默认另票",
    "x1_draft": "resolve 可覆盖，x1 调用点仍读 DRAFT_MODEL，本轮不改 x1",
    "x1_flag": "不在 overlay；维持 registry 模型，不改到 LMS",
    "embed": "维持云端 embed；不把本槽指到 LM Studio",
    "local_embed": "维持 fastembed 本地权重，不改生产",
    "neural_rerank": "维持 bge-reranker-base，不改生产精排",
    "nli": "维持 transformers 本地，不进 LM Studio；locked",
    "judge_qwen": "三云端评委之一；locked；不推荐本地替代",
    "judge_deepseek": "三云端评委之一；locked；不推荐本地替代",
    "judge_kimi": "三云端评委之一；locked；不推荐本地替代",
}

_REPO_ROOT = Path(__file__).resolve().parents[1]
_VERDICT_DOCS = (
    _REPO_ROOT / "docs" / "ops" / "model-fit-report.md",
    _REPO_ROOT / "docs" / "evidence" / "model-fit" / "2026-10-15.md",
)

_RESOLVE_COLUMNS = (
    "profile",
    "slot",
    "registry_model",
    "resolved_model",
    "platform",
    "kind",
    "base_url",
)
_VERDICT_COLUMNS = ("read_point", "verdict", "note")


class FitReviewError(RuntimeError):
    """草稿表与 registry 或报告不一致。不回退到别的结论。"""


def slot_kind(slot: str) -> str:
    """locked 优先于 overlay。其余槽位 local-lms 仍返回 registry 原对象。"""
    if slot in PROFILE_LOCKED_SLOTS:
        return "locked"
    if slot in LOCAL_LMS_OVERLAY_SLOTS:
        return "overlay"
    return "registry"


def _cell(value: str | None) -> str:
    if not value:
        return "-"
    return value


def _format(columns: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    widths = [len(name) for name in columns]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def line(cells: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells)).rstrip()

    body = [line(columns), line(tuple("-" * width for width in widths))]
    body.extend(line(row) for row in rows)
    return "\n".join(body)


def _require_verdict_table() -> None:
    if set(VERDICTS) != set(MODEL_REGISTRY):
        missing = sorted(set(MODEL_REGISTRY) - set(VERDICTS))
        extra = sorted(set(VERDICTS) - set(MODEL_REGISTRY))
        raise FitReviewError(f"结论表与 registry 槽位不一致。缺 {missing}，多 {extra}。")
    bad = sorted(slot for slot, verdict in VERDICTS.items() if verdict not in VERDICT_ALLOWED)
    if bad:
        raise FitReviewError("结论词非法: " + ", ".join(bad))
    if C04_VERDICT not in VERDICT_ALLOWED:
        raise FitReviewError(f"C-04 结论词非法: {C04_VERDICT}")
    if C04_READ_POINT in MODEL_REGISTRY:
        raise FitReviewError("c04_generator 不应是 registry 槽位。正式生成器读 DEFAULT_MODEL。")
    if DEFAULT_MODEL != MODEL_REGISTRY["default_llm"].model:
        raise FitReviewError("DEFAULT_MODEL 与 registry default_llm 不一致。")
    if DRAFT_MODEL != MODEL_REGISTRY["x1_draft"].model:
        raise FitReviewError("DRAFT_MODEL 与 registry x1_draft 不一致。")
    missing_slots = sorted((LOCAL_LMS_OVERLAY_SLOTS | PROFILE_LOCKED_SLOTS) - set(SLOTS))
    if missing_slots:
        raise FitReviewError("打印表未覆盖: " + ", ".join(missing_slots))
    if tuple(VERDICTS) != SLOTS:
        raise FitReviewError("结论表顺序与 SLOTS 不一致。")


def _verdict_needles() -> list[str]:
    needles = [f"fit-verdict {slot} {VERDICTS[slot]}" for slot in SLOTS]
    needles.append(f"fit-verdict {C04_READ_POINT} {C04_VERDICT}")
    return needles


def _require_docs() -> None:
    needles = _verdict_needles()
    for path in _VERDICT_DOCS:
        if not path.is_file():
            raise FitReviewError(f"缺少报告 {path}")
        text = path.read_text(encoding="utf-8")
        absent = [needle for needle in needles if needle not in text]
        if absent:
            raise FitReviewError(f"{path.name} 缺少结论行: " + "; ".join(absent))


def _resolution_rows() -> tuple[list[tuple[str, ...]], list[str]]:
    """两个 profile 都显式传入，不读 FRESHLATCH_MODEL_PROFILE。"""
    rows: list[tuple[str, ...]] = []
    warnings: list[str] = []
    for profile in (PROFILE_CLOUD, PROFILE_LOCAL_LMS):
        for slot in SLOTS:
            entry = resolve_model(slot, profile=profile)
            rows.append(
                (
                    profile,
                    slot,
                    _cell(MODEL_REGISTRY[slot].model),
                    _cell(entry.model),
                    _cell(entry.platform),
                    slot_kind(slot),
                    _cell(entry.base_url),
                )
            )
            if profile == PROFILE_LOCAL_LMS and slot in LOCAL_LMS_OVERLAY_SLOTS:
                if entry.model != DEFAULT_LMS_MODEL:
                    warnings.append(
                        f"warn: {slot} local-lms resolved model is {entry.model}, "
                        f"desk prefer remains {DEFAULT_LMS_MODEL}"
                    )
    return rows, warnings


def _verdict_rows() -> list[tuple[str, ...]]:
    rows = [(slot, VERDICTS[slot], _NOTES[slot]) for slot in SLOTS]
    rows.append(
        (
            C04_READ_POINT,
            C04_VERDICT,
            f"读 DEFAULT_MODEL={DEFAULT_MODEL}；正式 profile 禁止 local-lms；不写 RESULT",
        )
    )
    return rows


def _counts() -> str:
    keep = sum(1 for verdict in VERDICTS.values() if verdict == "keep")
    prefer = sum(1 for verdict in VERDICTS.values() if verdict == "prefer_local")
    cloud = sum(1 for verdict in VERDICTS.values() if verdict == "must_cloud")
    return f"keep:{keep},prefer_local:{prefer},must_cloud:{cloud}"


def render() -> str:
    _require_verdict_table()
    _require_docs()
    rows, warnings = _resolution_rows()
    parts = [
        "model_fit_review http=none paid=none",
        "layer: desk",
        f"date: {DESK_DATE}",
        f"machine: {DESK_MACHINE}",
        f"draft_prefer: {DEFAULT_LMS_MODEL} n_ctx~{DESK_DRAFT_N_CTX} base: {DEFAULT_LMS_BASE_URL}",
        f"compare_27b: {DESK_27B_MODEL} mixed-offload n_ctx~{DESK_27B_N_CTX} prefer_9b_for_drafts=yes",
        "registry_defaults: unchanged",
        _format(_RESOLVE_COLUMNS, rows),
        _format(_VERDICT_COLUMNS, _verdict_rows()),
    ]
    parts.extend(warnings)
    footer = (
        f"ok slots={len(SLOTS)} verdicts={_counts()} "
        f"c04={C04_VERDICT} http=none paid=none lms_required=no"
    )
    parts.append(footer)
    return "\n".join(parts)


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "只读打印槽位解析与 keep/prefer_local/must_cloud 草稿。不发网络请求。"
        ),
    )


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    try:
        text = render()
    except (ModelProfileError, FitReviewError) as exc:
        print(f"model_fit_review failed: {exc}", file=sys.stderr)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
