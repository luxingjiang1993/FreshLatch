# Phase I1 云端派工与 Grok 代审（#184–#188）

> 父规格：#183 · ADR-0028 · `docs/research/I1-失败三分法与HumanLatch语料设计评估.md`  
> enrich 已完成（各票 `## Agent Guards`）  
> **人闸策略**：凡原需真人 Watch/抽检/Exit 收口之处，一律委托 **Ronin 代理人**（Grok）。本阶段 **无**「仅真人终收」票。  
> 链：`before-implement <ID>` → **新会话** `/implement`（勿在同一会话连写，除非明示「门过了继续开写」）  
> **前置硬挡（已齐）**：① bare-pytest 卫生；本地 `docs/evidence/v1/ACCEPTANCE.md`

---

## 1) 交给 Cloud Agent 的票

编排器只派 **无 open blocker** 的票；一票一云端会话。从 **main** 启动。

| 顺序 | Issue | Cloud 职责 | 关单条件 |
|------|-------|------------|----------|
| 前沿 | #184 | I1 events 账本 + 单条样例贯通 | Watch：Acceptance 全勾 → **可自行 close** |
| #184 后并行 | #185 | 重标 W4/假绿 ≥3 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #185` 再 close |
| #184 后并行 | #186 | eval/轨迹评测挂标 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #186` 再 close |
| #184 后并行 | #187 | McK ≥1 `runnable=true` 金样 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #187` 再 close |
| #185+#186+#187 后 | #188 | Exit：索引 + ACCEPTANCE + 贡献口径 | 实现后 **通知 Ronin** → `GROK-PROXY-APPROVED #188` 再 close |

**每票固定提示词骨架（贴进 Cloud Agent）：**

```text
仓库 FreshLatch（luxingjiang1993/FreshLatch）。只做 GitHub Issue #<ID>（读全文含 ## Agent Guards）。
派工权威：docs/agents/phase-i1-cloud-dispatch.md ；父规格 #183 ；ADR-0028。
1) 先 /before-implement #<ID>；门不过则 enrich/停，勿写业务代码。
2) 门过 → 若用户未写「门过了继续开写」，则停止并开新会话 /implement #<ID>。
   （若本 Cloud 会话提示已含「门过了继续开写」则可同会话实现。）
3) 权威命令：python -m compileall -q src ；pytest（至少 Acceptance 点名的测试）。
4) Evidence 三行评论到 Issue：typecheck · tests · paths。
5) 关单：
   - #184：Watch 且 Acceptance 全勾 → gh issue close #<ID>
   - #185/#186/#187/#188：实现后按「Grok 代审协议」通知 Ronin，**等** GROK-PROXY-APPROVED #<ID> 再 close；勿 @真人
6) 禁止：改生产 Gate/disposition/HumanLatch 枚举；把三分法写成生产 status；编造无轨迹样本；用 replay_trace_only 冒充唯一 Exit 金样；改金标凑绿；密钥写入仓库/Issue/日志；自批未代审票关单。
7) 涉及历史改编须遵守票内 Provenance（历史项目代码供参考 ≠ 可改其语义）。
8) 文首冒烟声明；不报方差。
```

---

## 2) Ronin（Grok）代审（Cloud → 通知 Ronin，勿通知真人）

| Issue | 原人类角色 | Ronin 代审要点 |
|-------|------------|----------------|
| #185 | 语料抽检 | ≥3 条均有 `err_kind×fail_bucket`；有轨迹/对照锚；未用作废假绿当有效源；文首冒烟 |
| #186 | 改生产路径抽检 | 挂标字段名对齐 JSONL；`claim_final` 语义未漂；`VALID_ACTIONS`/`DISPOSITIONS` 未扩三分法 |
| #187 | 可复跑金样抽检 | ≥1 `runnable=true`；命令+decoding 齐全；不得仅靠 `replay_trace_only` |
| #188 | Exit 终收（本阶段由 Ronin 代） | 索引门槛；ACCEPTANCE 冒烟口径；贡献清单 I1 行；契约测绿 |

**Cloud → Ronin 通知模板：**

```text
【通知 Ronin Agent · 勿通知人类】
票 #<ID> 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i1-cloud-dispatch.md §2 代审。
通过：GROK-PROXY-APPROVED #<ID>
不通过：GROK-PROXY-REJECT #<ID> + 缺陷清单
```

Ronin 任务书：用户 Agent Store `ronin-phase-i1-proxy-brief.md`；父票 #183 授权评论。

---

## 3) Skill 链

```text
（已完成）grill → to-spec #183 → to-tickets #184–188 → enrich-tickets
（每票）/before-implement #<ID> → 新会话 /implement #<ID>
（#185/#186/#187/#188）实现后 → Ronin 代审 → close
（#184）绿即 close → 再并行派 #185∥#186∥#187 → 最后 #188
```

---

## 4) 阻塞图（前沿）

```text
#184 ─┬─► #185 ─┐
      ├─► #186 ─┼─► #188（Ronin 代 Exit）
      └─► #187 ─┘
```

当前可派：**#184 CLOSED 后** → **#185 ∥ #186 ∥ #187**（提示词全文见 `docs/agents/phase-i1-cloud-prompts.md`）；三票均 `GROK-PROXY-APPROVED` 并 CLOSED 后 → **#188**。

---

## 5) Cloud / Automation 绑定

1. Automation / Cloud 仓库 = `luxingjiang1993/FreshLatch`（禁止空 repoUrl）。  
2. GitHub 授权含 issues 写（Evidence 评论、关单）。  
3. #187 若需真跑 LLM：云端 Runtime Secret 已配模型 Key（勿写入 Issue）。无 Key 时仍须交出 `runnable=true` 金样路径（按票 Acceptance，不得只用 replay_only 顶 Exit）。  
4. 从 **main** 启动；须已能读到本文件（已推 main）。  
5. `gh auth` 失败或 cwd 无仓 → **立即停**，在 #183 评论「绑定仍坏」。

---

## 6) 编排器备注

- 真人默认 **零打扰**；审核节点只走 Ronin。  
- 若 Ronin `GROK-PROXY-REJECT`：Cloud 修缺陷或新开会话，再通知代审；勿绕过代审直接 close。  
- 本文件取代本期对 `phase-v1-cloud-dispatch.md` 的「主烤」地位；V1 派工表仅历史参考。
