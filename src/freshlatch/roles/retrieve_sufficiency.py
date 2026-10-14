"""检索观察的充分性标签。纯函数,零 I/O。

与 `roles/loop.py` 相邻:只回答「这次检索够不够继续写 fresh」。
不训练分类器,不联网,不改规则闸。无 `t1_evidence_ids` 不得 fresh 仍在
`gates/rule_gate.py`,本模块不放宽它。
"""

from __future__ import annotations

from typing import Literal

Sufficiency = Literal["sufficient", "insufficient"]

# 检索观察拒因。与规则闸 NO_T1_EVIDENCE 分工:本码在写 fresh 之前。
REASON_INSUFFICIENT_EVIDENCE = "insufficient_evidence"

INSUFFICIENT_FRESH_REFUSAL = (
    "reverify_claim(fresh) 拒绝: 检索观察 sufficiency=insufficient,"
    "reason_code=insufficient_evidence。本轮未见可引用的 @T1 块,不得写 fresh。"
)


def label_retrieve_sufficiency(blocks: list) -> dict[str, str | None]:
    """给一次 retrieve 的块列表打标。

    至少一条 evidence_id 以 @T1 结尾 → sufficient,reason_code 为空。
    否则(含零块)→ insufficient + insufficient_evidence。
    只看 id 后缀,不读正文,不打分。
    """
    for block in blocks:
        if not isinstance(block, dict):
            continue
        evidence_id = str(block.get("evidence_id") or "")
        if evidence_id.endswith("@T1"):
            return {"sufficiency": "sufficient", "reason_code": None}
    return {
        "sufficiency": "insufficient",
        "reason_code": REASON_INSUFFICIENT_EVIDENCE,
    }


def may_continue_fresh_write(observations: list[dict]) -> bool:
    """本会话是否可继续写 fresh。

    尚无检索观察时不在此拒,既有证据白名单与规则闸仍负责。
    任一观察为 sufficient 时,本票不把该输入改成拒答。
    已有观察且全部为 insufficient 时,不得继续写 fresh。
    """
    if not observations:
        return True
    return any(item.get("sufficiency") == "sufficient" for item in observations)
