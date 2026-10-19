# MemoryForensics 操作定义对齐与论文路径设计评估

> **决议日期**: 2026-09-21
> **触发**: 对 `docs/research/memory-forensics-heuristic-algorithms-analysis.md` 的事实核查;用户要求按 Anthropic 评测纪律给出现状评估、修正与短中长期行动,目标是模块质量本身达到可发表,而不是先写一篇包装文。
> **格式基准**: 《HumanLatch闭环设计评估.md》《Agent循环实现选型评估.md》
> **相关**: 立项切片 §11、`skills/memory_forensics/references/memory-schema.md`、ADR-0013、ADR-0014

---

## 1. 问题:我们要做什么决策

MemoryForensics 已经有表、工具名和一条启发式流水线,但与产品操作定义不对齐,文档把 demo 写成了测量结论,并把词表规则包装成高创新算法。要一次拍板五件事:

1. **现状分层**:哪些已实装、哪些只是演示、哪些是文档假绿。
2. **检测器立刻怎么改**:继续堆关键词,还是把判据锁回 schema(T1 冲突 / 同对象互斥 / 无源或源不存在)。
3. **评测何时填 `must_quarantine`**:本提交一起填,还是先锁构造规则、另提交再填(防 HARKing)。
4. **Lead 何时挂 W9 白名单**:现在挂进复验主链,还是与 `must_stale` 评测隔离。
5. **论文路径**:发什么、不发什么、先做哪层测量。创新点是产品闩的质量,不是另写一篇「AI 沦为」。

## 2. 前置约束:哪些答案已被钉死

| 前置 | 来源 | 对本决议的锁死作用 |
|---|---|---|
| 只审本课题长期记忆,不卖记忆库,不接 Mem0,不做主界面 | 立项切片 §11、§14 | 论文叙事不得写成 memory product;对照基线可以引用 Mem0,产品不得变成 Mem0 适配器 |
| 三类发现:dead / contradictory / unverified | 切片 §11.1、memory-schema | 检测器必须执行这三条操作定义,不能用时效词冒充 dead |
| dead = 与当前 T1 原文冲突,或 checksum 对不上;checksum 半边本期留位未启用 | 切片 §11.1、CONTEXT 规则闸条 | 不得实现或宣传 checksum-dead;无 T1 不得标 dead |
| unverified = 无 `source_ref` 或出处已不存在;不可核 ≠ 假 | memory-schema | 字段真值判断只覆盖定义前半;后半要查文档是否存在 |
| contradictory = 同维度不可并存,需两条 id 一起记录 | memory-schema;切片例子是相对关系互斥 | 竞品A价 vs 竞品B价不是互斥 |
| 隔离=移出召回,人确认前不移出,Agent 不得删除 | 切片 §11.2、CONTEXT 隔离 | 论文贡献若存在,是 fail-closed latch + 人审,不是自动抹记忆 |
| Forensic 真 Agent,可 `retrieve(as_of=T1)` / `read_source`;深度恒 1;不得改主张 | 切片 §11.2、skill 文件 | 确定性闩可以是基线;不得把闩宣传成已在跑的 ReAct Agent |
| Demo 8–12 条;金标 2 dead + 1 对互斥 + 2 unverified;其余可召回 | 切片 §11.3 | 对照条目不得被「全隔离」假绿吃掉 |
| `must_quarantine` 在 `gold.json` 占位为空;W1–W4 单测锁空数组 | `data/eval/gold.json`、`tests/eval/test_gold_gate.py` | 本提交不填金标(先锁规则) |
| 评测期联网代码级禁用;demo 层 ≠ 统计结论 | ADR-0005、Anthropic 清单 1–2 | 单次 demo 不得报准确率 |
| 词表定义上下文无关;评测加严判据不进 CONTEXT | Anthropic 清单 4 | 算法细节、causal 对齐留评估文档 |
| Lead 复验白名单仍为 `LEAD_TOOLS_W3`;W9 工具表已定义未挂载 | `lead.py`、`tools.py` | 挂载会扰动 `must_stale` 主链,必须显式隔离 |

## 3. 候选路线

### 维度一:检测器立刻怎么改

- **a. 维持时效词 + 价格关键词启发式,只改文档口径**
- **b. 丢弃启发式,直接上 embedding / LLM-as-judge**
- **c. 把现有三条函数改成操作定义执行体**(T1 对照 dead、对象门闩互斥、源存在性 unverified),词表只作同维度门,不当论文方法

### 维度二:`must_quarantine` 金标

- **a. 本提交按 demo 结果回填 gold**(事后贴金标)
- **b. 本评估先锁构造规则,另一次提交再写 id,写完再跑评测**
- **c. 继续空数组,只靠 demo 脚本验收 W12**

### 维度三:Lead 挂载 Forensic

- **a. 立即把 Lead 白名单换成 `LEAD_TOOLS_W9`**
- **b. 处理器先写上,白名单仍 W3;W9 挂载与记忆金标 runner 绑定,不进 `must_stale` 主链**
- **c. 永不挂 Lead,Forensic 永远只跑独立脚本**

### 维度四:论文方法身份

- **a. 宣称启发式算法原创,投 AAAI/ACL/NeurIPS 主会**
- **b. 放弃发表,只做课程 demo**
- **c. 方法身份 = T1 锚定的 fail-closed 记忆闩**(与主张复验同构),启发式只作可复现基线;先 workshop / Findings / 系统论文,主会必须另做对照实验

### 维度五:中长期能力扩张

- **a. 知识图谱 + 多模态 + 主动外网验证(原分析文 §4)**
- **b. 先闭环产品闩与预注册评测,再加可消融的学习器;图谱/多模态/外网列为弃或远景,不挡论文最小集**

## 4. 逐路线评估

### 4.1 检测器:a vs b vs c

| 维度 | a. 只改文档 | b. 立刻上模型 | c. 操作定义闩 |
|---|---|---|---|
| 与 schema 一致 | 否:时效词 ≠ dead | 可能,但不可复现、评测期禁联网 | 是:dead 必须点回 T1 |
| Anthropic 清单 1 | 继续把 demo 当测量 | 随机系统单次跑会假装成方法 | 闩是确定性层,可逐位复现 |
| 误报 | 竞品A vs 竞品B;「目前」仍有效 | 依赖解码参数,未预注册 | 对象不相交不互斥;无 T1 不下死 |
| 实现成本 | 零代码 | 高,且与 Critic 职责重叠 | 中:改三条函数 + 接 `read_source` |
| 论文可用性 | 负贡献(会被审稿人当场拆穿) | 无基线无金标=不可投 | 可引用的 **rule baseline** |
| 被否理由 | 操作定义已被切片钉死 | 「默认 LLM」不是规格;且无对照 | — |

**被否的原推荐(原分析文)**:把 Source Reference Existence Check / Keyword Matching / Temporal Indicator 写成高原创算法,并称 100% 准确率、零误报、可投 AAAI/NeurIPS。否决理由:字段真值判断不是算法;时效词检测与 dead 定义冲突;仓库无标注集;会议清单是愿望。此条命中 Anthropic 清单 1、2、4、5。

**拍板**:c。

### 4.2 金标:a vs b vs c

| 维度 | a. 本提交回填 | b. 先锁后填 | c. 继续空 |
|---|---|---|---|
| HARKing | 检测器刚改完就按它的输出写金标=事后改判据 | 构造规则先于结果 | 切片 §11.3 北极星空转 |
| 单测 | 必改 `test_gold_gate` 的空数组断言 | 本提交不动该断言 | 维持 |
| 测量身份 | 假测量 | 预注册 | 只有 demo |
| 被否 | 清单 5:可编辑 ≠ 可逆 | — | W12 记忆金标永不存在 |

**拍板**:b。本评估 §7 锁构造规则。本提交 **不** 改 `gold.json` 的 `must_quarantine`。

### 4.3 Lead 挂载:a vs b vs c

| 维度 | a. 立即 W9 | b. 处理器预留、评测隔离 | c. 永不挂 |
|---|---|---|---|
| 切片 §11.2 | 符合「Lead 看见打架再 spawn」 | 符合,但模型暂时不可见 | 违反集成定义 |
| `must_stale` 主链 | 模型可能耗费步数去审记忆,引入混杂 | 主链零变化 | 主链零变化 |
| 代码 | Lead 换白名单即改变所有复验 | `_t_spawn_forensic` 已在、W3 不可见 | 处理器可删 |
| 被否 | 清单 2:评测混杂 | — | 产品闩接不上复验单 |

**拍板**:b。W9 挂载是中期项,与记忆金标 runner 绑定,显式不进 12 条主张矩阵。

### 4.4 论文身份:a vs b vs c

| 维度 | a. 启发式顶会 | b. 不发表 | c. T1 闩 + 基线分层 |
|---|---|---|---|
| 相对文献 | 词表规则相对 FEVER/Mem0/STALE 无新算法 | 放弃切片里已点名的开放问题 | 问题定义可辩护:高相关记忆在「记忆彼此不吵、但与 T1 吵」时如何 fail-closed |
| 审稿预期 | 主会拒稿(方法浅、无对照、过声称) | 与「模块好到能发」目标冲突 | workshop → Findings/系统文;主会另要数据集与基线 |
| 产品一致性 | 把 FreshLatch 说成记忆算法公司 | 只剩课程作业 | 与「卖作废不卖记住更多」同构 |
| 被否 | 清单 1、3、6 | 用户目标否决 | — |

文献对照(二手检索,不作 TAM;C 级数字不进主表):

- Mem0 *State of AI Agent Memory 2026*:承认高相关 staleness 仍开放;decay 解决的是低相关近因。
- Zep/Graphiti:有矛盾新事实到达才失效;「无新记忆来吵架的静默过期」看不见。
- MemGPT/Letta、MemoryBank、A-MEM:优化召回/压缩/层级,不把项目语料 T1 当记忆的 ground truth。
- FEVER/FEVEROUS:主张对 Wikipedia,不是 Agent 项目记忆对双快照语料。
- STALE(2026):对话里用户信念是否被新观察隐式推翻;设定不同。
- 切片已引用的 GitHub Copilot 叙述:过期记忆比没有记忆更危险。

**本模块若有论文,贡献候选是问题与系统,不是检测器公式。** 可写进摘要的发现目前 **尚未产生**。

**拍板**:c。

### 4.5 扩张:a vs b

原分析文的图谱、多模态、外网主动验证在切片 §14 与评测禁联网下不可作为近期路径。外网验证破坏 `must_stale` 可复现性。多模态本课题语料是 markdown。图谱在 10 条记忆上不可证伪。

**拍板**:b。登记册把图谱/多模态/外网标【弃】于论文最小集;学习器标【留位】,必须能对闩做消融才允许出现。

## 5. 拍板 + 逐项子决策

**总拍板**:MemoryForensics 的身份是 **T1 锚定、人确认才移出召回的 fail-closed 闩**,检测器必须执行 schema,评测必须预注册,论文必须等测量,不能用启发式分析文里的会议清单当计划。

| # | 子决策 | 选择 | 说明 |
|---|---|---|---|
| 1 | 检测顺序 | unverified → dead(T1) → 其余互斥 | 已死条目不再与 T1 真记忆配成「两边都隔离」 |
| 2 | dead 判据 | 与 source_ref 对应 T1 条款/全文冲突;含「从 X 降至 Y」覆盖 | 无 T1 文本 → 不下 dead;时效词单独不算 |
| 3 | 互斥判据 | 同属性词 + (数字冲突或反义) + 具体对象门闩 | 对象不相交 → 不互斥 |
| 4 | unverified | 无 source_ref,或 doc 在 T0/T1 都不存在 | 不可核 ≠ 假 |
| 5 | checksum-dead | 留位 | CONTEXT 已钉死未启用 |
| 6 | 主张作废连带记忆 void | 留位 | schema 有,条目尚无 claim_id 字段 |
| 7 | Forensic 形态(本期) | 确定性 `inspect()` | 不是 LLM 循环;skill 文件仍描述真 Agent,中期再同构 Critic |
| 8 | Lead 白名单 | 仍 W3 | `_t_spawn_forensic` 预留;挂载另提交 |
| 9 | `must_quarantine` | 本提交不填 | 构造规则见 §7 |
| 10 | 论文方法名 | T1-anchored memory latch | 禁止把词表叫算法名投稿 |
| 11 | 会议 | 先 workshop/系统;主会另开实验 | 禁止把 AAAI/NeurIPS 写进当前里程碑 |
| 12 | UI 记忆卫生侧栏 | 中期 | 切片 §11.4;主屏仍是复验单 |

### 5.1 本提交已执行的代码修正(demo 层验证,不是金标)

`ForensicAgent.inspect()` 按上表执行。`scripts/w9_w12_memory_forensics_demo.py` 合成 10 条、入库真实语料后一次运行(2026-09-21,本机,非采样):

- dead: `mem_dead_price`(99 被 T1「降至 79」覆盖,证据 `t0-competitor-notes#p2@T1`)、`mem_dead_reg`(未出台 vs T1 强制,证据 `t0-regulatory-memo#p2@T1`)
- contradictory: `mem_cx_high` vs `mem_cx_low`
- unverified: 无 source_ref 一条 + 指向不存在文档一条
- 对照 4 条仍在召回:`mem_ok_market/cost/tech/support`

此读数是 **demo 层、n=1、合成记忆**。禁止写成准确率。禁止写进论文主表。

## 6. 工程手段总登记册

处置词汇:实装 · 留位 · 承载 · 触发 · 弃

| 手段 | 原理 | 优势 | 代价 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| T1 条款对照 dead | 按 `source_ref` 读 T1 块,数值覆盖/监管极性冲突才标死 | 与主张 stale 同构,可点回 | 覆盖规则覆盖不了全部句法 | Critic 必须锚 T1 | **实装** |
| 「从 X 降至 Y」覆盖 | T1 仍出现旧数字时,旧数字不算 live | 挡住 99∈T1 子集假绿 | 只覆盖降价句式 | 语料 p2 真实句法 | **实装** |
| 具体对象门闩 | 两边都有具体对象且不相交 → 不互斥 | 挡住竞品A vs 竞品B | 裸「竞品」仍可能互斥,这是定义内 | schema「同维度」 | **实装** |
| 源存在性 unverified | `read_source` T0/T1 皆空 → 不可核 | 覆盖定义后半 | 依赖入库 | 工具说明原文 | **实装** |
| 提议-确认隔离 | `propose_quarantine` 后 `confirm_quarantine` 改 status | 可逆、可审计 | 人未确认时召回仍含腐烂 | HumanLatch | **实装**(此前已有,保留) |
| `inspect()` 与 `run()` 分离 | 纯函数审核 vs 工具落标 | Lead 同步派驻可复用 | 两入口要保持同一判据 | Auditor `judge` vs 工具 | **实装** |
| forensic `retrieve/read_source` | 工具层接到 store | 真 Agent 期可直接用 | 本期 `run()` 主要走 read_source/get_chunk | FORENSIC_TOOLS 白名单 | **实装**(接线) |
| `_t_spawn_forensic` | Lead 处理器 | W9 一行挂载 | 默认不可见,避免假集成 | `_t_spawn_critic` | **留位**(代码在,白名单未挂) |
| 真 Forensic ReAct 循环 | 与 Critic 同构 ≤8 步 | 切片「真 Agent」 | 随机层,需容差条款 | `roles/critic.py` | **留位** |
| `must_quarantine` 金标 | 切片 §11.3 | 北极星 | 填早即 HARKing | `must_stale` | **留位**(规则已锁) |
| 记忆假绿对照 | 无工具 LLM 把记忆摘要成「结论仍一致」必须假绿 | 证明闩有效 | 要固定摘要提示词 | 主张假绿对照 | **留位** |
| 记忆卫生 UI 侧栏 | 待隔离、理由、T1 点回、确认 | 切片 §11.4 | 主屏红线 | 复验单双栏 | **承载** |
| W9 白名单挂载 | Lead 可见 spawn | 产品集成 | 扰动主张评测 | 阶段挂载纪律 | **触发**(记忆 runner 就位后) |
| 隔离名单注入 Lead 上下文 | `quarantine_list` 现空槽 | 腐烂不进下一轮记忆侧 | 要从 store 同步 | `runner.quarantine_list` | **触发** |
| checksum-dead | 与 validity_basis 对账 | schema 有 | 语料 checksum 全空 | checksum 激活契约 | **留位** |
| 作废主张连带记忆 void | schema 操作定义 | 与 HumanLatch 闭环 | 记忆无 claim_id | void 主张 | **留位** |
| sentence-transformers 语义矛盾 | 余弦+情感当矛盾 | 看起来像 NLP | 高相似≠矛盾;引入模型漂移 | 原分析文 §4.2 | **弃**(论文最小集) |
| 记忆知识图谱 | 实体关系检测矛盾 | 可讲故事 | 10 条记忆不可证伪 | 原分析文 | **弃**(论文最小集) |
| 多模态 consistency | 表/图/文对齐 | 远景产品 | 无多模态语料 | 原分析文 | **弃** |
| 外网主动验证 | news API | 像生产 | 评测期禁联网 | 原分析文;web_search 插座 | **弃**(评测路径) |
| 时效词单独标 dead | 「目前/当前」 | 实现廉价 | 与 dead 定义冲突、误报 | 修正前代码 | **弃** |
| 把 demo 准确率当论文结果 | 7 或 10 条合成 | 好看 | 清单 1 直接出局 | 原分析文 §2.1 | **弃** |

## 7. 预注册:`must_quarantine` 构造规则(先于填数)

以下规则锁定后,填 `gold.json` 的另一次提交不得因检测器输出不好看而改规则。改规则 = 本评测作废,须新开决议。

### 7.1 规模与分桶(切片 §11.3 原文操作化)

- 合成记忆 **8–12** 条,写入将建的记忆夹具(路径另提交指定,不进本仓主张 `causal_chain`)。
- **must_quarantine** 必须包含:2 条 dead id + 互斥对中「不得同时召回」的两侧 id + 2 条 unverified id。
- **must_keep**(本评估加的对照桶,不进 CONTEXT):至少 3 条 T1 仍支持、有合法 `source_ref`、且不与 must_quarantine 条目共享「具体对象 ∩ 同一 ATTRIBUTE 词」的记忆。防止全隔离假绿。
- 互斥对不得再用「T0 旧价 vs T1 新价」冒充;那种配对应落在 dead,只隔离旧侧。互斥对必须是 T1 **不能单独裁决** 的同维度相对表述。

### 7.2 通过线(记忆 runner,尚未存在)

- 建议态即可计「离开下一轮召回」(切片:建议态即可隔离召回)。
- must_quarantine 每条 id 必须被 flag,且 `propose_quarantine` 名单包含该 id。
- must_keep 不得出现在提议隔离名单。
- 每条 dead 必须带至少 1 个可点回的 `doc_id#anchor@T1`;evidence_id 必须能在 T1 语料取回块。空列表 = 本条失败。
- 每条 unverified 的理由必须能指出「缺 source_ref」或「文档 id 不存在」。
- 人未确认前,磁盘 `status` 仍为 active(单测已有结构,行为要锁)。

### 7.3 层声明

- 记忆 runner 第一版是 **冒烟**(n=1 确定性闩,或 LLM Forensic 时 n=3、temp 与模型写进 meta)。
- 确定性闩:逐位一致;背离 = 违例。
- 若中期换成 LLM Forensic:随机层容差另锁,不得把 n=3 写成方差。
- 解码参数、模型、日期写入 `gold.json` meta 或 runner 报告头;托管端点漂移限制写入留档。

### 7.4 什么背离算违例级

- must_quarantine 漏标。
- must_keep 被隔离。
- dead 无 T1 证据 id,或 id 编造不在语料。
- 未确认即改 `status=quarantined`(demo 脚本的「模拟人确认」不算产品自动删除,但产品路径不得跳过确认)。
- 评测路径出现联网。
- 把本 §7 在看到结果之后改掉还不声明作废。

## 8. Anthropic 视角自审(本方案对照清单 1–7)

1. **演示可过 ≠ 测量可信**:§5.1 demo 已声明层。W12_ACCEPTANCE_SUMMARY 等把 demo 打成验收通过,本评估要求那些文档加勘误,不得再当测量。
2. **单次运行判生死**:本提交检测器是确定性的,n=1 合法;一旦上 LLM Forensic,必须另锁采样。禁止把本次 demo 报成准确率。
3. **默认不是规格**:闩无 temperature。将来 LLM 路径必须写模型/日期/解码。checksum-dead 不因为「以后会有」而假装在场。
4. **词表上下文无关**:CONTEXT 只加 `must_quarantine` 产品金标定义。覆盖正则、ATTRIBUTE 词表不进 CONTEXT。
5. **止损预注册**:§7 先于 gold 填数。本条满足 ADR 三条件,见 ADR-0014。
6. **复现两层**:确定性层=inspect 对同一输入同一输出;随机层尚未启用。违例级见 §7.4。
7. **ADR 三条件**:「先锁金标再填」看起来改起来便宜,但事后改判据毁灭实验意义 → 难反转 + 反直觉 + 真实取舍,故立 ADR-0014。

清单命中后的修正已合入拍板:不填 gold、不挂 W9 进主张评测、不投主会当近期 KPI、弃时效词 dead。

## 9. 现状评估(分层,不混写)

### 9.1 已实装且与定义对齐(本提交后)

- 三表:long_term_memory / memory_flags / quarantine_proposals
- 五工具 + retrieve/read_source 接线
- inspect 顺序与对象门闩、T1 覆盖、源存在性
- 人确认后 status=quarantined,list_memories 只返回 active
- Lead `_t_spawn_forensic` 代码在盘,W3 不可见

### 9.2 未实装(文档曾写成已完成)

- Forensic 作为裸 ReAct 真 Agent(skill 写了,代码没有循环)
- Lead 白名单 W9 挂载
- `runner.quarantine_list` 从 store 同步
- 记忆卫生 UI 侧栏(复验单仍在;侧栏未做)
- `gold.json` must_quarantine 仍 `[]`
- 记忆假绿对照
- checksum-dead、作废连带 void
- 第二份更脏 T1 语料是否已为记忆卫生服务:主张评测语料在,记忆夹具此前用假 doc_id,与语料脱节

### 9.3 文档假绿(必须勘误)

- `memory-forensics-heuristic-algorithms-analysis.md`:原创性评级、100% 准确率、实验结果、AAAI/NeurIPS 清单
- W9–W12 技术评估 §7「文本相似度」(代码无相似度)
- task-completion / w9 README / W12_ACCEPTANCE_SUMMARY:「侧栏已有」「与 Lead 无缝集成」「W12 全部通过」

## 10. 短中长期行动清单

### 10.1 近期(0–3 个月):产品闩闭合,论文还不是目标

优先级从高到低。前三项是止损,做完才允许谈发表。

1. **勘误**(本提交):撤回过声称;本评估成为单一真相。
2. **记忆夹具 + 按 §7 填 must_quarantine**(另提交):8–12 条,真实 doc_id,对照桶 must_keep。
3. **记忆冒烟 runner**:确定性 inspect,断言 §7.2;n=1。不并进 12 条主张矩阵。
4. **UI 侧栏**:待隔离、理由、T1 点回或「缺 source_ref」、确认按钮。主按钮仍是「开始复验」。
5. **确认后同步 `quarantine_list`**:下一轮记忆侧上下文不得出现已隔离 id。
6. **假绿对照(记忆)**:固定提示词让无工具模型摘要记忆库;必须输出「仍一致」;本闩必须标出金标 id。
7. **W9 挂载**:仅记忆 runner / 手动演示开启;默认 Lead 复验仍 W3。

完成定义(近期):切片 §11.5 四条验收可在 demo+冒烟层勾选,并在报告头写「demo/冒烟,非统计」。

### 10.2 中期(3–12 个月):测量层,workshop 论文最小集

1. Forensic 循环与 Critic 同构:新会话、skill 教义、FORENSIC_TOOLS、≤8 步、结论唯一出口(可复用 propose_quarantine + 结构化 finding)。
2. 基线消融(必须同一金标、同一层声明):
   - B0 无审计(全召回)
   - B1 TTL/时效词
   - B2 仅互斥(无 T1)
   - B3 本闩(T1 + 互斥 + 无源)
   - B4 LLM-as-judge(写死模型与解码)
3. 增加 **静默过期** 条目:与其它记忆不互斥,只与 T1 冲突。这是相对 Mem0/Zep 可辩护的差异。
4. n≥5 仅对 LLM 条件;确定性闩仍 n=1 逐位。报告分表,不合并。
5. 投稿目标:**Agent 记忆 / AI 安全 / 系统可靠性 workshop**,或 Findings 系统短文。标题应含 invalidation/quarantine/T1 snapshot,不含 “novel heuristic algorithm”。

完成定义(中期):有预注册报告、有 B0–B3 对照、有静默过期桶、审稿人能复现确定性闩。

### 10.3 长期(12 个月+):主会才需要的东西

1. 公开、许可清晰的双快照记忆卫生数据集(合成可,但要声明;真机密永不进公开集)。
2. 跨领域(定价以外)与跨语言,证明闩不是中文价格正则。
3. 若上学习器:必须对 B3 有正消融,并报告失败案例,不得只报均值。
4. 此时才评估 ACL/AAAI **系统或 demo track**;ICML/NeurIPS 主会仍不自然,除非出现可分离的学习问题。
5. 图谱/多模态/外网验证仍默认不进主路径;若做,必须新开决议,且外网不得进可复现评测。

## 11. 面试讲法

**Q: 这不就是关键词规则吗,为什么能发论文?**
A: 关键词不是贡献。贡献若成立,是把 Agent 项目记忆当成与主张同构的可作废对象:ground truth 是 T1 快照,不是向量近邻,也不是 TTL。Mem0 自己写过高相关 staleness 仍开放;Zep 要等一条新记忆来吵架。我们审的是「记忆之间不吵、但和 T1 吵」的静默腐烂,并且移出召回要等人。现在还没有可写进摘要的发现,只有可复现的闩和预注册评测计划。

**Q: 为什么不先上 embedding?**
A: 余弦高表示近义,不表示矛盾。先上模型会把不可复现的随机层当成方法,违反「默认不是规格」。学习器只能作为对闩的消融,不能当第一版判据。

**Q: 为什么本周不把 must_quarantine 填上?**
A: 检测器刚按定义改完,若按它的输出写金标,就是事后改判据。规则先锁在本评估 §7,填数另提交。这和 must_stale 的纪律同一条。

**Q: 为什么 Lead 还不挂 spawn_forensic?**
A: 处理器在,白名单不在。挂上去会让主张复验模型把步数花在记忆上,`must_stale` 矩阵不再干净。记忆评测和主张评测必须分开跑。

**Q: 当前模块能不能投 NeurIPS?**
A: 不能。没有学习问题,没有对照,没有可公开的测量。说能投是对审稿人撒谎,也会把产品做成记忆算法表演。

**Q: 10 条合成记忆算实验吗?**
A: 算 demo 层冒烟,与 W4 假绿对照的「仪器」同类,不是统计。n=1 确定性闩可以逐位复现,这是优点,不是论文主表。
