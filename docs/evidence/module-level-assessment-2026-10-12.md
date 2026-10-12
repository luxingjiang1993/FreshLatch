# FreshLatch 模块水平评估（2026-10-12）

> 性质：只读水平评估。不改生产代码，不改 `PRODUCTION_RETRIEVAL_MODE`，不改 `RESULT-Y` / `PREREG-Y` / `retrieval-decision.md`。
> 代码基线：`main` @ `a7505d66bac24e7b6ffc1e243c86c61ad2a95b96`（`docs(SLO-phase2): #573 judge–human calibration 旁表协议（P3）`）。
> 对照稿：draft PR [#580](https://github.com/luxingjiang1993/FreshLatch/pull/580) 的 `docs/evidence/architecture-module-status-2026-10-12.md`（基线 `666679c`，未合并）。下文凡引用该稿，均已在本基线上重读代码。
> 前沿输入：两源整合版（组会票序 FC→Skill→RAG→Agent→UI，外加 Eval）。冲突 C1 / C4 / C5 的情景规则见 §2。
> 测量：本评估未跑 `pytest`，未跑 `python -m freshlatch.eval`，未重放路线 Y。已落档数字只标明出处；本轮没有新测到的指标一律写「未测到」。

## 1. 执行摘要

**As-is：整体 L3。** 主链已经是可测的复验产品：工具白名单与规则闸能把无 T1 证据的 fresh 打回，生产检索默认是 `hybrid+rerank`，轨迹能记下检索臂。Skill 的运行时仍是整份注入加失败回退，hooks 未启用。权限分层、检索 sufficiency 拒答、citation CI 都未落地，所以整体不到 L4。

**If-landed：整体 L4。** 情景是组会票序，并且 RAG 一张票同时吸收两源：sufficient-context / CRAG 拒答，加上 temporal / patch 元数据过滤。不换向量库，不装 REA。主链（Function Call、RAG、Agent）五轴木桶到 L4：非法调用有 reason code 与 L0/L1/L2，证据不足能拒，失败轨迹能复放，golden 与 citation 进 CI。仍不到 L5：没有金融级数字闸与成熟 HITL 产品面，路线 Y 的正式结果仍是已落档的丙。

一句话：现在能诚实讲解的是「复验闸 + hybrid+rerank + 预注册负结果」；按短名单只摘 fields/modes 之后，能讲解的是「可回归的拒答产品」。单做来源 A 或单做来源 B，主链木桶都还是 L3。

## 2. 标尺说明

### 2.1 五档

| 档 | 含义 |
|---|---|
| L1 演示/脚本 | 能跑通故事，缺契约与可测门禁 |
| L2 可工作原型 | 主路径可用，fail-open 多，观测弱 |
| L3 工程化 MVP | 有 schema / 测试 / 证据字段，核心路径 fail-closed 或可拒答 |
| L4 生产向团队产品 | 可回归、可审计、有 SLI/ablation、权限分层落地 |
| L5 领域标杆 | 时序 / patch / 金融级证据闸门与 HITL 成熟，可对外对标头部产品 |

### 2.2 五轴（每模块都评）

1. 正确性与 fail-closed：非法 args、证据不足时能否拒。
2. 可观测与可复放：trace、reason codes、checkpoint。
3. 可测性：contract、Recall@k、MRR、citation gate。
4. 与产品定位契合：复验已签发主张，temporal / patch-aware。
5. 与前沿短名单差距：只对照可摘 pattern，不要求整栈迁移。

### 2.3 木桶与整体档

模块综合档取该模块五轴的最低档。整体档取主链三模块的最低档：Function Call、RAG、AI Agent。这三块直接决定「非法调用拒不拒、证据不足答不答、失败能不能复放」。

Skill、UI、Eval 并列报告。它们可以 corroborate 主链，不能单独把整体抬档，也不能因为 Skill 未启用 hooks 就把已经有规则闸的主链打成 L2。

L4 要四件事同时在：可回归、可审计、SLI 或 ablation 能重复跑、权限分层落地。缺一件就停在 L3。L5 还要时序/patch/金融证据闸和 HITL 都成熟到能对标头部产品。路线 Y 已落档为丙，本评估不把该实验说成标杆。

### 2.4 双情景与冲突项

| 情景 | 落地内容 | 整体档 |
|---|---|---|
| As-is | 仅 `main` @ `a7505d6` | L3 |
| If-landed | 组会票序，且 RAG 同时吸收 temporal/patch 与 sufficiency/abstain。形状：FC schema + L0/L1/L2 → Skill hooks `failClosed` → RAG sufficiency/CRAG + temporal/patch → Agent verify/abstain + checkpoint → UI Query→Hits→Attribution→Unknown\|Override → Eval golden + citation CI | L4 |
| 只落地 A | 来源 A 序：RAG temporal/patch → FC schema/门禁 → Skill 业务化 → Agent 短环 → UI 双栏 → Eval CI。不含 B 的 L0/L1/L2、hooks `failClosed`、sufficient-context、checkpoint | L3 |
| 只落地 B | 组会序的闸门与 walkthrough，不含 A 的 temporal×semantic 与 patch/`as_of` 元数据过滤 | L3 |

C1（票序）：A 先 RAG，组会先 FC。If-landed 按组会序。只落地 A 时 RAG 的契合轴会先变厚，主链木桶仍是 L3，因为拒答与权限分层不在 A 的首票里。

C4 / C5（RAG 主打、CRAG 挂点）：A 把 temporal/patch 放在检索，把 CRAG 放在 Agent 论文列。B 把 sufficiency→abstain 与 CRAG 的 grade→abstain 边放在 RAG。If-landed 规定 RAG 同时吸收两边，CRAG 的挂点在 retrieve 边（Correct / Incorrect / Ambiguous → 再检索或 abstain），Agent 只消费该边的 grade 与 reason code，不另做一套网络回退。只落地 A：RAG 综合档保持 L3（契合轴单独到 L4 门槛，fail-closed 轴仍是现有规则闸）。只落地 B：RAG 综合档保持 L3（fail-closed 轴到 L4 门槛，temporal/patch 增量未落地）。

明确不做：换向量库、装 REA、改 `PRODUCTION_RETRIEVAL_MODE`、重写路线 Y 成立格。

### 2.5 已核实的已知事实

- 生产默认检索是 hybrid+rerank，不是 BM25。常量在 `src/freshlatch/store/base.py` 的 `PRODUCTION_RETRIEVAL_MODE`。`tests/unit/test_store.py` 断言该值。`RRF_K = 60`（`src/freshlatch/store/pipeline.py`），神经精排只吃前 `NEURAL_RERANK_K = 10` 条（`src/freshlatch/store/neural_rerank.py`）。本地模型是 `BAAI/bge-small-zh-v1.5` 与 `BAAI/bge-reranker-base`（`src/freshlatch/models.py`）。
- `docs/spec/00-架构总览.md` 图注仍写「生产默认 BM25」。该句与代码、`docs/roadmap.md`、`docs/evidence/retrieval-decision.md` 不一致。本报告以代码为准。
- 冲乙 PE-Y 正式跑为丙。`docs/evidence/patch-events/RESULT-Y.md` 已落档：分层「结果丙」；T−C 95% 下界 ≤ 0，成立格写「不成立」。本评估未复跑 `compare_primary`。点估计与区间只以该页为准，此处不另算。
- 中文文档保留英文技术词。本报告沿用 BM25、hybrid、rerank、Recall@k、MRR、embedding、chunk。

### 2.6 draft PR #580 哪些句子在本基线上仍成立

#580 未合并。它的基线 `666679c` 到本基线 `a7505d6` 的增量是 SLO phase-2 协议页（主张忠实抽检、失败归因三桶、人机校准旁表），`src/freshlatch/` 的行为代码不在这四笔提交里。下列 #580 句子经重读仍成立：

| #580 句子 | 本基线证据 |
|---|---|
| Lead 白名单是 `LEAD_TOOLS_W3`，`web_search` 只有注释 | `src/freshlatch/tools.py`：`LEAD_TOOLS_W3`、`WEB_SEARCH_SOCKET_NOTE` |
| `load_skill_body` 只读 `SKILL.md`，不读 `references/` | `src/freshlatch/skills_loader.py` |
| Agent Guards hooks 默认未启用 | `docs/agents/agent-guards.md` 写明 Hooks 为 Advanced/optional，仓库内无 `hooks.json` / `failClosed` |
| 生产默认 `hybrid+rerank`；缺向量记 `bm25_fallback` | `PRODUCTION_RETRIEVAL_MODE`；`sqlite_store.py` 在无可用 vec 时写 `last_retrieval_mode = "bm25_fallback"` |
| 工具返回不含检索臂；轨迹事件含检索臂 | `LeadReverifier._t_retrieve` 返回 `blocks` 与 `retrieval_used`；`RunContext.try_retrieve` 的事件含 `retrieval_mode` / `rerank_mode` |
| `run_loop` 不 import langgraph；轨迹 `run_meta` 不含 `token_usage` | `src/freshlatch/roles/loop.py`；`Runner._dump_trajectory` |
| 审计视图展示轨迹路径 | `src/freshlatch/ui/static/reverify.html` 把 `STATE.trajectory` 渲染成路径字符串 |
| `auditor_max_steps` 没有循环读取 | 仅 `src/freshlatch/guardrails.py` 字段，注释为「W5–W8 实装后生效」 |

#580 建议的下一步（检索臂写进工具返回、`token_usage` 落盘、SLI 5 聚合函数）在本基线上仍是建议，未实现。

## 3. 总表

| 模块 | as-is | if-landed | 关键缺口（最多 3） |
|---|---|---|---|
| Function Call | L3 | L4 | 无 API `strict` 与通用 schema 再验；`UnknownToolGuard` 直接拆循环；无 L0/L1/L2 |
| Skill | L2 | L3 | 加载失败回退内联人格；`references/` 运行时不可读；hooks 未启用 |
| RAG | L3 | L4 | 无 sufficient-context / CRAG 边；无 patch 元数据过滤与 temporal×semantic；SLI 5 与 citation 未进 CI |
| AI Agent | L3 | L4 | 无 verify→abstain 节点与命名 reason code；轨迹无完整 assistant 文本与 `token_usage`；checkpoint 只覆盖人审 |
| UI | L3 | L4 | 审计面只显示轨迹路径；无 Hits 分数与 Attribution；Unknown 不展示检索 reason code |
| Eval / Evidence | L3 | L4 | 金标 LLM 与 Recall 不进 CI；无 claim citation gate；SLI 协议页没有 `src/` 聚合函数 |

只落地 A 或只落地 B 时的模块档（综合档，木桶）：

| 模块 | 只落地 A | 只落地 B |
|---|---|---|
| Function Call | L3 | L4 |
| Skill | L2 | L3 |
| RAG | L3 | L3 |
| AI Agent | L3 | L4 |
| UI | L3 | L4 |
| Eval / Evidence | L4 | L3 |
| 整体（主链木桶） | L3 | L3 |

只落地 A 时 Eval 可以到 L4，因为 A 的第 6 步包含 citation CI。RAG 与 Function Call 仍是 L3，主链木桶是 L3。只落地 B 时 Function Call、Agent、UI 到 L4，RAG 的契合轴没有 temporal/patch 增量，主链木桶仍是 L3。

## 4. 分模块详评

### 4.1 Function Call · as-is L3 · if-landed L4

产品里的工具是复验动作。现行 Lead 可见集合是 `LEAD_TOOLS_W3`：`retrieve`、`read_source`、`reverify_claim`、`mark_stale`、`mark_gap`、`finish_reverify`、`spawn_critic`（`src/freshlatch/tools.py`）。活跃数低于短名单的「≤20」。`tool_specs` 对白名单外名字直接 `KeyError`。schema 带 `additionalProperties: false` 与 `required`。

| 轴 | as-is | 证据 |
|---|---|---|
| 正确性与 fail-closed | L3 | `mark_stale` 的 `dimension` 非法整 call 拒绝。`tests/unit/test_dimension_crosscheck.py` 有 `test_lead_mark_stale_illegal_dimension_rejected`。`retrieve` 若带 `retrieval_mode`，`LeadReverifier._t_retrieve` 返回 `{"error": "生产路径不可指定 retrieval_mode"}`，检索串改走 `transform_claim_query`。证据 id 由 `check_evidence_ids` 限定为本会话 retrieve 返回值。 |
| 可观测与可复放 | L3 | 工具步进入 `RunContext.events`，再由 `Runner._dump_trajectory` 写入 JSONL。非法工具名走 `UnknownToolGuard`（`roles/loop.py`），异常抛出后循环中断，没有 typed reason code 回灌。 |
| 可测性 | L3 | 维度非法、证据 id、白名单有单测。没有 BFCL 式「合法 call / 应拒 / 非法 args」回归维。本评估未跑该维，未测到 illegal-call 通过率。 |
| 产品契合 | L3 | `as_of` 是工具参数，取 T0/T1。没有 `patch_id` 工具。`LEAD_TOOLS_W9` 含 `list_memories` / `spawn_forensic`，Runner 默认不把它们放进 `tool_specs`。 |
| 前沿差距 | L3 | 可摘项里，小 catalog、`additionalProperties: false`、错误回给模型，已经在主路径上。未摘：API 侧 `strict: true`（`LLMClient.chat` 只把 `tools` 传给 `chat.completions.create`，无 `strict`）、耗尽 retry 后的统一 fail-closed、L0 只读 / L1 需批 / L2 禁止。 |

If-landed（组会首票形状）：检索相关工具各自 schema，非法 args 先变成 reason code，有限自纠，耗尽后 fail-closed；写操作用审批映射 L0/L1/L2。五轴都到 L4。不到 L5：catalog 仍是复验域，没有 multi-turn agentic 排行榜规模。本评估未测到落地后的 illegal-call 率。

只落地 A：schema、错误 code、契约测会变厚，权限分层不在 A 的可摘清单里，综合档保持 L3。只落地 B：综合档 L4。

### 4.2 Skill · as-is L2 · if-landed L3

运行时有三份教义：`skills/reverify/`、`skills/devil_advocate/`、`skills/freshness_audit/`。`load_skill_body` 剥掉 frontmatter，把正文交给角色 system prompt。文件缺失或正文为空返回 `None`，调用方回退内联人格并记 `skill_fallback`。加载器文档写明这是故意不抛。这是 fail-open。

`skills/reverify/SKILL.md` 的 frontmatter 写「references 由循环内 read_source 按需读取」。`read_source` 读的是语料快照（`store.read_source`），没有工具能打开 `skills/reverify/references/`。`tests/unit/test_skills.py` 锁的是文件里的工具名 ⊆ 白名单，以及 focus 六值，不证明 references 进了上下文。

Agent Guards（`docs/agents/agent-guards.md`）是开工纪律：grill → spec → tickets → implement。Hooks 一节写明默认不启用。仓库内检索不到 `failClosed` 或 `hooks.json`。

`skills/memory_forensics/` 不进 `Runner` 的默认教义注入。`ForensicAgent.inspect` 是确定性函数。

| 轴 | as-is | 证据 |
|---|---|---|
| 正确性与 fail-closed | L2 | 教义缺失时回退人格并继续跑。高风险路径没有 exit≠0 的可执行入口。 |
| 可观测与可复放 | L2 | `skill_fallback` 会进轨迹事件。审计页不展示该事件（UI 只渲染轨迹路径，见 §4.5）。 |
| 可测性 | L2 | `tests/unit/test_skills.py` 是静态一致。没有 hook deny 的 contract。 |
| 产品契合 | L2 | 教义正文写了 T0/T1、`mark_gap`、unknown。patch diff、财报、策略 walkthrough 没有独立 skill 包。 |
| 前沿差距 | L2 | 目录 + `SKILL.md` 已有。未摘：`allowed-tools` 运行时约束、metadata→body→references 三级真加载、`failClosed: true`。 |

If-landed：3–5 个中文业务 skill（财报 / 事件 / patch diff / 策略 walkthrough）加上一个 Guards hook 样板（exit 2 deny，`failClosed: true`）。正确性轴到 L3。样板 hook 仍缺 skill 库的 retrieve+rerank，也缺按周回归的权限 SLI，综合档 L3。L4 要等 hook deny 本身进入可重复的 contract。

只落地 A：playbook 与渐进加载变厚，hooks 仍未启用，综合档保持 L2。只落地 B：综合档 L3。

### 4.3 RAG · as-is L3 · if-landed L4

生产路径在 `SQLiteStore.retrieve`：BM25 与 dense 做 RRF（`RRF_K = 60`），`hybrid+rerank` 再对前 10 条做本地 cross-encoder。没有任何可用 vec 时 `last_retrieval_mode = "bm25_fallback"`。reranker 不可用时 `last_rerank_mode = lexical_fallback`。`filter_retrieve_pool` 剔除 `poison` / `untrusted`。`as_of` 与 `source_type` 是 SQL `WHERE`。

`Chunk` 有 `parent_id` 与 `hypo_questions`，注释写明留位。`src/freshlatch/store/` 下没有 `patch_id`、`valid_from`、`valid_to`。时序能力停在 T0/T1 快照过滤。semantic × temporal 分，以及 patch 元数据先于 RRF 的过滤，都尚未落地。

评测函数在 `src/freshlatch/eval/retrieve_eval.py` 与 `retrieve_typed.py`（Recall@k、MRR@10、臂对比）。CI（`.github/workflows/ci.yml`）只跑 `ruff` 与 `pytest tests/`，工作流注释写明金标 runner 不走 CI（ADR-0005）。本评估未复测 Recall@k / MRR / nDCG。已落档决策链在 `docs/evidence/retrieval-decision.md`，其中写明 2026-10-07 真人拍板把默认臂改为 hybrid+rerank，拍板范围是 DECISION-16 的 16 条。本报告不抄那页的小数，避免把历史测量说成本次结果。

`src/freshlatch/` 内没有 sufficient、CRAG、faithfulness 的实现符号。证据不足的拒答发生在规则闸：无 `t1_evidence_ids` 不得 fresh（`gates/rule_gate.py`），以及 Lead 教义里的 `mark_gap`。拒答点在判定闸。检索质量分级尚未落地。

SLI 5（e2e P95 与 retrieval fallback rate）的协议在 `docs/ops/延迟与检索回退周报.md`。`src/` 里没有把一周轨迹收成该行的函数。claim-level faithfulness 在 `docs/ops/抽检-主张忠实.md` 与 `docs/evidence/slo-phase2/周报附录骨架.md`，骨架自己写着不填比率。本评估未测到 fallback rate、P95、faithfulness。

| 轴 | as-is | 证据 |
|---|---|---|
| 正确性与 fail-closed | L3 | 缺向量有具名回退，毒块被滤掉。检索层对「上下文不够」没有 abstain。空命中仍把 `blocks` 交回模型，拒答靠后续闸。 |
| 可观测与可复放 | L3 | 单次 `retrieve` 事件有 `query`、`as_of`、`evidence_ids`、`retrieval_mode`、`rerank_mode`、`hits`。没有周聚合，工具观察里也没有这些臂字段。 |
| 可测性 | L3 | Recall@k / MRR 函数与历史报告在仓。CI 不跑它们。本评估未测到新的 Recall@k 或 MRR。 |
| 产品契合 | L3 | T0/T1 换源与复验定位一致（`CONTEXT.md` 的 T0/T1 定义）。patch-aware 排序未进 retrieve。路线 Y 测的是补丁放行，结果丙，且与检索默认臂是两套仪器。 |
| 前沿差距 | L3 | hybrid → RRF(k=60) → rerank 已在生产默认臂上。未摘：sufficient-context 闸、CRAG 三态边、claim faithfulness 字段、temporal×semantic、patch 元数据过滤。 |

If-landed：保留现有 hybrid+rerank 与 SQLite。retrieve 边增加 sufficiency 标签，不足则 abstain 或 CRAG 再检索；chunk 元数据增加 patch / 有效期并在融合前过滤；manifest 记录 rerank 开/关；Recall@k / MRR 与 citation 进入可回归证据。五轴到 L4。不到 L5：不训练 TempRetriever，不上 RAGChecker 级在线监控，向量库仍是 SQLite。本评估未测到落地后的 Recall 增量。

只落地 A：契合轴到 L4 门槛（temporal/patch 过滤），fail-closed 轴仍是今天的规则闸，综合档 L3。只落地 B：fail-closed 轴到 L4 门槛（sufficiency/CRAG），契合轴仍是 T0/T1 `WHERE`，综合档 L3。两边都摘，综合档才是 L4。CRAG 在 If-landed 挂在 RAG retrieve 边；Agent 只读 grade，避免 C5 两套挂点。

### 4.4 AI Agent · as-is L3 · if-landed L4

循环是 `run_loop`（`src/freshlatch/roles/loop.py`）：`while` 里 chat → tool → observe。ADR-0004 把这条路线钉死，并写明 LangGraph 不进 Agent 层。`src/freshlatch/latch/pipeline.py` 的 LangGraph `interrupt` + `SqliteSaver` 只做人审 checkpoint，图注释写「图不是 Agent」。

编排在 `Runner.run`：跨轮腐烂命中则本条不进 Lead；否则 Lead；然后 `rule_gate`、`seal_no_unfounded_fresh`。Auditor 是 `Auditor.judge` 一次 structured output，解析失败落 unknown（`roles/auditor.py`）。Auditor 缺席不构成绿格（`rule_gate` 的 `AUDITOR_ABSENT`）。fresh 必须带锚 `@T1` 的证据 id。

轨迹 JSONL 的 `run_meta` 含 mode、decoding、guardrails。事件含工具步与 retrieve。`LLMClient.token_usage` 在进程内累加，`_dump_trajectory` 不写它。`LoopResult.messages` 在循环返回后不进 JSONL。因此能复盘工具名与 args，不能复盘工具之间的 assistant 文本。`auditor_max_steps` 无读取方。

检索预算耗尽时 `try_retrieve` 返回结构化结果，不抛异常（fail-soft）。`UnknownToolGuard` 则抛异常（fail-closed 但拆掉循环）。两种失败形态并存。

| 轴 | as-is | 证据 |
|---|---|---|
| 正确性与 fail-closed | L3 | 无 T1 证据不得 fresh；Auditor 非法 status → unknown；作废名单上的 fresh 由闸打回。没有独立的 verify 节点。模型在检索空结果后仍可能先生成再被闸打回，拒答点在闸，不在生成前。 |
| 可观测与可复放 | L3 | 工具轨迹 JSONL 与人审 checkpoint 都在。Agent 步没有 time-travel。`token_usage` 未落盘。 |
| 可测性 | L3 | CI 跑零 LLM 的闸与 UI 单测（ADR-0005）。金标 `python -m freshlatch.eval run` 不进 CI。本评估未测到 pass@k 或方差。 |
| 产品契合 | L3 | 循环的任务就是复验已签发主张，查询串不允许模型改写。数字与叙事尚未拆成 code-computed 与叙述两段。patch 正式实验为丙，Agent 没有消费该负结果的产品闸。 |
| 前沿差距 | L3 | ReAct 短循环、证据 id、步数软收尾已在。未摘：`retrieve→verify→(repair\|abstain)`、state 里的 `grade` / `retry_count`、失败轨迹 checkpoint、命名 abstention reason codes。 |

If-landed：在现有 `run_loop` 上加 verify 节点与命名 reason code，state 留下 `evidence_ids` / `grade` / `retry_count`，失败轨迹可从 checkpoint 复放。不引入第二套 agent runtime，不把 Causal Agent Replay 当默认。综合档 L4。不到 L5：无人机共检的金融 desk，不把反事实重放当产品路径。

只落地 A：短环 verify|abstain 让正确性轴到 L4 门槛，可复放轴仍缺失败 checkpoint，综合档 L3。只落地 B：综合档 L4。

### 4.5 UI · as-is L3 · if-landed L4

UI 是 FastAPI 加静态复验单（ADR-0002）。`src/freshlatch/ui/app.py` 的 `MAIN_BUTTON_TEXT` 是「开始复验」。`GET /` 为复验单，`GET /prepublish` 为发前页。默认 `VIEW_MODE_DEFAULT = "craftsman"`。主张状态有 fresh / stale / unknown / void（`reverify.html`）。无 `@T1` evidence id 时前端禁用续命，后端闸兜底。

审计面板把轨迹显示为路径字符串，不解析 JSONL，因此页面上看不到 `retrieval_mode`、`rerank_mode`、`skill_fallback`、分数。布局是固定双栏（主张 | 原文），文件内无 `@media`。会话状态是进程内 `_state`，无登录。

相关单测包括 `tests/unit/test_ui_view_mode.py`、`test_ui_latch.py`、`test_ui_redlines.py`、`test_ui_retrieve_zero_hit.py`。本评估未在浏览器里点按，未测到视口行为。

| 轴 | as-is | 证据 |
|---|---|---|
| 正确性与 fail-closed | L3 | 未选定 T1 来源时 `POST /api/reverify` 拒绝。unknown 有文案，要求经 `mark_gap` / `reverify_claim(unknown)` 落档。页面不展示「为什么这条检索不足」。 |
| 可观测与可复放 | L2 | 职人视图隐藏角色名。审计视图有轨迹路径与预算轮询（`pollBudget`）。Hits、rerank 分、reason code 不在面板上。本轴把模块综合档按木桶计算时，与其它 L3 轴取最低会得到 L2。下文「综合档 L3」是按产品面（复验单可拒、可人审、有 TestClient）给的模块档，并单独把观测轴标成 L2，避免用路径字符串冒充归因面板。 |
| 可测性 | L3 | TestClient / HTML 断言在。没有 citation 对齐的 UI contract。 |
| 产品契合 | L3 | 主界面是复验单（ADR-0002、`CONTEXT.md`）。人审动词是 `discard` / `renew`。补丁确认走 Evidence-bound API，与 latch 动词分列。 |
| 前沿差距 | L2 | 已有答案侧的状态与原文点回。未摘：Query→Hits（含 score）→Attribution→Unknown\|Override，`verified\|partial\|abstain` 徽章，trace 时间线。 |

观测轴 L2 与模块综合档：若严格五轴木桶，UI as-is 应记 **L2**。本报告在总表仍写 **L3**，理由写在这里，避免两处数字打架时读者误读：复验单的主路径（判定、人审、发前拒绝）有测试且能拒，符合 L3 的「核心路径可拒」；观测轴单独是 L2。面试时两句都要说。若面试官要求单数字木桶，UI as-is 说 L2。

If-landed：在现有复验单上加四段 walkthrough，abstain 必须露出 reason code，Hits 带已有的检索分。职人视图仍不展开 Agent 角色名。综合档 L4（观测轴随之上去）。不到 L5：无多用户权限，无 PDF span 高亮，无人审 `used/edited/rejected/disputed` 全套。

只落地 A：双栏与徽章相对今天的复验单是增量，reason code 与分数面板不在 A 的最小摘法里，综合档 L3（观测轴可到 L3）。只落地 B：四段 walkthrough 落地，综合档 L4。

### 4.6 Eval / Evidence · as-is L3 · if-landed L4

评测入口是 `python -m freshlatch.eval`（`eval/__main__.py`）：`run`、`control`、`retrieve` 等。`retrieve` 能出 Recall / MRR。假绿对照是无工具基线（ADR-0005）。CI 绿灯表示不变量没破。模型表现绿走手动金标 runner，不进这次 GitHub Actions。

路线 Y 是另一套仪器。`RESULT-Y.md` 抄录结论：结果丙；T−C 未过 Y 尺。预注册在 `PREREG-Y.md`。本评估未复跑，未测到新的 false-accept。丙是已落档负结果，说明止损句事先写死并被遵守；它不证明检索或复验闸达到 L5。

生产观测六项与 phase-2（faithfulness 抽检、失败归因、人机校准）是协议与空表。周报骨架写明样本不足时留占位，禁止把数字写回 `RESULT-Y`。`src/` 无对应聚合实现。

| 轴 | as-is | 证据 |
|---|---|---|
| 正确性与 fail-closed | L4（局部） | 路线 Y 成立格只认 T−C，下界 ≤ 0 则不成立，页内禁止判甲。该纪律约束的是实验抄表。在线 citation 闸尚未落地。 |
| 可观测与可复放 | L3 | 轨迹、`i1_events`、latch_log、patch_events JSONL 分文件。SLI 周报没有代码聚合。本评估未测到任一 SLI 比率。 |
| 可测性 | L3 | 零 LLM 单测在 CI。Recall@k / MRR 与金标 e2e 需手跑。无 citation gate。本评估未测到 CI 里的 Recall 或 citation 通过率。 |
| 产品契合 | L3 | 金标与 Hard-Gold 服务于「过期主张能否被拦住」。patch 正式跑已执行且为丙，产品不能把乙当现状。 |
| 前沿差距 | L3 | 自研 harness 与预注册在。未摘：RAGAS/DeepEval 式 CI assert、claim 级 citation 必须落在 turn-scoped evidence registry、judge 版本缺失即 fail。 |

If-landed：冻结一小撮中文 golden；Recall@k 与 MRR 按臂分列进 CI；答案 citation 对不齐 evidence registry 则 fail。judge 模型版本写进该次运行记录。综合档 L4。不到 L5：不把 LLM-judge 当成金融数字的唯一真相，也不把丙改写成乙。

只落地 A：第 6 步就是这条 CI，Eval 综合档 L4。只落地 B：Recall 表与 citation 落 registry，若没有 CI assert，综合档保持 L3。

## 5. 面试 / 作品集口径

受众：求职 mid-level RAG / Agent。能讲的是仓里已有的闸与已落档的测量纪律。不能讲的是短名单里尚未开票的模式。

### 5.1 能讲

- 产品把已签发主张从「曾经为真」复验成「现在仍可复验」（`CONTEXT.md`）。T0 是签发快照，T1 是复验快照。无 T1 证据 id 不得 fresh（`rule_gate`）。人审是 `discard` / `renew`，作废后不能再被 Agent 改绿。
- 工具面是小白名单。schema 拒绝额外字段。模型不能改检索串，也不能在工具参数里切检索臂。`web_search` 未挂载，避免评测期联网破坏可复现。
- 生产检索默认 hybrid+rerank：jieba BM25 与本地 bge embedding 做 RRF(k=60)，再由 `bge-reranker-base` 重排 top-10。缺向量记 `bm25_fallback`，精排失败记 `lexical_fallback`。切换经过预登记与真人拍板，范围写在 `docs/evidence/retrieval-decision.md`（DECISION-16 的 16 条，不是全库逐行人审）。面试时指向该页，并说明自己这次没有复测。
- 循环是自写 ReAct，LangGraph 只做人审 interrupt。这个边界来自 ADR-0004，可以用「图不是 Agent」讲清楚。
- 路线 Y 正式结果是丙：T−C 的 95% 下界未过预注册的成立格。讲「我们把负结果留在 RESULT-Y，没有改尺」。温度与 seed 以该页为准（`temperature=0`，Decoding.seed 有记录，API seed 为 `None`）。`temperature=0` 时不要把 seed 说成已经采样了运行间噪声。

### 5.2 不能吹

- 不能说已有 sufficient-context、CRAG、claim faithfulness CI。检索空了或不够时，拒答在规则闸，不在检索分级器。
- 不能说 patch-aware 或 temporal hybrid ranking 已上生产。生产时序是 `as_of` 的 T0/T1 过滤。`patch_id` / `valid_from` / `valid_to` 不在 store。路线 Y 为丙，不能说补丁放行实验成立，也不能说优于 RARR / KPR（`RESULT-Y.md` 的边界句）。
- 不能说 function calling 达到 strict constrained decoding 或 BFCL。`LLMClient.chat` 未传 `strict`。没有 L0/L1/L2 工具审批。非法工具名会拆掉循环。
- 不能说 Agent Skills 已是 fail-closed hooks，或 references 会按需加载。现状是整份 SKILL 注入，缺失则回退人格。
- 不能说审计 UI 能看 Hits 分数、rerank、归因。审计视图显示轨迹文件路径。
- 不能把 `docs/evidence/retrieval-decision.md` 或冒烟集 n=36 的历史 Recall 说成此次复测，也不能把冒烟集满分说成 Hard-Gold 结论。本评估未测到新的 Recall@k、MRR、nDCG、P95、fallback rate、faithfulness。
- 不能说整体是 L5 或「对标 Perplexity Finance / FinRobot」。那些产品的 citation walkthrough、code-computed 数字和 HITL 反馈环不在本仓。

### 5.3 作品集里怎么放档位

对外一句话用 §1：现状 L3，短名单只摘落地后 L4。Skill 单独是 L2→L3。UI 若被要求五轴木桶，as-is 观测轴是 L2，模块主路径是 L3。把 #580 称为「另一份未合并的只读架构笔记」，不要写成已合并设计。

## 6. 风险：只做 UI / 讲解、不做闸门

只改复验单的讲解层（徽章、双栏、轨迹时间线、面试稿），不落地 schema 再验、hooks `failClosed`、sufficiency/CRAG、citation CI：

- 整体档停在 **L3**。主链木桶不变。
- UI 表面可以看起来像短名单的 walkthrough。若这些字段不绑定真实的 `retrieval_mode`、grade、reason code，观测轴停在 **L2**：能看故事，不能审计。
- 讲解若把 `mark_gap` 说成 CRAG，或把 T0/T1 `WHERE` 说成 temporal retriever，听众听到的是 L4/L5，代码仍是 L3。作品集会被追问一次路径就穿。
- 路线 Y 的丙不会因为 UI 文案改变。把丙放进幻灯片的「我们如何拒答」页，比放进「我们证明了补丁闸」页安全。

## 7. 未实现、未开功能票

本评估不实现下列项，也不开票。整合版短名单自身写明未开票、未改仓库。`gh issue list --state open` 在 2026-10-12 的打开项集中在 SLO 观测协议与 patch_events 实验轨（例如 #556、#569、#576）。其中没有「FC schema + L0/L1/L2」「Skill `failClosed`」「RAG sufficiency/CRAG + temporal/patch」「Agent verify checkpoint」「UI 四段 walkthrough」「citation CI」的实现票。

下列能力在 `main` @ `a7505d6` 上未实现：

| 项 | 现状符号 | 若要做，形状（仍未开票） |
|---|---|---|
| FC API `strict` + 运行时 schema 再验 + illegal reason code | `tools.py` 有 `additionalProperties: false`；`llm.py` 的 `chat` 不传 `strict`；`UnknownToolGuard` 抛异常 | 检索工具分 schema；耗尽 retry 后 fail-closed |
| 工具权限 L0/L1/L2 | 仓内 L0 现指 HumanLatch 人审出口（`gates/rule_gate.py` 文首） | 读检索 / 写观测需批 / 禁动生产臂，各有测试 |
| Skill hooks `failClosed` | `docs/agents/agent-guards.md` 写明 hooks 未启用 | 一个 `exit 2` + `failClosed: true` 样板 |
| references 按需读取 | `load_skill_body` 不读 `references/` | 独立只读工具，或改掉 frontmatter 的承诺 |
| sufficient-context 与 CRAG 边 | `src/` 无对应符号 | retrieve 边：不足则 abstain 或再检索 |
| temporal×semantic 与 patch 元数据过滤 | 仅 `as_of` WHERE；store 无 `patch_id` | 过滤先于 RRF；不换向量库 |
| claim citation CI | 协议页在 `docs/ops/抽检-主张忠实.md`；CI 只跑零 LLM pytest | golden 上 citation 对不齐则 fail |
| Agent verify 节点与失败 checkpoint | 拒答在 `rule_gate`；checkpoint 在 `latch/pipeline.py` 人审图 | state 含 grade / retry_count；失败轨迹可复放 |
| UI Query→Hits→Attribution→Unknown\|Override | 审计面板渲染轨迹路径 | 绑定已有事件字段，abstain 露 reason code |
| SLI 5 聚合 | 协议在 `docs/ops/延迟与检索回退周报.md` | 纯函数读轨迹目录；显式切到 BM25 的开关不算 `bm25_fallback` |
| `web_search`、默认改挂 `LEAD_TOOLS_W9`、把 LangGraph 引进 `run_loop` | 插座或未默认 | 短名单 If-landed 也不包含这三项 |

#580 文末的六步接线（工具返回带检索臂、用量落盘、SLI 5 聚合、教义读取、本地臂子命令、截断与死字段）在本基线上仍未实现。本报告不开这些票。
