# ε: override/void 事件管道字段设计评估

> **决议工单**: [ε: override/void 事件管道字段](https://github.com/luxingjiang1993/FreshLatch/issues/108)（地图 [#96](https://github.com/luxingjiang1993/FreshLatch/issues/96)）  
> **决议日期**: 2026-09-23（两轮 grilling，全采推荐）  
> **决议落点**: 本评估、ADR-0023、CONTEXT「override（派生标签）」  
> **上游**: ADR-0006 HumanLatch；`latch_log` / `invalidation_list` / `rerun_log`（spec 02）；void≠stale

---

## 1. 问题 + 前置约束

Batch 5（ε）：拍板 override / void（及必要 renew）事件管道的**字段集与时间线挂载**——谁产生、最小字段、与作废名单/卡片一致、审计可见；定 schema/契约，**不定**动力学模型或统计。

验收层：文案+管道（字段可机检；不声称 override 动力学已验证）。

| 前置 | 来源 | 锁死作用 |
|---|---|---|
| Agent 不得自把红改绿 | CONTEXT / ADR-0006 | 人审是唯一 L0 写路径 |
| void 是人的决定 | CONTEXT | discard → invalidation_list |
| 禁止 override⇒模型变好 | 票面勿重开 | override 非进步指标 |
| latch_log 已有 ts/claim/action/evidence/actor | spec 02 | 扩列优于新表 |
| Memo 禁轨迹 | ADR-0015 | 事件不进 Client Memo |

**Anthropic 命中**: #1 管道在场 ≠ 动力学验证；#2 禁单次 override 率当模型变好；合入「派生标签 + 无通过线」。

---

## 2–3. 候选与评估

| 维度 | 拍板 | 被否 |
|---|---|---|
| override 身份 | 派生 bool 标签，不新 action | 新 action=override；本批不建模 |
| 存贮 | 扩 `latch_log` | 新 `latch_events`；只 JSON 不定表 |
| 挂载 | 主张卡片时间线 + 审计可滤 | 仅审计；进 Memo |
| rerun | 仍 `rerun_log` 分立 | 统一事件流；本批只 void |

---

## 4. 拍板

### 4.1 action 不变

`VALID_ACTIONS = discard | renew`（现状）。**不**新增 `override` action。

### 4.2 override 谓词（派生）

写入人审成功结果时计算 `override: bool`：

| 条件 | override |
|---|---|
| `discard` 成功 ∧ `machine_status_before == fresh` | `true` |
| `renew` 成功 ∧ `machine_status_before ∈ {stale, unknown}` | `true` |
| 其他成功人审（含对非 fresh 的 discard、对 fresh 的 renew） | `false` |
| 失败 / 幂等跳过 | 不写新行或 `override` 不适用（实现 to-spec 钉：幂等 discard 跳过则不新增对抗语义行） |

**硬禁**: 把 override 计数下降解释为「模型变好」；不得设 Override Rate 通过线（C1 已推迟，本票继续不锁）。

### 4.3 `latch_log` 扩列（契约）

| 字段 | 必填 | 说明 |
|---|---|---|
| `ts, claim_id, action, evidence_id?, actor` | 沿用 | 现有 |
| `machine_status_before` | **必填**（人审写路径） | 落档前机器 status |
| `override` | **必填** bool | 按 §4.2 派生 |
| `run_id` | 可选 | 有则填 |
| `reviewer_note` | 可选 | 与 discard reason 对齐 |

`invalidation_list` 仍为作废**单一真相**（claim_id, voided_at, actor, reason?）。  
`rerun_log` 不并入本管道。

### 4.4 时间线

- 主张卡片：展示人审时间线条目（含 override 标记可选显式）。  
- 审计视图：可过滤 `override=true`。  
- Client Memo：**不**投影事件流。

### 4.5 ADR-0023

钉「派生标签 + 扩 latch_log + 禁动力学升格」。

---

## 5. 工程手段总登记册

| 手段 | 原理 | 优势 | 代价 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| override 派生标签 | 审计标签≠新动词 | 禁模型变好叙事 | 谓词要测 | HumanLatch | **实装**（契约） |
| 扩 latch_log | 唯一写路径延续 | 少表 | 迁移列 | spec 02 | **实装**（契约；代码 **触发** to-spec） |
| 卡片+审计双挂 | 职人可见/审计可滤 | 对齐 void 灰显 | UI 工 | K4 时间线 | **触发** |
| 新 override action | 表面清晰 | — | 与 discard/renew 双轨 | — | **弃** |
| 进 Memo | 客户可见对抗 | — | 破 ADR-0015 | — | **弃** |
| Override Rate 通过线 | 早出数 | — | 动力学未定义+升格 | C1 | **弃**（本批） |

---

## 6. 面试讲法

**Q:override 是不是说明模型错了、后来变好了？**  
A:不是。override 只标记「人这次决定与落档前机器 status 对抗」。禁止用它的频率讲模型变好。动力学是 NEXT，本批只锁字段。

**Q:为什么不作废名单里写 override？**  
A:作废名单回答「哪些 id 永不得再绿」；override 是审计迹属性。单一真相不混。
