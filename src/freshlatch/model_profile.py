"""模型 profile 解析。云端登记仍在 MODEL_REGISTRY，本模块只做覆盖。

环境变量：

- ``FRESHLATCH_MODEL_PROFILE``：``cloud``（缺省）或 ``local-lms``。未知值失败关闭。
- ``FRESHLATCH_LMS_MODEL``：local-lms 覆盖用的模型名，缺省 ``qwen3.5-9b``。
- ``FRESHLATCH_LMS_BASE_URL``：local-lms 的 OpenAI 兼容根地址，缺省
  ``http://127.0.0.1:1234/v1``。

local-lms 只覆盖 ``default_llm`` 与 ``x1_draft``。``embed`` 不改到 LM Studio，
继续走云端 embed 与已有的 ``local_embed``。锁定槽位返回 registry 原对象，
覆盖不生效，也不抛异常：列出槽位和正式读登记的代码可以照常调用。
未知 profile、未知槽位、把 LMS 模型或地址设成空字符串，则失败关闭。

LM Studio 不校验密钥。覆盖后的 ``env_key`` 为 ``None``。``LLMClient`` 在
``env_key`` 为空时不读云端密钥，用占位串构造客户端。调用方仍可显式传入 api_key。

C-04 正式生成器没有独立槽位。正式模块继续读 ``MODEL_REGISTRY["default_llm"]``
与 ``DEFAULT_MODEL``，并在调用时显式传入模型名。本模块不改这两处常量，
不改 RESULT，不改 manifest。``nli`` 与三家 ``judge_*`` 在锁定集合里，
local-lms 不能换掉它们。正式跑前拒绝 local-lms 写入在
``freshlatch.formal_run_gate.assert_formal_run_allowed``。本模块不放行那次写入。
"""

from __future__ import annotations

import os
from dataclasses import replace

from freshlatch.models import MODEL_REGISTRY, ModelEntry

PROFILE_CLOUD = "cloud"
PROFILE_LOCAL_LMS = "local-lms"
KNOWN_PROFILES = frozenset({PROFILE_CLOUD, PROFILE_LOCAL_LMS})

ENV_MODEL_PROFILE = "FRESHLATCH_MODEL_PROFILE"
ENV_LMS_MODEL = "FRESHLATCH_LMS_MODEL"
ENV_LMS_BASE_URL = "FRESHLATCH_LMS_BASE_URL"

DEFAULT_LMS_MODEL = "qwen3.5-9b"
DEFAULT_LMS_BASE_URL = "http://127.0.0.1:1234/v1"
LMS_PLATFORM = "lmstudio"

# 日常草稿可切到本机。x1 调用点仍读 registry 常量，这里只让 resolve_model 能解析到同一台 LMS。
LOCAL_LMS_OVERLAY_SLOTS = frozenset({"default_llm", "x1_draft"})

# 正式评委与 C-04 的 nli。生成器锁见模块说明，不在这个集合里另造槽位。
PROFILE_LOCKED_SLOTS = frozenset(
    {
        "judge_qwen",
        "judge_deepseek",
        "judge_kimi",
        "nli",
    }
)


class ModelProfileError(ValueError):
    """profile 解析失败。不回退到云端。"""


class UnknownModelProfileError(ModelProfileError):
    """FRESHLATCH_MODEL_PROFILE 不是 cloud 或 local-lms。"""


class UnknownModelSlotError(ModelProfileError):
    """槽位不在 MODEL_REGISTRY。"""


def _selected_profile(profile: str | None) -> str:
    if profile is None:
        raw = os.environ.get(ENV_MODEL_PROFILE)
        if raw is None:
            return PROFILE_CLOUD
        profile = raw
    name = profile.strip()
    if name not in KNOWN_PROFILES:
        raise UnknownModelProfileError(
            f"未知模型 profile {profile!r}。只允许 {PROFILE_CLOUD} 或 {PROFILE_LOCAL_LMS}。"
        )
    return name


def _env_or_default(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip()
    if not value:
        raise ModelProfileError(f"{name} 为空。local-lms 拒绝空模型名或空地址。")
    return value


def _local_lms_entry(cloud: ModelEntry) -> ModelEntry:
    """复制云端行的温度与输出上限，换成本机模型、地址和平台。"""
    return replace(
        cloud,
        model=_env_or_default(ENV_LMS_MODEL, DEFAULT_LMS_MODEL),
        platform=LMS_PLATFORM,
        base_url=_env_or_default(ENV_LMS_BASE_URL, DEFAULT_LMS_BASE_URL),
        env_key=None,
    )


def resolve_model(slot: str, profile: str | None = None) -> ModelEntry:
    """按 profile 返回槽位条目。profile 缺省时读 FRESHLATCH_MODEL_PROFILE。

    未设置该环境变量时与今天的云端 registry 相同，返回登记表里的原对象。
    local-lms 对非覆盖槽位同样返回原对象。锁定槽位即使将来被放进覆盖表，
    也仍返回原对象。
    """
    chosen = _selected_profile(profile)
    if slot not in MODEL_REGISTRY:
        known = ", ".join(sorted(MODEL_REGISTRY))
        raise UnknownModelSlotError(f"未知模型槽位 {slot!r}。已登记: {known}。")
    cloud = MODEL_REGISTRY[slot]
    if chosen == PROFILE_CLOUD or slot in PROFILE_LOCKED_SLOTS or slot not in LOCAL_LMS_OVERLAY_SLOTS:
        return cloud
    return _local_lms_entry(cloud)
