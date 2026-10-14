# FreshLatch 水平缺口清单（If-landed → 顶尖 demo → L5）

> **As-of 2026-10-15 / HEAD `9af5af00ef85ad693bc3877299f2ac978ce75f2e`（M8 #621 PASS；父提交 `9cc116d975e06246c6c9d61db8a173364d16a73b`，L4-SK-02 / #620）。** L4U-DOC-02。
> 本回写只把 A 层勾选对齐 #602–#621 与 [`m8-a-layer-checklist-2026-10-14.md`](m8-a-layer-checklist-2026-10-14.md)。B-01…B-05、C-01…C-04 保持 `[ ]`。禁止把未实现项打成 `[x]`。
> 与评估页同一结论：工程 **L4**（可回归的拒答产品），Skill **L3**，**不是 L5**。注册 G1 / A1 / T1 / R1 仍 `status=TBD` / `counted_as_pass=false`。RESULT-Y **丙**。`value=` 不是产品率。
> A-EV-03 仍是 `[ ]`：未实现，不是勾选滞后。
> 水平评估见 [`module-level-assessment-2026-10-12.md`](module-level-assessment-2026-10-12.md)（文首 As-of 横幅为现行档）。前沿参考见 [`module-level-frontier-refs-ABC-2026-10-12.md`](module-level-frontier-refs-ABC-2026-10-12.md)。
> 2026-10-12 原文性质（历史）：只读规划清单。不开功能票、不改生产代码、不改 `PRODUCTION_RETRIEVAL_MODE`、不改 `RESULT-Y` / `PREREG-Y`。标尺 L1–L5 同评估文档。整体档取主链木桶（Function Call / RAG / AI Agent）。

## 0. 怎么读

三层**累加**。上层默认以下层已落地为前提。

| 层 | 目标产品档 | 面试口径（职级，不是产品 L） | 前提 |
|---|---|---|---|
| **A. If-landed** | L4 | 中级场能站稳（硅谷 L4 / Meta E4；上海约 P6 / 字节 2-1） | 2026-10-12 前提是 as-is L3。HEAD 上除 A-EV-03 外已勾，工程档 L4，不是 L5 |
| **B. 顶尖 demo 包** | 仍是产品 L4 的上沿；面试里是中级场最能打的 demo | 同上职级，评委记住拒答与负结果 | A 已落地 |
| **C. 领域标杆** | 产品 L5 | senior 场能站住（硅谷 L5 / Meta E5；上海约 P7 / 字节 2-2） | A + B 已落地，且 C 全齐 |

明确不做（各层共用）：换向量库、装 REA、把 LangGraph 引进 `run_loop`、默认挂上 `LEAD_TOOLS_W9`、接上 `web_search`、把冒烟集或未测数字说成新测量。

路线 Y：`RESULT-Y` 已落档为丙。同一次预注册禁止第二次正式主跑充数。B 层的时序/patch 项是**夹具演示**，不等于乙。C 层「成立的 patch 实验」须另开预注册或合法新尺；乙成立后仍不得称优于 RARR·KPR。

勾选状态：2026-10-12 落盘时全部为 `[ ]`。2026-10-15 起，已合入 #602–#620 的 A 层项改为 `[x]`，并写明 PR 与 squash；未实现项保持 `[ ]`。M8 清单本身是 #621，不是单独的 A-* 行。

---

## A. If-landed（组会票序 · 产品 L3 → L4）

情景（2026-10-12）：组会票序 FC→Skill→RAG→Agent→UI→Eval；RAG 同时吸收 temporal/patch 与 sufficiency/abstain。详见评估文档 §2.4。HEAD 上该情景除 A-EV-03 外已合入，见下表「见 M8 指针」。

| ID | 模块 | 项 | 验收形状（一句话） |
|---|---|---|---|
| A-FC-01 | Function Call | `[x]` schema 再验 + illegal reason code | 非法 args → typed reason code；有限自纠；耗尽 fail-closed。见 M8 指针：L4-FC-01 [#609](https://github.com/luxingjiang1993/FreshLatch/pull/609) `5ab6ca3e077e61ecee6181e41c31ea33e430c1ec` |
| A-FC-02 | Function Call | `[x]` API `strict`（若端点支持） | `chat.completions` 侧能拒非法 schema；业务语义仍再验。见 M8 指针：L4-FC-02 [#610](https://github.com/luxingjiang1993/FreshLatch/pull/610) `005a7e2b9aa21e4364ef412a64f39bcb1daa71de`。端点不支持则书面声明仅运行时再验，仍算本项 |
| A-FC-03 | Function Call | `[x]` 权限分层（实现名 `tool_tier_0/1/2`，不是 HumanLatch 的 L0） | 读检索 / 写观测需批 / 禁动生产臂，各≥1 测。见 M8 指针：L4-FC-03 [#611](https://github.com/luxingjiang1993/FreshLatch/pull/611) `17d9ddb89e09d13dff6069ab42c149866039c35b` |
| A-SK-01 | Skill | `[x]` hooks `failClosed` | 样板：exit 2 deny + `failClosed: true`。见 M8 指针：L4-SK-01 [#619](https://github.com/luxingjiang1993/FreshLatch/pull/619) `27acda75cefa11e6a4327aeb22febbd17ddcb4b9`。默认不启用；Skill 综合仍 L3 |
| A-SK-02 | Skill | `[x]` 3–5 个中文业务 skill | 财报 / 事件 / patch diff / 策略 walkthrough；在盘未挂 Runner。见 M8 指针：L4-SK-02 [#620](https://github.com/luxingjiang1993/FreshLatch/pull/620) `9cc116d975e06246c6c9d61db8a173364d16a73b` |
| A-SK-03 | Skill | `[x]` references 真加载或改掉假承诺 | `load_skill_reference` 读 `skills/{slug}/references/{name}.md`。见 M8 指针：L4-SK-03 [#618](https://github.com/luxingjiang1993/FreshLatch/pull/618) `bb6f3e20e6346b24514c69f9b72498fa7ee7e163` |
| A-RAG-01 | RAG | `[x]` sufficient-context → abstain / 再检索 | retrieve 边标签；不足不硬答。见 M8 指针：L4-RAG-01 [#602](https://github.com/luxingjiang1993/FreshLatch/pull/602) `e7b44f469ab32ac89926af66c557c82cb246f7bb` |
| A-RAG-02 | RAG | `[x]` CRAG grade 边 | Correct / Incorrect / Ambiguous → refine 或 abstain（挂 retrieve，不另起网络回退）。见 M8 指针：L4-RAG-02 [#604](https://github.com/luxingjiang1993/FreshLatch/pull/604) `aa7f2a5537f0a5236bde8337dc73fd16d55c4c0f`。Ambiguous 不是 B-02 的 `conflicting_evidence` |
| A-RAG-03 | RAG | `[x]` temporal / patch 元数据过滤 | `patch_id` / 有效期；过滤先于 RRF；不换库。见 M8 指针：L4-RAG-03 [#606](https://github.com/luxingjiang1993/FreshLatch/pull/606) `1ac137d15d5c1fe52c596276f1e549fc75d793f4`。本勾不等于 B-04 |
| A-RAG-04 | RAG | `[x]` hybrid+rerank 可测字段 | 每 hit 暴露可测分；记 rerank ON/OFF。见 M8 指针：L4-RAG-04 [#605](https://github.com/luxingjiang1993/FreshLatch/pull/605) `42df3c7371d0d4add7ce7594c3df9adb5edda8a1`。不改 `PRODUCTION_RETRIEVAL_MODE` |
| A-AG-01 | Agent | `[x]` verify → repair \| abstain | 短环；state 含 `evidence_ids` / `grade` / `retry_count`。见 M8 指针：L4-AG-01 [#612](https://github.com/luxingjiang1993/FreshLatch/pull/612) `99b285e50df7194c510ce09433ec0b0eeba8ea18` |
| A-AG-02 | Agent | `[x]` 命名 abstention reason codes | 证据不足等可枚举；进轨迹。见 M8 指针：L4-AG-02 [#613](https://github.com/luxingjiang1993/FreshLatch/pull/613) `9da579a37dd24daec49eaf5aa43f4780ac465119` |
| A-AG-03 | Agent | `[x]` 失败轨迹可复放 | JSONL 复放；不另起 runtime，LangGraph 不进 `run_loop`。见 M8 指针：L4-AG-03 [#614](https://github.com/luxingjiang1993/FreshLatch/pull/614) `9b55ff7ac84a2820243b88207432f8a91a49472e`。本勾不等于 B-05 |
| A-UI-01 | UI | `[x]` Query → Hits → Attribution → Unknown \| Override | 分数与 reason code 可见；职人视图仍不泄角色名。见 M8 指针：L4-UI-01 [#615](https://github.com/luxingjiang1993/FreshLatch/pull/615) `dc551f01c94a6a1b20977fe7a09d8b4467b30868` |
| A-UI-02 | UI | `[x]` verified \| partial \| abstain 徽章 | 绑定真实闸，不绑装饰。见 M8 指针：L4-UI-02 [#616](https://github.com/luxingjiang1993/FreshLatch/pull/616) `3c3ac7a6fdb89288a5ad868ad733cfe13669cb46` |
| A-EV-01 | Eval | `[x]` golden + Recall@k / MRR 分列表 | 臂对比可重复跑；不预填新数字，不抬注册地板。见 M8 指针：L4-EV-01 [#617](https://github.com/luxingjiang1993/FreshLatch/pull/617) `2aba5500069ac813ba8ab3254258e5093e1d48c7`。`replaces_frozen_baseline=false`。不是因为仓内早已有 Recall 函数而空勾，见文末歧义 §5 |
| A-EV-02 | Eval | `[x]` citation 进 CI | claim 对不齐 turn-scoped evidence registry → fail。见 M8 指针：L4-FC-CITE [#607](https://github.com/luxingjiang1993/FreshLatch/pull/607) `b0c66bf68f9c9a668ee12ac932e422e10c8a163c` 与 L4-EV-02 [#608](https://github.com/luxingjiang1993/FreshLatch/pull/608) `b131d562e76b8ea38e8437dc643a088055258d35`。夹具绿不是注册 A1 新地板 |
| A-EV-03 | Eval | `[ ]` SLI 5 聚合（可选但建议） | 轨迹目录 → e2e P95 + fallback rate；显式切 BM25 ≠ `bm25_fallback`。**仍未实现**（`src/` 无该聚合）。M8 写明 optional、不挡 PASS。这是开着的缺口，不是勾选滞后。不计入注册 G1/A1/T1/R1 |

另有已合、但不单列成 A-* 行的指针：L4-EV-T1-CASE [#603](https://github.com/luxingjiang1993/FreshLatch/pull/603) `7547e9f15d57ddbec018f69d56cd01940e0f5c17`（冻结名次上的 T1 个案锁，不改注册 T1 地板）。M8 记录页是 [#621](https://github.com/luxingjiang1993/FreshLatch/pull/621) `9af5af00ef85ad693bc3877299f2ac978ce75f2e`。

**A 层完成判据**：主链木桶 L4；Skill 可为 L3。整体对外口径：可回归的拒答产品。HEAD 上除 A-EV-03 外已满足该工程判据。A-EV-03 不挡它。满足 A 层判据不是 L5。

只落地来源 A 或只落地来源 B：在 2026-10-12 反事实里主链木桶仍停在 L3（见评估文档总表）。该句不描述 HEAD。

---

## B. 顶尖 demo 包（面试中级场最能打 · 仍非产品 L5）

前提：A 层已落地。目标：一场 walkthrough 里**能当场拒、能指到句子、能复放失败**。冲乙正式主跑不要求变成乙。

| ID | 项 | 要解决的空洞 | 验收形状（一句话） |
|---|---|---|---|
| B-01 | `[ ]` **数字闸** | A 仍是「证据 id 齐了就可以 fresh」；错数字可以写得很顺 | 主张中的数由 code / operator 算出；对不上 → abstain；模型只叙述「这句话怎么来」 |
| B-02 | `[ ]` **冲突拒答** | sufficiency / CRAG 只覆盖「不够」；「够了但相反」会挑流畅那条 | 两条 T1 互斥 → reason code `conflicting_evidence`；不得选更流畅的一侧硬答 |
| B-03 | `[ ]` **句子级归因** | Hits + 分数仍是块级；追问「哪半句支撑定价」停住 | 答案一句 → 支撑句 +（若有）反对句，均可点回 T1 原文位置 |
| B-04 | `[ ]` **一次看得见的时序 / patch 闸** | A 的元数据过滤若只在后端，面试看不见 | 同一主张、两份 `as_of` 或两个 patch：错版本被滤或标 stale；面板露出 `patch_id` / 有效期。**夹具**，不是 n=400 乙 |
| B-05 | `[ ]` **失败复放 + 人审改账** | A 有 checkpoint 雏形时，人仍只有 `discard` / `renew` | 打开一条失败轨迹，能指：检索空 / grade 不够 / 工具被 L2 拒；新增 `disputed`（或等价），改过的结论进台账且可再打开 |

**B 层完成判据**：产品综合档仍诚实标 **L4 上沿**（缺 C 则不到领域标杆）。面试口径：中级场（硅谷 L4 / 上海 P6·2-1）里最能打的 demo。幻灯片末页可放路线 Y 的丙：尺事先锁死，下界未过，不称补丁实验成立。

Skill：B 不要求 56 份 playbook。一场 demo 里一份 skill 的 `allowed-tools` 叫不了 L2、hook 返回 deny，即可。

---

## C. 领域标杆（产品 L5 · senior 场）

前提：A + B 已落地。下列四项**全部**齐，整体才进 L5。

| ID | 项 | 要解决的空洞 | 验收形状（一句话） |
|---|---|---|---|
| C-01 | `[ ]` **训练过的时序检索** | A/B 的 temporal 是元数据过滤或夹具；无训练型时序检索 | 有文档化的时序检索臂（训练或等价已发表方法落地）；评测分列 Recall@k / MRR（或 nDCG），数字来自该次测量 |
| C-02 | `[ ]` **在线 claim 监控** | A 的 citation / faithfulness 若只在 CI / 抽检 | 生产路径有 claim 级监控或连续抽检流水；缺分 / 漂移可报警或拒发；层身份写清（观测 ≠ 实验成立格） |
| C-03 | `[ ]` **多租户权限** | 今日 `tenant_id` 可选过滤；无完整权限产品 | 租户隔离 + 工具/数据权限分层可演示、可测；越权路径 fail-closed |
| C-04 | `[ ]` **成立的 patch 实验** | `RESULT-Y` 为丙；同尺不得二次充数 | 合法新预注册或新尺下，成立格按原文通过；**仍不得**称优于 RARR·KPR；禁止把夹具 B-04 写成乙 |

**C 层完成判据**：产品综合 **L5**。面试口径：senior 场（硅谷 L5 / Meta E5；上海约 P7 / 字节 2-2）能站住。人是否 senior 仍取决于个人是否拥有这些闸与实验，不取决于文件是否存在。

C-04 若再跑仍为丙：闸门可以很满，综合档停在 **L4**，实验轴不得写成 L5。

---

## 累计档位速查

| 已完成层 | 产品综合档 | 面试一句话 |
|---|---|---|
| 仅 2026-10-12 as-is（已过期） | L3 | 复验闸 + hybrid+rerank + 预注册负结果 |
| A（HEAD：除 A-EV-03 外已勾；B/C 仍 `[ ]`） | **L4**（Skill L3；不是 L5） | 可回归的拒答产品；注册仍 TBD；RESULT-Y 丙 |
| A + B | L4 上沿（面试顶尖 demo） | 当场拒、指到句、复放失败；末页诚实放丙 |
| A + B + C（含成立的 patch 实验） | L5 | 时序 / patch / 金融级证据闸 / HITL 成熟。HEAD 未到这一行 |
| A + B + C 但 patch 实验仍负 | L4 | 不得称领域标杆 |

本清单覆盖不到 Staff 场（硅谷 L6、阿里 P8、字节 3-1）：多团队在用、线上事故与路线拍板不在本页。

---

## 开票前已知歧义与边界（须钉死）

> 本清单**够当规划 / 面试档位 / 摘法索引**，**不够当** Matt `/implement` 开工规格（缺可执行 Acceptance、Paths、Provenance、Trust/Blast）。下列项不是推翻 A→B→C 梯子的硬错误，但会让实现票走偏。开第一张功能票前至少钉死 §1–§3。

### 1. `L0` 词冲突（A-FC-03）

仓内既有 **L0 = HumanLatch 人审出口**（见 `gates/rule_gate.py` 文首、`CONTEXT.md`、评估文档第 7 节）。  
本清单 `A-FC-03` 的 L0 / L1 / L2 指的是**工具权限分层**（读检索 / 写观测需批 / 禁动生产臂），与人审 L0 **不是同一词表**。

**开票须改名**，例如 `tool_tier_0|1|2` 或「读 / 需批 / 禁」。禁止在实现 PR 里继续裸写「L0」而不加限定，以免与 HumanLatch 语义打架。

### 2. A 与 B 边界：勿做成两遍、勿提前勾上

| 易混对 | A 勾上只证明 | B 仍缺的硬条件 |
|---|---|---|
| `A-RAG-03` ↔ `B-04` | 后端有 temporal / `patch_id` / 有效期过滤（先于或并入 RRF） | 面板**看得见** `as_of` / `patch_id` / 有效期；夹具可演示错版本被滤或 stale。A 做完 ≠ B-04 |
| `A-AG-03` ↔ `B-05` | 失败轨迹可复放（扩展 JSONL 与/或既有 latch checkpoint） | 审计面能指三桶（检索空 / grade 不够 / 工具被 `tool_tier_2` 拒）+ 人审 `disputed`（或等价）进台账可再开 |

`A-AG-03` 的「checkpoint / 等价复放」= 轨迹 JSONL 可复盘 + 人审侧既有 LangGraph checkpoint。**禁止**把 LangGraph time-travel 引进 `run_loop`（见前沿参考 A-AG-03 / B-05 摘法）。

### 3. B-01 数字闸：两种验收读法须二选一

| 读法 | 含义 | 更贴 FreshLatch 处 |
|---|---|---|
| **verbatim 对账** | 从主张与 T1 证据抽数 → exact（或声明容差）匹配；对不上 → abstain / unknown | 复验主链（前沿 B-01 默认摘法） |
| **公式重算** | 数由 code / operator 算出，模型只叙述「怎么来」 | FinRobot / VeNRA 式；可选增强，非首票默认 |

清单正文「主张中的数由 code / operator 算出」易被读成第二种。开票时**必须钉死**采用哪一种（或分两张票：先对账、后重算）。未钉死不得勾 `[x]`。

### 4. A 层完整前沿表不在本仓

A 的完整实践/论文表原在组会两源整合附件（`freshlatch-module-frontier-refs-MERGED`）。本仓内 A 只有 [`module-level-frontier-refs-ABC-2026-10-12.md`](module-level-frontier-refs-ABC-2026-10-12.md) 的**按 ID 薄索引**。干净 clone **看不到**附件全文。

**用法**：开 A 票以评估文档 + ABC 前沿索引的「挂点 / 摘法」为准；需要完整两侧原文时另落仓或指向已归档附件，勿假设上传目录常驻。

### 5. A-EV-01 易被误判「早已完成」

`src/freshlatch/eval/retrieve_*.py` 在 2026-10-12 已有 Recall@k / MRR 函数与历史报告。当时清单标 `[ ]`，是因为缺的是**可重复的同 pin · 同 gold · 分列表 · 可进回归**的形状，不是从零写指标。

2026-10-15 的 `[x]` 只对应 L4-EV-01 #617 的臂表（`replaces_frozen_baseline=false`，smoke 可重复，不替换冻结 `neural-rerank/per-query.json`，不把注册 R1/T1 的 `counted_as_pass` 改成 true）。禁止回头把「仓里早就有 Recall」当成勾选理由。夹具或臂表变绿不等于注册地板变了。

### 6. 非 bug、但是限（摘码时自知）

- 前沿参考中多条 ★0 个人仓：存在性已抽查，质量方差大；**只摘 pattern，禁止整仓迁移**。
- TempRetriever（C-01）官方训练代码调研日未公开；可作理论锚，禁止写「已复现 TempRetriever」。
- `A-FC-02` 的 API `strict`：DashScope / qwen 等托管端点可能不支持；保留「若端点支持」，不支持则文档声明「仅运行时再验」仍可勾业务语义闸。
- `C-04` 受预注册与 `RESULT-Y` 丙防火墙约束；乙不成则整体诚实停 L4（见累计档位表）。

### 7. 本清单够用 / 不够用

| 用途 | 是否够用 |
|---|---|
| 排优先级、面试档位、防吹过头 | 够 |
| 按 ID 查可摘 repo / 论文 | 够（B/C 尤甚；A 见 §4） |
| 直接 `/implement` | **不够** → 先 to-tickets + enrich（Acceptance / Paths / Provenance / Trust） |
| 勾选变 `[x]` | 须已合并实现或已关闭验收；不得空勾 |

---

## 与评估文档 / #580 的关系

| 文档 | 角色 |
|---|---|
| [`module-level-assessment-2026-10-12.md`](module-level-assessment-2026-10-12.md) | 现行档在文首 As-of 横幅与 §1 / §3；§4 五轴是 2026-10-12 快照 |
| 本清单 | A/B/C 缺口勾选；A 层（除 A-EV-03）已按 #602–#620 回写；B/C 仍空；**开票前歧义见上一节** |
| [`module-level-frontier-refs-ABC-2026-10-12.md`](module-level-frontier-refs-ABC-2026-10-12.md) | 各 ID 的 GitHub / 论文 / 产品可摘 pattern（只摘 fields/modes） |
| draft PR #580 架构评估 | 另文；接线建议（检索臂进工具返回等）可作 A 的前置小票，不替代本清单 |

本页**不开票**。勾选变为 `[x]` 须对应已合并实现或已关闭验收，不得空勾。2026-10-15 的 A 层 `[x]` 都指到上表 PR / squash。B-01…B-05 与 C-01…C-04 在本回写时仍是 `[ ]`。
