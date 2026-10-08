"""自动核验。只按已写明的一致那句比较。

``after_text`` 去掉首尾空白后，和所绑 ``evidence_text`` 逐字相同则 ``ok`` 为真，否则为假。
支撑和矛盾不另判。没有分数方向，``score`` 为空。
调用方传入臂、``claim_id``、``after_text``、``evidence_id``、``evidence_text``。
比较只用 ``after_text`` 和 ``evidence_text``。入库检查在核验前面做完，这里不再看。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def verify_edit(request: Mapping[str, Any]) -> dict[str, Any]:
    """返回 ``ok``、``score``、``reason``。``score`` 恒为空。"""
    after = request.get("after_text")
    evidence = request.get("evidence_text")
    ok = isinstance(after, str) and isinstance(evidence, str) and after.strip() == evidence
    return {"ok": ok, "score": None, "reason": "一致" if ok else "核验不过"}
