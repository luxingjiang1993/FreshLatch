"""doctor.py 环境自检 CLI(决议 #708 · 票 #714,Exit/harness)。

手动体检入口::

    python -m freshlatch.doctor            # 四检查项全跑(网络项会真连端点,默认 5s 超时)
    python -m freshlatch.doctor --offline  # 跳过网络项(CI 空跑 / 无网环境)

四检查项(决议 #708 钉死,不做依赖树全扫、不调真实 LLM):
网络可达 / 权重·模型路径存在 / 代理环境变量可读 / UTF-8 编码。

契约:
- 失败 → 非零 exit;stdout 全中文 + 检查项名;
- 不打印密钥、代理凭据与 API key(只报「已设置/未设置」与脱敏值);
- 类比 ``eval/auditor_arm.py`` harness 形态:CLI only、不进硬 CI(CI 仅 import
  smoke)、不上产品主 CTA、无 UI 自检按钮;
- 单项检查抛异常不崩整体:该项记失败,继续跑完剩余项。
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from freshlatch.model_profile import resolve_model
from freshlatch.ui.weight_precheck import (
    _cache_roots,
    local_embed_weights_ready,
    neural_rerank_weights_ready,
)

# 全部小写比较,别名同义:utf-8 / utf8。
_UTF8_ALIASES = {"utf-8", "utf8"}


@dataclass(frozen=True)
class CheckResult:
    """一项体检结果。name 是对外稳定的检查项名(stdout 逐字出现)。"""

    name: str
    ok: bool
    detail: str
    skipped: bool = False


def check_network(
    base_url: str | None = None,
    *,
    timeout: float = 5.0,
    connect: Callable[..., Any] | None = None,
) -> CheckResult:
    """TCP 连一下 LLM 端点(host:port)判网络可达;不发请求、不调 LLM。

    connect 可注入(测试夹具/特殊网络栈);缺省 socket.create_connection。
    """
    if base_url is None:
        entry = resolve_model("default_llm")
        base_url = entry.base_url
    try:
        parts = urlsplit(base_url)
        host = parts.hostname
    except ValueError:
        host = None
    if not host:
        return CheckResult("网络可达", False, f"端点地址无法解析:{base_url!r}")
    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
    except ValueError:  # 非数字端口
        return CheckResult("网络可达", False, f"端点端口非法:{base_url!r}")
    connector = connect or (lambda hp, to: socket.create_connection(hp, timeout=to))
    try:
        connector((host, port), timeout)
    except OSError as exc:
        return CheckResult(
            "网络可达", False,
            f"无法连接 {host}:{port}({exc.__class__.__name__});"
            "检查本机网络/代理配置,或重试;必要时用 --offline 跳过本项。",
        )
    return CheckResult("网络可达", True, f"端点 {host}:{port} 可连接")


def check_weights(cache_dir: str | None = None) -> CheckResult:
    """文件层 stat 权重快照(复用 I-02 预检,毫秒级;不 import fastembed、不加载模型)。"""
    embed_ok = local_embed_weights_ready(cache_dir)
    rerank_ok = neural_rerank_weights_ready(cache_dir)
    missing: list[str] = []
    if not embed_ok:
        missing.append("embedding(bge-small-zh-v1.5)")
    if not rerank_ok:
        missing.append("reranker(bge-reranker-base,约 1.1GB)")
    roots = "、".join(str(r) for r in _cache_roots(cache_dir))
    if missing:
        return CheckResult(
            "权重路径", False,
            f"缺权重快照:{'、'.join(missing)};缓存目录 {roots} 未命中。"
            "可在 UI 预检面板下载,或先选「先用 BM25(精度降级)」跑通主链。",
        )
    return CheckResult("权重路径", True, f"embedding 与 reranker 权重缓存就绪({roots})")


def _redact_proxy_value(value: str) -> str:
    """代理值脱敏:netloc 含 userinfo 时只留 scheme://***@host:port。"""
    try:
        parts = urlsplit(value if "//" in value else f"http://{value}")
        host = parts.hostname or "?"
        port = parts.port
    except ValueError:
        return "***"
    netloc = host if port is None else f"{host}:{port}"
    if "@" in parts.netloc:
        netloc = f"***@{netloc}"
    return f"{parts.scheme}://{netloc}"


def _env_value(env: Mapping[str, str], key: str) -> str | None:
    """大小写都认(urllib 系偏好小写);取到非空值即返回。"""
    for k in (key, key.lower()):
        v = env.get(k)
        if v:
            return v
    return None


def check_proxy(env: Mapping[str, str] | None = None) -> CheckResult:
    """代理环境变量「可读」检查:值可解析、NO_PROXY 无裸写 IPv6;脱敏回显。

    已知坏值:NO_PROXY 裸写 ``::1``(IPv6 必须写成 ``[::1]``,I-07 #679)。
    只读不执行;凭据部分永不落 stdout。
    """
    env = os.environ if env is None else env
    set_vars: list[str] = []
    problems: list[str] = []
    for key in ("HTTP_PROXY", "HTTPS_PROXY"):
        v = _env_value(env, key)
        if v:
            set_vars.append(f"{key}={_redact_proxy_value(v)}")
    no_proxy = _env_value(env, "NO_PROXY")
    if no_proxy:
        set_vars.append(f"NO_PROXY={no_proxy}")
        for token in no_proxy.split(","):
            t = token.strip()
            if not t or t.startswith("["):
                continue
            if t.count(":") >= 2:
                problems.append(f"NO_PROXY 里 IPv6 要写成 [{t}](裸写 {t})")
    if problems:
        current = ";".join(set_vars) if set_vars else "未设置"
        return CheckResult("代理环境变量", False, ";".join(problems) + f";当前:{current}")
    if set_vars:
        return CheckResult("代理环境变量", True, "可读;" + "; ".join(set_vars))
    return CheckResult("代理环境变量", True, "未设置(按直连处理;LLM 传输默认 trust_env=False)")


def check_encoding(streams: tuple[Any, ...] | None = None) -> CheckResult:
    """stdout/stderr 编码必须是 UTF-8,否则中文报告乱码(Windows 常见 cp936)。"""
    streams = (sys.stdout, sys.stderr) if streams is None else streams
    bad: list[str] = []
    for stream in streams:
        enc = (getattr(stream, "encoding", None) or "").lower()
        if enc not in _UTF8_ALIASES:
            bad.append(getattr(stream, "encoding", None) or "未知")
    if bad:
        return CheckResult(
            "UTF-8 编码", False,
            f"输出流编码非 UTF-8({', '.join(bad)});请设 PYTHONUTF8=1(或 chcp 65001)后重跑,"
            "否则中文报告会乱码。",
        )
    return CheckResult("UTF-8 编码", True, "stdout/stderr 均为 UTF-8")


def _guard(fn: Callable[..., CheckResult], **kwargs: Any) -> CheckResult:
    """单项检查抛异常不崩整体:记失败 + 中文异常名,继续跑剩余项。"""
    try:
        return fn(**kwargs)
    except Exception as exc:  # noqa: BLE001 — 体检入口,宽捕获保整体可跑完
        name = getattr(fn, "__name__", "未知检查")
        return CheckResult(f"检查异常:{name}", False, f"本项抛异常未跑完({exc.__class__.__name__})")


def run_checks(
    *,
    skip_network: bool = False,
    timeout: float = 5.0,
    env: Mapping[str, str] | None = None,
    connect: Callable[..., Any] | None = None,
    streams: tuple[Any, ...] | None = None,
) -> list[CheckResult]:
    """跑全部检查项;依赖全部可注入,测试零网络零真实下载。"""
    results: list[CheckResult] = []
    if skip_network:
        results.append(CheckResult("网络可达", True, "已跳过(--offline)", skipped=True))
    else:
        results.append(_guard(check_network, timeout=timeout, connect=connect))
    results.append(_guard(check_weights))
    results.append(_guard(check_proxy, env=env))
    results.append(_guard(check_encoding, streams=streams))
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="freshlatch.doctor",
        description="环境自检(决议 #708):网络可达/权重路径/代理环境变量/UTF-8;失败非零 exit。",
    )
    ap.add_argument("--offline", action="store_true",
                    help="跳过网络检查(CI 空跑 / 无网环境);其余项照跑")
    ap.add_argument("--timeout", type=float, default=5.0, help="网络检查超时秒数(默认 5)")
    args = ap.parse_args(argv)

    results = run_checks(skip_network=args.offline, timeout=args.timeout)
    print("FreshLatch 环境自检(doctor · 决议 #708)")
    for r in results:
        tag = "[跳过]" if r.skipped else ("[通过]" if r.ok else "[失败]")
        print(f"  {tag} {r.name}: {r.detail}")
    failed = [r for r in results if not r.ok]
    if failed:
        print(f"自检结论:失败 {len(failed)}/{len(results)} 项,按上方中文说明处理后重跑。")
        return 1
    print(f"自检结论:{len(results)} 项全部通过(含跳过项)。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
