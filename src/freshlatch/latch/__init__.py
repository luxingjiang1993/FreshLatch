"""HumanLatch 管道(ADR-0006)。LangGraph 用法全隔离在本包:Agent 循环(roles/)不 import langgraph。

- pipeline.HumanLatch:轮次级单 interrupt + 决定列表 resume + 单主张重跑 + checkpoint 清理。
- 评测模式代码级跳过(ADR-0006 §7):mode="eval" 时不建 thread、不碰 checkpoint、不 import langgraph
  (langgraph 均为函数内延迟导入,eval 路径零依赖)。
"""

from freshlatch.latch.pipeline import HumanLatch, HumanLatchError, LatchRound

__all__ = ["HumanLatch", "HumanLatchError", "LatchRound"]
