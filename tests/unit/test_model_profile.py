"""MUM-S2：profile 解析。不发网络请求，不读付费密钥。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from freshlatch.model_profile import (
    DEFAULT_LMS_BASE_URL,
    DEFAULT_LMS_MODEL,
    ENV_LMS_BASE_URL,
    ENV_LMS_MODEL,
    ENV_MODEL_PROFILE,
    LOCAL_LMS_OVERLAY_SLOTS,
    PROFILE_LOCKED_SLOTS,
    ModelProfileError,
    UnknownModelProfileError,
    UnknownModelSlotError,
    resolve_model,
)
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY


def _clear_profile_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_MODEL_PROFILE, raising=False)
    monkeypatch.delenv(ENV_LMS_MODEL, raising=False)
    monkeypatch.delenv(ENV_LMS_BASE_URL, raising=False)
    monkeypatch.delenv("DASHSCOPE_BASE_URL", raising=False)


def test_no_env_matches_cloud_registry(monkeypatch):
    """未设置 profile 时，每个槽位都是 registry 原对象。"""
    _clear_profile_env(monkeypatch)
    assert set(PROFILE_LOCKED_SLOTS) >= {"judge_qwen", "judge_deepseek", "judge_kimi", "nli"}
    assert "default_llm" in LOCAL_LMS_OVERLAY_SLOTS
    assert "embed" not in LOCAL_LMS_OVERLAY_SLOTS
    for slot, entry in MODEL_REGISTRY.items():
        assert resolve_model(slot) is entry
        assert resolve_model(slot, profile="cloud") is entry
    assert DEFAULT_MODEL == MODEL_REGISTRY["default_llm"].model


def test_explicit_cloud_ignores_local_env(monkeypatch):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-lms")
    assert resolve_model("default_llm", profile="cloud") is MODEL_REGISTRY["default_llm"]


def test_local_lms_remaps_default_llm_and_leaves_registry(monkeypatch):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, " local-lms ")
    entry = resolve_model("default_llm")
    cloud = MODEL_REGISTRY["default_llm"]
    assert entry is not cloud
    assert entry.purpose == "default_llm"
    assert entry.model == DEFAULT_LMS_MODEL == "qwen3.5-9b"
    assert entry.base_url == DEFAULT_LMS_BASE_URL == "http://127.0.0.1:1234/v1"
    assert entry.platform == "lmstudio"
    assert entry.env_key is None
    assert entry.temperature == cloud.temperature == 0
    assert cloud.model == "qwen-flash"
    assert cloud.platform == "dashscope"
    assert cloud.env_key == "DASHSCOPE_API_KEY"
    assert DEFAULT_MODEL == "qwen-flash"


def test_local_lms_reads_model_and_base_url_env(monkeypatch):
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_LMS_MODEL, " qwen3.5-9b-local ")
    monkeypatch.setenv(ENV_LMS_BASE_URL, " http://127.0.0.1:1235/v1 ")
    entry = resolve_model("default_llm", profile="local-lms")
    assert entry.model == "qwen3.5-9b-local"
    assert entry.base_url == "http://127.0.0.1:1235/v1"


def test_local_lms_shares_overlay_with_x1_draft_only(monkeypatch):
    """x1_draft 与 default_llm 共用 LMS。x1 调用点不在本票，registry 常量不变。"""
    _clear_profile_env(monkeypatch)
    draft = resolve_model("x1_draft", profile="local-lms")
    cloud = MODEL_REGISTRY["x1_draft"]
    assert draft.model == DEFAULT_LMS_MODEL
    assert draft.base_url == DEFAULT_LMS_BASE_URL
    assert draft.platform == "lmstudio"
    assert draft.env_key is None
    assert draft.max_output_tokens == cloud.max_output_tokens == 32768
    assert cloud.model == "qwen-flash"
    assert resolve_model("x1_flag", profile="local-lms") is MODEL_REGISTRY["x1_flag"]


def test_local_lms_does_not_remap_embed(monkeypatch):
    _clear_profile_env(monkeypatch)
    assert resolve_model("embed", profile="local-lms") is MODEL_REGISTRY["embed"]
    assert resolve_model("local_embed", profile="local-lms") is MODEL_REGISTRY["local_embed"]
    assert resolve_model("neural_rerank", profile="local-lms") is MODEL_REGISTRY["neural_rerank"]
    assert MODEL_REGISTRY["embed"].model == "text-embedding-v4"


def test_locked_slots_stay_on_cloud_registry(monkeypatch):
    """锁定槽位拒绝 local 覆盖：返回云端原对象。C-04 的 nli 含在其中。"""
    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_LMS_MODEL, "")
    for slot in ("judge_qwen", "judge_deepseek", "judge_kimi", "nli"):
        assert slot in PROFILE_LOCKED_SLOTS
        assert resolve_model(slot, profile="local-lms") is MODEL_REGISTRY[slot]
    nli = MODEL_REGISTRY["nli"]
    assert nli.platform == "transformers"
    assert nli.base_url is None
    assert nli.env_key is None


def test_unknown_profile_fails_closed(monkeypatch):
    _clear_profile_env(monkeypatch)
    with pytest.raises(UnknownModelProfileError, match="local-gpu"):
        resolve_model("default_llm", profile="local-gpu")
    monkeypatch.setenv(ENV_MODEL_PROFILE, "LOCAL-LMS")
    with pytest.raises(UnknownModelProfileError, match="LOCAL-LMS"):
        resolve_model("default_llm")
    monkeypatch.setenv(ENV_MODEL_PROFILE, " ")
    with pytest.raises(UnknownModelProfileError):
        resolve_model("default_llm")


def test_unknown_slot_and_empty_lms_env_fail_closed(monkeypatch):
    _clear_profile_env(monkeypatch)
    with pytest.raises(UnknownModelSlotError, match="generator_model"):
        resolve_model("generator_model", profile="cloud")
    monkeypatch.setenv(ENV_LMS_MODEL, "  ")
    with pytest.raises(ModelProfileError, match=ENV_LMS_MODEL):
        resolve_model("default_llm", profile="local-lms")
    monkeypatch.setenv(ENV_LMS_MODEL, "qwen3.5-9b")
    monkeypatch.setenv(ENV_LMS_BASE_URL, "")
    with pytest.raises(ModelProfileError, match=ENV_LMS_BASE_URL):
        resolve_model("default_llm", profile="local-lms")


def test_llm_client_local_lms_uses_resolved_endpoint_and_placeholder_key(monkeypatch):
    from freshlatch import llm as llm_mod

    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-lms")
    monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://override.example/v1")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "cloud-secret-must-not-be-read")
    seen: dict[str, str] = {}

    class _FakeOpenAI:
        def __init__(self, *, api_key: str, base_url: str, http_client=None) -> None:
            seen["api_key"] = api_key
            seen["base_url"] = base_url
            # #679 I-07:LLMClient 默认装配 trust_env=False 的 http_client,桩照单全收
            assert http_client is not None and http_client.trust_env is False

    monkeypatch.setattr(llm_mod, "OpenAI", _FakeOpenAI)
    monkeypatch.setattr(llm_mod, "load_dotenv", lambda *_args, **_kwargs: None)
    client = llm_mod.LLMClient()
    assert client.client is not None
    assert seen["base_url"] == DEFAULT_LMS_BASE_URL
    assert seen["api_key"] == "MISSING_DASHSCOPE_API_KEY"
    assert "cloud-secret-must-not-be-read" not in seen["api_key"]

    explicit = llm_mod.LLMClient(api_key="explicit-key", base_url="http://127.0.0.1:9/v1")
    assert explicit.client is not None
    assert seen["api_key"] == "explicit-key"
    assert seen["base_url"] == "http://127.0.0.1:9/v1"


def test_decoding_default_follows_profile_and_explicit_model_stays(monkeypatch):
    """日常 DecodingParams() 跟 profile。显式 model= 不改，正式生成器与 x1 仍钉调用方传入的名字。"""
    from freshlatch.llm import DecodingParams

    _clear_profile_env(monkeypatch)
    assert DecodingParams().model == DEFAULT_MODEL == "qwen-flash"
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-lms")
    assert DecodingParams().model == DEFAULT_LMS_MODEL
    pinned = DecodingParams(model=DEFAULT_MODEL, temperature=0.0)
    assert pinned.model == DEFAULT_MODEL
    assert pinned.temperature == 0.0


def test_chat_sends_profile_model_only_when_caller_omits_model(monkeypatch):
    from freshlatch.llm import DecodingParams, LLMClient

    _clear_profile_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-lms")
    seen: dict[str, str] = {}

    def create(**kwargs):
        seen["model"] = kwargs["model"]
        return SimpleNamespace(
            usage=None,
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok", tool_calls=None))],
        )

    llm = LLMClient(api_key="test-key", base_url="http://127.0.0.1:9/v1")
    llm.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    llm.chat([{"role": "user", "content": "ping"}])
    assert seen["model"] == DEFAULT_LMS_MODEL
    llm.chat(
        [{"role": "user", "content": "ping"}],
        decoding=DecodingParams(model=DEFAULT_MODEL, temperature=0.0),
    )
    assert seen["model"] == DEFAULT_MODEL
    assert llm.decoding_log[-1].model == DEFAULT_MODEL
