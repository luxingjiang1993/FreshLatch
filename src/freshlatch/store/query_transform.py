"""主张查询变换:确定性模板,角色不得自由改写检索串。

默认:statement 恒等。给出登记维度或 focus 时,在末尾追加封闭枚举的中文名。
"""

from __future__ import annotations

from freshlatch.tools import FOCUS_DIMENSIONS

DIMENSION_ZH: dict[str, str] = dict(zip(
    FOCUS_DIMENSIONS,
    ("竞品价格", "监管口径", "访谈改口", "成本模型", "市场结构", "技术生态"),
))


def transform_claim_query(
    statement: str,
    *,
    dimension: str | None = None,
    focus: str | None = None,
) -> str:
    """把主张变成 retrieve 的 query。focus 优先于登记维度;都空则为恒等。"""
    text = (statement or "").strip()
    if not text:
        raise ValueError("主张查询变换需要非空 statement")
    key = focus or dimension
    if not key:
        return text
    label = DIMENSION_ZH.get(key)
    if label is None:
        raise ValueError(f"主张查询变换只接受封闭枚举,收到: {key}")
    return f"{text} {label}"
