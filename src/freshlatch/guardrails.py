"""步数/检索预算集中定义,由 Runner 注入;eval harness 可代码级覆盖(§6.1)。"""

from __future__ import annotations

from dataclasses import dataclass

BUDGET_EXHAUSTED_MESSAGE = "预算已尽,基于现有证据下结论。"


@dataclass
class Guardrails:
    lead_max_steps: int = 18
    critic_max_steps: int = 8
    auditor_max_steps: int = 6  # W5–W8 实装后生效
    forensic_max_steps: int = 8  # W9–W12
    retrieval_budget: int = 24  # Run 级共享,retrieve 装饰器计数

    def exhausted_soft_close(self) -> str:
        """步数预算归零时不硬断,注入此消息软收尾——护栏管天花板,不管结论。"""
        return BUDGET_EXHAUSTED_MESSAGE
