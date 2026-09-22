# FreshLatch

FreshLatch 的术语表。FreshLatch 把已签发主张从「曾经为真」改成「现在仍可复验」:过期、冲突、无 T1 原文支持的主张不得保持绿灯,人决定作废或续命。

## 主张与语料

**主张 (Claim)**:
一条已被签发过的陈述(如「专业版定价 299 元/席/月」),是复验的对象。
_Avoid_: 结论、论点、statement

**登记维度 (registered dimension)**:
主张签发时由签发人登记的维度标签(封闭枚举同 focus 六值),住在签发卷宗结构里,不注入复验模型上下文;是规则闸维度跨检的比对锚(ADR-0011)。签发时未登记的主张,stale 路径维度防线回落 Auditor 语义核对(ADR-0010 不变量 7)。
六枚举的统一语义 = 主张前提的证据出处类型,不是主题词:competitor_pricing 竞品定价数据 / regulatory_stance 监管口径 / interview_reversal 访谈·纪要·口头口径(机制维度,无论内容谈的是定价、成本还是监管) / cost_model 成本测算 / market_structure 市场格局 / tech_ecosystem 技术生态。判法:问「原主张凭什么为真?」——答所依赖的证据类型即维度(#31)。
_Avoid_: 主张维度、维度标签

**T0 / T1 语料**:
T0 是主张签发时的原始文档快照;T1 是复验时刻的新文档快照。判定以 T1 原文为 ground truth。
_Avoid_: 旧库/新库、源数据/目标数据

**T1 来源三卡 (T1 Source Picker)**:
复验前用户显式选择 T1 ground truth 来源的三种合法入口:上传 T1 语料包、粘贴变更要点(先成草稿,人点「确认入库」后才 ingest)、使用内置合成评测包(界面标明 synthetic)。未选定合法 T1 来源不得假装已有最新事实。联网插座若存在则默认关,不进 Batch 1 主路径(ADR-0016)。
_Avoid_: T1 自动盯梢、联网默认同步、粘贴即入库

**must_stale**:
金标中必须被判定为 stale 的主张,任何 harness 不得对其放行,用于锁住评测可复现性。

**must_fresh**:
金标中必须被判定为 fresh 的主张;含「看似已死其实 fresh」干扰项,防止全红假象。

**must_unknown**:
金标中 T1 无原文覆盖、必须判 unknown 的主张;锁住「无 `t1_evidence_ids` 不得 fresh」这条闸的评测。

**must_quarantine**:
金标中必须被提议移出下一轮记忆侧召回的 `memory_id`(死事实、互斥对、不可核)。人确认前磁盘条目不删除。构造规则与通过线在评估文档,不进本词表。
_Avoid_: 记忆准确率、隔离率

## 复验主链

**复验单 (Reverify Sheet)**:
一次复验的主界面与产出物:每条主张的原文点回、判定、理由、人审动作。不是聊天框。默认「职人视图」只用主张状态与人动作语言;同一页可切到「审计视图」才显示 Lead/Critic/轨迹等工程角色信息。
_Avoid_: 报告、看板

**客户向复验备忘 (Client Memo)**:
可转发附件形态的复验产出:课题问题句、生成时间、免责声明、三分栏(仍成立/已作废/缺口)、每条 claim_id 与一句话理由、可点回的 evidence_id(格式 `doc_id#anchor@as_of`,本批不做字符级偏移 span)。不含 Agent 轨迹、不含「建议进入/不进入」类商业裁决。与内部审计/复验单导出分离。
_Avoid_: 客户报告、复验 PDF、结论备忘录

**主张导入稿 (Claim Import Draft)**:
职人用 Markdown/粘贴进入的主张清单约定格式:每条以 `## claim_id` 起头、其后正文一段;缺 id 时系统分配 `c-import-N`。只读已签发主张,不做新调查。JSON docket 为高级入口。
_Avoid_: 自由散文抽主张、一键 LLM 切分(首版不做)

**职人视图 / 审计视图**:
复验单同一界面的两种信息密度:职人视图是默认成交面;审计视图展开 Agent 轨迹与角色名,供排障与面试演示,不改变闸与人闩语义。
_Avoid_: 简单模式/专家模式、调试页

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
对 Lead 的 stale 判定给出的反对意见(结构化:kind + Auditor 判定/机械事实 + 理由 + 证据 id),挂在复验单该主张卡片下,随红/黄卡进 HumanLatch,是人审续命的合法输入之一。kind 三分:auditor_semantic(Auditor 语义异议,ADR-0010 不变量 7)/ mechanical_crosscheck(闸层机械跨检,ADR-0011 不变量 8)/ mechanical_precheck(mark_stale 受理层预检,ADR-0012)。自由文本异议不进复验单;跨轮注入复验上下文只注 kind 通用文案,机械异议原文含登记维度值不得原样注入(ADR-0012)。
_Avoid_: 异议备注、反对票

**同维度复验 (same-dimension reverify)**:
被维度异议打回后的恢复路径:Lead 回到 T1 检索与主张签发原文度量维度一致的证据,再走 reverify_claim(fresh) 过双判一致;无同维度覆盖则显式 unknown 收口——且仅在本会话维度预检打回之后已成功受理过一次 reverify_claim(fresh) 之后才允许该 unknown(ADR-0012 §2 收口次序)。每 Lead 会话每主张 mark_stale 维度打回额度 1 次(封死枚举探测),异议未清时 finish_reverify 机械拒绝。fresh 仍唯一经双判一致,本路径不引入任何放行或降门槛。
_Avoid_: 二次复验、重判

**Forensic (记忆刑侦)**:
真 Agent(中期形态)或确定性闩(本期执行体),只审本课题长期记忆:找死事实、互斥条目、无 `source_ref`/出处不存在的条目;不得改主张、不得放行、不得删除文件。dead 必须点回 T1;无 T1 不得标 dead。
_Avoid_: 记忆插件、Mem0、记忆体检产品

## 闸与人审

**规则闸 (Gate)**:
纯函数/Workflow 层,强制执行不变量:`stale` / `unknown` 不得绿灯、无 `t1_evidence_ids` 不得 `fresh`、checksum 对不上不得 fresh/续命(本期**留位未启用**:语料 checksum 全空、store 无读口、fresh 路径不构造 `validity_basis` 故该半边结构性空转;激活契约与「checksum_fn 不得读同一个库列」的套套逻辑陷阱见 docs/research/checksum链激活契约.md)、stale 必须携带可点回 T1 反证 id、stale 反证不得为纯元陈述、fresh 需双判一致(`auditor_verdict` 在场且非 dissent,ADR-0009)、stale 反证经 Auditor 维度核对异议时打回落 unknown + 异议记录(ADR-0010)、登记维度 ≠ 反证自标维度时机械跨检打回 unknown + 机械比对异议(`DIMENSION_CROSSCHECK_MISMATCH`,ADR-0011;两维任一缺失回落 Auditor 语义核对;**受理层预检先行、闸层转兜底**,ADR-0012)、续命(renew)必须带 ≥1 个锚 T1 的 evidence_id(ADR-0006 §4;renew 是人审 L0 出口,不受双判一致约束)。绿灯唯一出口。
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

**死事实 / 互斥 / 不可核**(记忆层三标记):
操作定义在 `skills/memory_forensics/references/memory-schema.md`。dead 与复验 stale 同构但作用于记忆;互斥要两条 id;不可核 ≠ 假。checksum 对不上的 dead 半边本期留位未启用。
_Avoid_: 过时词匹配、记忆准确率

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
