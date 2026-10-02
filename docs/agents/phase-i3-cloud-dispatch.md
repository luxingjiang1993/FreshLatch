# Phase I3 云端派工与 Grok 代审（#249–#253）

> 父规格：#248 · ADR-0032 · `docs/spec/20-PhaseI3-InterviewHardening.md` · 评估 `docs/research/I3-面试加固三轨设计评估.md`  
> enrich 已完成（各票 `## Agent Guards`）  
> **人闸策略**：凡原需真人 Watch/抽检/Exit 收口之处，一律委托 **Ronin 代理人**（Grok）。本阶段 **无**「仅真人终收」票（含 #253 DoD）。真人默认 **零打扰**。  
> 链：`before-implement <ID>` → **同会话「门过了继续开写」** `/implement`（见 prompts）  
> **硬前置**：V2 Exit 已齐；规格/工单 #248–#253 已 enrich；决议四件套已在 main。  
> **启动闸**：须父票 #248 出现 `GROK-PROXY-APPROVED I3-DISPATCH` 后，编排器/Automation/Cloud 方可派工。

---

## 1) 交给 Cloud Agent / Automation 的票

编排器只派 **无 open blocker** 的票；**一票一云端会话**（或一 cron 轮次只啃一票）。从 **main** 启动。  
I3 票序 **严格串行**（grill 钉死）：`#249 → #250 → #251 → #252 → #253`。

| 顺序 | Issue | Cloud 职责 | 关单条件 |
|------|-------|------------|----------|
| 1 | #249 | #8 出处禁区旁路（Policy-as-code thin） | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #249` 再 close |
| 2 | #250 | B′ 合成夹具（超时/重入/闸分布） | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #250` 再 close |
| 3 | #251 | Hard-Gold 骨架（分文件·不改臂） | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #251` 再 close |
| 4 | #252 | e2e + ACCEPTANCE 三轨分节 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #252` 再 close |
| 5 | #253 | DoD CLOSE | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #253` 再 close（**Ronin 代 Exit**） |

**每票固定提示词骨架（贴进 Cloud / Automation）：**

```text
仓库 FreshLatch（luxingjiang1993/FreshLatch）。只做 GitHub Issue #<ID>（读全文含 ## Agent Guards）。
派工权威：docs/agents/phase-i3-cloud-dispatch.md ；提示词：docs/agents/phase-i3-cloud-prompts.md ；父规格 #248 ；ADR-0032。
1) 先确认 #248 已有 GROK-PROXY-APPROVED I3-DISPATCH；否则停并评论「等待 I3-DISPATCH」。
2) 确认本票无 open blocker（前序票均 CLOSED）；否则停。
3) /before-implement #<ID>；门不过则 enrich/停，勿写业务代码。
4) 门过 → 本会话含「门过了继续开写」则同会话 /implement；否则停并开新会话。
5) 权威命令：python -m compileall -q src ；pytest（至少 Acceptance 点名的测试）。
6) Evidence 三行评论到 Issue：typecheck · tests · paths。
7) 关单：实现后按「Grok 代审协议」通知 Ronin，**等** GROK-PROXY-APPROVED #<ID> 再 close；勿 @真人。
8) 禁止：改 PRODUCTION_RETRIEVAL_MODE；宣称 Hard-Gold 已授权换臂；OPA/Cedar；改写 rule_gate 不变量正文；Memory/多 Agent；Studio；C′/图谱；用 I3 替代 I1/I2；报方差；整包再验挂钩子；密钥入库；自批未代审关单。
9) Provenance：遵守票内历史参考；idea #8 ≠ 历史语料金标工单 #8。
10) ACCEPTANCE/文首层标签强制；骨架 ≠ 换臂；夹具 ≠ 真事故。
```

全量可复制提示词见 `docs/agents/phase-i3-cloud-prompts.md`。

---

## 2) Ronin（Grok）代审

| Issue | Ronin 代审要点 |
|-------|----------------|
| #249 | 声明式出处禁区；政策拒可见；未改 rule_gate 不变量正文；零 LLM；回归绿 |
| #250 | 超时结构化错误；重放不双写；闸分布一页；标明合成夹具；未挂整包再验到钩子 |
| #251 | hard gold 分文件 n≥20·traps/对抗≥30%；增益报告可跑；断言仍 bm25；文首骨架不改臂 |
| #252 | ACCEPTANCE 文首层标签；三轨分节互不顶替；不报方差 |
| #253 | Out 未偷渡；硬 Exit 指针齐；不升格换臂/政策平台 |

**Cloud → Ronin 通知模板：**

```text
【通知 Ronin Agent · 勿通知人类】
票 #<ID> 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i3-cloud-dispatch.md §2 代审。
通过：GROK-PROXY-APPROVED #<ID>
不通过：GROK-PROXY-REJECT #<ID> + 缺陷清单
```

**派工启动授权：** 父票 #248 评论 `GROK-PROXY-APPROVED I3-DISPATCH`。

---

## 3) Skill 链

```text
（已完成）grill → to-spec #248 → to-tickets #249–253 → enrich-tickets
（启动前）GROK-PROXY-APPROVED I3-DISPATCH @ #248
（每票）/before-implement #<ID> → /implement #<ID>（同会话「门过了继续开写」）
（每票）实现后 → Ronin 代审 → close
顺序：#249 → #250 → #251 → #252 → #253（禁止跳序）
```

---

## 4) 阻塞图

```text
#249 → #250 → #251 → #252 → #253（Ronin 代 Exit）
```

当前可派（**仅当** `GROK-PROXY-APPROVED I3-DISPATCH` 已出现）：**#249**。

---

## 5) Cloud / Automation 绑定

1. 仓库 = `luxingjiang1993/FreshLatch`；从 **main** 启动。  
2. GitHub 授权含 issues 写与 PR。  
3. 须已推 main：本文件、prompts、ADR-0032、spec 20、CONTEXT 词条。  
4. 真人默认零打扰；审核只走 Ronin。
