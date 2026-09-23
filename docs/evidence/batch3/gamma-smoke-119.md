# Batch 3 γ-SMOKE 跑次记录（#119）

> 层：`smoke`。n=1，冒烟检查。不报方差，不报统计显著。
> 入口：既有 `python -m freshlatch.eval run`（`run_gold`）。不新开评测 harness。
> 判据：`docs/research/C3-判定拉齐预登记卡.md` γ-SMOKE-1/2；ADR-0018。本记录不改判据、不改 `data/eval/gold.json`。
> 代码指针：加固已在 `feature/future-roadmap` 的 `919d18e`（#118 / PR #124）之后。本跑次 commit `db85e679f95839af5295e69617283e71cfaaf265`。
> 托管端点会漂移，跨会话复现只能近似。

## 跑次档案

| 项 | 值 |
|---|---|
| 日期 | 2026-09-23 |
| 开跑 (UTC) | 2026-09-23T07:10:55Z |
| 落档 (UTC) | 2026-09-23T07:15:48Z |
| 模型 | `qwen-flash` |
| temperature | `0.0` |
| seed | `None`（temp=0，seed 无采样意义） |
| n | `1` |
| commit | `db85e679f95839af5295e69617283e71cfaaf265` |
| 语料 | 当次 `ingest` 灌入本地库后再跑；不是改 gold |
| 机器原文 | `reports/report-20260923.md`、`reports/report-20260923.json` |

机器原文里的「波动区间」「S2 占比」是既有 harness 字段。本票不把它们读成方差或统计显著。

## γ-SMOKE-1 仅表明

γ-SMOKE-1（qwen-flash，temp=0.0，seed=None，n=1，日期 2026-09-23，commit db85e679f95839af5295e69617283e71cfaaf265，入口既有 run_gold，层=smoke）仅表明加固后 must_stale（c1/c2/c3/c7）判 fresh 合计为 0。四条终态都是 stale，Lead stale 且 Auditor stale，无异议。不是统计证明，不是产品已验证，不是假绿已根治，γ 通过也不等于假绿对照成立。

| claim_id | 终态 | Lead | Auditor | 异议 |
|---|---|---|---|---|
| c1 | stale | stale | stale | 无 |
| c2 | stale | stale | stale | 无 |
| c3 | stale | stale | stale | 无 |
| c7 | stale | stale | stale | 无 |

矩阵 must_stale 列：fresh 0、stale 4、unknown 0。

## γ-SMOKE-2 仅表明

γ-SMOKE-2（同一次跑次，n=1，层=smoke）仅表明：终态 fresh 的 c4、c5、c6 都是 Lead fresh 且 Auditor fresh，异议为空；Auditor 缺席的 c10、c11、c12 落 unknown，没有转成 fresh。本跑次没有无依据 fresh。本跑次没有异议记录样本，因此不把「未出现异议」写成异议路径已统计验证。不报方差，不报统计显著。

| claim_id | 终态 | Lead | Auditor | 读法 |
|---|---|---|---|---|
| c4 | fresh | fresh | fresh | 双判一致 fresh |
| c5 | fresh | fresh | fresh | 双判一致 fresh |
| c6 | fresh | fresh | fresh | 双判一致 fresh |
| c10 | unknown | unknown | 缺席 | 缺口落 unknown，不是 fresh |
| c11 | unknown | unknown | 缺席 | 缺口落 unknown，不是 fresh |
| c12 | unknown | unknown | 缺席 | 缺口落 unknown，不是 fresh |

## 旁路观察（不进本票通过线）

同一次 `run_gold` 还跑了其余金标。下列读数不改写上面两句，也不构成改 gold 或放宽闸的理由。

- c8（must_fresh）终态 stale，Lead stale 且 Auditor stale。
- c9（must_unknown）终态 stale，Lead stale 且 Auditor stale。
- 干扰项 c13 终态 stale；c14 终态 fresh 且 Auditor fresh、异议为空。c14 不进 12 条矩阵，不计本票通过线。

## 禁升格（本记录不包含这些主张）

- γ 通过意味着假绿对照成立，或假绿已根治
- 消融规格已锁意味着消融已证明，或测量闭合
- 主链抗假绿仅表明句可以升格为 γ-INV 通过线
- α-demo 或 γ-SMOKE 意味着产品已验证
- n=1 可以报方差或统计显著

本票不做消融实跑，不锁方差通过线。未改 `data/eval/gold.json`。
