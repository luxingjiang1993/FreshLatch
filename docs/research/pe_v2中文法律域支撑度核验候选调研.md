# pe_v2 中文法律域支撑度核验候选调研

> **工单**:[#521](https://github.com/luxingjiang1993/FreshLatch/issues/521)（父图 [#517](https://github.com/luxingjiang1993/FreshLatch/issues/517)）  
> **层级**:仓外可操作性事实纪要（仪器 grilling 原料）。**不是**核验器选型决议；不改 `PREREG.md`；不改业务代码。  
> **方法**:主张跟到一手来源（HuggingFace model card、论文 PDF/官方页、GitHub README/许可）。二手综述不充当真相。  
> **整合参照**:`docs/research/冲甲冲乙行动方案整合.md` §2.2（冲乙仪器：支撑度核验 + 中文法律域小标定）。

---

## 1. 问题与 pe_v2 设定

**问题**:现行 `verify_edit` 把「一致」操作化为 `after_text.strip() == evidence_text`，`score` 恒空（见 `src/freshlatch/eval/patch_events_verify.py`；补定见 `docs/evidence/patch-events/PROMPT-AND-VERIFY-GAPS.md`）。冲乙仪器要非空支撑置信，需要**替代逐字一致**的「改写是否被所绑证据支撑」核验器。本纪要只回答：各候选在 pe_v2 设定下的**仓外可操作性**。

**pe_v2 设定（仓内已钉死，本票不改）**:

| 项 | 取值 | 来源 |
|---|---|---|
| 语料 | 公开中文法律/法规/司法解释文本；主张逐字可定位 | `DECISION-LOG.md`「扩充公开语料」；`data/corpus/pe_v2/PROVENANCE.json` |
| 来源快照 | 国家法律法规数据库现行有效文本汇编（`senry5433/china-effective-laws-regulations`，CC0-1.0）；官网入口 `https://flk.npc.gov.cn/` | 同上 |
| premise | **绑定 chunk**（`evidence_text` / 已入库 T1 chunk） | `PREREG.md` attested edit；整合方案 §2.2 |
| hypothesis | **`after_text`**（改写句） | `PROMPT-AND-VERIFY-GAPS.md`；`verify_edit` 入参 |
| 任务形 | 单 chunk 对单句：证据能否支撑这次修改（支撑 / 不支撑；最好带可排序 `score`） | 整合方案 §2.2；评委问题 B 措辞在 `PREREG.md` |

**本票 Out**:不拍板采用哪条；不写预注册；不改代码；不得把下列仓外基准的跑分装成本仓「已过线」。

---

## 2. 逐候选可操作性

### 2.1 mDeBERTa-v3 XNLI（多语 NLI）

| 维 | 事实 |
|---|---|
| **许可** | HuggingFace card 元数据 `license: mit`（模型卡 YAML）。底层 mDeBERTa-v3-base 为 Microsoft 预训练权重，部署时仍须核 Microsoft/DeBERTa 原仓库条款；本卡声明的微调权重为 MIT。 |
| **中文能力证据** | 训练语言列表含 `zh`；在 **XNLI 中文测试集**上自报 Accuracy **0.803**（15 语表中的 `zh` 列）。训练数据含 machine-translated multilingual-NLI-26lang-2mil7（含 zh）+ XNLI validation；作者明确警告：MT 数据降低 NLI 质量。 |
| **本地 / API** | **本地**:`transformers` 加载 `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`；三分类 `entailment/neutral/contradiction` + softmax 可作 `score`。无官方托管推理 API 要求。A100 上自报 ~1887 text/sec（zh）。注意：mDeBERTa 当前不支持 FP16（卡内 Debugging 节链到 Microsoft/DeBERTa#77）。 |
| **标定成本** | 零样本可直接跑 premise=chunk、hypothesis=`after_text`。法律域小标定：需自建「正确改 / 坏改」金标对（可复用 pe_v2 构造算子），量级由 grilling 另定；模型本身不附中文法律标定集。 |
| **已知陷阱** | (1) 通用 NLI ≠ 法条支撑：条款号、但书、废止日期等法律陷阱无专项训练。(2) zh 训练对大量来自 MT，卡内 Limitations 写明质量下降。(3) 长 chunk 截断：标准序列分类会 truncation。(4) `entailment` 阈值如何映射 `ok`/`score` 未由本卡规定——属预注册事项，本票不钉。 |
| **一手链接** | [HF model card](https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7) · [README blob](https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7/blob/main/README.md) |

### 2.2 MiniCheck

| 维 | 事实 |
|---|---|
| **许可** | GitHub 仓库 SPDX **Apache-2.0**。[`lytang/MiniCheck-Flan-T5-Large`](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large) card：`license: mit`，`language: [en]`。`Bespoke-MiniCheck-7B` README 写明商业使用须联系 `company@bespokelabs.ai`（与开源小模型许可分流）。 |
| **中文能力证据** | 官方 model card / README **只标 English**；训练为 ANLI + 英文合成 C2D/D2C；评测基准 LLM-AggreFact 域为 news/dialogue/science/healthcare 等，**一手材料未给出中文法律或中文通用评分数**。 |
| **本地 / API** | **本地为主**:`pip install "minicheck @ git+..."`；`MiniCheck(document, claim) → {0,1}` + `raw_prob`。另有 Ollama / Guardrails / playground 演示路径（README Updates）。多句 claim 须先拆句（README IMPORTANT）。 |
| **标定成本** | 开箱即用（英文 grounding）；中文法律域仍需小标定 / 敏感性闸。合成数据生成代码与 14K 训练数据已开源（HF `lytang/C2D-and-D2C-MiniCheck`），但语种为英文管线。 |
| **已知陷阱** | (1) **与 pe_v2 形最近的英文句级核验器之一**（doc=chunk，claim=`after_text`），但中文未验证。(2) 句子切分对中文标点须另定义。(3) 7B 商业许可与 <1B 开源模型分流。(4) 作者强调评测用「真实 claim」、不主张注入错误类型的编辑集代表真实行为——与 pe_v2 **故意构造坏改算子**的敏感性闸目标不完全同构。 |
| **一手链接** | [GitHub README](https://github.com/Liyan06/MiniCheck) · [arXiv 2404.10774](https://arxiv.org/abs/2404.10774) · [ACL Anthology PDF](https://aclanthology.org/2024.emnlp-main.499.pdf) · [Flan-T5 card](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large) |

### 2.3 AttrScore

| 维 | 事实 |
|---|---|
| **许可** | GitHub SPDX **MIT**。微调权重如 `osunlp/attrscore-flan-t5-large` card 标 **Apache-2.0**、语言标签 **en**。数据集声明「research purpose use only」（README Acknowledgement）。 |
| **中文能力证据** | 评测集 AttrEval-GenSearch 来自 New Bing、覆盖 12 英文域；训练为英文相关任务改写。**一手材料无中文法律数字。** |
| **本地 / API** | **本地微调权重**(Flan-T5 770M–11B、LLaMA/Alpaca/Vicuna 等 HF 检查点)或 **prompt ChatGPT/GPT-4**（需 OpenAI key）。输出三分类：Attributable / Extrapolatory / Contradictory。 |
| **标定成本** | 英文可零样本 / 用现成检查点；中文法律需重标或翻译迁移。人工标注成本论文引用量级约 **$1 / (query, answer, reference)**（相关工作 Liu et al. 2023，AttrScore 论文讨论段）。 |
| **已知陷阱** | (1) **任务形与「证据是否支撑 claim」最近**（相对 FActScore / ALCE 全 benchmark）。(2) pe_v2 无「Query」时需把 Claim 定义为纯 `after_text`（论文允许 plain sentence）。(3) GenSearch 上 GPT-4 评测存在「同模型生成又评测」偏差，作者自写 caution against over-optimism。(4) Simulation 集错误模式过简，迁移到法律坏改算子可能假信心。 |
| **一手链接** | [GitHub README](https://github.com/OSU-NLP-Group/AttrScore) · [arXiv 2305.06311](https://arxiv.org/abs/2305.06311) · [Findings EMNLP PDF](https://aclanthology.org/2023.findings-emnlp.307.pdf) · [HF dataset](https://huggingface.co/datasets/osunlp/AttrScore) |

### 2.4 ALCE（含 AutoAIS 引用支撑度量）

| 维 | 事实 |
|---|---|
| **许可** | GitHub SPDX **MIT**。 |
| **中文能力证据** | 基准语料为英文 ASQA / QAMPARI / ELI5 + Wikipedia 检索；**一手 README/论文未提供中文法律支撑数字。** |
| **本地 / API** | 本地跑 `eval.py`；引用质量走 **AutoAIS**，底层 NLI 为 `google/t5_xxl_true_nli_mixture`（大模型，需 GPU）。生成侧基线常依赖 OpenAI。 |
| **标定成本** | 作为「整套 citation QA 基准」接入 pe_v2 成本高；若只借 AutoAIS「cited docs 是否支撑句子」子程序，仍须换中文 NLI 或接受英文 T5-XXL 在中文上的未知行为。 |
| **已知陷阱** | (1) 测的是 **带 citation 的长答** 是否被所引文档支撑，不是单 chunk 绑定的文档改写闸。(2) AutoAIS 依赖 TRUE 系英文 NLI。(3) 与 pe_v2「改不改」主指标不同构——最多借子度量思想。 |
| **一手链接** | [GitHub](https://github.com/princeton-nlp/ALCE) · [EMNLP 2023 PDF](https://aclanthology.org/2023.emnlp-main.398.pdf) · [arXiv 2305.14627](https://arxiv.org/abs/2305.14627) |

### 2.5 SummaC

| 维 | 事实 |
|---|---|
| **许可** | GitHub SPDX **Apache-2.0**；`pip install summac`。 |
| **中文能力证据** | Benchmark 六集均为英文摘要一致性（CNN/DM、XSum 等）。底层 NLI（如 ViTC）面向英文。**一手材料无中文法律数字。** |
| **本地 / API** | **本地**:`SummaCZS` / `SummaCConv`；`score([document],[summary])`。CPU 可跑，GPU 可选。 |
| **标定成本** | 英文摘要一致性开箱；映射到 pe_v2 时 document=chunk、summary=`after_text` 需自标定阈值。 |
| **已知陷阱** | (1) 设计目标是 **摘要相对原文不一致检测**，不是法条改写支撑。(2) 句对聚合假设英文分句。(3) 与「坏改算子敏感性」需另闸，不能把 SummaC benchmark 分数当 pe_v2 过线。 |
| **一手链接** | [GitHub](https://github.com/tingofurro/summac) · [arXiv 2111.09525](https://arxiv.org/abs/2111.09525) · [TACL / Anthology](https://aclanthology.org/2022.tacl-1.10/) |

### 2.6 TRUE（及衍生 NLI 权重）

| 维 | 事实 |
|---|---|
| **许可** | 仓库 SPDX **Apache-2.0**。HF 权重 [`google/t5_xxl_true_nli_mixture`](https://huggingface.co/google/t5_xxl_true_nli_mixture)：`license: apache-2.0`，`language: [en]`。 |
| **中文能力证据** | TRUE 论文/仓库是 **事实一致性度量的元评测**（11 个英文数据集标准化为 grounding vs generated_text）。开源 NLI 权重训练于 SNLI/MNLI/FEVER/SciTail/PAWS/VitaminC 等，**语言标签仅 en**。 |
| **本地 / API** | (a) 元评测脚本：本地 CSV → ROC AUC 等；(b) NLI 权重：本地 T5-XXL，输入格式 `"premise: … hypothesis: …"`，二分类 entailment。无中文官方 API。 |
| **标定成本** | 作为「怎么评核验器」的工具可复用其元评测思路；作为 pe_v2 直接核验器则等同跑一个英文巨型 NLI，法律中文标定仍要自做。 |
| **已知陷阱** | (1) **TRUE ≠ 现成中文支撑度分数**——多数引用「TRUE」时实际指其 NLI 权重或元评测框架。(2) T5-XXL 资源重。(3) ALCE AutoAIS 依赖此权重，陷阱同 §2.4。 |
| **一手链接** | [GitHub README](https://github.com/google-research/true) · [NAACL 2022](https://aclanthology.org/2022.naacl-main.287/) · [HF NLI card](https://huggingface.co/google/t5_xxl_true_nli_mixture) |

### 2.7 FActScore 族中与「编辑是否被证据支撑」最近者

| 维 | 事实 |
|---|---|
| **许可** | GitHub SPDX **MIT**；`pip install factscore`。 |
| **中文能力证据** | 默认知识源为 **英文 Wikipedia 2023/04/01**；人物传记长文设定。支持自定义 knowledge source 预处理，但 **一手材料默认管线与演示均为英文**。 |
| **本地 / API** | 原子事实分解与判定默认走 **OpenAI API**（README：约 **$1 / 100 sentences** 量级）；可选 LLaMA 等估计器。自定义知识源需本地建 retrieval DB。 |
| **标定成本** | 高：要为 pe_v2 chunk 建自定义知识源，并承担 API / 分解误差。人评成本论文称自动化估计误差 <2%（相对其人评），但是在传记 Wikipedia 设定下。 |
| **与 pe_v2 的距离（最近者界定）** | **构念较远**：FActScore = 长文拆成原子事实后，相对**外部知识源**的支持率。pe_v2 要的是**已绑定单一 chunk** 对整句 `after_text` 的支撑闸。若强行套用，最近操作是：把 bound chunk 当作唯一 knowledge source、跳过开放检索——但仍引入原子分解噪声，且与「一次改写一句」不对齐。族内更近的是 **「原子事实 vs 给定段落」的布尔支持标签**这一子步骤，而非完整 FActScore 产品分数。 |
| **已知陷阱** | (1) 勿把 Wikipedia 传记 FActScore 数字写进 pe_v2 过线。(2) API 费用与非确定性。(3) 法律但书/序号在原子分解中易碎。 |
| **一手链接** | [GitHub](https://github.com/shmsw25/FActScore) · [EMNLP 2023](https://aclanthology.org/2023.emnlp-main.741/) · [arXiv 2305.14251](https://arxiv.org/abs/2305.14251) |

### 2.8 verified-chinese-law-kb

| 维 | 事实 |
|---|---|
| **许可** | **代码 MIT**；**数据 CC BY-SA 4.0**（`LICENSE` + `LICENSE-DATA`）。使用数据须署名 + 相同方式共享；README 要求关键事项仍核对官方原文。 |
| **中文能力证据** | 本体即中文：8 部已发布法律、**2,327** 条律师逐字核验条文；来源 `flk.npc.gov.cn`；字段含 `effective_date` / `revision_of` / `verification_status`。 |
| **本地 / API** | **纯本地** JSONL / 模块下载 CLI；无推理 API。是 **真值库**，不是 NLI 核验器。 |
| **能提供的标定协议（不能装已过线）** | (1) 版本轴 + 失效法清单（`deprecated_laws.json`）→ 构造「旧法当新法」坏改。(2) 逐字核验标准（`docs/VERIFICATION_STANDARD.md`）→ 金标抽取纪律。(3) 与 pe_v2 同源官网，可交叉核对条文，但 **不得**把该 KB 的存在或下游 bench 分数写成 FreshLatch 核验器已过线。 |
| **已知陷阱** | (1) CC BY-SA 传染：派生标注集可能需同等共享。(2) 覆盖 8 部法，不等于 pe_v2 全部主张法域。(3) M3 起省略 `verified_by` 具名签署字段（署名约定变更）。 |
| **一手链接** | [GitHub README](https://github.com/vickywu97/verified-chinese-law-kb) · [LICENSE-DATA](https://raw.githubusercontent.com/vickywu97/verified-chinese-law-kb/master/LICENSE-DATA) |

### 2.9 legal-hallucination-bench

| 维 | 事实 |
|---|---|
| **许可** | GitHub SPDX **MIT**（徽章与 `LICENSE`）。 |
| **中文能力证据** | 中文法律引注幻觉基准；KB 与 verified-chinese-law-kb 同源量级（2327 节点）；5 国产模型 × **29** 陷阱题真实跑分（README 报告 HVI 约 33.3%–54.2%；增值税法域逐字 EXACT 0%）。 |
| **本地 / API** | **离线零依赖**：`python -S`；不内置 LLM 调用。输入 `answers.jsonl` 离线评分。 |
| **能提供的标定协议（不能装已过线）** | (1) **二元硬门禁**：归一化逐字一致才 1.0，否则 0——与现行 pe_v2 `verify_edit` 同族，**不能**单独充当「支撑度软分」解决方案，但可作敏感性/回归金标。(2) **废止法陷阱**（`DEPRECATED_LAW_NAMES`）→ 坏改算子模板。(3) **专家标注闭环**：`annotate` → 人工隔离引文 → `run`（demo 显示启发式窗口会制造假阳性）。(4) 答案级维度（编造判例 / 循环引注 / 自相矛盾）供扩展陷阱，不污染条文级 HVI。 |
| **已知陷阱** | (1) 测的是 **引注忠实度**，不是「改写句相对绑定 chunk 的语义支撑」。(2) 29 题陷阱集 ≠ pe_v2 配额结构。(3) README 免：不构成法律意见；自动化结论可能偏差。 |
| **一手链接** | [GitHub README](https://github.com/vickywu97/legal-hallucination-bench) |

---

## 3. 对照总表（可操作性一览）

| 候选 | 许可（代码/权重要点） | 中文一手证据 | 部署 | 与「chunk ⊨ after_text」距离 | 标定提示 |
|---|---|---|---|---|---|
| mDeBERTa-v3 XNLI | MIT（微调卡） | XNLI-zh Acc 0.803 | 本地小模型 | 近（标准 NLI） | 法律小标定 + 阈值 |
| MiniCheck | Apache-2.0 仓；小模型 MIT；7B 商业另议 | 仅 en | 本地（+可选托管 demo） | 近（doc-claim） | 中文未验证 |
| AttrScore | MIT 仓；权重多 Apache-2.0 | 仅 en | 本地或 OpenAI | **最近（归因三分类）** | 中文重标贵 |
| ALCE AutoAIS | MIT | 仅 en | 本地 T5-XXL | 远（citation QA） | 借子程序代价高 |
| SummaC | Apache-2.0 | 仅 en | 本地 pip | 中（摘要一致性） | 阈值自定 |
| TRUE | Apache-2.0；NLI 权重 en | 元评测 / 英文 NLI | 本地 XXL | 中（二分类 entail） | 勿等同中文过线 |
| FActScore | MIT | 默认 enwiki | API 重 | **远**（长文×知识源） | 自定义 KS 仍不对齐 |
| verified-chinese-law-kb | 代码 MIT / 数据 CC BY-SA | 原生中文法律 | 本地数据 | 非打分器 | 版本/废止协议 |
| legal-hallucination-bench | MIT | 原生中文 + 国产跑分 | 离线标准库 | 非软支撑分 | 陷阱 + 逐字金标 |

---

## 4. 供仪器 grilling 可引用事实句

> **以下为仓外事实句，供冲乙仪器 grilling 引用。非决议；不构成核验器选型或预注册修改。**

1. HuggingFace 卡 `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` 声明 `license: mit`、训练语言含 `zh`，并在 XNLI 测试集上自报中文 Accuracy **0.803**；同一卡警告 multilingual-NLI 训练数据为机器翻译、会降低 NLI 质量。  
2. MiniCheck 官方权重卡（如 `lytang/MiniCheck-Flan-T5-Large`）语言标签为 **`en` only**；接口形为 `MiniCheck(document, claim)→{0,1}` 且附 `raw_prob`，与「chunk / after_text」同形，但一手材料未给出中文法律评分数。  
3. AttrScore 论文将归因评测定义为对 (claim, reference) 输出 Attributable / Extrapolatory / Contradictory；GitHub 许可 MIT，公开检查点语言标签为英文——任务形接近「证据是否支撑改写」，但中文法律域无一手现成数字。  
4. ALCE 的引用支撑自动指标 AutoAIS 依赖 `google/t5_xxl_true_nli_mixture`（HF 卡：`language: en`，Apache-2.0）；ALCE 基准本身是英文 citation QA，不是中文法律 chunk 改写闸。  
5. SummaC（`tingofurro/summac`，Apache-2.0，`pip install summac`）与 TRUE 仓库（`google-research/true`，Apache-2.0）一手材料均为**英文**事实一致性 / 元评测设定；TRUE 开源 NLI 权重同样标 `en`。  
6. FActScore（`shmsw25/FActScore`，MIT）默认知识源为英文 Wikipedia，并按原子事实比例计分；与 pe_v2「单绑定 chunk 支撑单句 after_text」构念距离大于 MiniCheck/AttrScore/多语 NLI。  
7. `verified-chinese-law-kb`：代码 MIT、数据 **CC BY-SA 4.0**，提供 8 部法共 2,327 条律师核验条文与版本轴；可作中文法律金标/废止陷阱原料，**本身不是**支撑度打分器。  
8. `legal-hallucination-bench`（MIT，离线 `python -S`）用二元逐字门禁 + 废止法陷阱评引注幻觉（README：5 模型×29 题，HVI 约 33.3%–54.2%）；其协议可借来做敏感性金标，**不得**装成 pe_v2 软支撑核验已过线，也与「语义支撑分」不是同一构念。

---

## 5. 检索日志（一手）

| 对象 | 取用 |
|---|---|
| mDeBERTa | HF model card + README YAML（2026-10-10 抓取） |
| MiniCheck | GitHub README；HF Flan-T5 card；arXiv/ACL PDF |
| AttrScore | GitHub README；arXiv/Findings PDF；HF dataset/model tags |
| ALCE | GitHub README；EMNLP PDF |
| SummaC | GitHub README + SPDX |
| TRUE | GitHub README；HF `t5_xxl_true_nli_mixture` card；NAACL 页 |
| FActScore | GitHub README；EMNLP/arXiv |
| verified-chinese-law-kb / legal-hallucination-bench | `master` 分支 README、LICENSE、LICENSE-DATA |
| pe_v2 设定 | 仓内 `DECISION-LOG.md`、`PROMPT-AND-VERIFY-GAPS.md`、`patch_events_verify.py`；整合方案 PR #516 文档 |
