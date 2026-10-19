# C1 Batch 0+1 预登记卡

- **状态**: 预锁定（grill-with-docs 2026-09-22 共享理解确认）
- **范围**: 仅 Batch 0（本卡）+ Batch 1（α + span + 检索失败提示 + 进度 UX）
- **非范围**: Batch 2–5、侧轨 R1、vector、W9/Memory UI、改 gold.json / 通过线凑绿
- **词表**: 见根目录 CONTEXT.md（客户向复验备忘、T1 来源三卡、主张导入稿、职人视图/审计视图）
- **ADR**: ADR-0015（客户向复验备忘字段集）、ADR-0016（T1 来源三卡与变更草稿确认入库）

## 纪律（Anthropic 清单合入）

1. 每条验收必须标层：demo / smoke / invariant / instrument；禁止跨层升格。
2. 失败只改实现，不改本卡判据；改判据 = 本批验收作废（HARKing）。
3. 解码参数若涉及 LLM 跑批须写明模型/温度/日期；本批 α-demo 以人工脚本与确定性检查为主。
4. Time-to-Sheet **只观测、不设硬通过线**。
5. 禁止升格句：不得把 α-demo 说成「产品已验证 / 一期测量闭合 / UX 证明了 latch」；latch 由 Void→Stay-Red / 闸证明。

## α-inv vs α-demo（分列）

### α-inv（invariant）

| ID | 判据 | 通过线 |
|---|---|---|
| INV-1 | Void→Stay-Red | 作废后重跑该 claim **不得** fresh；=100% |
| INV-2 | Client Memo 字段集 | 导出物含 ADR-0015 必填字段；**不得**含商业裁决句 |
| INV-3 | 禁止角色泄漏（备忘正文） | 客户向备忘正文不得出现 Lead/Critic 字样 |

### α-demo（demo）

| ID | 判据 | 通过线 |
|---|---|---|
| DEM-1 | Import Friction | ≥1 条非 JSON「主张导入稿」成功导入 |
| DEM-2 | T1 Clarity | 三卡可选；粘贴路径须「确认入库」后才可被 retrieve |
| DEM-3 | Client Memo rubric | 下列 5 条全「是」+ 禁止项全「无」（人工勾选，事后不加分项） |
| DEM-4 | 预算进度可见 | 复验中可见 Lead 步数/lead_max_steps 与 retrieve 次数/retrieval_budget |
| DEM-5 | 检索零命中提示 | UI 出现强提示；unknown 仍须 Lead 显式落档 |
| DEM-6 | 职人/审计视图 | 默认职人视图；可切换审计视图 |
| DEM-7 | Time-to-Sheet | 固定脚本走通一遍并记录分钟数；**不设 <10min 硬阈值** |

### Export Attachable rubric（DEM-3 预锁）

1. 有课题问题句与生成时间戳
2. 有免责声明（非法律意见 / 非自动决策；可标明 synthetic）
3. 三分栏齐全：仍成立 / 已作废 / 缺口
4. 每条有 claim_id + 一句话理由
5. 至少一条带可点回 evidence_id，或缺口栏显式写「无 T1 覆盖」

**禁止项：** 出现「建议进入/不进入」；默认备忘正文出现 Lead/Critic 字样。

## Batch 1 功能锁（与蓝图对齐）

- 引用 span：沿用 evidence_id（doc_id#anchor@as_of），不做字符级偏移
- 检索失败→unknown：Lead 经 mark_gap / reverify_claim(unknown) 为主；UI 零命中强提示（路径 C）
- 主张导入稿：## claim_id + 正文；缺 id → c-import-N
- JSON docket = 高级入口

## 本批指标行总表

| 指标 | 层 | 本批处置 |
|---|---|---|
| Void→Stay-Red | invariant | INV-1 |
| Client Memo rubric | demo | DEM-3 |
| Import Friction | demo | DEM-1 |
| T1 Clarity | demo | DEM-2 |
| Time-to-Sheet | demo | DEM-7 仅观测 |
| 预算进度可见 | demo | DEM-4 |
| 检索零命中提示 | demo | DEM-5 |
| Override Rate 等 | — | Batch 5+；本卡不锁通过线 |

## 下一步（Matt 最新流）

本卡与 ADR/设计文档落盘后：/to-spec → /to-tickets → 每票 /implement（/clear 间隔）。不要默认 /writing-plans。
