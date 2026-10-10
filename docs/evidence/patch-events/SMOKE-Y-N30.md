# SMOKE-Y-N30 冒烟报告（可扔）

> **可扔 · 冒烟层 · 不作过门 · 不保证乙 · 不进 RESULT-Y。**
> n=30 冒烟只描述本 30 条上的仪器与方向可读性；区间只描述这 30 条重抽样噪声，**不**写成总体结论，**不**进 RESULT-Y 成立格，**不**单独构成 `gate_passed`，**不**保证乙。
> 本页**不**激活 `PREREG-Y`；**不**填 RESULT-Y 成立格；**不**升格 `gate_passed`。
> **层身份**：冒烟（合成/夹具可；本票不发正式主跑）。

## 协议针（跑前写死）

- **n** = 30（冒烟；非正式 n=400）
- **bootstrap seed** = `20261007`（只描述这 30 条重抽样噪声）
- **代码针**：#529 PE-Y-SMOKE-01
- **输入来源**：确定性合成三臂记录（本票不发正式主跑）
- **选取**：R（固定 k = T 自然放行数；T/B1/B2 按 score；C 走 coverage_c）

## 必看字段

### T 自然 k

- **k** = `16`

### T−C 固定 k 差点估计方向

- **点估计** = 0.375
- **方向** = `positive`（`positive` 表示点估计 > 0；冒烟只报方向，**不**构成 `gate_passed`）

### T/B1/B2 fixed-k claim_id 集（坍缩检测）

- **T**：`smoke-000, smoke-001, smoke-002, smoke-004, smoke-006, smoke-008, smoke-010, smoke-012, smoke-014, smoke-016, smoke-018, smoke-020, smoke-022, smoke-024, smoke-026, smoke-028`
- **B1**：`smoke-001, smoke-002, smoke-004, smoke-005, smoke-007, smoke-008, smoke-010, smoke-011, smoke-013, smoke-014, smoke-016, smoke-017, smoke-019, smoke-020, smoke-022, smoke-023`
- **B2**：`smoke-029, smoke-028, smoke-027, smoke-026, smoke-025, smoke-024, smoke-023, smoke-022, smoke-021, smoke-020, smoke-019, smoke-018, smoke-017, smoke-016, smoke-015, smoke-014`
- **collapse** = `false`（三臂 fixed-k `claim_id` 集完全相同则为 true）
- **stop** = `false`（`collapse=true` → 停；不得激活 / 不得进探针升格）

### score 卫生

- **ok** = `true`
- None 混进可排序池：`[]`
- reject 非 −∞：`[]`
- release 非有限：`[]`

### B1/B2 差（必报 · 不过条件）

| 对比 | 点估计 | 进冒烟停条件？ | 进 gate_passed？ |
|---|---:|---|---|
| T−C | 0.375 | 否（只报方向） | **否** |
| T−B1 | 0.4375 | **否** | **否** |
| T−B2 | 0.4375 | **否** | **否** |

> B1/B2 差**必报**，**不**作冒烟通过/停条件以外的过门条件；停条件仅 `collapse=true`。

## 层身份断言（防火墙）

| 断言 | 值 |
|---|---|
| `constitutes_gate_passed` | `False` |
| `enters_result_y` | `False` |
| `guarantees_yi` | `False` |
| `writes_population_ci` | `False` |
| PREREG-Y 激活 | 否（本页不写激活批注） |
| RESULT-Y 成立格 | 未写 |

## 结论

- 本页未检出三臂 fixed-k 坍缩（`collapse=false`）。
- 即便方向可读，本页**仍不**构成 `gate_passed`，**不**保证乙。
- 后续仍须敏感性 ∧ 真数据 GATE-Y ∧ 人令；本 Cloud Agent 不激活。

## 边界

- 可扔；不进 RESULT-Y；不单独构成 `gate_passed`；区间不写总体；不保证乙。
- 不改正式 n / 成立尺（点>0.05）；不回写 B/C；不另开 Z；金标不进 score。
- 入口：`PYTHONPATH=src python -m freshlatch.eval.patch_events_smoke_y`
