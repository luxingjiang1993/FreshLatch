"""MUM-S6：连通性体检进程内退出码。不发网络，不要求 LM Studio 或云端密钥。"""

from __future__ import annotations

import importlib.util
import io
import sys
import urllib.error
from pathlib import Path

import pytest

from freshlatch.model_profile import (
    ENV_LMS_BASE_URL,
    ENV_LMS_MODEL,
    ENV_MODEL_PROFILE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_MOD_NAME = "smoke_model_connectivity_mum_s6"

_KEY_NAMES = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_FAKE_KEYS = {
    "DASHSCOPE_API_KEY": "sk-test-dashscope",
    "DEEPSEEK_API_KEY": "sk-test-deepseek",
    "MOONSHOT_API_KEY": "sk-test-moonshot",
}


def _load_smoke():
    path = REPO_ROOT / "scripts" / "smoke_model_connectivity.py"
    spec = importlib.util.spec_from_file_location(_SCRIPT_MOD_NAME, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


SMOKE = _load_smoke()


@pytest.fixture(autouse=True)
def _forbid_urlopen(monkeypatch: pytest.MonkeyPatch):
    def boom(*args, **kwargs):
        raise AssertionError("urlopen")

    monkeypatch.setattr(SMOKE.urllib.request, "urlopen", boom)


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_MODEL_PROFILE, raising=False)
    monkeypatch.delenv(ENV_LMS_MODEL, raising=False)
    monkeypatch.delenv(ENV_LMS_BASE_URL, raising=False)
    for name in _KEY_NAMES:
        monkeypatch.delenv(name, raising=False)


def _set_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in _FAKE_KEYS.items():
        monkeypatch.setenv(name, value)


def _ok_get(monkeypatch: pytest.MonkeyPatch, calls: list) -> None:
    def fake(url: str, timeout: float, api_key: str | None) -> SMOKE.ProbeHit:
        calls.append((url, timeout, api_key))
        return SMOKE.ProbeHit(url=url, status=200, error=None)

    monkeypatch.setattr(SMOKE, "http_get", fake)


def _assert_secrets_absent(text: str) -> None:
    for value in _FAKE_KEYS.values():
        assert value not in text
    assert "Bearer" not in text


def test_script_does_not_send_chat():
    text = (REPO_ROOT / "scripts" / "smoke_model_connectivity.py").read_text(encoding="utf-8")
    for banned in ("openai", "chat/completions", "requests", "httpx"):
        assert banned not in text
    assert "method=\"GET\"" in text or "method='GET'" in text


def test_default_missing_env_exits_one_without_http(monkeypatch, capsys):
    _clear_env(monkeypatch)
    calls: list = []
    _ok_get(monkeypatch, calls)
    assert SMOKE.main([]) == 1
    captured = capsys.readouterr()
    assert "smoke_model_connectivity probe=none chat=none" in captured.out
    assert "env_missing=7" in captured.out
    assert "missing" in captured.out
    assert "DASHSCOPE_API_KEY" in captured.err
    assert "DEEPSEEK_API_KEY" in captured.err
    assert "MOONSHOT_API_KEY" in captured.err
    assert "smoke_model_connectivity failed:" in captured.err
    assert calls == []
    assert "probe GET" not in captured.out


def test_default_with_fake_keys_exits_zero(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)
    calls: list = []
    _ok_get(monkeypatch, calls)
    assert SMOKE.main([]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "ok profile=cloud slots=10 env_missing=0 probe=none chat=none" in captured.out
    assert "qwen-flash" in captured.out
    assert "judge_qwen" in captured.out
    assert "n/a" in captured.out
    assert calls == []
    _assert_secrets_absent(captured.out + captured.err)


def test_local_lms_without_probe_does_not_call_http(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)
    calls: list = []
    _ok_get(monkeypatch, calls)
    assert SMOKE.main(["--profile", "local-lms"]) == 0
    out = capsys.readouterr().out
    assert "ok profile=local-lms slots=10 env_missing=0 probe=none chat=none" in out
    assert out.count("lmstudio") == 2
    assert "http://127.0.0.1:1234/v1" in out
    assert calls == []


def test_unknown_env_profile_exits_one(monkeypatch, capsys):
    _clear_env(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-gpu")
    assert SMOKE.main([]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "smoke_model_connectivity failed:" in captured.err
    assert "local-gpu" in captured.err


def test_empty_lms_model_exits_one(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)
    monkeypatch.setenv(ENV_LMS_MODEL, "  ")
    calls: list = []
    _ok_get(monkeypatch, calls)
    assert SMOKE.main(["--profile", "local-lms", "--probe-lms"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert ENV_LMS_MODEL in captured.err
    assert calls == []


def test_unknown_flag_exits_two():
    with pytest.raises(SystemExit) as exc:
        SMOKE.main(["--probe-chat"])
    assert exc.value.code == 2


def test_nonpositive_timeout_exits_one(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)
    calls: list = []
    _ok_get(monkeypatch, calls)
    assert SMOKE.main(["--timeout", "0"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "--timeout" in captured.err
    assert calls == []


def test_probe_http_cloud_gets_models_and_hides_keys(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)
    calls: list = []
    _ok_get(monkeypatch, calls)
    assert SMOKE.main(["--probe-http", "--timeout", "2"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "ok profile=cloud slots=10 env_missing=0 probe=http chat=none" in captured.out
    assert "probe GET https://dashscope.aliyuncs.com/compatible-mode/v1/models status=200" in captured.out
    assert "probe GET https://api.deepseek.com/models status=200" in captured.out
    assert "probe GET https://api.moonshot.cn/v1/models status=200" in captured.out
    urls = [item[0] for item in calls]
    assert urls == [
        "https://dashscope.aliyuncs.com/compatible-mode/v1/models",
        "https://api.deepseek.com/models",
        "https://api.moonshot.cn/v1/models",
    ]
    assert all(item[1] == 2 for item in calls)
    assert calls[0][2] == _FAKE_KEYS["DASHSCOPE_API_KEY"]
    assert calls[1][2] == _FAKE_KEYS["DEEPSEEK_API_KEY"]
    assert calls[2][2] == _FAKE_KEYS["MOONSHOT_API_KEY"]
    assert all("127.0.0.1" not in url for url in urls)
    assert all("/chat" not in url for url in urls)
    _assert_secrets_absent(captured.out + captured.err)


def test_probe_http_missing_keys_does_not_send(monkeypatch, capsys):
    _clear_env(monkeypatch)
    calls: list = []
    _ok_get(monkeypatch, calls)
    assert SMOKE.main(["--probe-http"]) == 1
    assert calls == []
    assert "probe GET" not in capsys.readouterr().out


def test_probe_http_non_2xx_exits_two(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)

    def fake(url: str, timeout: float, api_key: str | None) -> SMOKE.ProbeHit:
        return SMOKE.ProbeHit(url=url, status=503, error="HTTP 503")

    monkeypatch.setattr(SMOKE, "http_get", fake)
    assert SMOKE.main(["--probe-http"]) == 2
    captured = capsys.readouterr()
    assert "error=HTTP 503" in captured.out
    assert "unreachable GET" in captured.err
    assert "HTTP 503" in captured.err
    _assert_secrets_absent(captured.out + captured.err)


def test_probe_lms_on_cloud_hits_only_lms(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)
    calls: list = []
    _ok_get(monkeypatch, calls)
    assert SMOKE.main(["--profile", "cloud", "--probe-lms"]) == 0
    captured = capsys.readouterr()
    assert "probe=lms chat=none" in captured.out
    assert calls == [("http://127.0.0.1:1234/v1/models", 5.0, None)]
    assert "dashscope" not in captured.out.split("probe GET", 1)[-1]
    _assert_secrets_absent(captured.out + captured.err)


def test_probe_lms_timeout_exits_two(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)

    def fake(url: str, timeout: float, api_key: str | None) -> SMOKE.ProbeHit:
        return SMOKE.ProbeHit(url=url, status=0, error="timeout")

    monkeypatch.setattr(SMOKE, "http_get", fake)
    assert SMOKE.main(["--probe-lms", "--timeout", "1"]) == 2
    err = capsys.readouterr().err
    assert "unreachable GET http://127.0.0.1:1234/v1/models timeout" in err


def test_probe_http_and_lms_dedup_on_local_profile(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)
    monkeypatch.setenv(ENV_LMS_BASE_URL, "http://127.0.0.1:1234/v1")
    calls: list = []
    _ok_get(monkeypatch, calls)
    assert SMOKE.main(["--profile", "local-lms", "--probe-http", "--probe-lms"]) == 0
    urls = [item[0] for item in calls]
    assert urls == [
        "http://127.0.0.1:1234/v1/models",
        "https://dashscope.aliyuncs.com/compatible-mode/v1/models",
        "https://api.deepseek.com/models",
        "https://api.moonshot.cn/v1/models",
    ]
    assert calls[0][2] is None
    assert "probe=http,lms chat=none" in capsys.readouterr().out


def test_explicit_profile_ignores_unknown_env(monkeypatch, capsys):
    _clear_env(monkeypatch)
    _set_keys(monkeypatch)
    monkeypatch.setenv(ENV_MODEL_PROFILE, "local-gpu")
    assert SMOKE.main(["--profile", "cloud"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "profile=cloud" in captured.out


def test_http_get_is_get_and_discards_body(monkeypatch):
    seen = {}

    class _Response:
        status = 200

        def read(self, limit: int) -> bytes:
            seen["limit"] = limit
            return b'{"data":[]}'

        def __enter__(self):
            return self

        def __exit__(self, *args) -> bool:
            return False

    def fake_urlopen(request, timeout):
        seen["method"] = request.get_method()
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["authorization"] = request.get_header("Authorization")
        seen["data"] = request.data
        return _Response()

    monkeypatch.setattr(SMOKE.urllib.request, "urlopen", fake_urlopen)
    hit = SMOKE.http_get("http://127.0.0.1:9/v1/models", 1.5, "sk-test-dashscope")
    assert hit.status == 200
    assert hit.error is None
    assert seen["method"] == "GET"
    assert seen["url"] == "http://127.0.0.1:9/v1/models"
    assert seen["timeout"] == 1.5
    assert seen["authorization"] == "Bearer sk-test-dashscope"
    assert seen["data"] is None
    assert seen["limit"] == SMOKE._READ_LIMIT


def test_http_get_timeout_and_http_error(monkeypatch):
    def raise_timeout(request, timeout):
        raise urllib.error.URLError(TimeoutError("timed out"))

    monkeypatch.setattr(SMOKE.urllib.request, "urlopen", raise_timeout)
    hit = SMOKE.http_get("http://127.0.0.1:9/v1/models", 1, None)
    assert hit.error == "timeout"
    assert hit.status == 0

    def raise_http(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            401,
            "denied",
            hdrs=None,
            fp=io.BytesIO(b"secret-body"),
        )

    monkeypatch.setattr(SMOKE.urllib.request, "urlopen", raise_http)
    denied = SMOKE.http_get("http://127.0.0.1:9/v1/models", 1, "sk-test-dashscope")
    assert denied.status == 401
    assert denied.error == "HTTP 401"
    assert "secret-body" not in (denied.error or "")


def test_docs_point_at_s7_and_ci_skips_probe():
    connectivity = (REPO_ROOT / "docs" / "ops" / "model-connectivity.md").read_text(encoding="utf-8")
    assert "S7" in connectivity
    assert "--probe-http" in connectivity
    assert "--probe-lms" in connectivity
    assert "chat completions" in connectivity
    assert "CI" in connectivity
    assert "不" in connectivity and "探针" in connectivity
    status = (REPO_ROOT / "docs" / "_archive" / "2026-10" / "plans" / "model-unified-mgmt" / "00-status.md").read_text(
        encoding="utf-8"
    )
    assert "scripts/smoke_model_connectivity.py" in status
    assert "S7" in status
    profiles = (REPO_ROOT / "docs" / "ops" / "model-profiles.md").read_text(encoding="utf-8")
    assert "model-connectivity.md" in profiles
    assert "S7" in profiles
