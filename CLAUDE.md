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
