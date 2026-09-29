# Phase I2 — Cloud 全量提示词 + Ronin 通知（复制即用）

> 编排：`docs/agents/phase-i2-cloud-dispatch.md` · 父票 #213 · ADR-0030  
> **用法**：每票一 Cloud 会话（或 Automation 一轮只啃一票）；提示词整段粘贴。含「门过了继续开写」。  
> 真人默认零打扰；审核只走 Ronin。  
> **前置**：#213 已有 `GROK-PROXY-APPROVED I2-DISPATCH`。

---

## 0) 编排器 / Automation 检查清单（开跑前）

- [ ] #213 评论含 `GROK-PROXY-APPROVED I2-DISPATCH`
- [ ] `docs/agents/phase-i2-cloud-dispatch.md` 与本文件已在 `main`
- [ ] 按阻塞图只派无 open blocker 的票
- [ ] 顺序：(#214 ∥ #215 ∥ #216) → #217 → #218 → #219
- [ ] 一轮只做一个 Issue；做完再下一轮

---

## 编排器轮次提示词（Automation cron / 手工启动）

```text
你是 FreshLatch I2 编排+实现 Agent（Cloud）。仓库 luxingjiang1993/FreshLatch，从 main 工作。

## 零打扰
不要 @ 真人、不要等真人回复。人审一律走 Ronin（Grok）。

## 启动闸
1) gh issue view 213 --comments
2) 若无「GROK-PROXY-APPROVED I2-DISPATCH」→ 在 #213 评论「等待 I2-DISPATCH」并结束本轮。
3) 若有 → 继续。

## 选票（只选一张）
优先顺序：先并行前沿中编号最小且 open 且无 open blocker 的一张：
- #214、#215、#216 互不阻塞（可任选未 CLOSED 者；建议优先 #214，其次 #215，再次 #216）
- #217 仅当 #214 与 #215 均 CLOSED
- #218 仅当 #214、#215、#217 均 CLOSED
- #219 仅当 #218 CLOSED
若本轮无票可做（全在等 Ronin 或全 CLOSED）→ 在 #213 评论状态一行并结束。

## 执行
对该票完整执行对应「Cloud → #N」提示词（见下文同名章节），含：
门过了继续开写 · before-implement · implement · 测绿 · Evidence 三行 · PR · 贴 Ronin 通知 · **不要**在无 GROK-PROXY-APPROVED #N 时 close。

## 若 Issue 评论已有 GROK-PROXY-APPROVED #N 且 Acceptance 齐
则 gh issue close #N，再结束本轮（下一轮 cron 会捡下一张）。

## 禁止
安全平台；#4 顶替 Exit；自批关单；密钥入库；改生产默认臂；打扰真人。
```

---

## 1) Cloud → #214（召回信任边界）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #214。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 214（含 ## Agent Guards / Provenance）
- 派工：docs/agents/phase-i2-cloud-dispatch.md · docs/agents/phase-i2-cloud-prompts.md
- 父：#213 · ADR-0030
- 前置：#213 已有 GROK-PROXY-APPROVED I2-DISPATCH

## 要做
1. claim #214。
2. 可选 tenant_id + poison/untrusted；retrieve 显式 tenant 硬过滤；poison 剔除；无参兼容；Forensic 直调不旁路；夹具 acl-t001/poison-t001 + 确定性测。
3. Provenance：对照 docs/research/参考代码盘点.md → 历史项目代码供参考/project 多agent/rag.py 仅思路；禁止 CASE-高效召回整包、10课沙箱当 ACL、quarantine 当租户。
4. 命令：python -m compileall -q src ；pytest tests/unit/test_store.py tests/unit/test_i2_retrieve_trust.py -q（文件名以实现为准）
5. Evidence 三行评论到 #214。开 PR 合 main。
6. **不要自行 close**。贴下面 Ronin 通知；等 GROK-PROXY-APPROVED #214 再 close。

## Ronin 通知（实现完成后原样贴到 #214）
【通知 Ronin Agent · 勿通知人类】
票 #214 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i2-cloud-dispatch.md §2 与用户 Store ronin-phase-i2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #214
不通过：GROK-PROXY-REJECT #214 + 缺陷清单
```

---

## 2) Cloud → #215（注入 Gate 确定性）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #215。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main · gh issue view 215
- 派工：phase-i2-cloud-dispatch.md · 父 #213 · ADR-0030
- 前置：GROK-PROXY-APPROVED I2-DISPATCH

## 要做
1. claim #215。
2. inj-t001 + rule_gate/_finalize 确定性拒绿；禁止挂 meta_gate；零 LLM。
3. 命令：python -m compileall -q src ；pytest tests/unit/test_rule_gate.py tests/unit/test_i2_injection_gate.py -q
4. Evidence；开 PR；**不要自行 close**；贴 Ronin 通知。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #215 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i2-cloud-dispatch.md §2 与用户 Store ronin-phase-i2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #215
不通过：GROK-PROXY-REJECT #215 + 缺陷清单
```

---

## 3) Cloud → #216（可选 #4 adv-fresh）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #216（可选票）。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。

## 权威
- gh issue view 216 · phase-i2-cloud-dispatch.md · #213 · ADR-0030
- 前置：GROK-PROXY-APPROVED I2-DISPATCH
- 本票不挡 #217/#218/#219 硬链

## 要做
1. claim #216。
2. 仅 1 条 adv-fresh-t001；明示不计入 I2 Exit；禁止改 adversarial INDEX 升版=Done。
3. Evidence；开 PR；贴 Ronin 通知；勿自关。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #216 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i2-cloud-dispatch.md §2 与用户 Store ronin-phase-i2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #216
不通过：GROK-PROXY-REJECT #216 + 缺陷清单
```

---

## 4) Cloud → #217（security.md + evidence 短页）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #217。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。

## 权威
- 依赖 #214 与 #215 已 CLOSED · gh issue view 217 · phase-i2-cloud-dispatch.md

## 要做
1. claim #217。
2. docs/security.md 三行薄表 + docs/evidence/i2/ 短索引；冒烟声明；#4 不进硬行。
3. 路径存在性验收；Evidence；开 PR；贴 Ronin 通知；勿自关。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #217 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i2-cloud-dispatch.md §2 与用户 Store ronin-phase-i2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #217
不通过：GROK-PROXY-REJECT #217 + 缺陷清单
```

---

## 5) Cloud → #218（注入 e2e + ACCEPTANCE）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #218。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。

## 权威
- 依赖 #214+#215+#217 CLOSED · gh issue view 218 · ADR-0030 分层硬门

## 要做
1. claim #218。
2. 注入 1× Lead+Critic+LLM 冒烟；ACCEPTANCE 文首冒烟+decoding；硬勾三例确定性；无 Key 不伪造通过；ACL/poison 不绑 LLM。
3. Evidence；开 PR；贴 Ronin 通知；勿自关。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #218 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i2-cloud-dispatch.md §2 与用户 Store ronin-phase-i2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #218
不通过：GROK-PROXY-REJECT #218 + 缺陷清单
```

---

## 6) Cloud → #219（DoD CLOSE）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #219。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。

## 权威
- 依赖 #218 CLOSED · 形态对齐 docs/evidence/v15/V15-DoD-CLOSE.md

## 要做
1. claim #219。
2. 写 i2 DoD 关门摘要；核对 Out 未偷渡；#213 收口评论；#216 可选不挡硬关。
3. Evidence；开 PR；贴 Ronin 通知；等 GROK-PROXY-APPROVED #219 再 close（Ronin 代 Exit）。勿 @真人。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #219 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i2-cloud-dispatch.md §2 与用户 Store ronin-phase-i2-proxy-brief.md 代审（本票=Exit 代收）。
通过：GROK-PROXY-APPROVED #219
不通过：GROK-PROXY-REJECT #219 + 缺陷清单
```
