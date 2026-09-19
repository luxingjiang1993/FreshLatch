# FreshLatch

FreshLatch 的术语表。FreshLatch 把已签发主张从「曾经为真」改成「现在仍可复验」:过期、冲突、无 T1 原文支持的主张不得保持绿灯,人决定作废或续命。

## 主张与语料

**主张 (Claim)**:
一条已被签发过的陈述(如「专业版定价 299 元/席/月」),是复验的对象。
_Avoid_: 结论、论点、statement

**T0 / T1 语料**:
T0 是主张签发时的原始文档快照;T1 是复验时刻的新文档快照。判定以 T1 原文为 ground truth。
_Avoid_: 旧库/新库、源数据/目标数据

**must_stale**:
金标中必须被判定为 stale 的主张,任何 harness 不得对其放行,用于锁住评测可复现性。

**must_fresh**:
金标中必须被判定为 fresh 的主张;含「看似已死其实 fresh」干扰项,防止全红假象。

**must_unknown**:
金标中 T1 无原文覆盖、必须判 unknown 的主张;锁住「无 `t1_evidence_ids` 不得 fresh」这条闸的评测。

## 复验主链

**复验单 (Reverify Sheet)**:
一次复验的主界面与产出物:每条主张的原文点回、判定、理由、人审动作。不是聊天框。
_Avoid_: 报告、看板

**Lead Reverifier (Lead)**:
真 Agent,自主规划复验:改写查询、按 `as_of=T0|T1` 换源、读原文、调 `reverify_claim` / `mark_stale` / `mark_gap`,并决定是否派驻 Critic / Auditor / Forensic。
_Avoid_: 主 agent、调查员

**Critic**:
真 Agent,只找「主张已死」的反证,不得强化「仍然成立」,不得放行。
_Avoid_: 反驳者、质疑器

**focus 维度**:
Lead 派驻 Critic 时给的反证搜索方向。封闭枚举 6 值,与语料金标维度同构:竞品价格 / 监管口径 / 访谈改口 / 成本模型 / 市场结构 / 技术生态。可选参数,省略 = 不限方向;调用边界硬校验,非法值拒绝并回列词表,重试计步。金标不记 focus(评测测判定,不测调度品味)。
_Avoid_: 聚焦、方向、视角

**Auditor**:
短循环 Agent,判定 `fresh` / `stale` / `unknown`;不得改主张正文,**不得拥有放行权**。
_Avoid_: 审核员、裁判

**Forensic (记忆刑侦)**:
真 Agent,只审本课题长期记忆:找死事实、互斥条目、无 `source_ref` 条目;不得改主张、不得放行、不得删除文件。

## 闸与人审

**规则闸 (Gate)**:
纯函数/Workflow 层,强制执行不变量:`stale` / `unknown` 不得绿灯、无 `t1_evidence_ids` 不得 `fresh`、checksum 对不上不得 fresh/续命。绿灯唯一出口。
_Avoid_: 校验器、检查器

**HumanLatch**:
人审工作流:人对每条红/黄灯主张点「作废」或「续命」(续命必须带 T1 evidence_id),并确认记忆隔离。Agent 不得自己把红灯改回绿灯。

**作废名单 (Invalidation List)**:
被人作废的主张 id 清单;进名单的主张重跑时不得再判 fresh。删除文件另闸,可先隔离不删盘。

**隔离 (Quarantine)**:
把腐烂记忆条目移出召回集的动作;人确认前不得移出,Agent 不得自动抹记忆。

## 评测

**假绿对照 (False-Green Control)**:
无工具基线:同模型不带工具只读 T0 摘要,应把已死主张判「成立」(假绿)。本产品必须红,对照成立才说明复验真在起作用。

**金标 (Gold)**:
人工标注的期望判定(dead / alive / must_stale 等),harness 据此打分;评测期联网代码级禁用,保住可复现性。

**语料污染位**:
语料中故意埋的陷阱(看似死其实活、看似活其实死、fresh 干扰项),防止评测靠表面线索作弊。
