# CLAUDE.md

## 交流语言

始终使用中文与用户交流:所有提问、叙述、工单、地图、文档一律用中文(技术术语可保留英文原词,如 `Lead Reverifier`、`must_stale`)。

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues (via the `gh` CLI). See `.claude/rules/issue-tracker.md`.

### Triage labels

Default label vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `.claude/rules/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `.claude/rules/domain.md`.

## 决议文档纪律(每次决议工单必须执行,无需提醒)

每张决议类工单(grilling/prototype/research 拍出技术选型或设计拍板)关闭时,**必须一次性落齐以下四件套**,缺一不可:

1. **大而全评估文档** → `docs/research/<主题>设计评估.md`(命名基准:《Agent循环实现选型评估.md》《HumanLatch闭环设计评估.md》)。固定结构:
   - §问题 + 前置约束(哪些答案已被先前的工单/ADR 钉死)
   - §候选路线(每个决策维度的全部候选,含被否项)
   - §逐路线评估(对照表:维度 × 候选,被否理由写透)
   - §拍板 + 逐项子决策
   - §工程手段总登记册(大而全:每项手段一句话原理/优势/代价/参考先例/本期处置,处置词汇表:实装·留位·承载·触发·弃)
   - §面试讲法(grilling 预案问答)
2. **ADR** → `docs/adr/NNNN-<kebab>.md`(版本号顺延;仅在难反转+反直觉+真实取舍三条件齐备时)
3. **词表更新** → 新术语即时落 `CONTEXT.md`
4. **决议评论 + 关单 + 地图 Decisions-so-far 补行**(补行里必须带评估文档链接,格式「评估见 docs/research/XXX.md」)

**Why**: 选型以 Anthropic 级面试讲解为判据——评估文档的登记册和面试讲法两节就是面试弹药库;被否选项写透才能在被追问「为什么不选 X」时答得上。

**How to apply**: wayfinder 会话 resolve 工单的最后一步自动执行四件套并 git commit;缺任何一件视为工单未 resolve。

## Anthropic 评价纪律(每次决议必须主动执行,无需用户提醒)

每张决议类工单(grilling/prototype/research)在给出推荐方案后、关单前,**必须主动做一轮「Anthropic 视角评审」拿既定清单挑自己的方案**,把挑出的修正合入拍板;用户问「Anthropic 会怎么评价」是兜底,不是触发条件。固定清单(随实践增补):

1. **演示可过 ≠ 测量可信**:验收/评测类判据先声明自己是哪一层;demo 层判据不得假装成统计结论。
2. **随机系统单次运行判生死 = 不合格**:必须采样运行间噪声;采样要真的在变——`temp=0` 时 seed 是摆设,多 seed 跑出相同结果是假信心;n 小就诚实框定为冒烟检查,不报方差。
3. **「默认」不是规格**:解码参数(temperature/seed/模型版本/日期)显式写明并逐运行记录;托管端点在漂移,跨会话复现只能是近似的,此限制写入留档。
4. **词表定义上下文无关**:评测模式加严判据(causal_chain 对齐、金标核对)归评估文档,不进 `CONTEXT.md`;生产里判不出来的概念不是产品词汇。
5. **止损/验收判据预先锁定(pre-registration)**:判据先于结果写死,事后修改 = 验收作废(HARKing);可编辑 ≠ 可逆,事后改判据技术上容易、实验意义上毁灭性——这类纪律本身满足 ADR 三条件,要记 ADR。
6. **复现条款定义两层**:确定性层(闸、不变量)逐位一致;随机层给文档化容差;并预定义「什么背离算违例级」。
7. **ADR 三条件重检**:被挑战的方案若靠「改起来便宜」跳过 ADR,要追问「事后修改是否破坏实验/止损意义」,是则三条件齐备。

**Why**: 本仓全部决议以「Anthropic 级面试讲解」为判据,评审清单就是面试弹药的一部分;被动等用户提醒 = 纪律失效。

**How to apply**: 决议类工单 resolve 流程中,grilling 每轮推荐后自问清单 1–7,有命中则在下一轮主动提出修正;评估文档「逐路线评估」一节必须包含被 Anthropic 清单否决的原推荐(写透理由)。

## Agent Guards

Thin overlay on Matt Pocock — not a second `/implement`. Config: `docs/agents/agent-guards.md`.

- After `/to-tickets` → `/enrich-tickets`
- Before coding → `/before-implement <id>` then fresh session `/implement`
- Setup once: `/setup-agent-guards`

