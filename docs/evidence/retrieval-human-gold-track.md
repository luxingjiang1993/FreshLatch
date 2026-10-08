# 检索全库人工金标另轨（入口 / 说明）

> **票**: [#445](https://github.com/luxingjiang1993/FreshLatch/issues/445) · Parent [#436](https://github.com/luxingjiang1993/FreshLatch/issues/436) · 精神继承 [#429](https://github.com/luxingjiang1993/FreshLatch/issues/429)  
> **Trust**: Gate（人）· 本页只立边界与入口，不代填金标、不发模型  
> **状态**: 另轨说明已立 · **全库逐行人工金标未完成**

## 明文（必读）

**检索金标 ≠ 放行闸成立。**

本轨无论做到哪一步，都不得用检索层的 Recall@10 / MRR@10 / nDCG@10（或任何检索分差）声称 patch_events 放行闸主比较成立，不得宣称结果甲，不得填 `RESULT-B` 成立格，不得回写旧 `RESULT.md` 成立格。

本轨不改生产常量 `PRODUCTION_RETRIEVAL_MODE`（现行值见代码与 `docs/evidence/retrieval-decision.md`；本说明页不触碰该行）。

## 与路线 B 冲甲主表的分层

| 层 | 载体 | 测什么 | 本轨关系 |
|---|---|---|---|
| 放行闸 · 路线 B 冲甲主表 | `docs/evidence/patch-events/PREREG-B.md`（协议已锁 · **正式主跑未激活**）；操作定义 ADR-0034；评估见 `docs/research/patch_events-路线B冲甲可识别选取设计评估.md` | 固定放行下的 false-accept（选取 R · k 下限 10 · 仓外门闩） | **另一层**。检索金标进不了主比较 score，也不能代替门闩或正式抄表 |
| 检索 · 生产默认与比臂 | `docs/evidence/retrieval-decision.md`、`docs/evidence/issue-284/`、`docs/evidence/x1-retrieval-modes/`、`docs/evidence/neural-rerank/` | 检索臂 Recall / MRR / nDCG | 本轨只服务「金标是否经真人逐行审」；**不能证明放行闸** |
| 对外可说句子 | `docs/evidence/当前可说口径.md`（若尚未合入则以 [PR #417](https://github.com/luxingjiang1993/FreshLatch/pull/417) 稿为准） | 现在能念什么 | 本轨完成前，对外仍须写：金标非全库人工；真人只审 DECISION-16 的 16 题 |

路线 B 的成立定义、选取、激活条件只在 `PREREG-B.md` / ADR-0034。本页不复制成立格，不建 `RESULT-B.md` 壳，不抄主表数字。

## 范围声明

- **默认范围**: x1 作答臂 `score_role=arm`，n=224（与 #283 / #285 / DECISION-16 分母一致）。  
- **全库**: 若执行人声明「全库」，须在台账首行写死题集路径与题数（含护栏是否纳入）；未声明前默认仍是 224。  
- **题集路径**: `data/exp/x1/questions.json`（及对应 `gold.json`）；provenance 见 `data/exp/x1/LABELING-PROVENANCE.json`。  
- **现状**: `human_row_review=false`。真人已审范围只有 `docs/evidence/issue-284/DECISION-16.md` 的 16 道 Recall 分差题，不是全库逐行人工审核。

## 本轨目标（完成后才可撤的限制）

完成后（须人 Gate 签认）才可撤对外限制「只审 DECISION-16 / 非全库人工金标」。在此之前：

- `docs/evidence/当前可说口径.md`（或 PR #417 等效稿）仍写：金标是模型标注；真人只审 16 题；**不能说成全库人工金标**。  
- 检索决策链 `retrieval-decision.md` 的局限性表述保持有效。

本轨**完成 ≠** 放行闸成立，也**≠** 授权改 `PRODUCTION_RETRIEVAL_MODE` 或改五处冻表面。

## 台账（人写；链可起草模板，不代填）

执行人：Oriental Ronin（或指定标注流程）。建议台账落在本目录下独立文件（例如后续票写死的 `docs/evidence/retrieval-human-gold-ledger.md` 或子目录），与本说明页分开。

最低字段（跑前锁死，不在此页改成更松）：

| 字段 | 含义 |
|---|---|
| `question_id` | 题号 |
| 范围批注 | 224 或全库声明 |
| 原文 chunk 核对 | 金标 evidence id 是否与语料一致 |
| 裁决 | 保持 / 修订 / 剔除（修订须记新旧 id） |
| 审阅人 · 日期 | 真人签名位 |
| 是否影响 DECISION-16 分差集 | 是/否（是则另开检索重算票，仍不碰放行闸） |

链不代填金标行。填表与签认是人的 Gate。

## 禁止清单（本票 / 本轨）

1. 不填 `docs/evidence/patch-events/RESULT-B.md` 成立格（该文件若尚未建壳，本轨也不建、不填）。  
2. 不回写旧 `docs/evidence/patch-events/RESULT.md` 成立格，不回写旧 `PREREG.md`。  
3. 不改 `PREREG-B.md` 的选取、成立定义或文首激活状态。  
4. 不改 `PRODUCTION_RETRIEVAL_MODE`；不改放行闸代码；不发模型。  
5. 不改五处冻表面（README 导语相对基线、`docs/现状四闸-结构图.html`、`src/freshlatch/ui/app.py` 入口块、简历一行 / mastery pack 等对外表面；详见 `tests/unit/test_pe_freeze_surfaces.py`）。  
6. 不用本轨进度填路线 B 门闩报告，不把检索数升格为冲甲主张。

## 指针

| 用途 | 路径 |
|---|---|
| 检索决策链 | `docs/evidence/retrieval-decision.md` |
| 16 题真人拍板 | `docs/evidence/issue-284/DECISION-16.md` |
| 当前可说口径 | `docs/evidence/当前可说口径.md`（或 PR #417） |
| 路线 B 协议 | `docs/evidence/patch-events/PREREG-B.md` |
| 路线 B ADR | `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md` |
| 规格 · 人轨另票 | `docs/spec/24-patch-events-路线B冲甲.md`（票序第 8 项） |

## 面试一句

检索可以另开全库人工金标轨，用来撤「只审 16 题」的检索口径限制；那一轨和放行闸冲甲主表（`PREREG-B` / ADR-0034）分层。**检索金标成立不能证明放行闸成立。**
