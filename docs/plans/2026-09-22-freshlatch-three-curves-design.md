# FreshLatch 三曲线方向设计（2026-09-22）

Status: design snapshot after grill-with-docs Batch 0+1 shared-understanding lock  
Branch: eature/future-roadmap  
**Do not treat this file as an implementation ticket.** Next: /to-spec → /to-tickets → /implement.

## 0. 整合原则

1. 品类：复验闩 / 卖作废；不自动商业裁决；不接 Mem0 当卖点。
2. C2/C3 进实施必须服务 C1 指标、可标层、有触发；Pitch 不得压过「卖作废」。
3. RESEARCH 与产品报告出口分离（ACCEPTANCE「仅表明」vs 论文草稿）。
4. Anthropic：预登记 + demo/smoke/invariant/instrument 分层；α-inv ≠ α-demo。

## 1. Batch 0+1（本设计已钉死，见预登记卡与 ADR）

| 交付 | 路径 |
|---|---|
| 预登记卡 | [docs/research/C1-Batch0-1预登记卡.md](../research/C1-Batch0-1预登记卡.md) |
| ADR-0015 Client Memo | [docs/adr/0015-客户向复验备忘字段集.md](../adr/0015-客户向复验备忘字段集.md) |
| ADR-0016 T1 三卡 | [docs/adr/0016-T1来源三卡与变更草稿确认入库.md](../adr/0016-T1来源三卡与变更草稿确认入库.md) |
| 词表 | CONTEXT.md |

**Batch 1 功能包：** 主张导入稿 + T1 三卡 + Client Memo 导出 + 职人/审计视图 + evidence_id 点回 + 零命中提示 + 步数/retrieve 进度。

## 2. 第一曲线摘要（完整蓝图保留）

- 北极星旅程 S1–S6（P0）；S7–S8 P1；S9–S10 P2  
- 方案 α–ζ；推进序：预登记 → α（inv/demo 分列）→ β∥γ → δ → ε；ζ 维持  
- 详见会话蓝图；本文件以 Batch 排期为执行视图  

## 3. 实施批次总表

| 批次 | 内容 | 验收层 | 状态 |
|---|---|---|---|
| **Batch 0** | 本预登记卡 | 文档纪律 | **已落盘** |
| **Batch 1** | α + span(evidence_id) + unknown 提示 + 进度 UX | α-inv / α-demo | **待 /to-spec** |
| **Batch 2** | β checksum + 攻击面用例 | invariant | NEXT（可另会话并行） |
| **Batch 3** | γ + 消融/多 seed **规格** | invariant + smoke | NEXT |
| **Batch 4** | δ 第二课题 + 数据释放草稿 | 迁移预锁 | NEXT |
| **Batch 5** | ε 信任内嵌 + 对抗套件目录骨架 + override 管道 | 文案+管道 | **决策已齐**（#106–108；待 `/to-spec`） |
| **侧轨 R1** | must_quarantine 金标 | 研究 | RESEARCH |
| **不进** | 无触发 vector、HyDE、金标前 W9/真 Forensic、Mem0、换框架、主会真实对照 | — | REJECT/HOLD |

### NOW（已并入 Batch 1 或 2）

- 引用高亮 span → Batch 1（evidence_id）  
- 检索失败→显式 unknown → Batch 1  
- 步数/预算进度 UX → Batch 1  
- Auditor/维度加固 → Batch 3  
- checksum 攻击面 → Batch 2  

### NEXT

vector fuse（严触发）、parent-child、W9/真 Forensic（金标后）、续命建议、缺口聚类、消融实跑、多 seed 实跑、δ 研究版、override 动力学、合成数据释放协议。

### RESEARCH

System 文身份、假绿对抗套件（Batch 5 先目录）、Latch vs Retrieve、成本-安全曲线、negative result 可选、must_quarantine = R1。

## 4. Matt Pocock 最新流（本仓用法）

`
已完成: grill-with-docs（Batch 0+1）
下一步: /to-spec → /to-tickets → /implement（每票 /clear）
大图仍雾: /wayfinder（决策票）→ 再 /to-spec
不要默认: /writing-plans、/executing-plans
`

## 5. 一票否决讲法

- Time-to-Sheet 有数 = 产品验证成功  
- rubric 全过 = 客户会付费  
- UX 升级证明了 latch（错：Void→Stay-Red / 闸才证明）  
