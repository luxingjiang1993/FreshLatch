# Phase I3 — 面试加固三轨（#8 · B′夹具 · Hard-Gold骨架）规格

> 来源：`/grill-with-docs`（I3）共享理解 → `/to-spec`  
> 词表：`CONTEXT.md`  
> 权威 ADR：`0032`（政策旁路 · B′ 夹具 · Hard-Gold 骨架不改臂）；上游 `0003`/`0026`（增益门与默认臂）、规则闸族、`0030`（旁路思维）、`0031`（禁整包再验挂钩子）  
> 评估：`docs/research/I3-面试加固三轨设计评估.md`  
> 路线图：`docs/roadmap.md` Phase I3  
> **测试主缝（已确认 2026-10-03）— 三轨分列，互不顶替；实现序 #8 → B′ → Hard-Gold → DoD：**  
> 1. **政策拒旁路** — 声明式出处禁区经 Verify+ 旁路装入 → 命中不得绿灯（**政策拒**）；**不**改写 `rule_gate` 不变量语义  
> 2. **B′ 假绿可见** — 合成超时/假绿 → 结构化错误可见（不静默绿）；人审动作重放 → 不双写坏账；轨迹 → 闸分布一页（CLI 或 MD）  
> 3. **Hard-Gold 骨架** — `retrieve_hard_gold`（n≥20，traps/对抗≥30%）可跑 + 分列增益报告 + **断言 `PRODUCTION_RETRIEVAL_MODE == "bm25"`**  
> 子缝（仅主缝测不到时）：规则文件 schema；观测页字段形状；Hard-Gold 规格文档落盘；`docs/evidence/i3/ACCEPTANCE.md` 分节。**优先按票序暴露主缝，禁止用一轨 Exit 顶替另一轨。**

---

## Problem Statement

主链 Verify+ 冒烟已齐，但冲 mid 仍缺三句可指认的加固弹药：(1) **政策拒**——声明式禁区能拦绿灯，且与新鲜度拒分语义；(2) **演示不假绿**——超时/重入有结构化失败与可观测闸分布，而非静默绿或坏账；(3) **检索数字诚实**——难金标骨架与增益门可跑，同时明确**未授权换臂**。三者现散落 Backlog，若分开空转或糊成一票，会分别踩「无 Trigger 空开 B′」「冒烟当 Hard-Gold」「#8 改写 rule_gate」等坑。

## Solution

交付 **Phase I3 一阶段三轨**（冒烟 / 面试加固）：

1. **#8 Policy-as-code（thin）**：声明式规则文件；首条 = **出处禁区**；Verify+ **旁路** → 政策拒 ≥1 可复现；不做 OPA/Cedar。  
2. **B′ 夹具**：timeout / 结构化错误 / 人审串行幂等（薄）+ 闸分布一页；合成夹具，不声称修真事故。  
3. **Hard-Gold 骨架**：完整规格 + 分文件难金标 + 增益报告；**本波不改**生产默认臂。

证据落 `docs/evidence/i3/ACCEPTANCE.md`（文首层标签强制；三轨分节）。

## User Stories

### 轨 A · Policy-as-code（#8）

1. As an 面试官, I want 看到出处禁区命中后不得绿灯, so that 「政策拒」可指认。
2. As an 面试官, I want 政策拒与 stale/unknown/元陈述拒分语义可讲, so that 不与新鲜度闸糊在一起。
3. As an 架构守护者, I want 禁区经旁路装入而非改写 rule_gate 不变量正文, so that 既有闸回归不破语义。
4. As an 架构守护者, I want 规则以声明式文件加载, so that 可预登记、可复现。
5. As an 架构守护者, I want 本期无 OPA/Cedar/政策平台, so that 不违 Out。
6. As a 语料作者, I want 已入库 T1 仍可被出处政策拒支撑绿灯, so that 「入库≠可绿」成立且与薄 URL 白名单正交。
7. As an 验收者, I want ≥1 条可复现政策拒夹具进确定性测, so that 口头不算。
8. As an 验收者, I want ACCEPTANCE #8 分节勾选且不与 B′/Hard-Gold 互顶, so that 三轨分列。

### 轨 B · B′ 夹具

9. As an 面试官, I want 故意超时/假绿夹具给出结构化错误而非静默绿, so that 可靠性故事可演。
10. As an 面试官, I want 人审动作重放一次不双写坏账, so that 重入可讲。
11. As an 面试官, I want 从轨迹生成一页闸分布（CLI 或 MD）, so that 「说清闸」有锚。
12. As a 产品负责人, I want 文档标明合成夹具、不声称修过真生产事故, so that 不装 B′ 真 Trigger 复盘。
13. As a 产品负责人, I want 不做 Memory/多 Agent/跨 Provider 硬关门, so that 守 roadmap Out。
14. As an 架构守护者, I want 不把整包再验挂回发前钩子, so that ADR-0031 不破。
15. As an 验收者, I want B′ 三硬条（结构化错误 · 重入 · 观测页）分列可勾, so that 不互顶。

### 轨 C · Hard-Gold 骨架

16. As an 面试官, I want 难金标与冒烟 retrieve_gold 分文件, so that 层不糊。
17. As an 面试官, I want hard gold n≥20 且 traps/对抗类≥30% 预登记可指, so that 禁 HARKing。
18. As an 面试官, I want 分列臂报告 + 增益门判决可复跑, so that 与 I0 叙事连续。
19. As an 架构守护者, I want Exit 断言 PRODUCTION_RETRIEVAL_MODE 仍为 bm25, so that 骨架≠换臂。
20. As an 架构守护者, I want Hard-Gold 规格文档落盘且文首声明本波不改臂, so that ADR-0026 纪律可见。
21. As an 验收者, I want 禁止把 n=36 冒烟表称作 Hard-Gold 已过, so that 不升格。
22. As an 验收者, I want 不报检索方差/统计显著, so that 层身份诚实。

### 联合 / 纪律

23. As a 产品负责人, I want 实现序为 #8 → B′ → Hard-Gold → DoD, so that 一人一条且先拿最快 demo。
24. As a 产品负责人, I want 不解冻 Studio、不开 C′/图谱/CMS、不 High-Recall 改默认, so that Out 成立。
25. As a 产品负责人, I want 不用 I3 叙事替代 I1/I2 冲 mid, so that 安全与失败样本仍算铁证。
26. As an 验收者, I want docs/evidence/i3/ACCEPTANCE.md 文首强制冒烟/面试加固层标签, so that 对齐 ADR-0026 模板。
27. As an 验收者, I want 联合 DoD 仅当三轨硬条均 pass, so that 互不顶替。
28. As a 回归守护者, I want 既有 rule_gate / retrieve 冒烟 / HumanLatch / publish-hook 回归不红, so that 主链不回退。
29. As an AFK agent, I want 本规格可拆成带 Acceptance 的工单, so that 可按序实现。
30. As an 面试讲解者, I want 能讲清政策拒≠新鲜度拒、Hard-Gold 骨架未换臂、B′ 夹具非事故复盘, so that mid 不被打穿。
31. As a 文档维护者, I want README/路线图写明 I3 In/Out/Exit 与改臂另决议, so that 叙事一致。
32. As a CI 守护者, I want #8 与 B′ 硬门及 Hard-Gold 默认臂断言进零 LLM 可跑测, so that 无 Key 也能验。

## Implementation Decisions

### 主缝与模块

- **主缝 1（政策拒旁路）**：新建旁路加载器（模块名实现自洽）读声明式规则（建议 YAML/JSON，至少支持出处域名/路径模式）；在绿灯出口路径上于既有 `rule_gate` **之后或旁路组合点**施加政策拒，使命中不得 `fresh`/不得包级装可发（实现选点须保证：不修改 `rule_gate` 内既有不变量谓词正文）。确定性夹具 ≥1。  
- **主缝 2（B′ 假绿可见）**：在 runner/人审路径增加超时 → 结构化错误（可见 code/message）；人审 discard/renew（或等价）重放幂等不双写；提供轨迹→闸分布一页（CLI 子命令或写 MD）。合成夹具，文档标「非真事故」。  
- **主缝 3（Hard-Gold 骨架）**：新增 `data/eval/retrieve_hard_gold.json`（文件名可微调，须与 smoke gold **分文件**）；规格落 `docs/`（可挂 `docs/eval-retrieve.md` 扩节或独立 `docs/hard-gold.md`）；评测入口复用/扩展 `python -m freshlatch.eval retrieve` 能跑 hard 集并出分列报告；测试断言 `PRODUCTION_RETRIEVAL_MODE == "bm25"`。  
- **证据**：`docs/evidence/i3/` — ACCEPTANCE 分节 `#8` / `B′` / `Hard-Gold` / 联合 Out 勾选。  
- **票序硬约束**：合并顺序与依赖 = #8 → B′ → Hard-Gold → DoD；后票不得改前票已锁 Exit 口径。

### API / 契约（逻辑，不钉文件路径）

- `load_policy_rules(path) → rules`  
- `apply_policy_gate(claim|decision_ctx, rules) → allow|政策拒(+code)`（挂 Verify+ 旁路）  
- `run_with_timeout_structured(...)` / 错误形状含稳定 `error_code` + 短中文  
- `render_gate_distribution(trajectory|run_id) → md|stdout`  
- `python -m freshlatch.eval retrieve --gold hard`（或等价旗标）→ reports 分列 + 增益判决  
- **禁止**：改 `PRODUCTION_RETRIEVAL_MODE`；OPA SDK；把禁区 if 塞进 `rule_gate` 不变量函数体内改语义；导出前整包再验挂钩子。

### 历史项目代码供参考 · 改编标注

| I3 能力 | 参考 | 处置 |
|---------|------|------|
| 绿灯出口 | `rule_gate` / `_finalize` | **旁路组合**；不改不变量正文 |
| 人审幂等 | `human_latch` discard 幂等跳过 | **复用/加薄**重放夹具 |
| retrieve 评测 | `freshlatch.eval retrieve` / smoke gold | **扩 hard 集**；分文件 |
| 增益门 | `docs/eval-retrieve.md` / ADR-0026 | **复跑**；不改公式装换臂 |
| 元数据旁路思维 | I2 poison 剔除 | **类比**政策旁路，不同语义 |

**必须重写 / 不得当默认抄入**

- 完整政策引擎 / RBAC 平台  
- 把 smoke `retrieve_gold` 扩成「难」却不分文件  
- Memory/多 Agent 硬化作 Exit  
- 本波改生产默认臂  

## Testing Decisions

- **好测试**：只断言三主缝外部行为；零 LLM 硬门覆盖 #8 政策拒、B′ 结构化错误/幂等、Hard-Gold 默认臂断言与 hard 集可跑（若 dense 不可用，分列臂按 I0 纪律标需索引，**不得**因此改臂）。  
- **主测**：出处禁区命中→非绿；未命中不误伤既有 fresh 路径（回归）；超时夹具→结构化错误；latch 重放行数/名单不双写；观测页含闸码计数；hard gold 加载 n≥20；`PRODUCTION_RETRIEVAL_MODE=="bm25"`。  
- **Prior art**：`test_*rule_gate*`、`test_*latch*`、`test_*retrieve*`、I0 reports 复跑、I2 旁路测。  
- **ACCEPTANCE**：文首强制：

```text
层身份：冒烟 / 面试加固（I3）。不报方差；不作统计显著；
不是改生产默认臂授权；不是政策平台已交付；不是已修真生产事故。
```

Hard-Gold 分节额外：`本波 Hard-Gold = 骨架语料 + 增益门复跑；未授权改臂。`

## Out of Scope

- 改 `PRODUCTION_RETRIEVAL_MODE`；宣称 Hard-Gold 已授权换臂  
- OPA/Cedar / 政策平台；改写 `rule_gate` 不变量语义  
- Memory 大叙事、多 Agent 拓扑、跨 Provider 对照作硬关门  
- 解冻 Studio；C′ 插件平台；图谱/CMS；High-Recall 改默认  
- 用 I3 替代 I1/I2 冲 mid；报方差/统计显著  
- 导出前整包再验挂回发前钩子  
- 主张模式禁区 / 时间禁区（留位，非本波硬条）  
- High-Recall SKU 实装  

## Further Notes

- **Seams 确认**：三主缝已于 2026-10-03 共享理解确认；优先按票序暴露。  
- **DoD / Exit**：对照 roadmap Phase I3 与 ADR-0032；三轨硬条 + `docs/evidence/i3/ACCEPTANCE.md`。  
- **下一跳**：`/before-implement` → `/implement`（Frontier [#249](https://github.com/luxingjiang1993/FreshLatch/issues/249)；子票 #249–#253 · `.scratch/i3-tickets/INDEX.md`）。  
- **规格 issue**：[GitHub #248](https://github.com/luxingjiang1993/FreshLatch/issues/248) `ready-for-agent`。  
- **决议**：grill 四件套已落（评估 + ADR-0032 + CONTEXT + roadmap）；本规格为实现权威用户故事面。  
- **命名注意**：idea **#8** = Policy-as-code；历史「语料金标工单 #8」不是本物，开票须写全称。
