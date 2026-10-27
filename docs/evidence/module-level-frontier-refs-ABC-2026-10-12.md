# FreshLatch A/B/C 缺口 · 前沿参考短名单（2026-10-12）

> 受众：后续开票 / 只摘 fields/modes。不换向量库、不装 REA、不把 LangGraph 引进 `run_loop`。
> 对齐：[`module-level-gap-checklist-2026-10-12.md`](module-level-gap-checklist-2026-10-12.md) 的 ID；水平评估见 [`module-level-assessment-2026-10-12.md`](module-level-assessment-2026-10-12.md)。
> 调研日：2026-10-12（Asia/Shanghai）。GitHub 存在性以 `gh api repos/...` 抽查为准；星标与 `pushed_at` 为当日快照，会变。
> 原则：只偷 pattern；禁止编造 repo；日期未知标「日期未核实」；未开票、未改生产代码。
> A 层：组会两源整合短名单（附件 `freshlatch-module-frontier-refs-MERGED`）已覆盖；本页给 **按 ID 索引 + 少量补漏**。B/C 层为本轮主查。
> **开票前歧义**（L0 词冲突、A/B 边界、B-01 两种读法、A 附件不在仓、A-EV-01 误勾等）以缺口清单「开票前已知歧义与边界」为准：[`module-level-gap-checklist-2026-10-12.md`](module-level-gap-checklist-2026-10-12.md)。

## Meta · 核验备注

- 已用 `gh api` 抽查存在：`jkelly-dev1/citation-abstention-rag`、`Zhonghui-li/sec-filing-agent`、`aman9824/finance-filings-analyst`、`Nakshathra-2808/FinTrustRAG`、`pagand/VeNRA`、`hljoren/sufficientcontext`、`HuskyInSalt/CRAG`、`jaineet17/causal-agent-replay`、`seungyoonee/TSM`、`siyue-zhang/MRAG`、`Betswish/MIRAGE`、`anthonywchen/RARR`、`alexmartin1722/kpr`、`AmarReddy4/multitenant-rag-rbac`、`jay-tank/ragmoat`、`patibandlavenkatamanideep/trust-rag-finance`、`tkarim45/sec-rag-analyst`、`neeraj1909/xai-rag`、`amazon-science/RAGChecker`、`AI4Finance-Foundation/FinRobot`、`declare-lab/trust-align`、`AsaifAli/LangGraph-RAG`、`gaurika05/verified-scholar-agent`。
- TempRetriever（arXiv:2502.21024）正文写「code will be available after acceptance」——**截至调研日未找到官方公开训练仓**；可摘论文模式，勿假装有可 clone 训练代码。
- X（Twitter）共识帖多为观点、难复现；本页不以单条帖子作工程依据。hybrid→rerank 思想已在仓内生产臂与既有短名单中。
- 产品参考（Perplexity Finance 等）无开源实现；只摘交互模式。

---

## A. If-landed（L3→L4）· 按 ID 索引

完整实践表与论文表见两源整合版（上传附件 / 组会短名单）。下表只写「摘到哪、FreshLatch 挂点」。

| ID | 首选可摘源 | 可摘 pattern | FreshLatch 挂点 |
|---|---|---|---|
| A-FC-01 | OpenAI function calling + structured outputs；LangChain tool-args validation middleware；Wavise reliable tool calling | schema 再验 → typed error → 有限自纠 → 耗尽 fail-closed | `tools.py` / `run_loop`；统一 `UnknownToolGuard` 与参数错误形态 |
| A-FC-02 | OpenAI `strict: true` + `additionalProperties:false` | 采样边界拒非法 args（仍需业务语义 gate） | `LLMClient.chat` 传 tools 时；端点若不支持则文档声明「仅运行时再验」 |
| A-FC-03 | OpenAI Agents SDK `needsApproval`；OpenHands ConfirmRisky | 工具权限分层：读 / 需批 / 禁（开票勿裸写 L0，避与 HumanLatch L0 冲突） | 映射检索只读 vs 写观测 vs 禁动生产臂；各≥1 测；词表见缺口清单歧义 §1 |
| A-SK-01 | Cursor Hooks（exit 2 + `failClosed:true`）；cookbook hooks | 可执行 deny，非 prompt 劝告 | `docs/agents/agent-guards.md` 旁样板；不进 `run_loop` 替代白名单 |
| A-SK-02 | agentskills.io Spec；`anthropics/skills`；FinRobot skills/ | `SKILL.md` + progressive disclosure；金融 playbook 形状 | `skills/` 增 3–5 中文业务包 |
| A-SK-03 | Spec references/scripts；仓内 `test_skills.py` 已锁工具名⊆白名单 | 真工具读 references，或改掉假承诺 | 新工具或修正 `skills/reverify/SKILL.md` frontmatter |
| A-RAG-01 | Sufficient Context（ICLR 2025 · `hljoren/sufficientcontext`） | sufficient 标签 → selective abstain | retrieve 边；不足不硬答 |
| A-RAG-02 | CRAG（`HuskyInSalt/CRAG` · arXiv:2401.15884） | Correct / Incorrect / Ambiguous → refine \| abstain | **挂 retrieve**（组会 C5 裁决）；Agent 只消费 grade |
| A-RAG-03 | MRAG（`siyue-zhang/MRAG` · arXiv:2412.15540）；来源 A temporal 短名单 | 无训练：语义分 × 时间分；`patch_id` / 有效期元数据先于 RRF | `Chunk` 增列 + SQL/融合前 filter；不换库 |
| A-RAG-04 | `tkarim45/sec-rag-analyst`；`neeraj1909/xai-rag` | 每 hit BM25/dense/RRF/rerank 分；rerank ON/OFF ablation | 轨迹 + 工具观察字段；manifest |
| A-AG-01 | Self-RAG / verified-scholar / LangGraph-RAG 短环 | `retrieve→generate→verify→(repair\|abstain)` | 现有 `run_loop` 加节点；state：`evidence_ids`/`grade`/`retry_count` |
| A-AG-02 | `jkelly-dev1/citation-abstention-rag` reason codes | 命名拒答码进轨迹 | 与 UI Unknown 态共用词表 |
| A-AG-03 | LangGraph checkpointer / time-travel（人审已用）；CAR 仅排障 | 失败轨迹可复放 | **不**把 LangGraph 引进 Agent 循环；扩展轨迹 JSONL + 既有 latch checkpoint |
| A-UI-01 | sec-rag-analyst Streamlit；citation-abstention UX；trust-rag-finance HITL | Query→Hits→Attribution→Unknown\|Override | 薄扩 `ui/static/reverify.html` 审计面 |
| A-UI-02 | 同上 + Perplexity Finance（产品参考） | verified \| partial \| abstain 徽章绑真闸 | 职人视图仍去角色化 |
| A-EV-01 | 仓内 `eval/retrieve_*`；hybrid-rag-mcp 类 harness | Recall@k / MRR 分列表可重复 | 不预填数字；CI 策略见 A-EV-02 |
| A-EV-02 | DeepEval citation faithfulness；Trust-Align；citation-abstention CI gate | claim 对不齐 evidence registry → fail | GitHub Actions 增量；与零 LLM gate 语义分离（ADR-0005） |
| A-EV-03 | `docs/ops/延迟与检索回退周报.md`；NVIDIA/Phoenix 字段习惯（不新建主名） | 轨迹目录 → P95 + fallback rate | 纯函数；显式切 BM25 ≠ `bm25_fallback` |

---

## B. 顶尖 demo 包（L4 上沿）

### B-01 数字闸（code-computed · 对不上则 abstain）

**目标模式**：主张中的数由代码/工具算出；模型只叙述来源；数字不在证据或算式里 → abstain。

| 类型 | Name | URL | 可摘模式 | 核验 |
|---|---|---|---|---|
| GitHub | citation-abstention-rag | https://github.com/jkelly-dev1/citation-abstention-rag | 数字单独校验：引用句在、数字被改 → unsupported；reason codes；CI 门 | ★0 · pushed 2026-10-06 |
| GitHub | sec-filing-agent | https://github.com/Zhonghui-li/sec-filing-agent | **Numbers only from tools**（XBRL / `compute_*`）；LLM 不做金融算术；`abstain(reason)`；audit replay | ★3 · pushed 2026-10-12 |
| GitHub | finance-filings-analyst | https://github.com/aman9824/finance-filings-analyst | 数字必须落在 verbatim quote 内；verifier 与模型分离；cite-or-abstain | ★0 · pushed 2026-06-15 |
| GitHub | FinTrustRAG | https://github.com/Nakshathra-2808/FinTrustRAG | NCTS：抽数 → 对 chunk 核对 → 公式重算 → trust score 分档 | ★29 · pushed 2026-05-26 |
| GitHub | VeNRA | https://github.com/pagand/VeNRA | 程序执行算数 + fact ledger + forensic audit；对抗数值陷阱数据 | ★6 · pushed 2026-06-21 |
| GitHub | FinRobot | https://github.com/AI4Finance-Foundation/FinRobot | 数字 code-computed；LLM 叙事；audit operators | ★8202 · pushed 2026-09-28 |
| 论文 | VeNRA / numerical hallucination detector | arXiv:2603.04663（作者页宣称；日期随 arXiv） | 数值幻觉与 ledger 分离 | 论文页随站点；以 arXiv 为准 |
| 产品/实践 | Verified Citations and Abstention in RAG for Finance（博文） | https://adam-boudjemaa.com/blog/agents-in-production/3 | span + NLI + **numeric exact match**；失败 abstain | 产品文，非仓 |

**FreshLatch 摘法（默认 = verbatim 对账）**：在 `reverify_claim(fresh)` / 落档前加确定性数字闸：从主张与 T1 证据抽数 → exact（或声明容差）匹配；失败 reason code 如 `numeric_mismatch` → unknown/abstain。不必上 XBRL。公式重算（FinRobot / VeNRA）为可选增强，须另票；与缺口清单歧义 §3 对齐后再勾 B-01。

### B-02 冲突拒答（`conflicting_evidence`）

**目标模式**：两条 T1 互斥时拒答，不挑更流畅的一侧。

| 类型 | Name | URL | 可摘模式 | 核验 |
|---|---|---|---|---|
| 论文+基准 | Evidence Sufficiency Benchmark（CMC 2026） | https://www.techscience.com/cmc/v89n1/68467 · PDF 同站 | L1–L5；**L5 Conflicting Evidence** 上模型 over-answer 65–91%；缺证据比冲突更容易拒 | 期刊页 2026 |
| 论文 | GRAB-RAG / Prompt-Based Abstention Fails Under Misleading Context | https://arxiv.org/html/2608.22228 | 缺证据会拒；误导/冲突上下文仍答；需 **conflict check**，非 prompt  sufficiency | arXiv HTML |
| 论文+代码 | Sufficient Context（ICLR 2025） | https://arxiv.org/abs/2411.06037 · https://github.com/hljoren/sufficientcontext | 二元 sufficient + selective generation；对「不够」强，对「相反」需另挂冲突边 | ★69 |
| 论文+代码 | CRAG | https://arxiv.org/abs/2401.15884 · https://github.com/HuskyInSalt/CRAG | Incorrect/Ambiguous 边；冲突可映射到 Incorrect→abstain（勿默认 web 回退） | ★475 |
| GitHub | citation-abstention-rag | 同上 | 多 claim 支持比；可扩 reason：`conflicting_evidence` | 见上 |
| GitHub | xai-rag | https://github.com/neeraj1909/xai-rag | claim 级 NLI：supported / not_supported / **neutral**；可扩展 contradiction 标签 | ★0 · pushed 2026-10-07 |
| GitHub | RAGChecker | https://github.com/amazon-science/RAGChecker | claim-level entailment 诊断字段 | ★1127 |

**FreshLatch 摘法**：retrieve 或 verify 节点做 **pairwise / NLI 冲突检测**（两条 `@T1` 证据对同一前提相反）→ 固定 reason code `conflicting_evidence` → 禁止 fresh。评测夹具对齐 Evidence Sufficiency 的 L5 故事（小 n 冒烟即可，不报方差）。**禁止**只靠 prompt「若冲突请拒答」。

### B-03 句子级归因（支撑句 + 反对句）

**目标模式**：答案一句 → 可点开支撑摘录与反对摘录，落到 T1 原文位置。

| 类型 | Name | URL | 可摘模式 | 核验 |
|---|---|---|---|---|
| 论文（CHI’26） | Attribution Gradients | https://arxiv.org/abs/2510.00361 | claim 分解 → supporting **与 contradicting** excerpts → 渐进展开 | arXiv 2025-10 |
| 论文+代码 | MIRAGE（EMNLP 2024） | https://arxiv.org/abs/2406.13663 · https://github.com/Betswish/MIRAGE | model internals 标 context-sensitive token→文档；需开源权重访问 | 官方仓存在 |
| 论文 | Traceable Search | https://arxiv.org/abs/2409.13099 | phrase-level provenance | 日期未再核 PDF |
| 论文 | RAG-Ex（SIGIR 2024） | https://dl.acm.org/doi/10.1145/3626772.3657660 | 通用解释层「为何生成该句」 | ACM |
| GitHub | finance-filings-analyst | 同上 | **character offsets** 端到端；span 可点回 | 见上 |
| GitHub | citation-abstention-rag | 同上 | claim ↔ exact character span | 见上 |
| GitHub | AsaifAli/LangGraph-RAG | https://github.com/AsaifAli/LangGraph-RAG | evidence IDs + fail-closed citation + UI | ★0 · pushed 2026-09-21 |
| 产品 | Perplexity Finance | https://www.perplexity.ai/finance | 答案旁来源条（闭源交互参考） | 产品 |

**FreshLatch 摘法**：复验单审计/归因面板：对判定理由句做 claim 切分；每 claim 挂 ≥1 支撑 `evidence_id` + 可选反对 id；点击滚到原文（现有 `read_source` / 双栏）。**间接**学 Attribution Gradients 的「支撑+反对」展开；**不上** MIRAGE（托管 qwen 无 internals）。offsets 有则更好，无则先句级字符串定位。

### B-04 一次看得见的时序 / patch 闸（夹具）

**目标模式**：同一主张、两版 `as_of` 或两 `patch_id`，错版本被滤或 stale；面板看得见。**≠** 冲乙成立。

| 类型 | Name | URL | 可摘模式 | 核验 |
|---|---|---|---|---|
| 论文+代码 | MRAG | https://arxiv.org/abs/2412.15540 · https://github.com/siyue-zhang/MRAG | 无训练：query→main+temporal；语义×符号时间分 | EMNLP Findings 2025 · 仓存在 |
| 论文 | TempRetriever | https://arxiv.org/abs/2502.21024 | 训练型：query date + doc timestamp 写入 dense（**代码未公开**） | 论文；代码「acceptance 后」 |
| 论文+代码 | TSM（Time-Specifier Model Merging） | https://arxiv.org/html/2507.06782 · https://github.com/seungyoonee/TSM | 按时间词分训再 merge；保非时序查询 | ★1 · pushed 2025-12-03 |
| 实践 | sec-rag-analyst / xai-rag UI | 见上 | Hits 展示 metadata 列（日期/版本） | 见上 |
| 仓内 | T0/T1 `as_of` WHERE；`RESULT-Y` 丙 | `store/*` · `docs/evidence/patch-events/RESULT-Y.md` | 夹具用两版文档演示 filter；末页诚实放丙 | 已核实 |

**FreshLatch 摘法**：合成夹具包：主张 A + doc@T0 与 doc@T1（或 `patch_id=p1|p2`）；错版本不进 top-k 或判定 stale；UI 列 `as_of`/`patch_id`/有效期。排序可先抄 MRAG 符号时间分（B 层）；**训练型**留给 C-01。

### B-05 失败复放 + 人审改账（`disputed`）

**目标模式**：打开失败轨迹能指检索空 / grade 不够 / L2 拒；人可 `disputed` 写台账并可再开。

| 类型 | Name | URL | 可摘模式 | 核验 |
|---|---|---|---|---|
| 文档 | LangGraph time-travel / checkpointers | https://docs.langchain.com/oss/python/langgraph/use-time-travel · checkpointers 文档 | `checkpoint_id` 复放/fork；**仓内已用于人审**，Agent 层勿整图迁入 | 官方文档 |
| 论文+代码 | Causal Agent Replay (CAR) | https://arxiv.org/abs/2606.08275 · https://github.com/jaineet17/causal-agent-replay | `do_resample(k)` 找因果失败步；带 CI；**排障用，非默认路径** | ★14 · pushed 2026-07-09 |
| 论文 | Who&When（ICML 2025，CAR 引用） | arXiv:2505.00212（CAR 文内） | LLM-judge 步归因 ~14% → 勿当唯一归因 | 经 CAR 引用 |
| GitHub | trust-rag-finance | https://github.com/patibandlavenkatamanideep/trust-rag-finance | advisor feedback：used / edited / **rejected** / **disputed**；audit trail | ★2 · pushed 2026-06-05 |
| GitHub | citation-abstention-rag | 同上 | hash-chained audit；reason code 可复盘 | 见上 |
| GitHub | verified-scholar-agent | https://github.com/gaurika05/verified-scholar-agent | grade 理由 + LangSmith 轨迹 | ★0 |
| 仓内 | HumanLatch `discard`/`renew`；`latch_log`；轨迹 JSONL | `gates/human_latch.py` · `latch/pipeline.py` | 扩展动词或旁路 `disputed` 事件；失败步投影到审计 UI | 已核实 |

**FreshLatch 摘法**：**直接**——审计面板解析 JSONL：空 hits / grade / L2 deny 三桶高亮；latch 增 `disputed`（或等价事件）写入可导出台账。**间接**——CAR 只在排障剧本用，不进默认复验。**不要**把人审图改成 Agent 运行时。

---

## C. 领域标杆（产品 L5）

### C-01 训练过的时序检索

**目标模式**：有文档化的**训练型**（或已发表等价方法落地）时序臂；Recall@k / MRR / nDCG 来自该次测量。

| 类型 | Name | URL | 可摘模式 | 核验 |
|---|---|---|---|---|
| 论文 | TempRetriever | https://arxiv.org/abs/2502.21024 | date/timestamp 融入 dense；时间负采样；Top-1 / nDCG 提升 | **官方代码未公开**（文内声明） |
| 论文+代码 | TSM | https://github.com/seungyoonee/TSM · arXiv HTML 2507.06782 | 分 specifier 训练再参数合并 | 仓存在 |
| 论文 | TMRL / Temporal-aware Matryoshka Adaptation | https://arxiv.org/html/2601.05549 | 高效适配 TEM；对照 TempRetriever / Ts-Retriever | 2026-01 HTML |
| 论文 | TS-Retriever（CIKM 2024） | DOI 10.1145/3627673.3679800 | 时间约束 contrastive negatives | 会议 DOI |
| 论文+代码 | MRAG | 见 B-04 | **无训练**基线；C-01 应用训练臂时仍可作对照 | 仓存在 |

**FreshLatch 摘法**：另开评测臂（`bind_eval_retrieval_mode` 族），**不**改 `PRODUCTION_RETRIEVAL_MODE` 除非 Hard-Gold/改臂闸授权。优先可复现的 TSM 或自训小适配；TempRetriever 仅理论锚，无代码则勿写「已复现 TempRetriever」。测量预注册；n 小标冒烟。

### C-02 在线 claim 监控

**目标模式**：生产路径持续抽检 faithfulness / claim；漂移可报警或拒发；层身份 = 观测 ≠ 实验成立格。

| 类型 | Name | URL | 可摘模式 | 核验 |
|---|---|---|---|---|
| 产品/文档 | Arize Phoenix Faithfulness | https://arize.com/docs/phoenix/evaluation/pre-built-metrics/faithfulness | span 级 faithful/unfaithful；挂 trace | 官方文档 |
| 产品/文档 | Arize AX RAG eval cookbook | https://arize.com/docs/ax/cookbooks/evaluate/evaluating-rag | 在线任务：采样、过滤、retrieval vs correctness 分层 | 官方文档 |
| 产品 | LangSmith online evals | 厂商文档 / 2026 综述文 | 生产流量 LLM-as-judge + 人工队列 | 综述：metacto 等；以官方为准 |
| 实践文 | LLM Observability before first incident | https://shirokoff.ca/blog/llm-observability | 抽 10–20% 流量；滚动 faithfulness；OTel/openinference | 博客 |
| 论文+代码 | RAGChecker | 见上 | claim 诊断字段 → 监控 payload | ★1127 |
| 仓内纪律 | SLO-min6 / phase-2；ADR-0042 | `docs/ops/*` · `docs/evidence/slo-phase2/*` | 协议已有；**禁新建 Phoenix-\* 主名**；观测 ≠ RESULT-Y | 已核实 |

**FreshLatch 摘法**：自研轻量：轨迹采样 → claim 抽检（对齐 `#571` 协议）→ 周报/报警；可选 OTel 导出。字段习惯可对照 Phoenix/LangSmith，**产品名与主依赖不强制引入**（与仓内「不新建 Phoenix-* 主名」一致）。

### C-03 多租户权限

**目标模式**：租户隔离 + 工具/数据权限可测；越权 fail-closed；`tenant_id` **不得**由模型/客户端随意指定为唯一真相。

| 类型 | Name | URL | 可摘模式 | 核验 |
|---|---|---|---|---|
| 架构指南 | Secure multitenant RAG（Microsoft） | https://github.com/microsoftdocs/architecture-center 路径 `docs/ai-ml/guide/secure-multitenant-rag.md`（亦见 Learn 站点同题） | store-per-tenant vs 共享库+filter；security trimming；审计接地数据 | 文档仓路径以 blob 为准 |
| GitHub | multitenant-rag-rbac | https://github.com/AmarReddy4/multitenant-rag-rbac | JWT 声明构造 filter；**禁止客户端自带 filter**；Qdrant `must` tenant | ★0 · pushed 2026-04-19 |
| GitHub | ragmoat | https://github.com/jay-tank/ragmoat | AST lint：向量查询无 tenant filter → blocker | ★0 · pushed 2026-08-13 |
| 参考 | SkillAlchemy R1 vendor filter cheatsheet | https://github.com/agentsope/SkillAlchemy（`skills/agentsop-multi-tenant-rag/references/...`） | 各向量库强制 filter 对照表；静默漏滤风险 | 路径存在于搜索结果；作 cheatsheet |
| 仓内 | `filter_retrieve_pool` + 可选 `tenant_id`；poison/untrusted | `store/base.py` | 今日可选过滤；升格为**服务端身份注入** + 越权单测 | 已核实 |

**FreshLatch 摘法**：从会话/鉴权上下文注入 `tenant_id`，工具参数若传入必须与会话一致否则拒；SQLite WHERE 强制；单测：跨租户 retrieve 零命中或 error。不换 Qdrant；pattern 迁移到现有 store。

### C-04 成立的 patch 实验

**目标模式**：合法新预注册下成立格通过；**仍不得**称优于 RARR·KPR；禁止把 B-04 夹具写成乙。

| 类型 | Name | URL | 可摘模式 | 核验 |
|---|---|---|---|---|
| 经典+代码 | RARR | https://arxiv.org/abs/2210.08726 · https://github.com/anthonywchen/RARR | 检索→一致性门→最小修订→attribution report；**对照基线，非要打败的口号** | ★53 · 代码偏旧（2023） |
| 论文+代码 | Knowledge Pull Requests (KPR) | https://arxiv.org/abs/2609.26634 · https://github.com/alexmartin1722/kpr | claim 抽出→冲突旗标→ChangeLog；人审批准知识变更 | ★1 · pushed 2026-09-23 |
| 仓内 | PREREG-Y / RESULT-Y / ADR-0037 等 | `docs/evidence/patch-events/*` · `docs/adr/0037*` | 成立格只认 T−C；同尺禁二次充数；当前**丙** | 已核实 |
| 论文（金融修订相关） | Enhancing Financial Report QA … Reranking（短名单曾列） | arXiv HTML 2603.16877 | rerank lift 写法进报告模板；**不是** patch 成立格 | 日期以 arXiv 为准 |

**FreshLatch 摘法**：若再冲乙——**新预注册**（或合法新尺）+ 仪器修复 + 敏感性/冒烟门闩后主跑；抄表纪律不变。工程可摘 KPR 的「冲突旗标 + ChangeLog + 人批」到补丁提案 UX；RARR 作文献对照与边界句来源（「不称优于」）。B-04 夹具永远进 demo 页，不进成立格。

---

## 跨层：产品与 X

| 来源 | 用途 | 限制 |
|---|---|---|
| Perplexity Finance | B-03/A-UI 来源条交互 | 闭源；勿声称实现对等 |
| FinRobot Desktop | B-01 数字/叙事分离；A-SK playbook | 重桌面；FreshLatch 用 Streamlit/静态页薄实现 |
| X 上「hybrid 后再 rerank」共识帖 | 与仓内默认臂一致的舆论锚 | 不作测量证据 |

---

## 建议摘取优先级（仍不开票）

与缺口清单累加一致：

1. **先 A**（组会票序）——否则 B/C 无拒答骨架。  
2. **B-01 → B-02 → B-03**（数字闸、冲突码、句子归因）——面试记忆点最大。  
3. **B-04 + B-05**（可见夹具 + 复放/`disputed`）——把「看得见」补齐。  
4. **C-02 / C-03**（在线抽检、租户强制）——工程标杆，相对可并行。  
5. **C-01 / C-04**（训练时序臂、成立的 patch 实验）——成本高；C-04 受预注册与丙防火墙约束最严。

---

## 明确不摘 / 不做

- 整栈迁到 LangChain/LangGraph Agent、换 FAISS/Chroma/Qdrant 为生产默认库。  
- 把 CAR 或 MIRAGE 设为默认在线路径。  
- 用 B-04 夹具或 UI 文案改写 `RESULT-Y` 成立格。  
- 编造 TempRetriever 官方训练仓或未核实的星标数字。  
- 新建与仓内纪律冲突的观测产品主名（Phoenix-* 等）。

---

## 收尾

- 本页路径：`docs/evidence/module-level-frontier-refs-ABC-2026-10-12.md`  
- 配套勾选：`docs/evidence/module-level-gap-checklist-2026-10-12.md`  
- 未开票、未改 `src/`、未改实验结论页。
