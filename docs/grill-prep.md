# Grill 前置阅读清单 + 待钉决策清单

> 用途：开 `grill-with-docs` / `grilling` 前给 coding agent 与你自己用。  
> 配套执行路线图：`docs/roadmap.md`（v3.1）。  
> 开场提示词模板：[prompts/grill-with-docs-freshlatch.md](./prompts/grill-with-docs-freshlatch.md)

> 原则：路线图定阶段与边界；本页定「读什么」和「必须先烤死什么」——**未钉死前不要 implement V1**。

---

## 0. 会话怎么开

1. 先读完 §1 阅读包（agent 可自行打开仓内文件；找得到的事实不要问用户）。  
2. 以 `docs/roadmap.md` 为设计树根。  
3. 本页 §2 是 **第一轮 frontier 推荐题**（可整轮抛出）；§3 是后续轮才解封的题。  
4. 每轮产出：更新本页勾选 + 必要时写 ADR / glossary（`grill-with-docs` → grilling + domain-modeling）。  
5. **共享理解确认前**：不改产品代码；I0 纯文档/表可与 grill 并行。

---

## 1. 前置阅读包（按顺序）

### 必读（开 grill 前）

| # | 路径 / 对象 | 读什么 |
|---|-------------|--------|
| 1 | `docs/roadmap.md` | 阶段序、In/Out/Exit、硬边界、论文路线 A、`patch_events` 意图 |
| 2 | 本文件 | 待钉决策；避免重复发明问题 |
| 3 | Phase A retrieve / Gate 相关 **现有 spec 或 ADR**（`docs/spec/`、`docs/adr/`、`docs/verification/` 内与 retrieve、gate、disposition、金标相关者） | 现有枚举与契约，防 V1 另起一套口径 |
| 4 | 现成 **eval / 金标 / 评测报告**（仓内 `docs/evidence/`、`docs/task-completion/` 或 eval 脚本产物；以实际文件名为准） | I0「为何 BM25」的数字从哪来、能否复跑 |
| 5 | HumanLatch / 人审相关文档或代码入口 | I1 样本与状态机别悬空 |

### 强烈建议（第一轮后、写 V1 前）

| # | 对象 | 读什么 |
|---|------|--------|
| 6 | Lead / Critic 调用 retrieve 的约束（代码或 agent 文档） | 「Agent 不可自选 retrieval_mode」是否仍真 |
| 7 | 入库 / T1 / checksum 现有实现（若有） | V1 是接上还是新建 |
| 8 | UI 现状（若有发前相关屏） | 两屏是增量还是从零 |

### 对照即可（勿当执行序）

| # | 对象 | 注意 |
|---|------|------|
| 9 | `docs/roadmap.md.v-prev-backup.md`（若存在） | 旧 A/M/B/C 叙事；**以 v3.1 为准** |
| 10 | GitHub `luxingjiang1993/FreshLatch` 远程 | 仅当本地与远程不一致时核对；执行以本地「蓝海项目5」为准 |

### Agent 自查清单（读完应能回答）

- [ ] 生产默认检索臂是什么？评测臂有哪些？  
- [ ] 「未入库不得绿灯」在现有代码/文档里如何表述？  
- [ ] 现有 disposition / 闸结果枚举叫什么？  
- [ ] 金标或 eval 的复跑入口在哪？  
- [ ] 人审（HumanLatch）现在走到哪一步？  

答不出 → 先补读或在 grill 里标「未知事实」，不要猜着写 V1。

---

## 2. 第一轮待钉决策（Frontier · 建议一次问完）

> 格式对齐 grilling：每题给推荐答案；你改或认后勾选。

### Q1 — 单一垂直锁定

**问题：** V1 只做一个垂直：顾问报告 / 研报 / 合规对外口径，选哪一个？买家画像与样例主张从哪来？

**推荐：** 选你最容易自用、能稳定产出「已签发主张」的那一个；默认倾向 **合规对外口径** 或 **顾问报告**（二者谁已有真实文档就选谁）。研报若样本难搞可后置。

- [x] 已钉（2026-09-29）：**顾问报告**；样例主包 = McKinsey State of AI（**T0≈2025-03 rewiring** → **T1≈2025-11 agents**）；仓内只存主张+摘录+出处，不整本镜像 PDF  
- [x] ADR/glossary 已记（ADR-0027 · CONTEXT · 评估文档）  

---

### Q2 — V1 两屏信息架构

**问题：** 「发前列表」必显哪些列？「Run 详情」必显哪些块（主张、T1、证据、闸结果、包结论、人审动作）？

**推荐：**  
- 列表：标题/来源、包结论、更新时间、Run 状态  
- 详情：原文摘要、T1 checksum 列表、逐条闸结果、包级 disposition、人审作废/续命、轨迹链接  

- [x] 已钉（2026-09-29）：列表新建；详情 = 现有复验单 + 包结论条（增量，非三套 UI）  
- [x] 与现有 UI 关系：**增量**（复验单改造成 Run 详情）

---

### Q3 — 包结论 ↔ 现有闸 / 金标口径

**问题：** 包级「可发 / 需补丁 / 勿发」如何由条文闸结果聚合？与现有枚举是否一一映射还是新层？

**推荐：** **新层聚合，底层枚举不改名**；写一张映射表进 ADR，禁止 V1 UI 发明第四套状态词。

- [x] 已钉：新层聚合；边界见 §2d Round 2 Q15；**ADR-0027 已落**  
- [x] 金标用例抽 1 条验证映射（#174 `test_prepublish_e2e` / ADR-0027）  

---

### Q4 — T1 入库范围（V1 最小）

**问题：** V1 支持哪些源？URL 抓取？本地文件类型？失败/重复/冲突如何呈现？

**推荐：** V1 最小 = **本地文件（md/txt/pdf 择已有解析能力）+ 可选单个 URL**；冲突 → 待人审，不自动绿灯。

- [x] 已钉源类型列表（2026-09-29）：现有三卡（md 上传 / 粘贴确认 / 合成）+ **(c′) 薄 URL**，白名单域名 **仅** `www.mckinsey.com`；失败显式错误并可回落粘贴；**不做**开放爬虫 / 多源平台  
- [x] 失败态已列：非白名单 / 超时或网络错 / 非文本或空正文 / 落盘前校验失败 → 不入库，可回落粘贴（Round 2）  

---

### Q5 — `patch_events` schema（V1 起记）

**问题：** 落盘格式（JSONL / DB 表）？字段是否就用路线图所列？人手补丁如何录入？

**推荐：** 先 **JSONL** 于 `data/patch_events/`（或仓内约定目录）；字段最少：

`claim_id, before_disp, patch_span, t1_ids, human_confirm, reverify, minutes, arm=C|T, ts, actor`

人手补丁走同一 schema，`arm` 先标 `C` 或手工 `T`。

- [x] schema 约定路径：`data/patch_events/`（JSONL；文件随 to-spec/实现提交）  
- [ ] 示例一行已提交  

---

### Q6 — I0 与 V1 的硬依赖

**问题：** I0 Exit 是否 **硬挡住** V1 开工，还是「建议先过」可并行？

**推荐：** **文档任务可并行**；V1 **合并/对外 demo 前** I0 必须 Exit（表在仓且你能闭卷算）。编码 agent 可先搭 V1 骨架，但不得宣称发前主叙事完成。

- [x] 已钉：文档/骨架可并行；**V1 merge 或对外 demo 叙事前**必须 I0 Exit（2026-09-29 I0 grill Round 1；I0 已 DONE）

---

### Q7 — 论文记账是否从第一天侵入产品 UX

**问题：** C vs T 对照是否进 UI，还是仅后台/脚本记账？

**推荐：** V1 **只后台记账**；C vs T 切换不进正式发前 UX（避免产品变成实验台）。实验脚本读写同一 JSONL。

- [x] 已钉（2026-09-29 Round 2）：V1 **只后台记账**；C vs T 不进正式发前 UX  


> 用途：回答「能不能找网上可用材料」；**未**自动下载进仓（版权/体积/二次分发另决）。  
> 优先可公开打开的洞察页/PDF 链接作 T0/T1 来源登记；仓内只保留摘录+出处，不整本镜像侵权分发。

### 档 A · MBB / 顶咨（顾问报告垂直 · 用户点名档）

| ID | 机构 | 材料 | 入口 |
|----|------|------|------|
| **McK-SoAI-2025** | McKinsey | *The state of AI in 2025: Agents, innovation, and transformation*（2025-11） | [洞察页](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai) · [PDF](https://www.mckinsey.com/~/media/mckinsey/business%20functions/quantumblack/our%20insights/the%20state%20of%20ai/november%202025/the-state-of-ai-2025-agents-innovation_cmyk-v1.pdf) |
| **McK-SoAI-Mar2025** | McKinsey | *How organizations are rewiring to capture value*（2025-03；同系列前一波） | [洞察页](https://www.mckinsey.com/capabilities/quantumblack/our%20insights/the-state-of-ai-how-organizations-are-rewiring-to-capture-value) · [PDF](https://www.mckinsey.com/~/media/mckinsey/business%20functions/quantumblack/our%20insights/the%20state%20of%20ai/2025/the-state-of-ai-how-organizations-are-rewiring-to-capture-value_final.pdf) |
| **McK-Agentic** | McKinsey | *Seizing the agentic AI advantage*（2025-06） | [PDF](https://www.mckinsey.com/~/media/mckinsey/business%20functions/quantumblack/our%20insights/seizing%20the%20agentic%20ai%20advantage/seizing-the-agentic-ai-advantage-june-2025.pdf) |
| **McK-GenAI-Frontier** | McKinsey / MGI | *The economic potential of generative AI*（经典生产力边界数字，易过期） | [PDF](https://www.mckinsey.com/~/media/mckinsey/business%20functions/mckinsey%20digital/our%20insights/the%20economic%20potential%20of%20generative%20ai%20the%20next%20productivity%20frontier/the-economic-potential-of-generative-ai-the-next-productivity-frontier.pdf) |
| **BCG-AI-Value** | BCG | AI Adoption 2024（74% struggle to scale value）等 | [例](https://www.bcg.com/press/24october2024-ai-adoption-in-2024-74-of-companies-struggle-to-achieve-and-scale-value) · [AI at Work 2025](https://www.bcg.com/publications/2025/ai-at-work-momentum-builds-but-gaps-remain) |
| **Bain-Tech-2025** | Bain | Technology Report 2025 专题页 | [入口](https://www.bain.com/insights/topics/technology-report) |

### 档 B · 同「高大上」邻档（非 MBB 但面试够硬）

| ID | 机构 | 材料 | 入口 |
|----|------|------|------|
| **HAI-2025** | Stanford HAI | *AI Index Report 2025*（引用 McKinsey survey 数字，开源友好） | [PDF](https://hai-production.s3.amazonaws.com/files/hai_ai_index_report_2025.pdf) |
| **WEF / IMF 类** | 多边 | 年度 AI/数字经济报告（按需再钉单份） | 官方站点检索 |

### 档 C · 合规官方（上一轮；可作辅包，非用户本轮主诉求）

BOI / GenAI 暂行办法 / 个保审计办法 — 见会话记录；适合 `regulatory_stance`，档次是「监管原文」不是「顶咨品牌」。

### 与 Q4（c′）耦合 — **已钉 2026-09-29**

| 语料策略 | Q4 | 状态 |
|----------|-----|------|
| **顾问报告 + McKinsey State of AI（T0=2025-03 → T1=2025-11）** | **(c′) 白名单仅 `www.mckinsey.com`** | **已钉**；失败→显式错+粘贴回落；不扩第二生产域名 |

**版权纪律：** V1 仓内只存「已签发主张清单 + 摘录块 + 来源 URL/日期」；禁止把整本 McKinsey PDF 当开源数据集再分发。

---

## 2d. V1 grill Round 1 已钉摘要（2026-09-29）

| # | 拍板 |
|---|------|
| Q1 | 垂直=顾问报告；主包 McK SoAI T0=2025-03 / T1=2025-11 |
| Q2 | 发前列表新建；Run 详情=复验单+包结论条 |
| Q3 | 包结论=新层聚合；底层 fresh/stale/unknown/void 不改名 |
| Q4 | 三卡 + c′ URL；白名单 `www.mckinsey.com` |
| Q5 | JSONL `data/patch_events/` + roadmap 字段 + ts/actor |
| Q6 | I0 已 DONE，不挡 V1 |

### Round 2（2026-09-29 · 认推荐）

| # | 拍板 |
|---|------|
| Q7 | C vs T **只后台 JSONL**；发前 UI 无开关 |
| Q15 | 包映射：未收口 stale→勿发；有 unknown→需补丁；**全 fresh 无人审→可发**；红灯人审收口且无未处理 unknown→可发 |
| Q16 | URL 失败四态：非白名单 / 超时网络 / 非文本或空 / 落盘前校验失败 → 不入库，可回落粘贴；PDF URL 另票 |
| Q17 | V1 **不做**薄对话（留 V1.5）；禁对话改 disposition |
| Q18 | **开 ADR-0027**（垂直+包结论新层+薄 URL 白名单，一条短 ADR） |

**待共享理解确认后落盘：** ~~ADR-0027 · 评估 · CONTEXT~~ → **已落盘（2026-09-29 共享理解确认）**

**已落盘（V1 决议）:**  
`docs/adr/0027-v1-顾问报告垂直包结论与薄URL.md` · `docs/research/V1-发前闭环垂直与包结论设计评估.md` · CONTEXT 词条

**共享理解再确认（2026-09-29）：** V1 决议枝全部仍成立。  
**纠偏（2026-09-29）：** 本期主烤 **Phase I1**（已 grill DONE · corpus/Exit 已齐）。  
**下一跳:** Phase I2（安全两例）；V1.5 Exit 已齐见 `docs/evidence/v15/ACCEPTANCE.md` · `V15-DoD-CLOSE.md`。  
**主缝（I1）：** 失败三分法 ↔ 闸层 ↔ 可复盘样本（ADR-0028）。

---

## 2e. I1 grill · Round 1–2 已钉（2026-09-29）

### Round 1（混选）

| # | 拍板 |
|---|------|
| **I1-Q1** | **(c)**：本地 **V1 Exit 证明齐** 才碰 I1 实现/落样本/宣称 Exit；grill 与决议文档可先完成 |
| **I1-Q2** | **(b) 全链视角**：找不到 / 找错 / 没用上 = retrieve · Lead/Critic 用证 · Gate/人审收口 三桶 |
| **I1-Q3** | **(b)**：eval/轨迹挂标签；**生产** Gate / disposition / HumanLatch 动词 **不改枚举** |
| **I1-Q4** | **(c)**：重标 W4/假绿+轨迹 ≥3；V1 顾问垂直/McK **≥1** 可复跑金样 |
| **I1-Q5** | **(a)+(b)**：`docs/evidence/i1/` 每条一页 **且** JSONL + 短索引 md |
| **I1-Q6** | **(a)**：①卫生先关；grill 可并行；写码/落样本挡卫生 Exit 后，且仍受 Q1 约束 |

### Round 2（全认推荐 · 2026-09-29）

| # | 拍板 |
|---|------|
| **I1-Q7** | **(c)**：另写 `docs/evidence/v1/ACCEPTANCE.md`（对照 I0）；含 disposition 映射抽检、patch_events 一行、默认臂仍 bm25、人审走通；远程 CLOSED ≠ 自动 Exit |
| **I1-Q8** | **(a)** 采纳默认层映射表（找不到→retrieve/T1；找错→错段或点错证；没用上→Gate/HumanLatch 未收口） |
| **I1-Q9** | **(c)**：漏拦/误拦按金标或人终审定义；**每条必须**同时打三分法一桶（复盘主键 = 漏\|误 × 桶） |
| **I1-Q10** | **(a)**：JSONL 最少字段见下；路径 **`docs/evidence/i1/events.jsonl`** |
| **I1-Q11** | **(c)**：优先可复跑命令+显式 decoding；无 Key 可 `runnable=replay_trace_only`，**不得**作唯一 Exit 金样 |
| **I1-Q12** | **(a)**：开短 ADR；评估文档四件套；见下方 Anthropic 修正 |

**JSONL 最少字段：**  
`sample_id, claim_id, gold_or_human, machine_status, package_disp?, fail_bucket, err_kind, layer, trajectory_ptr, evidence_md, runnable, ts, actor`

**本期序（叠约束）：** ① bare-pytest 卫生 **DONE** → 本地 V1 Exit（`docs/evidence/v1/ACCEPTANCE.md`）**DONE** → I1 to-spec / 落 corpus / implement **DONE**（`docs/evidence/i1/ACCEPTANCE.md`；#183 CLOSED）。

**Anthropic 清单修正（合入拍板）：**
1. I1 corpus / 三分法标签 = **答辩·冒烟层**，文首声明；不报统计显著/方差。  
2. 可复跑金样须显式记录模型/temperature/seed/日期；托管漂移写入 ACCEPTANCE。  
3. **词表：** `找不到/找错/没用上` 与 `漏拦/误拦` 为 **评测/答辩标签**，生产判不出 → **不进 CONTEXT 产品词表正文**；CONTEXT 仅留「I1 失败复盘（评测标签）」指针 + corpus 路径；细则进 ADR/评估。  
4. Exit 判据本轮预锁（HARKing 禁事后改桶定义凑样本）。

**Frontier：** 已空。  
**共享理解:** 已确认（2026-09-29）。  

**已落盘:**  
`docs/research/I1-失败三分法与HumanLatch语料设计评估.md` · `docs/adr/0028-i1-失败三分法评测标签与语料.md` · CONTEXT 评测区指针  

**下一跳:** Phase I2（V1.5 Exit 已齐：`docs/evidence/v15/ACCEPTANCE.md`；父规格 #196 CLOSED）。

---

## 2f. V1.5 grill · Evidence-bound / attested patches（2026-09-29）

### Round 1（全认推荐）

| # | 拍板 |
|---|------|
| **V15-Q1** | **(a)** 整条主张正文替换 + 必填 `t1_ids`（⊆ 已入库 T1） |
| **V15-Q2** | **(a)** 增量挂复验单/Run 详情（提案→确认→再验条带） |
| **V15-Q3** | **(b)** Exit=**表单闭环**；薄对话不挡 Exit |
| **V15-Q4** | **(b)** 主张级入口（与包结论解耦）；非「仅需补丁横幅」 |
| **V15-Q5** | **(a)** 独立 Verify+ `propose_patch`/`confirm_patch`；**不扩** HumanLatch `discard\|renew`；确认后强制再验；`patch_events.arm=T` |
| **V15-Q6** | **(a)** Fail-closed：空或不在已入库 T1 → 拒绝确认 |
| **V15-Q7** | **(a)** Exit=冒烟 demo+导出；**n≥30 不挡** Exit；文首冒烟声明 |
| **V15-Q8** | **(a)** 单次补丁导出包（before/after、`t1_ids`+指针、确认者、再验前后 disposition） |

### Round 2（全认推荐 · 含 Anthropic 预锁）

| # | 拍板 |
|---|------|
| **V15-Q9** | **(a)** 薄对话本期 **Out**（不实装、不 stub；评估/ADR 留位） |
| **V15-Q10** | **(a)** confirm 后只重跑被补丁主张 → 再聚合包结论 |
| **V15-Q11** | **(b)** 可提案 = 未 discard 的 `unknown` **或** `stale`；`void`/`fresh` 不可 |
| **V15-Q12** | **(a)** 本 Run 已入库 T1 的 `evidence_id` 多选 + 硬闸 |
| **V15-Q13** | **(a)** 原地覆盖 `statement`；`before_text`/`after_text` 进 `patch_events`（schema 增列） |
| **V15-Q14** | **(a)** Exit 脚本：discard mck-1&4 → 需补丁 → patch mck-3 → 确认 → 单条再验 → 导出 |
| **V15-Q15** | **(a)** 开 ADR-0029（共享理解确认后落） |
| **V15-Q16** | **(a)** #8 不并行 |
| **V15-Q17** | **(a)** `docs/evidence/v15/ACCEPTANCE.md` |
| **V15-Q18** | **(a)** 确认时人手填 `minutes` |
| **Anthropic** | Exit=冒烟层；禁单次报 C vs T 显著；Evidence-bound 词进 CONTEXT、论文 n/四指标进评估；Q14 脚本预锁禁 HARKing |

### Round 3（全认推荐 · 收束）

| # | 拍板 |
|---|------|
| **V15-Q19** | **(a)** 导出 = JSON + 短 Markdown |
| **V15-Q20** | **(a)** propose 仅 Run/会话暂存；未 confirm 不改正文、不写正式 `patch_events` |
| **V15-Q21** | **(a)** Exit **不硬要**「可发」；硬条=硬闸+confirm+再验触发+导出；升「可发」=加分勾 |
| **V15-Q22** | **(a)** roadmap V1.5 In 改为表单闭环；薄对话移出 In→Out/留位 |
| **V15-Q23** | **(a)** 保留 `patch_span`（默认可自动）；正文真相=`before_text`/`after_text` |

**Anthropic 预锁（Round 2 合入）：** Exit/ACCEPTANCE=冒烟·对客 demo 层；禁单次报 C vs T 显著；词表进 CONTEXT、论文 n/四指标进评估；Q14 脚本预锁禁 HARKing。

**Frontier：** 已空。  
**共享理解:** 已确认（2026-09-29）。  

**已落盘:**  
`docs/research/V1.5-Evidence-bound补丁设计评估.md` · `docs/adr/0029-v1.5-evidence-bound补丁与独立确认API.md` · CONTEXT（Evidence-bound / propose·confirm / Verify+）· roadmap V1.5 In/Out/Exit · GitHub [#195](https://github.com/luxingjiang1993/FreshLatch/issues/195) CLOSED · 实现 [#196](https://github.com/luxingjiang1993/FreshLatch/issues/196)–[#203](https://github.com/luxingjiang1993/FreshLatch/issues/203) CLOSED（冒烟 Exit）  

**下一跳:** Phase I2 grill / to-spec。

---

## 2b. I0 grill 已钉（2026-09-29 · Round 1 · 认推荐）

| # | 决策 | 拍板 |
|---|------|------|
| I0-Q1 | 数字真相源 | 先对齐 `origin/main`（含 Phase A / PR #167）；以现有 `reports/retrieve-*.md` 为可引用数字；I0 文档收敛+引用，未重跑不改报告数字 |
| I0-Q2 | accounting-card 公式面 | 最小 = **Recall@10 + 增益门谓词** + **must_stale 回放**保险丝；MRR/p95 详表进 `eval-retrieve` |
| I0-Q3 | 为何仍 BM25 | 主句 = 预登记门未过（dense 更差；rerank 无严格增益）；护栏 = Hard-Gold 未开不得因持平改默认 |
| I0-Q4 | eval-retrieve ↔ reports | docs = 总览+命令+叙事；数字 **只链接** reports，不整表复制 |
| I0-Q5 | 无 API Key 复跑 | Exit 认 BM25（+本地可得 traps/transform）；dense/hybrid/rerank 列标「需 dense index」；禁止只用 markdown 顶替实跑 |
| I0-Q6 | contribution-boundary v0 | 正文 = Phase A / retrieve 子系统贡献；整条发前协议 =「后续阶段将声明」占位 |
| I0-Q7 | I0↔V1 | 同 §2 Q6：并行骨架；挡 merge/demo 叙事 |
| I0-Q8 | Anthropic 层标签 | `accounting-card` 与 `eval-retrieve` **文首**钉：「演示/冒烟层（n=36）；不报方差；不作统计显著声明」 |

### Round 2（2026-09-29 · 认推荐）

| # | 决策 | 拍板 |
|---|------|------|
| I0-Q9 | accounting-card 大纲 | 文首冒烟声明 → 假设 → 公式/门谓词 → 数字一行表 → 权衡 → 指针；**加** 30 秒面试口述稿；重建步骤不进卡片 |
| I0-Q10 | 复跑命令 | `eval-retrieve` **双列** POSIX + PowerShell |
| I0-Q11 | 贡献黑名单 | 禁用话术全禁：agentic RAG / 非 BM25 已默认 / 统计显著最优 / 首次·PCC / Phase A=发前闭环已交付 |
| I0-Q12 | Exit 操作化 | 闭卷四探针 + 口头改一条门谓词能推出仍关/可能开；现场重跑 BM25 = 加分非硬门 |
| I0-Q13 | Hard-Gold | I0 仅一句指针；不写完整规格、不同步空 issue |
| I0-Q14 | ADR | **开 ADR-0026**：冒烟层预登记 + reports 为数字 SoT + 无增益不改默认（交叉引用 ADR-0003） |

**共享理解:** 已确认（2026-09-29）。  

**已落盘:**  
`docs/accounting-card.md` · `docs/eval-retrieve.md` · `docs/contribution-boundary.md` · `docs/adr/0026-i0-冒烟层与reports为数字真相源.md` · `docs/research/I0-冒烟层与数字真相源设计评估.md` · `docs/evidence/i0/ACCEPTANCE.md`  

**I0 Exit:** **DONE**（2026-09-29；证据见 ACCEPTANCE）。  
**V1 Round 1–2:** 已钉（见 §2d）。**共享理解已确认（含 2026-09-29 再确认）**；ADR-0027 / 评估 / CONTEXT 已落。规格/#168 已走过；远程 #169–#175 CLOSED。  
**本期序（纠偏）：** ① bare-pytest 卫生先关 → ② **I1 grill**（§2e）→ to-spec → implement。
---

## 3. 后续轮（依赖 §2 / §2e 部分答案）

| 题 | 依赖 | 内容 |
|----|------|------|
| **V1-R2 Q7** | Q5 | ~~论文 C vs T 是否进 UX~~ **已钉** |
| **V1-R2 映射边界** | Q3 | ~~「全 fresh 无人审」等边界~~ **已钉** |
| Q9 Evidence-bound 补丁 UX | Q5, Q3 | **V1.5 DONE（冒烟）**（§2f；#196–#203 CLOSED） |
| **I1-R2** 三分法 ↔ 层映射表 | I1-Q2/Q3 | 找不到/找错/没用上 × retrieve/Lead/Critic/Gate/HumanLatch |
| **I1-R2** 漏拦 vs 误拦操作定义 | I1-Q2/Q4 | 与假绿对照 / must_* 金标如何对齐 |
| **I1-R2** Exit 闭卷口述稿 | I1-Q4/Q5 | 指着哪 3 条讲清层级 |
| **I1-R2** 是否开 ADR | I1-Q2/Q3 | 三分法进词表 vs 仅评估文档 |
| Q11–Q13 | 更后 | 见原表 |

### I0 Round 2（依赖 §2b；见本会话）

| 题 | 依赖 | 内容 |
|----|------|------|
| I0-Q9 | I0-Q2 | accounting-card 章节大纲 |
| I0-Q10 | I0-Q4/Q5 | eval-retrieve 目录与复跑命令块 |
| I0-Q11 | I0-Q6 | 贡献边界禁用话术表 |
| I0-Q12 | I0-Q2/Q8 | Exit 闭卷探针 +「改假设重算」演示定义 |
| I0-Q13 | I0-Q3 | Hard-Gold 指针形态 |
| I0-Q14 | I0-Q1/I0-Q8 | 是否另开 ADR |

---

## 4. Glossary 种子（domain-modeling 起步）

| 术语 | 工作定义（可在 grill 中修订） |
|------|------------------------------|
| **T1** | 已入库、可 checksum 的一级证据材料；未入 T1 不得参与绿灯裁定 |
| **Gate** | 对主张/包的可审计复验（检索→裁决→人审路径） |
| **Verify+** | Gate + 入库 + 报告级汇总 + 带确认改稿 + 薄对话 |
| **Studio** | 多工作站外壳；冻结；须穿同一 Gate |
| **disposition（包结论）** | 可发 / 需补丁 / 勿发（聚合层） |
| **retrieval arm** | BM25 / dense / hybrid / rerank；生产默认 BM25 |
| **HumanLatch** | 人审状态机与误判样本驱动说明（I1 将钉 corpus 形态） |
| **失败三分法 / 漏拦·误拦** | **评测·答辩标签**（非生产 Gate 枚举）；定义与映射见 I1 ADR/评估；corpus 在 `docs/evidence/i1/` |
| **Evidence-bound patch** | 引用 ⊆ 已入库 T1 的**整条主张正文替换**；人确认才应用；强制再验；产品路径恒 `arm=T`（对外少用 proof-carrying）→ **已迁 CONTEXT / ADR-0029** |
| **propose_patch / confirm_patch** | Verify+ 独立 API（≠ HumanLatch discard/renew）→ **已迁 CONTEXT / ADR-0029** |
| **patch_events** | 改稿对照实验与产品审计共用事件账 |
| **Hard-Gold** | 另票；过增益门才讨论改生产默认臂 |
| **冒烟层评测（I0）** | Phase A retrieve 对比表的诚实档：n 小、可复跑、**禁止**升格为统计显著/方差结论；文首必须声明（评测文档纪律，不进产品词表正文） |
| **retrieve 子系统评测** | `python -m freshlatch.eval retrieve` 轨；与主张金标 `eval run --gold` **分轨**，不得混报 |
| **V1 垂直（顾问报告）** | 近端唯一垂直：已签发顾问/战略主张的发前复验；样例主包 McKinsey State of AI（T0≈2025-03 / T1≈2025-11）；非研报、非合规主包 |
| **薄 URL（c′）** | T1 合法入口之一：仅白名单域名单条抓取→落盘；失败显式错误并可回落粘贴确认入库；非开放爬虫 |

定稿后迁到正式 `docs/` glossary 或 ADR；此处仅种子。

---

## 5. Coding agent 开工闸门

| 阶段 | 允许 | 禁止 |
|------|------|------|
| Grill 未确认共享理解 | 读仓、列疑问、起草 ADR/glossary、**I0 文档** | 宣称 V1 Done；改生产默认臂 |
| §2 Q1–Q5 已钉 | 搭 V1 骨架、schema、映射 ADR | 多垂直；对话改裁决 |
| **本期①卫生未 Exit** | 只修 pytest path / 导入 / `pythonpath` | 开写 #169+ 产品票 |
| V1 Exit | 演示发前路径；开始稳定记 `patch_events` | 难金标改默认；Studio |
| I1 Exit 前 | — | 用 V1.5/论文叙事替代 mid 铁证 |
| **V1.5 grill 已确认 · Exit 已齐** | I2 / 论文预实验簿记 | 薄对话；扩 HumanLatch；Exit 硬绑可发；改生产默认臂；用 V1.5 替代 I1 |

---

## 6. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-09-29 | 初版：配合 roadmap v3.1，供 grill-with-docs 使用 |
| 2026-09-29 | I0 grill Round 1 认推荐：§2b 已钉；§2 Q6 勾选；glossary 增冒烟层/retrieve 子系统评测种子 |
| 2026-09-29 | I0 grill Round 2 认推荐：大纲/命令/黑名单/Exit/Hard-Gold/ADR-0026；I0 frontier 清空待共享理解确认 |
| 2026-09-29 | 共享理解确认；I0 三件套+ADR-0026+评估文档落盘；CONTEXT 增 retrieve 子系统评测词条 |
| 2026-09-29 | V1 grill Round 1–2 认推荐：顾问报告+McK SoAI；两屏增量；包结论新层；c′=`www.mckinsey.com`；patch_events JSONL；Q7/Q15–Q18 已钉；待共享理解后 ADR-0027 |
| 2026-09-29 | V1 共享理解确认；ADR-0027+评估+CONTEXT 落盘；下一跳 to-spec |
| 2026-09-29 | V1 共享理解再确认；本期序曾钉 ①卫生→V1 implement |
| 2026-09-29 | **纠偏**：本期主烤 **I1**；§2e Round 1 Frontier；卫生仍①；V1 远程 CLOSED / 本地 DoD 待勾 |
| 2026-09-29 | I1 Round 1 混选钉入 §2e；Round 2 待答 |
| 2026-09-29 | I1 Round 2 全认；frontier 空；Anthropic 修正：三分法不进产品词表正文；待共享理解确认后四件套 |
| 2026-09-29 | I1 共享理解确认；评估+ADR-0028+CONTEXT 指针落盘；下一跳 ①卫生 + V1 ACCEPTANCE → to-spec |
| 2026-09-29 | **I1 DONE**：corpus/Exit 齐；四件套入库；#183 CLOSED；下一跳 V1.5 |
| 2026-09-29 | **V1.5 Round 1** 全认：正文替换+T1 硬闸；复验单增量；表单 Exit；独立 patch API；冒烟 Exit；导出包；§2f |
| 2026-09-29 | **V1.5 Round 2** 全认：薄对话 Out；单条再验；unknown+stale 可提案；T1 多选；before/after 进账本；mck 脚本；ADR-0029；v15 ACCEPTANCE；minutes 手填 |
| 2026-09-29 | **V1.5 Round 3** 全认：JSON+MD 导出；草案暂存；Exit 不硬要可发；roadmap In 去薄对话；patch_span 保留；frontier 空待共享理解确认 |
| 2026-09-29 | **V1.5 共享理解确认**；评估+ADR-0029+CONTEXT+roadmap 落盘；下一跳 to-spec |
| 2026-09-29 | **V1.5 DONE（冒烟）**：#196–#203 CLOSED（Ronin Exit）；证据 `docs/evidence/v15/`；下一跳 I2 |
