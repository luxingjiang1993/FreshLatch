"""解析 profile 冒烟：对代表 slot 调用 resolve_model，打印表。

不发网络请求，不构造 LLM 客户端，不读付费密钥。LM Studio 不必在跑。
未知 profile、未知 slot、空的 LMS 模型名或地址、覆盖/锁定不变量不成立时退出码 1。
"""

from __future__ import annotations

import argparse
import os
import sys

from freshlatch.model_profile import (
    ENV_MODEL_PROFILE,
    LOCAL_LMS_OVERLAY_SLOTS,
    LMS_PLATFORM,
    PROFILE_CLOUD,
    PROFILE_LOCAL_LMS,
    PROFILE_LOCKED_SLOTS,
    ModelProfileError,
    resolve_model,
)
from freshlatch.models import DEFAULT_MODEL, DRAFT_MODEL, MODEL_REGISTRY

# 顺序固定，stdout 才稳定。overlay 与 locked 必须都在这张表里。
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

_COLUMNS = ("profile", "slot", "model", "platform", "base_url", "kind")


def slot_kind(slot: str) -> str:
    """locked 优先于 overlay。其余槽位 local-lms 仍返回 registry 原对象。"""
    if slot in PROFILE_LOCKED_SLOTS:
        return "locked"
    if slot in LOCAL_LMS_OVERLAY_SLOTS:
        return "overlay"
    return "registry"


def _profile_args(explicit: str | None) -> list[str | None]:
    """显式 --profile 不读 FRESHLATCH_MODEL_PROFILE。缺省且未设该 env 时打印两个 profile。"""
    if explicit == "both":
        return [PROFILE_CLOUD, PROFILE_LOCAL_LMS]
    if explicit is not None:
        return [explicit]
    if os.environ.get(ENV_MODEL_PROFILE) is None:
        return [PROFILE_CLOUD, PROFILE_LOCAL_LMS]
    return [None]


def _label(profile: str | None) -> str:
    if profile is not None:
        return profile
    return os.environ.get(ENV_MODEL_PROFILE, "").strip()


def _cell(value: str | None) -> str:
    if not value:
        return "-"
    return value


def _require_slot_coverage() -> None:
    missing = sorted((LOCAL_LMS_OVERLAY_SLOTS | PROFILE_LOCKED_SLOTS) - set(SLOTS))
    if missing:
        raise ModelProfileError("代表 slot 未覆盖: " + ", ".join(missing))


def _require_formal_pins() -> None:
    """C-04 与 x1 调用点读的是 registry 常量，不是 resolve_model 的返回值。"""
    if DEFAULT_MODEL != MODEL_REGISTRY["default_llm"].model:
        raise ModelProfileError(
            "DEFAULT_MODEL 与 registry default_llm 不一致。C-04 正式生成器读这两处。"
        )
    if DRAFT_MODEL != MODEL_REGISTRY["x1_draft"].model:
        raise ModelProfileError("DRAFT_MODEL 与 registry x1_draft 不一致。x1 调用点仍读该常量。")


def _check(profile: str, slot: str, entry) -> None:
    cloud = MODEL_REGISTRY[slot]
    if profile == PROFILE_CLOUD:
        if entry is not cloud:
            raise ModelProfileError(f"cloud 下 {slot} 应返回 registry 原对象")
        return
    if profile != PROFILE_LOCAL_LMS:
        raise ModelProfileError(f"冒烟不接受 profile {profile!r}")
    if slot in PROFILE_LOCKED_SLOTS or slot not in LOCAL_LMS_OVERLAY_SLOTS:
        if entry is not cloud:
            raise ModelProfileError(f"local-lms 下 {slot} 应保持 registry 原对象")
        return
    if entry is cloud or entry.platform != LMS_PLATFORM:
        raise ModelProfileError(f"local-lms 下 {slot} 应覆盖为 LM Studio")


def _format(rows: list[tuple[str, ...]]) -> str:
    widths = [len(name) for name in _COLUMNS]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def line(cells: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells)).rstrip()

    body = [line(_COLUMNS), line(tuple("-" * width for width in widths))]
    body.extend(line(row) for row in rows)
    return "\n".join(body)


def render(explicit: str | None) -> str:
    _require_slot_coverage()
    _require_formal_pins()
    rows: list[tuple[str, str, str, str, str, str]] = []
    labels: list[str] = []
    for profile in _profile_args(explicit):
        label = _label(profile)
        labels.append(label)
        for slot in SLOTS:
            entry = resolve_model(slot, profile=profile)
            _check(label, slot, entry)
            rows.append(
                (
                    label,
                    slot,
                    _cell(entry.model),
                    _cell(entry.platform),
                    _cell(entry.base_url),
                    slot_kind(slot),
                )
            )
    shown = ",".join(labels)
    footer = f"ok slots={len(SLOTS)} profiles={shown} http=none"
    return f"smoke_model_resolve http=none\n{_format(rows)}\n{footer}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="解析代表 slot 的 profile，打印 model / platform / base_url。不发网络请求。",
    )
    parser.add_argument(
        "--profile",
        choices=(PROFILE_CLOUD, PROFILE_LOCAL_LMS, "both"),
        default=None,
        help=(
            "cloud、local-lms 或 both。缺省时，未设置 FRESHLATCH_MODEL_PROFILE 则打印两者，"
            "否则只按该 env 解析。"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        text = render(args.profile)
    except ModelProfileError as exc:
        print(f"smoke_model_resolve failed: {exc}", file=sys.stderr)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
