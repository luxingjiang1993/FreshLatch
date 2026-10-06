# 文档口径对齐与 onboarding 修订规格

> 来源：新电脑只读盘点会话 → `/to-spec`（Matt Pocock；本仓未安装 upstream skill，按 [to-spec 模板](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md) 合成，**不再访谈**）  
> 词表：`CONTEXT.md`  
> 权威 ADR（只对齐、不新拍）：`0002`/`0004`/`0009`（Auditor / 裸循环）；`0003`/`0026`/`0032`/`0033`（生产默认臂与 Hard-Gold 过线≠换臂）；`0016`/`0027`（T1 三卡 / 查询变换 / 包结论）；`0017`（checksum 半激活）；`0031`（发前钩子 ≠ 平台）  
> 盘点依据：同会话「现状盘点 + 风险清单」（基于代码与文档现状推断，无本机 git 史）  
> **测试主缝（已确认 2026-10-06）：onboarding 口径单一真相** —  
> 新读者只打开 README 现状表 + `docs/spec/README.md` + `docs/spec/00-架构总览.md` + `docs/roadmap.md` 文首，读到的**阶段、默认检索臂、Auditor 形态、Lead 不得自由改写检索串、评测臂已可跑、过线≠换臂**，与 `CONTEXT.md` + ADR-0032/0033 + 代码不变量一致；**禁止**用本波改 `PRODUCTION_RETRIEVAL_MODE` 或重跑 L3 金标来「证明」对齐。  
> 子缝（仅当主缝扫不到时）：① `docs/roadmap.md` 文内自相矛盾句；② 工具表废弃符号（`spawn_auditor`）标注；③ 管线模块说明与评测臂已填实对齐。**优先只暴露主缝。**

---

## Problem Statement

我在一台新电脑上拿到 FreshLatch，没有过往开发上下文。仓内文档同时存在三套时间层：W1–W4 汇编规格、V1–V2 发前闭环、I3/Hard-Gold 改臂闸。对外 README 停在 V2 冒烟；路线图文首写 #259 已过线未换臂，文末仍写「复跑未跑」；架构总览仍写 Auditor 是真 Agent、Lead 可改写查询、检索后两级空实现。结果是：我无法判断「现在该改代码还是该改叙述」，最容易把 Hard-Gold 过线讲成已换 hybrid，或按过期规格开工。

## Solution

做一次 **文档回填 + 极薄注释诚实化**，把 onboarding 面拉到与已接受 ADR 和现行代码一致。不新开产品能力，不换生产检索臂，不重开 checksum 全链，不重跑主张金标当本波 Exit。修订按「先消自相矛盾 → 再补对外现状 → 再给早期规格加历史横幅与关键句回填 → 最后标废弃符号」的顺序，使下一跳（改臂 Gate 人终收 / C′）有一张不骗人的地图。

## User Stories

1. As a 新电脑接手人, I want README 现状表写明 I3 冒烟已齐与 Hard-Gold 过线未换臂, so that 我不会以为产品停在 V2 或缺检索工作。
2. As a 新电脑接手人, I want README 写清下一跳是改臂 Gate 人终收或冻 bm25 与 C′ backlog, so that 我知道不该先做 Studio/薄对话。
3. As a 新电脑接手人, I want 路线图文首与文末对「复跑是否已跑」同一句话, so that 我不会在同一文件读到相反状态。
4. As a 新电脑接手人, I want 规格索引标题不再只说 W1–W4, so that 我知道卷 10–21 才是后期权威面。
5. As a 新电脑接手人, I want 架构总览文首声明「W1–W4 历史汇编，冲突以 ADR + CONTEXT 为准」, so that 我不会把占位续命/空实现管线当真实现。
6. As a 面试官, I want 对外页明确过线 ≠ 已换 hybrid, so that mid 不被「Hard-Gold」一词打穿。
7. As a 面试官, I want 文档继续声明层身份是冒烟/面试加固, so that 没人把 I3 骨架或 9 月 L3 报告升格成统计闭合。
8. As a 面试官, I want Auditor 被写成单轮 structured-output、不得拥有放行权, so that 与 ADR-0009 和现行角色代码一致。
9. As a 面试官, I want Lead 被写成不得自由改写检索串、须走主张查询变换, so that 与词表和 `query_transform` 一致。
10. As an 架构守护者, I want 生产默认臂叙述处处仍为 bm25, so that 本波无法偷换臂。
11. As an 架构守护者, I want 评测臂 dense/hybrid/rerank 被写成「可执行评测臂、生产不默认走」, so that 不再与「后两级空实现」互殴。
12. As an 架构守护者, I want checksum 半激活（renew 接线 / fresh 结构性空转）保持诚实登记, so that 没人宣传全链已启用。
13. As an 架构守护者, I want Forensic/记忆卫生标明不在默认 Lead 白名单, so that 无人把 W12 旁路当主链。
14. As an 架构守护者, I want `spawn_auditor` 在工具表被标废弃或移出挂载叙事, so that 实现会话不会按已废 API 开工。
15. As an 架构守护者, I want 不改规则闸不变量正文, so that 对齐文档不触发闸回归。
16. As a 文档维护者, I want 立项切片里 Lead 可 spawn_auditor / 改写查询的句子被回填, so that 产品切片不与词表打架。
17. As a 文档维护者, I want grill-prep 标明 V1 已实现、本页是历史阅读包, so that 代理不会停在「不要 implement V1」。
18. As a 文档维护者, I want W12 合规报告保持「不得引用为通过」文首, so that 本波不重写那份长报告、只避免把它链进 README 现状。
19. As a 文档维护者, I want CONTEXT 词表不因本波新增评测专用概念, so that 遵守「词表定义上下文无关」。
20. As a 产品负责人, I want 本波不做 LICENSE 决策, so that 法律面仍 Gate、不混进口径票。
21. As a 产品负责人, I want 本波不实现 C′ 插件/开放 webhook, so that 不把文档对齐偷渡成 V2 平台化。
22. As a 产品负责人, I want 本波不重跑 L3 gold/control, so that 9 月 remaining 报告仍是表现层真相源、本票不 HARKing。
23. As a 产品负责人, I want 本波不关闭或代批 GitHub 改臂实现票, so that 人终收纪律不被文档 agent 代行。
24. As an AFK agent, I want 修订分成可独立验收的文档批次, so that 一次会话只动一类矛盾。
25. As an AFK agent, I want 每批有「禁止出现的过时句」清单, so that 验收可 grep、不靠品味。
26. As an AFK agent, I want 实现决策不发明新模块名, so that 只改叙述与注释。
27. As a 回归守护者, I want 零产品行为 diff（闸、检索默认、HumanLatch、发前钩子）, so that 对齐不引入假绿。
28. As a 回归守护者, I want 若必须改 Python，仅限模块 docstring / 废弃常量注释, so that 行为测试不必扩面。
29. As a CI 守护者, I want 本波不强制新增 pytest, so that 文档票不绑 LLM、也不假装代码未测。
30. As a 读者, I want 合成 demo / 非 SaaS / 非 W12 通过 的 README 诚实句保留, so that 已做对的边界不被改坏。
31. As a 读者, I want 双包（thesis 合成课题 vs 顾问垂直主包）仍被标明谁是近端垂直, so that 选错 pack 时有文档锚。
32. As a 规格读者, I want 目录与模块卷要么加历史横幅要么补后期模块存在性一句, so that 早期目录树不被当成缺文件。
33. As a wayfinder, I want 本规格明确不新写 ADR, so that 决议四件套不被空转（无新难反转决策）。
34. As an 面试讲解者, I want 能指着「过线书面授权开票、配置仍 bm25」讲改臂闸, so that 与 ADR-0033 一致。
35. As an 安全意识用户, I want I2/V2 仍被标冒烟本机, so that 对齐时不升格渗透认证或 webhook 平台。

## Implementation Decisions

### 主缝与策略

- **主缝**：onboarding 口径单一真相（见文首）。测的是「打开规定的三份入口文档后会不会读到与 ADR/代码相反的阶段或机制」——不是新 API。
- **权威序（冲突时）**：`CONTEXT.md` 词表 > 已接受 ADR > `docs/evidence/` 层标签 > 路线图文首 NOW > README 对外现状 > W1–W4 汇编规格。本波只把后者拉向前者，**禁止**反向改 ADR 或词表语义。
- **不新拍板**：过线门、默认臂、Auditor 形态、查询变换、checksum 半激活、Studio 冻结、薄对话 Out —— 全部沿用既有 ADR。本规格是回填，不是 grilling。
- **不新 ADR**：不满足「难反转 + 反直觉 + 真取舍」；若实施中发现要改默认臂或激活 fresh checksum，**停、另开决议票**。

### 修订批次（建议 `/to-tickets` 按此切，一人一条）

1. **消自相矛盾（路线图）**  
   只改路线图内「复跑未跑」与「#259 已过线」冲突句，使全文与文首 NOW、Hard-Gold 证据目录一致：过线 · 未换臂 · 待 Gate 人终收。不改阶段 In/Out 表（除非同一句自相矛盾）。

2. **对外现状（README）**  
   在 Current status 增 I3（冒烟/面试加固）与 Hard-Gold 过线未换臂两行；Known gaps 保留 BM25 生产默认、开放爬虫未做、薄对话 Out、curl≠平台。不删除「非 SaaS / 非 W12 通过 / 非闭合测量」。

3. **早期规格历史化（架构总览 + 目录与模块 + 规格索引）**  
   文首加「历史汇编 / 冲突以 ADR+CONTEXT 为准」横幅。回填**最少关键句**（不必重画整张数据流）：Auditor 非带工具真 Agent；Lead 检索串经主张查询变换；HumanLatch 续命已实装非 disabled 占位；管线评测臂已填、生产默认 BM25；目录树注明后期模块（发前钩子、政策旁路、包结论等）已存在于仓、细节见对应卷。规格索引标题改为覆盖 W1–W4 汇编 **及** 后续阶段卷，并登记本卷。

4. **代码旁注释诚实化（薄）**  
   仅当文档回填后仍会从源码文首读到「空实现」或「请挂 spawn_auditor」时：更新管线模块说明；工具表将 `spawn_auditor` 标为 ADR-0009 废止、默认 Lead 白名单不含之。**禁止**删除仍被测试引用的符号（若测仍 import 名称，只改注释/文档字符串，行为保持）。

5. **卫星页指针（立项切片关键句 + grill-prep 状态）**  
   切片：Auditor/查询/spawn_auditor 与词表对齐；定价/日活叙事不加「已在售」。grill-prep：文首改为历史阅读包 + 现行 frontier 指向路线图 NOW（改臂 Gate / C′），删除或划掉「未钉死前不要 implement V1」作为现行禁令。

### 明确不写入实现的「看起来像该修」项

- 主张金标 L3 `all_hit` / 旧假绿对照：证据仍以既有 remaining 报告为表现层真相；本波只避免 README 假装已闭合。  
- `W12_*` 长报告：保留文首不可引用边界，不重写。  
- LICENSE、密钥、dense 索引是否在盘、GitHub 工单开闭：本波文档可提「需人确认」，不代操作。  
- `app.py` 重复 import：非口径，另票卫生。

### 词表

- 不往 `CONTEXT.md` 加「文档漂移」「onboarding 口径」等工程卫生词。  
- 正文继续用：Verify+、包结论、主张查询变换、Hard-Gold 过线、改臂授权闸、checksum 半激活、政策拒、发前钩子。

## Testing Decisions

- **好测试**：只断言读者可观察的口径（入口文档出现/禁止出现的句子；生产默认臂常量未被本 diff 改写）。不测排版美学，不测 LLM。  
- **主测（建议拆进验收，默认可人工勾选）**：  
  - 路线图不得同时存在「复跑未跑」与「#259 过线」两种未划线现行句。  
  - README 现状含 I3 与「过线未换臂」；不含「I3 未做」「已换 hybrid」。  
  - 架构总览含历史横幅；不再把 Auditor 列为与 Lead/Critic 同类的「三个真 Agent」作为现行句（可保留划线/历史注）。  
  - `PRODUCTION_RETRIEVAL_MODE` 仍为 `bm25`（本 diff 零改该赋值）。  
- **Prior art**：I3 默认臂断言测、各阶段 ACCEPTANCE 文首层标签、README「This README is not a certification」。  
- **本仓用户纪律**：未另要求则**不新写测试脚本**；Exit 用人工清单 +（可选）对禁止句的搜索。权威命令若跑：`python -m compileall -q src` 仅当第 4 批改了 `.py`。

**ACCEPTANCE 文首（预锁，禁事后改层身份）：**

```text
层身份：文档回填 / onboarding 口径。不是改臂授权；不是 L3 重测；
不是 checksum 全链激活；不是新功能阶段 Exit。
```

## Out of Scope

- 改 `PRODUCTION_RETRIEVAL_MODE`；宣称已换 hybrid/rerank  
- 重跑 `eval run --gold`、control/control-c、Hard-Gold dense 重建  
- 激活 fresh 半边 checksum；构造 `validity_basis`（ADR-0024 仍「另票」）  
- 默认 Lead 挂载 Forensic / 记忆卫生主链  
- 解冻 Studio；实装薄对话；C′ Word/Notion/开放 webhook  
- 新 ADR、新评估文档四件套（无新决议）  
- 选择 SPDX LICENSE；提交真实客户卷宗  
- 代关 / 代批改臂 Gate 实现票  
- 大改数据流图为「重画架构」；删除 W1–W4 历史规格  
- 为对齐而改闸谓词、金标、包结论枚举

## Further Notes

- **Seams**：主缝已于 2026-10-06 确认；不允许扩成改臂实现。  
- **DoD**：五票合上且满足各票 Acceptance；规格索引已挂本卷；无产品行为变化。  
- **工单（已拆、已 enrich 薄字段）**：`tasks/DOC-01.md` … `DOC-05.md`；索引 `.scratch/doc-align-tickets/INDEX.md`。GitHub 未发（工作区非 git 仓）。  
- **下一跳**：Frontier `DOC-01` 与 `DOC-04` 各开**新会话** `/before-implement <id>` → `/implement`。不要在本规格会话改产品文档正文。  
- **Trust**：默认 Watch；Blast none。人若要 Gate 请改工单字段。  
- **与盘点报告的映射**：高风险 1–2 = DOC-01–03；注释与卫星页 = DOC-04–05。
