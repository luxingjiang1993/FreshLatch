# Batch 1 α 验收记录(#94)

> **预登记唯一真相**:`docs/research/C1-Batch0-1预登记卡.md`  
> **本文件**:确定性套件执行记录。失败只改实现,不改预登记判据。  
> **测口**:Latch/Gate 套件 + Client Memo 导出契约;**不用** `freshlatch.eval` 主跑、**不改** gold / 通过线 / 假绿统计主口。

## 禁止升格句

不得把 α-demo 说成「产品已验证 / 一期测量闭合 / UX 证明了 latch」;latch 由 Void→Stay-Red / 闸证明。

---

## α-inv(invariant · 确定性通过线)

| ID | 判据 | 通过线 | 测口 | 结果 |
|---|---|---|---|---|
| INV-1 | Void→Stay-Red | 作废后该 claim 经 fresh / renew / rerun→Lead fresh **不得**变绿可签发;=100% | Latch/Gate:`test_alpha_inv_acceptance.py::test_inv1_*` + `test_rule_gate` / `test_renew` / `test_latch` | 见机器执行戳 |
| INV-2 | Client Memo 字段集 | 导出物含 ADR-0015 必填字段;**不得**含商业裁决句 | Client Memo 导出契约:`test_client_memo_export` / `test_alpha_inv_acceptance::test_inv2_*` | 见机器执行戳 |
| INV-3 | 禁止角色泄漏 | 备忘正文不得出现 Lead/Critic 字样 | 同上 INV-2 seam | 见机器执行戳 |

**α-inv 编排命令**(可选):

```text
PYTHONPATH=src python scripts/run_alpha_inv_acceptance.py
```

或单跑套件:

```text
PYTHONPATH=src python -m pytest tests/unit/test_alpha_inv_acceptance.py -q
```

---

## α-demo(demo · 仅对照,不升格)

下列 DEM 项若在本记录提及,**仅作对照**,不构成本票 α-inv 通过线,更不得升格为「产品已验证 / latch 已证明」。

| ID | 判据 | 本票处置 |
|---|---|---|
| DEM-1 | Import Friction | 对照(归 #88);本票不判 |
| DEM-2 | T1 Clarity | 对照(归 #89);本票不判 |
| DEM-3 | Client Memo rubric | 人工勾选面挂在 Client Memo 导出物;机检边界由 INV-2/3 承载;不升格 |
| DEM-4 | 预算进度可见 | 对照(归 #92);本票不判 |
| DEM-5 | 检索零命中提示 | 对照(归 #93);本票不判 |
| DEM-6 | 职人/审计视图 | 对照(归 #91);本票不判 |
| DEM-7 | Time-to-Sheet | **仅观测**:固定脚本走通并记录分钟数;**不设 <10min 硬阈值** |

### DEM-7 观测命令

```text
PYTHONPATH=src python scripts/dem7_time_to_sheet.py --out-dir reports/batch1_alpha/dem7
```

读数落 `reports/batch1_alpha/dem7/dem7-time-to-sheet.json` 的 `elapsed_minutes`;`hard_threshold` 恒为 `null`。

---

## 层级声明

- α-inv = 确定性 invariant;单次失败即未过;与 LLM 运气无关。
- α-demo = 演示/观测层;过线 ≠ 测量可信 ≠ 产品已验证。
- 演示可过 ≠ 测量可信(Anthropic 纪律 #1)。

<!-- MACHINE_STAMP -->

### 机器执行戳(2026-09-30T07:50:06Z)

- α-inv 套件结果: **PASS**
- DEM-7 观测分钟数: **0.0014** (hard_threshold=none;仅观测)
- 测口:Latch/Gate + Client Memo;未用 freshlatch.eval 主跑;未改 gold
- pytest 尾部:

```
............                                                             [100%]
12 passed in 2.23s
```
