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

**结构锚切块**:
语料按文档内显式锚(现行约定 `## pN`)切成可点回块;块的对外身份是 `evidence_id` 中的 anchor。本期不改用纯字数窗切块作为主契约。
_Avoid_: 滑窗切块(主契约)、token chunk(对外身份)

**快照取代 (snapshot supersession)**:
同一事实主题在 T0 仍成立、在 T1 已被改写或删除的跨快照关系;检索陷阱与后续腐烂叙事的「过期」若出现,本期特指此类,不是日历失效日。
_Avoid_: 过期(含糊)、expires_at、日历过期

**T1 来源三卡 (T1 Source Picker)**:
复验前用户显式选择 T1 ground truth 来源的合法入口。基线三卡(ADR-0016):上传 T1 语料包、粘贴变更要点(先成草稿,人点「确认入库」后才 ingest)、使用内置合成评测包(界面标明 synthetic)。**V1 增量**(ADR-0027):**薄 URL**——仅白名单域名(现行 `www.mckinsey.com`)单条抓取并落盘后再验;失败不入库,可回落粘贴确认。未选定合法 T1 来源不得假装已有最新事实。开放联网/多域爬取默认不做。
_Avoid_: T1 自动盯梢、联网默认同步、粘贴即入库、开放爬虫

**V1 垂直 · 顾问报告**:
近端唯一产品垂直:对已签发顾问/战略类主张做发前复验。样例主包为 McKinsey State of AI 公开洞察(T0≈2025-03 波 / T1≈2025-11 波);仓内只保留主张、摘录与出处,不把整本咨报当开源语料再分发(ADR-0027)。
_Avoid_: 多垂直并行、研报主包、合规主包(可另阶段)、用合成课题对外冒充已选垂直

**包结论 (disposition)**:
报告级聚合态,封闭三值:**可发** / **需补丁** / **勿发**。由主张级 `fresh`/`stale`/`unknown` 与人审收口聚合而成,是新层,不改名底层枚举。聚合边界见 ADR-0027。
_Avoid_: 通过/待改/拦截等第四套正式词、把 disposition 与单条 fresh 混称

**薄 URL (c′)**:
T1 合法入口之增量:白名单域名单条 URL → 抓取 → 落盘 → 再验。失败四态(非白名单、超时/网络、非文本或空正文、落盘前校验失败)均不入库。非开放搜索。
_Avoid_: 多源采编、自动盯梢、失败仍半写入库

**patch_events**:
改稿对照实验与产品审计共用的事件账;V1 起以 JSONL 落 `data/patch_events/`;C vs T 对照只后台/脚本记账,不进正式发前 UX(ADR-0027)。V1.5 正式确认事件须含 `before_text`/`after_text`(ADR-0029);未确认草案不入账。
_Avoid_: 发前 UI 上的实验臂开关、把未记账称作已开始论文实验、提案即写入正式账本

**Evidence-bound patch（attested patch）**:
引用 ⊆ 本 Run 已入库 T1 的整条主张正文替换;人确认才应用;确认后强制单条再验。产品路径恒 attested(`arm=T`);对外少用 proof-carrying(ADR-0029)。
_Avoid_: proof-carrying / PCC(对外主称)、无证自由改稿冒充 attested、首次带证据改稿

**propose_patch / confirm_patch**:
Verify+ 独立补丁 API:提案暂存与人确认应用。不是 HumanLatch 动词;不扩展 `discard`|`renew`(ADR-0029)。
_Avoid_: apply_patch 作人闩第三按钮、用 renew 顺带改正文

**Verify+**:
发前产品形:Gate + T1 入库 + 包结论 + Evidence-bound 补丁(人确认改稿) + 发前钩子(采用闸,ADR-0031)。薄对话留位未实装;Studio 冻结。形状关系:`Gate ⊂ Verify+ ⊂ Studio`。
_Avoid_: 把未做薄对话称作 Verify+ 已完备、Studio 已解冻、把入站 check 称作插件平台已交付

**发前钩子（publish hook）**:
导出/打包前的确定性采用闸:读发前 Run 的包结论与 T1 checksum/`run_id` 机械新鲜度,决定是否允许 Client Memo(及同闸出口)放出。本期硬出口=Memo UI+CLI + 入站 HTTP check;不是检索向量 embed,不在钩子路径强制整包再验(ADR-0031)。
_Avoid_: Embed(向量)、embedding 钩子、导出即自动 Lead 再跑、无闸导出、把 curl 冒烟称作 webhook 平台

**主张台账（claim ledger）**:
作废名单(`invalidation_list`)与续命人审日志(`latch_log` 的 discard/renew)的只读投影;挂复验单/Run 详情旁路并可导出 Markdown。不是新写表,不是 `patch_events`(ADR-0031)。
_Avoid_: claim_ledger 双写表、把补丁账当人审台账、第三套主导航「资产库」

**tenant_id**:
召回 ACL 上下文:块/文档所属合成租户标识;缺省 `default`。带 `tenant_id` 的 retrieve 只返回同租户块(ADR-0030)。不是多租户产品或 SSO。
_Avoid_: 租户管理面、RBAC 平台、把会话 evidence 白名单称作 ACL 已交付

**poison / untrusted**:
块级不可引用元数据标签。带此标签的块即使检索得分高也不得进入可引用证据集(ADR-0030)。
_Avoid_: 无标签内容启发式冒充投毒防护硬门、把 quarantine 记忆卫生等同投毒标签

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

**职人视图 / 审计视图**:
复验单同一界面的两种信息密度:职人视图是默认成交面;审计视图展开 Agent 轨迹与角色名,供排障与面试演示,不改变闸与人闩语义。
_Avoid_: 简单模式/专家模式、调试页

**客户向复验备忘 (Client Memo)**:
可转发附件形态的复验产出:课题问题句、生成时间、免责声明、三分栏(仍成立/已作废/缺口)、每条 claim_id 与一句话理由、可点回的 evidence_id(格式 `doc_id#anchor@as_of`,本批不做字符级偏移 span)。不含 Agent 轨迹、不含「建议进入/不进入」类商业裁决。与内部审计/复验单导出分离。
_Avoid_: 客户报告、复验 PDF、结论备忘录

**T1 来源三卡 (T1 Source Picker)**:
（词条正文见上文「主张与语料」节；含 V1 薄 URL 增量，ADR-0016 / ADR-0027。）

**主张导入稿 (Claim Import Draft)**:
职人用 Markdown/粘贴进入的主张清单约定格式:每条以 `## claim_id` 起头、其后正文一段;缺 id 时系统分配 `c-import-N`。只读已签发主张,不做新调查。JSON docket 为高级入口。
_Avoid_: 自由散文抽主张、一键 LLM 切分(首版不做)

**evidence_id 时点格式**:
检索层对外契约的命中主键,格式 `doc_id#anchor@as_of`(如 `t0-competitor-notes#p2@T1`)。`@` 后缀标明快照时点;判 fresh/stale 引用的证据必须锚 T1。Lead 引用 evidence_id 必须逐字来自本会话 retrieve 返回(白名单校验),不得编造。库内 `chunk_id` 仅存储实现细节,不进工具返回、轨迹与评测金标。
_Avoid_: 证据链接、出处编号、chunk_id(对外)

**快照过滤 (snapshot filter)**:
retrieve 按离散快照时点 `as_of ∈ {T0,T1}`(及可选 `source_type` / `doc_version`)收窄语料的过滤;不是日历生效/失效窗。日历时间窗不进本期检索契约。
_Avoid_: 时间窗(含糊)、effective_from、expires_at、日历过滤

**主张查询变换 (claim→query transform)**:
检索入口把主张(及可选登记维度/`focus` 封闭枚举映射)变成 retrieve 的 `query` 的确定性/可配变换;评测可对比变换前后召回。Lead/Critic 等角色不得自由改写检索串。
_Avoid_: Lead 改写查询、query rewrite(Agent 品味)、HyDE(未拍板前)

**Lead Reverifier (Lead)**:
真 Agent,自主规划复验:调用 retrieve(查询串由主张查询变换产出,Lead 不得自由改写检索串)、按 `as_of=T0|T1` 换源、读原文、调 `reverify_claim` / `mark_stale` / `mark_gap`,并决定是否派驻 Critic / Auditor / Forensic。
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
被维度异议打回后的恢复路径(ADR-0012; #239 教义优先序):①仍有推翻性 T1 证据时,按『原主张凭什么为真』重选**不同** dimension 再 `mark_stale`(勿重复刚被拒的维;登记维不披露;额度仍 1);②或回到 T1 检索与主张签发原文度量维度一致的支持证据,再走 `reverify_claim(fresh)` 过双判一致;③确无推翻性证据且无同维度覆盖 → 显式 unknown 收口——且仅在本会话维度预检打回之后已成功受理过一次 `reverify_claim(fresh)` 之后才允许该 unknown(ADR-0012 §2 收口次序)。每 Lead 会话每主张 mark_stale 维度打回额度 1 次(封死枚举探测),异议未清时 finish_reverify 机械拒绝。fresh 仍唯一经双判一致,本路径不引入任何放行或降门槛。
_Avoid_: 二次复验、重判

**Forensic (记忆刑侦)**:
真 Agent(中期形态)或确定性闩(本期执行体),只审本课题长期记忆:找死事实、互斥条目、无 `source_ref`/出处不存在的条目;不得改主张、不得放行、不得删除文件。dead 必须点回 T1;无 T1 不得标 dead。
_Avoid_: 记忆插件、Mem0、记忆体检产品

## 闸与人审

**规则闸 (Gate)**:
纯函数/Workflow 层,强制执行不变量:`stale` / `unknown` 不得绿灯、无 `t1_evidence_ids` 不得 `fresh`、checksum 对不上不得 fresh/续命(**Batch 2 半激活**,ADR-0017:renew 半边接线真 `checksum_fn`=语料现算 sha256且禁读库列,以确定性负例验收;fresh 半边仍**结构性空转**——不构造 `validity_basis`;不得升格为「checksum 已证明 latch」;盘点见 docs/research/checksum链激活契约.md,决议见 docs/research/β-checksum激活契约与空转设计评估.md)、stale 必须携带可点回 T1 反证 id、stale 反证不得为纯元陈述、fresh 需双判一致(`auditor_verdict` 在场且非 dissent,ADR-0009)、stale 反证经 Auditor 维度核对异议时打回落 unknown + 异议记录(ADR-0010)、登记维度 ≠ 反证自标维度时机械跨检打回 unknown + 机械比对异议(`DIMENSION_CROSSCHECK_MISMATCH`,ADR-0011;两维任一缺失回落 Auditor 语义核对;**受理层预检先行、闸层转兜底**,ADR-0012)、续命(renew)必须带 ≥1 个锚 T1 的 evidence_id(ADR-0006 §4;renew 是人审 L0 出口,不受双判一致约束)。绿灯唯一出口。
_Avoid_: 校验器、检查器

**Policy-as-code（thin · #8）**:
声明式禁区规则经 Verify+ **旁路**装入闸路径;命中则不得绿灯。不是 OPA/Cedar 政策平台,不是现有规则闸不变量正文本身(ADR-0032)。
_Avoid_: 政策引擎已交付、把禁区塞进并改写 rule_gate 不变量语义、完整 RBAC 策略面

**政策拒**:
因禁区规则命中而不得绿灯的拦截语义;与新鲜度拒、`must_stale`、元陈述拒、ACL/poison 拒 **分语义**(ADR-0032)。
_Avoid_: 与 stale/unknown 混称、把政策拒说成检索投毒已拦

**checksum 半激活 / 结构性空转**:
checksum 链按半边诚实登记启用态:已宣称激活的半边须接线且确定性负例打得响;未激活半边明示结构性空转,不得宣传全链已启用。套套逻辑(`checksum_fn` 读与 basis 同源库列)视为假激活。操作验收句在评估文档与 ADR-0017,不进本定义扩写。Batch 2 攻击面用例表(ATK-CS-*)见 docs/research/β-checksum攻击面用例集合设计评估.md。β+ 档 3a(ADR-0024):方向已锁为将来 list 同构全员受检,本批仍不构造 fresh `validity_basis`;单 doc 主证据激活已否;实装须另票预登记。评估见 docs/research/β+-档3a-fresh-validity_basis设计评估.md。β+ 档 3b(ADR-0025):跨轮腐烂重检方向已锁——复验入口与 UI 拉单双触发、同一 `check_basis`/`apply_rot`,不符→`unknown`+机械码;无 basis 的 fresh 不检;实装须另票。评估见 docs/research/β+-档3b-跨轮腐烂重检设计评估.md。
_Avoid_: checksum 已启用(含糊全称)、开关已打开、档3a已启用、跨轮重检已上线(决议未实装时)

**元陈述 (meta-statement)**:
T1 中关于测量/跟踪行为本身的陈述(未复测/不再列入跟踪项/无新数据/待发布/未入账),不承载关于主张对象的实质事实。元陈述是证据缺口,不是推翻:stale 理由以纯元陈述为唯一依据由规则闸打回(`META_ONLY_DISPROOF`)并落 `unknown`。标记词表封闭枚举,增补走评审工单。
_Avoid_: 状态说明、跟踪备注

**检索陷阱三类 (retrieve trap kinds)**:
供检索评测与后续 Agent 对抗共用的语料构造类别:快照取代、同快照冲突陈述、元陈述。不是主张金标 must_* 的别名;相关 evidence 须人工标进 retrieve 金标(主张金标可派生的除外)。
_Avoid_: 过期/冲突/元陈述包(路线图旧称「过期」须读作快照取代)

**HumanLatch**:
人审工作流:人对每条红/黄灯主张点「作废」或「续命」(续命必须带 T1 evidence_id),并确认记忆隔离。Agent 不得自己把红灯改回绿灯。续命生效链次序(Batch 2):格式→点回→闸(含 checksum)→仅绿后写 validity_basis;失败零写;`error_code`+短中文透传(见 docs/research/β-checksum与HumanLatch-renew交界设计评估.md)。跨轮腐烂重检(ADR-0025)不得自动 void、不得篡改人审 L0;机器仅可将带 basis 的 fresh 机械落 unknown。

**作废名单 (Invalidation List)**:
被人作废的主张 id 清单;进名单的主张重跑时不得再判 fresh。删除文件另闸,可先隔离不删盘。存储真相是 SQLite `invalidation_list` 表,随课题持久,与长期记忆的「已废 id」是同一份,不复制。
_Avoid_: 黑名单、封禁列表

**void（已作废）**:
被人工作废的主张终态,复验单上灰显。与 Auditor 判的 `stale` 并存不互斥:`stale` 是机器判定,`void` 是人的决定。作废后重跑不得再绿,由规则闸查作废名单强制。

**override（派生标签）**:
人审 `discard`/`renew` 落档时,相对落档前机器 `status` 是否构成对抗的布尔标记(非新 action)。谓词与 `latch_log` 扩列见 ADR-0023;禁止把 override 计数解释为「模型变好」,本批不锁 Override Rate 通过线。
_Avoid_: override 按钮、第三种人审动作、模型变好指标

**读法源 (How-to-Read source)**:
「如何读复验」的单一文案真相:身份(卖作废)/机器判定/人作废/边界(非法律·非自动)/验收诚实;投影至复验单旁路、Client Memo 附注与 ACCEPTANCE 可引用句(Batch 5 ε)。demo 可读 ≠ 付费或验证成功。
_Avoid_: 产品验证证书、法律意见书、自动决策说明

**重跑 (Rerun)**:
人对某条作废主张发起的单主张复验:新开一个 LangGraph thread(`reverify-{claim_id}-{ts}`),只重跑该主张,结果作为时间线条目挂在该主张卡片下(如「重跑后仍红(第 N 次)」)。人点按钮触发,不自动。

**隔离 (Quarantine)**:
把腐烂记忆条目移出召回集的动作;人确认前不得移出,Agent 不得自动抹记忆。

**死事实 / 互斥 / 不可核**(记忆层三标记):
操作定义在 `skills/memory_forensics/references/memory-schema.md`。dead 与复验 stale 同构但作用于记忆;互斥要两条 id;不可核 ≠ 假。checksum 对不上的 dead 半边本期留位未启用。
_Avoid_: 过时词匹配、记忆准确率

## 评测

**retrieve 子系统评测**:
与主张金标 `eval run --gold` **分轨**:入口为 `python -m freshlatch.eval retrieve`,产物在 `reports/retrieve-*.md`。I0 引用该轨数字时须遵守冒烟层预登记与 reports 为真相源(ADR-0026;`docs/accounting-card.md` / `docs/eval-retrieve.md`)。通过线与增益门正文在规格/评估文档,不在此扩写。
_Avoid_: 把 retrieve 冒烟表与主张金标混报、把冒烟写成统计证明

**Hard-Gold**:
retrieve **难金标**轨,与冒烟 `retrieve_gold` **分文件**(如 `retrieve_hard_gold`)。**骨架波**(I3)可跑分列报告但**不等于**已授权改 `PRODUCTION_RETRIEVAL_MODE`(ADR-0026 · ADR-0032)。
_Avoid_: 把 n=36 冒烟称作 Hard-Gold、骨架跑过即已换臂、与主张金标混报

**Hard-Gold 过线 / 改臂授权闸**:
在骨架之上的**决策闸**:须 dense 索引 + hard 臂对比 + I0 增益门(Hybrid 通过线于 hard 集成立)才**书面授权**开改臂**实现票**(Gate);不过线则冻 bm25。hard 评测库与 A0 **同库**=corpus+traps。本闸钉流程 ≠ 已换臂。2026-10-07 真人拍板 DECISION-16 的 16 条之后，生产默认是 `hybrid+rerank`；一键回退 `set_retrieval_switch("bm25")`。那次拍板不是全库逐行人工审核，也不是本闸本身。同日精排改为本地 `BAAI/bge-reranker-base`（只重排 top-10；见下条）。操作定义见 ADR-0033 与 `docs/research/Hard-Gold过线与改臂决议设计评估.md`;证据 `docs/evidence/hard-gold-arm/`、`docs/evidence/issue-284/DECISION-16.md`、`docs/evidence/neural-rerank/`。
_Avoid_: 无 dense 判过线、用主张金标/control-c 顶替、grill 直接改生产臂、把本闸称作已换 hybrid、臂对比缺 traps 仍判门

**生产精排**:
`hybrid+rerank` 的精排是本地 `BAAI/bge-reranker-base`（fastembed `TextCrossEncoder`，CPU），只重排 hybrid 已经给出的 top-10。依据是 #293 的 MRR@10 与 nDCG@10 提升。权重缺失或推理报错时打 warning，退回 `rerank_lexical`，记 `last_rerank_mode=lexical_fallback`。切回词重叠：`set_retrieval_switch("hybrid+rerank_lexical")`。一键回退 BM25：`set_retrieval_switch("bm25")`。金标口径不变，人工只审过 DECISION-16 的 16 题。
_Avoid_: 把 K=30 送进 cross-encoder、失败时静默仍标成神经精排、把这次切换说成全库人工 gold

**I1 失败复盘（评测标签）**:
答辩/冒烟用语,不是生产 Gate 或 disposition 枚举。桶名(找不到/找错/没用上)与漏拦/误拦的操作定义、corpus 路径见 ADR-0028 与 `docs/research/I1-失败三分法与HumanLatch语料设计评估.md`;语料落 `docs/evidence/i1/`。
_Avoid_: 把三分法写成生产 status、无轨迹编造样本、远程 V1 关单冒充本地 Exit 后宣称 I1 完成

**I2 安全三例（评测/答辩）**:
面试安全轮冒烟用语,不是安全认证或生产枚举。三例=越权召回 / 间接注入 / 检索投毒;操作定义与 Exit 分层见 ADR-0030 与 `docs/research/I2-安全三例设计评估.md`;证据落 `docs/evidence/i2/` 与 `docs/security.md`。idea #4 过期伪装不计入本 Exit。
_Avoid_: 安全平台已交付、用 #4 顶替 I2、单次 LLM 报安全通过率

**假绿对照 (False-Green Control)**:
无工具基线:同模型不带工具只读 T0 摘要,应把已死主张判「成立」(假绿)。本产品必须红,对照成立才说明复验真在起作用。

**判定拉齐预登记 (γ / C3)**:
Batch 3 判据与「禁改 gold 凑绿」操作化的单一真相在 `docs/research/C3-判定拉齐预登记卡.md`(ADR-0018)。通过线/加严句不在此扩写;γ 通过 ≠ 假绿对照成立。消融/多 seed 本批仅锁规格、实跑未做(未跑 ≠ 已证明;见 docs/research/γ-消融表与多seed规格时序设计评估.md)。假绿仪器与 γ/消融须分条引用、禁互相顶替(见 docs/research/γ-与假绿仪器分条措辞设计评估.md)。
_Avoid_: 改金标凑绿、把 smoke 当统计证明、未跑称作已证明、γ 通过称作假绿已根治

**金标 (Gold)**:
人工标注的期望判定(dead / alive / must_stale 等),harness 据此打分;评测期联网代码级禁用,保住可复现性。

**语料污染位**:
语料中故意埋的陷阱(看似死其实活、看似活其实死、fresh 干扰项),防止评测靠表面线索作弊。

**复述测试 (blind restatement test)**:
定位红线的验收仪器:不给任何介绍,真人盲看 3 分钟界面后写一句话「这个产品是做什么的」,并回答探针「它和文档搜索工具有什么区别」。判定原话留档。W4 验收(不得被复述成「第二个 EvidenceOS」)与 W12 停止条件(两次纠正无效)共用此仪器。
_Avoid_: 盲测、用户测试

**第二课题包 (second-thesis pack)**:
FreshLatch 内与第一课题同构的另一份合成课题(平行问题句、T0/T1 语料、平行 gold 子集),走同一导入→T1 三卡→复验单→作废/续命→客户备忘旅程,不改主课题闸与词表语义。Batch 4 本批唯一包为报价保质期薄切片(QuoteTTL 薄,claim 级);不是独立 QuoteTTL 产品表面,不是只改问题句的换皮。候选池、backlog 序与另图备选的单一真相在 `docs/research/δ-第二课题选题设计评估.md`(ADR-0019),不在此复制整表。
_Avoid_: 第二产品线、多垂类已验证、QuoteTTL 产品(本包)

**软 Port (soft Port)**:
第二课题包迁移的诚实口径:闸不变量、主张字段集、gold 键形状、SQLite 表结构、HumanLatch、职人旅程、六维枚举为零改冻结面;允许平行数据包、配置切换与只读装载器;claim_id 必须命名隔离,每包独立 DB 文件允许。加列/加键/改闸/新主 CTA/扩第七维等由证伪探针判定失败(ADR-0020)。不是「src 字面零 diff」。
_Avoid_: 硬零改、零改代码(含糊)、已多垂类 Port

**合成数据释放草稿 (C4)**:
合成评测材料(语料/gold/平行课题包)对外分发前的规矩预锁文档;必须标明 synthetic;许可在草稿阶段可为占位。文档落盘不等于数据集已对外可用;已释放须满足 C4 卡门闩(ADR-0021)。不是产品功能说明书,不管闸与 Agent 实现。
_Avoid_: 已开源数据集、数据已释放(仅因 C4 存在)、多垂类数据集已发布

**对抗套件目录 (Adversarial Catalog)**:
假绿/对抗用例的版本化索引(`docs/research/adversarial/`,`catalog_version` semver,条目 `ATK-<FAMILY>-NN`)。Batch 5 仅为骨架(ADR-0022);目录存在 ≠ 仪器已过;禁报统计通过率、禁 pass_rate 列;与金标/预登记/ATK-CS 只指针。
_Avoid_: 对抗已通过证书、套件通过率表(本批)、仪器已过(仅因目录有行)

**patch_events 平行轨**:
与冲甲主链（路线 B / #431）完全平行的对照设计探针轨：检验更干净、可识别的比较能否露出 T 相对 B1/B2 差异并更适产品叙事。成功 ≠ 甲成立。实现只许旁路（`compare_alt_*`、`docs/evidence/patch-events-alt/`）或只读复用旧 jsonl/夹具；对主 `compare_primary` 与冲甲预注册正文零 diff。操作定义见 ADR-0035 与 `docs/research/patch_events-平行轨可识别对照设计评估.md`。
_Avoid_: 改主 compare_primary 追甲、本轨数字填主 RESULT、称探针为甲、回写旧 PREREG、复活路线 A

**同文四闸**:
平行轨探针主结构：先锁定一份共享 `after_text`，再让 C/T/B1′/B2 只做闸判（比闸不比改写器）。分头四臂生成不是本轨主结构。
_Avoid_: 把同文四闸写进冲甲主预注册当作已激活主仪器、用同文夹具差填冲甲成立格

**B1′（真事后核验对照）**:
平行轨中的收紧 B1：禁止看 evidence id / 绑定；同文锁定后才延迟获得 evidence 正文核验；拒绝不得记成 T。用于避免现行 B1 与 T 信息集过近而成假对照。
_Avoid_: 让 B1′ 看 binding id、把 B1′ 拒绝记成 T、把收紧写成削弱对照凑差

**平行轨升级闸**:
探针结果三档预锁：可分开（允许另开主论文级新预注册文件，不取代冲甲页）/ 分不开（不升级，写技术报告）/ 不值得升级（放弃旁路主论文预注册）。可分开 ≠ 甲。见结果后改闸作废。
_Avoid_: 可分开称作甲成立、见阴性后放宽升级闸、升级时反写主 compare_primary
