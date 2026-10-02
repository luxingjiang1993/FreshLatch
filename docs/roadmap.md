# FreshLatch Roadmap v3.1（阶段版）

> 状态：执行版（2026-09-29 修订 · 论文路线 A）。  
> 相对 v2：按阶段 In/Out/Exit 重排；补入 Verify+/Studio 嵌套、差异化短名单、论文挂点、客户对客话术；并应用核查补丁（默认序、#8 锚点、I2≠#4、Legacy map、单垂直、L0–L2）。
> 2026-09-29：锁定论文路线 A（Evidence-bound / attested patch → V1.5）；补全「论文↔模块」预实验与 venue。  
> 备份：`/workspace/freshlatch-roadmap.v2-backup.md`（及更早的 v1-backup，若仍在）。
> Grill 前置：开 `grill-with-docs` 前先读 [grill-prep.md](./grill-prep.md)（阅读包 + 待钉决策）。


**North star:** 已签发主张必须「现在仍可复验」；无 T1 不得绿灯；人决定作废/续命。  
**Shape:** `Gate ⊂ Verify+ ⊂ Studio` · 近端只做 Verify+ · Studio 冻结  
**Cadence:** 一人同时只开 **一条** 阶段（V 或 I）；无固定四周日历  
**Bar:** 冲 mid = 数字 + 失败样本 + 安全三例 + 口述，不靠 UI  
**代理:** 仓库变更按 L0/L1/L2（Ronin 可代 L1；**人终收类如历史 #166 不代批/代关**）；超时或证据不足 fail-closed。

```
DONE: Phase A · Phase I0 · Phase V1（冒烟 + 本地 ACCEPTANCE）· Phase I1（冒烟 corpus）· Phase V1.5（冒烟 Evidence-bound）· Phase I2（冒烟安全三例）· Phase V2（冒烟·采用层 发前钩子+台账）· Phase I3（冒烟/面试加固三轨）· ① bare-pytest 卫生
NOW → NEXT:
  C′ 外部嵌入平台化 |（Hard-Gold 已过线 · 未换臂 · Gate #260 待人终收）
BACKLOG: C′ 外部嵌入平台化 | 图谱/采编 CMS | High-Recall SKU | Studio (frozen) | B′ 真事故扩面（I3 夹具以外仍 on-demand）
```

**默认阶段序（钉死）：** `V1 → I1 → V1.5`。  
**唯一例外：** 自用痛点明确是「改稿再验」时，允许 V1 后先开 V1.5；**冲 mid 仍以 I1 为准**，不得用 V1.5 替代 I1。  
**本期：** V1.5 / I2 / V2 / **I3 Exit 已齐**；**Hard-Gold 改臂闸流程已钉**（[#257](https://github.com/luxingjiang1993/FreshLatch/issues/257) · ADR-0033）；**#259 同库复跑已过线 · 未换臂 · 待 Gate 实现票**（证据 `docs/evidence/hard-gold-arm/`）。

---

## Phase A — Retrieval subsystem · **DONE**

**Goal:** 可测、可降级的 retrieve；生产默认 BM25。

| | |
|--|--|
| **In** | BM25 默认；dense/hybrid/rerank 评测臂；`bm25_fallback`；Agent 只调冻结 retrieve |
| **Out** | agentic RAG；未过增益门改默认臂 |
| **Exit** | 已齐（#160/#161/#163 Ronin L1 代审通过；#166 人终收） |

**口径：** Phase A = 子系统 RAG（可测 retrieve），**不是** agentic RAG。

---

## Phase I0 — Accounting + eval · **DONE**

**Goal:** 面试官能打开仓复现「为何默认 BM25」。  
**Track:** I（可与收尾文档并行，优先于炫 UI）

| | |
|--|--|
| **In** | `accounting-card`；`eval-retrieve` 对比表；降级说明；贡献清单 v0 |
| **Out** | 产品功能开发；改生产默认臂 |
| **Exit** | 已齐（表在仓；BM25 复跑指标与 SoT 一致；四探针标准答核对；见 `docs/evidence/i0/ACCEPTANCE.md`） |

**Deliverables**
1. [x] `docs/accounting-card.md` — 假设 → 公式 → 数字 → 权衡  
2. [x] `docs/eval-retrieve.md` + 可复跑命令 — 含「为何仍 BM25」  
3. [x] `docs/contribution-boundary.md` v0  

**工程证据（2026-09-29）:** 已对齐 `origin/main`；`python -m freshlatch.eval retrieve` → `n=36 Recall@10=1.0000 MRR@10=0.7324 replay=pass`（与 SoT 指标一致；Windows CRLF 未覆盖 #166 报告）。

---

## 本期优先 ① — bare-pytest path 卫生 · **DONE（2026-09-29）**

**Goal:** 裸 `pytest` 与 `python -m pytest` 对 `tests/` collection 行为一致。  
**Track:** 工程卫生 · **已关**

| | |
|--|--|
| **In** | 根治 `from tests.unit.test_meta_gate import …` 在裸 `pytest.exe` 下失败 |
| **Out** | 改产品 Gate/检索默认臂 |
| **Exit** | **已齐**：清空 `PYTHONPATH` 后裸 `pytest tests/` collection **0 errors**；点名两 c9 文件裸跑与 `python -m pytest` 均绿 |

**实装:** 仓库根 `pytest.ini` → `pythonpath = .`。权威命令仍可用 `python -m pytest`。

---

## Phase V1 — Pre-publish loop · **DONE（冒烟）· 本地 ACCEPTANCE 见 evidence/v1**

**Goal:** 一条可演示的发前路径：入库 → Gate → 包结论 → 人审 → 两屏。  
**Track:** V · **Depends on:** I0 DONE  
**决议:** ADR-0027；评估见 `docs/research/V1-发前闭环垂直与包结论设计评估.md`  
**共享理解:** 2026-09-29 再确认成立（垂直/两屏/包结论/薄 URL/patch_events/不做薄对话）  
**本地 Exit 证明:** `docs/evidence/v1/ACCEPTANCE.md`（I1-Q7/ADR-0028；关门摘要另见 `V1-DoD-CLOSE.md`）

| | |
|--|--|
| **In** | **单一垂直=顾问报告**（McK SoAI 03→11 样例包）；T1 落盘（checksum）；三卡+薄 URL（`www.mckinsey.com`）；Gate；包结论新层（**可发 / 需补丁 / 勿发**）；作废/续命；两屏（列表新建+复验单详情）；**`patch_events` JSONL 起记**（后台 C/T） |
| **Out** | **多垂直并行**；难金标；High-Recall 改默认；Studio；薄对话/厚对话改裁决；开放爬虫 |
| **Exit** | **已齐（冒烟级，2026-09-29）**：发前路径可 demo；轨迹追到 T1 checksum；包结论与预登记映射/闸口径一致。证据 `docs/evidence/v1/V1-DoD-CLOSE.md`。非 Hard-Gold；生产默认臂仍 `bm25`。 |

**Definition of Done**（冒烟级勾选；证据见 `docs/evidence/v1/V1-DoD-CLOSE.md`。grill / to-spec 历史留在文末修订记录）
- [x] 未归档不得定论  
- [x] 报告级 disposition 可追责  
- [x] 人审路径走通  
- [x] 单一垂直已写进文档/README  
- [x] `patch_events` schema 已落并开始记账  

---

## Phase I1 — Failure taxonomy + HumanLatch corpus · **DONE（冒烟）**

**Goal:** 把「能跑」变成「能答辩错在哪层」。  
**Track:** I · **Depends on:** **本地 V1 Exit**（`docs/evidence/v1/ACCEPTANCE.md` **已齐 · 2026-09-29**）· **默认在 V1.5 之前**  
**决议:** ADR-0028；评估见 `docs/research/I1-失败三分法与HumanLatch语料设计评估.md`  
**本地 Exit 证明:** `docs/evidence/i1/ACCEPTANCE.md`（短索引 + `events.jsonl`；Ronin 代批 #188）

| | |
|--|--|
| **In** | 失败三分法（全链三桶）挂 **eval/轨迹标签**；≥3 漏拦/误拦复盘（重标 + ≥1 可复跑）；`docs/evidence/i1/` 页 + `events.jsonl` |
| **Out** | 新功能大项；编造无复盘样本；**改生产** Gate/disposition/HumanLatch 枚举；把三分法写成生产 status |
| **Exit** | **已齐（冒烟级，2026-09-29）**：短索引漏/误 ≥3 且 `runnable=true` ≥1（`i1-s005`）；证据 `docs/evidence/i1/ACCEPTANCE.md`。子票 #184–#188 CLOSED；父规格 #183 收口。非 Hard-Gold；生产枚举未扩。 |

---

## Phase V1.5 — Evidence-bound / attested patches · **DONE（冒烟）· CUSTOMER WEDGE**

**Goal:** 改稿带证据、人确认后应用、可立刻再验。  
**Track:** V · **DONE（冒烟）** · **Depends on:** V1；**默认在 I1 之后**（例外见文首）· **I1 Exit 已齐**  
**Maps to idea #2（对客主卖点 · 论文主投路线 A）**  
**决议:** ADR-0029；评估见 `docs/research/V1.5-Evidence-bound补丁设计评估.md`  
**共享理解:** 2026-09-29 已确认（表单闭环 / 独立 patch API / 薄对话本期 Out / 冒烟 Exit）

**对外用语：** evidence-bound / attested patch（**少用** proof-carrying，易撞形式化 PCC）。

| | |
|--|--|
| **In** | **表单闭环**：主张正文替换 + 必填 `t1_ids`（⊆ 本 Run 已入库 T1）+ 人确认才应用 + 强制单条再验；复验单/Run 详情增量 UX；`propose_patch`/`confirm_patch`（不扩 HumanLatch）；正式 `patch_events` 含 before/after；导出 JSON+短 MD |
| **Out** | **薄对话**（本期不实装、不 stub）；开放问答；对话改正式裁决；编辑器秀 / span 级 diff 台；产品路径无证 C；#8 并行；Exit 硬绑「可发」 |
| **Exit** | **已齐（冒烟级，2026-09-29）**：硬闸拒无证 + 有证 confirm + 再验触发 + 导出可演示；证据 `docs/evidence/v15/ACCEPTANCE.md`；关门摘要 `docs/evidence/v15/V15-DoD-CLOSE.md`。升「可发」=加分非硬条；**n≥30 不挡**。非 Hard-Gold；生产默认臂仍 `bm25`；HumanLatch 未扩；薄对话未进主链。 |

**Note:** 不定 mid 生死；冲 mid 仍靠 I0+V1+I1+I2，**不得用本阶段替代 I1**。对客尖刀 + 论文主投实验在本阶段。

---

## Phase I2 — Security demos · **INTERVIEW SAFETY ROUND**

**Goal:** 越权召回 · 间接注入 · 检索投毒 **各一例**可复现（冒烟 · 面试安全轮）。  
**Track:** I · **Depends on:** 不晚于对外主叙事；V1.5 Exit 已齐 · 可错峰  
**决议:** ADR-0030；评估见 `docs/research/I2-安全三例设计评估.md`  
**共享理解:** 2026-09-29 已确认（三例 Exit · 真路径薄 ACL · Gate 注入拒 · poison 元数据剔除 · 分层硬门 · roadmap 完整对齐三例）

| | |
|--|--|
| **In** | **三例**：① 合成 `tenant_id` 越权召回失败测例（真 `retrieve` 硬过滤）；② 污染 T1 间接注入 + 规则闸 fail-closed；③ 显式 `poison`/`untrusted` 高分块不得进可引用集；`docs/security.md` 薄表（每威胁一行）；`docs/evidence/i2/ACCEPTANCE.md`；确定性 pytest 硬门 + 注入场景 **1×** Lead+Critic+LLM 冒烟（显式 decoding） |
| **Out** | 安全平台；多攻击面大而全；完整 RBAC/租户管理面；无标签投毒启发式作硬门；三威胁全绑 LLM 判生死；**用 #4 对抗出版人替代本阶段**；UI 硬门 |
| **Exit** | **已齐（冒烟级，2026-09-29）**：三例 demo 可复现；证据 `docs/evidence/i2/ACCEPTANCE.md` + `docs/security.md`；关门摘要 `docs/evidence/i2/I2-DoD-CLOSE.md`。文首冒烟声明；**不**报安全通过率/方差。非渗透认证。#4 可选≠Exit。 |

**I2 ≠ #4：** Idea **#4**（过期伪装 / 出版对抗）可同波交 **1** 条可选样例（ACCEPTANCE 分节）；**不计入 I2 Exit**，二者互不替代。

---

## Phase B′ — Agent hardening · **部分并入 I3 · 真事故仍 ON-DEMAND**

**Status:** I3 本波仅做 **合成夹具**（timeout/结构化错误/串行幂等薄刀 + 闸分布一页）；**不声称**修过真生产事故。真 Trigger（演示卡死/人审重放翻车）仍可另开薄票扩面。  
**Goal:** 修真实演示/人审事故，不为「像生产」空转；I3 夹具服务冲 mid。  
**Depends on:** V1 + I1 之后；I3 见下节

| Trigger | Work |
|---------|------|
| 演示卡死/假绿 | timeout / retry / 结构化错误 |
| 人审重放出事 | 串行幂等 / 重入 |
| 说不清闸分布 | 轨迹 → 一页观测 |

**Out:** Memory 大叙事、多 Agent 拓扑、跨 Provider 对照作硬关门。

---

## Phase I3 — 面试加固三轨（#8 · B′夹具 · Hard-Gold骨架）· **DONE（冒烟/面试加固）**

**Goal:** 冲 mid 可答辩加固包：政策旁路拒绿灯 · Agent 假绿/重入不静默 · 难金标骨架可跑且默认臂仍 bm25。  
**Track:** I · **Depends on:** V1–V2 / I0–I2 冒烟已齐  
**决议:** ADR-0032；评估见 `docs/research/I3-面试加固三轨设计评估.md`  
**共享理解:** 2026-10-03 已确认（一阶段三轨 · 票序 #8→B′→Hard-Gold→DoD · 不改臂 · 出处禁区旁路）  
**规格:** `docs/spec/20-PhaseI3-InterviewHardening.md` · GitHub [#248](https://github.com/luxingjiang1993/FreshLatch/issues/248)  
**子票:** #249–#253；依赖 `#249→#250→#251→#252→#253`  
**主缝:** 政策旁路能拒绿灯、Agent 假绿/重入不静默、难金标骨架可跑且默认臂仍为 bm25——三轨证据分列，互不顶替。

| | |
|--|--|
| **In** | **#8**：声明式出处禁区 → Verify+ 旁路 → 政策拒 ≥1 可复现；**B′**：timeout/结构化错误 + 人审串行幂等薄 + 闸分布一页（合成夹具）；**Hard-Gold**：规格 + `retrieve_hard_gold` n≥20（traps/对抗≥30%）+ 分列增益报告 + **断言仍 bm25**；`docs/evidence/i3/ACCEPTANCE.md` |
| **Out** | 改 `PRODUCTION_RETRIEVAL_MODE`；宣称 Hard-Gold 已授权换臂；OPA/Cedar/政策平台；改写 `rule_gate` 不变量语义；Memory/多 Agent/跨 Provider 硬关门；Studio；C′/图谱/CMS；High-Recall 改默认；用 I3 替代 I1/I2；报方差/显著；整包再验挂回发前钩子 |
| **Exit** | **已齐（冒烟/面试加固，2026-10-02）**：三轨硬条均 pass；证据 `docs/evidence/i3/ACCEPTANCE.md`；关门摘要 `docs/evidence/i3/I3-DoD-CLOSE.md`。**非**改臂授权；**非**政策平台；**非**真事故复盘。生产默认臂仍 `bm25`。 |

**票序（一人一条）：** #8 → B′ → Hard-Gold → 联合 DoD（已交付）。

---

## Phase V2 — 发前钩子 + 主张台账 · **ADOPTION**（历史别名 Embed + ledger）

**Goal:** 「要发了」多一步被采用；主张作废/续命历史可查。  
**Track:** V · **Depends on:** V1 可信 · I2 Exit 已齐 · **不与** I0–I2 抢带宽  
**决议:** ADR-0031；评估见 `docs/research/V2-发前钩子与主张台账设计评估.md`  
**共享理解:** 2026-09-30 已确认（发前钩子闸 · Memo UI+CLI · 入站 check · 台账只读投影 · 冒烟 Exit）

| | |
|--|--|
| **In** | **发前钩子（publish hook）**：只读包结论 + T1 checksum/`run_id` 机械新鲜度（**不**整包再验）；硬出口 = Client Memo **UI+CLI** 同闸 + **入站** HTTP check（本机默认 + 可选 token）；**主张台账** = 作废名单 ∪ 续命 `latch_log` **只读投影**（详情旁路 + 可导出 MD）；`需补丁` 默认拒干净导出，`ack_needs_patch` 才放行并强制页眉 |
| **Out** | 大图谱；全量采编平台（旧 Phase C）；Word/Notion/开放 webhook **平台化**（→ Backlog C′）；Memo 商业裁决；扩 HumanLatch / renew 改正文；新表双写作废；改生产默认臂；解冻 Studio；把检索 embed 称作本阶段交付 |
| **Exit** | **已齐（冒烟·采用层，2026-09-30）**：Memo 闸动作正确 + `curl`/TestClient 入站 hook allow/deny 各 ≥1 + 台账可见本次 discard/renew + `docs/evidence/v2/ACCEPTANCE.md`；关门摘要 `docs/evidence/v2/V2-DoD-CLOSE.md`。sheet/补丁同闸 = 加分另票。**不**硬绑「可发」。非 Hard-Gold；`curl` ≠ 插件/webhook 平台已交付；生产默认臂仍 `bm25`；Studio 未解冻。 |

---

## Backlog · **SEPARATE TICKETS / FROZEN**

### Ticket: Hard-Gold + arms gate · **骨架并入 I3 · 改臂闸已决议 · 已过线 · 未换臂**
I3 交付难金标骨架 + 增益报告 + **不改臂**。  
**改臂授权闸**已 grill 收口（[#257](https://github.com/luxingjiang1993/FreshLatch/issues/257) · ADR-0033）；**#258** 曾因臂对比缺 traps 假 fail；**#259** 同库（corpus+traps）按原门复跑：**已过线 · 未换臂**（Hybrid pass；Rerank 关；配置仍 bm25）。  
评估见 `docs/research/Hard-Gold过线与改臂决议设计评估.md`；证据 `docs/evidence/hard-gold-arm/` · [`RERUN-20261003-259.md`](./evidence/hard-gold-arm/RERUN-20261003-259.md)。  
**不等于** 旧 Phase B；**≠** 已换臂；**须** Gate 实现票人终收后方可改 `PRODUCTION_RETRIEVAL_MODE`。

### Ticket: High-Recall SKU（可选）
预算内二次检索；同一审计契约；默认臂变更仍走 Hard-Gold 改臂决议。

### Ticket: Policy-as-code thin slice（idea **#8**）· **并入 I3**
禁区规则进 Gate 旁路；I3 首条 = 出处禁区。完整政策平台仍 **Out**。

### Ticket: C′ 外部嵌入平台化（备选 · 非 V2 Exit）
Word / PPT / Notion 插件、开放公网 webhook 等 Adoption **后期**嵌入面。  
**最早:** **不得早于 V2 冒烟 Exit**（仓内发前钩子闸已立）。  
**不等于** V2 入站 check 已交付即平台完成；**不**替代大图谱/采编 CMS。

### Ticket: 图谱 / 全量采编 CMS（备选 · 非近端）
旧 Phase C 资产库叙事；仍标产品 Out 近端不做。另票评估前 **不**开实现。

### Frozen: Studio
| Lock | Rule |
|------|------|
| Workstations | 将来若做：研/写/审等 **全部强制穿同一 Gate** |
| Narrative | 面试不讲多 Agent / CrewAI 秀 |
| Schedule | **无代码、无日期**；解冻另决议 |

### Not scheduled
| Idea | 处理 |
|------|------|
| **#1** Claim Runtime | 仅内部/面试「发前流水线」说法，**不说 OS** |
| **#4** 对抗出版人 | 单攻击面 demo / 短论文；**非**近半年产品主线；**≠ I2** |
| **#7 / #9 / #10** | 暂不排期（#9 可在 V 稳定后评估） |
| **#3 / #5 / #6** | 已丢 |

---

## Cross-cutting（每阶段都生效）

**Hard rules**
- 只认已入库 T1；`web → 落盘 → 再复验`
- 对话不改正式裁决；ingest ≠ 事实正确（白名单/冲突/人审）
- 生产默认 BM25，直到 Hard-Gold **过线**（ADR-0033）且 Gate 实现票人终收改臂
- 对客主卖：改完立刻可再验 + 证据可导出 + 发前少翻车；少卖 Claim OS / 对抗平台 / 通用助手

**Always ship**
- 贡献清单随 I0 / V1 / I1 追加  
- 一票否决：表不会算 / 口径不一致 / 假样本 / 无安全三例 / 未入库当真理 / 深挖贡献清单穿帮

**代理与权限（L0 / L1 / L2）**
| 档 | 谁 | 例 |
|----|----|----|
| L0 | 自动 | 只读、可逆低影响 |
| L1 | Ronin 可代 | 改分支、提 PR、答澄清、定优先级、约定范围内代审 |
| L2 | 本人 | 外发消息、付费、生产破坏性、密钥/扩权、不可逆删除、**人终收类 issue** |

**Papers ↔ 模块（挂阶段，不另开第二产品）**

| 优先级 | Paper bet | Hang on | Venue 优先 |
|--------|-----------|---------|------------|
| **主投 · 路线 A** | **Evidence-bound / attested patch**（idea #2；系统论文，不装方法首创） | **V1.5** | **Findings / Industry / Demo**（对口可达、非保送）；Workshop 保底；**主会长文不当默认计划** |
| **保底短文** | Adversarial freshness（idea #4 · 单攻击面） | 可选 demo；**≠ I2 Exit** | Workshop / Demo |
| **替补** | Auditable verify pipeline | V1 + I1 | **仅当 V1.5 严重延期** 时升 Industry/Findings；**不占**保底短文位 |
| 旁 | Policy-as-code（#8） | thin；**≥ V1 Exit**；默认可与 V1.5 薄并行 | Industry / workshop 旁支 |
| 有数据再写 | Retrieval-for-verification；HumanLatch 误判语料 | Hard-Gold；I1 | findings / 资源向 |

**贡献口径（事实核查后 · 须遵守）**
- 可写的是 **组合协议**，不是单点发明：已入库 T1 才能裁定；`web→落盘→再验`；补丁必须引用 ⊆ 已入库 T1；人确认才落地；强制再验；对话不改正式裁决。
- Related Work 承认祖先（RARR / PAVE / 事实检查 / PCC 代码线等）；划清边界为「**发前新鲜度复验协议**」。
- **禁止**吹「首次带证据改稿」；**禁止**用 proof-carrying 对外装形式化 PCC。

**翻车点（论文/对外）**
- 名不副实 PCC；无 **C vs T** 对照；对话改正式裁决；吹首次；用 V1.5 叙事替代 I1 冲 mid。

**预实验协议（不等阶段 Exit 即可开记）**
- **对照：** C = 无证自由改写；T = 强制引用 ⊆ 已入库 T1 的补丁 + 人确认 + 立刻再验。
- **四指标：** 再验通过率、人审工时、误改率、证据完整性。
- **自 V1 起**记账 `patch_events`（人手补丁也算）：`claim_id` / `before_disp` / `patch_span` / `t1_ids` / `human_confirm` / `reverify` / `minutes` / `arm=C|T`。
- **样本量：** 先 ≥30（自用可）；冲 Findings 尽量 50–100。
- **消融（可选）：** 去人确认 / 去强制再验 / 允许对话改裁决。
- **#4：** 5–10 合成过期伪装样例 + Gate 拦层（可复用 I1 三分法）；与 I2 错峰、互不替代。
- **阶段咬合：** I0 表在仓 → V1 闭环并开始记账 → I1 ≥3 复盘+失败三分法进论文 → V1.5 主实验 → I2 安全三例（ACL+注入+投毒）；**冲 mid = I0+V1+I1+I2，不得用 V1.5 替代 I1**。

**8–12 周论文节奏锚点（非产品四周日历）**
| 周 | 锚点 |
|----|------|
| W1–2 | I0 + `patch_events` schema |
| W3–5 | V1 闭环 + 开始记账；#4 开造样例 |
| W6–7 | I1 样本 + Related Work 冻结 |
| W8–10 | V1.5 主实验（C vs T） |
| W11–12 | 投稿 Findings/Industry/Demo；I2 错峰 |

**Venue 备注（对个人，勿夸大）**  
Findings ≈ 顶会正规次主赛道；Industry ≈ 同会落地轨；对 mid 是加分背书非门票；大众知名度有限。

**双 SKU**
| SKU | 内容 |
|-----|------|
| Standard | 生产 BM25 + 全量审计契约 |
| High-Recall（可选） | 预算内二次检索；同一契约；改默认臂走 Hard-Gold |

---

## Legacy map（旧路线 → 本阶段）

| 旧 | 现 |
|----|----|
| Phase A | **Phase A · DONE** |
| Phase M（span/契约/导出等） | **并入 V1** 验收与文档，不单开 |
| Phase B 大部 | **B′ 按需** + **I1** 样本；Memory/多 Agent 不做主线 |
| Phase C 采编平台化 | **V2** 发前钩子/台账；全量平台与 C′ 插件 → Backlog |
| 旧「四周」日历 | **作废**（非物理约束） |

---

## Phase cheat-sheet（开发时看这张）

| Phase | You are building | Done when |
|-------|------------------|-----------|
| **① 卫生** | bare-pytest path | **DONE**（`pytest.ini` `pythonpath = .`） |
| **I0** | 数字与表 | **DONE**（`docs/evidence/i0/ACCEPTANCE.md`） |
| **V1** | 发前闭环（单垂直） | **DONE**（冒烟；`docs/evidence/v1/ACCEPTANCE.md`） |
| **I1** | 失败证据 | **DONE**（冒烟；`docs/evidence/i1/ACCEPTANCE.md`） |
| **V1.5** | Evidence-bound 补丁（表单） | **DONE**（冒烟；`docs/evidence/v15/ACCEPTANCE.md` · `V15-DoD-CLOSE.md`） |
| **I2** | 安全三例（ACL·注入·投毒） | **DONE**（冒烟；`docs/evidence/i2/ACCEPTANCE.md` · `I2-DoD-CLOSE.md`；≠ #4；ADR-0030） |
| **B′** | 修真痛点 / I3 夹具 | **I3 夹具并入**；真事故仍 on-demand |
| **V2** | 发前钩子+主张台账 | **DONE**（冒烟·采用层；`docs/evidence/v2/ACCEPTANCE.md` · `V2-DoD-CLOSE.md`；ADR-0031） |
| **I3** | #8 政策旁路 · B′夹具 · Hard-Gold骨架 | **DONE**（冒烟/面试加固；`docs/evidence/i3/ACCEPTANCE.md` · `I3-DoD-CLOSE.md`；ADR-0032；未换臂） |
| **Backlog** | C′ / 图谱·CMS / High-Recall / Studio / 改臂闸（流程钉·复跑未跑） | 另票或冻结；改臂见 ADR-0033 |

---

## 一句话

**I0 钉数字 → V1 发前闭环 → ① bare-pytest 卫生（DONE）→ 本地 V1 ACCEPTANCE → I1 失败样本（DONE）→ V1.5 Evidence-bound 补丁（DONE · 冒烟）→ I2 安全三例（DONE · 冒烟 · [#213](https://github.com/luxingjiang1993/FreshLatch/issues/213)）→ **V2 发前钩子+主张台账（DONE · 冒烟·采用层 · [#226](https://github.com/luxingjiang1993/FreshLatch/issues/226) · ADR-0031）** → **I3 面试加固三轨（DONE · 冒烟/面试加固 · [#248](https://github.com/luxingjiang1993/FreshLatch/issues/248) · ADR-0032 · `docs/evidence/i3/ACCEPTANCE.md`）** → **Hard-Gold 改臂闸（流程 DONE · [#257](https://github.com/luxingjiang1993/FreshLatch/issues/257) · ADR-0033；复跑未跑·未换臂）**；C′ 插件平台与图谱/CMS 仅 Backlog；#4 只做可选 demo；Studio 冻死；论文挂同一条发前闭环。**

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-09-28 | v1：RAG→M→Agent→C |
| 2026-09-28 | v2：I0→V1→I1→V1.5→I2→B′→V2；Studio 冻结 |
| 2026-09-28 | **v3**：阶段 In/Out/Exit；Verify+/差异化/论文；补丁（默认 V1→I1→V1.5、#8 earliest、I2≠#4、Legacy map、单垂直、L0–L2） |
| 2026-09-29 | **v3.1**：锁定论文路线 A（Evidence-bound/attested patch）；Papers↔模块（venue/贡献口径/预实验/8–12 周锚点/翻车点）；对外少用 proof-carrying |
| 2026-09-29 | **I0 DONE**：三件套+ADR-0026+评估；ACCEPTANCE 见 `docs/evidence/i0/ACCEPTANCE.md`；评估见 `docs/research/I0-冒烟层与数字真相源设计评估.md` |
| 2026-09-29 | **V1 grill DONE**：顾问报告+McK SoAI；包结论新层；薄 URL=`www.mckinsey.com`；评估见 `docs/research/V1-发前闭环垂直与包结论设计评估.md`；ADR-0027；下一跳 to-spec |
| 2026-09-29 | **V1 to-spec**：`docs/spec/11-PhaseV1-PrePublish.md`；GitHub [#168](https://github.com/luxingjiang1993/FreshLatch/issues/168) `ready-for-agent` |
| 2026-09-29 | **V1 DoD close（#175）**：五项 DoD 勾选；冒烟级关门摘要见 `docs/evidence/v1/V1-DoD-CLOSE.md`。不升格检索臂、不宣称 Hard-Gold。人终收 issue 未在本行代关。 |
| 2026-09-29 | **本期序 / I1 grill**：① bare-pytest 卫生；主烤 I1；ADR-0028；评估见 `docs/research/I1-失败三分法与HumanLatch语料设计评估.md` |
| 2026-09-29 | **① bare-pytest 卫生 DONE**：`pytest.ini` `pythonpath = .` |
| 2026-09-29 | **本地 V1 ACCEPTANCE**：`docs/evidence/v1/ACCEPTANCE.md`（I1-Q7 硬挡解除条件） |
| 2026-09-29 | **I1 DONE（冒烟）**：corpus `docs/evidence/i1/`（s001–s005）；`ACCEPTANCE.md`；#184–#188 CLOSED（Ronin 代批）；评估见 `docs/research/I1-失败三分法与HumanLatch语料设计评估.md`；ADR-0028；父规格 #183 收口 |
| 2026-09-29 | **V1.5 grill DONE**：表单 Evidence-bound；独立 propose/confirm；薄对话 Out；冒烟 Exit 预锁；评估见 `docs/research/V1.5-Evidence-bound补丁设计评估.md`；ADR-0029；[#195](https://github.com/luxingjiang1993/FreshLatch/issues/195) CLOSED；下一跳 to-spec |
| 2026-09-29 | **V1.5 to-spec**：`docs/spec/12-PhaseV1.5-EvidenceBound.md`；GitHub [#196](https://github.com/luxingjiang1993/FreshLatch/issues/196) `ready-for-agent` |
| 2026-09-29 | **V1.5 to-tickets**：#197–#203 `ready-for-agent`（#204 重复已关）；enrich 齐；清单 `.scratch/v15-tickets/INDEX.md` |
| 2026-09-29 | **V1.5 云端派工待 Ronin**：`docs/agents/phase-v15-cloud-dispatch.md`；须 #196 `GROK-PROXY-APPROVED V1.5-DISPATCH` 后启 Cloud |
| 2026-09-29 | **V1.5 实现波 #197–#202**：patch_events before/after · propose/confirm · 再验 · UI 条带 · 导出 · e2e+ACCEPTANCE；PR #205–#210 合 main；Ronin 代批齐关 |
| 2026-09-29 | **V1.5 DoD close（#203）**：冒烟级关门摘要见 `docs/evidence/v15/V15-DoD-CLOSE.md`；硬 Exit 引用 ACCEPTANCE；Out 未偷渡（薄对话/扩 latch/C\|T UX/Exit 硬绑可发）；不升格 Hard-Gold；`GROK-PROXY-APPROVED #203`；#203 CLOSED |
| 2026-09-29 | **V1.5 DONE（冒烟）**：#197–#203 CLOSED（Ronin 代批）；PR #205–#211 合 main；父规格 #196 收口；下一主烤 **I2** |
| 2026-09-29 | **I2 grill DONE**：Exit=安全三例（越权·注入·投毒）；分层硬门；#4 可选≠Exit；评估见 `docs/research/I2-安全三例设计评估.md`；ADR-0030；roadmap I2 完整对齐三例；下一跳 to-spec |
| 2026-09-29 | **I2 to-spec**：`docs/spec/13-PhaseI2-SecurityDemos.md`；GitHub [#213](https://github.com/luxingjiang1993/FreshLatch/issues/213) `ready-for-agent`；主缝=召回信任边界+绿灯出口 |
| 2026-09-29 | **I2 to-tickets**：#214–#219 `ready-for-agent`；清单 `.scratch/i2-tickets/INDEX.md`；Frontier #214/#215/#216 |
| 2026-09-29 | **I2 enrich-tickets**：#214–#219 Agent Guards 齐（Paths/Provenance pass）；Frontier 同上 |
| 2026-09-29 | **I2 云端派工**：`docs/agents/phase-i2-cloud-dispatch.md` + `phase-i2-cloud-prompts.md`；人审全权 **Ronin**；启动闸=`GROK-PROXY-APPROVED I2-DISPATCH` @ #213 |
| 2026-09-29 | **I2 实现波 #214–#218**：ACL+poison · 注入 Gate · security.md · 注入 1× e2e+ACCEPTANCE；PR #220/#221/#223/#224 合 main；Ronin 代批齐关（#216 可选） |
| 2026-09-29 | **I2 DoD close（#219）**：冒烟级关门摘要见 `docs/evidence/i2/I2-DoD-CLOSE.md`；硬 Exit 引用 ACCEPTANCE+security.md；Out 未偷渡；不升格渗透认证/Hard-Gold |
| 2026-09-30 | **B′ 延后**：无真痛点先不做；挂 BACKLOG（on-demand 待命）；**不挡 V2**；下一跳改为 **V2** |
| 2026-09-30 | **V2 grill DONE**：发前钩子（Memo UI+CLI + 入站 check）+ 主张台账只读投影；冒烟 Exit 预锁；评估见 `docs/research/V2-发前钩子与主张台账设计评估.md`；ADR-0031；Backlog 补 C′/图谱·CMS；下一跳 to-spec |
| 2026-09-30 | **V2 to-spec**：`docs/spec/14-PhaseV2-PublishHook.md`；GitHub [#226](https://github.com/luxingjiang1993/FreshLatch/issues/226) `ready-for-agent`；主缝=发前钩子放行边界 |
| 2026-09-30 | **V2 to-tickets**：#227–#232 `ready-for-agent`；清单 `.scratch/v2-tickets/INDEX.md`；Frontier #227/#228 |
| 2026-09-30 | **V2 enrich-tickets**：#227–#232 Agent Guards 齐（Paths/Provenance pass）；Frontier 同上 |
| 2026-09-30 | **V2 实现波 #227–#231**：闸核心 · 台账 · Memo 套闸 · 入站 check · e2e+ACCEPTANCE；PR #233–#237 合 main；Ronin 代批齐关 |
| 2026-09-30 | **V2 DoD close（#232）**：冒烟·采用层关门摘要见 `docs/evidence/v2/V2-DoD-CLOSE.md`；硬 Exit 引用 ACCEPTANCE；Out 未偷渡（无平台/图谱/双写/商业裁决/整包再验挂钩子/改臂/Studio）；curl ≠ 平台已交付；不升格 Hard-Gold |
| 2026-10-03 | **I3 grill DONE**：整合 #8+B′夹具+Hard-Gold骨架；一阶段三轨；不改臂；出处禁区旁路；评估见 `docs/research/I3-面试加固三轨设计评估.md`；ADR-0032；下一跳 to-spec |
| 2026-10-03 | **I3 to-spec**：`docs/spec/20-PhaseI3-InterviewHardening.md`；GitHub [#248](https://github.com/luxingjiang1993/FreshLatch/issues/248) `ready-for-agent`；下一跳 to-tickets |
| 2026-10-03 | **I3 to-tickets + enrich**：#249–#253 `ready-for-agent`；清单 `.scratch/i3-tickets/INDEX.md`；Frontier #249 |
| 2026-10-02 | **I3 实现波 #249–#252**：政策旁路 · B′夹具 · Hard-Gold骨架 · ACCEPTANCE；PR #254–#256 + ACCEPTANCE 合 main；Ronin 代审中 |
| 2026-10-02 | **I3 DoD close（#253）**：冒烟/面试加固关门摘要见 `docs/evidence/i3/I3-DoD-CLOSE.md`；硬 Exit 引用 ACCEPTANCE；Out 未偷渡；骨架 ≠ 换臂；夹具 ≠ 真事故；不升格政策平台 |
| 2026-10-03 | **Hard-Gold 改臂闸 grill DONE（#257）**：过线=dense+hard 臂对比+Hybrid@hard；过线才 Gate 实现票；本波不换臂；评估见 `docs/research/Hard-Gold过线与改臂决议设计评估.md`；ADR-0033；证据 `docs/evidence/hard-gold-arm/`；下一跳 dense+hard 复跑票 |
| 2026-10-03 | **Hard-Gold 过线复跑（#258）**：dense ok；hard 臂对比通过线 fail（BM25 vs A0）；Rerank 关；**不过线 · 冻 bm25 · 未换臂**；书面结论 `docs/evidence/hard-gold-arm/RERUN-20261003.md` |
| 2026-10-03 | **Hard-Gold 同库复跑（#259）**：corpus+traps；dense=94；原门 Hybrid@hard **pass**；Rerank 关；**过线 · 未换臂**；书面结论 `docs/evidence/hard-gold-arm/RERUN-20261003-259.md`；下一跳 Gate 改臂实现票 |