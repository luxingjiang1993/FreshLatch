# FreshLatch Roadmap v3.1（阶段版）

> 状态：执行版（2026-09-29 修订 · 论文路线 A）。  
> 相对 v2：按阶段 In/Out/Exit 重排；补入 Verify+/Studio 嵌套、差异化短名单、论文挂点、客户对客话术；并应用核查补丁（默认序、#8 锚点、I2≠#4、Legacy map、单垂直、L0–L2）。
> 2026-09-29：锁定论文路线 A（Evidence-bound / attested patch → V1.5）；补全「论文↔模块」预实验与 venue。  
> 备份：`/workspace/freshlatch-roadmap.v2-backup.md`（及更早的 v1-backup，若仍在）。
> Grill 前置：开 `grill-with-docs` 前先读 [grill-prep.md](./grill-prep.md)（阅读包 + 待钉决策）。


**North star:** 已签发主张必须「现在仍可复验」；无 T1 不得绿灯；人决定作废/续命。  
**Shape:** `Gate ⊂ Verify+ ⊂ Studio` · 近端只做 Verify+ · Studio 冻结  
**Cadence:** 一人同时只开 **一条** 阶段（V 或 I）；无固定四周日历  
**Bar:** 冲 mid = 数字 + 失败样本 + 安全一例 + 口述，不靠 UI  
**代理:** 仓库变更按 L0/L1/L2（Ronin 可代 L1；**人终收类如历史 #166 不代批/代关**）；超时或证据不足 fail-closed。

```
DONE: Phase A · Phase I0 · V1 grill
NOW → NEXT:
  Phase V1 (to-spec → tickets → implement) → Phase I1 → Phase V1.5 → Phase I2
  → Phase B′ (on-demand) → Phase V2
BACKLOG: Hard-Gold ticket | Policy-as-code (#8) | Studio (frozen)
```

**默认阶段序（钉死）：** `V1 → I1 → V1.5`。  
**唯一例外：** 自用痛点明确是「改稿再验」时，允许 V1 后先开 V1.5；**冲 mid 仍以 I1 为准**，不得用 V1.5 替代 I1。

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

## Phase V1 — Pre-publish loop · **GRILL DONE · NEXT = to-spec**

**Goal:** 一条可演示的发前路径：入库 → Gate → 包结论 → 人审 → 两屏。  
**Track:** V · **Depends on:** I0 DONE  
**决议:** ADR-0027；评估见 `docs/research/V1-发前闭环垂直与包结论设计评估.md`

| | |
|--|--|
| **In** | **单一垂直=顾问报告**（McK SoAI 03→11 样例包）；T1 落盘（checksum）；三卡+薄 URL（`www.mckinsey.com`）；Gate；包结论新层；作废/续命；两屏（列表新建+复验单详情）；**`patch_events` JSONL 起记**（后台 C/T） |
| **Out** | **多垂直并行**；难金标；High-Recall 改默认；Studio；薄对话/厚对话改裁决；开放爬虫 |
| **Exit** | 真实发前路径可 demo；轨迹追到 T1 checksum；包结论与金标/闸口径一致 |

**Definition of Done**
- [ ] 未归档不得定论  
- [ ] 报告级 disposition 可追责  
- [ ] 人审路径走通  
- [ ] 单一垂直已写进文档/README（决议已钉；README 随 to-spec/实现勾）  
- [ ] `patch_events` schema 已落并开始记账  

---

## Phase I1 — Failure taxonomy + HumanLatch corpus · **MID UNLOCK**

**Goal:** 把「能跑」变成「能答辩错在哪层」。  
**Track:** I · **Depends on:** V1 · **默认在 V1.5 之前**

| | |
|--|--|
| **In** | 失败三分法接门禁（找不到/找错/没用上）；≥3 条漏拦/误拦复盘 |
| **Out** | 新功能大项；编造无复盘样本 |
| **Exit** | 指着样本讲清闸错层级 + ≥1 可复跑 case |

---

## Phase V1.5 — Evidence-bound / attested patches · **CUSTOMER WEDGE**

**Goal:** 改稿带证据、人确认后应用、可立刻再验。  
**Track:** V · **Depends on:** V1；**默认在 I1 之后**（例外见文首）  
**Maps to idea #2（对客主卖点 · 论文主投路线 A）**

**对外用语：** evidence-bound / attested patch（**少用** proof-carrying，易撞形式化 PCC）。

| | |
|--|--|
| **In** | 基于已入库证据的 diff；补丁引用证据；薄对话只解释/触发生成；人确认才应用 |
| **Out** | 开放问答；对话改正式裁决；编辑器秀 |
| **Exit** | 「改 → 确认 → 再验」闭环可 demo；证据可导出 |

**Note:** 不定 mid 生死；冲 mid 仍靠 I0+V1+I1+I2，**不得用本阶段替代 I1**。对客尖刀 + 论文主投实验在本阶段。

---

## Phase I2 — Security demos · **INTERVIEW SAFETY ROUND**

**Goal:** ACL + 间接注入/投毒各一例可演示。  
**Track:** I · **Depends on:** 不晚于对外主叙事；可与 V1.5 错峰  

| | |
|--|--|
| **In** | 越权召回失败测例；投毒/注入样例 + 防护；`docs/security.md` 一行表 |
| **Out** | 安全平台；多攻击面大而全；**用 #4 对抗出版人替代本阶段** |
| **Exit** | 上述 **两条** demo 可复现（口头不算） |

**I2 ≠ #4：** Idea **#4**（过期伪装 / 出版对抗、单攻击面红蓝）是 **可选面试弹药 / 短论文**，**不计入 I2 Exit**，二者互不替代。

---

## Phase B′ — Agent hardening · **ON-DEMAND ONLY**

**Goal:** 修真实演示/人审事故，不为「像生产」空转。  
**Depends on:** V1 + I1 之后出现痛点

| Trigger | Work |
|---------|------|
| 演示卡死/假绿 | timeout / retry / 结构化错误 |
| 人审重放出事 | 串行幂等 / 重入 |
| 说不清闸分布 | 轨迹 → 一页观测 |

**Out:** Memory 大叙事、多 Agent 拓扑、跨 Provider 对照作硬关门。

---

## Phase V2 — Embed + ledger · **ADOPTION**

**Goal:** 「要发了」多一步被采用；主张历史可查。  
**Track:** V · **Depends on:** V1 可信 · **不与** I0–I2 抢带宽

| | |
|--|--|
| **In** | ≥1 嵌入钩子（导出/打包前复验）；主张 ID 作废/续命列表 |
| **Out** | 大图谱；全量采编平台（旧 Phase C） |
| **Exit** | 钩子被真实工作流点到一次以上（自用也算） |

---

## Backlog · **SEPARATE TICKETS / FROZEN**

### Ticket: Hard-Gold + arms gate（另票 · 必单列）
过难金标 + 分列评测增益门 → 才讨论改生产默认（dense/hybrid/rerank）。  
**不等于** 旧 Phase B；**不挡** V1。

### Ticket: High-Recall SKU（可选）
预算内二次检索；同一审计契约；默认臂变更仍走 Hard-Gold。

### Ticket: Policy-as-code thin slice（idea **#8**）
禁区规则进 Gate；挂 Verify+ 旁路；**勿**单独立项做大平台。  
**Earliest:** **不得早于 V1 Exit**。  
**默认挂点:** I1 之后，或与 V1.5 **并行薄切片**；**不抢 V1**。

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
- 生产默认 BM25，直到 Hard-Gold 过线
- 对客主卖：改完立刻可再验 + 证据可导出 + 发前少翻车；少卖 Claim OS / 对抗平台 / 通用助手

**Always ship**
- 贡献清单随 I0 / V1 / I1 追加  
- 一票否决：表不会算 / 口径不一致 / 假样本 / 无安全 demo / 未入库当真理 / 深挖贡献清单穿帮

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
- **阶段咬合：** I0 表在仓 → V1 闭环并开始记账 → I1 ≥3 复盘+失败三分法进论文 → V1.5 主实验 → I2 ACL+注入/投毒；**冲 mid = I0+V1+I1+I2，不得用 V1.5 替代 I1**。

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
| Phase C 采编平台化 | **V2** 嵌入/台账；全量平台后置 |
| 旧「四周」日历 | **作废**（非物理约束） |

---

## Phase cheat-sheet（开发时看这张）

| Phase | You are building | Done when |
|-------|------------------|-----------|
| **I0** | 数字与表 | **DONE**（`docs/evidence/i0/ACCEPTANCE.md`） |
| **V1** | 发前闭环（单垂直） | 一条路径可追责 demo |
| **I1** | 失败证据 | 样本讲清分层 |
| **V1.5** | Evidence-bound 补丁 | 改→确认→再验 |
| **I2** | ACL + 注入/投毒 | 两 demo 可复现（≠ #4） |
| **B′** | 修真痛点 | 触发条件消失 |
| **V2** | 嵌入+台账 | 钩子进工作流 |
| **Backlog** | 金标 / #8 / Studio | 另票或冻结 |

---

## 一句话

**I0 钉数字 → V1 单垂直发前闭环 → I1 失败样本 → V1.5 Evidence-bound 补丁（对客/主投尖刀）→ I2 安全两例 → B′/V2 按需；#8 薄挂且不早于 V1；#4 只做可选 demo；Studio 冻死；难金标另票；论文挂同一条发前闭环。**

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
