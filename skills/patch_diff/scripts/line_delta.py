"""patch diff 行差计数。

比较 before_text 与 after_text 的行多重集,返回增删行数。
不写 patch_events,不改主张,不读语料。
"""

from collections import Counter


def line_delta(before_text: str, after_text: str) -> dict[str, int]:
    """统计改前独有行数、改后独有行数,以及两侧行数。"""
    before_lines = before_text.splitlines()
    after_lines = after_text.splitlines()
    before_counts = Counter(before_lines)
    after_counts = Counter(after_lines)
    removed = sum((before_counts - after_counts).values())
    added = sum((after_counts - before_counts).values())
    return {
        "removed": removed,
        "added": added,
        "before_lines": len(before_lines),
        "after_lines": len(after_lines),
    }
