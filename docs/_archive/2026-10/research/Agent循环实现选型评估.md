# Agent 循环实现选型评估

> 工单:[Agent 循环实现方式:裸 tools 循环 vs LangGraph ToolNode vs Agently](https://github.com/luxingjiang1993/FreshLatch/issues/6)
> 日期:2026-09-19 · 状态:**已拍板**(选 a,本文同时是面试讲解的完整底稿)
> 前置决议:工单 [#2](https://github.com/luxingjiang1993/FreshLatch/issues/2)(模型冒烟)、[#7](https://github.com/luxingjiang1993/FreshLatch/issues/7)(LangGraph 只做 interrupt 人审管道)、ADR-0001(白名单承载角色禁止事项)、ADR-0003(检索层)、立项切片 L194
> 配套 ADR:`docs/adr/0004-Agent循环裸tools路线.md`

---

## 1. 问题:我们要做什么决策

FreshLatch 的复验主链由三个真 Agent 驱动:Lead Reverifier(规划复验)、Critic(只找反证)、Auditor(短循环判定 fresh/stale/unknown,后 W4 还有 Forensic)。本题拍板:**这些 Agent 的「思考→调工具→看结果→再思考」循环用什么实现**。候选三条:

- **(a) 裸 OpenAI 兼容 chat.completions + tools 自写循环**(06 课蓝本方向);
- **(b) LangGraph ToolNode / create_react_agent 预制件**;
- **(c) Agently 4.1.4.8 的 action 注册 + workflow**。

判断好坏的五个判据(工单正文钉的):① 是否违反「LangGraph 只用于 checkpoint/interrupt,**图不是 Agent**」的立项纪律;② 步数护栏(Lead 18 / Critic 8 / Auditor 6 轮、单次检索预算 24)在哪层强制最干净;③ `spawn_critic` / `spawn_auditor` 的**动态派驻**(Lead 按中间结果决定,不是固定第 3 步召唤)在哪条路线最自然;④ 角色激励分离(Critic 不得强化原主张、Auditor 不得改主张)怎么用工具表白名单实现;⑤ 与工单 #7 的衔接——循环跑在图外,人审中断怎么接。

## 2. 前置约束:这道题的大半答案已被钉死

选型不是从零开始,有四块前置决策把搜索空间压得很窄:

| 前置约束 | 出处 | 对本题的含义 |
|---|---|---|
| 技术栈 = 「OpenAI 兼容 chat.completions + tools」;「LangGraph 只用于 checkpoint / interrupt 等人续命,图不是 Agent」 | 立项切片 L194 | 路线 (a) 就是立项切片点名的栈;(b) 的 ToolNode 循环恰好是把 Agent 塞进图 |
| qwen-flash / qwen-turbo 多轮工具调用能力冒烟 go,不假设并行 tool_calls | 工单 #2 | 裸循环的最大运行风险(模型在循环里稳不稳)已被实验否掉;循环设计不依赖并行 tool_calls |
| Agent 循环跑图外;LangGraph = `interrupt()` + `Command(resume)` + `SqliteSaver` 的人审管道 | 工单 #7(`docs/research/langgraph-interrupt人审模式研究.md`) | 任何把循环做进图的方案都要自造「Agent 图 + 人审图」两层矛盾 |
| 工具白名单承载角色禁止事项;`gates/` 独立为绿灯唯一出口 | ADR-0001 / 工单 #3 | 白名单不是本题的开放问题,是已定的承载层;本题只需拍「循环用什么跑」 |

**规模前提**:单人本地、Python 3.11、每主张一次复验 ≈¥0.001(工单 #2)、评测要求轨迹可复现。这不是要跑生产流量的系统,是要求**每一步都看得见、测得到**的评测体。

## 3. 候选路线

### 路线 a:裸 chat.completions + tools 自写循环

- **形态**:一个 `while` 循环——每圈把 messages + 本角色工具清单发给模型,模型返回 tool_calls 就由宿主执行、结果以 `role=tool` 喂回,返回最终判定或触顶收尾。全部魔法 ≈50 行。
- **工程化种子**:`OpenManus-cy/app/agent/toolcall.py`——think/act 分离、`max_steps=30` 步数护栏、ToolCollection 白名单、特殊工具(Terminate)终止、TokenLimitExceeded 熔断;`ReActAgent` 基类 + 每工具一个类,正好改成「每角色一个白名单」。
- **课程蓝本**:`06_模型如何规划并调用工具/examples/openai_native_tool_calling.py`(原生 tool_calls 往返 + 「未允许的工具直接 raise」的 fail-closed 校验,L117-118)。
- **依赖**:`openai`(仅 HTTP 传输)+ `pydantic`。无 langchain、无 agently。

### 路线 b:LangGraph ToolNode / create_react_agent

- **形态**:循环作为图的节点跑——StateGraph 里 LLM 节点 + ToolNode + 条件边回环,预制件接管「调模型→执行工具→回灌」整圈。
- **纪律问题**:ToolNode 的卖点恰是把 Agent 循环**做进图**。这与立项切片「图不是 Agent」正面冲突,与 #7「循环跑图外」自造两层图。
- **版本事实**(1.0.x 实测盘点,见 #7 研究):`create_react_agent` 已**弃用**并迁去 `langchain.agents`;0.x→1.0.x 已发生大量 API 变化(NodeInterrupt→interrupt()、invoke(None)→Command(resume) 等)。循环进图 = 把 Agent 行为绑上这条升级过山车。
- **护栏事实**:ToolNode 的内循环在框架内部,步数/预算要么自写 state 记账(两处改),要么绕开预制件重写循环(=退化回路线 a)。

### 路线 c:Agently 4.1.4.8 action 注册 + workflow

- **形态**:工具用 `register_action` 注册,循环由 Agently 的 workflow/TriggerFlow 驱动;课程先例 `06_.../examples/02_react_search_browse.py` 用 TriggerFlow + 结构化输出命令(action_id/finish)表达 ReAct,`MAX_ROUNDS=5` 在 plan 节点里手工检查。
- **与原生 tool_calls 的偏差**:课程范式是让模型输出**结构化 JSON 命令**(宿主分发器执行,`01_function_calling_once.py` 的 execute_command),而非 OpenAI 原生 tool_calls 协议;立项切片点名的栈是后者。
- **护栏与派驻事实**:步数护栏要表达成 workflow 节点条件,与 TriggerFlow 状态机纠缠;`spawn_critic` 的子 agent 生命周期要塞进 workflow 状态,focus 参数传递绕。
- **依赖成本**:引入 agently 整框架及其传递依赖,而它唯一做的是「替我们写那 50 行循环」。

## 4. 逐路线评估

| 维度 | a: 裸循环 | b: ToolNode / create_react_agent | c: Agently |
|---|---|---|---|
| ① 「图不是 Agent」纪律 | ✅ 天然满足,图不进 Agent 层 | ❌ 直接违反:循环即图节点 | ✅ 不碰 LangGraph,但循环进 workflow 黑盒 |
| ⑤ 与 #7 人审管道衔接 | ✅ 循环跑图外,命中人审即调 interrupt 管道 | 需拆「Agent 图 + 人审图」两层,自造矛盾 | 同 a,但 workflow 状态与人审管道是两套状态机 |
| ② 步数护栏强制层 | ✅ 循环层 `while` 条件 + 构造参数,一处改 | 自写 state 记账或绕开预制件(两处改) | 表达成节点条件,与状态机纠缠 |
| ③ 动态派驻 spawn_* | ✅ spawn 就是 Lead 白名单里的工具,命中起新循环实例 | 图静态编译:动态子 agent 要么跳出图调循环(=退化回 a),要么动态构图(复杂度爆炸) | action 可注册,子 agent 生命周期塞进 workflow 状态,focus 传递绕 |
| ④ 角色白名单表达 | ✅ 构造循环实例时按角色给 tools 列表,ADR-0001 逐字落地 | ToolNode 收 tools 列表,但人格/禁止事项在图外,职责劈两半 | 注册表集中,禁止事项靠 prompt 软约束 |
| 依赖重量 | 极轻(openai+pydantic) | 重(langgraph+langchain,且 API 仍在迭代) | 重(agently 框架及传递依赖) |
| 可测试性 | 护栏=纯函数/条件,pytest 直测;轨迹=自己的 messages 列表 | 框架行为,要按 LangGraph 的方式测 | 框架行为,按 Agently 语义测 |
| 可观测/回放(评测要轨迹可复现) | messages 列表天然是轨迹,落盘即回放 | 经 LangSmith 或 state 历史,多一层抽象 | 经 workflow 事件流 |
| 升级风险 | 零(OpenAI 兼容协议是行业事实标准) | 高(1.0.x 刚弃用 create_react_agent) | 中(框架版本节奏不可控) |
| 参考代码先例 | 06 课 + OpenManus `toolcall.py`(工程化完整) | CASE-投顾 hybrid_wealth_advisor_langgraph.py | 03–17 课主力,TriggerFlow 先例 |
| 面试叙事 | 「循环是自己的代码,护栏是可测的纯函数」 | 「循环交给框架」+ 被追问弃用 API 怎么办 | 「用课程框架」+ 被追问黑盒里发生了什么 |

## 5. 最终拍板:路线 a,并一并拍板三项子决策

**选 (a) 裸 OpenAI 兼容 chat.completions + tools 自写循环**,工程化种子取 OpenManus `toolcall.py` 骨架(think/act 分离、max_steps、ToolCollection、特殊工具终止),不引 langchain / agently。

- **真 Agent 定性**:三个选项的循环都是模型驱动(真 Agent),非固定节点 workflow;区别在于循环归谁管——(a) 归自己 50 行代码。(b)(c) 的弃选理由不是「假」,是纪律违反、黑盒、依赖重、升级风险,见 §4。
- **多 Agent 定性**:**真多 Agent**,但不是框架白送的——多 Agent 是 Lead 白名单里两个 spawn 工具 + 自己写的子循环实例化,派驻深度恒 1。若召唤时机由代码写死(固定第 3 步),那才是假多 Agent(workflow 编排),本项目明确禁止。

**拍板方式**:纯纸面拍板,不做 POC。选 (a) 的最大运行风险已被工单 #2 冒烟否掉;护栏/派驻细节随 W1 实现自然暴露再调。决议注明:**W1 开工第一个任务 = 先把 Lead 裸循环骨架跑通**(冒烟级别,一条主张端到端),把「试跑」挪进实现阶段第一步,不单独占一轮 POC。

### 5.0 子决策零:循环范式 = ReAct,弃 Plan-and-Execute

三路线对比(§4)回答的是「循环归谁管」,本小节补上同样属于拍板内容、但容易淹没在框架选型里的**循环范式**定性:路线 a 的循环形态是 **ReAct**——单循环内 think → act(tool_call) → observe(tool_result) 交错,每轮由模型基于最新观察决定下一个工具或收尾;**没有独立规划器**,「规划」以逐轮决策的形式发生在循环内。

- **Plan-and-Execute(先出完整计划、再逐步执行)在选型时即未作候选**:三路线中没有一条对应该形态。登记册 §6.1 补记了完整权衡——它的优势是步数可预算、轨迹整齐;致命代价是**计划错了不回头**,而复验是发现式调查:Lead 读到 T1 原文之前不知道该查什么,先出的计划会被第一步检索结果推翻。
- **措辞辨析**:切片 §9 的「Lead 自主规划复验」指 ReAct 循环内的逐轮自主决策,**不是** plan-and-execute 的「先排全程计划」——规划颗粒度是「下一步」,不是「全程」。同理,工单 #10 决议中 skill 文件的「工作流」节是喂给逐轮决策的**方法骨架**,不是固定步骤编排(§6.1 的「固定 workflow 编排」同样被弃,立项即排除)。
- **优势/代价取舍**:ReAct 现场纠错强、与步数护栏天然契合(每轮都是决策点,预算检查一处生效);代价是轨迹长、token 费、思考质量不可控——本期以 18 步预算封顶 + Critic 派驻承接「反思」职责(§6.1 Reflexion 【承载】)对冲。

### 5.1 子决策一:步数与检索护栏

- **步数护栏 = 循环层 `while` 条件**。每个角色实例化时拿到自己的 `step_budget` 构造参数(Lead 18 / Critic 8 / Auditor 6),每转一圈减一;归零不硬断,而是注入一条「预算已尽,基于现有证据下结论」的系统消息,强制模型收敛收尾——**护栏管天花板,不管结论**。
- **检索预算 24 = Run 级共享计数器**,不是每个角色各 24。理由:检索是真金白银的 API 成本 + 评测可复现锚点,约束对象是整个 Run;Lead 查多了 Critic 就剩得少,这本身倒逼 Lead 珍惜查询。实现 = `retrieve` 工具外包一层计数装饰器,计数器挂在 Run 上下文对象上,Lead / Critic / Auditor 共享。
- 预算超限时 retrieve 返回结构化「预算已尽」结果(非异常),让模型自己改用 `read_source` 已有证据——fail-soft,不 fail-hard。

### 5.2 子决策二:动态派驻 spawn_critic / spawn_auditor

- `spawn_critic` / `spawn_auditor` 就是 **Lead 白名单里的两个普通工具**,模型自己决定何时调,参数 `focus`(如「专攻定价条款」)。
- 命中后代码做的事:**同一进程内同步起一个全新循环实例**——新开会话(消息历史不共享)、换人格系统提示词、换工具白名单、换步数预算(Critic 8 / Auditor 6);跑完后把 Critic 的结构化结论(`report_finding` 产出)作为 tool result 回吐 Lead,Lead 继续自己的循环。
- **派驻深度恒 1(硬约束)**:Critic / Auditor 的白名单里**没有** spawn 工具,不能再叫人。控制流永远是 Lead 一个中枢,防复杂度爆炸。
- **不传全量 transcript**:派驻时 Lead 只传「主张原文 + focus + 相关 evidence_id 列表」。理由:更干净的激励隔离(Critic 不被 Lead 思路带偏)、更便宜的 token、评测更可复现。

### 5.3 子决策三:角色工具白名单(fail-closed,默认拒绝)

ADR-0001 已定「白名单承载角色禁止事项」,四张清单拍死如下:

| 工具 | Lead | Critic | Auditor | 说明 |
|---|---|---|---|---|
| `retrieve` | ✅ | ✅ | ✅ | 共享 Run 级预算计数 |
| `read_source` | ✅ | ✅ | ✅ | 读 T1 原文点回 |
| `reverify_claim`(判 fresh) | ✅ | ❌ 不得放行 | ❌ 不得放行 | Critic / Auditor 想强化主张也没有工具可写 |
| `mark_stale` / `mark_gap` | ✅ | ✅ 只许判死 | — | Critic 只许判死不许判活 |
| `spawn_critic` / `spawn_auditor` | ✅ | ❌ | ❌ | 深度恒 1 |
| `report_finding`(反证上报) | ❌ | ✅ 唯一出口 | — | Critic 的结论容器 |
| `verdict`(fresh/stale/unknown) | ❌ | ❌ | ✅ 唯一出口 | 进 `gates/` 校验:无 `t1_evidence_ids` 不得 fresh |

**三层分离原则**:**prompt 管任务、白名单管禁止、规则闸管放行**。「不得强化原主张」这类激励约束不靠 prompt 祈祷,靠工具不存在——机械执行,可测可证。

## 6. Agent 循环工程手段总登记册(大而全 · 优劣势评估 · 本期处置)

> 用途一:**面试讲解**——「这些手段我全盘点过,本期按纪律与规模取舍,取舍逻辑如下」。
> 用途二:**后续开发可选项参考**——循环增强(记忆、压缩、观测)启用时,从这里点菜,不再重开调研。
> 处置词汇表:**【实装】**本期启用 · **【留位】**接口/格子已留,本期空实现 · **【承载】**由 Agent 行为或已定机制承载,不是循环组件 · **【触发】**条件命中后在对应工单拍板 · **【弃】**本期纪律/规模下明确不用。

### 6.1 循环范式

| 手段 | 一句话原理 | 优势 | 代价/风险 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| ReAct(交错思考+行动) | 每圈模型先说理由再调工具,观察结果继续 | 纠错靠模型现场反思,单角色收敛好 | 轨迹长、token 费;思考质量不可控 | OpenManus `toolcall.py`;06 课 `02_react_search_browse.py` | 【实装】三角色循环的基本形态 |
| Plan-and-Execute(先规划后执行) | 先出完整计划,再逐步执行不回头 | 步数可预算,轨迹整齐 | 计划错了不回头,复验要的是发现式调查不是执行既定计划 | CASE-智能投研 五节点深思图 | 【弃】复验是探索性任务,计划会随证据变 |
| Reflexion(失败后自我复盘) | 一轮结束后让模型自我批评再跑一轮 | 质量上限高 | 成本翻倍;且与 Critic 派驻职责重叠 | 12/13 课收敛回路 | 【承载】「找反证」由 Critic 派驻承载,不让 Lead 自产自验(不变量 I1) |
| 固定 workflow 编排 | 节点顺序代码写死,模型只填空 | 完全可控可复现 | 假 Agent——模型不能改路径 | — | 【弃】立项即排除 |
| 嵌套子 agent(同步派驻) | 父循环把任务连上下文交给子循环,子等结论返回 | 上下文隔离干净,激励可分离 | 子循环错误处理要想清楚 | 本工单 spawn 设计 | 【实装】深度恒 1 |

### 6.2 工具调用形态

| 手段 | 一句话原理 | 优势 | 代价/风险 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| 原生 tool_calls(OpenAI 协议) | 模型输出结构化 tool_calls,宿主执行 | 协议行业标准,qwen 冒烟已验证;06 课蓝本 | 需自己校验未允许工具(fail-closed) | 06 课 `openai_native_tool_calling.py`;OpenManus | 【实装】 |
| 结构化输出命令(function command) | 模型输出 JSON 命令(action_id+arguments),宿主分发器执行 | 校验直接(走 pydantic schema) | 不是标准协议,多一层转换;与立项栈不符 | 06 课 `01_function_calling_once.py`、Agently 课程范式 | 【弃】立项切片点名原生 chat.completions+tools |
| 并行 tool_calls(一轮多个) | 模型一轮调多个独立工具 | 延迟低 | qwen-flash 能力未假设(#2 决议);多工具并发执行要处理部分失败 | OpenManus 有处理逻辑 | 【留位】循环结构允许(执行器逐条执行),不主动开 |
| `tool_choice` 强制 | API 层强制必须/禁止调工具 | 粗粒度控制零代码 | 不解决「调哪个」的激励问题 | OpenManus ToolChoice | 【触发】某角色收尾阶段若老乱调工具再启用 REQUIRED/NONE |
| 特殊工具终止(Terminate) | 把「结束」建模成一个工具,模型自己宣布完成 | 收尾时机由模型掌握,轨迹自然 | 模型可能提前宣布 | OpenManus Terminate | 【实装】各角色的「唯一出口工具」即此模式 |

### 6.3 护栏与容错

| 手段 | 一句话原理 | 优势 | 代价/风险 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| 步数预算(while 条件) | 循环层数圈,归零强制收敛 | 最干净的强制层,pytest 直测 | 触顶时结论质量靠收尾提示词兜底 | OpenManus `max_steps=30` | 【实装】18/8/6 角色级 |
| 预算已尽软收尾 | 触顶不硬断,注入「基于现有证据下结论」消息 | fail-soft,模型有尊严地收尾 | 需写好收尾提示词 | 本工单 §5.1 | 【实装】 |
| Run 级检索预算(装饰器计数) | 共享计数器包在 retrieve 外 | 成本与可复现双锚点 | 超限后模型行为要靠 prompt 引导到 read_source | 本工单 §5.1 | 【实装】24/Run |
| token 限额熔断 | 上下文逼近窗口时收手 | 防爆窗崩溃 | 本期上下文小(单主张),用不上 | OpenManus TokenLimitExceeded | 【触发】语料/记忆变大后启用 |
| 工具失败重试 | 调用异常重试 N 次 | 网络抖动免疫 | 重试幻觉(模型以为工具成功) | 通用 tenacity 模式 | 【触发】联调观察失败率后定 N |
| 工具白名单 fail-closed | 未列出的工具调用直接 raise | 激励约束机械执行 | 需逐角色维护清单 | 06 课 L117-118;ADR-0001 | 【实装】 |

### 6.4 上下文与记忆(循环内)

| 手段 | 一句话原理 | 优势 | 代价/风险 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| 全量 transcript 单角色内保留 | 循环内 messages 只增不减 | 轨迹完整可回放,实现零成本 | 长循环费 token(本期 18 圈封顶,可控) | OpenManus memory | 【实装】 |
| 子代理隔离(不传全史) | 派驻只带主张+focus+evidence_ids | 激励隔离+省 token+可复现 | 焦点选择质量影响 Critic 产出 | 本工单 §5.2 | 【实装】 |
| 上下文压缩/摘要 | 超长时旧消息压缩成摘要 | token 省 | 证据细节丢失,复验伤证据链 | LangChain 通用 | 【弃】证据完整性优先于 token,且 18 圈用不上 |
| 跨主张长期记忆 | 复验经验沉淀供下次复用 | 越用越聪明 | 记忆腐烂正是本产品要审的问题 | project 多agent rag.py;W9–W12 MemoryForensics | 【留位】本期循环不接记忆写入;Forensic 只做只读审查 |

### 6.5 观测与评测(循环层)

| 手段 | 一句话原理 | 优势 | 代价/风险 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| messages 轨迹落盘 | 每圈 messages 存 JSONL | 评测回放、面试演示、复现三合一 | 需定义落盘 schema | project 多agent store.save_state | 【实装】轨迹 = 评测的一等公民 |
| 结构化轨迹断言(测试) | pytest 直接断言「Lead 第 N 圈应调 retrieve」 | 护栏与白名单的可测性兑现 | 测试要写 | project 多agent pytest 先例 | 【实装】进 tests/ 闸门单测位 |
| Langfuse/LangSmith 追踪 | 框架级 LLM 调用追踪 | UI 好看,维度全 | 重依赖,本地评测用不上;出网伤可复现 | CASE-langfuse | 【弃】本地 JSONL 够用 |
| 步数/预算遥测 | 每 Run 记录步数分布、检索消耗 | 成本与收敛性量化 | 几乎零成本 | 本登记册 | 【实装】随轨迹落盘 |

### 6.6 登记册总结:取舍逻辑一句话

> **本期 = 裸 ReAct 循环 + 步数预算软收尾 + Run 级检索预算 + fail-closed 白名单 + 深度恒 1 派驻 + JSONL 轨迹;一切框架级增强(Plan-and-Execute、Reflexion、上下文压缩、追踪平台)统一由「本期规模(单主张 18 圈内)不够用」触发,触发后在对应工单从本册点菜。** 纪律(图不是 Agent、白名单管禁止、评测可复现)决定现在不需要框架,登记册决定不丢。

## 7. 面试讲法(grilling 预案)

**Q:这是真 AI Agent 还是 workflow?**

> 真 Agent。分界一条:模型自己决定下一步调哪个工具、什么时候停、什么时候叫 Critic 来——代码只提供工具清单和步数上限的「圈」,圈里走哪条路是模型现场决定的。workflow 是路提前画死、模型只能填空,那种假 Agent 我们立项就排除了。

**Q:是多 Agent 吗?**

> 是,而且是真多 Agent——但多 Agent 不是框架白送的,是我们写的一个工具:`spawn_critic` / `spawn_auditor` 就在 Lead 的工具清单里,Lead 跑到一半自己决定调用,我们就起一个全新循环实例(新会话、Critic 的工具白名单和人格、8 圈预算),结论回吐 Lead。派驻深度恒 1,Critic 不能再叫人。若召唤时机写死在代码里(固定第 3 步),那才是假多 Agent。

**Q:为什么不用 LangGraph / 主流 Agent 框架?**

> 框架用在它增值的地方:模型 API 用 OpenAI SDK 传输,人审续命用 LangGraph 的 interrupt + SqliteSaver(这是工单 #7 专门研究后定的),Web 层用 FastAPI。但 Agent 的控制循环是我们自己的 ~50 行代码,因为护栏(步数、预算、角色白名单)必须是可 pytest 直测的代码,不是框架行为。而且 LangGraph 1.0.x 刚把 `create_react_agent` 弃用——循环绑上框架升级,是我们这种要求轨迹逐次可复现的评测系统承受不起的。

**Q:步数护栏怎么保证?模型跑飞了呢?**

> 三层。循环层:`while` 条件数圈,Lead 18 / Critic 8 / Auditor 6,归零不硬断,注入「预算已尽,基于现有证据下结论」让模型收敛收尾。预算层:检索 24 次是 Run 级共享计数,Lead 乱查 Critic 就没得查,倒逼珍惜查询。白名单层:每个角色的禁止事项是机械执行的——Critic 手里根本没有「判 fresh」的工具,想强化原主张也没有工具可写。一句话:**prompt 管任务、白名单管禁止、规则闸管放行**。

**Q:这套东西在简历上怎么一句话说?**

> 「三角色(Lead/Critic/Auditor)真多 Agent 复验主链:自研 ~50 行裸 tools 循环握住控制流,步数/检索预算护栏为可测纯函数,角色激励分离由 fail-closed 工具白名单机械执行,动态派驻深度恒 1,人审经 LangGraph interrupt 管道,全程 JSONL 轨迹可回放、可复现。」
