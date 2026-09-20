# ADR-0009: 双判一致与 Auditor 在场不变量

- **状态**: Accepted(2026-09-21,工单 #20 拍板)
- **相关**: 工单 #20 评估见 `docs/research/Auditor形态设计评估.md`;形态确认 spec 03 §3.2;
  c2 派驻失灵定性 `docs/evidence/w4/repro-check.md` 背离二;#19 `docs/research/c5c6工程债处置设计评估.md`;
  不变量先例 ADR-0008

## 背景

W5–W8 Auditor(单轮判定 SOP)实装在即,而「Lead 判定 × Auditor 判定」的仲裁结构在规格与
代码(`rule_gate.py`)中双空白。最危险的缺口不是仲裁规则本身,而是**在场**:c2 事故已定性
「自信地错恰是派驻最不会触发的时刻」——若 Auditor 的参与由 Lead 主动调用(`spawn_auditor`)
决定,则 Auditor 恰在 Lead 自信错误(最需要它的时刻)系统性缺席。可选项的仲裁是演戏。

## 决议

### 1. 双判一致(fresh 的唯一路径是 Lead 与 Auditor 判定一致)

3×3 落档真值表(实现规格,单一真相在本 ADR 与评估文档):

| Lead \ Auditor | fresh | stale | unknown |
|---|---|---|---|
| **fresh** | **fresh(唯一绿格)** | stale | unknown |
| **unknown** | unknown + 异议记录 | stale | unknown |
| **stale** | stale + 异议记录 | stale | stale |

含 stale 落 stale;无 stale 含 unknown 落 unknown;全 fresh 才绿。Auditor 缺席不构成任何
绿格。安全不对称:fake-fresh(灾难方向,死主张挂绿灯)需双人一致;fake-stale(可恢复方向)
任一判即落,经 HumanLatch 人审兜底。Auditor 不得拥有放行权(词表)在此表现为:Auditor 的
fresh 永远不足以单独成绿。

### 2. Auditor 在场 = 闸层不变量,非模型自觉

`_t_reverify_claim(status=fresh)` 钩子内自动触发 Auditor(与 `_auto_critic_checkpoint` 同点
同构);规则闸新增前置不变量:`auditor_verdict` 在场且非 dissent,fresh 方可通过。触发器保证
运行,闸保证不变量,双保险零额外调用。**stale 路径不强制**:错误不对称推论——fake-stale 方向
已有 #19(Lead 侧维度自查+注入)与 HumanLatch 两层,第三层边际收益配不上每条主张的调用;
`spawn_auditor` 在 stale 路径保留为 Lead 主动工具(异议记录的技术载体)。

### 3. 异议记录(dissent)结构化落档

Lead stale/unknown × Auditor fresh 的反对意见(理由 + 证据 id)结构化挂在复验单该主张卡片下,
随红/黄卡进 HumanLatch,是人审续命的合法输入之一。自由文本异议不进复验单——人审负载下不可
diff 的异议等于没有异议。

## 后果

- 词表新增:`双判一致`(3×3 真值表落 CONTEXT.md 引用)、`异议记录`(CONTEXT.md)。
- 规则闸新增前置校验(GateDecision 扩展 auditor_verdict 字段);`auditor.py` 由边界占位实装为
  单轮 structured-output(SKILL.md 注入走 #19 已拍的 skills 接线)。
- 验收 pre-registration 随本 ADR 锁定(评估文档 §4.6):全量 12 条 n=3 temp=0;通过线含
  「must_fresh 不低于 #21 实测留档基线」,#21 未跑则本验收不得启动。
- 预登记重开触发器:W5–W8 若显单轮判定对合取主张噪声过大,形态重开新工单(本 ADR 管仲裁
  与在场,不管单轮形态本身——形态是 spec 03 §3.2 的既定决议)。
- 事后修改本 ADR 的不变量(放宽在场要求、改真值表)等于在保留「已验收」叙事的前提下拆双人
  拦截,W5–W8 及后续窗口的实验意义随之作废——修改必须走新评审工单并明示受影响窗口。
