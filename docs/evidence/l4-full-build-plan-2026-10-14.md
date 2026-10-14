# FreshLatch 产品向 L4 构建计划（2026-10-14）

> 读者：仓库主人。本页是开工顺序和薄票，不是 `/implement` 会话，不派 Ronin，不勾选缺口清单。
> 诊断：[l4-system-diagnosis-2026-10-14.md](l4-system-diagnosis-2026-10-14.md)。
> A 层原文：[module-level-gap-checklist-2026-10-12.md](module-level-gap-checklist-2026-10-12.md)。
> 档位：[module-level-assessment-2026-10-12.md](module-level-assessment-2026-10-12.md)。
> 摘法：[module-level-frontier-refs-ABC-2026-10-12.md](module-level-frontier-refs-ABC-2026-10-12.md)。
> 闸摘要：[grok-system-analysis-no-fc-2026-10-14.md](grok-system-analysis-no-fc-2026-10-14.md)。
> 基线：`main` @ `b2caaeffdc6ba56885087fcd5beddd560fb563b2`。

下一份合并进主干的实现 PR 应是下面的主链第 1 票，而不是再写一篇评估。本页本身只增加证据文档。

## 1. 为什么主链不从 Function Call 整包开工

10-12 组会序是 FC → Skill → RAG → Agent → UI → Eval。那个顺序保证最终木桶里有 schema、权限和 hooks。诊断没有删掉这些票。

把它整包放在第一刀，和 10-14 的测量对不上：

- 注册 R1 已无回归。FC schema 不改变冻结名次。
- 注册 A1 是金标 C∩R。FC 目录、`strict`、`tool_tier` 都不读、不写这个交集。线上引用只对应 cite-emit 那一片。
- 注册 T1 的两个 scored 失败是 c2 反序和 c3 双缺失，都在冻结神经 k10 上，而且三题的 R1 any-hit 已是 1。这是检索问题，同时 **不** 表现为注册 T1 数字会跟着代码变——除非替换 `docs/evidence/neural-rerank/per-query.json`，而那不在本计划的授权里。
- 今天的拒答点在 `rule_gate`（无 `@T1` 证据不得 fresh）。检索空了仍把 `blocks` 交回模型。on-call 拒答产品的第一缺口在 retrieve 边。
- 清单写明 A 层完成时 Skill 可为 L3。Skill 不进入主链木桶，不该占第一刀。

主链因此改成：拒答边 → 版本过滤（夹具，不动 x1 指纹）→ cite-emit 与其 CI → FC 卫生与 `tool_tier` → Agent 短环 → UI 绑定 → 可重复臂表。Skill 三票并行，不挡 M1。

最终宣称 L4 之前，FC 三票和 Agent 三票仍然都要落地。改的是顺序，不是范围。

## 2. 全程约束

每张实现票的 Do-not-touch 都包含：

- `PRODUCTION_RETRIEVAL_MODE`（`src/freshlatch/store/base.py`）
- `docs/evidence/patch-events/RESULT-Y.md` 与 `PREREG-Y.md` 的成立格
- `docs/evidence/quality-gate/PREREG.md` 的地板行、`segment_registered:` 行、`owner_freeze:` 行、§7 指纹三行、R1 确认行
- `docs/evidence/neural-rerank/summary.json` 与 `per-query.json`
- `data/eval/guard_should.json`、`cite_sentence.json`、`temporal_new_over_old.json`、`gold.json`
- `data/exp/x1/` 下语料与 `questions.json`（改字节会作废指纹）
- `RRF_K`、`NEURAL_RERANK_K`、`fastembed==0.8.1`、本地 embedding / rerank 模型名

每张碰产品行为的票，合并前重放：

`python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md`

期望：退出码 0；G1/A1/T1/R1 的 `value=` 与诊断 §3 的 token 一致；段行仍是 `status=TBD`、`counted_as_pass=false`。重放绿只证明地板没漂。夹具绿才证明本票的产品行为。

不发明 SESOI，不写新的绝对通过率，不把 `counted_as_pass` 改成 true，不把 `status` 改成 pass。

新术语（`tool_tier_*`、reason code）在该票实现时写入 `CONTEXT.md`。本规划 PR 不改词表。

A 层 RAG 的 grade 用确定性夹具，不引入 LLM judge，不在 224 题上调阈值。learned grader、句子级 span、冲突码 `conflicting_evidence`、数字闸，都不是 A 层完成条件。

## 3. 里程碑

| 里程碑 | 完成条件 | 对外能说的话 |
|---|---|---|
| M1 拒答边 | L4-RAG-01、L4-RAG-02、L4-RAG-04 | 检索边能在夹具上拒，hit 上有可测分。还不是 L4 |
| M2 版本过滤 | L4-RAG-03，外加 L4-EV-T1-CASE 已落地 | 错 `patch_id` 在夹具上被滤掉。注册 T1 地板不动。还不是 L4 |
| M3 线上引用检查 | L4-FC-CITE、L4-EV-02 | claim 的 id 必须落在本轮 registry，CI 用夹具失败。注册 A1 不动。还不是 L4 |
| M4 调用与权限 | L4-FC-01、L4-FC-02、L4-FC-03 | Function Call 轴到 L4 门槛。木桶仍看 RAG 与 Agent |
| M5 短环 | L4-AG-01、L4-AG-02、L4-AG-03 | Agent 轴到 L4 门槛。主链木桶可以是 L4，若 UI 与臂表未做完则先不对外宣称 A 层完成 |
| M6 审计面 | L4-UI-01、L4-UI-02 | 面板绑定真实 reason 与分数。职人视图仍不泄角色名 |
| M7 臂表 | L4-EV-01 | 同 pin、同 gold 的 Recall@k / MRR 分列表可重复跑，表上没有新的通过线 |
| M8 A 层完成 | M1–M7，且 Skill 旁路三票落地 | 可回归的拒答产品。Skill 标 L3。不标 L5。不把注册 A1/G1/T1 的 `value=` 说成产品率 |

Skill 旁路未完成时，主链可以走到 M7，对外仍写 Skill L2，不宣称 A 层完成。

B 层（数字闸、冲突拒答、句子归因、可见时序夹具、`disputed`）在 M8 之后另开，不插入本页票序。C 层不在本页。

## 4. 依赖

```text
L4-RAG-01 ── L4-RAG-02 ── L4-AG-01 ── L4-AG-02 ── L4-AG-03 ── L4-UI-01 ── L4-UI-02
    │              │
    │              └── L4-RAG-04（可与 RAG-02 串行；都改 retrieve 观察）
    │
    ├── L4-RAG-03 ── L4-EV-T1-CASE（CASE 也可紧随诊断先落地，不挡 RAG-01）
    │
    └── L4-FC-CITE ── L4-EV-02
                         │
L4-FC-01 ── L4-FC-02     │
L4-FC-03（Gate，可与 FC-01 并行，必须在 M4）
                         │
                    L4-EV-01（M7；不生产新通过线）

旁路，不挡 M1：L4-SK-03 → L4-SK-01 → L4-SK-02
```

`L4-FC-CITE` 依赖 RAG-01 的 reason 词表已经有一个「证据不足」码，避免引用检查和拒答各说一套。它不依赖 FC-01 的自纠循环：cite-emit 挂在现有 `reverify_claim` / `mark_stale` 上。

`L4-FC-03` 若与 cite-emit 同周落地，cite-emit 不得新开一只绕过 `tool_tier` 的写工具。

## 5. 主链票

票格式对齐 `tasks/_template.md`：Goal、Acceptance、Paths、Provenance、Trust。实现时再抄到 `tasks/<ID>.md` 并走 enrich。本页不创建那些文件。

### 5.1 L4-RAG-01

- **ID**: L4-RAG-01
- **Title**: `feat(rag): retrieve 边 sufficiency 标签，不足则不发 fresh`
- **Goal**: 对应 A-RAG-01。检索观察带 sufficiency 标签。夹具中证据不足时，路径不产生 fresh。现有「无 `t1_evidence_ids` 不得 fresh」保留。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/roles/lead.py`（`_t_retrieve` 的返回）
  - `src/freshlatch/roles/loop.py` 或紧邻的纯函数（标签与是否继续写判定）
  - `src/freshlatch/gates/rule_gate.py`（只读其 fresh 条件，本票不放宽）
  - 新夹具测试于 `tests/unit/`
- **Acceptance**:
  1. Given 夹具 store 对查询返回零块，When 跑到判定出口，Then 结果不是 fresh，轨迹含 `sufficiency=insufficient` 与 reason code `insufficient_evidence`，且测试不调用付费 LLM。
  2. Given 夹具返回至少一条本轮 `@T1` 块且原规则闸会放行的最小输入，When 跑同一出口，Then 本票不把该输入改成拒答。
  3. Given 上述 diff，When 检查 Do-not-touch 列表，Then 那些路径无改动。
  4. Given 离线质量闸命令，When 重放，Then 退出码 0，且诊断 §3 的 G1/A1/T1/R1 `value=` token 仍在 stdout。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/roles/lead.py#_t_retrieve`；`src/freshlatch/gates/rule_gate.py` 的无 T1 不得 fresh；清单 A-RAG-01；前沿索引里 Sufficient Context 的「标签 → 选择性拒答」，只摘标签，不迁仓库
  - What changed: 拒答前移到检索观察，规则闸仍在
  - Why not copy as-is: 论文实现带分类器与网页回退。本票用空命中夹具，不训练、不联网
- **Do-not-touch**: 第 2 节全文；不得在 224 题上拟合阈值

### 5.2 L4-RAG-02

- **ID**: L4-RAG-02
- **Title**: `feat(rag): retrieve 边 CRAG 三态，Agent 只消费 grade`
- **Goal**: 对应 A-RAG-02。Correct / Incorrect / Ambiguous 出现在检索边上。Incorrect 或 Ambiguous 走再检索一次或拒答。没有网络回退。Agent 循环不另写一套 grade。
- **Trust**: Watch
- **Paths**:
  - RAG-01 落下的检索观察
  - `src/freshlatch/roles/loop.py`
  - `tests/unit/` 夹具
- **Acceptance**:
  1. Given 夹具把检索标成 Incorrect，When 跑短路径，Then 要么再检索一次后仍失败并拒答，要么直接拒答；reason 可枚举；不出现 `web_search`。
  2. Given 夹具标成 Correct 且规则闸条件满足，When 跑同一路径，Then 本票不强制拒答。
  3. Given Ambiguous 夹具，When 跑完，Then 轨迹含 `grade=ambiguous`，且不把该状态写成 fresh。
  4. 质量闸重放与 Do-not-touch 同 RAG-01 的第 3、4 条。
- **Provenance**:
  - Kind: adapt
  - Source: 清单 A-RAG-02；前沿索引 CRAG 三态。挂点按评估 §2.4 固定在 retrieve
  - Why not copy as-is: 上游 CRAG 含网络检索回退。本仓 `web_search` 保持未挂载
- **依赖**: L4-RAG-01
- **边界**: 本票的 Ambiguous 是「这份观察不够支持继续写判定」。两条 T1 互相矛盾的 `conflicting_evidence` 属于 B-02，不在本票勾选。

### 5.3 L4-RAG-04

- **ID**: L4-RAG-04
- **Title**: `feat(rag): hit 可测分与 rerank 开关记录`
- **Goal**: 对应 A-RAG-04。每个 hit 带可测分；小夹具上的 manifest 能分出 rerank ON 与 OFF。显式切到 BM25 的运维开关不得记成 `bm25_fallback`。不重跑 224 题，不替换冻结基线。
- **Trust**: Auto
- **Paths**:
  - `src/freshlatch/roles/lead.py#_t_retrieve`
  - `src/freshlatch/store/pipeline.py`、`neural_rerank.py`（只读现有分，不改融合公式）
  - `src/freshlatch/runner.py` 的运维开关注释所对应的写入点
  - `tests/unit/test_store.py` 一类既有检索测试
- **Acceptance**:
  1. Given 一次 hybrid+rerank 检索夹具，When 读工具观察，Then 每个 hit 含可区分的分字段，且 `retrieval_mode` 仍不能由模型参数改写（传入则返回现有错误「生产路径不可指定 retrieval_mode」）。
  2. Given 同一小夹具分别走神经精排与词面精排，When 读两次 manifest，Then 能看出 rerank ON 与 OFF，且两次都不改 `PRODUCTION_RETRIEVAL_MODE`。本票不重跑 224 题，不替换 `neural-rerank/summary.json`。
  3. Given 运维开关切到 `bm25`，When 读 `last_retrieval_mode`，Then 值不是 `bm25_fallback`。`bm25_fallback` 仍只表示缺可用向量。
  4. 质量闸重放 token 不变。
- **Provenance**:
  - Kind: adapt
  - Source: `LeadReverifier._t_retrieve` 现返回 `blocks` 与 `retrieval_used`；轨迹事件已有 `retrieval_mode` / `rerank_mode`；清单 A-RAG-04
  - Why not copy as-is: 工具观察和轨迹字段今天不一致。本票把已有臂信息补进观察，不新做精排器
- **依赖**: 与 L4-RAG-02 串行，避免同时改同一返回字典。推荐在 RAG-02 之后。

### 5.4 L4-EV-T1-CASE

- **ID**: L4-EV-T1-CASE
- **Title**: `test(quality-gate): 冻结名次上的 T1 个案锁`
- **Goal**: 把诊断里的 c1 / c2 / c3 / trap 写成只读断言，防止以后用改金标或改冻结名次来「修好」注册 T1 而不留记录。不新增通过线，不改退出码语义。
- **Trust**: Auto
- **Paths**:
  - `tests/unit/test_quality_gate.py`（或紧邻的新测试文件）
  - 只读 `docs/evidence/neural-rerank/per-query.json`、`data/eval/temporal_new_over_old.json`
- **Acceptance**:
  1. Given 冻结 `k10.neural_ranked`，When 测试读 `s6-d1-c1-q1`，Then `in_force` 的下标小于 `superseded`。
  2. Given 同一文件，When 读 `s6-d1-c2-q1`，Then `superseded` 的下标小于 `in_force`。
  3. Given 同一文件，When 读 `s6-d1-c3-q1`，Then `in_force` 与 `superseded` 都不在列表中。
  4. Given `tno-trap-supersede-1`，When 在 per-query 的 id 集合里查找，Then 不存在，与 `unresolved` 一致。
  5. Given 质量闸源码 diff，When 检索，Then 本票没有把 conflict-pair 或 T1 设成 `counted_as_pass=true`，没有新的百分数地板。
- **Provenance**:
  - Kind: adapt
  - Source: `freshlatch.eval.retrieve_typed.conflict_pair_correct`；诊断 §4.3
  - Why not copy as-is: 质量闸只打印聚合 `value=`。个案锁把两种失败分开，聚合地板仍然只描述、不判产品通过
- **依赖**: 无。可与 L4-RAG-01 并行。不挡 M1。M2 宣称前应已合并，否则版本过滤容易被说成「T1 已通过」。

### 5.5 L4-RAG-03

- **ID**: L4-RAG-03
- **Title**: `feat(rag): patch 与有效期过滤先于 RRF`
- **Goal**: 对应 A-RAG-03。`Chunk` 增加可选 `patch_id`、`valid_from`、`valid_to`。过滤发生在 RRF 之前或并入融合的候选池之前。字段为空则本过滤器是空操作，现有语料的候选池不变。不复用 `doc_version`。不改 `as_of` 的 T0/T1 WHERE。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/store/base.py` 的 `Chunk`（不改 `PRODUCTION_RETRIEVAL_MODE` 那一行）
  - `src/freshlatch/store/pipeline.py`、`sqlite_store.py` 的候选池
  - 独立夹具语料（放在测试树，不放进 `data/exp/x1/`）
  - `tests/unit/`
- **Acceptance**:
  1. Given 夹具中同一主张有 `patch_id=p1` 与 `patch_id=p2`，查询指定 `p2`，When 检索，Then `p1` 不在候选池。
  2. Given 块的三个新字段皆空，When 对一份与现有单测相同的小库检索，Then 候选 id 序列与本票之前一致。
  3. Given `git diff -- data/exp/x1 docs/evidence/neural-rerank docs/evidence/quality-gate/PREREG.md`，When 检查，Then 无改动。
  4. 质量闸重放 token 不变。
  5. 测试名或断言里不出现「注册 T1 上升」或新的通过率。
- **Provenance**:
  - Kind: adapt
  - Source: `Chunk` 现有列；清单 A-RAG-03；前沿索引 MRAG 的无训练元数据过滤。只摘「先滤再融合」
  - Why not copy as-is: MRAG 的语义分×时间分可以以后做。本票只做元数据过滤。训练型时序臂是 C-01，不做
- **依赖**: 无硬依赖。推荐在 L4-EV-T1-CASE 之后，以免把夹具过滤叙述成 c2/c3 已修复。c2/c3 都是 `@T1` 对 `@T1`，本票不修改那两题的语料。

### 5.6 L4-FC-CITE

- **ID**: L4-FC-CITE
- **Title**: `feat(tools): claim 引用必须落在本轮 evidence registry`
- **Goal**: 线上引用构念的发射侧。`reverify_claim` 与 `mark_stale` 已通过 `check_evidence_ids` 限制为本轮见过的 id。本票把这个集合显式定为 turn-scoped registry，并在轨迹里记下判定所用 id。不新增绕过权限的写工具。不读取 `cite_sentence.json` 来打分。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/evidence.py`（`check_evidence_ids`）
  - `src/freshlatch/roles/lead.py`
  - 轨迹写入（`Runner._dump_trajectory` 所消费的事件）
  - `tests/unit/`
- **Acceptance**:
  1. Given 本轮 retrieve 返回集合 S，When `reverify_claim` 或 `mark_stale` 传入 S 之外的 id，Then 该 call 被拒绝，reason 可枚举，不产生 fresh。
  2. Given 传入的 id 都在 S 中且为 `@T1`，When 其余闸条件满足，Then 本票不额外拒绝。
  3. Given 一次成功判定，When 读轨迹事件，Then 能看到所用 evidence id 列表。
  4. Given diff，When 检索 `score_citation_overlap` 与 `cite_sentence.json`，Then 本票不修改它们，也不把注册 A1 的地板写入新断言。
- **Provenance**:
  - Kind: adapt
  - Source: `check_evidence_ids`；`LeadReverifier._seen_evidence`；清单 A-EV-02 的 registry 半边；诊断 §4.2
  - Why not copy as-is: 现有检查已能拒陌生 id。缺的是轨迹上的 registry 记录，以及与金标 C∩R 脱钩的测试名
- **依赖**: L4-RAG-01 的 `insufficient_evidence` 已存在，本票的拒因使用另一枚 code（工作名 `cite_outside_registry`），实现时写入 `CONTEXT.md`。

### 5.7 L4-EV-02

- **ID**: L4-EV-02
- **Title**: `test(eval): citation registry 夹具进 CI`
- **Goal**: 对应 A-EV-02。claim 的 id 对不齐本轮 registry 时 CI 失败。检查器是确定性集合比较，零 LLM，因此可以进现有 `pytest`，不违反 ADR-0005 对金标 LLM runner 的排除。
- **Trust**: Watch
- **Paths**:
  - `tests/unit/` 或 `tests/eval/` 中不调用 LLM 的文件
  - `.github/workflows/ci.yml`（仅当现有 `pytest tests/` 还没覆盖该路径时追加路径；不新增 LLM job）
- **Acceptance**:
  1. Given 一条夹具主张引用了 registry 外的 id，When `pytest` 跑该测试，Then 失败。
  2. Given 引用集合是 registry 的子集，When 跑同一测试，Then 通过。
  3. Given CI 工作流 diff，When 阅读，Then 没有 `freshlatch.eval run`，没有付费密钥，没有质量闸 `status=pass`。
- **Provenance**:
  - Kind: adapt
  - Source: ADR-0005；清单 A-EV-02；L4-FC-CITE 的 registry
  - Why not copy as-is: DeepEval / Trust-Align 的 LLM judge 不进这条 CI
- **依赖**: L4-FC-CITE

### 5.8 L4-FC-01

- **ID**: L4-FC-01
- **Title**: `feat(tools): 非法调用 typed reason、有限自纠、耗尽 fail-closed`
- **Goal**: 对应 A-FC-01。非法 args 变成 typed reason 回给模型，自纠次数有上限，耗尽后 fail-closed 并留下轨迹。`UnknownToolGuard` 不再以未分类异常拆掉循环作为唯一形态。`mark_stale` 非法 dimension 的拒绝保留。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/roles/loop.py`（`UnknownToolGuard`、`run_loop`）
  - `src/freshlatch/tools.py`
  - `src/freshlatch/roles/lead.py` 中已有的参数错误返回
  - `tests/unit/`
- **Acceptance**:
  1. Given 模型发出白名单外工具名，When 循环处理该步，Then 轨迹含 reason code，循环按有限次数再试，耗尽后运行以失败结束而不是无记录地抛出。
  2. Given `mark_stale` 的非法 dimension，When 调用，Then 仍然整 call 拒绝，且既有 `test_lead_mark_stale_illegal_dimension_rejected` 保持绿色。
  3. Given 合法 `retrieve`，When 调用，Then 行为与本票之前一致（查询串仍由 `transform_claim_query` 产出，模型传入的 query 仍被忽略）。
- **Provenance**:
  - Kind: adapt
  - Source: `UnknownToolGuard`；`tool_specs`；清单 A-FC-01
  - Why not copy as-is: 上游中间件假设 LangChain。本仓留在 `run_loop`
- **依赖**: 无。排在 cite-emit 之后，避免第一刀花在目录卫生上。

### 5.9 L4-FC-02

- **ID**: L4-FC-02
- **Title**: `feat(llm): tools strict，或不支持则书面声明仅运行时再验`
- **Goal**: 对应 A-FC-02。若当前 `LLMClient.chat` 所打的端点接受 `strict`，则传 `strict` 且保留 `additionalProperties: false`。业务语义（dimension、evidence id、as_of）仍由 L4-FC-01 再验。若端点不接受，本票只加一份开发者可见的声明和一条测试，证明请求里没有假装已经 strict。两种结局都可以勾完本票，勾的是「探测有结论」。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/llm.py` 的 `chat`
  - 声明放在与工具调用同一模块的 docstring，或 `docs/evidence/` 下一页短说明（实现时二选一，不两处矛盾）
  - `tests/unit/`
- **Acceptance**:
  1. Given 测试里的假端点接受 `strict`，When 构造请求，Then payload 含该字段。
  2. Given 假端点拒绝该字段，When 走声明分支，Then 业务再验测试仍覆盖非法 dimension，且代码注释写明仅运行时再验。
  3. 本票不把任一端点的探测结果写成召回率或通过率。
- **Provenance**:
  - Kind: adapt
  - Source: `LLMClient.chat` 今天只传 `tools`；清单 A-FC-02；缺口清单歧义 §6
- **依赖**: L4-FC-01

### 5.10 L4-FC-03

- **ID**: L4-FC-03
- **Title**: `feat(tools): tool_tier 读、需批、禁`
- **Goal**: 对应 A-FC-03。三档：`tool_tier_0` 读检索，`tool_tier_1` 写观测且需批，`tool_tier_2` 生产臂禁止。禁止在代码和文档里裸写「L0」表示这三档。HumanLatch 的人审出口保持原词。
- **Trust**: Gate
- **Blast**: auth
- **Paths**:
  - `src/freshlatch/tools.py`
  - 审批挂点：现有人审路径（`latch/`），不新造第二套审批产品
  - `tests/unit/` 每档至少一测
  - `CONTEXT.md` 增加 `tool_tier_0|1|2`，并写明与人审 L0 不同
- **Acceptance**:
  1. Given `retrieve` / `read_source`，When 无审批调用，Then 成功返回（夹具）。
  2. Given 被标成 `tool_tier_1` 的写观测工具，When 无批调用，Then 拒绝并留 reason。
  3. Given `tool_tier_2` 夹具工具，When 模型调用，Then fail-closed，且该工具不在默认 `LEAD_TOOLS_W3`。
  4. Given diff，When 检索新增标识符，Then 权限档名字是 `tool_tier_*`。`gates/rule_gate.py` 文首的人审 L0 语义无改写。
  5. `LEAD_TOOLS_W9` 仍然不是 Runner 默认挂载。`web_search` 仍然不在任何白名单。
- **Provenance**:
  - Kind: adapt
  - Source: `LEAD_TOOLS_W3`；清单 A-FC-03；缺口清单歧义 §1；前沿索引的 needsApproval 只摘「读 / 需批 / 禁」
  - Why not copy as-is: OpenAI Agents SDK 与 OpenHands 的审批运行时不引入
- **依赖**: 无硬依赖。必须在宣称 M4 之前合并。若晚于 L4-FC-CITE，须确认 cite 路径没有新的无档写工具。

### 5.11 L4-AG-01

- **ID**: L4-AG-01
- **Title**: `feat(agent): verify 后 repair 或 abstain`
- **Goal**: 对应 A-AG-01。在现有 `run_loop` 上增加短环。state 含 `evidence_ids`、`grade`、`retry_count`。grade 只读 RAG-02 的边。不 import langgraph 进 `roles/loop.py`。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/roles/loop.py`
  - `src/freshlatch/runner.py` 的轨迹字段
  - `tests/unit/`
- **Acceptance**:
  1. Given grade=Incorrect 且 retry 未耗尽，When 跑循环，Then 发生有限 repair（再检索或改判定草稿），`retry_count` 增加。
  2. Given retry 耗尽或 grade 仍不足，When 结束，Then abstain，不写 fresh。
  3. Given `roles/loop.py` 的 import，When 检查，Then 没有 langgraph。
- **Provenance**:
  - Kind: adapt
  - Source: `run_loop`；ADR-0004；清单 A-AG-01
  - Why not copy as-is: Self-RAG / LangGraph-RAG 的图运行时不进入 Agent 层。人审 checkpoint 仍留在 `latch/pipeline.py`
- **依赖**: L4-RAG-02

### 5.12 L4-AG-02

- **ID**: L4-AG-02
- **Title**: `feat(agent): 命名 abstention reason 进轨迹`
- **Goal**: 对应 A-AG-02。拒答原因是枚举，写入轨迹。至少包括 RAG-01 的 `insufficient_evidence` 与 FC-CITE 的 `cite_outside_registry`。UI 票以后只读这份枚举。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/roles/loop.py` 与轨迹 dump
  - `CONTEXT.md` 词表
  - `tests/unit/`
- **Acceptance**:
  1. Given 一条 abstain 夹具，When 读 JSONL，Then reason code 属于已写明的枚举，且不是自由文本独有。
  2. Given 枚举定义，When 对照 RAG-01 与 FC-CITE 的测试，Then 两边用同一符号。
- **Provenance**:
  - Kind: adapt
  - Source: 清单 A-AG-02；前沿索引 citation-abstention 的 reason code 只摘「命名码进轨迹」
- **依赖**: L4-AG-01、L4-RAG-01、L4-FC-CITE

### 5.13 L4-AG-03

- **ID**: L4-AG-03
- **Title**: `feat(agent): 失败轨迹可复放`
- **Goal**: 对应 A-AG-03。失败运行的 JSONL 含工具步、grade、reason、retry。人审侧继续用现有 latch checkpoint。不把 LangGraph time-travel 引进 `run_loop`。本票不加人审动词 `disputed`（那是 B-05）。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/runner.py` 的 `_dump_trajectory`
  - 测试夹具读取 JSONL
- **Acceptance**:
  1. Given 一次夹具失败（检索空或 grade 不足），When 从 JSONL 重放解析，Then 能读回 `evidence_ids`、`grade`、`retry_count`、reason code。
  2. Given `latch/pipeline.py`，When diff，Then 人审图的职责不变。
- **Provenance**:
  - Kind: adapt
  - Source: 现有 JSONL 与 latch checkpoint；清单 A-AG-03；缺口清单歧义 §2
  - Why not copy as-is: Causal Agent Replay 只可作排障参考，不进默认复验
- **依赖**: L4-AG-02

### 5.14 L4-UI-01

- **ID**: L4-UI-01
- **Title**: `feat(ui): 审计面 Query、Hits、Attribution、Unknown`
- **Goal**: 对应 A-UI-01。审计视图解析轨迹，展示查询、带分的 hits、判定所用 evidence id、Unknown 态的 reason code。职人视图仍不展示角色名。Override 沿用现有人审动词 `discard` / `renew`，本票不新增动词。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/ui/static/reverify.html`
  - `src/freshlatch/ui/app.py` 中给页面的数据
  - `tests/unit/test_ui_*.py`
- **Acceptance**:
  1. Given 一条含 hit 分与 reason code 的轨迹夹具，When TestClient 取审计视图，Then HTML 含该分数与该 code。
  2. Given 职人视图，When 读 HTML，Then 不含 Lead / Critic / Auditor 角色名（保持现有去角色化测试的方向）。
  3. Given 轨迹只有文件路径、没有解析字段，When 渲染，Then 不显示假的分数。
- **Provenance**:
  - Kind: adapt
  - Source: `reverify.html` 今天把轨迹渲染成路径；清单 A-UI-01
  - Why not copy as-is: 不引入 Streamlit，不照搬闭源产品的来源条
- **依赖**: L4-RAG-04、L4-AG-02

### 5.15 L4-UI-02

- **ID**: L4-UI-02
- **Title**: `feat(ui): verified、partial、abstain 徽章绑定真闸`
- **Goal**: 对应 A-UI-02。三枚徽章分别对应：闸允许的 fresh、证据不全但仍有本轮 id 的 partial、abstain。没有对应状态时不渲染徽章。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/ui/static/reverify.html`
  - `tests/unit/`
- **Acceptance**:
  1. Given 轨迹 reason 为 `insufficient_evidence`，When 渲染，Then 出现 abstain 徽章且不出现 verified。
  2. Given 无 grade、无 reason 的旧轨迹，When 渲染，Then 不出现这三枚徽章。
- **Provenance**:
  - Kind: adapt
  - Source: 清单 A-UI-02；L4-AG-02 的枚举
- **依赖**: L4-UI-01

### 5.16 L4-EV-01

- **ID**: L4-EV-01
- **Title**: `test(eval): Recall@k 与 MRR 分列表可重复跑`
- **Goal**: 对应 A-EV-01。同代码 pin、同 gold、分臂列出 Recall@k 与 MRR。输出落在证据目录或 CI artifact。表上不写新的通过线。不把历史 `neural-rerank/summary.json` 重算进这张表来替换冻结基线。
- **Trust**: Watch
- **Paths**:
  - `src/freshlatch/eval/retrieve_eval.py` 与 `retrieve_typed.py`（已有函数，本票只固定入口与输出）
  - 测试断言「命令可跑且写出列」，不断言新的均值门槛
  - CI：若进 GitHub Actions，用与 ADR-0005 相容的方式（零 LLM）。若需要本地模型权重且 CI 没有，则命令留在手动 milestone，测试只锁输出 schema，并在票上写明未进 CI 的原因
- **Acceptance**:
  1. Given 固定小夹具（不是 224 题全量，除非运行环境已有冻结权重且命令声明为手动），When 跑入口，Then 得到含臂名、Recall@k、MRR 的表。
  2. Given 该表，When 阅读，Then 没有「通过 / 失败」门槛数字。
  3. Given diff，When 检查冻结基线文件的 sha，Then 与 `PREREG` 所载一致。
- **Provenance**:
  - Kind: adapt
  - Source: 仓内 `recall_at_k` / `mrr_at_k`；清单 A-EV-01；缺口清单歧义 §5
  - Why not copy as-is: 函数已经存在。缺的是可重复的同 pin 输出，不是从零写指标
- **依赖**: L4-RAG-04 的字段稳定之后再做臂表，避免表头跟着观察格式变两次。

### 5.17 L4-EV-03（可选，不挡 M8）

- **ID**: L4-EV-03
- **Title**: `feat(eval): 轨迹目录聚合 e2e P95 与 fallback rate`
- **Goal**: 对应 A-EV-03。纯函数读轨迹目录，产出与 `docs/ops/延迟与检索回退周报.md` 同一列名的一行。显式 BM25 开关不计入 `bm25_fallback`。样本不足时输出占位，不填比率。不把该行写回 `RESULT-Y`。
- **Trust**: Auto
- **Paths**:
  - 新纯函数于 `src/freshlatch/eval/`
  - `tests/unit/`
- **Acceptance**:
  1. Given 含检索事件的夹具目录，When 聚合，Then 输出含 P95 与 fallback 计数字段。
  2. Given 事件的模式是运维开关 `bm25`，When 聚合，Then 不把它算进 `bm25_fallback`。
  3. Given 空目录，When 聚合，Then 占位，不出现编造的比率。
- **Provenance**:
  - Kind: adapt
  - Source: `docs/ops/延迟与检索回退周报.md`；清单 A-EV-03
- **与 L4 的关系**: 评估写的是「SLI 或 ablation」。L4-RAG-04 的 rerank 开关记录满足 ablation 这一腿。本票不做，M8 仍可宣称，只要 RAG-04 已合并。

## 6. Skill 旁路

不挡 M1。M8 需要三票都落地，否则 Skill 保持 L2，不宣称 A 层完成。

### 6.1 L4-SK-03

- **ID**: L4-SK-03
- **Title**: `fix(skills): references 真能读到，或删掉 frontmatter 承诺`
- **Goal**: 对应 A-SK-03。`skills/reverify/SKILL.md` 若仍写 references 由 `read_source` 按需读取，则要么提供只读技能引用的工具并列入相应白名单，要么改掉这句话。`load_skill_body` 今天只读 `SKILL.md` 的行为保持可测。
- **Trust**: Auto
- **Paths**:
  - `skills/reverify/SKILL.md`
  - `src/freshlatch/skills_loader.py`（若选真加载）
  - `tests/unit/test_skills.py`
- **Acceptance**:
  1. Given 现行 frontmatter，When 读它与加载器，Then 二者对 references 的承诺一致：要么测试能读到一个 reference 文件，要么文案不再声称 `read_source` 能打开 `skills/*/references/`。
  2. Given `test_skills.py` 的白名单断言，When 跑，Then 技能文案里的工具名仍是白名单子集。
- **Provenance**:
  - Kind: adapt
  - Source: `load_skill_body`；清单 A-SK-03
- **依赖**: 无

### 6.2 L4-SK-01

- **ID**: L4-SK-01
- **Title**: `feat(agents): Guards hook 样板 failClosed`
- **Goal**: 对应 A-SK-01。在 Agent Guards 文档旁边提供一个样板：退出码 2 表示 deny，且 `failClosed: true`。样板默认不启用，不替换 `run_loop` 的工具白名单。
- **Trust**: Watch
- **Paths**:
  - `docs/agents/agent-guards.md`
  - 样板 hook 文件（实现时按 Cursor hooks 的现用文件名，放在文档所指的可选路径）
  - 测试或脚本断言样板含 `failClosed` 与 exit 2 的说明
- **Acceptance**:
  1. Given 样板被显式启用且脚本返回 exit 2，When 按文档演练，Then 动作被拒绝。
  2. Given 默认配置，When 查仓库，Then 没有把该 hook 打开成全员默认，从而打断现有开发环。
  3. Given `src/freshlatch/roles/loop.py`，When diff，Then 本票不改循环。
- **Provenance**:
  - Kind: adapt
  - Source: `docs/agents/agent-guards.md` 现写 Hooks 为可选；清单 A-SK-01
- **依赖**: 无。推荐在 SK-03 之后，以免技能文档两处同时改。

### 6.3 L4-SK-02

- **ID**: L4-SK-02
- **Title**: `feat(skills): 3 到 5 个中文业务 skill 包`
- **Goal**: 对应 A-SK-02。新增财报、事件、patch diff、策略 walkthrough 中的 3–5 个目录，每个有 `SKILL.md`，可选 `scripts/`。默认 Runner 注入列表保持现状，除非另有主人点名的后续票。本票不把这些包挂进 Lead 系统提示。
- **Trust**: Auto（不挂进 Runner）。若实现时改了默认注入，Trust 升为 Watch 并停下等主人。
- **Paths**:
  - `skills/<name>/SKILL.md`
  - `tests/unit/test_skills.py`
- **Acceptance**:
  1. Given 新目录，When 跑技能测试，Then 每个包的工具名 ⊆ 白名单，正文为 UTF-8 中文，frontmatter 不承诺不存在的读取器。
  2. Given `Runner` 的默认教义列表，When diff，Then 与本票之前相同。
- **Provenance**:
  - Kind: new
  - Source: 清单 A-SK-02；前沿索引的 `SKILL.md` + progressive disclosure。只学形状，不复制 FinRobot 正文
- **依赖**: L4-SK-03

## 7. Trust 一览

| 票 | Trust | 原因 |
|---|---|---|
| L4-FC-03 | Gate | 权限分层，Blast=auth。主人合并前不算完成 |
| L4-RAG-01、02、03 | Watch | 改变何时拒答、候选池如何滤 |
| L4-FC-CITE、L4-FC-01、L4-FC-02 | Watch | 改变工具失败形态与引用约束 |
| L4-EV-02、L4-EV-01 | Watch | CI 与臂表容易被写成新通过线 |
| L4-AG-01、02、03 | Watch | 循环控制流 |
| L4-UI-01、02 | Watch | 用户可见，且必须绑真字段 |
| L4-SK-01 | Watch | hook 一旦默认开启会打断开发环 |
| L4-RAG-04、L4-EV-T1-CASE、L4-EV-03、L4-SK-03、L4-SK-02 | Auto | 加字段、只读锁、纯函数、或未挂进运行时的技能文件 |

任何一票若要改第 2 节的 Do-not-touch，Trust 升为 Gate，并先停。那一类改动不在本计划里。

## 8. 保持 report-only

下列各项继续只描述、不判产品通过：

- 注册 G1 / A1 / T1 / R1 的 `status=TBD` 与 `counted_as_pass=false`。无回归旗标只表示相对地板 token 没变坏。
- guardrail 0-hit、conflict-pair ordering、multi-hop 全命中。
- `trap-smoke`（`level=smoke`，不进分母）。
- 路线 Y 的结果丙，以及 T−B1 / T−B2。
- L4-EV-T1-CASE 的个案断言。它锁冻结文件的形状，不锁一个新的准确率门槛。
- L4-EV-01 的分列表。
- L4-EV-03 在样本不足时的占位。
- 线上引用检查的 CI 结果。它是夹具红绿，不是注册 A1 的新地板。若将来要把线上引用登记成新段，另写预注册，本页地板不动。那次登记满足「难反转、反直觉、事后改判据会毁掉止损意义」时再写 ADR。本计划不写该 ADR。

## 9. 明确不做

- 不换向量库，不装 REA，不把 LangGraph 引进 `run_loop`，不默认挂 `LEAD_TOOLS_W9`，不接 `web_search`。
- 不改 `PRODUCTION_RETRIEVAL_MODE`，不重写 hybrid → RRF(k=60) → rerank top-10 这条生产臂。
- 不发明 SESOI，不把冻结点估计改写成别的百分数，不把 `lead_delta=0.10` 或 p95 800 ms 写成产品线。
- 不第二次正式主跑路线 Y，不把 B-04 夹具写成乙，不称优于 RARR 或 KPR。
- 不改 x1 语料、题集、三份注册金标、冻结 per-query，以此抬注册分。
- 不把 c2/c3 的修复验收写成注册 T1 的 `value=` 上升。
- 不在 A 层做 B-01 数字闸。若 M8 之后开 B-01，先在那张票里钉死读法；清单歧义 §3 的默认摘法是 verbatim 对账，公式重算另票。未钉死不得开工。
- 不在 A 层做 B-02 冲突码、B-03 句子级归因、B-05 `disputed`。A-RAG-03 完成也不等于 B-04 的可见夹具。A-AG-03 完成也不等于 B-05。
- 不做 C-01 训练型时序检索，不写「已复现 TempRetriever」。不做 C-02 在线 claim 监控、C-03 多租户产品、C-04 新预注册冲乙。
- 不派 Ronin，不在本页把清单勾成 `[x]`。

## 10. 建议的实现顺序

主人审过本页之后，按这个顺序各开一个实现会话：

1. L4-RAG-01
2. L4-RAG-02
3. L4-RAG-04
4. L4-EV-T1-CASE（可与 1 并行）
5. L4-RAG-03
6. L4-FC-CITE
7. L4-EV-02
8. L4-FC-01
9. L4-FC-02
10. L4-FC-03（Gate，主人看权限测试再合并）
11. L4-AG-01
12. L4-AG-02
13. L4-AG-03
14. L4-UI-01
15. L4-UI-02
16. L4-EV-01

旁路从 L4-SK-03 开始，任何时候都能插进，不替换上面的第 1 步。

M8 之前若只完成了 1–3，对外仍然是 L3：拒答边开始出现，权限分层、短环和审计面还没有。
