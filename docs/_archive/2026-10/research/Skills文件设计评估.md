# Skills 文件内容设计评估

> 工单:[Skills 文件内容设计(reverify / devil_advocate / freshness_audit)](https://github.com/luxingjiang1993/FreshLatch/issues/10)
> 日期:2026-09-20 · 状态:已拍板(本文供实施参照与面试讲解)
> 配套:工单 #6(三层分离与角色白名单)、#14(focus 词表,本工单消费)、#9(双 gate 测试,单测落位)

---

## 1. 问题:我们要做什么决策

FreshLatch 四个角色(Lead / Critic / Auditor / Forensic)各有一份 Skill 文件,本工单回答:**这四份文件写什么、怎么组织、与代码的边界在哪**。具体五个子问题:

1. frontmatter 与正文结构:§14–16 课的渐进式披露机制怎么用在 skill 文件里;
2. 纪律条款怎么写成可执行约束:「不得用记忆补原文」「无 T1 原文不得判 fresh」「Critic 只找已死,不得强化原主张」「fresh/stale/unknown 口径」;
3. skill 文件与工具表白名单的关系:纪律在提示词层兜底还是代码层强制,怎么避免「双重真相」;
4. `spawn_critic(focus)` 的 focus 参数语义在 Critic 侧怎么呈现;
5. 【本期范围】memory_forensics.md 只留纪律骨架,实现留 W9–W12。

## 2. 决策的出发点:已拍板原则框死的答案空间

本工单的答案空间被两个已拍板决议大幅收窄, grilling 从确认边界开始而非自由发挥:

- **#6 的三层分离**:「prompt 管任务、白名单管禁止、规则闸管放行」。skill 文件在 prompt 层,它的天花板被钉死——**禁止事项的第一道防线永远在代码**,skill 只能做任务方法与教义。
- **#14 对「提示词层软约束」的明确弃用**:focus 词表案的决策三把「在 prompt 里告诉模型只能填这 6 个」否掉了,理由与 #6 同构——提示词约束可被稀释,参数校验是数学事实。本工单的纪律条款写法直接从这条否决长出来:**skill 里不写「你不许」式禁令清单**。

因此本工单的核心决策只剩一个:**prompt 层与代码层的「单一事实来源」怎么切分**——哪些内容以代码为真相、skill 只是投影,哪些内容 skill 就是真相本身(任务方法没有代码副本可漂移)。

## 3. 决策与拍板

### 决策一:装载形态——全套披露 vs 半套披露 vs 纯内嵌

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **半套披露 ✅** | 保留 frontmatter + 正文 + references/ 三层;spawn 时 Runner 整份读入正文,references 由循环内读文件工具按需加载;description 语义改为「Runner 何时为哪个角色加载」 | 第 15 课机制②原样落地;白赚 check_a_skill 的 frontmatter 校验规则;长材料不进常驻上下文,省 token | 机制①(模型自选 skill)被代码 spawn 取代,目录扫描对本期是死代码——但保留形状不亏,check 工具与未来扩展都认这个形状 |
| 全套披露 | Lead 循环也能通过工具发现并加载 skill | 与课程示例完全同构 | 角色是封闭集合(4 个),「发现」机制本期零调用;多开一个模型读提示词的通道,注入面变大 |
| 纯内嵌 | 不要 frontmatter,内容写进角色 prompt 常量 | 最简,少一层文件 | 放弃 check_a_skill 兼容;没有 references/ 按需披露,长材料要么全塞上下文要么没有 |

**拍板:半套披露。** FreshLatch 没有「模型从目录挑角色」的环节——四个角色是封闭集合,由 Runner/Lead 在代码里 spawn(ADR-0004),第 15 课机制①的「决策卡」在本项目的对应物就是 spawn 逻辑本身。机制②(正文先读、references 按需)原样保留,这是渐进式披露真正省 token 的那一半。frontmatter 照 Anthropic 规范写,name/description 规则白赚第 17 课校验器的既有规则集。

### 决策二:纪律条款写法——禁令照抄 vs 教义层 vs 不写

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **教义层 ✅** | 每条纪律写成「存在这条约束(代码强制)+ 为什么 + 被拦后的正确动作」;不写「你不许」式清单 | 单一事实来源不破:禁令的枚举真相只在代码,skill 无可漂移的禁令副本;模型被闸拦下有解释、有纠正路径,重试效率最高 | 需要克制——作者容易顺手把禁令写全,回漂成 (b) |
| 禁令照抄 | 四条纪律原文进 skill | 看着周全 | 正是工单点名的「双重真相」:代码改了纪律、skill 没跟上,模型读到过时禁令;两处维护 |
| 完全不写 | skill 只写任务方法 | 零漂移风险 | 模型被拦下时无解释无指引,重试靠模型猜,最贵 |

**拍板:教义层。** 三条边界:① 禁令的唯一枚举真相在代码(白名单常量 + 规则闸),skill 复述禁令的**存在与理由**而非**条目**;② 唯一例外是 focus 6 值词表进 `devil_advocate.md/references/focus-dimensions.md`——#14 已拍板错误信息回列词表给 Lead,Critic 侧列出自己认识的合法方向有助于理解任务,且词表一致性由 #14 已立的「代码常量 + 单测」钉死,skill 里的列表只是被测对象;③ 「拦截 → 纠正」写成显式对照表进正文(场景 → 原因 → 正确动作),每条注明「以代码返回的错误信息为准」——表是纠正路径的导航,不是错误文案的复制,单测只断言映射存在、不断言文案。

### 决策三:skill ↔ 代码一致性靠什么钉死

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **单测钉死 ✅** | tests/unit 设「skill 一致性测试」:frontmatter 规则 + 工具名 ⊆ 白名单 + focus 词表一致 + 对照表映射存在 | 把「一致」从约定变成数学事实,与 ADR-0001「禁止事项必须能在代码结构上被看见」同构;与 #14 词表一致性单测同构,模式复用 | 一个测试文件的成本 |
| 人工 code review | 靠人眼看 | 零代码 | 提示词资产无类型系统,漂移风险最大处恰恰最没人盯 |

**拍板:单测钉死,四条断言**:
1. frontmatter 规则——吸收第 17 课 check_a_skill 的校验规则(name ≤64 小写连字符、description ≤1024、无 XML 标签、name=目录名、metadata ~100 词、正文 ≤500 行),**纯 Python 重写,不引入 check_a_skill 工具链**(它依赖 Agently,ADR-0004 已弃);
2. skill 正文 + references 出现的工具名 ⊆ 该角色白名单代码常量(ADR-0004 四表的直接延伸);
3. `focus-dimensions.md` 的 6 值 == `FOCUS_DIMENSIONS` 代码常量(#14 决议延伸);
4. 拦截→纠正对照表只断言「场景→动作」映射存在,不断言错误文案(文案唯一真相在代码)。

### 决策四:Auditor 的形态——单轮判定 SOP vs 迷你循环

切片 §7 写 Auditor 是「短循环 Agent」,ADR-0004 拍板「Auditor 仅 verdict 出口、深度恒 1、最多 6 步」。深度恒 1 意味着**没有工具调用循环**。

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **单轮判定 SOP ✅** | Auditor = 一次 structured-output 调用:输入主张 + 证据包,输出 verdict ∈ fresh/stale/unknown + 理由;freshness_audit.md 是这次调用的 system prompt | 判定完全可复现(同证据包同判定,金标友好);「不得拥有放行权」物理成立(它连检索都没有,无法自造证据);实现最简 | Auditor  blind——证据包质量完全取决于 Lead/Critic,Lead 偷懒时 Auditor 无反制 |
| 迷你循环 | Auditor 有 2–3 步 retrieve/read | 能自己补证据,抗 Lead 偷懒 | 违反 ADR-0004「深度恒 1」; Auditor 能检索 = 能自造证据,放行权约束变复杂;判定不再可复现 |

**拍板:单轮判定 SOP,且不留「本期/后期」摇摆。** ADR-0004 已把深度钉死为 1;若 W5–W8 想给 Auditor 眼睛,那是推翻 #6 的新工单,本决议不开暗门。附带拍板:**判定口径的单一真相放 `freshness_audit.md/references/verdict-rubric.md`**(三档定义、无 t1_evidence_ids → 只能 unknown、干扰项正反例);Lead 侧 `reverify.md/references/verdict-basis.md` 只写 evidence_id 规范并指向 Auditor 口径——同一份口径两份拷贝必然漂移。

### 决策五:memory_forensics.md 骨架的「满」度

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **完整纪律版 ✅** | 与其余三份同规格写满(frontmatter/任务/工作流/教义/references);差别只在 Runner 不挂载 spawn_forensic、Lead 白名单不含它 | 切片 §9 已给出纪律原文,写满的成本只是现在写 vs 将来写;W9–W12 的实现成本在代码(spawn/flag_*/quarantine 状态机)不在提示词,现在写满等于免费;与「白名单 fail-closed」自洽——文件在磁盘上不构成暴露面,真正的大门是白名单 | 文件存在但本期不可达,新读者可能困惑(由 frontmatter description 写清「W9–W12 起由 Runner 加载」解决) |
| 占位版 | frontmatter + 一句话 | 零误导 | W9–W12 要回头补写,那时上下文已换,重写质量低于现在 |
| 不建文件 | 本期没这个角色 | 最干净 | 违背切片 §9 的文件清单;W9 从零写 |

**拍板:完整纪律版**,frontmatter description 明示加载时点。

### 决策六:位置与语言

| 选项 | 位置 | 语言 |
|---|---|---|
| **拍板 ✅** | 仓库根 `skills/<slug>/SKILL.md` + `references/`(提示词资产,非 Python 包,src 零提示词依赖;与课程工具链和 check_a_skill 默认形状对齐) | `name` 英文 slug(校验硬规则);description 与正文全中文(项目语言纪律,qwen 中文无损) |
| 备选 | `src/freshlatch/skills/`(跟着包走) | 全英文(对齐 Anthropic 生态惯例) |

### 决策七:语义质量保障——LLM 评审 vs 人审

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **人审兜底 ✅** | 四份 skill 内容被本工单 Q7–Q9 决议锁死,写完由项目主人审;不引入 skill-semantic-review | 本期 4 份文件、内容已被决议锁死,LLM 评审增量信息小;不引入「评审模型读提示词」的注入面与成本 | 无自动化语义把关,质量依赖决议粒度——本决议的逐节大纲即补偿 |
| 引入 skill-semantic-review | LLM 评审进评测 harness | 自动化 | 与 (a) 的优势重复;评审模型自身输出无金标 |

## 4. 四份文件规格总表(实施直接照此写)

统一节骨架:`# 角色名`(一段话:谁、被谁 spawn、输出去向)→ `## 任务` → `## 工作流` → `## 教义:约束与纠正` → `## 何时读 references`。

| Skill | 输入 | 形态 | references/ | 拦截→纠正对照表要点 |
|---|---|---|---|---|
| `reverify.md` (Lead) | 主张列表、作废/隔离名单 | 循环 ≤18 步 | `verdict-basis.md`(evidence_id 规范,口径指向 Auditor)、`rerun-rules.md`(名单约束、续命须新 T1 evidence_id) | 无 t1_evidence_ids 不得 fresh → mark_gap 或判 unknown;focus 非法值 → 按错误信息重试(计步);主张在作废名单 → 不得重判 |
| `devil_advocate.md` (Critic) | 主张 + focus + 已找到证据 id | 循环 ≤8 步,只找已死反证 | `focus-dimensions.md`(6 值词表,单测钉死)、`counterevidence-quality.md`(锚 T1 id+checksum、真冲突 vs 口径变化、干扰项) | 试图强化原主张/放行 → 无此工具,回到找反证 |
| `freshness_audit.md` (Auditor) | 主张 + 证据包 | **单轮判定 SOP**,无工具 | `verdict-rubric.md`(**判定口径单一真相**:三档定义、无 t1_evidence_ids → 只能 unknown、干扰项正反例、理由须引证据 id) | 证据包不足 → 只能 unknown,不得猜 |
| `memory_forensics.md` (Forensic) | 记忆条目召回集 | 循环 ≤8 步;**本期 Runner 不挂载** | `memory-schema.md`(条目字段、dead/contradictory/unverified 操作定义) | 试图改主张/删除/放行 → 无此工具,只能 flag_* / propose_quarantine |

## 5. 手段登记册

### 5.1 提示词层手段

| 手段 | 一句话原理 | 优势 | 代价/风险 | 本期处置 |
|---|---|---|---|---|
| 教义层纪律写法 | skill 写约束的存在+理由+纠正动作,不写禁令条目 | 单一真相不破;被拦有纠正路径 | 需要写作克制 | 【实装】 |
| 拦截→纠正对照表 | 场景→原因→正确动作的显式导航表 | 自我纠正路径最清晰,演示好看 | 与规则闸文案漂移风险 | 【实装】注明「以代码错误信息为准」,单测只断映射存在 |
| 禁令照抄进 skill | 纪律原文复述 | 周全感 | 双重真相 | 【弃】#6/#14 已否 |
| 提示词软约束(只填这 6 个) | 自然语言劝说 | 零代码 | 可被稀释 | 【弃】#14 决策三已否 |
| 近义词容错映射 | 打错自动纠正 | 顺滑 | 第二个真相来源 | 【弃】#14 已否 |

### 5.2 一致性手段

| 手段 | 一句话原理 | 优势 | 代价/风险 | 本期处置 |
|---|---|---|---|---|
| skill 一致性单测(4 断言) | frontmatter/工具名/focus 词表/对照表映射进 tests/unit | 一致从约定变数学事实 | 一个测试文件 | 【实装】 |
| check_a_skill 规则吸收重写 | 借第 17 课规则,纯 Python 自写 | 白赚成熟规则集,不引 Agently | 重写一次 | 【实装】 |
| check_a_skill 原样引入 | 七环节真实跑链路 | 全自动 | 依赖 Agently,违反 ADR-0004;与 #9 评测 harness 范围重复 | 【弃】 |
| skill-semantic-review | LLM 评审语义质量 | 自动化把关 | 注入面 + 成本,增量小 | 【弃】本期人审兜底,W5–W8 需要再立工单 |
| CONTEXT.md 收 skill 术语 | 词表收「Skill 文件/教义层」 | 领域语言完整 | 工程概念混进领域词表,违反 CONTEXT.md 纪律 | 【弃】 |

### 5.3 结构性手段

| 手段 | 一句话原理 | 优势 | 代价/风险 | 本期处置 |
|---|---|---|---|---|
| 半套渐进式披露 | frontmatter+正文+references/,机制①由 spawn 取代 | 省 token 的那一半保留 | 目录扫描本期是死代码 | 【实装】 |
| 单轮判定 SOP(Auditor) | 深度恒 1,给证据包不给工具 | 判定可复现;放行权物理成立 | Auditor blind,依赖 Lead 证据质量 | 【实装】推翻须新工单 |
| 口径单一真相在 Auditor | 判定 rubric 只存一份 | 防两份拷贝漂移 | Lead 侧引用多一跳 | 【实装】 |
| memory_forensics 完整纪律版 | 文件写满,Runner 不挂载 | W9–W12 提示词零成本 | 本期不可达文件存在 | 【实装】 |
| 仓库根 skills/ | 提示词资产与 Python 包分离 | src 零提示词依赖;课程工具链兼容 | 根目录多一层 | 【实装】 |
| Auditor 迷你循环(备选) | 给 Auditor 2–3 步检索 | 抗 Lead 偷懒 | 违反 ADR-0004;可复现性受损 | 【弃】 |

## 6. 与既有决议的关系

- **消费 #6**:三层分离的 prompt 层落地;白名单四表的 skill 侧投影由单测钉死。
- **消费 #14**:focus 词表进 Critic reference,一致性断言是 #14 单测的延伸。
- **被 #9 承载**:四条单测断言落 tests/unit(双 gate 的 unit 侧)。
- **为 W9–W12 预留**:memory_forensics.md 写满不挂载,W9 开工即写代码不写提示词。
