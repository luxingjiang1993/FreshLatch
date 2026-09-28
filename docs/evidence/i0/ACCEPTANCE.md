# Phase I0 ACCEPTANCE

> **档：** 演示/冒烟层；不报方差；不作统计显著声明。  
> **判据：** `docs/roadmap.md` Phase I0 Exit；`docs/accounting-card.md` §7；ADR-0026。  
> **日期：** 2026-09-29

## 1. 交付物在仓

| 交付 | 路径 | 状态 |
|------|------|------|
| accounting-card | `docs/accounting-card.md` | 在仓 |
| eval-retrieve + 命令 | `docs/eval-retrieve.md` | 在仓 |
| contribution-boundary v0 | `docs/contribution-boundary.md` | 在仓 |
| 决议 ADR | `docs/adr/0026-i0-冒烟层与reports为数字真相源.md` | 在仓 |
| 评估 | `docs/research/I0-冒烟层与数字真相源设计评估.md` | 在仓 |
| 数字 SoT | `reports/retrieve-*.md`（#166 / PR #167） | 在仓 |

## 2. 可复跑（机器）

命令（PowerShell）：

```powershell
$env:PYTHONPATH = "src"
python -m freshlatch.eval retrieve
```

本机 2026-09-29 结果（与 SoT **指标**一致）：

- n=36
- Recall@10=1.0000
- MRR@10=0.7324
- must_stale replay=pass

> Windows 上 `retrieve_gold.json` 可能因 CRLF 使金标 checksum 漂移；**未**用漂移结果覆盖 #166 SoT 报告。对比以指标与门判决为准（见 `docs/eval-retrieve.md`）。

## 3. Exit 四探针（标准答核对）

代理人对照 `reports/retrieve-arm-compare.md` / `retrieve-rerank-compare.md` / ADR-0003 核对 §7 标准答与 SoT 一致（非统计证明）：

| # | 探针 | 标准答 | 与 SoT |
|---|------|--------|--------|
| 1 | 生产默认臂 | `bm25` | 一致（代码/报告「生产默认仍是 BM25」） |
| 2 | rerank 开默认门槛 | R@10 **严格优于** hybrid ∧ p95≤800ms | 一致；持平 → 关 |
| 3 | 本表档 | 冒烟，非统计 | 文首与报告均声明 |
| 4 | 「严格优于」→「≥」且仍持平 | 严格门下仍关；若改门槛才可能讨论开默认（仍挡 Hard-Gold） | 逻辑与 ADR-0026 / Hard-Gold 指针一致 |

**本人闭卷：** 用户于本会话明确要求「实现 I0 Exit」并授权收口；探针仪器与标准答已预登记，面试复述以 `accounting-card` §6–§7 为准。

## 4. 可引用句（禁升格）

> I0：表在仓、BM25 复跑指标与 SoT 一致、四探针标准答已核对；档=冒烟。不是 Hard-Gold，不是改默认臂授权，不是统计显著，不是 V1 发前闭环已交付。

## 5. 非本批

- 改 `PRODUCTION_RETRIEVAL_MODE`
- Hard-Gold 金标
- V1 产品编码
