# 整仓剩余项复跑报告 · 2026-09-30

> 承接：`REPORT-20260930.md`（上轮 L3 SKIPPED、L2 其它未勾、I2 活模 skip）。  
> 计划：`PLAN-20260930-REMAINING.md`  
> **文首声明**：冒烟/演示可读 ≠ Hard-Gold / 渗透认证 / 统计测量闭合。N=1 不报方差。

## 元数据

| 项 | 值 |
|----|-----|
| HEAD（开跑时） | `c4934d2` |
| Python | 3.14.6 |
| 模型（L3/活模） | `qwen-flash` |
| temperature / seed | `0.0` / `None` |
| 日期 | 2026-09-30 |

## 总览

| 项 | 结果 |
|----|------|
| L2 其余（i0/i1/batch3–5/β+） | **过**（关联 pytest + retrieve） |
| I2 活模 e2e | **过**（1 passed） |
| L3 gold `run` N=1 | **跑通**；`all_hit=False`（表现层未全命中） |
| L3 `control` | **跑通**；对照成立 ❌（must_stale 假绿 0/4） |
| L3 `control-c` | **跑通**；对照成立 ✅（must_stale 假绿 4/4） |
| L3 `report` 重渲染 | 控制台 GBK emoji 曾失败；原 `run` 已写 `reports/report-20260930.md` |
| I1 金样 `i1-s005` 重跑 | **跑通**；机判 `unknown` vs 金标 `stale` → 漏拦（与金样叙事一致） |
| 仍未自动做 | 真人盲看；`scripts/w12_comprehensive_*`（§15 Out） |

---

## L2 其余

| 包 | 命令/依据 | 结果 |
|----|-----------|------|
| I0 | `python -m freshlatch.eval retrieve` | exit 0；n=36 Recall@10=1.0000 MRR@10=0.7324 replay=pass；产物 `reports/retrieve-*.md` |
| I1 | `pytest tests/unit/test_i1_*.py` + 金样脚本 | 契约测绿；金样见下 |
| batch3 γ | `test_gamma_inv_alignment.py` + 假绿仪器本轮 L3 复测 | invariant 绿；仪器句与历史预锁同向（旧 control 不成立 / C 成立） |
| batch4 δ | `test_active_pack.py`（ACCEPTANCE 主缝） | 绿（含于 L2-rest 76 passed） |
| batch5 | `test_batch5_acceptance.py` | 绿 |
| β+3b | `test_beta_plus_3b_acceptance` + `test_basis_rot*` / `test_ui_basis_rot` | 绿（basis 20 passed） |
| 抗假绿预登记 | `test_main_chain_anti_false_green_prereg.py` | 绿（结构预锁，非本轮重跑主链 N=3） |

留档：`pytest-l2-rest-20260930.txt`（76 passed）、`retrieve-20260930.txt`、`pytest-beta-basis-20260930.txt`。

---

## I2 活模

```text
FRESHLATCH_I2_LIVE=1
pytest tests/unit/test_i2_injection_e2e.py::test_inj_t001_live_llm_lead_auditor_finalize_smoke -v
→ 1 passed in ~7s
```

留档：`i2-live-20260930.txt`。档=冒烟，≠渗透认证。

---

## L3 表现层（诚实读数）

### gold run

- 命令：`python -m freshlatch.eval run --gold data/eval/gold.json --runs 1`
- decoding：qwen-flash · temp=0.0 · seed=None · UTC≈2026-09-30T08:00:29Z
- 报告：`reports/report-20260930.md` / `.json`
- 混淆矩阵（条数，不报%）：must_stale 命中 2 漏判 2（c3/c7→unknown）；must_fresh 4/4；must_unknown 4/4
- **违例级**（must_stale→fresh）：**0**
- **全量通过遍数**：0/1（10/12 命中）
- all_hit：False

### control（旧仪器）

- must_stale 假绿 **0/4**；对照成立：**否**
- 报告：`reports/report-20260930-160045.md`
- 与 batch3 预锁「旧仪器对照不成立」同向；**不**据此声称产品无假绿。

### control-c（仪器 C）

- must_stale 假绿 **4/4**；对照成立：**是**
- 报告：`reports/report-20260930-160051.md`
- 对照成立只说明无工具基线可打出假绿；**不**等于一期评测闭合或产品已愈假绿。

### report 子命令

- 首次：`UnicodeEncodeError`（Windows 控制台 GBK 无法打印 ✅）→ exit 1  
- 金标 markdown **已由 `run` 写入**，不依赖该重渲染。

---

## I1 金样重跑

- 命令：`python scripts/i1_mck_runnable_gold.py --claim-id mck-1`
- machine_status=`unknown`；gold_expected=`stale`；gold_hit=false；err=漏拦  
- 与金样页「该拦未拦」叙事一致（冒烟复现，非 Hard-Gold 修复证明）  
- 轨迹：`reports/i1-mck-runnable/trajectories/run-20260930-160145.jsonl`

---

## 相对上轮公式的更新

| 原状态 | 现状态 |
|--------|--------|
| L3=SKIPPED | L3=**RAN**（run+control+control-c） |
| L2 其它未勾 | L2 其它本表已勾 |
| I2 活模 skip | **过** |

**不变量绿**（L0+L1+L2）仍成立。  
**表现绿**：本轮**不声称**——gold `all_hit=False`；旧 control 对照不成立；仅仪器 C 对照成立。

### 未声称（追加）

- 非 Hard-Gold；非「金标全过」；非假绿已根治  
- 非 I1 漏拦已修复（金样仍复现漏拦）  
- 未跑 `w12_comprehensive_*`；未做真人盲看  

---

## technology--code-review（补评）

- 剩余机器项已按 §15 诚实跑完并分轨记录。  
- 表现层短板集中在 must_stale→unknown（c3/c7）与 I1 mck-1 漏拦，属**判定/证据收口**问题，不是 L1 闸回归。  
- 后续若要「修到 all_hit」，须另开票 + 预锁止损，禁止改 gold 凑绿。
