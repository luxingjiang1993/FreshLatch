# FreshLatch 模块现状与下一步（只读评估）

> 日期：2026-10-12。基线：`main` @ `666679c`（`docs(SLO-min6): #562 落冻结金标 canary 跑法（SLI 6）`）。
> 性质：独立读码评估。本文件不改 `PRODUCTION_RETRIEVAL_MODE`，不改任何实验结论页（`RESULT-Y` / `PREREG-Y` / `retrieval-decision.md` 等），不合并任何既有 PR。
> 口径：实现冲突以已接受 ADR + `CONTEXT.md` 为准。`docs/spec/00-架构总览.md` 仍写「生产默认 BM25」，与现行代码和 `docs/roadmap.md`、`docs/evidence/retrieval-decision.md` 不一致；下文以代码为准，不把这份旧规格当现状。

调查范围是 `src/freshlatch/` 的现行入口、`skills/`、`docs/agents/agent-guards.md`、`docs/roadmap.md`、`CONTEXT.md` 与相关 ADR。没有跑 LLM 评测，没有改检索臂。

## 总判

主链已经是可跑的产品形，不是空壳：Lead/Critic 的 function call 循环、规则闸、HumanLatch、复验单 UI、发前钩子、检索多臂都在代码里。缺口集中在「已经算出来但没交到下一层」和「文档承诺了但运行时没接线」，而不是缺一整套新框架。

| 模块 | 已经扎实的部分 | 真实缺口 |
|---|---|---|
| Function call / tools | 白名单 fail-closed、OpenAI schema、证据 id 白名单、查询串不可由模型改写 | `web_search` 只有注释；W9 工具处理器在、默认白名单不挂；工具返回不含已记录的检索臂 |
| Skill | 三份教义表启动时注入；缺文件会落 `skill_fallback`；单测锁工具名 ⊆ 白名单 | `references/*.md` 运行时不可读；Agent Guards hooks 未启用；`memory_forensics` 不进 Runner |
| RAG / retrieval | 生产默认 `hybrid+rerank`；本地 embedding + rerank；缺向量 / 缺权重有明确回退标记 | 回退只写在单次事件里，没有周报聚合；`parent_id` / `hypo_questions` 仍是空列；评测云端 embedding 与生产本地模型是两条路 |
| AI Agent | 裸 `while` 循环、步数软收尾、Run 级检索预算、轨迹 JSONL、Auditor 单轮 structured-output | 轨迹没有完整 messages，也没有 `token_usage`；`auditor_max_steps` 未被任何循环读取 |
| UI | 复验单 + 发前页、T1 三卡、人审、补丁确认、预算轮询 | 审计视图只显示轨迹路径；进程内单会话；无响应式布局 |

建议的开工顺序见文末。下面每节先写现状，再写可验收的下一步。下一步都是在现有符号上加接线或纯函数，不换检索栈，不重写实验结论。

---

## 1. Function Call / tools

### Status

工具表的唯一真相在 `src/freshlatch/tools.py`。

- Schema 工厂是 `_fn` / `_TOOL_DEFS` / `tool_specs`。白名单外的名字在 `tool_specs` 里直接 `KeyError`，不交给模型。
- 现行 Lead 白名单是 `LEAD_TOOLS_W3`：`retrieve`、`read_source`、`reverify_claim`、`mark_stale`、`mark_gap`、`finish_reverify`、`spawn_critic`。
- `LEAD_TOOLS_W1` 是无 Critic 的历史视图。`LEAD_TOOLS_W9` 在常量里多了 `list_memories`、`spawn_forensic`，Runner 不使用它。
- Critic 白名单 `CRITIC_TOOLS`：`retrieve`、`read_source`、`mark_stale`、`report_finding`。没有 `reverify_claim`，没有 spawn。
- `AUDITOR_TOOLS = ("verdict",)` 只是历史挂载视图。现行 Auditor 不走工具循环，见第 4 节。
- `spawn_auditor` 的 schema 还在 `_TOOL_DEFS`，ADR-0009 已废止，不在 `LEAD_TOOLS_W3` 里。`LeadReverifier._execute` 也没有这个名字。
- `WEB_SEARCH_SOCKET_NOTE` 是一行注释。没有 `web_search` schema，也不在任何白名单。评测侧 `src/freshlatch/eval/__init__.py` 与 `eval/runner.py` 用同一句话登记「模型物理上不可见」。
- 执行器：`LeadReverifier._execute`（`src/freshlatch/roles/lead.py`）、`Critic._execute`（`src/freshlatch/roles/critic.py`）。循环层再挡一次：`run_loop` 里名字不在本轮 `tools` 则抛 `UnknownToolGuard`。
- `retrieve` 的 `query` 参数在 schema 里是 required，执行时被丢掉。真正的检索串来自 `transform_claim_query`（`src/freshlatch/store/query_transform.py`）：statement 恒等，有登记维度或 focus 时只追加封闭枚举的中文名。模型多传 `retrieval_mode` 会得到 `{"error": "生产路径不可指定 retrieval_mode"}`。
- 证据引用：`check_evidence_ids`（`src/freshlatch/evidence.py`，由 Lead/Critic 调用）要求 id 逐字来自本会话 retrieve 返回，fresh/stale 还必须锚 `@T1`。
- `mark_stale` 在工具层就做了长度、纯元陈述（`is_meta_only_disproof`）、支撑误读（`is_support_review_misread_as_disproof`）、维度枚举、受理层维度预检（`dimension_crosscheck_mismatch`）。这些不是只写在 prompt 里。
- 可选 `tenant_id` 经 `optional_tenant_id` 传入 `RunContext.try_retrieve`，空值表示不过滤租户。poison / untrusted 在 `filter_retrieve_pool` 里始终剔除。
- 旁路：`src/freshlatch/forensic_tools.py` 的 `create_forensic_tools` 是另一套 async 字典，给 `scripts/w9_w12_memory_forensics_demo.py` 和 `tests/unit/test_i2_retrieve_trust.py` 用。它不进入 `run_loop`。

### 缺口

- 工具观察不带检索臂。`RunContext.try_retrieve` 已经把 `retrieval_mode`、`rerank_mode` 写入轨迹事件，`_t_retrieve` 的返回只有 `blocks` 和 `retrieval_used`。模型和审计 UI 都看不到这次是 `hybrid+rerank` 还是 `bm25_fallback`。
- `read_source` 把整篇 `full_text` 塞回 messages，没有长度上限。语料变大时，步数预算还没到，上下文先被一篇原文撑满。
- `UnknownToolGuard` 直接抛出，整段循环中断，而其它工具错误是回给模型的 `{"error": ...}`。白名单外调用和参数错误的失败形态不一致。
- `LEAD_TOOLS_W9` 的两个 handler（`_t_list_memories`、`_t_spawn_forensic`）已经写在 `_execute` 里，但 `tool_specs(list(LEAD_TOOLS_W3))` 不发给模型。这是预留，不是半接通的线上能力。`docs/research/MemoryForensics操作定义对齐与论文路径设计评估.md` 已明确否决「立刻把默认白名单换成 `LEAD_TOOLS_W9`」。
- `forensic_tools.py` 与 `roles/forensic.py` 是两套入口，名字相近，职责不同。前者是 async 工具适配，后者是确定性闩。

### Next

1. **把已有检索臂写进 retrieve 观察。** 在 `LeadReverifier._t_retrieve` 与 `Critic._t_retrieve` 的返回里增加 `retrieval_mode` 与 `rerank_mode`，值只读 `store.last_retrieval_mode` / `store.last_rerank_mode`（`try_retrieve` 返回后这两个属性已经写好）。不新增参数，不让模型传入 `retrieval_mode`。
   - Acceptance：单测里绑定 `hybrid+rerank` 与缺 vec 的 `bm25_fallback` 各一次，工具返回的模式与轨迹事件一致；`PRODUCTION_RETRIEVAL_MODE` 仍是 `hybrid+rerank`。
2. **`read_source` 观察截断。** 超过固定字符上限时返回 `full_text` 前缀 + `truncated: true` + 原文字符数。上限写成 `Guardrails` 上的一个整数，默认值进轨迹 `run_meta`。判定仍必须引用 retrieve 返回的 evidence id，截断不创造新的放行路径。
   - Acceptance：超长文档的工具返回带 `truncated: true`，短文档字节级不变；`tests/unit` 里现有点回原文测试保持通过。
3. **白名单与 handler 的契约测试。** 断言 `LEAD_TOOLS_W3` 的每个名字在 `LeadReverifier._execute` 的 handler 表里；`spawn_auditor` 不在该表；`list_memories` / `spawn_forensic` 若留在 handler 表，必须同时断言它们不在发给模型的 `tool_specs` 里。Critic 同理。
   - Acceptance：从 `LEAD_TOOLS_W3` 删掉一个名字或多挂一个 schema 名时，该测试失败。不改变运行时默认白名单。

明确不做：不实现 `web_search`；不把 `LEAD_TOOLS_W9` 设为默认；不把 `forensic_tools.create_forensic_tools` 接进 `run_loop`。

---

## 2. Skill（教义、guards、loader、hooks）

### Status

这里有三套不同的「hook / skill」，不要混成一个平台。

**角色教义（产品运行时）**

- 文件：`skills/reverify/`、`skills/devil_advocate/`、`skills/freshness_audit/`、`skills/memory_forensics/`，各有 `SKILL.md` 与 `references/`。
- 加载器：`src/freshlatch/skills_loader.py` 的 `load_skill_body`。只读 `skills/<slug>/SKILL.md`，剥掉闭合 frontmatter，缺失或空正文返回 `None`。不读 `references/`。
- 注入点：`Runner.__init__` 启动时加载 `reverify`、`devil_advocate`、`freshness_audit` 三份。`LeadReverifier._build_system`、`Critic._build_system`、`Auditor.judge` 在正文非空时用它做 system prompt；为 `None` 时回退内联 `LEAD_PERSONA` / `CRITIC_PERSONA` / `AUDITOR_PERSONA`，并 `emit` `skill_fallback`。
- `memory_forensics` 不在 `Runner._doctrine` 里。`roles/forensic.py` 的模块文档写检测顺序与该 SKILL 对齐，执行体是 `ForensicAgent.inspect` 纯函数，不把 SKILL.md 送进模型。
- 一致性单测：`tests/unit/test_skills.py`。四条断言：frontmatter、正文和 references 里反引号工具名 ⊆ 该角色白名单、focus 六值等于 `FOCUS_DIMENSIONS`、拦截对照表有「场景 / 原因 / 动作」三列。这锁的是文件与常量的静态一致，不证明 references 进了上下文。

**Agent Guards（开发流程，不是产品循环）**

- `docs/agents/agent-guards.md`：工单在 GitHub Issues；本地可选镜像 `tasks/`。默认 Trust = Watch。
- 同一文件写明：`Hooks` 一节是 “Advanced/optional — not enabled in this repo by default.” 仓库里没有启用中的 agent hook 脚本。
- 日链是 `grill-with-docs → to-spec → to-tickets → enrich-tickets → before-implement → /implement`。这是人/代理的开工纪律，不是 `run_loop` 的拦截器。

**发前钩子（产品闸，不是 skill loader）**

- `src/freshlatch/publish_hook.py` 的 `evaluate_publish_hook` 已实装，见第 6 节。它和 skill loader 无关。

`skills/reverify/SKILL.md` 的 frontmatter 写着「半套渐进式披露：references 由循环内 read_source 按需读取」。`read_source` 的实现是 `store.read_source(doc_id, as_of=...)`，只读语料快照。模型没有工具能打开 `skills/reverify/references/verdict-basis.md` 或 `rerun-rules.md`。教义正文已经把主要禁令写进了 SKILL.md 本体，所以主链不依赖这次「按需读」才能跑；但 frontmatter 的那句披露机制是空的。

内联人格字符串仍然很长（尤其 `CRITIC_PERSONA`）。它们是加载失败兜底，和 SKILL.md 双份维护。`skill_fallback` 事件会进轨迹，UI 不展示这个事件类型。

### Next

1. **把 progressive disclosure 做成真工具，或改掉 frontmatter 的假承诺。** 推荐前者，因为 `test_skills.py` 已经把 references 当教义资产在审。新增一个名字稳定的工具（建议 `read_doctrine_ref`），参数只接受本角色 `references/` 下的文件名。Lead 只能读 `skills/reverify/references/`，Critic 只能读 `skills/devil_advocate/references/`。路径规范化后必须仍落在该目录内。把该名字加入对应白名单，并改 SKILL frontmatter 里「用 read_source 读 references」那句，避免再把语料读取和教义读取说成同一个工具。
   - Acceptance：`verdict-basis.md` 返回正文；`../freshness_audit/SKILL.md`、绝对路径、不存在的文件名都返回 `error` 且不读到文件内容；`read_source` 对语料的行为不变；`test_skills.py` 的工具名子集断言更新后仍绿。
2. **`skill_fallback` 进审计视图。** `/api/reverify` 的响应和审计面板增加本轮是否发生 `skill_fallback`、缺的是哪个 slug。数据已经在 `RunContext.events` 里。
   - Acceptance：把 skills 根指到空目录的测试夹具跑完一次 Lead 构造（可不调用真实 LLM，直接调 `_build_system`），事件含 `skill_fallback`，投影函数能把它收成 `{skill: "reverify"}`。不改变兜底人格的文案。
3. **不要把 `memory_forensics/SKILL.md` 注入默认 Lead。** 若产品要在复验单上看见记忆卫生，下一步是人点按钮调用 `ForensicAgent.inspect`，而不是把 `spawn_forensic` 放进 `LEAD_TOOLS_W3`。

明确不做：不启用一套通用 agent hook 框架来替代白名单；不把 Agent Guards 的日链写进 `run_loop`。

---

## 3. RAG / retrieval

### Status

生产默认臂是代码常量，不是环境变量。

- `PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"`，定义在 `src/freshlatch/store/base.py`。
- 枚举 `RETRIEVAL_MODE_ENUM` / `EXECUTABLE_RETRIEVAL_MODES`：`bm25`、`dense`、`hybrid`、`hybrid+rerank`、`bm25_fallback`。
- 运维开关在 `RunContext.set_retrieval_switch`：`bm25`、`hybrid`、`hybrid+rerank`、`hybrid+rerank_lexical`。注释写明两者都不改 `PRODUCTION_RETRIEVAL_MODE`。Agent 工具签名不能传 `retrieval_mode`。评测夹具走 `arm_eval_retrieval_mode`，且 `mode != "eval"` 时拒绝。
- 打分在 `SQLiteStore.retrieve`（`src/freshlatch/store/sqlite_store.py`）和镜像实现 `InMemoryStore.retrieve`：
  - 未请求向量臂时走 `run_pipeline`：`recall_bm25` → `stage_vector_fuse` → `stage_rerank`。后两级在 `src/freshlatch/store/pipeline.py` 里是切片透传，所以这条路径就是 BM25。
  - `hybrid`：BM25 与 `rank_dense` 做 `rrf_fuse`，`RRF_K = 60`。
  - `hybrid+rerank`：先 RRF，再 `rerank_hybrid_candidates`。神经精排只吃前 `NEURAL_RERANK_K = 10` 条，尾巴保持 hybrid 原序。
  - 没有任何可用 vec 时 `last_retrieval_mode = "bm25_fallback"`，不再把缺一块 vec 的整池降级（`rank_dense` 跳过坏块）。
- 本地模型登记在 `src/freshlatch/models.py` 的 `MODEL_REGISTRY`：`local_embed` = `BAAI/bge-small-zh-v1.5`（`LOCAL_EMBED_DIM = 512`），`neural_rerank` = `BAAI/bge-reranker-base`。加载在 `store/local_embed.py`、`store/neural_rerank.py`，缓存目录是 `FASTEMBED_CACHE_PATH`。`FRESHLATCH_LOCAL_EMBED=0` 不挂 embedder；`FRESHLATCH_NEURAL_RERANK=0` 不加载 cross-encoder，记 `last_rerank_mode=lexical_fallback`。权重失败同样回退 `rerank_lexical`。
- 生产入口挂载：`ui/app.py` 的 `_store` 与 `packs.py` 调用 `attach_local_embedder`。入库补 vec 在 `SQLiteStore.add_document` 路径里调用 `fill_chunk_vecs`。
- 另一条 embedding 仍在：`store/embeddings.py` 的 `embed_texts` 打 DashScope `text-embedding-v4`（`MODEL_REGISTRY["embed"]`）。`python -m freshlatch.eval retrieve` 在 `data/dense/index.sqlite` 存在时会跑 `run_arm_compare` / `run_rerank_compare`（`eval/retrieve_eval.py`）。这是评测臂，不是 UI 的生产检索。
- 过滤：`as_of` / `source_type` 是 SQL `WHERE`。`filter_retrieve_pool` 去掉 `poison` / `untrusted`；只有调用方传入 `tenant_id` 才做租户硬过滤。
- 切块：`store/ingest.py` 按 `## pN` 锚切。`store/pdf_anchor.py` 把 PDF 文本抽成同构 markdown。`parent_id`、`hypo_questions` 在 `Chunk` 和 SQLite schema 里是留位列，没有任何检索阶段读取它们。
- 查询变换对比、陷阱集、Hard-Gold 都有函数：`run_transform_compare`、`run_trap_eval`、`run_hard_gold_retrieve`。CLI `retrieve --hard` 会打 Hard-Gold。没有 `data/dense/index.sqlite` 时，同一次 `retrieve` 命令不会跑三臂对比。
- 分型三臂另有入口：`src/freshlatch/eval/retrieve_typed.py`（自带 `main`，查询向量走 `store/embed_cache.py`）。它没有挂到 `python -m freshlatch.eval` 的子命令上。

`docs/roadmap.md` 文首写明：2026-10-07 拍板后生产默认是 `hybrid+rerank`，一键回退是 `set_retrieval_switch("bm25")`。`docs/evidence/retrieval-decision.md` 记录了同一决定，并写明切换理由（更大语料、更多噪声）在当时的评测语料上没有测到，仍是待复测假设。本评估不重新解释那些数字，也不建议再改默认臂。

### 缺口

- 单次事件有 `retrieval_mode` / `rerank_mode`，没有按 `docs/ops/延迟与检索回退周报.md` 定义的周报聚合函数。该协议要求同一行同时给出 e2e P95 与 retrieval fallback rate，并且「显式切到 BM25 或词重叠精排不算回退」。代码里这两类事件已经可区分：显式开关是 `RunContext.retrieval_switch`，意外回退是 `bm25_fallback` 与 `rerank_mode=lexical_fallback`。
- `stage_vector_fuse` / `stage_rerank` 的名字容易让人以为 BM25 路径也做了融合和精排。它们只服务 `run_pipeline` 的 BM25 路径，生产默认不走这里。
- 云端 `text-embedding-v4` 与本地 `bge-small-zh-v1.5` 的向量不能混在同一次 cosine 里（维度不同）。`rank_dense` 会跳过维度不符的块；若整池维度都不符，结果是 `bm25_fallback`。这是正确的降级，但调用方若把旧的 `data/dense/index.sqlite` 当成生产索引，会静默退回 BM25。
- 每次 `retrieve` 把符合 `as_of` 的 chunk 全读进内存再 BM25。`docs/research/检索路线选型评估.md` 的规模前提是几十到几百篇，这条实现对那个规模成立。它不是 ANN，也没有倒排持久化。
- `hypo_questions` 没有生成器，也没有参与召回。不要把它说成已经做了 HyDE。

### Next

1. **轨迹 → SLI 5 两字段的纯函数。** 新增一个不碰闸、不碰 `PRODUCTION_RETRIEVAL_MODE` 的聚合：输入是一批 `type=retrieve` 事件（以及可选的 Run 耗时）。输出一行：`e2e_p95_ms`（没有耗时样本时字段为空并写明「无样本」）、`retrieval_fallback_rate`。分子只计 `retrieval_mode=bm25_fallback` 或 `rerank_mode=lexical_fallback`。`retrieval_switch=bm25` 或 `hybrid+rerank_lexical` 的事件不算分子。分母是 retrieve 事件条数。
   - Acceptance：三行夹具（正常 `hybrid+rerank`、缺 vec 的 `bm25_fallback`、显式 `set_retrieval_switch("bm25")`）得到 fallback rate = 1/3；函数不写库、不调用 embedder。协议页 `docs/ops/延迟与检索回退周报.md` 本步不改写。
2. **本地向量的臂对比与云端索引解耦。** 给 `python -m freshlatch.eval retrieve` 增加一个显式子路径（或把已有的 `retrieve_typed.main` 收成子命令），用 `attach_local_embedder` 的同一模型在内存或当前 pack 的 sqlite 上打 bm25 / hybrid / hybrid+rerank，并在报告里写上模型名 `BAAI/bge-small-zh-v1.5` 与 `BAAI/bge-reranker-base`。没有 `FASTEMBED_CACHE_PATH` 或权重时退出码非 0，禁止把 BM25 结果标成 hybrid。
   - Acceptance：假向量单测（沿用 `retrieve_typed` 已有的假向量写法）三臂的 `last_retrieval_mode` 与请求一致；不读取 `DASHSCOPE_API_KEY`；不修改 `PRODUCTION_RETRIEVAL_MODE`。
3. **入库时拒绝混维 vec。** `fill_chunk_vecs` 或 `add_document` 在写入前检查维度等于 `LOCAL_EMBED_DIM`。已有非 512 维 blob 的库，`retrieve` 继续按块跳过，但打一条日志，日志里带 `last_retrieval_mode` 将要走的降级原因（维度不符 vs 完全没有 vec）。
   - Acceptance：写入 1024 维 vec 的单测被拒绝或被标成不可用，不进入 cosine；512 维路径与现在一致。

明确不做：不把生产默认改回 BM25；不引入 FAISS / Chroma / 另一个 reranker；不把 `hypo_questions` 做成 HyDE；不重跑或改写 `docs/evidence/retrieval-decision.md` 里的历史数字。

---

## 4. AI Agent（runner、多步、轨迹）

### Status

循环与角色是分开的，图不在循环里。

- 循环：`src/freshlatch/roles/loop.py` 的 `run_loop`。`while steps < max_steps`：`chat` → 若无 `tool_calls` 则 `finished=True` 结束 → 否则串行执行本轮全部 tool call。预算用尽且未自发结束时，追加一条 `soft_close` 再做一次无工具 `chat`。本文件不 import langgraph。ADR-0004 把这条路线钉死。
- 预算：`Guardrails`（`src/freshlatch/guardrails.py`）默认 Lead 18 步、Critic 8 步、检索 24 次/Run。`auditor_max_steps = 6` 与 `forensic_max_steps = 8` 只出现在这个 dataclass 里，没有任何调用方读取。Auditor 是 `Auditor.judge` 一次 `response_format=json_object`。Forensic 是 `ForensicAgent.inspect`，无 LLM 步数。
- 编排：`Runner.run`（`src/freshlatch/runner.py`）按主张顺序跑。每条先 `apply_rot_if_mismatch`（跨轮腐烂，ADR-0025）；命中则本条不进 Lead，直接 unknown。否则 `LeadReverifier.run`。然后 `_finalize`：`arbitrate_fresh` / `arbitrate_stale_mark` / `arbitrate_unknown`、`rule_gate`、`seal_no_unfounded_fresh`、`apply_policy_after_rule_gate`。
- Lead 在 `reverify_claim(fresh)` 前调用 `_auto_critic_checkpoint`（本会话未派驻过则强制一次，focus 不限）。fresh 与 mark_stale 在落档前调用 `_auto_auditor_checkpoint`。Critic 是同进程新的 `run_loop`，共享 `RunContext` 的检索预算，不共享 messages。
- 检索预算：`try_retrieve` 超限返回 `RETRIEVAL_EXHAUSTED` 字典，不抛异常。
- 轨迹：`_dump_trajectory` 写 `reports/trajectories/run-<ts>.jsonl`。首行 `run_meta`（mode、decoding、guardrails、作废名单、软收尾文案）。其后是 `ctx.events`：`lead_step` / `critic_step`（工具名、args、result）、`retrieve`、`auditor_verdict`、`skill_fallback`、`claim_result` 等。每条主张一条 `claim_final`。评测可以在 `claim_final` 之后追加 `i1_eval_labels`（`eval/i1_labels.py`），字段不写入生产 status。
- LLM：`src/freshlatch/llm.py` 的 `LLMClient.chat`。默认模型 `qwen-flash`，`DecodingParams` 默认 `temperature=0.0`。`token_usage` 在客户端上累加 `prompt_tokens` / `completion_tokens`。`Runner._dump_trajectory` 不写这份用量。UI 也不读它。
- 超时包装：`Runner.guarded_agent_call` → `i3_hardening.run_with_timeout_structured`。这是 I3 夹具用的受控包装，`Runner.run` 的主路径没有套上它。
- 模式：`RunContext.mode` 为 `online` 或 `eval`。eval 由评测 harness 用来跳过 HumanLatch 并禁止强制以外的联网；联网禁止的机制仍是白名单里没有 `web_search`。

`loop.py` 的 `on_event` 只在工具执行后触发。模型两轮工具之间的 assistant 文本留在 `LoopResult.messages`，函数返回后被丢掉，除了 Lead 在没有 `decision.reason` 时从最后一条 assistant 文本截 500 字做理由。因此 JSONL 能复盘「调了什么工具」，不能复盘「模型在工具之间说了什么」。

多主张是单线程顺序跑，共享 24 次检索。没有主张级并行，也没有跨主张的 planner。

### Next

1. **轨迹补上用量和助手文本，且不改 `claim_final` 字段集。** `run_meta` 增加 `token_usage`（来自 `LLMClient.token_usage.to_dict()`）。每个 `lead_step` / `critic_step` 之前，若本轮 assistant 有 `content`，追加一条 `type=assistant_note`，`content` 截断到与 `decision.reason` 相同的 500 字，并带 `truncated` 布尔。`claim_final` 的键保持现在的集合。
   - Acceptance：用假 `chat` 跑两步工具循环，JSONL 含 `run_meta.token_usage.total_tokens` 与一条 `assistant_note`；对 `claim_final` 做键集合快照，与改前测试夹具一致。
2. **删掉或接上死预算字段。** `auditor_max_steps` 与 `forensic_max_steps` 二选一：从 `Guardrails` 和 `run_meta.guardrails` 去掉，并在注释指向「Auditor 单轮 / Forensic 无 LLM」；或者让 `Auditor.judge` 拒绝第二次调用（若未来误接循环）。推荐去掉未读字段，避免轨迹看起来像 Auditor 仍有 6 步循环。
   - Acceptance：`rg auditor_max_steps src` 无匹配，或唯一匹配处有失败测试证明第二次 `judge` 被拒。现有 Auditor 解析测试不改断言。
3. **`UnknownToolGuard` 改成观察，而不是拆掉循环。** `run_loop` 捕获该异常，写入 `{"error": "未允许的工具: ..."}` 的 tool message，步数照常计数。白名单本身仍然 fail-closed：模型看不见的工具不会出现在 schema 里；这条只处理模型幻觉出的名字。
   - Acceptance：假消息带一个不在白名单的 tool name 时，循环继续到 `max_steps` 或下一次无工具回复，`tool_trace` 里有该错误；在白名单内的工具仍执行。

明确不做：不把 LangGraph 引进 `roles/`；不把 Auditor 改回多步工具循环；不在本步给主张做并行调度。

---

## 5. UI

### Status

UI 是 FastAPI 薄壳加两份静态 HTML，没有前端构建。

- 入口：`src/freshlatch/ui/app.py`。页面：`GET /` → `ui/static/reverify.html`，`GET /prepublish` → `ui/static/prepublish.html`。
- 复验单是双栏（左主张、右原文），标题带 SYNTHETIC。默认职人视图 `VIEW_MODE_DEFAULT = "craftsman"`，可切审计视图。主按钮文案常量 `MAIN_BUTTON_TEXT = "开始复验"`。
- 会话状态是模块级 `_state`：主张列表、轨迹路径、latch、预算、`run_ctx`、零命中、`active_run_id`、绑定的 T1 checksum。单进程一份。没有登录，没有多会话。
- T1 来源：`T1SourceSession`（`src/freshlatch/t1_source.py`）。上传、粘贴草稿再确认、内置 synthetic 包、薄 URL（`ALLOWED_URL_HOST = "www.mckinsey.com"`，失败四态不入库）。未 `ready` 时 `POST /api/reverify` 返回 400。
- 复验：`POST /api/reverify` 同步跑完 `Runner.run`，然后 `HumanLatch.enter_round`。进行中 `GET /api/claims` 经 `_current_budget` 读 live `RunContext`。页面 `setInterval(pollBudget, 400)` 更新步数和检索条。这是真轮询，不是画出来的进度条。
- 人审：`POST /api/latch/decide`、`POST /api/latch/rerun`、`GET /api/latch/status`。动词仍是 `discard` / `renew`（`VALID_ACTIONS`）。
- 补丁：`POST /api/patch/propose`、`/confirm`、`/discard-draft`。确认后 `_confirm_patch_reverify` 再跑单条。这是 Evidence-bound 路径，不是 HumanLatch 的第三个按钮。
- 其它读侧：主张台账导出、Client Memo 导出、`POST /api/publish-hook/check`、原文 `GET /api/source/{doc_id}`、主张草稿导入。
- 审计面板（`reverify.html` 的 `#audit-panel`）展示轨迹路径、解码参数、预算摘要。`renderGateResults` 在审计视图下再重复一次轨迹路径字符串。页面不解析 JSONL，不显示 `retrieval_mode`、`rerank_mode`、`skill_fallback`、`token_usage`。
- 布局：`main{display:grid;grid-template-columns:44% 56%}`。文件内没有 `@media`。窄屏会挤在同一套双栏里。
- 核心包不依赖 Web：闸、循环、检索都能在无 FastAPI 的测试里跑。UI 反过来在 `_store()` 里调用 `attach_local_embedder`，所以从页面点「开始复验」会走本地 embedding，除非 `FRESHLATCH_LOCAL_EMBED=0`。

### Next

1. **审计视图读本轮轨迹事件，而不是只显示路径。** `GET /api/claims` 在已有 `trajectory` 路径时，只读解析 JSONL，投影出：每条 retrieve 的 `query`、`as_of`、`hits`、`retrieval_mode`、`rerank_mode`；是否出现 `skill_fallback`；`run_meta` 里的 decoding。职人视图不渲染这些字段。解析失败时面板写「轨迹不可读」，不改主张 status。
   - Acceptance：用一份含 `bm25_fallback` 与 `skill_fallback` 的夹具 JSONL，审计投影含这两条；职人视图的 HTML 断言（现有 `test_ui_view_mode.py` 一类）仍不出现 Lead/Critic 字样以外的新角色名泄漏。若投影只在 `view=audit` 的 JSON 字段里，职人 DOM 测试可以不改。
2. **复验完成后把 `token_usage` 放进审计面板。** 依赖第 4 节把用量写入 `run_meta`。面板一行：`prompt_tokens` / `completion_tokens` / `total_tokens`。没有该键时显示「本轨迹无用量」，不要显示 0 假装计量过。
   - Acceptance：无 `token_usage` 键的旧 JSONL 不报错；有键时数字与文件一致。
3. **窄屏改成上下叠放。** 仅当视口宽度低于一个明确阈值（建议 800px）时，`main` 改为单列，主张列表在上、原文在下。桌面双栏的列宽比例保持 44/56。不改按钮文案，不改职人/审计的信息边界。
   - Acceptance：现有 UI 单测仍绿；手工或渲染脚本在窄宽度下网格列数是 1。本仓库 UI 测试目前以 FastAPI TestClient 和 HTML 字符串为主，若没有浏览器，就用 HTML 里存在对应 `@media` 规则作为机器验收，并在 PR 里说明没有跑真实视口。

明确不做：不把复验单改成聊天框；不在职人视图展开 Agent 轨迹；不把 `patch` 做成 HumanLatch 第三个动词；不在这一步做多用户会话存储。

---

## 6. 其它已存在、值得接着做的模块

这些不是另起一条产品线。它们已经在仓里，而且和上面五块共用同一条主链。

### 规则闸与人审

- `gates/rule_gate.py`：`rule_gate`、`arbitrate_*`、`seal_no_unfounded_fresh`、`dimension_crosscheck_mismatch`。绿灯唯一出口。fresh 路径的 checksum 仍是结构性空转：只有 `decision.validity_basis` 非空才比对，而本批不构造 fresh 的 basis（ADR-0017、ADR-0024）。renew 半边可以注入真的 `checksum_fn`。不要把「把 fresh checksum 接上」当成顺手补丁；ADR-0024 写明实装须另票预登记。
- `gates/human_latch.py`：`apply_decisions`，动词只有 `discard` / `renew`。`derive_override` 只标记人是否对抗落档前的机器 status。
- `gates/basis_rot.py`：复验入口和 `GET /api/claims` 都会对带 basis 的 fresh 做跨轮腐烂重检。无 basis 的 fresh 不检。
- `gates/policy_gate.py`：Verify+ 旁路的来源禁区，不是 OPA。`gates/meta_gate.py`、`gates/support_review.py` 是 stale 理由的确定性预检。
- `latch/pipeline.py`：LangGraph `interrupt` + SqliteSaver。图只做人审 checkpoint。Agent 循环不 import 它。

下一步若要动闸，只做一件已经在协议里、还没有函数的事：从 `latch_log` 里 `override is not None` 的行算 override rate，输出到与 `docs/ops/人审-override周报.md` 同构的一行。不要新增人审动词，不要把这个比率写成「模型变好」。

- Acceptance：三行 `latch_log` 夹具（override 1、override 0、旧行 override 空）里，空行不进分母；函数不写库。

### Eval harness

- 主 CLI：`python -m freshlatch.eval`，子命令 `run`、`control`、`control-c`、`report`、`retrieve`（`eval/__main__.py`）。`run` 是金标端到端，默认不进 CI。`control` / `control-c` 是无工具假绿对照。`retrieve` 是无 LLM 的 Recall@10 / MRR@10，并在金标和陷阱文件存在时顺带跑变换对比；三臂对比依赖 `data/dense/index.sqlite`。
- 检索纯函数已经比 CLI 表面多：`run_arm_compare`、`run_rerank_compare`、`run_transform_compare`、`run_trap_eval`、`retrieve_typed.main`。
- `eval/x1_checks.py`、`eval/x1_drafts/` 是题集草稿与结构检查，不是复验主链。
- `eval/patch_events_*.py` 是路线 B/Y 的实验仪器（生成、评委、敏感性、正式发送）。那些模块的结论页已经冻结或另有预注册。本评估不提议改它们的判据、温度或成立格。

和主链有关、且不碰实验结论的下一步，就是第 3 节的「本地向量臂对比成为显式子命令」。除此之外，eval 目录不缺新的实验臂。

### 发前、补丁、台账

- `prepublish.py`：`PrepublishRegistry`、`disposition_for_claims`。包结论三值在 `disposition.py`。
- `evidence_bound.py`：`propose_patch` / `confirm_patch` 的闸。引用必须落在本 Run 已入库 T1。
- `publish_hook.py`：`evaluate_publish_hook`。缺 run、checksum 漂移、勿发、需补丁未 ack，都是结构化拒绝。HTTP 入口在 UI 里，并认 `FRESHLATCH_HOOK_TOKEN`。
- `claim_ledger.py`：作废名单与 latch_log 的只读投影，不是第三张写表。
- `patch_events.py`：JSONL 账。UI 人审成功会追加事件；实验臂开关不在发前页面上。

这块相对完整。下一步不该再加一种导出格式。若要做工程，优先把发前页上的 hook 拒绝码（`HOOK_CHECKSUM_DRIFT` 等）在 UI 上显示成现有 `message`，而不是只返回 JSON。验收：TestClient 对漂移 checksum 得到 409，HTML 或 API 投影含 `HOOK_CHECKSUM_DRIFT`。不改 `evaluate_publish_hook` 的分支表。

### 可观测性

已经有的记录面：

- 轨迹 JSONL（工具步、检索臂、decoding、guardrails）。
- `LLMClient.token_usage` 与 `decoding_log`（停在进程里）。
- `i1_events.append_event`（`src/freshlatch/i1_events.py`）写评测事件 JSONL，与生产 status 分开。
- `docs/ops/生产观测最小6-索引.md` 定义了六个 SLI。索引自己写明层身份是观测/Watch 加离线 canary，不是实验成立格，也还没有硬百分数 Gate。

代码里还没有一个函数把「一周的轨迹目录」收成 SLI 5 那一行，也没有把 `token_usage` 落盘。第 3 节和第 4 节的两项就是补这个洞。不要为此引入 LangSmith、OpenTelemetry 或另一套 trace 产品名；协议页已经禁止新起 Phoenix / Confident 主名。

### 记忆刑侦

`roles/forensic.py` 的 `ForensicAgent` 能标 `unverified` / `dead` / `contradictory` 并 `propose_quarantine`。Lead 默认看不见它。`long_term_memory` 表在 SQLite schema 里。复验单没有记忆列表。

下一步保持「人触发的确定性扫描」，不要先做 LLM Forensic。验收：给定三条记忆夹具（无 `source_ref`、与 T1 数字冲突、两条同对象反义），`inspect` 的三类计数与现有单测一致，并且 UI 若加按钮，也只调用这个函数、不扩大 `LEAD_TOOLS_W3`。

---

## 建议开工顺序

按「改动面小、不碰默认检索臂、不碰实验结论、做完能用测试看见」排序：

1. 检索臂写进 retrieve 工具返回，并在审计视图读轨迹里的 `retrieval_mode` / `rerank_mode` / `skill_fallback`（第 1、5 节）。
2. `run_meta.token_usage` + `assistant_note`，审计面板在有键时才显示数字（第 4、5 节）。
3. SLI 5 纯聚合函数，分子定义对齐 `docs/ops/延迟与检索回退周报.md`（第 3、6 节）。
4. `read_doctrine_ref`，并修正 SKILL frontmatter 里把 references 说成 `read_source` 的那句（第 2 节）。
5. 本地 embedding 的三臂子命令，与 `data/dense/index.sqlite` 的云端向量脱钩（第 3 节）。
6. `read_source` 截断、`UnknownToolGuard` 改为观察、去掉未读的 `auditor_max_steps` / `forensic_max_steps`（第 1、4 节）。

第 1 到第 3 项都不改变模型能看见的工具集合，适合先做。第 4 项会改白名单，应该单独一张票。

## 本评估故意不提议的事

- 不改 `PRODUCTION_RETRIEVAL_MODE`，不把 `set_retrieval_switch` 的默认值写死成别的臂。
- 不重写 `docs/evidence/retrieval-decision.md`、`docs/evidence/patch-events/RESULT-Y.md`、`PREREG-Y.md` 或任何已落盘的 Recall@k / MRR 数字。
- 不引入 FAISS、Chroma、LangChain、LangSmith，或一套与仓内 SQLite + BM25 + 本地 fastembed 无关的检索框架。
- 不把 `web_search` 接进白名单。
- 不把 `LEAD_TOOLS_W9` 提成默认，也不把 `forensic_tools.py` 的 async 适配器接进 `run_loop`。
- 不在未另票预登记的情况下构造 fresh `validity_basis`。
