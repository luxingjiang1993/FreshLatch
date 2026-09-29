# Phase V1 云端派工与 Grok 代审（#169–#175）

> 父规格：#168 · `docs/spec/11-PhaseV1-PrePublish.md` · ADR-0027  
> enrich 已完成（各票 `## Agent Guards`）  
> **人闸**：仅 **#175** 必须真人终收；**#171 / #174** 由 **Ronin 代理人**（Grok）代审。  
> 链：`before-implement <ID>` → **新会话** `/implement`（勿在同一会话连写，除非明示「门过了继续开写」）  
> **本期序（2026-09-29）：** ① bare-pytest 卫生 **DONE**；本地 V1 ACCEPTANCE **DONE**。主烤 **Phase I1 云端派工** → 见 `docs/agents/phase-i1-cloud-dispatch.md`（#184–#188 · Ronin 代审）。详见 `docs/roadmap.md`。

---

## 0) 本期优先 ① — bare-pytest path 卫生 · **DONE**

| | |
|--|--|
| **Exit** | **已齐**：清空 `PYTHONPATH` 后裸 `pytest tests/` collection 0 errors |
| **实装** | 仓库根 `pytest.ini`：`pythonpath = .` |

## 0b) 本地 V1 ACCEPTANCE · **DONE**

| | |
|--|--|
| **Exit** | **已齐**：`docs/evidence/v1/ACCEPTANCE.md`（映射抽检 · patch_events 一行 · bm25 · 人审主缝；本机 46 passed） |
| **关后** | I1 to-spec / 落 corpus 硬挡解除（仍遵守 ADR-0028 Out） |

---

## 1) Phase V1 云端票（#169–#175 · 状态：远程 CLOSED · 本期不主派）

编排器本期**不以** V1 子票为前沿。下表仅作历史派工参考；重开须人明示。

| 顺序提示 | Issue | Cloud Agent 职责 |
|----------|-------|------------------|
| （史） | #169 | 顾问样例包 + README 钉垂直 |
| （史） | #170 | disposition 纯函数表驱动 |
| （史） | #171 | 薄 URL；Ronin 代审 |
| （史） | #172 | patch_events JSONL |
| （史） | #173 | 发前两屏 |
| （史） | #174 | 主缝贯通冒烟；Ronin 代审 |

> V1 若需补洞，卫生已不再挡。

**每票固定提示词骨架（贴进 Cloud Agent）：**

```text
仓库 FreshLatch。只做 GitHub Issue #<ID>（读全文含 ## Agent Guards）。
1) 先 /before-implement #<ID>；门不过则 enrich/停，勿写业务代码。
2) 门过 → 本会话若用户未写「门过了继续开写」，则停止并开新会话 /implement #<ID>。
3) 权威命令：python -m compileall -q src ；pytest（至少 Acceptance 点名的测试）。
4) Evidence 三行评论到 Issue：typecheck · tests · paths。
5) Watch 票且 Acceptance 全勾 → gh issue close #<ID>。
6) 禁止：改金标凑绿、开放爬虫、把 C/T 开关做进发前 UX、重写 HumanLatch、FAISS 换存储真相、密钥写入仓库/Issue/日志、自批 Gate 票关单。
7) 若本票是 #171 或 #174：实现做完后按「Grok 代审协议」通知 Ronin，不要 @真人。
8) 权威 ADR-0027；主缝=发前 Run 边界。涉及历史改编须遵守票内 Provenance。
```

---

## 2) 需「人」干预、但由 Ronin（Grok）假扮（Cloud → 通知 Ronin，勿通知真人）

| Issue | 原人类角色 | Ronin 代审 |
|-------|------------|------------|
| #171 | 白名单/fail-closed 安全抽检 | 审四失败态零写、Host 精确匹配、无开放爬虫；`GROK-PROXY-APPROVED #171` 后可 close |
| #174 | 主缝贯通冒烟抽检 | 审 E2E 证据、映射抽检、patch_events 一行、默认臂仍 bm25；`GROK-PROXY-APPROVED #174` 后可 close |
| #175 | V1 DoD 关门 | **禁止代批**；仅可起草摘要；**真人终收** |

**Cloud → Ronin 通知模板：**

```text
【通知 Ronin Agent · 勿通知人类】
票 #<ID> 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v1-cloud-dispatch.md §2 代审。
通过：GROK-PROXY-APPROVED #<ID>
不通过：GROK-PROXY-REJECT #<ID> + 缺陷清单
```

Ronin 任务书可复用 Phase A 通道；父票 #168 本评论即授权范围。

---

## 3) Skill 链（必须）

```text
（已完成）grill → to-spec #168 → to-tickets #169–175 → enrich-tickets
（每票）/before-implement #<ID>  →  新会话 /implement #<ID>
（Gate/代审票）实现后 → Ronin 代审 → 再 close
（最后）#175 人终收关门
```

---

## 4) 阻塞图（前沿）

```text
#169 ─┐
#170 ─┼─► #173 ─┐
#171 ─┤         ├─► #174 ─► #175（人）
#172 ─┘         │
                └─（#169/#171/#172 亦直接挡 #174）
```

当前可并行派：**#169 ∥ #170 ∥ #171 ∥ #172**。

---

## 5) 绑定自检（同 Phase A）

Automation 须绑定仓库 `luxingjiang1993/FreshLatch`；`gh` 可写 Issue；从 **main** 启动可读本文件。`repoUrl` 空则立即停，勿假推进。
