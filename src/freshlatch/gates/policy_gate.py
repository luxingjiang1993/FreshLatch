"""I3 #249 · Policy-as-code（thin · idea #8）出处禁区旁路。

声明式规则经 Verify+ **旁路**装入绿灯出口：命中 → **政策拒** → 不得绿灯。
与 `rule_gate` 不变量正文解耦（ADR-0032）：本模块不改写既有新鲜度/元陈述/注入等谓词。

语义分列：
- 政策拒 ≠ 新鲜度拒（stale/unknown/must_stale）
- 政策拒 ≠ 元陈述拒 / ACL·poison 拒

零 LLM；规则文件 JSON（亦可扩 YAML，本期 JSON）。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from freshlatch.gates.rule_gate import GateResult

# 政策拒稳定码（可见；≠ 新鲜度闸码）
ERR_POLICY_SOURCE_BAN = "POLICY_SOURCE_BAN"

DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "policy" / "source_ban.json"
)

_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


@dataclass(frozen=True)
class PolicyRule:
    """单条声明式规则。本期硬条仅 kind=source_ban。"""

    rule_id: str
    kind: str
    patterns: tuple[str, ...]
    description: str = ""


@dataclass(frozen=True)
class PolicyRules:
    version: str
    rules: tuple[PolicyRule, ...]
    note: str = ""


@dataclass
class PolicyContext:
    """政策旁路输入：出处串（域名/URL/路径/doc_id）供禁区匹配。

    已入库 T1 仍可被出处政策拒支撑绿灯——入库 ≠ 可绿（与薄 URL 白名单正交）。
    """

    provenance: list[str] = field(default_factory=list)


def load_policy_rules(path: str | Path | None = None) -> PolicyRules:
    """加载声明式政策规则（JSON）。path 缺省 = data/policy/source_ban.json。"""
    target = Path(path) if path is not None else DEFAULT_POLICY_PATH
    raw = json.loads(target.read_text(encoding="utf-8"))
    rules: list[PolicyRule] = []
    for item in raw.get("rules") or []:
        patterns = tuple(str(p).strip() for p in (item.get("patterns") or []) if str(p).strip())
        if not patterns:
            continue
        rules.append(
            PolicyRule(
                rule_id=str(item.get("id") or item.get("rule_id") or "").strip(),
                kind=str(item.get("kind") or "").strip(),
                patterns=patterns,
                description=str(item.get("description") or ""),
            )
        )
    return PolicyRules(
        version=str(raw.get("version") or "1"),
        rules=tuple(rules),
        note=str(raw.get("note") or ""),
    )


def extract_provenance_refs(
    *,
    evidence_ids: Iterable[str] | None = None,
    texts: Iterable[str] | None = None,
    extra: Iterable[str] | None = None,
) -> list[str]:
    """从证据 id / 正文 URL / 显式额外出处收集可匹配串（去重保序）。"""
    out: list[str] = []
    seen: set[str] = set()

    def _add(value: str) -> None:
        text = (value or "").strip()
        if not text or text in seen:
            return
        seen.add(text)
        out.append(text)

    for eid in evidence_ids or ():
        _add(eid)
        # doc_id#anchor@as_of → doc_id
        if "#" in eid:
            _add(eid.split("#", 1)[0])
    for body in texts or ():
        for match in _URL_RE.findall(body or ""):
            _add(match.rstrip(").,;]"))
    for item in extra or ():
        _add(item)
    return out


def _host_of(ref: str) -> str | None:
    text = ref.strip()
    if "://" in text:
        host = (urlparse(text).hostname or "").lower()
        return host or None
    # 裸域名样：banned.example 或 banned.example/path
    if "/" in text and not text.startswith("/"):
        head = text.split("/", 1)[0].lower()
        if "." in head and " " not in head:
            return head
    if "." in text and " " not in text and "/" not in text and "#" not in text:
        return text.lower()
    return None


def _path_of(ref: str) -> str:
    text = ref.strip()
    if "://" in text:
        parsed = urlparse(text)
        return parsed.path or "/"
    if text.startswith("/"):
        return text
    if "/" in text and not text.startswith("#"):
        # host/path → /path
        return "/" + text.split("/", 1)[1]
    return text


def _pattern_hits(ref: str, pattern: str) -> bool:
    """域名精确/后缀，或路径 glob/子串。"""
    pat = pattern.strip()
    if not pat:
        return False
    ref_l = ref.lower()
    pat_l = pat.lower()

    # 路径 glob（含 *）或以 / 开头：对 path 与全文做 fnmatch 风格
    if "*" in pat or pat.startswith("/"):
        import fnmatch

        path = _path_of(ref)
        return bool(
            fnmatch.fnmatch(path.lower(), pat_l)
            or fnmatch.fnmatch(ref_l, pat_l)
            or fnmatch.fnmatch(ref_l, f"*{pat_l}")
        )

    # 域名模式：host 相等或为子域
    host = _host_of(ref)
    if host is not None:
        if host == pat_l or host.endswith("." + pat_l):
            return True
        # URL 全文含该域名片段（防漏）
        if pat_l in ref_l:
            return True

    # doc_id / 路径子串
    return pat_l in ref_l


def apply_policy_gate(ctx: PolicyContext, rules: PolicyRules) -> GateResult:
    """对出处上下文施加政策闸。命中 source_ban → 政策拒（非绿）。

    未命中返回 green=True（旁路放行）；非 source_ban 规则本期忽略（留位）。
    """
    refs = [r for r in ctx.provenance if (r or "").strip()]
    for rule in rules.rules:
        if rule.kind != "source_ban":
            continue
        for ref in refs:
            for pat in rule.patterns:
                if _pattern_hits(ref, pat):
                    return GateResult(
                        allowed=False,
                        green=False,
                        error_code=ERR_POLICY_SOURCE_BAN,
                        reason=(
                            f"政策拒(出处禁区):规则 {rule.rule_id or '(unnamed)'} "
                            f"命中模式 {pat!r} ← 出处 {ref!r}"
                            "（政策拒 ≠ 新鲜度拒；ADR-0032 / I3 #249）"
                        ),
                    )
    return GateResult(allowed=True, green=True, reason="政策旁路:未命中禁区")


def apply_policy_after_rule_gate(
    rule_result: GateResult,
    *,
    provenance: list[str],
    rules: PolicyRules | None = None,
    rules_path: str | Path | None = None,
) -> GateResult:
    """绿灯出口组合点：仅当 rule_gate 已绿时再跑政策旁路；否则原样返回。

    不修改 `rule_gate` 不变量函数正文——调用方在 rule_gate 之后组合本结果。
    """
    if not rule_result.green:
        return rule_result
    loaded = rules if rules is not None else load_policy_rules(rules_path)
    policy = apply_policy_gate(PolicyContext(provenance=list(provenance)), loaded)
    if not policy.green:
        return policy
    return rule_result
