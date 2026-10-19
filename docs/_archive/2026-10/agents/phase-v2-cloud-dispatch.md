# Phase V2 云端派工与 Grok 代审（#227–#232）

> 父规格：#226 · ADR-0031 · `docs/spec/14-PhaseV2-PublishHook.md` · 评估 `docs/research/V2-发前钩子与主张台账设计评估.md`  
> enrich 已完成（各票 `## Agent Guards`）  
> **人闸策略**：凡原需真人 Watch/抽检/Exit 收口之处，一律委托 **Ronin 代理人**（Grok）。本阶段 **无**「仅真人终收」票（含 #232 DoD）。真人默认 **零打扰**。  
> 链：`before-implement <ID>` → **同会话可「门过了继续开写」** `/implement`（见 prompts）  
> **硬前置**：I2 Exit 已齐；规格/工单 #226–#232 已 enrich；决议四件套已在 main。  
> **启动闸**：须父票 #226 出现 `GROK-PROXY-APPROVED V2-DISPATCH` 后，编排器/Automation 方可派 Cloud。

---

## 1) 交给 Cloud Agent / Automation 的票

编排器只派 **无 open blocker** 的票；一票一云端会话（或一 cron 轮次只啃一票）。从 **main** 启动。

| 顺序 | Issue | Cloud 职责 | 关单条件 |
|------|-------|------------|----------|
| 前沿∥ | #227 | 发前钩子闸核心（evaluate 表驱动） | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #227` 再 close |
| 前沿∥ | #228 | 主张台账只读投影（旁路 + MD） | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #228` 再 close |
| #227 后 | #229 | Client Memo 套闸（CLI + UI） | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #229` 再 close |
| #227 后 | #230 | 入站 publish-hook check | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #230` 再 close |
| #228+#229+#230 后 | #231 | 冒烟 e2e + v2 ACCEPTANCE | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #231` 再 close |
| #231 后 | #232 | DoD CLOSE | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #232` 再 close（**Ronin 代 Exit**） |

**每票固定提示词骨架（贴进 Cloud / Automation）：**

```text
仓库 FreshLatch（luxingjiang1993/FreshLatch）。只做 GitHub Issue #<ID>（读全文含 ## Agent Guards）。
派工权威：docs/agents/phase-v2-cloud-dispatch.md ；提示词：docs/agents/phase-v2-cloud-prompts.md ；父规格 #226 ；ADR-0031。
1) 先确认 #226 已有 GROK-PROXY-APPROVED V2-DISPATCH；否则停并评论「等待 V2-DISPATCH」。
2) 确认本票无 open blocker；否则停。
3) /before-implement #<ID>；门不过则 enrich/停，勿写业务代码。
4) 门过 → 若提示含「门过了继续开写」则同会话 /implement；否则停并开新会话。
5) 权威命令：python -m compileall -q src ；pytest（至少 Acceptance 点名的测试）。
6) Evidence 三行评论到 Issue：typecheck · tests · paths。
7) 关单：实现后按「Grok 代审协议」通知 Ronin，**等** GROK-PROXY-APPROVED #<ID> 再 close；勿 @真人。
8) 禁止：Word/Notion/开放 webhook 平台；大图谱/采编 CMS；Memo 商业裁决；扩 HumanLatch；renew 改正文；新表双写作废；导出强制整包再验；改生产默认臂；解冻 Studio；把检索 embed 称作本阶段；密钥写入仓库/Issue/日志；自批未代审票关单；Exit 硬绑「可发」；报采用率。
9) Provenance：遵守票内历史参考（#229 对照 mission_control 只学入口；禁 Streamlit；#230 禁 OpenManus WS；#227 禁 ask_human/approve_promotion）。
10) ACCEPTANCE/文首冒烟采用层声明；curl ≠ 插件平台已交付。
```

全量可复制提示词见 `docs/agents/phase-v2-cloud-prompts.md`。

---

## 2) Ronin（Grok）代审（Cloud → 通知 Ronin，勿通知真人）

| Issue | 原人类角色 | Ronin 代审要点 |
|-------|------------|----------------|
| #227 | 闸核心抽检 | 五类语义表驱动；缺 run_id fail-closed；零 LLM；未整包再验 |
| #228 | 台账抽检 | discard∪renew 可见；renew∉作废名单；零新写表；未糊 patch_events |
| #229 | Memo 套闸抽检 | UI/CLI 同闸；deny 零写；ADR-0015 无商业裁决；需补丁+ack 有标记；未抄 Streamlit |
| #230 | 入站 check 抽检 | allow/deny；403/409；本机默认；未做插件平台/出站通知顶替 |
| #231 | Exit 冒烟抽检 | ACCEPTANCE 文首冒烟；硬条含 curl allow+deny；不硬绑可发 |
| #232 | DoD 终收（Ronin 代） | Out 未偷渡；硬 Exit 指针齐；不升格 Hard-Gold/平台已交付 |

**本阶段全部票均须 Ronin 代审后再 close**。

**Cloud → Ronin 通知模板：**

```text
【通知 Ronin Agent · 勿通知人类】
票 #<ID> 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v2-cloud-dispatch.md §2 与用户 Store ronin-phase-v2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #<ID>
不通过：GROK-PROXY-REJECT #<ID> + 缺陷清单
```

**派工启动授权（编排器/Automation 等此句）：** 父票 #226 评论 `GROK-PROXY-APPROVED V2-DISPATCH`。

Ronin 任务书：用户 Agent Store `ronin-phase-v2-proxy-brief.md`。

---

## 3) Skill 链

```text
（已完成）grill → to-spec #226 → to-tickets #227–232 → enrich-tickets
（启动前）GROK-PROXY-APPROVED V2-DISPATCH @ #226
（每票）/before-implement #<ID> → /implement #<ID>（可同会话）
（每票）实现后 → Ronin 代审 → close
顺序：(#227 ∥ #228) → (#229 ∥ #230) → #231 → #232
```

---

## 4) 阻塞图（前沿）

```text
#227 ─┬─► #229 ─┐
      └─► #230 ─┼─► #231 ─► #232（Ronin 代 Exit）
#228 ──────────┘
```

当前可派（**仅当** `GROK-PROXY-APPROVED V2-DISPATCH` 已出现）：**#227 ∥ #228**。

---

## 5) Cloud / Automation 绑定

1. Automation / Cloud 仓库 = `luxingjiang1993/FreshLatch`（禁止空 repoUrl）。  
2. GitHub 授权含 issues 写（Evidence 评论、关单）与 PR。  
3. 从 **main** 启动；须已能读到本文件与 prompts、ADR-0031、规格 14（已推 main）。  
4. `gh auth` 失败或 cwd 无仓 → **立即停**，在 #226 评论「绑定仍坏」。  
5. 真人默认 **零打扰**；审核节点只走 Ronin。  
6. Automation 建议：cron 轮询前沿一票；或 issue 评论触发 `V2-CLOUD-GO #<ID>`。

---

## 6) 编排器备注

- 若 Ronin `GROK-PROXY-REJECT`：Cloud 修缺陷或新开会话，再通知代审；勿绕过代审直接 close。  
- 本文件为 Phase V2 主派工权威；I2/V1.5 dispatch 仅历史参考。
