"""评测 harness(§4.1):金标对账 / 假绿对照 / 混淆矩阵 / 报告。

端到端 = 真实 Lead 循环 + Critic 派驻 + 规则闸,与复验单 UI 同一入口(ADR-0005 决策一)。
eval 模式两道代码级开关(§4.6):跳过 HumanLatch(W1–W4 未挂载,本包不 import langgraph);
联网禁用(web_search 不在任何角色白名单,模型物理上不可见)。
"""

from freshlatch.eval.matrix import BUCKETS, EXPECTED_VERDICT, VERDICTS, MatrixResult, confusion_matrix

__all__ = ["BUCKETS", "EXPECTED_VERDICT", "VERDICTS", "MatrixResult", "confusion_matrix"]
