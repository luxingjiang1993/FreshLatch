# Eval Retrieve — 子系统评测入口与「为何仍 BM25」

> **档：** 演示 / 冒烟层（n=36）；**不报方差**；**不作统计显著声明**。  
> **数字真相源：** 仓内 `reports/retrieve-*.md`（对齐 `origin/main` / Phase A PR #167 后应存在）。本页 **不整表复制** 数字，只链接。  
> **分轨：** 本页 = `python -m freshlatch.eval retrieve`；主张金标是另一轨 `eval run --gold`，禁止混报。  
> **纪律：** ADR-0026；卡片叙事见 [`accounting-card.md`](./accounting-card.md)。

---

## 1. 为何仍默认 BM25（三句）

1. **门未过：** dense R@10 低于 BM25；hybrid+rerank 未严格优于 hybrid → 不得开 rerank 生产默认。  
2. **Hard-Gold 未开：** 持平 ≠ 可改默认；改臂另票。  
3. **档诚实：** 上表是冒烟对照，不是「BM25 统计显著最优」。

数字与判决原文：

| 报告 | 内容 |
|------|------|
| [`reports/retrieve-bm25-baseline.md`](../reports/retrieve-bm25-baseline.md) | A0 BM25；R@10；MRR@10；must_stale 回放；checksum |
| [`reports/retrieve-arm-compare.md`](../reports/retrieve-arm-compare.md) | BM25 / dense / hybrid 三列 |
| [`reports/retrieve-rerank-compare.md`](../reports/retrieve-rerank-compare.md) | hybrid vs hybrid+rerank；门槛判决 |
| [`reports/retrieve-traps.md`](../reports/retrieve-traps.md) | 陷阱子集（不计入主 n） |
| [`reports/retrieve-transform-compare.md`](../reports/retrieve-transform-compare.md) | 查询变换对比 |
| [`reports/phase-a-close-draft.md`](../reports/phase-a-close-draft.md) | Phase A 关门汇总 |

若本地尚无 `reports/`：先合并/检出含 PR #167 的 `origin/main`（或既有 phase-a worktree），再读上表。

---

## 2. 可复跑命令

### 2.1 主命令（BM25；无 API Key 即可）

**POSIX / Git Bash**

```bash
PYTHONPATH=src python3 -m freshlatch.eval retrieve
```

**PowerShell（Windows）**

```powershell
$env:PYTHONPATH = "src"
python -m freshlatch.eval retrieve
```

有 dense 索引时同命令会写出臂对比与 rerank 对比报告；无索引时至少应能产出 BM25 基线（及本地可得的 traps/transform）。**I0 Exit 硬要求：BM25 轨可跑**；五臂全表为增强路径。

> **Windows 注意：** `retrieve_gold.json` 若被 Git `core.autocrlf` 转成 CRLF，复跑会改写 `retrieve_gold_checksum` / 聚合 checksum，但 **Recall@10 / MRR / replay** 应与 SoT 一致。对比以指标与门判决为准；**不要**把 CRLF 漂移的 checksum 提交覆盖 #166 已收报告，除非整仓统一 LF 后重算并另开说明。

### 2.2 Dense 索引（可选 · 需密钥）

```bash
# 配置 DASHSCOPE_API_KEY（勿写入仓库）
PYTHONPATH=src python3 scripts/build_dense_index.py
```

```powershell
$env:PYTHONPATH = "src"
python scripts/build_dense_index.py
```

产物：`data/dense/index.sqlite`（gitignore）。记录见 `reports/dense-rebuild.md`（若已生成）。

### 2.3 主张金标（另一轨 · 勿与 retrieve 混报）

```bash
PYTHONPATH=src python -m freshlatch.eval run --gold data/eval/gold.json
```

---

## 3. 增益门（预登记 · 摘抄）

| 门 | 谓词 | 本期冒烟结果（见 reports） |
|----|------|---------------------------|
| Hybrid 通过线 | ≥ min(BM25, dense)；BM25 相对 A0 容差 0 | pass |
| Rerank→生产 | R@10 **严格 >** hybrid ∧ p95≤800ms | 持平 → **关** |
| 改生产默认臂 | 上式 + **Hard-Gold** | Hard-Gold **未开** |

权威规格叙述：`docs/spec/10-PhaseA-RAG.md`。权威决策：ADR-0003（#156）、ADR-0026。

---

## 4. 改假设会重算（Exit 演示）

口头即可（现场重跑 BM25 为加分）：

- 若门槛从「严格优于」改为「≥」且实测仍 1.0000=1.0000 → 仍可用「持平不开」或「改门槛后才可能开」讲清判决变化；**Hard-Gold 仍挡**。  
- 若容差从 0 放宽且 BM25 略低于 A0 → 「A0 保险丝」判决可能从 pass 变 fail。  

禁止：改门之后仍声称「数字证明该换默认」而不提 Hard-Gold。

---

## 5. Out of scope（本页不做）

- 改 `PRODUCTION_RETRIEVAL_MODE`  
- 把冒烟表写成论文主结果  
- 用本页替代主张金标 / 假绿仪器结论
