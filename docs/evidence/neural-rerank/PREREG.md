# 神经 reranker 对照 · 跑数前口径

锁死日期：2026-10-07。写完这一页之后不得改判据、不得改种子、不得改门槛。结果写在 `RESULT.md`，不回写本页。

本实验不改 `PRODUCTION_RETRIEVAL_MODE`，不把神经 reranker 写进 `requirements.txt`。不调用 DashScope，不提交密钥。

## 数据

- 金标：`data/exp/x1/questions.json`，与 `main` `50adc3251737c318815105b3562a823198b80dc3` 上的该文件一致。
- 分母：`score_role=arm`，n=224。护栏题不进 Recall@10、MRR@10、nDCG@10、McNemar。
- 人工审核只覆盖 DECISION-16 的 16 道题。其余仍是模型双标加 Ronin 代理人（模型）代审，`human_row_review=false`。

## 候选

- hybrid 的做法与生产评测臂相同：BM25Okapi + jieba，dense 为本地 `BAAI/bge-small-zh-v1.5`（512 维），RRF k=60。embedding 库用生产钉死的 fastembed 0.7.1，不用评测 venv 里的 0.8.1，避免候选漂移。
- 主列 K=10：hybrid 的前 10 条。
- 加报列 K=30：hybrid 的前 30 条，重排后只取前 10 条。这一列单列，不进入取舍句。
- 左臂：`rerank_lexical`（jieba token overlap）。
- 右臂：`BAAI/bge-reranker-base`，fastembed `TextCrossEncoder`，CPU。分数高的在前；分数相同则保持 hybrid 原序。
- `BAAI/bge-reranker-v2-m3` 不是本页的决策臂。fastembed 的 `TextCrossEncoder` 支持列表里没有它时，本轮可以不跑，并在 RESULT 里写明原因。若另用本地 `sentence-transformers` `CrossEncoder` 跑了，只作加报，不改下面的取舍句。

## 指标

- Recall@10、MRR@10、nDCG@10（二元相关）。函数是 `retrieve_eval.recall_at_k`、`mrr_at_k`、`ndcg_at_k`。
- 配对差 = 神经 − lexical。
- bootstrap 10000 次，种子 20261007，95% 线性插值百分位。主列共用一条 `random.Random(20261007)`，顺序是 Recall，然后 MRR，然后 nDCG。K=30 另起一条同样的种子，不接着主列的 rng 往下抽。
- McNemar 用 Recall@10 是否命中，精确二项、双侧：较小一侧的累计概率乘 2，封顶 1。
- K=10 两边必须是同一组 id 的排列。Recall@10 因此必须逐题相同。有一题不同，这次运行作废，不写取舍句。

## 代价

- p95 用 `retrieve_eval._p95_ms`。样本是每一题重排本身的 `perf_counter` 秒数，不含 hybrid 检索，不含模型加载。门槛 ≤800ms。设备是 CPU。
- 首次加载时间单独记：构造 `TextCrossEncoder` 到第一次 `rerank` 返回。不并进 p95。
- 另报权重文件字节数，以及评测依赖文件 `requirements-eval-neural-rerank.txt`。生产 `requirements.txt` 不得出现 `bge-reranker`。
- 这个 p95 不与 #283、#285 的检索 p95 混成一张表。

## 取舍句

只看主列 K=10、模型 `BAAI/bge-reranker-base`。四条同时成立才写「建议另开切换票」：

1. nDCG@10 配对差的 95% 区间下界 > 0
2. nDCG@10 配对差的点估计 ≥ 0.01
3. MRR@10 配对差的 95% 区间下界 > 0
4. 神经 rerank 的 p95 ≤ 800ms

否则写「保持 lexical rerank，等大语料复测」。

两种写法都不是切换。本实验不改 `PRODUCTION_RETRIEVAL_MODE`。K=30 和 v2-m3 都不能把这句改掉。
