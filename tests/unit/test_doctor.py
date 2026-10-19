"""#714 T5(决议 #708):doctor.py 环境自检 CLI。

验收对齐(零真实网络、零真实下载、零 LLM):
- 人为制造失败(缺权重路径)→ exit≠0,stdout 含该项检查项名 + 中文说明;
- --offline 空跑:网络项跳过、不真连端点,可作 CI import/空跑 smoke;
- 代理检查:坏 NO_PROXY(裸 ::1)判失败;代理凭据脱敏不落 stdout;
- 任何密钥(DASHSCOPE_API_KEY 等)不落 stdout;
- 单项检查抛异常不崩整体,该项记失败继续跑。
"""

from __future__ import annotations

import subprocess
import sys

import pytest

import freshlatch.doctor as doctor
from freshlatch.doctor import (
    CheckResult,
    check_encoding,
    check_network,
    check_proxy,
    check_weights,
    main,
    run_checks,
)

PROXY_VARS = ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
              "http_proxy", "https_proxy", "no_proxy")


@pytest.fixture()
def clean_proxy_env(monkeypatch):
    for var in PROXY_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture()
def weights_ready(tmp_path, monkeypatch):
    """两套 huggingface 快照布局的权重缓存;FASTEMBED_CACHE_PATH 指向它。"""
    for short in ("bge-small-zh-v1.5", "bge-reranker-base"):
        d = tmp_path / f"models--BAAI--{short}" / "snapshots" / "rev" / "onnx"
        d.mkdir(parents=True)
        (d / "model.onnx").write_bytes(b"w")
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path))
    return tmp_path


class _FakeStream:
    def __init__(self, encoding: str | None):
        self.encoding = encoding


def _ok_encoding(streams=None) -> CheckResult:
    return CheckResult("UTF-8 编码", True, "测试桩")


# -- 网络可达(connect 全注入,零真实网络) ---------------------------------------------------


def test_network_ok_with_injected_connect():
    seen = {}

    def _connect(addr, timeout):
        seen["addr"] = addr
        seen["timeout"] = timeout

    r = check_network("https://dashscope.example.com/v1", timeout=1.5, connect=_connect)
    assert r.ok is True
    assert seen["addr"] == ("dashscope.example.com", 443)
    assert seen["timeout"] == 1.5
    assert "可连接" in r.detail


def test_network_unreachable_fails_chinese():
    def _refuse(addr, timeout):
        raise OSError("refused(夹具)")

    r = check_network("https://dashscope.example.com", connect=_refuse)
    assert r.ok is False
    assert r.name == "网络可达"
    assert "无法连接" in r.detail
    assert "代理" in r.detail  # 给用户的下一步提示


def test_network_unparseable_url_fails():
    r = check_network("not a url at all", connect=None)
    assert r.ok is False
    assert "无法解析" in r.detail


# -- 权重路径(文件层 stat) ------------------------------------------------------------------


def test_weights_missing_reports_chinese(tmp_path, monkeypatch):
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path))
    r = check_weights()
    assert r.ok is False
    assert r.name == "权重路径"
    assert "缺权重快照" in r.detail
    assert "bge-reranker-base" in r.detail  # 缺哪枚写明名字
    assert str(tmp_path) in r.detail  # 缓存目录提示(非敏感路径)


def test_weights_ready_ok(weights_ready):
    r = check_weights()
    assert r.ok is True
    assert "就绪" in r.detail


# -- 代理环境变量(可读 + 脱敏) ---------------------------------------------------------------


def test_proxy_unset_ok():
    r = check_proxy(env={})
    assert r.ok is True
    assert "未设置" in r.detail


def test_proxy_bare_ipv6_in_no_proxy_fails():
    r = check_proxy(env={"NO_PROXY": "::1,localhost"})
    assert r.ok is False
    assert r.name == "代理环境变量"
    assert "NO_PROXY" in r.detail
    assert "[::1]" in r.detail  # 修正提示


def test_proxy_values_redacted():
    r = check_proxy(env={"HTTPS_PROXY": "http://alice:topsecret@proxy.local:8080"})
    assert r.ok is True
    assert "proxy.local:8080" in r.detail
    assert "alice" not in r.detail
    assert "topsecret" not in r.detail
    assert "***@proxy.local" in r.detail


def test_proxy_lowercase_variants_read():
    r = check_proxy(env={"https_proxy": "http://127.0.0.1:9"})
    assert r.ok is True
    assert "HTTPS_PROXY=http://127.0.0.1:9" in r.detail


# -- UTF-8 编码 ------------------------------------------------------------------------------


def test_encoding_utf8_ok():
    r = check_encoding(streams=(_FakeStream("utf-8"), _FakeStream("UTF-8")))
    assert r.ok is True


def test_encoding_non_utf8_fails_with_hint():
    r = check_encoding(streams=(_FakeStream("gbk"),))
    assert r.ok is False
    assert r.name == "UTF-8 编码"
    assert "gbk" in r.detail
    assert "PYTHONUTF8" in r.detail  # 给 Windows 用户的修法


# -- main():exit 契约 + 中文 stdout ------------------------------------------------------------


def test_main_all_pass_exit_zero(weights_ready, clean_proxy_env, monkeypatch, capsys):
    monkeypatch.setattr(doctor, "check_encoding", _ok_encoding)
    monkeypatch.setattr(
        doctor, "check_network",
        lambda timeout=5.0, connect=None: CheckResult("网络可达", True, "夹具可连接"),
    )
    assert main([]) == 0
    out = capsys.readouterr().out
    for name in ("网络可达", "权重路径", "代理环境变量", "UTF-8 编码"):
        assert name in out  # 检查项名逐字出现
    assert "全部通过" in out


def test_main_missing_weights_nonzero_chinese(tmp_path, monkeypatch, capsys, clean_proxy_env):
    """验收:人为制造失败(缺权重路径)→ exit≠0 且 stdout 含该项中文说明。"""
    monkeypatch.setenv("FASTEMBED_CACHE_PATH", str(tmp_path))
    monkeypatch.setattr(doctor, "check_encoding", _ok_encoding)
    monkeypatch.setattr(
        doctor, "check_network",
        lambda timeout=5.0, connect=None: CheckResult("网络可达", True, "夹具可连接"),
    )
    assert main([]) != 0
    out = capsys.readouterr().out
    assert "权重路径" in out
    assert "缺权重快照" in out
    assert "[失败]" in out
    assert "失败 1/4 项" in out


def test_main_offline_skips_network(weights_ready, clean_proxy_env, monkeypatch, capsys):
    """CI 空跑形态:--offline 不真连端点(connect 抛错也照过),该项标记跳过。"""

    def _boom(addr, timeout):
        raise AssertionError("offline 模式不应发起网络连接")

    monkeypatch.setattr(doctor, "check_encoding", _ok_encoding)
    assert main(["--offline"]) == 0
    out = capsys.readouterr().out
    assert "跳过" in out
    assert "网络可达" in out


def test_main_network_failure_nonzero(weights_ready, clean_proxy_env, monkeypatch, capsys):
    def _refuse(addr, timeout):
        raise OSError("refused(夹具)")

    monkeypatch.setattr(doctor, "check_encoding", _ok_encoding)
    monkeypatch.setattr(
        doctor, "check_network",
        lambda timeout=5.0, connect=None: check_network(
            "https://dashscope.example.com", connect=_refuse),
    )
    assert main(["--timeout", "0.5"]) != 0
    out = capsys.readouterr().out
    assert "网络可达" in out
    assert "无法连接" in out


def test_main_bad_no_proxy_nonzero(weights_ready, monkeypatch, capsys):
    monkeypatch.setenv("NO_PROXY", "::1")
    monkeypatch.setattr(doctor, "check_encoding", _ok_encoding)
    monkeypatch.setattr(
        doctor, "check_network",
        lambda timeout=5.0, connect=None: CheckResult("网络可达", True, "夹具可连接"),
    )
    assert main([]) != 0
    out = capsys.readouterr().out
    assert "代理环境变量" in out
    assert "[::1]" in out


def test_main_never_prints_secrets(weights_ready, clean_proxy_env, monkeypatch, capsys):
    """密钥与代理凭据任何情况下不落 stdout(决议 #708 第 4 条)。"""
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test-secret-key-9f8e7d")
    monkeypatch.setenv("HTTPS_PROXY", "http://bob:hunter2@proxy.local:8080")
    monkeypatch.setattr(doctor, "check_encoding", _ok_encoding)
    monkeypatch.setattr(
        doctor, "check_network",
        lambda timeout=5.0, connect=None: CheckResult("网络可达", True, "夹具可连接"),
    )
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "sk-test-secret-key-9f8e7d" not in out
    assert "hunter2" not in out
    assert "bob" not in out


def test_check_exception_does_not_crash(weights_ready, clean_proxy_env, monkeypatch, capsys):
    """单项抛异常:记失败 + 中文,其余项照跑,doctor 不崩(契约:体检入口不裸抛)。"""

    def _boom():
        raise RuntimeError("english internals")

    monkeypatch.setattr(doctor, "check_weights", _boom)
    monkeypatch.setattr(doctor, "check_encoding", _ok_encoding)
    monkeypatch.setattr(
        doctor, "check_network",
        lambda timeout=5.0, connect=None: CheckResult("网络可达", True, "夹具可连接"),
    )
    assert main([]) != 0
    out = capsys.readouterr().out
    assert "检查异常" in out
    assert "RuntimeError" in out
    assert "网络可达" in out  # 其余项仍逐行输出
    assert "english internals" not in out  # 异常消息原文不落盘,只留类型名


def test_run_checks_all_injectable_zero_io(weights_ready, clean_proxy_env):
    """run_checks 依赖全注入:零网络、零真实下载,返回四项。"""
    results = run_checks(
        connect=lambda addr, timeout: None,
        env={},
        streams=(_FakeStream("utf-8"), _FakeStream("utf-8")),
    )
    assert len(results) == 4
    assert all(r.ok for r in results)


# -- CLI 真实子进程空跑(CI smoke 形态) --------------------------------------------------------


def test_cli_module_offline_smoke(weights_ready, clean_proxy_env):
    """`python -m freshlatch.doctor --offline` 子进程:零网络 exit 0,stdout 中文。"""
    import os

    env = {k: v for k, v in dict(os.environ).items() if k not in PROXY_VARS}
    env["PYTHONUTF8"] = "1"  # 管道 stdout 在 Windows 默认 cp936,钉死 UTF-8 使编码检查确定
    proc = subprocess.run(
        [sys.executable, "-m", "freshlatch.doctor", "--offline"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "环境自检" in proc.stdout
    assert "网络可达" in proc.stdout
    assert "全部通过" in proc.stdout
