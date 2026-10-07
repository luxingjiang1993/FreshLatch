# Accounting Card — Phase A 为何当时保持 BM25

> **现状（2026-10-07）：** 生产默认已改为 `hybrid+rerank`。本页表格仍是 Phase A 冒烟（n=36）的预锁假设，不是现在的常量。回退见 `set_retrieval_switch("bm25")`。决策见 `docs/evidence/retrieval-decision.md`。

> **档：** 演示 / 冒烟层（n=36）；**不报方差**；**不作统计显著声明**。  
> **数字真相源：** `reports/retrieve-*.md`（Phase A / PR #167）；本页只收敛叙事，不另造第二份数字。  
> **纪律：** ADR-0026；增益门与评测可跑见 ADR-0003（#156 修订）。  
> **规格对照（非本页）：** `docs/spec/10-PhaseA-RAG.md`。

---

## 1. 假设（先于数字）

| 项 | 值 |
|----|-----|
| 语料 | 28 文件 / 84 chunks（日期 2026-09-28） |
| 主指标 n | 36（冒烟） |
| 默认臂 | `PRODUCTION_RETRIEVAL_MODE = bm25` |
| A0 容差 | BM25 相对 A0 Recall@10 容差 = **0.0** |
| Hybrid 通过线 | hybrid ≥ min(BM25, dense) |
| Rerank→生产默认 | Recall@10 **严格优于** hybrid **且** p95 ≤ 800ms |
| 保险丝 | must_stale 金标命中回放须 pass |
| 聚合 checksum | 见 `reports/retrieve-bm25-baseline.md`（#166 SoT；勿用手改） |

---

## 2. 公式 / 门谓词

1. **Recall@10(arm)**：主金标上臂强制 `retrieval_mode` 的宏平均召回。  
2. **Hybrid 通过** ⟺ `R@10(hybrid) ≥ min(R@10(bm25), R@10(dense))` ∧ BM25 相对 A0 不越容差。  
3. **Rerank 可开生产默认** ⟺ `R@10(hybrid+rerank) > R@10(hybrid)` ∧ `p95 ≤ 800ms`（两条同时）。  
4. **改生产默认臂** ⟺ 上式过线 **且** 另票 **Hard-Gold** 过线（本期未开；见 roadmap Backlog）。

---

## 3. 数字（一行表 · 引用 reports）

| 臂 | Recall@10 | 判决相关 |
|----|----------|----------|
| BM25（A0） | 1.0000 | 相对 A0 pass；must_stale 回放 pass |
| dense | 0.9722 | **低于** BM25 |
| hybrid（RRF k=60） | 1.0000 | ≥ min(BM25,dense) → 通过线 pass |
| hybrid+rerank | 1.0000 | **非**严格更好；p95=11.4ms；**生产默认关** |

详表与复跑：[`docs/eval-retrieve.md`](./eval-retrieve.md) → `reports/retrieve-arm-compare.md` / `retrieve-rerank-compare.md` / `retrieve-bm25-baseline.md`。

---

## 4. 权衡 — 为何仍 BM25

**主句（预登记门）：** dense 召回更差；rerank 未严格优于 hybrid → 按已锁门槛 **不得**改生产默认。  

**护栏：** 即便 hybrid 与 BM25 持平，改默认仍须另开 **Hard-Gold**（难金标 + 分列增益门）；I0 / Phase A **未**授权换臂。  

**不是本轮主因（选型史）：** SQLite+BM25 可复现、过滤干净、零重依赖——见 ADR-0003 原文；面试先讲门，再讲选型。

---

## 5. 指针

- 复跑与命令：[`eval-retrieve.md`](./eval-retrieve.md)  
- 贡献边界：[`contribution-boundary.md`](./contribution-boundary.md)  
- Hard-Gold：roadmap Backlog 另票；**本期未开**  
- 评估全文：`docs/research/I0-冒烟层与数字真相源设计评估.md`

---

## 6. 面试 30 秒口述稿

「Phase A 把 retrieve 做成可测子系统，生产默认钉死 BM25。我们在冒烟集 n=36 上跑了 dense / hybrid / rerank：dense 的 Recall@10 更差，rerank 相对 hybrid 没有严格增益，所以按预登记门槛不能改默认。hybrid 持平也不够——还要另开 Hard-Gold。这张表是冒烟，不是统计证明。面试官能打开仓跑 `eval retrieve`，改『必须严格优于』这条假设，判决仍是关。」

---

## 7. Exit 自检（闭卷）

1. 生产默认臂？→ `bm25`  
2. rerank 开默认两门槛？→ 严格优于 hybrid ∧ p95≤800ms  
3. 本表档？→ 冒烟，非统计  
4. 若把「严格优于」改成「≥」且数字仍持平？→ 仍不满足「严格」；若允许 ≥ 且其他不变，才可能讨论开默认（仍挡 Hard-Gold）
