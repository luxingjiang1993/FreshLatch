# Phase A 云端派工与 Grok 代审（#156–#166）

> 父规格：#155 · enrich 已完成  
> **人闸**：仅 **#166** 必须真人；#160/#161/#163 由 **Ronin 代理人**（Grok）代审。  
> **#165**：授权实现 Agent **自备脱敏 PDF/真文档冒烟样本**（勿用含真实隐私的材料）。  
> 链：`before-implement <ID>` → **新会话** `/implement`（勿在同一会话连写，除非明示「门过了继续开写」）

---

## 1) 交给 Cloud Agent 的票（实现 + 可自行关单）

编排器只派 **无 open blocker** 的票；一票一云端会话。

| 顺序提示 | Issue | Cloud Agent 职责 |
|----------|-------|------------------|
| 前沿 | #156 | 文档 ADR/路线图；绿即 close |
| 前沿 | #157 | retrieve 契约/轨迹/mode；pytest 回放绿即 close |
| #157 后 | #158 | 主张查询变换 + Lead/Critic；绿即 close |
| #157 后 | #165 | PDF→同构锚冒烟（需样本，见 §4）；绿即 close |
| #158 后 | #159 | 金标+eval+基线；绿即 close |
| #159 后 | #164 | 变换前后对比（默认无 LLM）；绿即 close |
| #161 后 | #162 | Hybrid RRF 三列；绿即 close |

**每票固定提示词骨架（贴进 Cloud Agent）：**

```text
仓库 FreshLatch。只做 GitHub Issue #<ID>（读全文含 ## Agent Guards）。
1) 先 /before-implement #<ID>；门不过则 enrich/停，勿写业务代码。
2) 门过 → 本会话若用户未写「门过了继续开写」，则停止并开新会话 /implement #<ID>。
3) 权威命令：python -m compileall -q src ；pytest（至少 Acceptance 点名的测试）。
4) Evidence 三行评论到 Issue：typecheck · tests · paths。
5) Watch 票且 Acceptance 全勾 → gh issue close #<ID>。
6) 禁止：改 gold 凑绿、FAISS 换存储真相、把密钥写入仓库/Issue/日志、自批 Gate 票关单。
7) 若本票是 #160/#161/#163：实现做完后按「Grok 代审协议」通知 Grok，不要 @真人。
```

---

## 2) 需「人」干预、但由 Ronin（Grok）假扮（Cloud → 通知 Ronin，勿通知真人）

| Issue | 原人类角色 | Ronin 代审 |
|-------|------------|------------|
| #160 | Spot-check 陷阱金标 | 按标注卡审；`GROK-PROXY-APPROVED #160` 后可 close |
| #161 | Gate(db)+密钥 | 审 Acceptance/降级/无密钥进日志；批准后可 close |
| #163 | 生产默认开闭 | 机械套 Recall@10∧p95≤800ms；批准后可 close |
| #166 | 阶段关门 | **禁止代批**；仅可起草；真人终收 |

**Cloud → Ronin 通知模板：**

```text
【通知 Ronin Agent · 勿通知人类】
票 #<ID> 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-a-cloud-dispatch.md §2 代审。
通过：GROK-PROXY-APPROVED #<ID>
不通过：GROK-PROXY-REJECT #<ID> + 缺陷清单
```

Ronin 任务书副本：用户 Agent Store `ronin-phase-a-proxy-brief.md`；父票 #155 已留授权评论。
---

## 3) Skill 链（必须）

```text
（已完成）grill → to-spec #155 → to-tickets #156–166 → enrich-tickets
（每票）/before-implement #<ID>  →  新会话 /implement #<ID>
（Gate/代审票）实现后 → Grok 代审 → 再 close
（最后）#166 关门汇总
```

- `before-implement`：只做门禁，默认**不写代码**，打印交接句后停。  
- `implement`：TDD 缝上实现 → typecheck/tests → code-review → commit。  
- 本仓权威命令见 `docs/agents/agent-guards.md`。

---

## 4) 现在还需要你提供 / 拍板的（缺一项编排器就卡）

| # | 你要提供或确认的 | 为什么 | 默认建议 |
|---|------------------|--------|----------|
| A | **书面授权**：「#160/#161/#163（及是否含 #166）允许 Grok 代审并 `GROK-PROXY-APPROVED` 后关单」 | 否则与 Agent Guards「人批 Gate」冲突，Cloud 不敢关 | 授权 160/161/163；#166 仍可只给你 |
| B | **Grok 通道**：怎么唤起（Cursor 里另一个 Agent / xAI API / 飞书机器人 / 只留 Issue 评论等人看 Bot） | 没有通道就「通知 Grok」落空 | 你选定一种并给接入方式 |
| C | **Cloud 环境密钥**：云端是否已注入 `DASHSCOPE_API_KEY`（勿贴 key 到聊天） | #161 真 dense；否则只验 fallback | 本机有密钥；云端你确认 Secret 开关 |
| D | **#165 真 PDF**：放哪（路径或上传）；`data/` 下目前无 PDF | 冒烟样本 | 你丢一份进 `data/smoke/` 或授权 Agent 自备脱敏 PDF |
| E | **谁当编排器**：你手动按前沿派 Cloud，还是 Autopilot/脚本轮询 `gh` | blocking 不会自动派工 | 先手动派 #156∥#157，或让我写轮询脚本 |
| F | **分支策略**：Cloud 是否允许 push / 是否每票独立 PR | 避免抢同一分支 | 每票 `feat/phase-a-<id>` 或单集成分支 |
| G | **#166 终收件人**：只要 Grok，还是你也要看终包 | 决定编排器停在哪 | 建议你仍看 #166 一页 |

## 5) Cloud / Automation 绑定（防空 repoUrl）

若运行日志出现 `repoUrl` 为空、无仓库检出、`gh` 未登录：

1. Automation 必须选中仓库 **`luxingjiang1993/FreshLatch`**（或绑定已含该仓的 Cloud Environment），禁止「Start from scratch / 无仓」。
2. GitHub 账号对 Cursor Cloud 已授权 **contents + issues 写**（评论 Evidence、关单）。
3. Secrets 已有 `DASHSCOPE_API_KEY`（Runtime Secret）即可；勿写入 Issue。
4. 仓库根已提交 `.cursor/environment.json`（`install`=pip install）；Agent 从 **main** 启动才能读到 `docs/agents/phase-a-cloud-dispatch.md`。

编排器自检：若 `gh auth status` 失败或 cwd 无 FreshLatch → **立即停**，在 #155 评论「绑定仍坏」，不要假装推进 #156/#157。

**你现在最少只需回四句：**  
1）授权代审范围（例如「160/161/163 给 Grok，166 仍给我」）  
2）Grok 怎么叫  
3）云端 Secret：已配 / 未配 / #161 改本机跑  
4）#165 PDF：我来放 / Agent 自备  

其余（派 #156/#157）我可以在你确认后立刻开写编排或帮你生成首张 Cloud 提示词全文。
