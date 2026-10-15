"""MUM-S6 密钥与连通性体检。

默认只做 env 与 resolve_model：不发 HTTP，不发 chat completions，不读 .env 文件。
``--probe-lms`` / ``--probe-http`` 才对 base_url 做 GET ``/models``。
不写 C-04 RESULT，不改 floors / gold / x1 / production arm。

退出码：0 通过；1 配置（未知 profile、空 LMS、缺 env、非法地址、超时参数）；
2 探针不可达（超时、连接失败、HTTP 非 2xx）或 argparse 拒绝参数。
正式跑的 cloud profile 闸在 S7，不在本脚本。
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from freshlatch.model_profile import (
    ENV_MODEL_PROFILE,
    KNOWN_PROFILES,
    LOCAL_LMS_OVERLAY_SLOTS,
    LMS_PLATFORM,
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

_COLUMNS = ("profile", "slot", "model", "platform", "base_url", "env_key", "env")
_READ_LIMIT = 4096


@dataclass(frozen=True)
class ProbeHit:
    """一次 GET /models 的结果。error 为空表示 HTTP 2xx。不含密钥，不含正文。"""

    url: str
    status: int
    error: str | None


@dataclass(frozen=True)
class _Row:
    profile: str
    slot: str
    model: str
    platform: str
    base_url: str | None
    env_key: str | None
    env_state: str


@dataclass(frozen=True)
class _Report:
    text: str
    code: int
    error: str | None


def env_state(env_key: str | None) -> str:
    """present / missing / n/a。不返回密钥值。"""
    if not env_key:
        return "n/a"
    raw = os.environ.get(env_key)
    if raw is None or not raw.strip():
        return "missing"
    return "present"


def models_endpoint(base_url: str) -> str:
    """OpenAI 兼容根地址加上 ``/models``。不改写成别的路径。"""
    base = base_url.strip()
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ModelProfileError(f"base_url 不是带主机名的 http(s) 地址: {base_url!r}")
    trimmed = base.rstrip("/")
    if trimmed.endswith("/models"):
        return trimmed
    return trimmed + "/models"


def http_get(url: str, timeout: float, api_key: str | None) -> ProbeHit:
    """GET url。只在请求头放 Bearer。不发 POST，不读成聊天结果。"""
    headers = {
        "Accept": "application/json",
        "User-Agent": "FreshLatch-model-connectivity/1.0",
    }
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(_READ_LIMIT)
            status = int(getattr(response, "status", 0) or 0)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        if 200 <= status <= 299:
            return ProbeHit(url=url, status=status, error=None)
        return ProbeHit(url=url, status=status, error=f"HTTP {status}")
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            return ProbeHit(url=url, status=0, error="timeout")
        return ProbeHit(url=url, status=0, error="connection")
    except TimeoutError:
        return ProbeHit(url=url, status=0, error="timeout")
    except OSError:
        return ProbeHit(url=url, status=0, error="connection")
    if 200 <= status <= 299:
        return ProbeHit(url=url, status=status, error=None)
    return ProbeHit(url=url, status=status, error=f"HTTP {status}")


def _cell(value: str | None) -> str:
    if not value:
        return "-"
    return value


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


def _require_slot_coverage() -> None:
    missing = sorted(set(MODEL_REGISTRY) - set(SLOTS))
    extra = sorted(set(SLOTS) - set(MODEL_REGISTRY))
    if missing or extra:
        detail = []
        if missing:
            detail.append("未覆盖 " + ", ".join(missing))
        if extra:
            detail.append("多余 " + ", ".join(extra))
        raise ModelProfileError("代表 slot 与 registry 不一致: " + "; ".join(detail))


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
        raise ModelProfileError(f"体检不接受 profile {profile!r}")
    if slot in PROFILE_LOCKED_SLOTS or slot not in LOCAL_LMS_OVERLAY_SLOTS:
        if entry is not cloud:
            raise ModelProfileError(f"local-lms 下 {slot} 应保持 registry 原对象")
        return
    if entry is cloud or entry.platform != LMS_PLATFORM:
        raise ModelProfileError(f"local-lms 下 {slot} 应覆盖为 LM Studio")


def selected_name(explicit: str | None) -> str:
    """显式 --profile 不读 FRESHLATCH_MODEL_PROFILE。缺省且未设置该 env 时是 cloud。"""
    if explicit is not None:
        resolve_model("default_llm", profile=explicit)
        return explicit
    raw = os.environ.get(ENV_MODEL_PROFILE)
    if raw is None:
        return PROFILE_CLOUD
    name = raw.strip()
    if name not in KNOWN_PROFILES:
        resolve_model("default_llm")
        raise ModelProfileError(f"未知模型 profile {raw!r}")
    return name


def _bearer(env_key: str | None) -> str | None:
    if not env_key:
        return None
    raw = os.environ.get(env_key)
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    return value


def _missing_message(rows: list[_Row]) -> str:
    parts: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if row.env_state != "missing" or not row.env_key or row.env_key in seen:
            continue
        seen.add(row.env_key)
        slots = [item.slot for item in rows if item.env_key == row.env_key and item.env_state == "missing"]
        parts.append(f"{row.env_key} ({', '.join(slots)})")
    return "missing env " + "; ".join(parts)


def probe_label(probe_http: bool, probe_lms: bool) -> str:
    parts: list[str] = []
    if probe_http:
        parts.append("http")
    if probe_lms:
        parts.append("lms")
    if not parts:
        return "none"
    return ",".join(parts)


def _collect(profile: str | None) -> tuple[str, list[_Row]]:
    _require_slot_coverage()
    _require_formal_pins()
    name = selected_name(profile)
    rows: list[_Row] = []
    for slot in SLOTS:
        entry = resolve_model(slot, profile=profile)
        _check(name, slot, entry)
        rows.append(
            _Row(
                profile=name,
                slot=slot,
                model=entry.model,
                platform=entry.platform,
                base_url=entry.base_url,
                env_key=entry.env_key,
                env_state=env_state(entry.env_key),
            )
        )
    return name, rows


def _targets(
    rows: list[_Row],
    *,
    probe_http: bool,
    probe_lms: bool,
) -> list[tuple[str, str | None]]:
    """返回 (url, api_key)。LMS 只在 profile=local-lms 的解析结果或 --probe-lms 里出现。"""
    ordered: list[tuple[str, str | None]] = []
    seen: set[str] = set()

    def add(base_url: str | None, api_key: str | None) -> None:
        if not base_url:
            return
        url = models_endpoint(base_url)
        if url in seen:
            return
        seen.add(url)
        ordered.append((url, api_key))

    if probe_http:
        for row in rows:
            add(row.base_url, _bearer(row.env_key))
    if probe_lms:
        # 只取 local-lms overlay 的地址。cloud profile 下也不会把 DashScope 加进来。
        lms = resolve_model("default_llm", profile=PROFILE_LOCAL_LMS)
        add(lms.base_url, None)
    if not ordered:
        raise ModelProfileError("没有可探测的 base_url")
    return ordered


def _table(rows: list[_Row]) -> str:
    rendered = [
        (
            row.profile,
            row.slot,
            _cell(row.model),
            _cell(row.platform),
            _cell(row.base_url),
            _cell(row.env_key),
            row.env_state,
        )
        for row in rows
    ]
    return _format(rendered)


def _footer(word: str, name: str, rows: list[_Row], probe: str) -> str:
    missing = sum(1 for row in rows if row.env_state == "missing")
    return (
        f"{word} profile={name} slots={len(rows)} env_missing={missing} "
        f"probe={probe} chat=none"
    )


def build_report(
    profile: str | None,
    *,
    probe_http: bool,
    probe_lms: bool,
    timeout: float,
) -> _Report:
    name, rows = _collect(profile)
    probe = probe_label(probe_http, probe_lms)
    header = f"smoke_model_connectivity probe={probe} chat=none"
    table = _table(rows)
    missing = [row for row in rows if row.env_state == "missing"]
    if missing:
        text = "\n".join((header, table, _footer("fail", name, rows, probe)))
        return _Report(text=text, code=1, error=_missing_message(rows))
    if not probe_http and not probe_lms:
        text = "\n".join((header, table, _footer("ok", name, rows, probe)))
        return _Report(text=text, code=0, error=None)

    targets = _targets(rows, probe_http=probe_http, probe_lms=probe_lms)
    lines = [header, table]
    failures: list[str] = []
    for url, api_key in targets:
        hit = http_get(url, timeout, api_key)
        if hit.error is None:
            lines.append(f"probe GET {hit.url} status={hit.status}")
            continue
        lines.append(f"probe GET {hit.url} error={hit.error}")
        failures.append(f"unreachable GET {hit.url} {hit.error}")
    word = "fail" if failures else "ok"
    lines.append(_footer(word, name, rows, probe))
    if failures:
        return _Report(text="\n".join(lines), code=2, error="; ".join(failures))
    return _Report(text="\n".join(lines), code=0, error=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "检查当前 profile 的 env 与 resolve_model。默认不发 HTTP。"
            " --probe-lms / --probe-http 才 GET /models。不发 chat completions。"
        ),
    )
    parser.add_argument(
        "--profile",
        choices=(PROFILE_CLOUD, PROFILE_LOCAL_LMS),
        default=None,
        help="cloud 或 local-lms。缺省时读 FRESHLATCH_MODEL_PROFILE，未设置则为 cloud。",
    )
    parser.add_argument(
        "--probe-lms",
        action="store_true",
        help="GET LM Studio 的 /models。profile 不是 local-lms 时也只打 LMS 地址，不打云端 chat。",
    )
    parser.add_argument(
        "--probe-http",
        action="store_true",
        help="对当前 profile 解析出的 http(s) base_url GET /models。CI 不要加这个旗标。",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="探针超时秒数，必须大于 0。默认 5。",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        print("smoke_model_connectivity failed: --timeout 必须大于 0", file=sys.stderr)
        return 1
    try:
        report = build_report(
            args.profile,
            probe_http=args.probe_http,
            probe_lms=args.probe_lms,
            timeout=args.timeout,
        )
    except ModelProfileError as exc:
        print(f"smoke_model_connectivity failed: {exc}", file=sys.stderr)
        return 1
    print(report.text, flush=True)
    if report.error:
        print(f"smoke_model_connectivity failed: {report.error}", file=sys.stderr)
    return report.code


if __name__ == "__main__":
    raise SystemExit(main())
