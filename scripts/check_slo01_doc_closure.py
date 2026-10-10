#!/usr/bin/env python3
"""SLO-01：生产补丁/放行 SLO 文档闭环与禁词机检。

验收层=文档一致性(demo/纪律层),不是实验乙成立格。
退出码 0=通过;非 0=失败并打印原因。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 互指链上的真源路径(相对仓根)
CHAIN = {
    "ops": ROOT / "docs/ops/生产补丁放行SLO.md",
    "map": ROOT / "docs/ops/生产补丁放行SLO-地图.md",
    "research": ROOT / "docs/research/生产补丁放行SLO设计评估.md",
    "adr": ROOT / "docs/adr/0034-生产补丁放行SLO与实验防火墙.md",
    "spec": ROOT / "docs/spec/24-生产补丁放行SLO.md",
    "context": ROOT / "CONTEXT.md",
    "grill": ROOT / "docs/grill-prep.md",
    "spec_readme": ROOT / "docs/spec/README.md",
}

# 每个节点必须出现的互指标记(子串即可)
MUST_LINK: dict[str, list[str]] = {
    "ops": [
        "ADR-0034",
        "docs/research/生产补丁放行SLO设计评估.md",
        "docs/spec/24-生产补丁放行SLO.md",
        "CONTEXT.md",
    ],
    "adr": [
        "docs/ops/生产补丁放行SLO.md",
        "docs/research/生产补丁放行SLO设计评估.md",
        "docs/spec/24-生产补丁放行SLO.md",
        "CONTEXT.md",
    ],
    "research": [
        "ADR-0034",
        "docs/ops/生产补丁放行SLO.md",
        "docs/spec/24-生产补丁放行SLO.md",
        "CONTEXT.md",
        "§2j",
    ],
    "spec": [
        "0034",
        "docs/ops/生产补丁放行SLO.md",
        "docs/research/生产补丁放行SLO设计评估.md",
        "CONTEXT.md",
    ],
    "context": [
        "生产补丁/放行 SLO",
        "实验—生产防火墙",
        "docs/ops/生产补丁放行SLO.md",
        "ADR-0034",
        "docs/spec/24-生产补丁放行SLO.md",
        "docs/research/生产补丁放行SLO设计评估.md",
    ],
    "map": [
        "评估见 `docs/research/生产补丁放行SLO设计评估.md`",
        "ADR-0034",
        "docs/ops/生产补丁放行SLO.md",
    ],
    "grill": [
        "生产补丁/放行 SLO",
        "ADR-0034",
        "docs/ops/生产补丁放行SLO.md",
    ],
    "spec_readme": [
        "24-生产补丁放行SLO.md",
        "ADR-0034",
    ],
}

# 禁词扫描目标(与工单 Acceptance 一致)
BANNED_TARGETS = ("ops", "spec", "adr")
BANNED_RE = re.compile(r"软甲|接近乙|主实验成功")
# 允许出现在否定/禁止语境
NEGATION_MARKERS = ("禁止", "禁称", "禁", "不得", "Out of Scope", "文面禁止", "不")


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)


def check_paths() -> list[str]:
    errors: list[str] = []
    for key, path in CHAIN.items():
        if not path.is_file():
            errors.append(f"缺失路径 [{key}]: {path.relative_to(ROOT)}")
    return errors


def check_links() -> list[str]:
    errors: list[str] = []
    for key, needles in MUST_LINK.items():
        text = CHAIN[key].read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"互指缺失 [{key}] 缺「{needle}」")
    return errors


def _allowed_banned_hit(line: str) -> bool:
    """禁词仅允许出现在禁止/否定语境。"""
    return any(m in line for m in NEGATION_MARKERS)


def check_banned() -> list[str]:
    errors: list[str] = []
    for key in BANNED_TARGETS:
        path = CHAIN[key]
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not BANNED_RE.search(line):
                continue
            if _allowed_banned_hit(line):
                continue
            errors.append(
                f"禁词非禁止语境 [{key}]:{i}: {line.strip()}"
            )
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(check_paths())
    if not errors:
        errors.extend(check_links())
        errors.extend(check_banned())

    if errors:
        for e in errors:
            _fail(e)
        print(f"SLO-01 机检失败: {len(errors)} 项", file=sys.stderr)
        return 1

    print("SLO-01 机检通过: 路径存在 · 互指完整 · 禁词仅禁止语境")
    return 0


if __name__ == "__main__":
    sys.exit(main())
