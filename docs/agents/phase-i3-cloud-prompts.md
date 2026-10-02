# Phase I3 — Cloud 全量提示词 + Ronin 通知（复制即用）

> 编排：`docs/agents/phase-i3-cloud-dispatch.md` · 父票 #248 · ADR-0032  
> **用法**：每票一 Cloud 会话；提示词整段粘贴。含「门过了继续开写」。  
> **前置**：#248 已有 `GROK-PROXY-APPROVED I3-DISPATCH`。  
> **顺序**：#249 → #250 → #251 → #252 → #253（禁止跳序）。

---

## 0) 编排器检查清单

- [ ] #248 评论含 `GROK-PROXY-APPROVED I3-DISPATCH`
- [ ] `docs/agents/phase-i3-cloud-dispatch.md`、本文件、ADR-0032、`docs/spec/20-PhaseI3-InterviewHardening.md` 已在 `main`
- [ ] 只派无 open blocker 的一张；前序均 CLOSED
- [ ] 一轮只做一个 Issue

---

## 编排器轮次提示词

```text
你是 FreshLatch I3 编排+实现 Agent（Cloud）。仓库 luxingjiang1993/FreshLatch，从 main 工作。

## 零打扰
不要 @ 真人。人审一律走 Ronin（Grok）。

## 启动闸
1) gh issue view 248 --comments
2) 若无「GROK-PROXY-APPROVED I3-DISPATCH」→ 在 #248 评论「等待 I3-DISPATCH」并结束。
3) 若有 → 继续。

## 选票（只选一张 · 严格串行）
- #249 若 open 且无 blocker → 做 #249
- #250 仅当 #249 CLOSED
- #251 仅当 #250 CLOSED
- #252 仅当 #251 CLOSED
- #253 仅当 #252 CLOSED
若无票可做 → 在 #248 评论状态一行并结束。

## 执行
对该票完整执行对应「Cloud → #N」提示词：
**必须先 /before-implement #N，门过后再 /implement #N**（本会话授权「门过了继续开写」）。
测绿 · Evidence 三行 · PR · 贴 Ronin 通知 · **不要**在无 GROK-PROXY-APPROVED #N 时 close。

## 若已有 GROK-PROXY-APPROVED #N 且 Acceptance 齐
则 gh issue close #N，再结束本轮。

## 禁止
改默认臂；OPA；改写 rule_gate 不变量；Memory/多 Agent；Studio；跳序；自批关单；密钥入库；打扰真人。
```

---

## 1) Cloud → #249（Policy-as-code 出处禁区）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #249。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。
**硬顺序：必须先完成 before-implement，门过才允许写业务代码。**

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 249（含 ## Agent Guards）
- 派工：docs/agents/phase-i3-cloud-dispatch.md · docs/agents/phase-i3-cloud-prompts.md
- 父：#248 · ADR-0032 · 规格 docs/spec/20-PhaseI3-InterviewHardening.md
- 前置：#248 已有 GROK-PROXY-APPROVED I3-DISPATCH

## 要做
1. claim #249。
2. **/before-implement #249**：核对 ID/Acceptance/Paths/Provenance；门不过则停并评论缺口，勿写业务代码。
3. 门过 → **/implement #249**：声明式出处禁区规则 + Verify+ 旁路 → 政策拒不得绿灯；≥1 确定性夹具；零 LLM 单测。
4. **禁止**改写 rule_gate 不变量函数正文；禁止 OPA/Cedar；不做 B′/Hard-Gold。
5. 命令：python -m compileall -q src ；pytest tests/unit/test_i3_policy_gate.py -q（文件名以实现为准）
6. Evidence 三行评论到 #249。开 PR 合 main（分支名含 249）。
7. **不要自行 close**。贴 Ronin 通知；等 GROK-PROXY-APPROVED #249 再 close。

## Ronin 通知（实现完成后原样贴到 #249）
【通知 Ronin Agent · 勿通知人类】
票 #249 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i3-cloud-dispatch.md §2 代审。
通过：GROK-PROXY-APPROVED #249
不通过：GROK-PROXY-REJECT #249 + 缺陷清单
```

---

## 2) Cloud → #250（B′ 合成夹具）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #250。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。
**硬顺序：必须先 before-implement，门过才写业务代码。**

## 权威
- 前置：#249 CLOSED；#248 已有 I3-DISPATCH
- 读：gh issue view 250；派工/规格同 #249 章

## 要做
1. claim #250；确认 #249 CLOSED。
2. /before-implement #250 → 门过 → /implement #250。
3. 交付：超时/假绿→结构化错误；人审重放不双写；闸分布一页（CLI/MD）；标明合成夹具·非真事故。
4. 禁止 Memory/多 Agent；禁止整包再验挂回 publish_hook。
5. 命令：python -m compileall -q src ；pytest tests/unit/test_i3_agent_hardening.py -q
6. Evidence 三行 · PR（分支含 250）· Ronin 通知 · 勿自关。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #250 实现已完成。请按 docs/agents/phase-i3-cloud-dispatch.md §2 代审。
通过：GROK-PROXY-APPROVED #250
不通过：GROK-PROXY-REJECT #250 + 缺陷清单
```

---

## 3) Cloud → #251（Hard-Gold 骨架）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #251。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。
**硬顺序：必须先 before-implement，门过才写业务代码。**

## 权威
- 前置：#250 CLOSED；I3-DISPATCH 已批

## 要做
1. claim #251；确认 #250 CLOSED。
2. /before-implement #251 → 门过 → /implement #251。
3. Hard-Gold 规格（文首骨架·不改臂）；data/eval/retrieve_hard_gold.json 分文件 n≥20、traps/对抗≥30%；eval 可跑 hard；断言 PRODUCTION_RETRIEVAL_MODE=="bm25"。
4. **禁止**改生产默认臂；禁止把 smoke gold 改名冒充 Hard-Gold。
5. 命令：python -m compileall -q src ；pytest tests/unit/test_i3_hard_gold.py -q ；python -m freshlatch.eval retrieve（hard 旗标以实现为准）
6. Evidence · PR（分支含 251）· Ronin 通知 · 勿自关。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #251 实现已完成。请按 docs/agents/phase-i3-cloud-dispatch.md §2 代审。
通过：GROK-PROXY-APPROVED #251
不通过：GROK-PROXY-REJECT #251 + 缺陷清单
```

---

## 4) Cloud → #252（ACCEPTANCE）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #252。

## 门过了继续开写
**硬顺序：先 /before-implement #252，门过再 /implement。**

## 权威
- 前置：#251 CLOSED

## 要做
1. claim #252。
2. before-implement → implement：落 docs/evidence/i3/ACCEPTANCE.md；文首层标签强制；三轨分节硬条互不顶替；Hard-Gold 分节声明未授权改臂。
3. 复跑预锁命令使三节可勾。
4. Evidence · PR · Ronin 通知 · 勿自关。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #252 实现已完成。请按 docs/agents/phase-i3-cloud-dispatch.md §2 代审。
通过：GROK-PROXY-APPROVED #252
不通过：GROK-PROXY-REJECT #252 + 缺陷清单
```

---

## 5) Cloud → #253（DoD）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #253。

## 门过了继续开写
**硬顺序：先 /before-implement #253，门过再 /implement。**

## 权威
- 前置：#252 CLOSED

## 要做
1. claim #253。
2. before-implement → implement：落 docs/evidence/i3/I3-DoD-CLOSE.md；引用 ACCEPTANCE；Out 未偷渡表；父 #248 收口评论；更新 roadmap 关门行。
3. 不升格换臂/政策平台；不代关需真人终收的其他 issue。
4. Evidence · PR · Ronin 通知 · 等 GROK-PROXY-APPROVED #253 再 close。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #253 实现已完成。请按 docs/agents/phase-i3-cloud-dispatch.md §2 代审（Ronin 代 Exit）。
通过：GROK-PROXY-APPROVED #253
不通过：GROK-PROXY-REJECT #253 + 缺陷清单
```
