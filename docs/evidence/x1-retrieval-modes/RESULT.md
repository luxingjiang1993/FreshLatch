# x1 检索模式对比（离线测量）

> 层：实验 / 冒烟。单次确定性运行，不报方差，不作统计显著。
> 不是改臂授权。`PRODUCTION_RETRIEVAL_MODE` 仍为 bm25。
> 数据：模型双标 + Ronin 代理人（模型）代审，`human_row_review=false`，不是人工逐行审核。

## 输入

- 金标提交: `5de99c1`（PR #282）
- 题集: `data/exp/x1/questions.json`（n=267，arm=224，guardrail=43）
- 语料: `data/exp/x1/corpus` + `data/exp/x1/traps`，chunk=794
- check_x1 退出码: 0
- 生产默认臂（跑前/跑后）: bm25 / bm25
- 配置 dense 模型 `text-embedding-v4`（dim=1024）: 未跑。该路径只在 `embeddings.py` 调用 DashScope，本测量禁止付费 API。
- 本地 dense 模型: `BAAI/bge-small-zh-v1.5`，dim=512，库 `fastembed`。查询向量在计时前预计算，与 `retrieve_typed.make_cached_query_embedder` 一样，p95 不含模型加载、不含网络嵌入。
- Recall@10 用 `freshlatch.eval.retrieve_eval.recall_at_k`：top-10 里出现任一 relevant 记 1，否则 0，再对题宏平均。不是集合召回率。
- p95 来自单次 `time.perf_counter`。重复运行会有毫秒级抖动，800ms 门槛对这个抖动不敏感。Recall 与 MRR 由排序决定。
- MRR@10 用同文件 `mrr_at_k`。p95 用同文件 `_p95_ms`（入参秒，返回毫秒）。
- 主表分母只含 `score_role=arm`。护栏题不进 Recall / MRR。
- 合成模板陷阱 47 道：`ret013-draft/round4/part2/questions.part2.json` 的 48 个 id 与正式题集的交集。缺 `r4n-s2-d0-t1-91-qc`。这 47 道仍计入总体与 trap，单独一列只是子集。
- 金标 qtype 词表是 lexical / paraphrase / multi_hop。本报告的 lexical 即字面重合题，没有另造 literal 列。category 里 adversarial 的 n=0。

## 主表

| 切片 | n | bm25 Recall@10 | bm25 MRR@10 | bm25 p95_ms | dense Recall@10 | dense MRR@10 | dense p95_ms | hybrid Recall@10 | hybrid MRR@10 | hybrid p95_ms | hybrid+rerank Recall@10 | hybrid+rerank MRR@10 | hybrid+rerank p95_ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 总体 | 224 | 0.9196 | 0.7275 | 72.335 | 0.9330 | 0.7601 | 14.594 | 0.9732 | 0.7740 | 84.914 | 0.9732 | 0.7567 | 87.253 |
| lexical | 60 | 1.0000 | 0.9792 | 76.407 | 0.9667 | 0.9281 | 14.644 | 0.9833 | 0.9528 | 84.212 | 0.9833 | 0.9639 | 86.842 |
| paraphrase | 119 | 0.8739 | 0.6455 | 72.335 | 0.8992 | 0.7014 | 14.811 | 0.9580 | 0.7195 | 85.742 | 0.9580 | 0.6795 | 92.001 |
| multi_hop | 45 | 0.9333 | 0.6089 | 68.971 | 0.9778 | 0.6915 | 14.255 | 1.0000 | 0.6798 | 83.496 | 1.0000 | 0.6845 | 83.553 |
| hard | 153 | 0.9216 | 0.7421 | 69.486 | 0.9150 | 0.7459 | 14.466 | 0.9673 | 0.7867 | 83.027 | 0.9673 | 0.7701 | 87.253 |
| trap | 71 | 0.9155 | 0.6962 | 79.295 | 0.9718 | 0.7908 | 15.156 | 0.9859 | 0.7465 | 87.745 | 0.9859 | 0.7277 | 88.335 |
| adversarial | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 合成模板陷阱47 | 47 | 0.9787 | 0.8000 | 81.337 | 1.0000 | 0.8754 | 17.391 | 0.9787 | 0.8440 | 87.745 | 0.9787 | 0.8170 | 92.001 |

## 相对 bm25 的 Recall@10 差与门槛

门槛（本测量采用，与 rerank 预登记的 800ms 同一延迟上限）：Recall@10 严格高于 bm25，且该臂 p95 ≤ 800 ms。
过门槛只表示可以另开票讨论，不是改默认。

| 臂 | 总体 Recall@10 差（臂 − bm25） | 总体 p95_ms | 严格提升且 p95≤800 |
|---|---:|---:|---|
| dense | 0.0134 | 14.594 | 是 |
| hybrid | 0.0536 | 84.914 | 是 |
| hybrid+rerank | 0.0536 | 87.253 | 是 |

## 仓库 rerank 预登记门（相对 hybrid，不是相对 bm25）

- hybrid Recall@10: 0.9732
- hybrid+rerank Recall@10: 0.9732
- hybrid+rerank p95_ms: 87.253
- `rerank_default_verdict`: 生产默认关
- 该门要求 Recall@10 严格高于 hybrid 且 p95≤800ms 才写「生产默认开」。`rerank_lexical` 只重排 hybrid 已给出的 top-10，任一命中的 Recall@10 在这个实现下不会高于 hybrid。

## 模式是否诚实

- bm25: bm25
- dense: dense
- hybrid: hybrid
- hybrid+rerank: hybrid+rerank

## 结论

按总体「Recall@10 严格高于 bm25 且 p95≤800ms」，dense、hybrid、hybrid+rerank 都过线。建议只把 hybrid 放进另开的讨论票：总体 Recall@10 0.9196 → 0.9732，p95 84.914 ms。hybrid 的 lexical 是 0.9833，低于 bm25 的 1.0000，总体增益来自 paraphrase 与 multi_hop。dense 总体只高到 0.9330，但 lexical 0.9667 低于 bm25 的 1.0000，hard 0.9150 也低于 bm25 的 0.9216。hybrid+rerank 的总体 Recall@10 与 hybrid 相同，仓库预登记门（须严格高于 hybrid）的判决是「生产默认关」，不建议为 rerank 另开切换票。本轮不是授权：生产默认仍是 bm25；向量是本地 bge-small-zh-v1.5，不是配置里的 text-embedding-v4；题集是模型双标加模型代审。

## 原始文件

- `summary.json`
- `per-query.csv`
- `per-query.json`
