"""正式跑前闸。写入 C-04 RESULT / 注册分之前必须通过。

未设置 ``FRESHLATCH_MODEL_PROFILE`` 或值为 ``cloud`` 时放行。
``local-lms`` 失败关闭。未知 profile 失败关闭，沿用 ``resolve_model`` 的错误。

``FRESHLATCH_ALLOW_NON_RESULT_DEBUG=1`` 只表示非 RESULT 调试。
``assert_formal_run_allowed`` 不因该变量放行。正式 RESULT 写入仍然拒绝。

锁定槽位 ``judge_*`` 与 ``nli`` 必须仍是 ``MODEL_REGISTRY`` 原对象。
检查复用 ``resolve_model``：``local-lms`` 下锁定槽位返回原对象才算未被覆盖。
"""

from __future__ import annotations

import os

from freshlatch.model_profile import (
    PROFILE_CLOUD,
    PROFILE_LOCAL_LMS,
    PROFILE_LOCKED_SLOTS,
    ModelProfileError,
    _selected_profile,
    resolve_model,
)
from freshlatch.models import MODEL_REGISTRY

ENV_ALLOW_NON_RESULT_DEBUG = "FRESHLATCH_ALLOW_NON_RESULT_DEBUG"


class FormalRunGateError(ModelProfileError):
    """正式跑前闸拒绝。不写 RESULT，不回退到另一 profile。"""


def _non_result_debug_flag() -> bool:
    """只有精确的 ``1`` 算解锁。其它值不算。"""
    return os.environ.get(ENV_ALLOW_NON_RESULT_DEBUG, "").strip() == "1"


def non_result_debug_allowed(profile: str | None = None) -> bool:
    """``local-lms`` 且显式解锁时为真。真也不表示可以写正式 RESULT。"""
    chosen = _selected_profile(profile)
    if chosen != PROFILE_LOCAL_LMS:
        return False
    return _non_result_debug_flag()


def _assert_locked_slots_uncovered(profile: str) -> None:
    for slot in sorted(PROFILE_LOCKED_SLOTS):
        resolved = resolve_model(slot, profile=profile)
        if resolved is not MODEL_REGISTRY[slot]:
            raise FormalRunGateError(
                f"正式跑拒绝：锁定槽位 {slot} 在 profile {profile!r} 下不是 MODEL_REGISTRY 原对象。"
            )


def assert_formal_run_allowed(profile: str | None = None) -> None:
    """未设置或 ``cloud`` 通过。``local-lms`` 与未知 profile 失败关闭。

    ``profile`` 缺省时读 ``FRESHLATCH_MODEL_PROFILE``，与 ``resolve_model`` 相同。
    显式传入时以参数为准。调试解锁变量不参与放行。
    """
    chosen = _selected_profile(profile)
    _assert_locked_slots_uncovered(chosen)
    if chosen != PROFILE_LOCAL_LMS:
        _assert_locked_slots_uncovered(PROFILE_LOCAL_LMS)
    if chosen == PROFILE_CLOUD:
        return
    raise FormalRunGateError(
        f"正式跑拒绝：profile 是 {chosen!r}。"
        f"写入 C-04 RESULT / 注册分只允许未设置或 {PROFILE_CLOUD!r}。"
        f"{ENV_ALLOW_NON_RESULT_DEBUG}=1 只用于非 RESULT 调试，不得打开正式 RESULT 写入。"
    )
