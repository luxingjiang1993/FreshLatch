"""主张数字与所引 @T1 证据 span 的逐字对账。纯函数,零 I/O。

从主张文本抽出数字字面量,每一枚都必须作为同样的字面量出现在
所引证据 span 的数字字面量里。对不上则 numeric_mismatch,不得 fresh。
票内声明的容差:无。不把 12.5 当成 12.50,不把 1,299 当成 1299,
不做法式重算,不设 SESOI。
前导 ASCII 字母粘连的数字(T1、p1)不是数字字面量。
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

# 轨迹与工具回执共用这一枚拒因码。不是 grade_ambiguous。
REASON_NUMERIC_MISMATCH = "numeric_mismatch"

# 票内声明的容差。None 表示只接受字面量逐字相同。
NUMERIC_TOLERANCE = None

# 左边界挡住 T1 / p1 这类标识;右边界允许单位字母,但不把更长的小数拆开。
_NUMERIC_TOKEN = re.compile(
    r"(?<![0-9A-Za-z.])-?\d+(?:,\d{3})*(?:\.\d+)?%?(?!\d)(?!\.\d)"
)


@dataclass(frozen=True)
class VerbatimNumericResult:
    """ok 为真时本闸不拒。missing 保持主张中的出现顺序。"""

    ok: bool
    reason_code: str | None
    missing: tuple[str, ...]


def extract_numeric_tokens(text: str) -> tuple[str, ...]:
    """按出现顺序抽出不重复的数字字面量。空文本没有数字。"""
    if not text:
        return ()
    found: list[str] = []
    for match in _NUMERIC_TOKEN.finditer(text):
        token = match.group(0)
        if token not in found:
            found.append(token)
    return tuple(found)


def check_verbatim_numbers(
    claim_text: str,
    spans: Iterable[str],
) -> VerbatimNumericResult:
    """主张中的每个数字字面量都必须出现在所给 span 的数字字面量里。

    主张没有数字字面量时本闸通过,不代替其他拒答闸。
    spans 只应传入已经引用的 @T1 证据正文。
    """
    tokens = extract_numeric_tokens(claim_text)
    if not tokens:
        return VerbatimNumericResult(ok=True, reason_code=None, missing=())
    present: set[str] = set()
    for span in spans:
        present.update(extract_numeric_tokens(span))
    missing = tuple(token for token in tokens if token not in present)
    if missing:
        return VerbatimNumericResult(
            ok=False,
            reason_code=REASON_NUMERIC_MISMATCH,
            missing=missing,
        )
    return VerbatimNumericResult(ok=True, reason_code=None, missing=())


def numeric_mismatch_message(missing: Iterable[str]) -> str:
    """回给模型的观察。reason_code 另字段携带,文案本身不是原因码。"""
    shown = "、".join(missing)
    return (
        "reverify_claim(fresh) 拒绝: 主张中的数字未在所引 @T1 证据 span 中逐字出现,"
        f"reason_code={REASON_NUMERIC_MISMATCH}。不得写 fresh。缺失: {shown}"
    )
