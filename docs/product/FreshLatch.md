# FreshLatch 复验闩（实施切片）

本文从第五轮正本 [`10套AI产品概念方案.md`](./10套AI产品概念方案.md) 抽出方案 1，供开工使用。正本不改。公司名仍是 FreshLatch，不是 MemoryForensics，不是 EvidenceOS。

**北星：** 已签发主张在 T1 是否仍可复验。过期、冲突、无 T1 原文支持的主张不得保持绿灯。人决定作废或续命。

**本切片新增的小模块：** MemoryForensics 记忆刑侦，只审本课题长期记忆，不另开产品、不接托管 Mem0、不做主界面。

---

## 1. 一句话定位

把已签发主张从「曾经为真」改成「现在仍可复验」；过期、冲突、无 T1 原文支持的主张不得保持绿灯，人决定作废或续命。

**单一垂直 = 顾问报告**（近端唯一垂直，ADR-0027）：V1 发前路径只服务已签发顾问/战略类主张；样例主包为 McKinsey State of AI 公开洞察摘录（见 `data/packs/v1-mck-soai/`）。研报/合规可另阶段，不与本垂直并行。thesis-1 / QuoteTTL 仅回归，不算第二垂直。

## 2. 目标用户

**中国第一年现金楔子：** 独立顾问、产业研究员、战略岗。他们已经出过一版判断，两周后客户追问「还成立吗」。买的是复验报告，不是再生成一篇。设计伙伴价按课题 3000–8000 元，或个人订阅 199–349 元/月。

**美国经济买方：** 独立 consultant、sales engineer、policy researcher。预算是 research / proposal integrity，不是 Copilot 席位。定价 $29–49/月个人，团队按席 + 按复验次数。

**日活：** 做课题、要对自己上周附件负责的人。经济买方常常就是日活。

**明确拒绝：** 只要更快摘要的增长团队；要企业 SSO 全家桶的采购；要自动商业裁决的买方；要无限记忆的 Agent 平台采购。

## 3. 核心痛点

T0 卷宗或咨询 PDF 看起来可辩护。T1 价格变了、竞品发了新闻、监管口径更新、访谈对象改口。人仍把 T0 绿灯附件发给客户。频率大约每 2–6 周一次「还成立吗」。做错一次是职业风险。

JTBD：**给我一份能指回 T0 与 T1 原文的复验单：哪些仍成立、哪些必须作废、缺口是什么。不要再给我一篇新摘要。**

情报锚（Tavily，截至 2026-09-19）：Mem0 把 memory staleness 列为未解决问题，高相关记忆会突然自信地错；衰减解决近因，不解决源认证。

## 4. 产品怎么跑

一次复验有六段。Lead、Critic、Forensic 默认是 Agent。过期绿灯闸、隔离闸、人审名单是 Workflow。Auditor 可以是短循环 Agent，不得拥有放行权。

1. **Lead Reverifier（真 Agent）：** 看见 T0 主张、已检索的 T0/T1 块、作废名单、隔离中的记忆 id、缺口。下一步由模型决定：改写查询、按 `as_of=T0|T1` 换源、read 原文、`reverify_claim`、`mark_stale`、`mark_gap`、`spawn_critic`、`spawn_auditor`、`spawn_forensic`、`finish_reverify`。ground truth 是原文，不是模型记忆。
2. **Critic（真 Agent）：** 只找「主张已死」的反证。不得强化「仍然成立」。动态决定检索什么。
3. **Forensic（真 Agent，小模块）：** 只审本课题长期记忆。找死事实、互斥条目、无源条目。不得改主张正文，不得放行。
4. **Auditor（短循环 Agent + 规则闸）：** 判定 `fresh` / `stale` / `unknown`。`stale` 与 `unknown` 不得保持绿灯（代码强制）。
5. **Scribe / 复验单 UI（Workflow）：** 只排版。主界面是复验单，不是聊天框，也不是记忆列表。
6. **HumanLatch（Workflow）：** 人点「作废」或「续命（必须带 T1 evidence_id）」。隔离记忆也要人确认后才移出召回。Agent 不得自己把红灯改回绿灯，不得自己删除记忆。

禁止给出「建议进入 / 不进入市场」的最终商业裁决。诚实自治：复验与刑侦 L1；作废、续命、隔离确认给人 L0。不宣传 L3 生产写入。

## 5. 与红海的边界

| 现有方案 | FreshLatch |
|----------|------------|
| EvidenceOS | T0 取证成卷 | T1 对已签发主张复验作废 |
| Mem0 / Cognee / Zep | 存储与召回 | 本课题记忆里已死、互斥、无源的条目不得再当召回 |
| Perplexity / Glean | 更快给一段话 | 复验单：fresh / stale / unknown |

错位失败：主界面变成聊天框；再跑一遍 T0 调查；主卖点变成「我们记忆更准」。

## 6. 默认课题（锁定，开工第一天选定后禁止改）

**问题：** 两周前那份「是否在未来 12 个月进入东南亚中小企业 AI 客服市场」的判断，现在还成立吗？

语料：

- T0：合成访谈、成本模型、竞品笔记。
- T1：故意改掉的竞品价格、监管口径、客户访谈改口。至少三条必须在金标里打成 stale。

Demo 只用合成材料。界面标明 synthetic。准备材料不是法律意见，不是自动决策。真实客户机密不进作品集。

用户旅程：导入 T0 主张 → Lead 按 `as_of=T1` 循环对照 → Critic 找已死反证 → 复验单红绿 → 人作废一条 → 禁用名单重跑 → 该主张不得再绿。对照：无工具 LLM 读 T0 摘要必须把已死主张判绿；本产品必须红。

## 7. 角色诚实表

| 角色 | 类型 | 职责 | 禁止 |
|------|------|------|------|
| Runner | Workflow | 预算、步数、作废名单、隔离名单、LangGraph checkpoint | 编造仍成立；最终商业裁决 |
| Lead | 真 Agent | 自主规划复验，决定是否派 Critic / Auditor / Forensic | 无 T1 原文把 stale 改 fresh；放行 |
| Critic | 真 Agent | 找已死主张 | 强化原主张；放行 |
| Forensic | 真 Agent | 审长期记忆：死事实、矛盾、无源 | 改主张正文；删除；放行 |
| Auditor | 短循环 Agent | 判定 fresh / stale / unknown | 改主张正文；放行 |
| 规则闸 | Workflow | stale / unknown 不得绿灯；dead / contradictory / unverified 不得召回 | 扮演调查 |
| HumanLatch | Workflow | 作废、续命、确认隔离 | 自动续命；自动抹记忆 |

派驻必须由 Lead 根据中间结果决定，不是固定「第 3 步一定召唤」。

## 8. 数据与记忆

**语料：** Windows 本地。私有与公开分 `source_type`，时间分 `as_of=T0|T1`。Chroma 或 SQLite。未命中禁止用模型记忆作答。

**主张 schema：**

- `claim_id`
- `statement`
- `t0_evidence_ids`
- `t1_evidence_ids`
- `status`：`fresh` / `stale` / `unknown` / `void`
- `last_confirmed_at`
- `validity_basis`：`doc_id` + checksum

无 `t1_evidence_ids` 不得 `status=fresh`。续命必须带新的 T1 evidence_id。

**短期记忆：** 本轮轨迹、最近检索块。上下文只装主张列表、最近检索、作废名单、隔离名单。不装全部语料。

**长期记忆（本课题，不是通用记忆库）：** 已证主张、已废 id、缺口、`last_confirmed_at`、`validity_basis`。条目字段：`memory_id`、`content`、`written_at`、`last_confirmed_at`、`source_ref`、`checksum`、`status`。

**评测：** `data/eval/gold.json`。北极星是 must_stale 的 claim_id，以及 must_quarantine 的 memory_id。用户作废率是在线指标。不是「报告好读」。

## 9. 工具（Function Call 与 MCP 同构）

复验：

- `retrieve(query, source_type, as_of)`
- `read_source(doc_id)`
- `reverify_claim(claim_id, status, evidence_ids)`
- `mark_stale(claim_id, reason)`
- `mark_gap(description)`
- `spawn_critic(focus)`
- `spawn_auditor(claim_id)`
- `finish_reverify()`

刑侦小模块：

- `list_memories()`
- `spawn_forensic(focus)`
- `flag_contradiction(memory_id_a, memory_id_b, reason)`
- `flag_dead(memory_id, reason, evidence_ids)`
- `flag_unverified(memory_id, reason)`
- `propose_quarantine(memory_ids)`

`propose_quarantine` 只写建议。移出召回由代码在人确认后执行。MCP 暴露 `retrieve`、`read_source`、`reverify_claim`、`list_memories`。不暴露删除。

Skill 文件：

- `skills/reverify.md`：不得用记忆补原文；无 T1 不得判 fresh。
- `skills/devil_advocate.md`：只找已死，不得强化原主张。
- `skills/freshness_audit.md`：fresh / stale / unknown 口径。
- `skills/memory_forensics.md`：只审本课题记忆；无 source_ref 即 unverified；不得删除。

栈：Python 3.11、OpenAI 兼容 chat.completions + tools、FastAPI 或 Streamlit、Pydantic v2。LangGraph 只用于 checkpoint / interrupt 等人续命，图不是 Agent。不要 Docker。不要 Kubernetes。

步数护栏：Lead 最多 18 轮，Critic 最多 8 轮，Forensic 最多 8 轮，Auditor 最多 6 轮，单次检索预算 24。

## 10. 12 周切片

环境：Windows 10/11、Python 3.11、VS Code、PowerShell。控制台 UTF-8：

`$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new()`

代码放蓝海项目5 新目录。不改前四轮仓库。不改第五轮正本。

**W1–W2：** 合成 T0/T1 语料、索引、Lead 循环、复验单 UI。无聊天主框。验收：无 T1 原文不得绿灯；主按钮不得叫「生成答案」。

**W3–W4：** Critic 动态派驻；点回新旧原文；作废 id 进禁用名单并重跑。评测页 fresh / stale / unknown。对照：无工具 LLM 必须假绿，本产品必须红。**W4 结束仍不能点回 T1 原文，或 Critic 零有效已死反证，则立项失败。** 主界面若已是聊天框，或被复述成「又一个 EvidenceOS」，同样失败。此阶段不做刑侦模块，避免挡住 W4。

**W5–W8：** Auditor；`gold.json` 的 must_stale；MCP `retrieve` / `read_source` / `reverify_claim`；导出复验单 Markdown。续命必须等人给出 T1 原文。开始记 token，不按 token 卖。

**W9–W12：** 记忆刑侦小模块（见下一节）+ 口播。第二份更脏的 T1 语料。12 周不实现 QuoteTTL、CommitWatch、LivingBrief 产品，不接 Mem0。

## 11. 小模块：MemoryForensics

正本里 MemoryForensics 是独立产品：审计生产 Agent 的长期记忆，买方是工程负责人，按次体检。单独做会把蓝海项目5 写成记忆插件。

收进来之后，它只做一件事：**本课题长期记忆如果已经腐烂，不得继续被 Lead 当召回。** 它不卖「记住更多」，不托管记忆，不扫客户生产库。

### 11.1 审什么

只审 FreshLatch 自己写下的长期记忆，外加 demo 里故意放进同一 JSON 的少量腐烂条目。不审会话短期轨迹。不审向量库里的 T0/T1 原文（那是语料，不是记忆）。

三类发现：

- **dead：** 记忆内容与当前 T1 原文冲突，或 `validity_basis` checksum 对不上。
- **contradictory：** 两条记忆互斥，例如「竞品月费仍高于我们」与「竞品已降到我们的 70%」同时可召回。
- **unverified：** 没有 `source_ref`，或 source 已不存在。

规则闸：这三类不得进入下一轮 `retrieve` 的记忆侧上下文。原文检索不受影响。

### 11.2 谁来做

Lead 看见「记忆与刚读到的 T1 块打架」或「召回里有无 source_ref 的条目」时，调用 `spawn_forensic`。不是每轮固定召唤。

Forensic 自己决定先查哪条、要不要 `retrieve(as_of=T1)`、要不要 `read_source`。它只能 `flag_*` 和 `propose_quarantine`。Runner 把建议放进待确认名单。人点确认后，代码把这些 id 移出召回。Agent 不能直接删文件。

激励分离：Forensic 不得调用 `reverify_claim` 把主张改成 fresh，也不得替 Critic 写反证正文。

### 11.3 Demo 规模（小）

不要做 40 条生产记忆体检。合成记忆控制在 8–12 条，其中金标必须隔离：

- 2 条 dead（价格或监管口径已在 T1 改掉，记忆仍写旧结论）
- 1 对 contradictory（2 条互斥，都要出召回或至少标红并禁止同时召回）
- 2 条 unverified（无 `source_ref`）

其余条目应保持可召回，防止「全部隔离」假绿。评测文件可并进 `data/eval/gold.json` 的 `must_quarantine` 字段。

对照：无工具 LLM 把记忆库摘要成「历史结论仍然一致」必须假绿；本模块必须把金标 id 标出，且未确认前这些 id 已不得进入 Lead 上下文（建议态即可隔离召回，删除仍等人）。

### 11.4 UI

主屏仍是复验单。侧栏或第二块叫「记忆卫生」，列出待隔离条目、理由、点回的 T1 原文、确认按钮。不得把记忆列表做成首页。成交句仍是「哪些主张已经死了」，不是「你的 Agent 记忆里有 6 条死事实」。

### 11.5 排期与验收

放在 W9–W12，在 W4 复验验收通过之后。若 W4 未过，先停，不加本模块。

验收：

- 金标 dead / unverified 不得出现在 Lead 下一轮上下文。
- 人未确认前，磁盘上的记忆文件不被删除。
- 主按钮仍是「开始复验」，不是「记忆体检」。
- Forensic 零发现，或发现不能点回 T1 / 缺失的 source_ref，则本模块失败，但不把整个 FreshLatch 改名叫记忆产品。

### 11.6 面试里怎么讲（90 秒，挂在主叙事后面）

> Memory vendors optimize recall. Inside FreshLatch, forensic is a small latch on our own project memory. The lead spawns it when a stored conclusion fights the T1 span. Dead, contradictory, and uncertified entries leave the recall set. Quarantine confirm is human. We do not sell a memory database.

主动揭短：不接 Mem0；不审跨会话用户身份；条目只有十余条。

## 12. 面试主叙事（8–10 分钟）

- **0:00–0:40** 「Answers and dockets expire. FreshLatch is a reverify latch. Lead loops on T0 and T1. A critic hunts dead claims. Stale cannot stay green. Renew requires a T1 span.」
- **0:40–2:00** 2026 记忆层已标配，staleness 仍未解决。本产品卖作废，不卖记住更多。
- **2:00–4:30** 现场：`as_of=T1` 改写检索 → 主张从绿变红 → Critic 反证 → 作废重跑 → freshness 金标。
- **4:30–6:30** 无 T1 闸；fail-closed；Critic 不得把死主张判活；L1 复验 / L0 续命。
- **6:30–8:00** must_stale。无工具对照必须假绿。
- **8:00–9:00** 侧栏演示一条无源记忆被移出召回。强调这是可靠性模块。
- **9:00–10:00** 缺口：无企业 SSO；一类课题；合成数据。对照前四轮：出门、动手、认款、证据，这是作废层。

禁止开场「我做了个知识库 GPT」或「我做了第二个 EvidenceOS」或「我做了 Mem0」。

## 13. 停止条件

- W4 结束仍不能点回 T1 原文，或 Critic 给不出可理解的已死反证。
- W8 结束仍无作废名单、无 freshness 页、无 MCP 或等价工具暴露。
- W12 结束外部观察者仍把产品说成「AI 搜索」「行业 GPT」「卷宗换皮」或「记忆插件」，两次纠正无效。
- 为了成交把主按钮改成生成答案，或把主仓改成记忆中台。
- 真实客户完整机密进入公开作品集：立即停，降级为仅合成。

## 14. 明确不做

- 不改第五轮十套正本里其他九套的定义。
- 不把 MemoryForensics 做成第二个公司、第二个首页、Mem0 适配器。
- 12 周不做 QuoteTTL、CommitWatch、SkillRot、企业连接器、自动商业裁决。
- 不按 token 卖。不抽「帮客户赢了标」的成功费。
