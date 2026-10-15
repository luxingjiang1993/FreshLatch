# 训练 / 时序检索 · 新预注册

锁死日期：2026-10-15。票 L4-C-01。本页是**另一份** prereg，不是 `docs/evidence/quality-gate/PREREG.md` 的改写。写完本节的指标名、k、臂列与 `replaces_frozen_baseline=false` 之后，不得为了让某次运行好看而改这些字段。

本期没有训练权重，也没有打分器。臂上的 Recall@k / MRR / nDCG 保持未测量。空着不是 0，也不是从冻结基线抄来的数。

本页不改 `PRODUCTION_RETRIEVAL_MODE`。生产臂仍是 `hybrid+rerank`。`temporal_trained` 只在 eval 的非默认臂钩子里可选，运维开关不接受它。

## 1. 事前指标

在任何一次测量写出数字之前，列与聚合方式先锁在这里。

| 项 | 锁定值 |
|---|---|
| k | 10 |
| 指标 | Recall@k、MRR、nDCG |
| 相关 | 二元。相关集是该 query 的日期适用版本，不是「当前在效力」版本 |
| 聚合 | 只对本页语料的 query 做算术平均。两臂分列，不合成一个数 |
| level | schema。本语料 n=2。不报方差 |
| 解码 | 不调用 LLM。temperature 未使用，seed 未使用，model 未使用 |
| 通过线 | 无。不设门槛数字 |

以后若主人另批一次真测量，数字只能来自那一次、写在新的 measurement 文件里。不得回写上表的指标名、k 或臂列，不得把冻结 T1 / R1 的 `value=` 填进本表。

## 2. 臂列

| arm | 角色 | 生产默认 | 权重 | Recall@k | MRR | nDCG | measurement_status |
|---|---|---|---|---|---|---|---|
| temporal_trained | 训练或已发表等价方法的评测臂。本期无权重、无打分器 | false | absent | unmeasured | unmeasured | unmeasured | unmeasured |
| mrag_untrained | 无训练对照列。只占列名，本期不打分 | false | not_applicable | unmeasured | unmeasured | unmeasured | unmeasured |

`mrag_untrained` 不是 `PRODUCTION_RETRIEVAL_MODE`，也不能经 `set_retrieval_switch` 切到生产。`temporal_trained` 经 `RunContext.arm_eval_retrieval_mode` 仅在 `mode=eval` 时绑定。绑定后 `try_retrieve` 不调用 store 的 BM25 / dense / hybrid / rerank。生产实现 `SQLiteStore.retrieve` 若被绑到该臂，在排序前拒绝，不改记成别的臂。`src/freshlatch/store/base.py` 本期不改，内存假实现不另接这条拒绝。

replaces_frozen_baseline=false

## 3. 与冻结 T1 / R1 的关系

冻结 T1 是 `docs/evidence/neural-rerank/per-query.json` 上的回放，指标名 `T1-new-over-old-accuracy`。冻结 R1 是同一回放上的 `R1-recall@10` 与 `R1-mrr@10`。它们的 `value=` 只由 `docs/evidence/quality-gate/PREREG.md` 与离线质量闸重放决定。

本页：

- 不替换、不改写 `docs/evidence/neural-rerank/per-query.json`，也不改该目录下其它文件。
- 不改写注册 T1 的 `value=`。
- 不改写注册 R1 的 `value=`。
- 不改 `docs/evidence/quality-gate/PREREG.md` 的地板。
- 质量闸各行保持 `counted_as_pass=false`，`status=TBD`。
- 不改 `docs/evidence/patch-events/RESULT-Y.md`。本页不登记路线 Y 的成立格。

`frozen_relation.T1=does_not_replace`。`frozen_relation.R1=does_not_replace`。

## 4. 版本语料

独立语料：`data/temporal-trained/v1/corpus.json`。

- corpus_id: `temporal-trained-v1`
- corpus_version: `v1`
- level: `schema`
- n: 2
- corpus_sha256: 49ada9927084e2ccc73eba27d1486be1f384494b4325e5cb49e99473843f5b3e

同一 `doc_id` 有两个版本。query 带 `query_date`。`relevant` 指向日期适用的那一版。该文件不在 `data/exp/x1/`，也不是 `data/eval/gold.json` 或三份金标。

测量入口：

`python -m freshlatch.eval temporal-prereg --corpus data/temporal-trained/v1/corpus.json --out docs/evidence/temporal-trained-retrieval`

入口只写 `measurement.json`。它拒绝把输出放进 `docs/evidence/neural-rerank/`、`docs/evidence/quality-gate/`、`docs/evidence/patch-events/`、`data/exp/x1/`、`data/eval/`。即使传入一个存在的权重文件，本期仍不打分：`measurement_status=unmeasured`，三个指标保持 null。

## 5. Provenance

- Kind: new（本页）+ adapt（对照列与版本语料习惯）。
- TempRetriever 论文：https://arxiv.org/abs/2502.21024 。官方训练仓未核实公开。本页只把它当作理论锚，不宣称复现该工作。
- MRAG 无训练对照：https://arxiv.org/abs/2412.15540 · https://github.com/siyue-zhang/MRAG 。`mrag_untrained` 只借用「无训练、时间与语义分开列」的习惯。不把该仓代码拷进产品，本期也不打这一列的分。
- FiscalQA Pro 方法锚：https://arxiv.org/abs/2608.09393 · https://github.com/rosecymbler/fiscal-fr-bench 。摘的是版本语料加 query date 对齐适用版本。该仓写明端到端检索器未公开。不迁移其分数，不把它的语料拷进本仓。

## 6. 主人如何审本页

Trust=Gate。合并前由主人看这一页，而不是看夹具是否变绿。

1. 第 1 节的事前指标仍是 Recall@k、MRR、nDCG，k=10，且没有门槛数字。
2. 第 2 节两臂分列，生产默认都是 false，`replaces_frozen_baseline=false` 仍在。
3. 第 3 节仍写明不替换冻结 `per-query.json`，不改写注册 T1 / R1 的 `value=`，`counted_as_pass=false`。
4. 第 4 节的 `corpus_sha256` 与 `data/temporal-trained/v1/corpus.json` 的 LF sha256 一致，且路径不在 `data/exp/x1/`。
5. 第 5 节没有把未公开的训练仓写成已经落地的复现。
6. `measurement.json` 的臂行仍是 `measurement_status=unmeasured`，Recall@k / MRR / nDCG 为 null。

主人点头之前，不要把 `measurement_status` 改成已测量，不要往臂行填数字，不要改质量闸地板。
