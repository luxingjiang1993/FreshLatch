# 检索默认臂决策链：目标 hybrid+rerank，尚未切换

本文是证据与说辞，供论文和面试引用。它不是切换授权。

写本文时 `PRODUCTION_RETRIEVAL_MODE` 仍是 `bm25`。本文不改这个常量，不新跑评测，不调用 DashScope 或任何付费 API。下面的数字都引自已落盘的报告或仓内标注文件；四位小数沿用各报告主表，未另作四舍五入。

当前决定（用户，经 Ronin 代理人转达）：保留 rerank 臂一起上，目标是切到 hybrid+rerank。理由是真实业务语料大、噪声多时 rerank 更有说服力。这条理由在本文的语料上没有被测量证明，登记为待在大语料上复测的假设。工程缺口在 [Issue #286](https://github.com/luxingjiang1993/FreshLatch/issues/286)。切换要等真人抽看 16 道 Recall 分差题之后终收。

## 1. 时间线

| 时间 | 事件 | 链接 |
|---|---|---|
| 2026-09-29 | I0 冒烟：BM25 基线 n=36，Recall@10=1.0000，MRR@10=0.7324。这是词法单臂，不是三臂对比。 | `docs/evidence/i0/ACCEPTANCE.md` |
| Phase A | 冒烟集 n=36 的四臂表：BM25 1.0000，dense 0.9722，hybrid 1.0000，hybrid+rerank 1.0000（p95=11.4ms，生产默认关）。因此保持 bm25，并要求另开 Hard-Gold。 | `docs/accounting-card.md`（数字真相源指向 `reports/retrieve-*.md`，Phase A / PR #167） |
| 2026-10-03 | Hard-Gold 骨架并入，断言仍 bm25。n=20，traps/对抗 8（40%）。 | [Issue #251](https://github.com/luxingjiang1993/FreshLatch/issues/251) · [PR #256](https://github.com/luxingjiang1993/FreshLatch/pull/256) |
| 2026-10-03 | 改臂授权闸：过线才允许开 Gate 实现票；本波不换臂。 | [Issue #257](https://github.com/luxingjiang1993/FreshLatch/issues/257) · `docs/adr/0033-hard-gold-过线与改臂授权闸.md` |
| 2026-10-03 | 同库复跑过线，未换臂。hard 集 BM25 Recall@10=0.6000，dense=0.6500，hybrid=0.7500，hybrid+rerank=0.7500，p95=67.3ms，rerank 门关。 | [Issue #259](https://github.com/luxingjiang1993/FreshLatch/issues/259) · `docs/evidence/hard-gold-arm/RERUN-20261003-259.md` |
| 2026-10-03 起 | 改臂实现票仍待人终收，本决策链不实施它。 | [Issue #260](https://github.com/luxingjiang1993/FreshLatch/issues/260) |
| 2026-10-07 | RET-01.3 x1 金标并入 main，commit `5de99c1`。模型双标 + Ronin 代理人（模型）代审，`human_row_review=false`。 | [PR #282](https://github.com/luxingjiang1993/FreshLatch/pull/282) |
| 2026-10-07 | x1 上 bm25 / dense / hybrid / hybrid+rerank 分列。本地 bge-small-zh-v1.5，不是 text-embedding-v4。建议只讨论 hybrid；rerank 预登记门关。 | [PR #283](https://github.com/luxingjiang1993/FreshLatch/pull/283) |
| 2026-10-07 | 切换前验证票：两臂都评，人终收，不改默认。 | [Issue #284](https://github.com/luxingjiang1993/FreshLatch/issues/284) |
| 2026-10-07 | 显著性、代价、656 条顺序分差清单、一键回退冒烟。书面建议保持 bm25。 | [PR #285](https://github.com/luxingjiang1993/FreshLatch/pull/285) |
| 2026-10-07 | 用户改决定：目标改为 hybrid+rerank，但先补工程缺口；切换仍等人抽看 16 题。本文与该票只记录，不实施。 | [Issue #286](https://github.com/luxingjiang1993/FreshLatch/issues/286) |

## 2. 早期 easy-gold：为什么保持 bm25，先做难金标

常被说成「bm25 / dense / hybrid 的 Recall@10 全是 1.0，所以没信息」。仓内原表不是这样。

`docs/accounting-card.md` 把该表标成演示 / 冒烟层（n=36），不报方差，不作统计显著。原表是：

| 臂 | Recall@10 | 判决 |
|---|---:|---|
| BM25（A0） | 1.0000 | 相对 A0 pass |
| dense | 0.9722 | 低于 BM25 |
| hybrid（RRF k=60） | 1.0000 | 通过线 pass |
| hybrid+rerank | 1.0000 | 非严格更好；p95=11.4ms；生产默认关 |

dense 是 0.9722，不是 1.0。BM25 已经顶满，hybrid 只是持平，rerank 没有严格优于 hybrid。预登记门因此不能改生产默认。hybrid 持平也不够换臂，还要另开 Hard-Gold。这就是 [Issue #251](https://github.com/luxingjiang1993/FreshLatch/issues/251) 的由来，不是「三臂都是 1.0 所以看不出差别」。

不要把这张表和 I0 的 BM25 单臂基线混成一句。`docs/evidence/i0/ACCEPTANCE.md` 只写了 n=36、Recall@10=1.0000、MRR@10=0.7324，那是词法冒烟，没有 dense。

随后的 Hard-Gold 小集（n=20）确实拉开了：BM25 0.6000，dense 0.6500，hybrid 0.7500，rerank 仍是 0.7500（[Issue #259](https://github.com/luxingjiang1993/FreshLatch/issues/259)）。过线只授权「可以开实现票讨论」，没有换臂。[Issue #260](https://github.com/luxingjiang1993/FreshLatch/issues/260) 到写本文时仍是 `ready-for-human`。

## 3. RET-01.3 金标（PR #282）

并入提交 `5de99c1`。题集 `data/exp/x1/questions.json`：267 题，主分母 `score_role=arm` 为 224，护栏 43。护栏不进 Recall、MRR、nDCG、McNemar。qtype 词表是 lexical / paraphrase / multi_hop（arm 上 60 / 119 / 45）。category 在臂题上是 hard 与 trap；adversarial 的 n=0。chunk=794。

标注协议写在 `data/exp/x1/LABELING-PROVENANCE.json` 与 `data/exp/x1/ret013-draft/PROTOCOL.md`：两个模型各自标注；影响打分的分歧、一致题里按种子 20261007 抽的约 20%，以及 12 条内容修正，由 Ronin 代理人（模型）受 owner 委托看过。`human_row_review=false`。不是人工逐行审核。

原 211 题的 A/B 一致度（`PROTOCOL.md`，不是 100%）：

- qtype 一致 141/211，κ=0.44
- arm/护栏一致 193/211，κ=0.73
- relevant 完全一致 141/211，平均 Jaccard 0.835
- answer_points 等价 102/211
- category 一致 136/211，κ=0.32
- 分歧 165 题，一致 46 题

### 合成模板陷阱 47 题单列

`data/exp/x1/SOURCES.md` 与 `ret013-draft/round4/summary.md`：第二部分是 16 个批次、同一模板（一篇旧口径、一篇现行口径，各 3 题），共 48 题。正式题集与这 48 个 id 的交集是 47。缺的是 `r4n-s2-d0-t1-91-qc`（盲标否决：问句要平均数，语料只有中位数）。这 47 题仍计入总体和 trap，分数必须单独一列。另有补批次 `r4n-s6-d2-t1-91-*` 三题，`labels-supplement.json` 写明 `blind_second_label=false`，没有另一份独立 A 稿，不在这 47 题里。

### 盲标 100% 一致：可疑点，不是质量证明

round4 的 54 题对照在 `data/exp/x1/ret013-draft/round4/blind-b/compare-b.json`。逐行计数（n=54）：

- `rel_eq` 为真：54/54
- `cat_a == cat_b`：54/54
- `kind_a == kind_b`：54/54
- `qtype_a == qtype_b`：44/54
- `ap_a == ap_b`：44/54
- decision：accept 53，reject 1（`r4n-s2-d0-t1-91-qc`）

relevant、category、陷阱类别是 100% 一致。qtype 和要点不是。被否的那题 relevant 仍然对齐，否决原因是答案歧义，不是双方标不一致。

这个 100% 可疑，原因写在同一批材料里：

- 起草方和盲标方都是 Ronin 代理人（模型）。`LABELING-PROVENANCE.json` 的 `round4.annotator_A` 与 `round4.blind_b` 都是这一身份；盲标说明是「本会话。先只看问句和语料，再对照 A」。这和原 211 题的 B（Cursor 云端代理，GPT-5.6 Sol，标注时没看过 A）不是同一套独立性。
- `round4/summary.md` 已把风险写在前面：16 个批次都是「两篇材料 + 三题」，问法相近。模板题上 relevant / category 全中，不能当成独立复核通过。
- 协议句是「relevant 与 category 一致则接受」。在模板题上，这条规则会把 100% 一致直接变成接受，抽样复查没有按原 211 题的 20% 再做一轮。provenance 写明 round4 新题不另抽 20%。

因此：金标可用作内部臂对比的固定分母，不能写成人工金标，也不能把 round4 的 100% 字段一致写成标注者间信度。

## 4. PR #283 分列结果（原样）

来源：[PR #283](https://github.com/luxingjiang1993/FreshLatch/pull/283) 的 `docs/evidence/x1-retrieval-modes/RESULT.md`。层是实验 / 冒烟，单次运行，不报方差。Recall@10 是 `recall_at_k`：top-10 里出现任一 relevant 记 1，否则 0，再宏平均，不是集合召回。p95 是单次 `time.perf_counter`，重复运行有毫秒级抖动。查询向量在计时前预计算。本地向量是 fastembed 的 `BAAI/bge-small-zh-v1.5`，dim=512。配置里的 `text-embedding-v4`（dim=1024）未跑。

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

相对 bm25 的总体 Recall@10 差：dense +0.0134（p95 14.594），hybrid +0.0536（p95 84.914），hybrid+rerank +0.0536（p95 87.253）。三臂的 p95 都低于 800ms。

同文件的 rerank 预登记门（相对 hybrid，不是相对 bm25）：hybrid 与 hybrid+rerank 的 Recall@10 都是 0.9732，rerank p95 87.253，`rerank_default_verdict` 为「生产默认关」。lexical 上 dense 0.9667、hybrid 0.9833，都低于 bm25 的 1.0000。hard 上 dense 0.9150 低于 bm25 的 0.9216。模板 47 题上 hybrid 的 Recall@10 与 bm25 同为 0.9787。

`summary.json` 里 check_x1：退出码 0，`trap_adversarial_ratio` 0.3169642857142857，`synthetic_ratio` 0.8299748110831234，`public_ratio` 0.17002518891687657，去污染命中 0，LCS 旗标 0。

#283 当时的书面建议是：只把 hybrid 放进讨论票，不为 rerank 另开切换票。那是测量建议，不是改臂授权。

## 5. PR #285 显著性、代价、回退（原样）

来源：[PR #285](https://github.com/luxingjiang1993/FreshLatch/pull/285) 的 `docs/evidence/issue-284/RESULT.md`。方法在跑数前写死：bootstrap 10000 次，seed=20261007，配对差 = 右 − 左，95% 线性插值百分位。顺序是三组 Recall，然后两组重排的 MRR，然后两组重排的 nDCG。McNemar 是 Recall 命中的精确二项、双侧。p95 与 #283 不是同一次计时，毫秒数不要混抄。

| 配对 | Recall 左 | Recall 右 | 差 | 95% 区间 | 只左中 | 只右中 | 都中 | 都未中 | McNemar p |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 词法 vs 混合 | 0.9196 | 0.9732 | +0.0536 | +0.0223 ~ +0.0893 | 2 | 14 | 204 | 4 | 0.004181 |
| 词法 vs 重排 | 0.9196 | 0.9732 | +0.0536 | +0.0223 ~ +0.0893 | 2 | 14 | 204 | 4 | 0.004181 |
| 混合 vs 重排 | 0.9732 | 0.9732 | +0.0000 | +0.0000 ~ +0.0000 | 0 | 0 | 218 | 6 | 1.000000 |

| 配对 | 指标 | 左 | 右 | 差 | 95% 区间 |
|---|---|---:|---:|---:|---|
| 词法 vs 重排 | mrr | 0.7275 | 0.7567 | +0.0291 | +0.0045 ~ +0.0538 |
| 词法 vs 重排 | ndcg | 0.7268 | 0.7618 | +0.0350 | +0.0140 ~ +0.0561 |
| 混合 vs 重排 | mrr | 0.7740 | 0.7567 | -0.0173 | -0.0420 ~ +0.0062 |
| 混合 vs 重排 | ndcg | 0.7795 | 0.7618 | -0.0177 | -0.0348 ~ -0.0014 |

代价（同文件）：

- 模型载入 0.543 秒（权重已在本地缓存，不含首次下载）。
- 语料向量构建 5.728 秒，794 块，dim=512，向量本体约 1626112 字节。
- 问句向量 0.571 秒，224 条。p95 不含这段，也不含模型载入。
- 内存：构建前 RSS 124908 KiB，构建后 RSS 633324 KiB，进程峰值 HWM 643680 KiB。
- 查询 p95：混合 82.543 ms，重排 90.681 ms，词法 69.783 ms。门槛 800 ms。
- fastembed 0.7.1 没有写进 `requirements.txt`。传递包名：huggingface-hub, loguru, mmh3, numpy, onnxruntime, pillow, py-rust-stemmers, requests, tokenizers, tqdm。

回退冒烟（eval 路径，结束时生产默认仍是 bm25）：

- 请求 hybrid → 记录 hybrid，命中 10 条
- 请求 hybrid+rerank → 记录 hybrid+rerank，命中 10 条
- 请求 bm25 → 记录 bm25，命中 10 条
- online 拒绝切臂，异常文案是「生产路径不可强制 retrieval_mode」，实际检索 bm25
- 清掉一块同 as_of 的向量后请求 hybrid → `bm25_fallback`；写回后恢复 hybrid

清单在该 PR 的 `docs/evidence/issue-284/CHECKLIST.md`：词法 vs 混合 224 条，词法 vs 重排 224 条，混合 vs 重排 208 条，合计 656。分差定义是 top-10 的 id 集合或顺序不同，所以远多于 Recall 不一致的 16 题。#285 的一句话建议是保持 bm25。用户在这之后把目标改成 hybrid+rerank；该建议不再当作最终产品决定，但工程和人审两项没有被这句改决定取消。

## 6. 为什么不直接切

四件事在切换前都还开着。

1. 未人审。金标不是人工逐行。#284 的 656 条建议是模型按规则起草的。切换终收指定的是真人抽看 16 道 Recall 分差题，这件事还没做。
2. 差距小，所以先做了显著性，而不是看见 +0.0536 就改默认。做完之后，词法 vs 混合的 Recall 区间是 +0.0223 ~ +0.0893，McNemar p=0.004181，区间不跨 0。这只说明在这 224 题、这一次固定排序上，混合的任一命中高于词法；它不取消人审，也不证明换默认已经安全。混合 vs 重排的 Recall 区间是 +0.0000 ~ +0.0000。
3. 代价。向量构建、约 629 MB 量级的进程峰值（HWM 643680 KiB），以及未入库的 fastembed 依赖。p95 仍低于 800 ms，延迟本身不是否决项。
4. 工程缺口。入库和补丁/失效路径不写向量。池中任一缺 `vec`，`rank_dense` 返回空，整次检索记 `bm25_fallback`。在这个缺口补上之前，把生产默认改成 hybrid，线上会在第一条缺向量时整池掉回词法，而且轨迹不会写成 hybrid。这就是 [Issue #286](https://github.com/luxingjiang1993/FreshLatch/issues/286) 要补的事：同步写向量、fastembed 入生产依赖、开关保留 `arm_eval_retrieval_mode("bm25")` 一键回退。本票不实施切换。

## 7. 本语料上 rerank 没有召回增益，以及为什么仍保留

实际精排函数是 `freshlatch.store.pipeline.rerank_lexical`。它只重排 hybrid 已经返回的 top-10：查询与块文本做 jieba 分词，按 token 重叠计数排序，原序作平局打破。函数注释写明「不是 bge，也不做 α 加权」。`requirements.txt` 里已有 `jieba==0.42.1` 和 `rank-bm25==0.2.2`。没有 bge-reranker，也没有第二套神经重排依赖。#286 要进生产依赖的是 fastembed 与 `BAAI/bge-small-zh-v1.5`，不是一个新的 reranker 包。

机制上，任一命中的 Recall@10 不可能因为这次重排变高：金标要么已经在这 10 条里，要么不在；重排只换这 10 条的次序。所以混合 vs 重排的 Recall 差是 +0.0000、discordant 是 0/0，是这个实现的结果，不是采样运气。排序指标上，重排相对混合的 nDCG@10 差是 -0.0177，区间 -0.0348 ~ -0.0014，整个在 0 下面；MRR 差 -0.0173，区间跨 0。

本语料也很难让这种重排显出召回收益：

- 混合的 arm Recall@10 已经是 0.9732，天花板高，剩下 6 题两臂都没中。
- 语料 794 块，`synthetic_ratio` 0.8299748110831234，相对干净，不是开放域噪声堆。
- 陷阱的操作化定义（`SOURCES.md`，category-rule-v2）是快照取代、同快照冲突陈述、元陈述。问的是哪一版、哪一快照、哪句「未复测 / 无新数据」在干扰。这是时效和版本问题，不是「相关但词面完全无关」的大规模语义噪声。词重叠重排解决不了「旧口径和新口径都含同一批词」。

保留 rerank 臂的理由因此只能写成假设，不能写成本实验的结论：真实业务语料更大、噪声更多时，重排（含现在这个词重叠重排，以及将来若另票更换的神经重排）可能在排序甚至在召回候选上更有用。该假设要在大语料上复测。复测前不得引用 #283 / #285 的 Recall 持平，去证明「rerank 已经赢了」或「rerank 已经该删」。

用户决定是保留这条臂，目标切到 hybrid+rerank。和 #285「建议保持 bm25」的关系是：统计和工程当时都不支持立刻改默认；产品目标改为两臂一起上之后，缺的仍是人审 16 题和 #286 的写向量路径。目标变化没有把生产常量改掉。

## 8. 真人要看的 16 道题

这 16 道是 #285 清单「词法 vs 混合」一节里，理由为「前 10 条里有金标，另一臂没有」的题，对应 McNemar 的 2 与 14。词法 vs 重排的 Recall 分差是同一组 id，因为重排不改变 top-10 集合。题干和三臂 top-10 在 PR #285 的 `CHECKLIST.md`，不在本文重复粘贴。

只词法中（2）：`p1-lx-06-new`，`s4-d0-t0-01-q6`。

只混合 / 重排中（14）：`s1-d0-04-q3`，`s1-d0-05-q4`，`s1-d2-01-q1`，`s2-d0-04-q2`，`s2-d1-01-q3`，`s3-d1-01-q1`，`s4-d0-t1-02-q4`，`s4-d2-t1-04-q1`，`s5-d0-t0-01-q3`，`s5-d0-t0-01-q5`，`s6-d0-t1-03-q3`，`r4m-s5-d3-t1-05-q4`，`r4m-s5-d3-t1-05-q5`，`r4n-s6-d2-t1-91-qc`。

其中 `r4n-s6-d2-t1-91-qc` 属于补批次，不在合成模板陷阱 47 题里，且没有第二份独立盲标。

## 9. 面试口述版（约 1 分钟）

生产默认还是 BM25。冒烟集 36 题上 BM25 和 hybrid 的 Recall@10 都是 1.0，dense 是 0.9722，更差，rerank 也没有严格超过 hybrid，所以先保持 BM25，去开难金标，不是因为三臂都满分。224 道臂题上 hybrid 是 0.9732，BM25 是 0.9196，配对差 +0.0536，区间 +0.0223 到 +0.0893。rerank 用的是 `rerank_lexical`，只对 hybrid 已有的前 10 条做结巴词重叠排序，召回因此和 hybrid 相同；794 块里约 83% 是合成的，陷阱是快照和版本，不是词面无关的大噪声。目标仍定成 hybrid 加 rerank，因为真实业务更大更吵，这是待复测的假设。现在不切：金标是模型双标加模型代审，模板题 relevant 和 category 盲标 54/54 全一致，这个 100% 可疑；入库还不写向量，缺一块就整池 bm25_fallback；要等真人看完 16 道召回分差题。

## 10. 论文可用的方法与局限性

方法。在固定金标和固定 as_of 过滤下比较四条检索臂。词法臂是 BM25Okapi 加 jieba 分词。稠密臂是本地 fastembed 的 BAAI/bge-small-zh-v1.5（512 维余弦），不是配置中的 DashScope text-embedding-v4；该付费路径未调用。混合臂用 RRF（k=60）融合名次，不做分数的 α 加权。hybrid+rerank 调用 `rerank_lexical`，只对混合臂已经返回的 top-10 按查询词与块文本的 jieba token 重叠计数重排。主指标是 arm 题（n=224）上的 Recall@10：top-10 中出现任一 relevant 记 1，再宏平均，不是集合召回。排序指标是 MRR@10，以及二元相关的 nDCG@10（理想排序把金标放在最前）。显著性是配对 bootstrap 10000 次、种子 20261007、配对差的 95% 百分位区间，以及 Recall 命中上的精确双侧 McNemar。延迟是单次 perf_counter 的 p95，门槛 800 ms，不含模型加载和问句向量预计算。合成模板陷阱 47 题单列，不从总分母剔除。

局限性。金标由两个模型标注，审核由 Ronin 代理人（模型）受委托完成，`human_row_review=false`，不是人工逐行金标。原 211 题的 relevant 完全一致只有 141/211；round4 的 54 道新题由同一模型会话先起草再作盲标，relevant、category 与陷阱类别 54/54 一致，其中 48 道为同一模板，这种一致不能当作独立标注可靠性，qtype 也只对齐 44/54。语料 794 块，合成占比 0.8299748110831234，混合臂 Recall@10 已到 0.9732。任一命中的 Recall@10 对「只重排已有 top-10」的词重叠重排不敏感，因此召回持平是机制结果。陷阱按快照取代、同快照冲突和元陈述操作化，测的是时效与版本，不覆盖开放域里词面无关的相关性噪声。混合相对词法的 nDCG 优势与重排相对混合的 nDCG 劣势，都不能外推成「大语料上重排有增益」；后者只登记为待复测假设。p95 是单次计时。生产入库与失效路径尚未同步写向量，缺一块向量会使整次混合检索记为 `bm25_fallback`。基于以上限制，本文不把生产默认报告为已经切换。
