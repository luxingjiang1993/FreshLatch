# FreshLatch 离线产品质量闸 · PREREG

> 状态：QG-02 草稿。`owner_freeze: pending`。起草会话不得把该行写成 `confirmed`。
> 观察树：`b5fe41c10d711f0f4e7496465665dee793c1a7cf`（2026-10-13）。指纹按该树现算，未调用 LLM。
> 建议命令形状（只登记，仓库里还没有这个子命令）：
>
> `python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md`
>
> 盘点来源：QG-01。本页不实装 runner，不改产品代码。

人把第 7 节的 `owner_freeze: pending` 改成 `owner_freeze: confirmed` 之后，这一页才是锁定的产品质量闸。锁定前跑出的数字不是锁定闸的结果。

---

## 1. 层与非目标

这一页是离线产品质量闸的预注册。它登记身份、分母、指标归属和通过线的空位。它不声明 SESOI，不报统计显著，不报方差。

已有材料停留在冒烟或单次实验，不能升格成这一页的 SESOI：

| 材料 | 自标层 | 与本页的关系 |
|---|---|---|
| `data/eval/retrieve_gold.json` | `level=smoke`，n=36 | 不进本页分母 |
| `data/eval/retrieve_traps.json` | `level=smoke`，3 题 | 不进本页分母 |
| `data/eval/retrieve_hard_gold.json` | `level=hard_gold_skeleton`，n=20 | 不进本页分母 |
| `docs/evidence/x1-retrieval-modes/summary.json` | `level=实验/冒烟`；单次确定性运行 | 词面测量。第 2 节排除，不作为基线 |
| `docs/evidence/neural-rerank/summary.json` | 单次确定性对照 | 第 2 节的冻结基线文件。文件里的点估计是描述，不是通过线 |
| CI `ruff check` + `python -m pytest tests/ -q` | ADR-0005 代码不变量，零 LLM | 不变量闸。不是 R1 / G1 / A1 / T1 |

`.github/workflows/ci.yml` 写明：流水线绿 = 代码不变量没破；模型表现绿 = 金标 runner 报告，手动或 milestone，不走 CI。`pytest.ini` 没有 quality-gate marker。`python -m freshlatch.eval` 现有子命令是 `run` / `control` / `control-c` / `report` / `retrieve`。`retrieve` 是 BM25 冒烟入口。四闸还没有统一入口。

四闸在 QG-01 的状态，本页沿用：

| 闸 | 状态 | 本页处置 |
|---|---|---|
| R1 Retrieval | partial。`recall_at_k` / `mrr_at_k` 已有；题集与神经 K=10 描述数已有 | 定义登记。通过线 TBD |
| G1 Refuse/guards | partial。`must_stale` / `must_fresh` / `must_unknown` 在 CI；应拒金标缺失 | 机械闸留在 CI。should-refuse / should-pass 保持 `unregistered` |
| A1 Attribution | missing。无句级 citation 金标 | 保持 `unregistered`。不得记成通过 |
| T1 Temporal | partial。陷阱冒烟与 3 对 `conflict_pair` 已有；新压过旧无独立题集 | 排序定义可登记。new-over-old 保持 `unregistered`。通过线 TBD |

非目标：

- 不重开 PE-Y。`docs/evidence/patch-events/RESULT-Y.md` 分层为结果丙（T−C 点估计 `0.0927152317880795`，95% 下界 `-0.006493506493506496`，成立格不成立，n=400）。该 false-accept 是改写放行构念。它不是 A1，不能当作句级 false cite。
- 不含 live LLM。不含 UI。不含多 seed 的 S1，不含 Agent/Skill 行为闸。
- 不改 `PRODUCTION_RETRIEVAL_MODE`，不改 gold，不改题集。
- 本页不实装质量闸 runner。

`unregistered` 的段没有通过线。命令若把这种段打印成 pass，该次运行作废。QG-01 的退出约定一并冻结：任一已登记且已写死通过线的 P0 段失败，或任一仍为 `unregistered` 的段被当成通过，退出码非 0。A1 在 `data/eval/cite_sentence.json` 落地之前保持 `unregistered`，不能靠缺省跳过变成退出码 0。

---

## 2. 臂针与冻结基线

生产臂是 `hybrid+rerank`。针来自当前代码与依赖，不来自仍写「生产默认 BM25」的旧文档。

| 针 | 冻结值 | 出处 |
|---|---|---|
| 模式 | `PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"` | `src/freshlatch/store/base.py` |
| embedding | 本地 `BAAI/bge-small-zh-v1.5`，dim 512 | `LOCAL_EMBED_MODEL`，`LOCAL_EMBED_DIM` |
| 融合 | RRF，常数 k=60。融合的是名次倒数，rank 从 1 起 | `RRF_K`；`hybrid+rerank` 路径调用 `rrf_fuse(..., k=RRF_K)` |
| 精排 | `BAAI/bge-reranker-base`，fastembed `TextCrossEncoder`，CPU | `NEURAL_RERANK_MODEL` |
| 精排宽度 | 只重排 hybrid 的 top-10 | `NEURAL_RERANK_K = 10` |
| 库 | `fastembed==0.8.1` | `requirements.txt`、`pyproject.toml`；基线文件自报 `fastembed_version=0.8.1` |

`src/freshlatch/store/pipeline.py` 里「生产默认不走这条融合」是旧注释。冻结行以上表为准：`hybrid+rerank` 先做 RRF，再把前 10 条送进神经精排。

运维开关 `set_retrieval_switch("bm25")`、`set_retrieval_switch("hybrid+rerank_lexical")`，以及缺向量时的 `bm25_fallback`、精排失败时的 `last_rerank_mode=lexical_fallback`，都不改上面的常量。它们不是本页的臂针。

`data/exp/x1/config.json` 的 `embed_model=text-embedding-v4`（dim 1024）是 x1 实验配置。它与本地 `BAAI/bge-small-zh-v1.5`（dim 512）不是同一个 embedding。本页指纹该文件，是为了侦测字节变化，不是为了把 DashScope embedding 写成生产臂。

神经 rerank 旧预注册正文曾写 fastembed 0.7.1。基线文件自报 `0.8.1`，现行生产依赖也是 `0.8.1`。本页的库针是 `fastembed==0.8.1`。

### 冻结基线文件（只此一份）

`docs/evidence/neural-rerank/summary.json`

baseline_summary_sha256: 8fb4f1271b844c979b28bf351cf22ecbad354e3f5f35f7d2e1e7d760efb8e526

字节数 2451。引入提交 `bfd483875e27ee4fc7c5d608e85cb4549d4053c9`。产品读数只取该文件的 `k10` 右臂（神经精排）。`k30` 留在同一文件里，生产不把 30 条送进 cross-encoder，`k30` 不作为产品基线点。

`k10` 的描述数字（n=224，单次确定性运行，`human_row_review=false`）。这些是描述，不是通过线，也不是显著性结论：

| 字段 | 值 |
|---|---|
| Recall@10 左臂与右臂 | `0.9732142857142857`（两边相同） |
| MRR@10 右臂（神经） | `0.8381855867346939` |
| MRR@10 左臂（词面精排） | `0.7566609977324263` |
| 神经精排 p95 | `434.1544819999399` ms（描述；不是本页证物） |

### 排除的另一份摘要

`docs/evidence/x1-retrieval-modes/summary.json` 是另一次测量。它的 `production_retrieval_mode_before` 与 `production_retrieval_mode_after` 都是 `bm25`，自标 `实验/冒烟`。其中 `hybrid+rerank` 列的总体 MRR@10 等于上表左臂 `0.7566609977324263`，对得上词面精排，对不上神经右臂 `0.8381855867346939`。

excluded_lexical_summary_sha256: 82a14ae9934e59d37f70bb0577e12d45718decd102cd7d51f584896a9f819143

两份文件不得拼成一条基线。用词面摘要顶替神经摘要，本页作废。旧文档里「生产默认仍是 BM25」的句子不写入本页的冻结行。

---

## 3. 分母

题集路径收成一份：`data/exp/x1/questions.json`。

`data/eval/retrieve_x1.json` 不存在。CLI 或 RET-01.4 若仍指向该路径，本页不采用。

| 项 | 冻结值 |
|---|---|
| 题集 | `data/exp/x1/questions.json` |
| 题集最后变更提交 | `50adc3251737c318815105b3562a823198b80dc3`（与神经预注册当时点名的金标提交相同） |
| 原始字节 sha256 | `2cd7c5fb1e14859049c148e4dafc95b4d3c0abb4fa1080965dcc57b0d57c73fe` |
| n | 267 |
| `score_role=arm` | 224。Recall@10 / MRR@10 的分母只含这一层 |
| `score_role=guardrail` | 43。全部 `as_of=T1`。不进 Recall@10 / MRR@10 |
| k | 10 |
| 标注 | `meta.human_row_review=false`。`status=owner-delegated-model-reviewed`。人工审核只覆盖 DECISION-16 的 16 题，不是 224 题逐行人审 |

arm 内切片（描述分母，不是通过线）：`qtype` lexical 60、paraphrase 119、multi_hop 45；`category` hard 153、trap 71。

`conflict_pair` 3 对，都在 arm 内：`s6-d1-c1-q1`、`s6-d1-c2-q1`、`s6-d1-c3-q1`。键为 `in_force`、`superseded`、`precedence`。

命中定义沿用 `recall_at_k`：top-k 里出现 `relevant` 中任一 id 记 1，否则 0；`relevant` 为空记 0。对 arm 题做宏平均。比较是 `relevant` 字符串的精确匹配（本题集里的 id 带 `@T0` / `@T1`）。这是任一命中，不是集合召回率。

`mrr_at_k`：k 内第一个命中 id 的名次 i 记 `1/i`，否则 0。同样只对 arm 宏平均。

以下集合不并进这 224 的分母：`retrieve_gold.json`（n=36）、`retrieve_hard_gold.json`（n=20）、`retrieve_traps.json`（3 题）。

---

## 4. 指标归属

主指标只属于 R1 的 arm 分母：Recall@10、MRR@10。k=10。

`ndcg_at_k` 已实现，神经基线文件里也有 nDCG@10。本页不把它收成产品质量通过指标。它留在历史对照表里。

以下各项单独成列，不并进主 Recall@10：

| 列 | 定义 | 归属 | 通过线 |
|---|---|---|---|
| guardrail 0-hit | `guardrail_pass`：返回列表中不得出现 `as_of=T0` 的块。实现里 `query_as_of` 参数被丢弃，检查的是返回块 | G1 旁列。43 道护栏题 | TBD |
| conflict-pair ordering | `conflict_pair_correct`：`in_force` 的名次严格小于 `superseded`。被取代条未返回且现行条返回了，算正确。两者都没返回，或只有被取代条返回，算不正确。函数不读 `precedence` | R1/T1 旁列。n=3 | TBD |
| multi-hop 全命中 | `_full_hit`：k 内必须包含该题全部 `relevant` 才记 1 | R1 旁列。arm 内 multi_hop n=45。主 Recall 在这些题上仍是任一命中 | TBD |
| false cite / miss cite | 句级误引 / 漏引 | A1。金标未落地 | 无通过线。`unregistered`。不得记成通过 |

guardrail 0-hit 在 `as_of=T1` 过滤已经打开时接近恒真，因为池子里已经没有 T0 块。本页不把这条恒真写成通过。`--disable-as-of` 不是本页冻结的跑法。

`data/eval/gold.json` 的 `must_stale` / `must_fresh` / `must_unknown`（`c1`–`c12`）由 `tests/eval/test_gold_gate.py` 在 CI 里检查。那是机械闸不变量，不是 should-refuse 拒绝率，也不顶替 R1 的 224 题分母。

---

## 5. 标签 schema

### 已存在、本页采用的题集字段

`data/exp/x1/questions.json`：

- `meta`：`status`、`category_rule`（`category-rule-v2`）、`qtype_rule`（`qtype-kw-v1`）、`human_row_review`、`reviewer`
- 每题：`id`，`query`，`as_of`（`T0` 或 `T1`），`qtype`（`lexical` / `paraphrase` / `multi_hop`），`category`，`score_role`（`arm` / `guardrail`），`relevant`，`answer_points`，`distractors`，`eval_intent`
- 可选 `conflict_pair`：`in_force`，`superseded`，`precedence`

### 已存在、但不作为本页应拒 / 句级 / 新压过旧金标

- `data/eval/gold.json`：主张级 `must_stale` / `must_fresh` / `must_unknown` / `causal_chain`。服务 CI 机械闸。
- `data/eval/retrieve_traps.json`：冒烟三题。`trap-conflict-1` 把同快照冲突的两侧都放进 `relevant`，测不到「错条排前」。

### `unregistered`（文件不存在；本页不编行、不编通过线）

| 段 | 预留文件名 | 状态 |
|---|---|---|
| should-refuse / should-pass | `data/eval/guard_should.json` | `unregistered` |
| 句级 citation（false cite / miss cite） | `data/eval/cite_sentence.json` | `unregistered`。A1 一直保持到该文件作为金标落地 |
| new-over-old | `data/eval/temporal_new_over_old.json` | `unregistered` |

段状态词只有两个：已有金标且通过线已写死，或 `unregistered`。通过线为 TBD 的列有定义、无通过线，不得打印成 pass。

---

## 6. 各闸 SESOI / 通过线

本页不发明显著性，不把单次描述数字写成产品通过线。证据薄的格子写 TBD。

| 段 | 本页锁定的内容 | 产品通过线 |
|---|---|---|
| R1 Recall@10 | 第 3 节定义。神经 `k10` 两边同为 `0.9732142857142857`（描述，n=224，非逐行人审） | TBD |
| R1 MRR@10 | 第 3 节定义。神经右臂 `0.8381855867346939`（描述） | TBD。相对词面左臂的差 `0.08152458900226757` 是该实验的配对对照，不是产品下限 |
| guardrail 0-hit | 第 4 节定义。n=43 | TBD |
| conflict-pair ordering | 第 4 节定义。n=3，未进 CI | TBD |
| multi-hop 全命中 | 第 4 节定义。n=45 | TBD |
| G1 should-refuse / should-pass | `unregistered` | 无。不得记成通过 |
| A1 false cite / miss cite | `unregistered` | 无。不得记成通过 |
| T1 new-over-old | `unregistered`。`run_trap_eval` 在旧块排到新块前面时不失败 | 无。不得记成通过 |

`tasks/RET-01.4.md` 与 `data/exp/x1/config.json` 里的 `lead_delta=0.10`（hybrid − BM25 的分型 R@10）是 **draft-experiment-only**。该票正文仍要求把生产臂写成 bm25。这个 0.10 不是产品质量通过线。

神经旧预注册的四条取舍（nDCG 下界、nDCG 点估计、MRR 下界、p95 ≤ 800 ms）是「建议另开切换票」的实验规则。基线文件的 `recommendation` 字段保留该历史措辞。那四条不是本页的产品通过线。800 ms 不是 R1 / G1 / A1 / T1 的默认证物。以后若单列 p95，另写容差，不回改本页。

DECISION-16 与 2026-10-07 的换臂是人的产品决定。它不充当本页的 Recall 或 MRR 通过线。

---

## 7. 指纹、模型与 owner_freeze

指纹算法是 `freshlatch.eval.retrieve_typed.compute_x1_fingerprints`：语料为 `data/exp/x1/corpus` 与 `data/exp/x1/traps` 下全部 `.md`，聚合根目录 `data/exp/x1`；题集聚合根目录是 `questions.json` 的父目录；`config_sha256` 是 `data/exp/x1/config.json` 的原始字节 sha256。题集指纹不是第 3 节的原始文件 sha256。原始文件 sha256 是 `2cd7c5fb1e14859049c148e4dafc95b4d3c0abb4fa1080965dcc57b0d57c73fe`；下面的 `questions_aggregate_sha256` 是聚合行的哈希。

下面四行各出现一次。前三行是 `PREREG_FP_KEYS`。解析器不读 `owner_freeze`。

corpus_aggregate_sha256: 569597e1441363799f8da487cdd9102a9a769de07baaf6cebc4033466ab1adfd
questions_aggregate_sha256: 4221c5e0ad9983b112e432496fe78fe5125d9781d63973451a650d326b5cd952
config_sha256: 54736467729ccdc14aa1c9704908bf6f9dbc9292005488a92ae73edb23cfa2d6
owner_freeze: pending

模型针（与第 2 节同一组）：

- embedding：`BAAI/bge-small-zh-v1.5`，dim 512，本地 fastembed
- 精排：`BAAI/bge-reranker-base`，`NEURAL_RERANK_K=10`
- 融合：RRF k=60
- 库：`fastembed==0.8.1`
- 模式：`hybrid+rerank`

`config.json` 里的 `draft_model=qwen-flash`、`flag_model=qwen-plus` 是出题草稿模型。离线闸不调用它们。

`owner_freeze: pending` 由人改成 `owner_freeze: confirmed`。在那之前，本页是草稿。

---

## 8. 作废条件

出现下列任一情况，本页作废；已经据此声称的通过一并作废：

- 改金标、改题集路径、改第 7 节三行指纹所覆盖的字节、改 k、改第 2 节模型针或 `fastembed==0.8.1`、改 RRF k、改精排宽度。
- 跑数之后再改通过线、改分母、改命中定义、改段的 `unregistered` 状态。这是事后改判据。
- 用 `docs/evidence/x1-retrieval-modes/summary.json` 顶替第 2 节的神经基线，或把两份摘要合成一条基线。
- 把 A1、should-refuse / should-pass、new-over-old 在金标落地前记成通过。
- 重开 PE-Y，或把 RESULT-Y 的 false-accept 当作 A1。
- 把 **draft-experiment-only** 的 `lead_delta=0.10` 写成产品通过线。
- 把 800 ms 写成这四闸的默认证物。
- 把旧文档中的「生产默认 BM25」写回第 2 节的冻结行。
- `owner_freeze` 仍为 `pending` 时，把该次运行称为锁定产品质量闸。

排序指标在确定性层要求逐位一致：同一臂、同一金标、同一 k 下，题级名次与命中 0/1 逐题相同。本页不给排序指标留随机容差。p95 若以后纳入，不走这条逐位规则，须另页写容差。QG-04 之前还不存在新的对照运行；这条规则先写死，避免跑完再补。

---

## 9. 离线排除清单

文档中的命令形状不得做下列事情：

- 调用 `python -m freshlatch.eval run`、`control`、`control-c`。
- 读取 `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY`、`MOONSHOT_API_KEY`。
- 按 `data/exp/x1/config.json` 正式跑 `scripts/run_retrieve_x1.py`（`text-embedding-v4`，以及草稿模型 `qwen-flash` / `qwen-plus`）。
- 发送 PE-Y 的 judge、generate 或 formal。
- 跑需要 `FRESHLATCH_I2_LIVE=1` 与 `DASHSCOPE_API_KEY` 的 `test_inj_t001_live_llm_lead_auditor_finalize_smoke`。
- 打开 UI，或把 CI `pytest tests/` 的绿当成 R1 / G1 / A1 / T1 的通过。

---

## 冻结之后的下一步

本页停下。下一步不是在这一页里补跑。

- QG-03：实装入口命令与夹具，命令形状即本页文首那一行，`--prereg` 指向本文件。夹具须让 `unregistered` 段不能被记成通过，且不得调用第 9 节列出的 live 路径。QG-03 不编写 `cite_sentence` / `guard_should` / `temporal_new_over_old` 的金标行，除非另有人开的金标票。
- QG-04：对第 2 节那一份神经基线做 1 次离线运行。1 次是冒烟核对，不报方差，不补 SESOI。跑完若要改本页任一冻结字段，本页作废，另开预注册。
