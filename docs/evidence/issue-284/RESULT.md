# Issue #284 切换前验证

层：实验 / 冒烟，外加跑数前写死的配对区间。单次运行。不是切换授权，不报已证明最优。
数据是模型双标 + Ronin 代理人（模型）代审，`human_row_review=false`，不是人工逐行审核。
抽查清单是模型按规则起草的，供 Oriental Ronin 人工审，本页不宣称已经人工审核。

- 票：https://github.com/luxingjiang1993/FreshLatch/issues/284
- 引用：https://github.com/luxingjiang1993/FreshLatch/pull/283
- 金标：`data/exp/x1/questions.json`，arm=224，guardrail=43，chunk=794
- 向量：本地 `BAAI/bge-small-zh-v1.5`，dim=512，库 fastembed 0.7.1。不是 `text-embedding-v4`。
- 生产默认臂（跑前/跑后）：bm25 / bm25
- check_x1 退出码：0
- Recall@10 沿用 `recall_at_k`（前 10 条里出现任一金标记 1）。MRR 沿用 `mrr_at_k`。
- nDCG@10：金标集合内为 1、否则为 0，理想排序把金标放在最前。
- bootstrap：10000 次，seed=20261007，配对差 = 右 − 左，95% 线性插值百分位。顺序：三组 Recall，然后两组重排的 MRR，然后两组重排的 nDCG。
- McNemar：Recall 命中的精确二项、双侧。

## 显著性

| 配对 | Recall 左 | Recall 右 | 差 | 95% 区间 | 只左中 | 只右中 | 都中 | 都未中 | McNemar p |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 词法 vs 混合 | 0.9196 | 0.9732 | +0.0536 | +0.0223 ~ +0.0893 | 2 | 14 | 204 | 4 | 0.004181 |
| 词法 vs 重排 | 0.9196 | 0.9732 | +0.0536 | +0.0223 ~ +0.0893 | 2 | 14 | 204 | 4 | 0.004181 |
| 混合 vs 重排 | 0.9732 | 0.9732 | +0.0000 | +0.0000 ~ +0.0000 | 0 | 0 | 218 | 6 | 1.000000 |

重排额外的排序指标（配对差 = 右 − 左）：

| 配对 | 指标 | 左 | 右 | 差 | 95% 区间 |
|---|---|---:|---:|---:|---|
| 词法 vs 重排 | mrr | 0.7275 | 0.7567 | +0.0291 | +0.0045 ~ +0.0538 |
| 词法 vs 重排 | ndcg | 0.7268 | 0.7618 | +0.0350 | +0.0140 ~ +0.0561 |
| 混合 vs 重排 | mrr | 0.7740 | 0.7567 | -0.0173 | -0.0420 ~ +0.0062 |
| 混合 vs 重排 | ndcg | 0.7795 | 0.7618 | -0.0177 | -0.0348 ~ -0.0014 |

## 代价

- 模型载入：0.543 秒（权重已在本地缓存，不含首次下载）。
- 语料向量构建：5.728 秒，794 块，dim=512，向量本体约 1626112 字节。
- 问句向量：0.571 秒，224 条。p95 不含这段，也不含模型载入。
- 内存：构建前 RSS 124908 KiB，构建后 RSS 633324 KiB，进程峰值 HWM 643680 KiB。
- 查询 p95：混合 82.543 ms，重排 90.681 ms，词法 69.783 ms。门槛 800 ms。
- 新增依赖没有写进 `requirements.txt`。测量用 fastembed 0.7.1，包名：huggingface-hub, loguru, mmh3, numpy, onnxruntime, pillow, py-rust-stemmers, requests, tokenizers, tqdm。完整版本约束在 `cost.json`。
- 补丁/失效：解析入库（`parse_document_text` / `confirm_paste`）不计算向量，新块 `vec` 为空。`invalidation_list` 只记主张 id，不改块向量。再次 `add_document` 会把块上的 `vec` 原样写入；空向量会覆盖旧向量。池中只要有一块缺向量，`rank_dense` 返回空，检索记 `bm25_fallback`，不会把这次结果标成 hybrid。本次冒烟清掉一块向量后，请求 hybrid，记录为 bm25_fallback；写回向量后恢复为 hybrid。

## 开关与回退

回退步骤（本次冒烟已做完，可复做）：

1. 只在 `RunContext.mode == "eval"` 时调用 `arm_eval_retrieval_mode`。
2. `arm_eval_retrieval_mode("hybrid")` 后 `try_retrieve`，轨迹 `retrieval_mode` 为 hybrid。
3. `arm_eval_retrieval_mode("hybrid+rerank")` 后同样为 hybrid+rerank。
4. 一键回到词法：`arm_eval_retrieval_mode("bm25")` 再查一次，轨迹为 bm25。
5. `mode == "online"` 时 `arm_eval_retrieval_mode` 抛出「生产路径不可强制 retrieval_mode」，检索仍是 bm25。
6. 不修改 `PRODUCTION_RETRIEVAL_MODE`。本次结束时它仍是 bm25。

冒烟记录：

- 请求 hybrid → 记录 hybrid，命中 10 条
- 请求 hybrid+rerank → 记录 hybrid+rerank，命中 10 条
- 请求 bm25 → 记录 bm25，命中 10 条
- 生产路径拒绝切臂：生产路径不可强制 retrieval_mode
- 生产路径实际检索：bm25
- 缺一块向量时请求 hybrid → bm25_fallback；写回后 → hybrid

## 清单

- 路径：`docs/evidence/issue-284/CHECKLIST.md`
- 分差条数：词法 vs 混合 224，词法 vs 重排 224，混合 vs 重排 208。

## 一句话建议

建议保持 bm25：混合相对词法的 Recall@10 配对差点估计 +0.0536（区间 +0.0223 到 +0.0893），但入库和补丁不写向量，池里缺一条向量就会整池降成 bm25_fallback，不能当成已经切到混合；重排相对混合的 Recall 配对差为 +0.0000，nDCG@10 配对差 -0.0177（区间 -0.0348 到 -0.0014），没有单独构成换默认的理由。

生产默认没有改。切换仍等真人终收。
