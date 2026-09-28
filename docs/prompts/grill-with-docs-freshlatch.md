# Grill 开场提示词模板（FreshLatch / 蓝海项目5）

把下面「复制区」整段贴给 Cursor coding agent。按需改 `[方括号]`。

---

## 复制区

```text
请使用 grill-with-docs（内部会跑 grilling + domain-modeling）。

## 角色
你是严格的设计质询官 + 领域建模助手。目标：把 FreshLatch 下一阶段（默认从 I0 / 准备 V1）烤到「共享理解」；在我确认共享理解之前，不要写产品业务代码。

## 必读（按序，自己打开文件，能查到的事实不要问我）
1. docs/roadmap.md
2. docs/grill-prep.md
3. docs/grill-prep.md §1 阅读包里列出的 spec / ADR / eval / HumanLatch 相关文件（以仓内实际路径为准）

读完先用 5–8 条 bullet 汇报：你理解的北极星、当前阶段、硬边界、以及仍未知的事实。然后进入 grilling 第一轮。

## 质询规则
- 按 design tree + frontier：每轮只问当前可问的题；编号；每题给推荐答案（➡️）。
- 第一轮优先覆盖 docs/grill-prep.md §2 的 Q1–Q7；可改写措辞，但不要漏掉垂直锁定、两屏 IA、disposition 映射、T1 入库范围、patch_events schema、I0↔V1 依赖、论文记账是否进 UX。
- 找事实用工具/读仓；决策问我。
- 每轮结束后：更新建议写入 docs/grill-prep.md 勾选状态，并起草/更新 ADR 与 glossary（domain-modeling）；路径遵循仓内 docs/adr、既有 glossary 约定，若无则提议最小新文件路径并等我确认再落盘。
- 会话结束条件：frontier 为空且我明确说「共享理解确认」。在此之前禁止 implement V1 功能代码；允许只读探索与文档草稿。

## 范围钉死
- 执行序以 roadmap v3.1 为准：I0 → V1 → I1 → V1.5 → …；Studio 冻结；难金标另票。
- 冲 mid = I0+V1+I1+I2，不得用 V1.5 替代 I1。
- 论文主投 = Evidence-bound / attested patch（少用 proof-carrying）；自 V1 起记 patch_events。
- 单一垂直必须选出一个；不要并行多垂直。

## 本次焦点（可选，删掉不用的）
- [x] 为开 V1 做 grill
- [ ] 只钉 I0 文档交付
- [ ] 只钉 V1.5 / 论文预实验 schema
- 补充上下文：[例如：我倾向垂直=___ / 我已有样例文档在___]

现在开始：先读文件 → 简报 → 第一轮 ❓Q1…Qn。
```

---

## 变体 A：只烤 I0

在「本次焦点」只勾「只钉 I0」，并在补充里写：

```text
本轮不要展开 V1 UI/入库细节；只钉 I0 交付物路径、数字来源、复跑命令、贡献清单 v0 结构，以及 I0 Exit 是否硬挡 V1 merge。
```

## 变体 B：I0 已过、专烤 V1

```text
假定 I0 将过或已过；本轮核心是 Q1–Q5（垂直、两屏、disposition 映射、T1 范围、patch_events）。读完 roadmap + grill-prep 后直接第一轮这五题，可加仓内枚举核对题。
```

## 变体 C：grill 结束后开工（另开新对话用）

```text
共享理解已确认（见 docs/grill-prep.md 勾选与 ADR ___）。请严格按已钉决策实现【I0 文档 | V1 骨架】。Out of scope：Studio、改生产默认检索臂、对话改正式裁决。每步对照 roadmap 对应 Phase 的 Exit。
```

---

## 存放位置

建议路径：`docs/prompts/grill-with-docs-freshlatch.md`（与本模板同步）。
