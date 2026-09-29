# Phase V1.5 — Evidence-bound / attested patches 规格

> 来源：`/grill-with-docs`（V1.5）共享理解 → `/to-spec`  
> 词表：`CONTEXT.md`  
> 权威 ADR：`0029`（Evidence-bound 补丁与独立确认 API）；上游 `0027`（包结论 / patch_events）、`0028`（不因三分法扩 HumanLatch）、`0006`（HumanLatch discard|renew）  
> 评估：`docs/research/V1.5-Evidence-bound补丁设计评估.md`  
> 路线图：`docs/roadmap.md` Phase V1.5  
> **测试主缝（已确认 2026-09-29）：Evidence-bound 确认边界** —  
> `可提案主张（未 discard 的 unknown|stale）+ after_text + t1_ids ⊆ 本 Run 已入库 T1 → confirm_patch → statement 原地覆盖 → 单条强制再验 → 重算包结论 → 追加 patch_events(arm=T, before_text/after_text, human_confirm=true, reverify=true) → 可导出 JSON+短 MD 包`  
> 子缝（仅当主缝测不到时）：① 资格闸；② propose 暂存零写；③ 导出包形状。**优先只暴露主缝。**

---

## Problem Statement

发前路径已能给出包结论「需补丁」，但顾问仍无法在复验单上**带着已入库 T1 改主张正文、确认后立刻再验、并带走证据包**。没有这条 Evidence-bound / attested 闭环，对客尖刀与论文路线 A 无法 demo；人审仍只有作废/续命，改稿与闩语义容易被混为一谈。

## Solution

在现有发前 Run / 复验单上增量交付 **表单式 Evidence-bound 补丁**：对未 discard 的 `unknown` 或 `stale` 主张提案改正文并勾选本 Run 已入库 `evidence_id`；人确认后 fail-closed 校验 ⊆ T1，原地覆盖 `statement`，强制单条再验并重算包结论，写入 `patch_events`（恒 `arm=T`，含 before/after），并导出 JSON+短 Markdown。独立 `propose_patch` / `confirm_patch`，不扩展 HumanLatch。本期不做薄对话；Exit 为冒烟层，不硬要包结论「可发」。

## User Stories

1. As a 独立顾问, I want 在复验单上对缺口主张提交带证改稿, so that 「需补丁」不是死胡同。
2. As a 独立顾问, I want 改的是整条主张正文而非 span 编辑器, so that 体验简单、不滑向编辑器秀。
3. As a 独立顾问, I want 确认前必须勾选已入库 T1 证据, so that 无证改稿进不了产品路径。
4. As a 独立顾问, I want 空 t1_ids 或非本 Run 归档 id 被拒绝且正文不变, so that fail-closed attested 成立。
5. As a 独立顾问, I want 确认后立刻对该主张再验, so that 「改完可再验」可演示。
6. As a 独立顾问, I want 再验后包结论自动重算, so that 列表/详情条与主张态一致。
7. As a 独立顾问, I want 一次补丁可导出 JSON 与短 Markdown, so that 证据可带走给客户或面试。
8. As a 独立顾问, I want 导出含 before/after、t1 指针、确认者、再验前后 disposition, so that 对客可读可追责。
9. As a 复验操作者, I want 只对未 discard 的 unknown 或 stale 看到补丁入口, so that fresh/void 不会被乱改。
10. As a 复验操作者, I want 已 discard 的主张走续命/重跑而非补丁, so that 闩与补丁分缝。
11. As a 复验操作者, I want 提案先暂存、未确认不改正文, so that 误点不会污染主张。
12. As a 复验操作者, I want 未确认不写正式 patch_events, so that 账本只记确认事实。
13. As a 复验操作者, I want 可丢弃未确认草案, so that 可重来。
14. As a 复验操作者, I want t1_ids 从本 Run 已入库 evidence_id 列表多选, so that 不靠手打字符串。
15. As a 复验操作者, I want 补丁条带挂在 Run 详情/复验单增量区, so that 不另开补丁台。
16. As a 复验操作者, I want 作废/续命按钮仍可用且语义不变, so that HumanLatch 不回归。
17. As a 复验操作者, I want 确认时可手填 minutes, so that 论文工时字段有值。
18. As a 复验操作者, I want patch_span 可自动默认（如 claim_id+正文替换）, so that 少填表。
19. As a 报告读者, I want 补丁不发明第四套 disposition 词, so that 仍只有可发/需补丁/勿发。
20. As a 报告读者, I want 主张级仍用 fresh/stale/unknown/void, so that 底层词表不漂。
21. As a 产品负责人, I want 发前 UX 无 C vs T 开关, so that 产品路径恒 attested。
22. As a 产品负责人, I want 产品写入 patch_events 时 arm 固定为 T, so that 与 ADR-0027/0029 一致。
23. As a 产品负责人, I want 本期不做薄对话（含 stub）, so that 路线图 In 不撒谎。
24. As a 产品负责人, I want 对话不得改正式 disposition, so that 硬规则成立。
25. As a 产品负责人, I want Exit 不硬要求包结论变「可发」, so that 不用单次 Gate 判生死。
26. As a 验收者, I want 硬 Exit 条为：无证拒确认 + 有证 confirm + reverify 触发 + 导出存在, so that 冒烟可勾。
27. As a 验收者, I want 升「可发」单独作为加分勾, so that 与硬条分离。
28. As a 验收者, I want 预锁演示脚本：discard mck-1 与 mck-4 → 需补丁 → patch mck-3 → 确认 → 单条再验 → 导出, so that 禁 HARKing。
29. As a 验收者, I want 证据落 docs/evidence/v15/ACCEPTANCE.md 且文首冒烟声明, so that 不升格统计。
30. As a 论文记录者, I want confirm 事件含 before_text 与 after_text, so that 账本与导出同源。
31. As a 论文记录者, I want C 臂仍可由脚本写同一账本, so that 对照实验可并行蓄数。
32. As a 论文记录者, I want n≥30 不挡本阶段产品 Exit, so that 楔子先可 demo。
33. As an 架构守护者, I want propose/confirm 独立于 HumanLatch 动词集, so that 不扩 discard|renew。
34. As an 架构守护者, I want 不用 renew 顺带改正文, so that 闩语义不被过载。
35. As an 架构守护者, I want 再验粒度为本条主张而非整包强制全跑, so that 冒烟成本可控。
36. As an 架构守护者, I want 生产默认检索臂仍为 bm25, so that 不借 V1.5 改臂。
37. As an 架构守护者, I want #8 Policy-as-code 本期不并行, so that 一人一条阶段。
38. As a 职人, I want 默认职人视图补丁入口用「改稿/确认/再验」语言, so that 不被 API 名淹没。
39. As an 审计者, I want 审计视图仍可看到事件与轨迹指针, so that 面试可切深。
40. As an AFK agent, I want 本规格可拆成带 Acceptance 的工单, so that 可按序实现。
41. As an 面试讲解者, I want 对外称 evidence-bound / attested patch 且少用 proof-carrying, so that 不撞形式化 PCC。
42. As an 面试讲解者, I want 禁止吹「首次带证据改稿」, so that 贡献边界成立。
43. As a 回归守护者, I want 既有 latch decide/rerun、disposition、发前列表回归不红, so that V1 不回退。
44. As a 回归守护者, I want I1 三分法标签与生产枚举仍分离, so that ADR-0028 不破。
45. As a 安全意识用户, I want 补丁引用的证据必须已入库, so that 未落盘 web 片段不能作证。
46. As a 文档维护者, I want README/路线图写明 V1.5 表单闭环与薄对话 Out, so that 叙事一致。

## Implementation Decisions

### 主缝与模块

- **主缝**：Evidence-bound 确认边界（见文首）。对外可测：给定合格输入 → 正文覆盖 + 再验触发 + disposition 更新 + T 臂账本行 + 导出包；非法 t1 → 拒确认且零改正文、零写正式账本。
- **补丁编排**：独立 Verify+ 用例服务（propose 暂存 / confirm 应用），**不**修改 HumanLatch `VALID_ACTIONS`。
- **资格闸**：仅 `unknown`|`stale` 且未 discard；`fresh`|`void`|已 discard → 拒提案/拒确认。
- **T1 硬闸**：confirm 时每个 `t1_id` 必须属于本 Run 已入库证据集合；空列表拒绝。
- **再验**：复用既有单主张重跑能力（与 latch rerun 同构粒度）；成功路径将事件 `reverify=true`；再聚合包结论（既有 disposition 纯函数）。
- **账本**：扩展既有 patch_events schema，正式 confirm 行必含 `before_text`/`after_text`；`arm="T"`；`human_confirm=true`；`minutes` 来自确认表单；`patch_span` 可自动默认。旧行缺 before/after 可读，新写入须齐。
- **导出**：confirm（或显式导出动作）产出同次补丁的 JSON + 短 Markdown；字段对齐 Exit/对客可读要求。
- **UX**：复验单/Run 详情增量条带；发前列表仅消费重算后的 disposition，不另造补丁台。
- **样例/Exit**：沿用 `v1-mck-soai`；ACCEPTANCE 预锁脚本见 ADR-0029。

### API / 契约（逻辑，不钉文件路径）

- `propose_patch`：输入 claim_id、after_text、可选 t1_ids 草案；校验资格；写入 Run/会话暂存；不改正文、不写正式 JSONL。
- `confirm_patch`：输入 claim_id、after_text、t1_ids、minutes、可选 patch_span；硬闸 → 覆盖 statement → 触发单条再验 → 重算 disposition → append patch_events → 返回新状态与导出句柄/载荷。
- `discard_patch_draft`（或等价）：清除暂存。
- 导出：按 patch 事件或 confirm 响应取得 JSON+MD。
- **禁止**：发前表面任何 arm=C|T 控件；薄对话端点；将 apply 并入 latch decide 的 action 枚举。

### 历史项目代码供参考 · 改编标注

| V1.5 能力 | 参考 | 处置 |
|-----------|------|------|
| 复验单增量表单条 | 本仓发前/复验单 UI（ADR-0002 / V1） | **以本仓为主**；只加补丁条带 |
| 确认后记账 | 本仓 `patch_events`（ADR-0027） | **扩展字段** before/after；产品路径写死 T |
| 单条再验 | 本仓 latch rerun | **复用粒度**；由 confirm 编排触发，不新造整包强制全跑 |
| 人审门闩 | HumanLatch discard\|renew | **不改动词集**；补丁另缝 |
| 列表壳 | V1 发前列表 | **只读 disposition 投影**更新 |

**必须重写 / 不得当默认抄入**

- 开放聊天改裁决、通用「AI 改稿」助手  
- 形式化 PCC / proof-carrying 对外主称  
- 把补丁做成第三种 latch 按钮或 renew 改正文  
- 编辑器秀 / span diff IDE

## Testing Decisions

- **好测试**：只断言主缝外部行为（无证拒确认且正文/账本不变；有证 confirm → 正文、reverify 标志、disposition、T 行、导出字段），不锁 CSS/像素与 LLM 品牌。
- **主测**：confirm 成功/失败表驱动；资格闸；propose 暂存零写；patch_events 含 before/after 且 arm=T；导出 JSON+MD 关键字段；既有 latch/disposition/prepublish/patch_events 回归不红。
- **Prior art**：`tests/unit/test_patch_events.py`、`test_prepublish_e2e.py`、`test_prepublish_list.py`、`test_ui_latch.py`、`test_disposition.py`；gate1 零 LLM CI——Exit 脚本中的真模型再验可为里程碑/手测加分，硬条用确定性夹具断言「再验已触发」与事件字段。
- **ACCEPTANCE**：实现后写 `docs/evidence/v15/ACCEPTANCE.md`（冒烟文首；硬条与加分勾分离；脚本预锁）。

## Out of Scope

- 薄对话（实装或 stub）；开放问答；对话改正式 disposition
- span 级 diff 编辑器；独立补丁台路由
- 扩展 HumanLatch 第三动词；renew 改正文
- 产品路径无证 C；发前 UX 上 C|T 开关
- Exit 硬绑包结论「可发」或 mck-3 必须 fresh
- 整包强制全量再验作为唯一路径
- #8 Policy-as-code 并行；Hard-Gold；改生产 retrieval 默认臂
- Studio；多垂直；用 V1.5 叙事替代 I1 冲 mid
- 吹「首次带证据改稿」或对外装形式化 PCC

## Further Notes

- **Seams 确认**：主缝「Evidence-bound 确认边界」已于 2026-09-29 用户确认。
- **DoD / Exit 对照路线图与 ADR-0029**：硬闸拒无证；有证 confirm；再验触发；导出可演示；`docs/evidence/v15/ACCEPTANCE.md`；升可发=加分。
- **下一跳**：`/to-tickets` → `/enrich-tickets` → `/before-implement` → `/implement`。  
- **规格 issue**：[GitHub #196](https://github.com/luxingjiang1993/FreshLatch/issues/196) `ready-for-agent`。  
- **I1 / V1**：已 DONE（冒烟）；本规格不得扩生产三分法枚举，不得宣称检索臂升格。  
- **决议工单**：grill 收口见 GitHub #195（CLOSED）。  
