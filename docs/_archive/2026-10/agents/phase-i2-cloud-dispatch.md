# Phase I2 云端派工与 Grok 代审（#214–#219）

> 父规格：#213 · ADR-0030 · `docs/spec/13-PhaseI2-SecurityDemos.md` · 评估 `docs/research/I2-安全三例设计评估.md`  
> enrich 已完成（各票 `## Agent Guards`）  
> **人闸策略**：凡原需真人 Watch/抽检/Exit 收口之处，一律委托 **Ronin 代理人**（Grok）。本阶段 **无**「仅真人终收」票（含 #219 DoD）。真人默认 **零打扰**。  
> 链：`before-implement <ID>` → **同会话可「门过了继续开写」** `/implement`（见 prompts）  
> **硬前置**：V1.5 Exit 已齐；规格/工单 #213–#219 已 enrich。  
> **启动闸**：须父票 #213 出现 Ronin（或已授权代理）`GROK-PROXY-APPROVED I2-DISPATCH` 后，编排器/Automation 方可派 Cloud。

---

## 1) 交给 Cloud Agent / Automation 的票

编排器只派 **无 open blocker** 的票；一票一云端会话（或一 cron 轮次只啃一票）。从 **main** 启动。

| 顺序 | Issue | Cloud 职责 | 关单条件 |
|------|-------|------------|----------|
| 前沿∥ | #214 | 召回信任边界（ACL + poison） | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #214` 再 close |
| 前沿∥ | #215 | 注入 Gate 确定性拒绿 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #215` 再 close |
| 前沿∥ | #216 | （可选）#4 adv-fresh | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #216` 再 close；**不挡**硬 Exit |
| #214+#215 后 | #217 | security.md + evidence/i2 短页 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #217` 再 close |
| #214+#215+#217 后 | #218 | 注入 1× LLM e2e + ACCEPTANCE | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #218` 再 close |
| #218 后 | #219 | DoD CLOSE | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #219` 再 close（**Ronin 代 Exit**） |

**每票固定提示词骨架（贴进 Cloud / Automation）：**

```text
仓库 FreshLatch（luxingjiang1993/FreshLatch）。只做 GitHub Issue #<ID>（读全文含 ## Agent Guards）。
派工权威：docs/agents/phase-i2-cloud-dispatch.md ；提示词：docs/agents/phase-i2-cloud-prompts.md ；父规格 #213 ；ADR-0030。
1) 先确认 #213 已有 GROK-PROXY-APPROVED I2-DISPATCH；否则停并评论「等待 DISPATCH」。
2) 确认本票无 open blocker；否则停。
3) /before-implement #<ID>；门不过则 enrich/停，勿写业务代码。
4) 门过 → 若提示含「门过了继续开写」则同会话 /implement；否则停并开新会话。
5) 权威命令：python -m compileall -q src ；pytest（至少 Acceptance 点名的测试）。
6) Evidence 三行评论到 Issue：typecheck · tests · paths。
7) 关单：实现后按「Grok 代审协议」通知 Ronin，**等** GROK-PROXY-APPROVED #<ID> 再 close；勿 @真人。
8) 禁止：安全平台/RBAC/租户管理面；用 #4 顶替 I2 Exit；无标签投毒启发式硬门；三威胁全绑 LLM；扩 HumanLatch；改生产默认臂；密钥写入仓库/Issue/日志；自批未代审票关单；宣称 adversarial INDEX 升版=Done。
9) Provenance：遵守票内历史参考标注（#214 对照 project 多agent/rag.py 思路；禁 CASE-高效召回/10课沙箱当 ACL；#218 禁 OpenManus ask_human）。
10) 文首/ACCEPTANCE 冒烟声明；不报安全通过率/方差。
```

全量可复制提示词见 `docs/agents/phase-i2-cloud-prompts.md`。

---

## 2) Ronin（Grok）代审（Cloud → 通知 Ronin，勿通知真人）

| Issue | 原人类角色 | Ronin 代审要点 |
|-------|------------|----------------|
| #214 | 召回信任边界抽检 | 显式 tenant 过滤；poison 剔除；无参兼容；Forensic 不旁路；Provenance 未照抄 CASE/沙箱 |
| #215 | 注入确定性抽检 | inj-t001 非 fresh；零 LLM；未挂 meta_gate；rule_gate 回归绿 |
| #216 | #4 可选抽检 | 仅可选；明示 ≠ I2 Exit；未改 INDEX 升版叙事 |
| #217 | 文档抽检 | security.md 三行齐；i2 短索引；冒烟声明；#4 不进硬行 |
| #218 | Exit 冒烟抽检 | ACCEPTANCE 文首冒烟；硬三例+1×e2e decoding；无 Key 不伪造通过；ACL/poison 未绑 LLM |
| #219 | DoD 终收（Ronin 代） | Out 未偷渡；硬 Exit 指针齐；不升格渗透认证/Hard-Gold |

**本阶段全部票均须 Ronin 代审后再 close**（无「绿即自行 close」例外，避免无人抽检）。

**Cloud → Ronin 通知模板：**

```text
【通知 Ronin Agent · 勿通知人类】
票 #<ID> 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i2-cloud-dispatch.md §2 与用户 Store ronin-phase-i2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #<ID>
不通过：GROK-PROXY-REJECT #<ID> + 缺陷清单
```

**派工启动授权（编排器/Automation 等此句）：** 父票 #213 评论 `GROK-PROXY-APPROVED I2-DISPATCH`。

Ronin 任务书：用户 Agent Store `ronin-phase-i2-proxy-brief.md`。

---

## 3) Skill 链

```text
（已完成）grill → to-spec #213 → to-tickets #214–219 → enrich-tickets
（启动前）Ronin 认领 + GROK-PROXY-APPROVED I2-DISPATCH
（每票）/before-implement #<ID> → /implement #<ID>（可同会话）
（每票）实现后 → Ronin 代审 → close
顺序：(#214 ∥ #215 ∥ #216) → #217 → #218 → #219
```

---

## 4) 阻塞图（前沿）

```text
#214 ─┐
#215 ─┼─► #217 ─► #218 ─► #219（Ronin 代 Exit）
#216 ─┘（可选；不挡 #217/#218/#219 硬链）
```

当前可派（**仅当** `GROK-PROXY-APPROVED I2-DISPATCH` 已出现）：**#214 ∥ #215 ∥ #216**。

---

## 5) Cloud / Automation 绑定

1. Automation / Cloud 仓库 = `luxingjiang1993/FreshLatch`（禁止空 repoUrl）。  
2. GitHub 授权含 issues 写（Evidence 评论、关单）与 PR。  
3. 从 **main** 启动；须已能读到本文件与 prompts（已推 main）。  
4. `gh auth` 失败或 cwd 无仓 → **立即停**，在 #213 评论「绑定仍坏」。  
5. 真人默认 **零打扰**；审核节点只走 Ronin。  
6. Automation 建议：cron 轮询前沿一票；或 issue 评论触发 `I2-CLOUD-GO #<ID>`。

---

## 6) 编排器备注

- 若 Ronin `GROK-PROXY-REJECT`：Cloud 修缺陷或新开会话，再通知代审；勿绕过代审直接 close。  
- 本文件为 Phase I2 主派工权威；V1.5/I1 dispatch 仅历史参考。
