# 生产补丁 / 放行 SLO · 运营纪律规格

> 来源：`/grill-with-docs`（生产补丁/放行 SLO）共享理解 → `/to-spec`  
> 词表：`CONTEXT.md`（生产补丁/放行 SLO · 实验—生产防火墙）  
> 权威 ADR：`0034`；上游 `0029`（Evidence-bound）、`0031`（发前钩子）、`0023`（override）、`0006`（HumanLatch）  
> 评估：`docs/research/生产补丁放行SLO设计评估.md`  
> 运营真源：`docs/ops/生产补丁放行SLO.md`  
> **测试主缝（已确认 2026-10-09）：运营指标分层与实验防火墙** —  
> `硬闸不变量(无证/未确认出门/自红转绿/无T1绿灯) + 观测周报字段(改对/误放误拒成对/作废/override/再验失败) + 离线 must_stale multi-run + 禁止回写 RESULT-Y/金标进生产 score → 同一纪律页可勾选`  
> 子缝（仅当主缝测不到时）：① 抽检协议表形状；② 周报聚合导出；③ 硬闸违例计数脚本。**优先只暴露主缝。本期不写业务代码直至 before-implement。**

---

## Problem Statement

发前闭环已能补丁、人审与发前钩子，实验侧也有固定 k 误放尺，但生产几乎没有可执行的数字 SLO。路线 Y 主跑结果丙表明「过闸≠改对」。若继续只盯实验成立格或口头约定，运营无法双管（改质量 + 放行纪律），也容易把生产变绿误写成实验乙。

## Solution

交付 **生产补丁/放行 SLO 纪律页** 与可拆观测票：分层（硬闸 / 观测 / 离线评测 / 实验-only）、起步阈值预注册、采集点与周报最小字段、与 RESULT-Y 丙的防火墙。北极星仍是 must_stale 与作废率。本规格授权文档与观测脚手架票，**不**授权改 Y 预注册/结果，**不**把金标当在线放行器。

## User Stories

1. As a 产品负责人, I want 一份运营真源列出改/放行/人审/复验指标, so that 团队不靠口头约定。
2. As a 产品负责人, I want 硬闸与观测分层写清, so that demo 不冒充总体测量。
3. As a 产品负责人, I want 明确生产变绿不得改判 RESULT-Y, so that 实验丙不被 HARKing。
4. As a 顾问用户, I want 无证补丁仍被拒绝, so that attested 名副其实。
5. As a 顾问用户, I want 未确认的草案不能改正文或当正式出口, so that 未确认不出门。
6. As a 顾问用户, I want Agent 不能自己把红灯改回绿灯, so that HumanLatch 自治成立。
7. As a 顾问用户, I want 续命必须带新 T1, so that 绿灯有原文。
8. As an 运营值班, I want 每周能填改对率抽检与错改率, so that 过闸≠改对可被看见。
9. As an 运营值班, I want 再验失败率可周报, so that 知道改完仍救不了的比例。
10. As an 运营值班, I want 误放与误拒成对出现, so that 少放不能装安全。
11. As an 运营值班, I want 作废率与 override rate, so that 人审分权可观察。
12. As an 运营值班, I want 导出前钩子拦截次数, so that 有事故前哨。
13. As an 评测负责人, I want must_stale multi-run 不低于当前金标门, so that 复验主业不退化。
14. As an 评测负责人, I want 金标不进生产 score, so that 无法刷分。
15. As an 评测负责人, I want must_fresh 不误杀被跟踪, so that 全红假象可防。
16. As a 论文作者, I want 固定 k / T−C 留在实验-only, so that 层身份不糊。
17. As a 论文作者, I want 文面禁止接近乙/软甲/主实验成功（对 Y）, so that 投稿映射不崩。
18. As a 安全意识用户, I want 无 T1 绿灯次数目标为 0, so that 假绿出口被钉死。
19. As a 架构守护者, I want 证据对不上不得 confirm 写进纪律, so that A2 不只是抽检愿望。
20. As a 架构守护者, I want 不单独用放行率升高当成功, so that B1 不被滥用。
21. As an AFK agent, I want 本规格拆成带 Acceptance 的票, so that 可 before-implement。
22. As an 验收者, I want 起步阈值预注册且事后改门槛=作废, so that 防 HARKing。
23. As an 验收者, I want 周报最小字段清单, so that 观测可勾。
24. As a 文档维护者, I want ADR-0034 与 ops 页互指, so that 权威不漂。
25. As a 面试讲解者, I want 能讲清丙之后为何仍做生产 SLO, so that 双管叙事成立。
26. As a 回归守护者, I want 本规格不要求改生产默认检索臂, so that Hard-Gold 纪律保留。
27. As a 回归守护者, I want 不扩 HumanLatch 动词, so that 与 ADR-0029 分缝。
28. As a 成本意识用户, I want 补丁确认耗时可观测, so that 人时可见。
29. As a 包结论读者, I want 可发/需补丁/勿发分布周报, so that 负载可见。
30. As a 双管设计者, I want 验收包最低集写进 ops 页, so that 另页扩面有锚。
31. As a Cloud agent, I want 本波禁止写业务代码直至人批 before-implement, so that 不抢 Gate。
32. As a tracker 维护者, I want 每票含 ID/Acceptance/Paths/必要 Provenance, so that Agent Guards 可 enrich。
33. As a 读者, I want 规格 Out 写明不改 Y 成立格, so that 范围钉死。
34. As a 读者, I want 不放宽甲定义、不用金标当在线放行器写进 Out, so that 硬约束可见。
35. As an 观测实现者, I want 采集点落在既有 propose/confirm、latch_log、publish_hook、eval runner, so that 少造平行账。
36. As an 观测实现者, I want 优先文档与计数脚手架而非大屏 UI, so that 本期不超额。
37. As a 抽检标注者, I want A3 严重错改定义与会害客户对齐, so that Watch 线可讨论。
38. As a 抽检标注者, I want 样本不足时诚实写「本周样本不足」, so that 不编数字。
39. As a 地图维护者, I want Decisions-so-far 能链到本评估, so that 决议可追溯。
40. As a 未来决议者, I want 升 &lt;5% 为 Gate 须另决议, so that 样本协议齐备前不假 Gate。

## Implementation Decisions

### 主缝与模块

- **主缝**：运营指标分层与实验防火墙（见文首）。对外可验：ops 页 + 规格 + ADR 互指完整；硬闸项有采集点；周报字段可填或诚实「未跑/样本不足」；文面零回写 Y / 零金标进生产 score。
- **真源**：`docs/ops/生产补丁放行SLO.md` 为指标与阈值单一真相；本规格描述行为与拆票边界，不复制全表数字以免双写漂移（阈值变更只改 ops 页并留修订注）。
- **硬闸承载**：复用既有 `confirm_patch` fail-closed、未确认不入正式 `patch_events`、HumanLatch、rule_gate 无 T1 不得 fresh、publish_hook。本期票可加**违例计数/清单**，不改闸语义 unless 另 Gate 票。
- **观测票**：抽检表、周报聚合、override/作废率查询、再验失败聚合——优先只读既有账本（`latch_log`、`patch_events`、disposition、publish_hook 结果）。
- **离线评测**：must_stale multi-run 走既有 eval/gold 轨；结果进 reports/evidence，**不**写入生产放行路径。
- **实验**：B4/B5/E* 只读指针；禁止本规格打开 PREREG-Y/RESULT-Y/formal-generations-y 编辑。

### 分层与阈值

- 分层词汇与起步阈值以 ops 页 §1/§4 为准（2026-10-09 预注册）。
- 严重错改 Watch 线 &lt;5%：观测-only；升 Gate 另决议。
- 随机评测：multi-run；n 小框定为冒烟，不报总体方差。

### 测试主缝优先

- 文档一致性机检（链接存在、禁词扫描、ops/ADR/评估互指）可作为第一批 Acceptance。
- 硬闸回归复用既有测试；新测只断言计数/清单，不放宽闸。
- 不把「放行率升高」写成绿灯断言。

## Testing Decisions

- 好测试只看纪律缝外面的行为：给定事件流或文档状态，硬闸违例可计、观测字段可产出或诚实空、防火墙禁词与禁路径成立。
- 优先测：无证拒、未确认不出门、自红转绿禁令、无 T1 绿灯禁令、金标不进生产 score 的文档/代码路径扫描。
- 不测：RESULT-Y 数字变绿；实验缩臂显著；大屏 UI。
- Prior art：`docs/evidence/v15/`、`v2/` 冒烟层标签；ADR-0023 override 不作通过线。

## Out of Scope

- 修改 `PREREG-Y` / `RESULT-Y` / `formal-generations-y` 或同页二跑凑乙。
- 放宽「甲」定义；禁止称软甲 / 接近乙 / 主实验成功（对 Y）。
- 金标作为在线放行器或生产 score 特征。
- 以单独放行率升高为成功标准。
- 本波业务功能大改（补丁算法、检索臂、HumanLatch 新动词、Studio）。
- 大屏运营产品 UI。
- 把评测加严阈值写入 `CONTEXT.md`。
- before-implement 人批之前写业务代码。

## Further Notes

- 决议四件套：评估 · ADR-0034 · CONTEXT · 地图/关单评论（GitHub 写权限若不可用则本地地图草稿 + PR 说明）。
- 票意向：改（A3/A4/A2/A6）· 放行（B2/B3/B6/B7）· 人审（C1/C2/C3）· 复验（D1/D3/D4）· 文档边界。
- 双管机制大改冲实验尺：必须另开预注册页，不在本规格。
