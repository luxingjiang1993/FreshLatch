# Phase V1.5 云端派工与 Grok 代审（#197–#203）

> 父规格：#196 · ADR-0029 · `docs/spec/12-PhaseV1.5-EvidenceBound.md` · 评估 `docs/research/V1.5-Evidence-bound补丁设计评估.md`  
> enrich 已完成（各票 `## Agent Guards`）  
> **人闸策略**：凡原需真人 Watch/抽检/Exit 收口之处，一律委托 **Ronin 代理人**（Grok）。本阶段 **无**「仅真人终收」票（含 #203 DoD）。  
> 链：`before-implement <ID>` → **同会话可「门过了继续开写」** `/implement`（见 prompts）  
> **硬前置**：I1 Exit 已齐；V1 ACCEPTANCE 已齐；规格/工单 #196–#203 已 enrich。  
> **启动闸**：须父票 #196 出现 Ronin `GROK-PROXY-APPROVED V1.5-DISPATCH` 后，编排器方可派 Cloud。

---

## 1) 交给 Cloud Agent 的票

编排器只派 **无 open blocker** 的票；一票一云端会话。从 **main** 启动。

| 顺序 | Issue | Cloud 职责 | 关单条件 |
|------|-------|------------|----------|
| 前沿 | #197 | patch_events before/after + 产品写 T | Watch：Acceptance 全勾 → **可自行 close** |
| #197 后 | #198 | propose/confirm API 核心 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #198` 再 close |
| #198 后并行 | #199 | confirm → 单条再验 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #199` 再 close |
| #198 后并行 | #200 | 复验单补丁条带 UI | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #200` 再 close |
| #198 后并行 | #201 | 导出 JSON+短 MD | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #201` 再 close |
| #199+#200+#201 后 | #202 | 主缝 e2e + v15 ACCEPTANCE | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #202` 再 close |
| #202 后 | #203 | DoD 关门摘要 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #203` 再 close（**Ronin 代 Exit**） |

**每票固定提示词骨架（贴进 Cloud Agent）：**

```text
仓库 FreshLatch（luxingjiang1993/FreshLatch）。只做 GitHub Issue #<ID>（读全文含 ## Agent Guards）。
派工权威：docs/agents/phase-v15-cloud-dispatch.md ；提示词：docs/agents/phase-v15-cloud-prompts.md ；父规格 #196 ；ADR-0029。
1) 先 /before-implement #<ID>；门不过则 enrich/停，勿写业务代码。
2) 门过 → 若提示含「门过了继续开写」则同会话 /implement；否则停并开新会话。
3) 权威命令：python -m compileall -q src ；pytest（至少 Acceptance 点名的测试）。
4) Evidence 三行评论到 Issue：typecheck · tests · paths。
5) 关单：
   - #197：Watch 且 Acceptance 全勾 → gh issue close #<ID>
   - #198–#203：实现后按「Grok 代审协议」通知 Ronin，**等** GROK-PROXY-APPROVED #<ID> 再 close；勿 @真人
6) 禁止：薄对话/stub；扩 HumanLatch VALID_ACTIONS；产品路径无证 C；发前 UX 上 C|T 开关；Exit 硬绑「可发」；改生产默认臂；#8 并行；密钥写入仓库/Issue/日志；自批未代审票关单；吹首次/PCC。
7) 涉及历史改编须遵守票内 Provenance（#200 adapt mission_control；禁抄 ask_human / approve_promotion）。
8) 文首/ACCEPTANCE 冒烟声明；不报 C vs T 显著。
```

全量可复制提示词见 `docs/agents/phase-v15-cloud-prompts.md`。

---

## 2) Ronin（Grok）代审（Cloud → 通知 Ronin，勿通知真人）

| Issue | 原人类角色 | Ronin 代审要点 |
|-------|------------|----------------|
| #198 | 核心 API / 硬闸抽检 | 无证拒确认且零写；有证覆盖+T 行 before/after；VALID_ACTIONS 未扩；无 C|T UX |
| #199 | 再验接线抽检 | 单条再验触发；reverify=true；非整包唯一路径；latch 回归绿 |
| #200 | UI 抽检 | 仅 unknown\|stale 入口；t1 多选；无薄对话/独立补丁台；Provenance 未照抄角色名 |
| #201 | 导出抽检 | JSON+MD 关键字段；与 Client Memo 分轨；无 Streamlit 第二栈 |
| #202 | Exit 冒烟抽检 | ACCEPTANCE 文首冒烟；硬条四勾；升可发仅加分；预锁脚本/夹具可引用 |
| #203 | DoD 终收（Ronin 代） | Out 未偷渡；冒烟口径；路线图/README 叙事一致；不升格 Hard-Gold |

**#197** 无需 Ronin（Watch 绿即 close）。

**Cloud → Ronin 通知模板：**

```text
【通知 Ronin Agent · 勿通知人类】
票 #<ID> 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v15-cloud-dispatch.md §2 与用户 Store ronin-phase-v15-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #<ID>
不通过：GROK-PROXY-REJECT #<ID> + 缺陷清单
```

**派工启动授权（编排器等此句）：** 父票 #196 评论 `GROK-PROXY-APPROVED V1.5-DISPATCH`。

Ronin 任务书：用户 Agent Store `ronin-phase-v15-proxy-brief.md`。

---

## 3) Skill 链

```text
（已完成）grill → to-spec #196 → to-tickets #197–203 → enrich-tickets
（启动前）Ronin 认领 + GROK-PROXY-APPROVED V1.5-DISPATCH
（每票）/before-implement #<ID> → /implement #<ID>（可同会话若提示授权）
（#198–#203）实现后 → Ronin 代审 → close
（#197）绿即 close → 再派 #198 → 再并行 #199∥#200∥#201 → #202 → #203
```

---

## 4) 阻塞图（前沿）

```text
#197 ─► #198 ─┬─► #199 ─┐
              ├─► #200 ─┼─► #202 ─► #203（Ronin 代 Exit）
              └─► #201 ─┘
```

当前可派（**仅当** `GROK-PROXY-APPROVED V1.5-DISPATCH` 已出现）：**#197**。

---

## 5) Cloud / Automation 绑定

1. Automation / Cloud 仓库 = `luxingjiang1993/FreshLatch`（禁止空 repoUrl）。  
2. GitHub 授权含 issues 写（Evidence 评论、关单）与 PR。  
3. 从 **main** 启动；须已能读到本文件与 prompts（已推 main）。  
4. `gh auth` 失败或 cwd 无仓 → **立即停**，在 #196 评论「绑定仍坏」。  
5. 真人默认 **零打扰**；审核节点只走 Ronin。

---

## 6) 编排器备注

- 若 Ronin `GROK-PROXY-REJECT`：Cloud 修缺陷或新开会话，再通知代审；勿绕过代审直接 close。  
- 本文件为 Phase V1.5 主派工权威；I1/V1 dispatch 仅历史参考。
