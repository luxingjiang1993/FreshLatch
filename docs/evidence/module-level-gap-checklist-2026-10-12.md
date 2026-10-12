# FreshLatch 水平缺口清单（If-landed → 顶尖 demo → L5）

> 日期：2026-10-12。性质：只读规划清单。不开功能票、不改生产代码、不改 `PRODUCTION_RETRIEVAL_MODE`、不改 `RESULT-Y` / `PREREG-Y`。
> 水平评估见 [`module-level-assessment-2026-10-12.md`](module-level-assessment-2026-10-12.md)。前沿参考（按本页 ID）见 [`module-level-frontier-refs-ABC-2026-10-12.md`](module-level-frontier-refs-ABC-2026-10-12.md)。本页把后续缺口收成可勾选项，便于另开任务。
> 标尺：L1–L5 同评估文档。整体档取主链木桶（Function Call / RAG / AI Agent）。

## 0. 怎么读

三层**累加**。上层默认以下层已落地为前提。

| 层 | 目标产品档 | 面试口径（职级，不是产品 L） | 前提 |
|---|---|---|---|
| **A. If-landed** | L4 | 中级场能站稳（硅谷 L4 / Meta E4；上海约 P6 / 字节 2-1） | as-is L3 |
| **B. 顶尖 demo 包** | 仍是产品 L4 的上沿；面试里是中级场最能打的 demo | 同上职级，评委记住拒答与负结果 | A 已落地 |
| **C. 领域标杆** | 产品 L5 | senior 场能站住（硅谷 L5 / Meta E5；上海约 P7 / 字节 2-2） | A + B 已落地，且 C 全齐 |

明确不做（各层共用）：换向量库、装 REA、把 LangGraph 引进 `run_loop`、默认挂上 `LEAD_TOOLS_W9`、接上 `web_search`、把冒烟集或未测数字说成新测量。

路线 Y：`RESULT-Y` 已落档为丙。同一次预注册禁止第二次正式主跑充数。B 层的时序/patch 项是**夹具演示**，不等于乙。C 层「成立的 patch 实验」须另开预注册或合法新尺；乙成立后仍不得称优于 RARR·KPR。

勾选状态：本页落盘时全部为 `[ ]`（未实现、未开票）。

---

## A. If-landed（组会票序 · 产品 L3 → L4）

情景：组会票序 FC→Skill→RAG→Agent→UI→Eval；RAG 同时吸收 temporal/patch 与 sufficiency/abstain。详见评估文档 §2.4。

| ID | 模块 | 项 | 验收形状（一句话） |
|---|---|---|---|
| A-FC-01 | Function Call | `[ ]` schema 再验 + illegal reason code | 非法 args → typed reason code；有限自纠；耗尽 fail-closed |
| A-FC-02 | Function Call | `[ ]` API `strict`（若端点支持） | `chat.completions` 侧能拒非法 schema；业务语义仍再验 |
| A-FC-03 | Function Call | `[ ]` 权限 L0 / L1 / L2 | 读检索 / 写观测需批 / 禁动生产臂，各≥1 测 |
| A-SK-01 | Skill | `[ ]` hooks `failClosed` | 样板：exit 2 deny + `failClosed: true` |
| A-SK-02 | Skill | `[ ]` 3–5 个中文业务 skill | 财报 / 事件 / patch diff / 策略 walkthrough 等；`SKILL.md` + 可选 `scripts/` |
| A-SK-03 | Skill | `[ ]` references 真加载或改掉假承诺 | 独立只读工具，或修正 frontmatter「用 `read_source` 读 references」 |
| A-RAG-01 | RAG | `[ ]` sufficient-context → abstain / 再检索 | retrieve 边标签；不足不硬答 |
| A-RAG-02 | RAG | `[ ]` CRAG grade 边 | Correct / Incorrect / Ambiguous → refine 或 abstain（挂 retrieve，不另起网络回退） |
| A-RAG-03 | RAG | `[ ]` temporal / patch 元数据过滤 | `patch_id` / 有效期等；过滤先于或并入 RRF；不换库 |
| A-RAG-04 | RAG | `[ ]` hybrid+rerank 可测字段 | 每 hit 暴露可测分；manifest 记 rerank ON/OFF ablation |
| A-AG-01 | Agent | `[ ]` verify → repair \| abstain | 短环；state 含 `evidence_ids` / `grade` / `retry_count` |
| A-AG-02 | Agent | `[ ]` 命名 abstention reason codes | 证据不足等可枚举；进轨迹 |
| A-AG-03 | Agent | `[ ]` 失败轨迹可复放 | checkpoint / 等价复放；不另起 runtime |
| A-UI-01 | UI | `[ ]` Query → Hits → Attribution → Unknown \| Override | 分数与 reason code 可见；职人视图仍不泄角色名 |
| A-UI-02 | UI | `[ ]` verified \| partial \| abstain 徽章 | 绑定真实闸，不绑装饰 |
| A-EV-01 | Eval | `[ ]` golden + Recall@k / MRR 分列表 | 臂对比可重复跑；本清单不预填数字 |
| A-EV-02 | Eval | `[ ]` citation 进 CI | claim 对不齐 turn-scoped evidence registry → fail |
| A-EV-03 | Eval | `[ ]` SLI 5 聚合（可选但建议） | 轨迹目录 → e2e P95 + fallback rate；显式切 BM25 ≠ `bm25_fallback` |

**A 层完成判据**：主链木桶 L4；Skill 可为 L3。整体对外口径：可回归的拒答产品。

只落地来源 A 或只落地来源 B：主链木桶仍停在 L3（见评估文档总表）。

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
| 仅 as-is | L3 | 复验闸 + hybrid+rerank + 预注册负结果 |
| A | L4 | 可回归的拒答产品 |
| A + B | L4 上沿（面试顶尖 demo） | 当场拒、指到句、复放失败；末页诚实放丙 |
| A + B + C（含成立的 patch 实验） | L5 | 时序 / patch / 金融级证据闸 / HITL 成熟 |
| A + B + C 但 patch 实验仍负 | L4 | 不得称领域标杆 |

本清单覆盖不到 Staff 场（硅谷 L6、阿里 P8、字节 3-1）：多团队在用、线上事故与路线拍板不在本页。

---

## 与评估文档 / #580 的关系

| 文档 | 角色 |
|---|---|
| [`module-level-assessment-2026-10-12.md`](module-level-assessment-2026-10-12.md) | as-is / if-landed 档位与证据 |
| 本清单 | A/B/C 缺口勾选；后续开票用 ID |
| draft PR #580 架构评估 | 另文；接线建议（检索臂进工具返回等）可作 A 的前置小票，不替代本清单 |

本页**不开票**。勾选变为 `[x]` 须对应已合并实现或已关闭验收，不得空勾。
