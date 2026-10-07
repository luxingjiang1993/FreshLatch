# 检索默认方式的决策链：目标是 hybrid+rerank，尚未切换

本文给论文和面试用。它记录一条决策，不是切换许可。

生产默认仍是 BM25。代码常量 `PRODUCTION_RETRIEVAL_MODE` 的值是 `bm25`。本文不改这行代码，不重跑评测，不调用阿里云 DashScope 的付费接口。

表里的四位小数照抄各报告主表。json 里的更长小数在对应小节注明，不另做一次四舍五入。

后文用这些英文名，不再另起译名：

- BM25：BM25Okapi，用结巴（jieba）分词。
- dense：把查询和 chunk 变成 embedding，按余弦排序。
- hybrid：BM25 与 dense 各自的名次做倒数秩融合（RRF，常数 k=60）。加的是名次的倒数，不是两路分数乘一个系数。
- hybrid+rerank：函数 `rerank_lexical` 只对 hybrid 已经给出的前 10 条做 rerank。做法是数结巴词的重叠，不是交叉编码器，也没有单独的 rerank 模型。
- Recall@10：前 10 条里出现任一 gold set 中的 chunk 记 1，否则记 0，再对题取平均。不是「gold set 里的 chunk 找回了百分之几」。
- MRR@10、nDCG@10、p95。

当前决定（用户，经 Ronin 代理人转达）：rerank 臂留下，目标改成 hybrid+rerank。理由是真实业务的语料更大、噪声更多，rerank 更有说服力。这条理由在本文的语料上没有测到，登记为待复测的假设。工程缺口在 [Issue #286](https://github.com/luxingjiang1993/FreshLatch/issues/286)。切换要等真人看完第 9 节的 16 道题。

## 1. 时间线

| 时间 | 事件 | 出处 |
|---|---|---|
| 2026-09-28 | BM25 冒烟基线落盘：28 个文件、84 个 chunk、n=36，Recall@10=1.0000，MRR@10=0.7324。只有 BM25，没有 dense。 | `reports/retrieve-bm25-baseline.md` |
| 2026-09-29 | I0 验收按同一指标复跑：n=36，Recall@10=1.0000，MRR@10=0.7324。 | `docs/evidence/i0/ACCEPTANCE.md` |
| Phase A | 同一冒烟集的四臂表。dense 的 embedding 模型是 `text-embedding-v4`。BM25 1.0000，dense 0.9722，hybrid 1.0000，hybrid+rerank 1.0000（p95=11.4 ms，生产默认关）。因此保持 BM25，并要求另开 Hard-Gold。 | `reports/retrieve-arm-compare.md`、`reports/retrieve-rerank-compare.md`、`docs/accounting-card.md`（叙事页指向 Phase A / PR #167） |
| 2026-10-02 | Hard-Gold 骨架并入。n=20，陷阱或对抗 8 题（40%）。验收断言默认臂仍是 bm25。 | [Issue #251](https://github.com/luxingjiang1993/FreshLatch/issues/251) · [PR #256](https://github.com/luxingjiang1993/FreshLatch/pull/256) · `docs/evidence/i3/ACCEPTANCE.md` |
| 2026-10-03 | 改臂闸：过线才允许开实现票。这一轮不换臂。 | [Issue #257](https://github.com/luxingjiang1993/FreshLatch/issues/257) · `docs/adr/0033-hard-gold-过线与改臂授权闸.md` |
| 2026-10-03 | Hard-Gold 同库复跑过线，未换臂。dense 的 embedding 仍是 `text-embedding-v4`（1024 维，94 个 chunk）。BM25 0.6000，dense 0.6500，hybrid 0.7500，hybrid+rerank 0.7500，p95=67.3 ms，rerank 门关闭。 | [Issue #259](https://github.com/luxingjiang1993/FreshLatch/issues/259) · `docs/evidence/hard-gold-arm/RERUN-20261003-259.md` |
| 2026-10-03 起 | 改臂实现票仍等人收。本文不实施它。 | [Issue #260](https://github.com/luxingjiang1993/FreshLatch/issues/260) |
| 2026-10-07 | RET-01.3 的 x1 gold set 并入 main，提交 `5de99c1`。两个模型标注，Ronin 代理人（模型）代审，`human_row_review=false`。 | [PR #282](https://github.com/luxingjiang1993/FreshLatch/pull/282) |
| 2026-10-07 | x1 上四臂分列。dense 改用本地 embedding `BAAI/bge-small-zh-v1.5`。配置里的 `text-embedding-v4` 未跑。当时书面建议只讨论 hybrid；rerank 的预登记门关闭。 | [PR #283](https://github.com/luxingjiang1993/FreshLatch/pull/283) |
| 2026-10-07 | 切换前验证票：hybrid 与 hybrid+rerank 都要评，真人终收，不改默认。 | [Issue #284](https://github.com/luxingjiang1993/FreshLatch/issues/284) |
| 2026-10-07 | 显著性、代价、656 条顺序分差清单、一键回到 BM25 的冒烟。书面建议保持 bm25。 | [PR #285](https://github.com/luxingjiang1993/FreshLatch/pull/285) |
| 2026-10-07 | 用户把目标改成 hybrid+rerank，先补工程缺口。切换仍等真人看 16 题。本文和这张票只记录，不实施。 | [Issue #286](https://github.com/luxingjiang1993/FreshLatch/issues/286) |

## 2. 冒烟集 36 题：不是三臂都满分

有一种说法是：BM25、dense、hybrid 的 Recall@10 都是 1.0，所以看不出差别，于是继续用 BM25。仓内原表不是这样。

`docs/accounting-card.md` 把这张表标成演示 / 冒烟（n=36），不报方差，也不宣称统计显著。数字来自 `reports/retrieve-arm-compare.md` 与 `reports/retrieve-rerank-compare.md`：

| 臂 | Recall@10 | 报告里的判决 |
|---|---:|---|
| BM25（A0） | 1.0000 | 相对 A0 通过；过期主张回放通过 |
| dense | 0.9722 | 低于 BM25 |
| hybrid（RRF k=60） | 1.0000 | 不低于 BM25 与 dense 中较差的一臂，通过线通过 |
| hybrid+rerank | 1.0000 | 没有严格好于 hybrid；p95=11.4 ms；生产默认关 |

dense 是 0.9722，没有满分。BM25 已经到顶，hybrid 只是持平，rerank 没有严格好于 hybrid。预登记的门要求 rerank 的 Recall@10 严格高于 hybrid，并且 p95 不超过 800 ms，两条同时成立才考虑把 rerank 设为默认。这次两条没齐，所以不能改默认。hybrid 与 BM25 持平也不够换臂，还要另开 Hard-Gold。这是 [Issue #251](https://github.com/luxingjiang1993/FreshLatch/issues/251) 的由来。

这次 dense 用的 embedding 是 `text-embedding-v4`（`reports/retrieve-arm-compare.md` 写明「模型: text-embedding-v4」）。rerank 对比页写明：对比臂是本地词重叠精排，不是 bge，也不是分数加权。语料是 28 个文件、84 个 chunk，基线报告日期 2026-09-28。不要把这张表和后面 x1 的本地 512 维 embedding 当成同一次测量。

`docs/evidence/i0/ACCEPTANCE.md` 在 2026-09-29 复跑的是 BM25 单臂：n=36，Recall@10=1.0000，MRR@10=0.7324。那一页没有 dense 的 0.9722。

## 3. Hard-Gold 小集

2026-10-02 的骨架（[PR #256](https://github.com/luxingjiang1993/FreshLatch/pull/256)）把 Hard-Gold 分成独立文件：n=20，陷阱或对抗 8 题，占 40%。验收断言默认臂仍是 bm25。

2026-10-03 的同库复跑（[Issue #259](https://github.com/luxingjiang1993/FreshLatch/issues/259)）拉开了分数，仍未换臂：

- BM25 Recall@10 = 0.6000，与 A0 相同
- dense = 0.6500
- hybrid = 0.7500，不低于 min(0.6000, 0.6500)，通过线通过
- hybrid+rerank = 0.7500，p95 = 67.3 ms，判决为生产默认关

这次 dense 索引由 `scripts/build_dense_index.py` 重建，embedding 模型仍是 `text-embedding-v4`，维度 1024，chunk 数 94（正文 84，陷阱 10）。它和下一节 x1 的 `BAAI/bge-small-zh-v1.5`（512 维）不是同一个 embedding，两套 Recall@10 不能横比。

过线的书面含义是：可以开改臂实现票讨论。生产默认仍是 bm25，直到实现票由人收下。[Issue #260](https://github.com/luxingjiang1993/FreshLatch/issues/260) 到写本文时仍是 `ready-for-human`。

## 4. RET-01.3 gold set（PR #282）

并入提交 `5de99c1`。题集 `data/exp/x1/questions.json` 共 267 题。主分母是作答臂 `score_role=arm`，224 题。护栏题 43 道，不进 Recall@10、MRR、nDCG@10 和 McNemar。

题型（qtype）全库是字面 lexical 66、改写 paraphrase 156、多跳 multi_hop 45。作答臂上是 60 / 119 / 45，多出来的字面题和改写题在护栏里。类别（category）全库是普通难例 hard 153、陷阱 trap 114，没有对抗题 adversarial。作答臂上是 hard 153、trap 71。43 道护栏题全部是 trap。chunk 794。

`questions.json` 的 meta：`human_row_review` 为 false，审阅者写的是「Ronin 代理人（模型），受 owner 委托」。类别规则是 category-rule-v2，题型规则是 qtype-kw-v1。

标注协议在 `data/exp/x1/LABELING-PROVENANCE.json` 和 `data/exp/x1/ret013-draft/PROTOCOL.md`。原 211 题由两个模型各自标注。A 是助手起草的稿。B 是 Cursor 云端代理（GPT-5.6 Sol），标注时没看过 A。影响打分的分歧、一致题里按种子 20261007 抽取的约 20%（9 题），以及 12 条内容修正，由 Ronin 代理人（模型）受委托看过。其余分歧按写死的规则合并。这不是人工逐行审。

原 211 题的一致度（`PROTOCOL.md`）：

- 题型一致 141/211，κ=0.44
- 作答臂 / 护栏一致 193/211，κ=0.73
- 证据 chunk 完全一致 141/211，平均 Jaccard 0.835
- 要点等价 102/211
- 类别一致 136/211，κ=0.32
- 分歧 165 题，一致 46 题

### 合成模板陷阱，47 题单独成列

`data/exp/x1/SOURCES.md` 与 `ret013-draft/round4/summary.md`：第二部分是 16 个批次、同一模板。每个批次两篇材料（一篇旧口径、一篇现行口径），各出 3 题，共 48 题。正式题集与这 48 个 id 的交集是 47。缺的是 `r4n-s2-d0-t1-91-qc`。盲标否决的原因是：问句要平均数，语料只有中位数 11 分钟。这 47 题仍算进总分和陷阱分，另外单列，避免模板把总分开高或开低。

另有补批次 `r4n-s6-d2-t1-91` 的 3 题。`labels-supplement.json` 写明 `blind_second_label` 为 false，没有另一份独立的 A 稿。这 3 题不在 47 题里。

### 盲标 100% 一致是可疑点

第四轮 54 题的对照在 `data/exp/x1/ret013-draft/round4/blind-b/compare-b.json`。逐行计数（n=54）：

- 证据 chunk 相等：54/54
- 类别相等：54/54
- 陷阱子类相等：54/54
- 题型相等：44/54
- 要点相等：44/54
- 决定：接受 53，拒绝 1（`r4n-s2-d0-t1-91-qc`）

证据、类别、陷阱子类是 100% 一致。题型和要点不是。被拒的那题证据仍然对齐，拒因是答案有歧义，不是双方标了不同的 chunk。

这个 100% 不能当成标注质量证明：

- 起草和盲标都是 Ronin 代理人（模型）。`LABELING-PROVENANCE.json` 里第四轮的 A 与盲标 B 都是这一身份。盲标说明是本会话先看问句和语料，再对照 A。这和原 211 题那个没看过 A 的 GPT-5.6 Sol 不是同一套独立性。
- `round4/summary.md` 已写风险：16 个批次都是「两篇材料加三题」，问法相近。
- 合并规则是「证据和类别一致就接受」。模板题上，100% 一致会直接变成接受。provenance 写明第四轮新题不再另抽 20%。

因此这套 gold set 可以当内部比臂的固定分母。它不是人工 gold set。第四轮的 100% 字段一致也不是标注者间信度。

## 5. PR #283 的分列结果

来源是 [PR #283](https://github.com/luxingjiang1993/FreshLatch/pull/283) 的 `docs/evidence/x1-retrieval-modes/RESULT.md`。层级是实验 / 冒烟，单次运行，不报方差。p95 来自单次计时，再跑会有毫秒级抖动。query embedding 在计时前算好，p95 不含加载模型，也不含网络 embedding。

本地 dense embedding 是 fastembed 的 `BAAI/bge-small-zh-v1.5`，512 维。#283 的 RESULT 只写库名 fastembed，没写版本号。版本 0.7.1 记在 #285 的 `summary.json`（`fastembed_version`）。

配置 `data/exp/x1/config.json` 写的是 `text-embedding-v4`、1024 维。这一路没跑。原因在 #283 的 RESULT：该路径只在 `embeddings.py` 里请求 DashScope，本测量禁止付费接口。`embeddings.py` 的地址是 DashScope 兼容模式，没有密钥会直接失败，不会改走本地 embedding。所以 x1 的 dense 分不是 `text-embedding-v4` 的分，也不能和上一节 1024 维的 Hard-Gold dense 分横比。

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

相对 BM25 的总体 Recall@10 差：dense +0.0134（p95 14.594），hybrid +0.0536（p95 84.914），hybrid+rerank +0.0536（p95 87.253）。三臂的 p95 都低于 800 ms。按「Recall@10 严格高于 BM25 且 p95≤800 ms」，三臂都过这条线。#283 仍只建议讨论 hybrid：字面题上 dense 0.9667、hybrid 0.9833，都低于 BM25 的 1.0000；普通难例上 dense 0.9150，低于 BM25 的 0.9216。模板 47 题上 hybrid 与 BM25 同为 0.9787，dense 是 1.0000。

相对 hybrid 的 rerank 门：两边 Recall@10 都是 0.9732，rerank p95 87.253，判决「生产默认关」。门要求 Recall@10 严格高于 hybrid。`rerank_lexical` 只对 hybrid 已给出的前 10 条做 rerank，任一命中的 Recall@10 在这个实现下不会更高。

`summary.json` 里的 check_x1：退出码 0，`trap_adversarial_ratio` 0.3169642857142857，`synthetic_ratio` 0.8299748110831234，`public_ratio` 0.17002518891687657，去污染命中 0，许可证违规 0，最长公共子串旗标 0。

#283 的书面建议是测量建议：只把 hybrid 放进讨论票，不为 rerank 另开切换票。它不是改默认的授权。

## 6. PR #285 的显著性、代价和 fallback

来源是 [PR #285](https://github.com/luxingjiang1993/FreshLatch/pull/285) 的 `docs/evidence/issue-284/RESULT.md`。方法在跑数前写死：bootstrap 10000 次，种子 20261007，配对差是右减左，95% 区间用线性插值百分位。顺序是三组 Recall@10，然后两组 rerank 的 MRR，然后两组 rerank 的 nDCG@10。McNemar 看的是 Recall@10 是否命中，精确二项、双侧。

下面的四位小数是 RESULT.md 的主表。`significance.json` 里的原始值更长，例如 BM25 的 Recall@10 0.9196428571428571，hybrid 的 Recall@10 0.9732142857142857，差 0.05357142857142857，McNemar 双侧 p 为 0.004180908203124997。主表写成 0.9196、0.9732、+0.0536、0.004181。含义相同，精度不同。#285 的 p95 与 #283 不是同一次计时，毫秒数不要并成一张表。

| 配对 | Recall@10 左 | Recall@10 右 | 差 | 95% 区间 | 只左中 | 只右中 | 都中 | 都未中 | McNemar p |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| BM25 vs hybrid | 0.9196 | 0.9732 | +0.0536 | +0.0223 ~ +0.0893 | 2 | 14 | 204 | 4 | 0.004181 |
| BM25 vs rerank | 0.9196 | 0.9732 | +0.0536 | +0.0223 ~ +0.0893 | 2 | 14 | 204 | 4 | 0.004181 |
| hybrid vs rerank | 0.9732 | 0.9732 | +0.0000 | +0.0000 ~ +0.0000 | 0 | 0 | 218 | 6 | 1.000000 |

| 配对 | 指标 | 左 | 右 | 差 | 95% 区间 |
|---|---|---:|---:|---:|---|
| BM25 vs rerank | MRR | 0.7275 | 0.7567 | +0.0291 | +0.0045 ~ +0.0538 |
| BM25 vs rerank | nDCG@10 | 0.7268 | 0.7618 | +0.0350 | +0.0140 ~ +0.0561 |
| hybrid vs rerank | MRR | 0.7740 | 0.7567 | -0.0173 | -0.0420 ~ +0.0062 |
| hybrid vs rerank | nDCG@10 | 0.7795 | 0.7618 | -0.0177 | -0.0348 ~ -0.0014 |

代价（RESULT.md；原始秒数在 `cost.json`）：

- 模型载入：报告 0.543 秒（`model_load_s` 0.5430166969999846）。权重已在本地缓存，不含首次下载。
- corpus embedding：报告 5.728 秒（`index_build_s` 5.728331330000174），794 个 chunk，512 维，embedding 本体 1626112 字节。
- query embedding：报告 0.571 秒（`query_embed_s` 0.5705401449999954），224 条。p95 不含这段，也不含模型载入。
- 内存：构建前常驻 124908 KiB，构建后 633324 KiB，进程峰值 643680 KiB。
- 查询 p95：hybrid 82.543 ms，rerank 90.681 ms，BM25 69.783 ms。门槛 800 ms。原始值在 `cost.json` 的 `p95_ms`：BM25 69.78307600002154，hybrid 82.5428959999499，rerank 90.68060099980357。
- fastembed 0.7.1 没有写进 `requirements.txt`。RESULT 列出的包名：huggingface-hub、loguru、mmh3、numpy、onnxruntime、pillow、py-rust-stemmers、requests、tokenizers、tqdm。版本区间在 `cost.json` 的 `fastembed_requires`，本文不收成单个版本号。

回到 BM25 的冒烟走的是评测模式。结束时生产默认仍是 bm25。

- 请求 hybrid，记录为 hybrid，命中 10 条。
- 请求 hybrid+rerank，记录为 hybrid+rerank，命中 10 条。
- 请求 BM25，记录为 bm25，命中 10 条。
- 在线模式拒绝切臂，异常文案是「生产路径不可强制 retrieval_mode」，实际检索仍是 bm25。
- 清掉一个与问句同一快照的 chunk embedding 后再请求 hybrid，记录为 `bm25_fallback`。写回 embedding 后恢复为 hybrid。

清单在该 PR 的 `docs/evidence/issue-284/CHECKLIST.md`。分差定义是前 10 条的证据编号集合或顺序不同，所以条数远多于 Recall@10 不一致的 16 题。清单由模型按固定规则起草，还没有人逐条看过。建议计数：

- BM25 vs hybrid：224 题。保持 bm25 172，可议 hybrid 48，可议 hybrid+rerank 0，需要改题 4。
- BM25 vs rerank：224 题。保持 bm25 172，可议 hybrid 0，可议 hybrid+rerank 48，需要改题 4。
- hybrid vs rerank：208 题。保持 bm25 149，可议 hybrid 36，可议 hybrid+rerank 19，需要改题 4。

224 + 224 + 208 = 656。可议的 48 题包含「两边都命中、但一边把 gold set 排得更前」的题，不等于第 9 节那 16 道 Recall@10 分差题。

#285 的一句话建议是保持 bm25。用户在这之后把目标改成 hybrid+rerank。那句建议不再当作最终产品决定。人审和工程缺口这两项并没有因此取消。

## 7. 为什么当时不直接切，以及 #286 要补什么

四件事在切换前都还开着。

1. 还没有人审。gold set 不是人工逐行审。656 条建议是模型起草的。终收看的是 16 道 Recall@10 分差题，这件事还没做。
2. 差距先做了显著性，而不是看见 +0.0536 就改默认。做完之后，BM25 对 hybrid 的 Recall@10 区间是 +0.0223 到 +0.0893，不跨 0，McNemar p 的主表值是 0.004181。这只说明在这 224 题、这一次固定排序上，hybrid 的任一命中高于 BM25。它不代替人审，也不说明换默认已经安全。hybrid 对 rerank 的 Recall@10 区间是 +0.0000 到 +0.0000。
3. 有代价。embedding 要现算，进程峰值 643680 KiB，fastembed 还没进生产依赖。p95 仍低于 800 ms，延迟本身不是否决项。
4. 入库和补丁还不写 embedding。`parse_document_text` 构造 chunk 时不填 `vec`（默认空）。`confirm_paste` 确认后直接 `add_document`。`add_document` 用 `INSERT OR REPLACE` 把 chunk 上的 `vec` 原样写入，空 embedding 会盖掉旧 embedding。`add_invalidation` 只记主张 id，不改 chunk embedding。`rank_dense` 只要池里有一个 chunk 缺 embedding 或维度不符就返回空，调用方把这次检索记成 `bm25_fallback`，不会标成 hybrid。#285 的冒烟清掉一个 chunk 的 embedding 后，请求 hybrid，记录就是 `bm25_fallback`。

[Issue #286](https://github.com/luxingjiang1993/FreshLatch/issues/286) 只补这个缺口，不实施切换，也不改 `PRODUCTION_RETRIEVAL_MODE`：

- 入库、补丁、失效三条路径同步写 embedding，避免整池掉成 `bm25_fallback`。缺 embedding 时仍须记 `bm25_fallback`，不能把降级结果标成 hybrid。
- 把 fastembed 和 `BAAI/bge-small-zh-v1.5`（512 维）写入生产依赖。现用精排是 `rerank_lexical`，只用已经在 `requirements.txt` 里的结巴。不新增神经 rerank 包，也不把没评过的 bge-reranker 写进依赖。
- 开关留下一键回到 BM25：评测模式下 `arm_eval_retrieval_mode("bm25")`。在线模式仍拒绝强制切臂。

切换不在 #286 里。真人看完 16 题之后另行终收。

## 8. 这批语料上 rerank 没有 Recall@10 增益，以及为什么仍留下

`rerank_lexical`（`src/freshlatch/store/pipeline.py`）的注释是：本地词重叠精排，只处理已有候选；不是 bge，也不做分数加权。实现是：查询和 chunk 文本都用 `jieba.lcut` 切词，重叠个数多的排前面；重叠相同则保持 hybrid 原来的次序。`rank-bm25` 只供 BM25 臂的 BM25Okapi 使用，rerank 不调用它。这里没有 rerank 模型。

hybrid 臂先在整池上做倒数秩融合，再截成前 10 条。rerank 只交换这 10 条的次序（`InMemoryStore` 在 `hybrid+rerank` 分支里对融合结果调用 `rerank_lexical`）。gold set 里的相关 chunk 要么已经在这 10 条里，要么不在。任一命中的 Recall@10 因此不会上升。hybrid 对 rerank 的 Recall@10 差是 +0.0000、不一致题是 0 对 0，是这个实现的结果，不是抽样碰巧。排序上，rerank 相对 hybrid 的 nDCG@10 差是 -0.0177，区间 -0.0348 到 -0.0014，整个在 0 下面。MRR 差是 -0.0173，区间跨过 0。

这批语料也很难让这种 rerank 显出 Recall@10 差别：

- hybrid 的作答臂 Recall@10 已经是 0.9732。hybrid 与 rerank 都没命中的题是 6 道。
- chunk 794，`synthetic_ratio` 为 0.8299748110831234，大部分是合成稿，不是开放域噪声堆。
- 陷阱按 category-rule-v2 操作化（`SOURCES.md`）：快照取代、同一快照里互相冲突的说法、元陈述（未复测、无新数据、待发布、未入账、不再列入跟踪）。问的是哪一版还算数。旧口径和新口径往往共用一批词，数词重叠分不出哪个 chunk 是现行值。

留下 rerank 臂的理由只能写成假设：真实业务语料更大、噪声更多时，把已经进入前 10 条的 chunk 再排一次，读起来可能更有说服力。本实验没有证明它。复测要在大语料上做，看排序是否更站得住。这次 Recall@10 持平，是因为 rerank 只处理了前 10 条。即便以后另票换成交叉编码器，只要仍只处理这 10 条，任一命中的 Recall@10 同样不会上升。#283 和 #285 的 Recall@10 持平，既不能用来证明 rerank 已经赢了，也不能用来证明 rerank 该删。

用户决定是留下这条臂，目标切到 hybrid+rerank。#285 当时的统计和工程都不支持立刻改默认。目标改了之后，缺的仍是人审 16 题，以及 #286 的写 embedding 路径。生产常量没有改。

## 9. 真人要看的 16 道题

这 16 道来自 #285 清单里 BM25 vs hybrid 那一节，理由是「前 10 条里有 gold set 的 chunk，另一臂没有」。它们对应 McNemar 的 2 与 14。BM25 对 rerank 的 Recall@10 分差是同一组 id，因为 rerank 不改变这 10 条的编号集合。题干和三臂前 10 条在 PR #285 的 `CHECKLIST.md`，本文不重复粘贴。

只 BM25 命中（2）：`p1-lx-06-new`，`s4-d0-t0-01-q6`。

只 hybrid / rerank 命中（14）：`s1-d0-04-q3`，`s1-d0-05-q4`，`s1-d2-01-q1`，`s2-d0-04-q2`，`s2-d1-01-q3`，`s3-d1-01-q1`，`s4-d0-t1-02-q4`，`s4-d2-t1-04-q1`，`s5-d0-t0-01-q3`，`s5-d0-t0-01-q5`，`s6-d0-t1-03-q3`，`r4m-s5-d3-t1-05-q4`，`r4m-s5-d3-t1-05-q5`，`r4n-s6-d2-t1-91-qc`。

`r4n-s6-d2-t1-91-qc` 属于补批次，不在合成模板陷阱 47 题里，也没有第二份独立盲标。

## 10. 面试口述（约 1 分钟）

默认还是 BM25。36 题的冒烟里，BM25 和 hybrid 的 Recall@10 都是 1.0，dense 是 0.9722，没有一起满分。那次 dense 的 embedding 是 text-embedding-v4，所以我们保持 BM25，先做 Hard-Gold。后来 224 道打分题上，hybrid 是 0.9732，BM25 是 0.9196，差 +0.0536，区间从 +0.0223 到 +0.0893。rerank 不加载模型，只把 hybrid 已经给出的前 10 条按结巴词的重叠重新排队，Recall@10 因此和 hybrid 一样。这批语料 794 个 chunk，合成占比约 0.83，陷阱主要是哪一版说法还算数。业务语料更大、更吵时，rerank 可能更有用，这还没测。现在不切：gold set 是模型标注、模型代审；模板题的证据和类别盲标 54 道全一致，这本身可疑；入库还不写 embedding；要等真人看完 16 道 Recall@10 分差题。

## 11. 论文可用的方法与局限性

方法。在固定 gold set、固定快照过滤下比较四条检索臂。BM25 臂是 BM25Okapi 加结巴分词。x1 的 dense 臂是本地 fastembed 0.7.1 的 BAAI/bge-small-zh-v1.5，512 维余弦。配置中的 DashScope text-embedding-v4（1024 维）未调用，因为 `embeddings.py` 只请求该付费接口。hybrid 臂用倒数秩融合（k=60）合并名次，不做分数加权。hybrid+rerank 调用 `rerank_lexical`，只对 hybrid 臂已经返回的前 10 条按结巴词重叠计数做 rerank，不加载 rerank 模型。主指标是作答臂（n=224）上的 Recall@10：前 10 条出现任一相关 chunk 记 1，再宏平均。排序指标是 MRR@10，以及二元相关的 nDCG@10（理想排序把 gold set 的相关 chunk 放在最前）。显著性是配对 bootstrap 10000 次、种子 20261007、配对差的 95% 百分位区间，以及 Recall@10 命中上的精确双侧 McNemar。延迟是单次计时的 p95，门槛 800 ms，不含模型加载和 query embedding 预计算。合成模板陷阱 47 题单列，不从总分母剔除。早期冒烟（n=36）与 Hard-Gold（n=20）的 dense 臂 embedding 是 text-embedding-v4，与 x1 的本地 embedding 分开报告。

局限性。gold set 由两个模型标注，审核由 Ronin 代理人（模型）受委托完成，`human_row_review=false`，不是人工逐行 gold set。原 211 题的证据完全一致只有 141/211。第四轮 54 道新题由同一模型会话先起草再作盲标，证据、类别与陷阱子类 54/54 一致，其中 48 道为同一模板；题型只对齐 44/54。这种一致不能当作独立标注可靠性。语料 794 个 chunk，合成占比 0.8299748110831234。hybrid 臂 Recall@10 为 0.9732。任一命中的 Recall@10 对「只处理已有前 10 条」的词重叠不敏感，Recall@10 持平是机制结果。实现只数词重叠，不加载 rerank 模型。陷阱按快照取代、同快照冲突和元陈述操作化，测的是时效与版本，不覆盖开放域里词面无关的相关性噪声。因此「大语料上 rerank 更有说服力」只登记为待复测假设，不能从本表外推。p95 是单次计时。生产入库与失效路径尚未同步写 embedding，缺一个 chunk 的 embedding 会使整次 hybrid 检索记为 `bm25_fallback`。因此本文不把生产默认写成已经切换。

## 12. 修订记录

本次只改 `docs/evidence/retrieval-decision.md`。对照仓内源文件后的更正：

1. 冒烟集的 dense embedding 补为 `text-embedding-v4`（`reports/retrieve-arm-compare.md`），不是 x1 后来用的 bge-small-zh-v1.5。语料补为 28 个文件、84 个 chunk；基线报告日期 2026-09-28，I0 验收复跑 2026-09-29。dense 的 Recall@10 维持 0.9722，明确不是三臂都满分。
2. Hard-Gold #259 的 dense 索引补为 `text-embedding-v4`、1024 维、94 个 chunk。与 x1 的 512 维本地 embedding 分开，避免两次 Recall@10 被读成同一模型。骨架验收日期由笼统的 2026-10-03 改为 2026-10-02（`docs/evidence/i3/ACCEPTANCE.md`），过线复跑仍是 2026-10-03。
3. 删去「约 629 MB」。源文件只有进程峰值 643680 KiB。
4. 写明 rerank 不加载模型，也不调用 `rank-bm25`。删去「将来换成神经 rerank 后 Recall@10 可能上升」。交叉编码器若仍只处理前 10 条，任一命中的 Recall@10 同样不变。不采用「rerank 模型太小」这一解释。
5. 补上 x1 未跑 `text-embedding-v4` 的原因：`embeddings.py` 只请求 DashScope，配置维度是 1024，#283 禁止付费接口。
6. 补上 #286 的三条缺口：入库与补丁/失效同步写 embedding、fastembed 入生产依赖、保留一键回到 BM25。该票不实施切换。
7. 补上清单建议计数：BM25 对 hybrid 172 / 48 / 4，BM25 对 rerank 172 / 48 / 4，hybrid 对 rerank 149 / 36 / 19 / 4。写明 16 道 Recall@10 分差不等于 48 道可议题。
8. 补全库题型 66 / 156 / 45，护栏 43 题均为 trap，全库 adversarial 为 0。fastembed 0.7.1 标明出自 #285 的 `summary.json`，#283 的 RESULT 只写库名。
9. #285 主表仍用四位小数。旁注原始值：Recall@10 0.9196428571428571 与 0.9732142857142857，McNemar p 为 0.004180908203124997。代价秒数同样旁注 `cost.json` 原值。
10. 中文按技术写作习惯重写。已核对数字的含义不改。
11. 关键专业名词改回英文原文，全文统一：BM25、dense、hybrid、rerank、Recall@10、MRR、nDCG@10、p95、embedding、bootstrap、McNemar、chunk、fallback（`bm25_fallback`）、gold set。去掉「词法 / 混合 / 稠密 / 重排」等译名。数字与其余表述不改。
