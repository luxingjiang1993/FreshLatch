# FreshLatch

FreshLatch 的术语表。FreshLatch 把已签发主张从「曾经为真」改成「现在仍可复验」:过期、冲突、无 T1 原文支持的主张不得保持绿灯,人决定作废或续命。

## 主张与语料

**主张 (Claim)**:
一条已被签发过的陈述(如「专业版定价 299 元/席/月」),是复验的对象。
_Avoid_: 结论、论点、statement

**登记维度 (registered dimension)**:
主张签发时由签发人登记的维度标签(封闭枚举同 focus 六值),住在签发卷宗结构里,不注入复验模型上下文;是规则闸维度跨检的比对锚(ADR-0011)。签发时未登记的主张,stale 路径维度防线回落 Auditor 语义核对(ADR-0010 不变量 7)。
_Avoid_: 主张维度、维度标签

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

**evidence_id 时点格式**:
检索层返回的证据标识,格式 `doc_id#anchor@as_of`(如 `t0-competitor-notes#p2@T1`)。`@` 后缀标明快照时点;判 fresh/stale 引用的证据必须锚 T1。Lead 引用 evidence_id 必须逐字来自本会话 retrieve 返回(白名单校验),不得编造。
_Avoid_: 证据链接、出处编号

**Lead Reverifier (Lead)**:
真 Agent,自主规划复验:改写查询、按 `as_of=T0|T1` 换源、读原文、调 `reverify_claim` / `mark_stale` / `mark_gap`,并决定是否派驻 Critic / Auditor / Forensic。
_Avoid_: 主 agent、调查员

**Critic**:
真 Agent,只找「主张已死」的反证,不得强化「仍然成立」,不得放行。反证必须锚在主张的同一前提/度量维度(定价≠成本类维度混淆不得 mark_stale)。
_Avoid_: 反驳者、质疑器

**有效反证 (valid counter-evidence)**:
Critic 产出的、达到可验收质量的反证:引用 ≥1 个可点回的 `t1_evidence_ids`,且理由文本含显式因果句(指出 T1 原文哪一句推翻了主张的哪个前提),不得只写「与最新文档不符」类空话,不得以纯元陈述(未复测/不再列入跟踪等)为唯一依据。因果句必须锚在主张的同一前提/度量维度——维度不符(如定价≠成本)不构成有效反证。评测模式下加严判据(引用 span 与金标 causal_chain 对齐)归评估文档,不进本定义。
_Avoid_: 有力反驳、像样反证

**focus 维度**:
Lead 派驻 Critic 时给的反证搜索方向。封闭枚举 6 值,与语料金标维度同构:竞品价格 / 监管口径 / 访谈改口 / 成本模型 / 市场结构 / 技术生态。可选参数,省略 = 不限方向;调用边界硬校验,非法值拒绝并回列词表,重试计步。金标不记 focus(评测测判定,不测调度品味)。
_Avoid_: 聚焦、方向、视角

**Auditor**:
短循环 Agent,判定 `fresh` / `stale` / `unknown`;不得改主张正文,**不得拥有放行权**。形态 = 单轮 structured-output 判定(无工具无循环,输入主张+证据包;W5–W8 实装,#20 拍板确认)。
_Avoid_: 审核员、裁判

**双判一致 (dual-verdict consensus)**:
fresh 的唯一路径:Lead 与 Auditor 判定一致(全 fresh 才绿)。含 `stale` 落 stale、含 `unknown` 落 unknown 的落档真值表见 ADR-0009(单一真相,不复制)。Auditor 缺席不构成任何绿格。
_Avoid_: 双人复核、双重确认

**异议记录 (dissent)**:
Auditor 对 Lead 的 stale/unknown 判定给出的反对意见(结构化:Auditor 判定 + 理由 + 证据 id),挂在复验单该主张卡片下,随红/黄卡进 HumanLatch,是人审续命的合法输入之一。自由文本异议不进复验单。
_Avoid_: 异议备注、反对票

**Forensic (记忆刑侦)**:
真 Agent,只审本课题长期记忆:找死事实、互斥条目、无 `source_ref` 条目;不得改主张、不得放行、不得删除文件。

## 闸与人审

**规则闸 (Gate)**:
纯函数/Workflow 层,强制执行不变量:`stale` / `unknown` 不得绿灯、无 `t1_evidence_ids` 不得 `fresh`、checksum 对不上不得 fresh/续命、stale 必须携带可点回 T1 反证 id、stale 反证不得为纯元陈述、fresh 需双判一致(`auditor_verdict` 在场且非 dissent,ADR-0009)、stale 反证经 Auditor 维度核对异议时打回落 unknown + 异议记录(ADR-0010)、登记维度 ≠ 反证自标维度时机械跨检打回 unknown + 机械比对异议(`DIMENSION_CROSSCHECK_MISMATCH`,ADR-0011;两维任一缺失回落 Auditor 语义核对)。绿灯唯一出口。
_Avoid_: 校验器、检查器

**元陈述 (meta-statement)**:
T1 中关于测量/跟踪行为本身的陈述(未复测/不再列入跟踪项/无新数据/待发布/未入账),不承载关于主张对象的实质事实。元陈述是证据缺口,不是推翻:stale 理由以纯元陈述为唯一依据由规则闸打回(`META_ONLY_DISPROOF`)并落 `unknown`。标记词表封闭枚举,增补走评审工单。
_Avoid_: 状态说明、跟踪备注

**HumanLatch**:
人审工作流:人对每条红/黄灯主张点「作废」或「续命」(续命必须带 T1 evidence_id),并确认记忆隔离。Agent 不得自己把红灯改回绿灯。

**作废名单 (Invalidation List)**:
被人作废的主张 id 清单;进名单的主张重跑时不得再判 fresh。删除文件另闸,可先隔离不删盘。存储真相是 SQLite `invalidation_list` 表,随课题持久,与长期记忆的「已废 id」是同一份,不复制。
_Avoid_: 黑名单、封禁列表

**void（已作废）**:
被人工作废的主张终态,复验单上灰显。与 Auditor 判的 `stale` 并存不互斥:`stale` 是机器判定,`void` 是人的决定。作废后重跑不得再绿,由规则闸查作废名单强制。

**重跑 (Rerun)**:
人对某条作废主张发起的单主张复验:新开一个 LangGraph thread(`reverify-{claim_id}-{ts}`),只重跑该主张,结果作为时间线条目挂在该主张卡片下(如「重跑后仍红(第 N 次)」)。人点按钮触发,不自动。

**隔离 (Quarantine)**:
把腐烂记忆条目移出召回集的动作;人确认前不得移出,Agent 不得自动抹记忆。

## 评测

**假绿对照 (False-Green Control)**:
无工具基线:同模型不带工具只读 T0 摘要,应把已死主张判「成立」(假绿)。本产品必须红,对照成立才说明复验真在起作用。

**金标 (Gold)**:
人工标注的期望判定(dead / alive / must_stale 等),harness 据此打分;评测期联网代码级禁用,保住可复现性。

**语料污染位**:
语料中故意埋的陷阱(看似死其实活、看似活其实死、fresh 干扰项),防止评测靠表面线索作弊。

**复述测试 (blind restatement test)**:
定位红线的验收仪器:不给任何介绍,真人盲看 3 分钟界面后写一句话「这个产品是做什么的」,并回答探针「它和文档搜索工具有什么区别」。判定原话留档。W4 验收(不得被复述成「第二个 EvidenceOS」)与 W12 停止条件(两次纠正无效)共用此仪器。
_Avoid_: 盲测、用户测试
