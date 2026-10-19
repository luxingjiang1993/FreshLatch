# FreshLatch L4 系统诊断（2026-10-14）

> 性质：只读诊断。不改生产代码，不改 `PRODUCTION_RETRIEVAL_MODE`，不改 `RESULT-Y`，不改 `PREREG` 地板 token，不发明 SESOI，不派 Ronin 执行。
> 代码基线：`main` @ `b2caaeffdc6ba56885087fcd5beddd560fb563b2`（`feat(quality-gate): QG-13 Track A 相对无回归地板与 segment_registered (#600)`）。
> 配套计划：[l4-full-build-plan-2026-10-14.md](l4-full-build-plan-2026-10-14.md)。
> 水平评估（2026-10-12，基线 `a7505d6`）：[module-level-assessment-2026-10-12.md](module-level-assessment-2026-10-12.md)。
> A 层清单：[module-level-gap-checklist-2026-10-12.md](module-level-gap-checklist-2026-10-12.md)。
> 前沿索引：[module-level-frontier-refs-ABC-2026-10-12.md](module-level-frontier-refs-ABC-2026-10-12.md)。
> 质量闸构念摘要：[grok-system-analysis-no-fc-2026-10-14.md](grok-system-analysis-no-fc-2026-10-14.md)。

本页把 10-12 的模块档位和 10-14 已落地的离线质量闸放在同一张桌上。产品向 L4 的定义沿用评估文档，不另造一档。

## 1. 结论

整体仍是 **L3**。主链（Function Call、RAG、AI Agent）还没有同时具备：可回归的拒答、可审计的证据字段、能重复跑的 ablation、以及工具权限分层。

10-14 的质量闸把这件事说得更具体：

- **R1 已经钉在高位。** 离线重放 Recall@10 与 MRR@10 对上神经 `k10` 右臂地板，`r1_no_regression=true`。这是冻结名次回放，不是本轮新检索。
- **注册 G1 是两份金标互相同意。** `source=gold-bucket-agreement`。它不测量模型拒答率。
- **注册 A1 是金标 `cited_ids` ∩ 来源题 `relevant`。** `source=cited-vs-relevant`。它不测量线上发射的引用。
- **注册 T1 是冻结名次上的 3 道有效题。** 其中 c1 现行条在前，c2 反序，c3 两条都不在前 10。`trap-supersede-1` 不在 224 行回放里，记 `unresolved`。R1 的 any-hit 在这三题上都是 1，所以 R1 高分看不见这三题的时序失败。
- **改检索栈、做 Function Call schema、做 Skill，都不会推动注册 A1 / G1 / T1。** 注册分读的是金标文件和 `docs/evidence/neural-rerank/per-query.json`。线上真引用要另建 cite-emit，并且不得把新数字写回这三行地板。

因此：组会票序「FC → Skill → RAG → Agent → UI」仍能把木桶送到 L4，但 **FC 整包不该排第一**。先做的是检索边上的拒答和版本过滤；Function Call 里先做 cite-emit 那一片；schema / `strict` / `tool_tier` 在木桶收口前完成，不作为开工第一刀。理由见计划正文。

对外口径保持评估文档那句：现在能讲的是「复验闸 + hybrid+rerank + 预注册负结果」。注册闸 exit 0 只能再加一句：「相对冻结点估计无回归，段状态仍是 TBD，`counted_as_pass=false`」。不能加「引用已达标」或「拒答率已满分」。

## 2. L4 在本仓里指什么

评估文档 §2.1：L4 是生产向团队产品，要可回归、可审计、有 SLI 或 ablation、权限分层落地。评估文档 §2.3 写明四件事同时在，缺一件停在 L3。

缺口清单的 A 层完成判据：主链木桶 L4，Skill 可为 L3，对外是可回归的拒答产品。只落地来源 A 或只落地来源 B，主链木桶仍是 L3。

本诊断把这个 L4 称为 on-call 拒答型 RAG / 团队门槛产品：值班时证据不够能拒、非法调用能拒、权限分层能测、审计面能指到真实字段。它不是 L5，也不是 B 层的数字闸、冲突码、句子级归因。

路线 Y 仍是结果丙。`docs/evidence/patch-events/RESULT-Y.md` 的成立格不成立。本诊断不复跑、不改尺、不把丙写成乙。

## 3. 10-14 质量闸实际印了什么

2026-10-14 在本基线上重放：

`python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md`

退出码 0。身份行：`owner_freeze=confirmed`，`fingerprints=match`，`arm=hybrid+rerank`，`paid_llm=false`。与 `docs/evidence/quality-gate/QG-GAT-FREEZE-RESULT.md` 的差别是：那一页是 #599 落档的第一次描述性冻结（当时段行 `status=unregistered`）；#600 之后段行变为 `status=TBD` 且 `registered=true`。两页都是 `counted_as_pass=false`。过线没有被记成通过。

| 段 | 重放要点 | 计分来源 |
|---|---|---|
| G1 | `value=1.0`，`n=12` `scored=12` `unresolved=0`，`g1_no_regression=true` | `gold-bucket-agreement` |
| A1 recall | `value=0.42857142857142855`，`n=7` `scored=7` `unresolved=0` | `cited-vs-relevant` |
| A1 precision | `value=0.6`，`n=7` `scored=5` `unresolved=2` | `cited-vs-relevant` |
| T1 | `value=0.3333333333333333`，`n=4` `scored=3` `correct=1` `unresolved=1`，`t1_no_regression=true` | `frozen-per-query-replay` |
| R1 Recall@10 | `value=0.9732142857142857`，`delta=0.0`，`r1_no_regression=true` | `frozen-per-query-replay` |
| R1 MRR@10 | `value=0.8381855867346939`，`delta=0.0`，`r1_no_regression=true` | `frozen-per-query-replay` |
| guardrail 0-hit | `value=unavailable`，`n=43` | 旁列，TBD |
| conflict-pair | `value=0.3333333333333333`，`correct=1` `n=3` | 旁列，TBD |
| multi-hop 全命中 | `value=0.7555555555555555`，`n=45` | 旁列，TBD |

这些 `value=` 是地板 token 的同一次点估计。`PREREG.md` §6 写明：这不是新 SESOI。本页引用 token 是为了和重放逐字对齐，不把它们升成产品合格线，也不另写绝对百分数。

R1 分母仍是 `data/exp/x1/questions.json` 的 arm 224 题。`meta.human_row_review=false`。人工审核覆盖 DECISION-16 的 16 题，不是 224 题逐行。命中定义是 top-10 里出现 `relevant` 中任一 id（`recall_at_k`），不是集合召回。

旁列三行（guardrail 0-hit、conflict-pair、multi-hop）失败不改退出码。不得用 conflict-pair 的 `n=3` 顶替 T1 地板，也不得用 multi-hop 全命中顶替 R1。

## 4. 注册构念和产品声称各算什么

### 4.1 G1：标签对桶，不是拒答率

`score_guard_should_accuracy` 比较 `data/eval/guard_should.json` 的 `label` 和 `data/eval/gold.json` 三档映射：`must_stale` / `must_unknown` → `should_refuse`，`must_fresh` → `should_pass`。`n_should_refuse=8`、`n_should_pass=4` 只是 label 计数，不除成率。

`value=1.0` 表示这 12 条手工标签和 `c1`–`c12` 的桶一致。CI 里的 `must_*` 机械闸是另一条不变量（ADR-0005，零 LLM）。规则闸「无 `t1_evidence_ids` 不得 fresh」也是另一条。三件事都真实，互不顶替。

产品声称「应该拒的主张会被拒」要测的是：给定主张，系统走出 `should_refuse` 的行为。注册 G1 不跑这段行为。

### 4.2 A1：金标 C ∩ R，不是线上引用

`score_citation_overlap` 的支撑集 R 是来源题的 `relevant`，引用集 C 是 `cite_sentence.json` 里手写的 `cited_ids`。

- recall = `sum(|C∩R|) / sum(|R|)`，只收入对上来源题且 `|R|>0` 的 keep 条。
- precision = `sum(|C∩R|) / sum(|C|)`，只收入 `|C|>0` 的 keep 条。空 `cited_ids` 不进 precision 分母。

本基线上 7 条 keep 的交集如下（R 来自 `questions.json`）：

| id | label（计分不读） | `|C∩R|` | `|R|` | `|C|` |
|---|---|---|---|---|
| `cs-p1-lx-03-supported` | supported | 1 | 1 | 1 |
| `cs-p1-lx-06-supported` | supported | 1 | 1 | 1 |
| `cs-s1-d0-01-q1-supported` | supported | 1 | 1 | 1 |
| `cs-p1-lx-04-false` | false_cite | 0 | 1 | 1 |
| `cs-s1-d0-01-q1-false` | false_cite | 0 | 1 | 1 |
| `cs-p1-lx-07-miss` | miss_cite | 0 | 1 | 0 |
| `cs-s1-d0-01-q3-miss` | miss_cite | 0 | 1 | 0 |

recall 的 3/7 与 precision 的 3/5 就是这两列之和。`label` 字段不进入函数。两条 `miss_cite` 用空 C 拉低 recall，同时退出 precision 分母，所以 precision 的 `unresolved=2` 是文件形状，不是模型漏引。

产品证据 id 走工具路径：`LeadReverifier._t_retrieve` 把本轮块放进 `_seen_evidence`，`reverify_claim` / `mark_stale` 经 `check_evidence_ids` 只能引用本轮见过的 id。这条路径真实存在。注册 A1 不读它，也不读轨迹。

缺口清单 A-EV-02 要的是另一构念：claim 对不齐 **turn-scoped evidence registry** 则 fail。那个构念今天没有金标段，也没有地板。把它的未来数字写进 `a1_citation_*_floor` 会触发 `PREREG` §8 的事后改判据，本计划禁止。

### 4.3 T1：冻结名次，不是活检索

`score_new_over_old_accuracy` 取 `source_refs` 第一题在 `docs/evidence/neural-rerank/per-query.json` 的 `k10.neural_ranked`，交给 `conflict_pair_correct`。该函数不读 `precedence`。没有冻结名次的条算 `unresolved`，函数不另跑检索。

`conflict_pair_correct`：现行条名次严格小于被取代条则真；被取代不在且现行在则真；两者都不在，或只有被取代条，则假。

| 条 | 冻结神经 k10 | 判定 | R1 any-hit |
|---|---|---|---|
| `tno-trap-supersede-1` | `trap-supersede-1` 不在 224 行里 | unresolved。金标注记写明它来自冒烟种子，不升成正式分母 | 不进本次 scored |
| `s6-d1-c1-q1` | `in_force` `p1-cac-o16#p9@T1` 第 1 位；`superseded` `p1-cac-o11#p13@T1` 第 3 位 | 真 | 1 |
| `s6-d1-c2-q1` | `superseded` `p1-cac-o11#p2@T1` 第 3 位；`in_force` `p1-cac-o16#p7@T1` 第 4 位。被取代条同时在该题 `relevant` 里 | 假，反序 | 1（第 1 位已是 relevant memo） |
| `s6-d1-c3-q1` | `in_force` `p1-cac-o16#p8@T1` 与 `superseded` `p1-cac-o13#p2@T1` 都不在前 10。第 1 位是 relevant memo `s6-d1-c3-memo#p1@T1`。题面 `precedence` `p1-cac-o16#p11@T1` 在第 3 位，计分不读它 | 假，双缺失 | 1 |

三对的 `in_force` 与 `superseded` 都带 `@T1`。现有 `as_of` WHERE 拆不开它们。c2 是同一 top-10 里的顺序问题。c3 是条款 id 没进 top-10，同族 memo 和 precedence 块进了。把 `NEURAL_RERANK_K` 从 10 加宽会碰到 `PREREG` §8 的精排宽度作废条件，本诊断不把它当修复。

注册 T1 的 `correct=1` 只来自 c1。c2 与 c3 是仅有的两个 scored 失败。样本就是这 3 条，外加 1 条 unresolved。这是冒烟量级的个案，不是带方差的时序实验。

旁列 `conflict-pair-ordering` 的 `correct=1` `n=3` 与这三题一致，因为 trap 条不在 arm 回放里。旁列没有地板。

### 4.4 R1 高，不蕴含 T1 或引用合格

三道 conflict 题的神经 Recall@10 与 MRR 都是 1。c2 的被取代条在 `relevant` 里，反序仍然 any-hit。c3 的 memo 在第 1 位，条款双缺失仍然 any-hit。保护 R1 地板是守住融合质量，不自动修正时序个案。

重放不执行 `SQLiteStore.retrieve`。改 `pipeline.py`、加元数据过滤、换精排实现，只要不替换 `neural-rerank/per-query.json` 和基线摘要，注册 R1 / T1 的 `value=` 保持不动。替换该文件属于新测量，不在本诊断的授权里。

## 5. 按模块：as-is 与 L4 缺口

10-12 评估的模块行为在本基线上复核过：`src/` 没有 `sufficient`、`CRAG`、`patch_id`、`failClosed`、`tool_tier`。`Chunk` 有 `doc_version`、`as_of`、`parent_id`，没有 `valid_from` / `valid_to`。生产默认仍是 `PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"`。`LEAD_TOOLS_W3` 仍是 Lead 白名单。`UnknownToolGuard` 仍在 `run_loop` 里抛异常并拆循环。`_t_retrieve` 返回的块字段是 `evidence_id`、`as_of`、`source_type`、`text`，另加 `retrieval_used` 计数；工具观察里没有 BM25 / dense / RRF / rerank 分。

下表的 L4 缺口沿用评估与 A 层清单。右列是 10-14 闸对这块缺口的约束：做了它，注册分会不会动。

| 模块 | as-is | L4 还缺 | 注册闸约束 |
|---|---|---|---|
| Function Call | L3 | 非法 args 的 typed reason、有限自纠、耗尽 fail-closed；端点 `strict` 或书面声明仅运行时再验；工具权限分层（读 / 需批 / 禁）。词表用 `tool_tier`，避开 HumanLatch 的 L0 | 整包不推动注册 A1/G1/T1/R1。cite-emit 只服务尚未注册的线上引用构念 |
| Skill | L2 | `failClosed` 样板；3–5 个中文业务 skill；references 真加载或改掉 frontmatter 承诺。A 层允许 Skill 停在 L3，不要求 L4 | 与四闸无关。不得阻塞拒答主链 |
| RAG | L3 | sufficient 标签与不足拒答；CRAG 三态挂在 retrieve 边，不另起网络回退；`patch_id` / 有效期过滤先于或并入 RRF；每 hit 可测分与 rerank 开关 ablation | 机制用夹具验收。不得改 x1 语料字节（指纹作废），不得替换冻结 per-query，不得把 c2/c3 的修复写成注册 T1 上升 |
| AI Agent | L3 | `verify → repair \| abstain`；命名 abstention reason；失败轨迹可复放。拒答点今天在 `rule_gate`，检索空结果仍把 `blocks` 交回模型 | 消费 RAG 的 grade。不把 LangGraph 引进 `run_loop` |
| UI | L3（观测轴 L2） | Query → Hits → Attribution → Unknown \| Override；徽章绑定真闸 | 只改讲解层则整体仍 L3（评估 §6） |
| Eval | L3 | 同 pin、同 gold 的 Recall@k / MRR 分列表可重复跑；turn-scoped citation 进 CI；SLI 5 聚合可选 | 注册四闸保持 report 身份：`status=TBD`，`counted_as_pass=false`。新构念另开预注册之前只有报告 |

`doc_version` 已在 `Chunk` 上。A-RAG-03 的 `patch_id` 不复用这个字段，避免一个字符串兼做校验版本和补丁身份。

## 6. Function Call 买得到什么

### 6.1 买得到

- **非法调用的失败形态。** 今天 `mark_stale` 的非法 `dimension` 会整 call 拒绝；白名单外名字在 `tool_specs` 层 `KeyError`；循环里的未知工具名由 `UnknownToolGuard` 抛出并拆掉循环。A-FC-01 把这些收成 typed reason、有限自纠、耗尽后 fail-closed。这是 L4 正确性轴，不产生新的 Recall 或引用率。
- **权限分层。** 评估把「权限分层落地」写成 L4 四条件之一。A-FC-03 用 `tool_tier_0` 读检索、`tool_tier_1` 写观测需批、`tool_tier_2` 禁动生产臂。这是木桶条件。它不测量 G1。
- **线上引用的发射约束，仅限 cite-emit 这一片。** 本轮见过的 evidence id 已经由 `check_evidence_ids` 限制 `reverify_claim` / `mark_stale`。缺的是：把「claim 的 id ⊆ 本轮 registry」做成与注册 A1 分开的检查，并在证据不足时先拒再写。句子级 span 是 B-03，不在这一片里。

### 6.2 买不到

- 注册 A1 的 C∩R。C 写在金标文件里。
- 注册 G1 的桶一致。两边都是手工标签。
- 注册 T1 与 R1。两者回放冻结名次。
- c2 反序、c3 双缺失。这是排序和条款召回。
- sufficient-context、CRAG 三态、patch 过滤。挂点在 retrieve 边。
- Skill `failClosed` 与 references。
- 审计面上的 Hits 分数。工具返回里还没有分。
- 把路线 Y 从丙改成乙。同尺禁止第二次正式主跑。

把 FC schema 或 `strict` 排在 RAG 拒答之前，主链会多一轮工具卫生，注册闸的打印保持今天这样，产品仍然在检索空结果之后把块交回模型、再靠规则闸打回 fresh。那不是 on-call 拒答产品的第一缺口。

## 7. 风险

### 7.1 样本与层身份

| 段 | 规模 | 层 |
|---|---|---|
| R1 arm | 224 题，`human_row_review=false`，单次冻结回放 | 无回归地板。确定性回放，没有运行间样本，不报方差 |
| G1 | 12 条，即 `c1`–`c12` | 文件一致性。冒烟量级的行为覆盖都不构成 |
| A1 | 7 条 keep；precision 只计其中 `|C|>0` 的 5 条 | 金标自洽。不能外推成引用成功率 |
| T1 | 4 条 keep，3 条 scored，1 条正确 | 个案。c2 与 c3 各代表一种失败，不能写成时序检索的通过率 |
| 路线 Y | n=400，结果丙 | 另一套仪器。false-accept 不是 A1 |

质量闸离线，不调用 LLM。`temperature` / seed 不参与这次重放。不得把这次 exit 0 说成多 seed 稳定性。

### 7.2 没有 SESOI

`PREREG` §6 与 QG-13 已经把 G1/A1/T1 的地板定义为「`value >=` 冻结点估计，且 `n` / `scored` / `unresolved` 逐字段相同」。相等不是回归。`value=unavailable` 或分母变化则无回归旗标为 false，退出码非 0。

这是锁分母、锁点估计。它没有回答「产品要好到什么程度才算够」。本诊断不补这个数。以后若要产品合格线，须在看到新结果之前另页预注册，并保持本页地板不动。事后改本页 token，该次验收作废。

### 7.3 金标自洽可以刷注册分

分母锁已经挡住一种刷法：删掉 c2/c3 或改 `scored` 会使无回归旗标为 false。两边金标连同地板 token 一起改，则直接落入 `PREREG` §8 作废。

剩下的风险是叙述刷分：

- 把 `g1_no_regression=true` 或 `value=1.0` 说成拒答率。
- 把 A1 的 recall / precision token 说成线上引用质量。计分不读 `supported` / `false_cite` / `miss_cite`。把一条 `false_cite` 的 `cited_ids` 改成该题 `relevant`，注册分会变，产品不变。
- 把 T1 的地板说成时序检索已测量。把 `in_force` 改成冻结名次第 1 位的 id，回放会变「正确」，检索器不变。
- 用 224 题 any-hit 的高 Recall 覆盖 c2/c3。三题 Recall 已经是 1。

产品改进的验收因此放到夹具契约和新的报告列上。注册四闸在每次相关 PR 里重放，只确认 token 没漂、退出码仍表达无回归，不确认产品变好了。

### 7.4 其他边界

- `guardrail-0hit=unavailable`。`as_of=T1` 过滤打开时这条接近恒真，`PREREG` 拒绝把它写成通过。`--disable-as-of` 不是冻结跑法。
- `lead_delta=0.10` 是 draft-experiment-only，不是产品通过线。
- 神经预注册里的 p95 ≤ 800 ms 不是这四闸的证物。
- 评估文档指出 `docs/spec/00-架构总览.md` 仍有「生产默认 BM25」的旧句。代码与 `PREREG` §2 以 `hybrid+rerank` 为准。本诊断不改那份总览。

## 8. 对票序的直接含义

10-12 的组会序把 FC 放第一，是因为冲突项 C1 选择了组会序，并且权限分层在 FC 票里。这个选择在「最终木桶要包含 FC」上仍然成立。

10-14 的证据改变的是开工顺序，不是最终清单：

1. 注册分不能当拒答或引用的验收。第一批实现票的 Acceptance 必须是夹具，外加「重放质量闸，地板 token 不变」。
2. c2/c3 不靠 FC。时序过滤用独立夹具，因为这两题都是 `@T1` 对 `@T1`，而且改 x1 语料会动指纹。
3. 线上引用只消费 FC 的 cite-emit 切片，并且检查器与 `score_citation_overlap` 分开。
4. Skill 不在主链木桶里。A 层完成时 Skill 目标是 L3，可以与主链并行，不占第一刀。
5. UI 等 reason code 和 hit 分出现再绑。先做徽章，整体档位不变。

有序票、Gate / Auto、以及明确不做，写在计划里。

## 9. 本页没有做的事

- 没有跑 `pytest`，没有跑 live LLM，没有重放路线 Y，没有新测 Recall。
- 没有改金标、题集、指纹、k、模型针、RRF k、精排宽度。
- 没有把 B-02 `conflicting_evidence` 或 B-01 数字闸算进 A 层完成。c2 是反序个案，不是已经实现的冲突拒答。
- 没有开 GitHub Issue，没有勾选 A 层清单。清单上的 `[ ]` 保持未实现。
