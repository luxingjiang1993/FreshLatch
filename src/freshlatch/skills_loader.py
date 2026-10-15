"""SKILL.md 教义表加载器(规格 T6 实装债,#21):Runner 在角色会话启动时整份注入正文。

c5/c6 事故根因之一(#19 评估文档事实 1):教义表在盘不在场——docstring 声称「Runner 注入
替换」但全 src 无加载代码,c5 二修的 SKILL 同步在行为层空转。本模块就是补这个接线债。

纪律:加载失败返回 None(不抛),由调用方回退内联人格并落 `skill_fallback` 事件——
静默降级 = 在盘不在场的事故形态复发。

references 不进这次注入。`load_skill_reference` 只读 `skills/<slug>/references/<name>.md`,
供测试与调用方按需打开。它不进入 Runner 默认技能注入列表,也不是 Lead 工具。

A-P9 单包 allowlist 走 `mounted_skill_package` / `invoke_skill_tool`。
默认 off,不改 `load_skill_body`,也不进 Runner 默认注入。
范围是单包 demo / 非 marketplace。
"""

from __future__ import annotations

import os
import re
import time
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2] / "skills"

# 与技能目录名、references 文件主名同形。拒绝目录穿越与扩展名。
_SLUG_RE = re.compile(r"^[a-z0-9]+([-_][a-z0-9]+)*$")
_REF_STEM_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def load_skill_body(slug: str, *, skills_root: Path | None = None) -> str | None:
    """读取 skills/<slug>/SKILL.md 正文(frontmatter 剥掉);文件缺失或正文为空返回 None。"""
    path = (skills_root or SKILLS_ROOT) / slug / "SKILL.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    body = text
    if lines and lines[0].strip() == "---":
        try:
            end = lines.index("---", 1)
            body = "\n".join(lines[end + 1:])
        except ValueError:  # frontmatter 未闭合:整份按正文处理,不猜
            body = text
    body = body.strip()
    return body or None


def load_skill_reference(
    slug: str, name: str, *, skills_root: Path | None = None,
) -> str | None:
    """只读 skills/<slug>/references/<name>.md。

    name 是文件主名,不含 .md、不含目录。缺失、空文件、或路径不在该 references
    目录内时返回 None。不读 SKILL.md,也不改变 load_skill_body 的注入范围。
    """
    if not _SLUG_RE.fullmatch(slug) or not _REF_STEM_RE.fullmatch(name):
        return None
    root = (skills_root or SKILLS_ROOT).resolve()
    skill_dir = (root / slug).resolve()
    ref_dir = (skill_dir / "references").resolve()
    path = (ref_dir / f"{name}.md").resolve()
    # 技能目录、references 目录、目标文件解析后都必须留在 skills 根下。
    # references 或文件本身是指向根外的符号链接时,这里拒绝。
    if not skill_dir.is_relative_to(root):
        return None
    if not ref_dir.is_relative_to(skill_dir):
        return None
    if not path.is_relative_to(ref_dir):
        return None
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


# -- A-P9: 单包 allowlist -------------------------------------------------------
# 默认 off。只挂恰好一个业务包。角色教义包不从这里挂。
# 不改 Runner 的三次 load_skill_body。

SKILL_ALLOWLIST_ENV = "FRESHLATCH_SKILL_ALLOWLIST"

BUSINESS_SKILL_PACKAGES: tuple[str, ...] = (
    "earnings_figures",
    "event_timeline",
    "patch_diff",
    "strategy_walkthrough",
)

# 确定性触发词,只给单包 demo 的该触发 / 不该触发判断。不调用模型。
SKILL_TRIGGER_TERMS: dict[str, tuple[str, ...]] = {
    "earnings_figures": ("财报", "收入", "毛利", "客单价"),
    "event_timeline": ("产品发布", "监管口径", "访谈改口"),
    "patch_diff": ("patch diff", "before_text", "after_text"),
    "strategy_walkthrough": ("walkthrough", "战略主张", "顾问报告"),
}

SKILL_TRACE_FIELDS: tuple[str, ...] = ("package", "id", "ok", "latency", "reason")

REASON_SKILL_ALLOWLIST_OFF = "skill_allowlist_off"
REASON_SKILL_ALLOWLIST_INVALID = "skill_allowlist_invalid"
REASON_SKILL_NOT_TRIGGERED = "skill_not_triggered"
REASON_SKILL_TOOL_NOT_ALLOWED = "skill_tool_not_allowed"
REASON_SKILL_OK = "ok"


def _parse_allowlist(raw: object) -> tuple[str | None, str]:
    """空白或字面量 off 视为未挂载。多项、未知 slug、角色包一律无效。"""
    if raw is None:
        return None, REASON_SKILL_ALLOWLIST_OFF
    if not isinstance(raw, str):
        return None, REASON_SKILL_ALLOWLIST_INVALID
    text = raw.strip()
    if text == "" or text == "off":
        return None, REASON_SKILL_ALLOWLIST_OFF
    if "," in text or any(ch.isspace() for ch in text):
        return None, REASON_SKILL_ALLOWLIST_INVALID
    if text not in BUSINESS_SKILL_PACKAGES:
        return None, REASON_SKILL_ALLOWLIST_INVALID
    return text, REASON_SKILL_OK


def mounted_skill_package(
    *,
    config: Mapping[str, str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> tuple[str | None, str]:
    """解析单包 allowlist。返回 (slug 或 None, reason)。

    配置里有 ``FRESHLATCH_SKILL_ALLOWLIST`` 时用配置,否则读环境。
    键缺失、空白、``off`` 都是 off,不挂任何包。
    恰好一个业务包 slug 才挂载。不会因为无效配置改挂全部包。
    """
    if config is not None and SKILL_ALLOWLIST_ENV in config:
        return _parse_allowlist(config[SKILL_ALLOWLIST_ENV])
    env = os.environ if environ is None else environ
    if SKILL_ALLOWLIST_ENV not in env:
        return None, REASON_SKILL_ALLOWLIST_OFF
    return _parse_allowlist(env[SKILL_ALLOWLIST_ENV])


def _text_triggers(package: str, text: str) -> bool:
    terms = SKILL_TRIGGER_TERMS.get(package)
    if not terms or not isinstance(text, str):
        return False
    hay = text.casefold()
    return any(term.casefold() in hay for term in terms)


def triggered_skill_package(
    text: str,
    *,
    config: Mapping[str, str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """当前挂载的那一个包是否该被这句话触发。未挂载或词不中则 None。"""
    mounted, _reason = mounted_skill_package(config=config, environ=environ)
    if mounted is None:
        return None
    if _text_triggers(mounted, text):
        return mounted
    return None


def _tool_tenant(tool_args: dict | None) -> str | None:
    if not isinstance(tool_args, dict) or "tenant_id" not in tool_args:
        return None
    value = tool_args.get("tenant_id")
    if value is None:
        return None
    return str(value)


def _authorize_skill_call(
    *,
    authorization: str | None,
    api_key: str | None,
    client_tenant: str | None,
    tool_tenant: str | None,
) -> str | None:
    """服务端会话 ACL。通过时返回 None,拒绝时返回原因码。不执行工具。"""
    from freshlatch.serving.acl import enforce_mapped_action
    from freshlatch.store.tenant_acl import resolve_pre_retrieval_tenant

    outcome = enforce_mapped_action(
        None,
        "session",
        authorization=authorization,
        api_key=api_key,
        client_tenant=client_tenant,
    )
    if outcome.get("ok") is not True:
        code = outcome.get("code")
        return str(code) if code else REASON_SKILL_ALLOWLIST_INVALID
    server = outcome.get("tenant_id")
    _resolved, denied = resolve_pre_retrieval_tenant(
        server if isinstance(server, str) else None,
        tool_tenant,
    )
    if denied is not None:
        code = denied.get("reason_code")
        return str(code) if code else "tenant_acl_denied"
    return None


def _write_trace(
    traces: list | None,
    *,
    package: str,
    invocation_id: str,
    ok: bool,
    started: float,
    reason: str,
    result: object,
    fail_closed: bool,
) -> dict:
    """轨迹字段固定为 package / id / ok / latency / reason。latency 单位是秒。"""
    trace = {
        "package": package,
        "id": invocation_id,
        "ok": ok,
        "latency": time.perf_counter() - started,
        "reason": reason,
    }
    if traces is not None:
        traces.append(trace)
    return {
        "ok": ok,
        "fail_closed": fail_closed,
        "reason": reason,
        "trace": trace,
        "result": result,
    }


def invoke_skill_tool(
    text: str,
    tool_name: str,
    tool_args: dict | None,
    handler: Callable[[dict], dict],
    *,
    config: Mapping[str, str] | None = None,
    environ: Mapping[str, str] | None = None,
    authorization: str | None = None,
    api_key: str | None = None,
    client_tenant: str | None = None,
    approval: object | None = None,
    traces: list | None = None,
    invocation_id: str | None = None,
) -> dict:
    """挂载包上的一次 skill→tool。

    未挂载、不该触发、ACL 拒绝、工具不在业务包投影、或 tool_tier 拒绝时,
    不调用 handler。tool_tier_2 与未分级名字交给 ``dispatch_tiered_tool``,
    不绕过 FC 分档。通过后的工具同样只经 ``dispatch_tiered_tool`` 执行。
    """
    from freshlatch.tools import (
        LEAD_TOOLS_W3,
        REASON_TOOL_TIER_DENIED,
        TOOL_TIER_2,
        dispatch_tiered_tool,
        tool_tier_of,
    )

    started = time.perf_counter()
    invocation = invocation_id or uuid.uuid4().hex
    mounted, mount_reason = mounted_skill_package(config=config, environ=environ)
    if mounted is None:
        return _write_trace(
            traces,
            package="",
            invocation_id=invocation,
            ok=False,
            started=started,
            reason=mount_reason,
            result=None,
            fail_closed=True,
        )
    if not _text_triggers(mounted, text):
        return _write_trace(
            traces,
            package=mounted,
            invocation_id=invocation,
            ok=False,
            started=started,
            reason=REASON_SKILL_NOT_TRIGGERED,
            result=None,
            fail_closed=True,
        )
    denied_reason = _authorize_skill_call(
        authorization=authorization,
        api_key=api_key,
        client_tenant=client_tenant,
        tool_tenant=_tool_tenant(tool_args),
    )
    if denied_reason is not None:
        return _write_trace(
            traces,
            package=mounted,
            invocation_id=invocation,
            ok=False,
            started=started,
            reason=denied_reason,
            result=None,
            fail_closed=True,
        )
    args = dict(tool_args or {})
    tier = tool_tier_of(tool_name)
    trajectory: list = []
    if tier == TOOL_TIER_2 or tier is None:
        observed = dispatch_tiered_tool(
            tool_name,
            args,
            handler,
            approval=approval,
            trajectory=trajectory,
        )
        return _write_trace(
            traces,
            package=mounted,
            invocation_id=invocation,
            ok=False,
            started=started,
            reason=REASON_TOOL_TIER_DENIED,
            result=observed,
            fail_closed=True,
        )
    if tool_name not in LEAD_TOOLS_W3:
        return _write_trace(
            traces,
            package=mounted,
            invocation_id=invocation,
            ok=False,
            started=started,
            reason=REASON_SKILL_TOOL_NOT_ALLOWED,
            result=None,
            fail_closed=True,
        )
    observed = dispatch_tiered_tool(
        tool_name,
        args,
        handler,
        approval=approval,
        trajectory=trajectory,
    )
    denied = bool(trajectory) and trajectory[-1].get("ok") is False
    if denied:
        return _write_trace(
            traces,
            package=mounted,
            invocation_id=invocation,
            ok=False,
            started=started,
            reason=REASON_TOOL_TIER_DENIED,
            result=observed,
            fail_closed=True,
        )
    return _write_trace(
        traces,
        package=mounted,
        invocation_id=invocation,
        ok=True,
        started=started,
        reason=REASON_SKILL_OK,
        result=observed,
        fail_closed=False,
    )
