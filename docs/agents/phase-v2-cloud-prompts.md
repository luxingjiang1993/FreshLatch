# Phase V2 — Cloud 全量提示词 + Ronin 通知（复制即用）

> 编排：`docs/agents/phase-v2-cloud-dispatch.md` · 父票 #226 · ADR-0031  
> **用法**：每票一 Cloud 会话（或 Automation 一轮只啃一票）；提示词整段粘贴。含「门过了继续开写」。  
> 真人默认零打扰；审核只走 Ronin。  
> **前置**：#226 已有 `GROK-PROXY-APPROVED V2-DISPATCH`。

---

## 0) 编排器 / Automation 检查清单（开跑前）

- [ ] #226 评论含 `GROK-PROXY-APPROVED V2-DISPATCH`
- [ ] `docs/agents/phase-v2-cloud-dispatch.md` 与本文件、ADR-0031、`docs/spec/14-PhaseV2-PublishHook.md` 已在 `main`
- [ ] 按阻塞图只派无 open blocker 的票
- [ ] 顺序：(#227 ∥ #228) → (#229 ∥ #230) → #231 → #232
- [ ] 一轮只做一个 Issue；做完再下一轮（并行前沿可同时开两个 Cloud）

---

## 编排器轮次提示词（Automation cron / 手工启动）

```text
你是 FreshLatch V2 编排+实现 Agent（Cloud）。仓库 luxingjiang1993/FreshLatch，从 main 工作。

## 零打扰
不要 @ 真人、不要等真人回复。人审一律走 Ronin（Grok）。

## 启动闸
1) gh issue view 226 --comments
2) 若无「GROK-PROXY-APPROVED V2-DISPATCH」→ 在 #226 评论「等待 V2-DISPATCH」并结束本轮。
3) 若有 → 继续。

## 选票（只选一张）
优先顺序：先并行前沿中编号最小且 open 且无 open blocker 的一张：
- #227、#228 互不阻塞（可任选未 CLOSED 者；建议优先 #227，其次 #228）
- #229 仅当 #227 CLOSED
- #230 仅当 #227 CLOSED
- #231 仅当 #228、#229、#230 均 CLOSED
- #232 仅当 #231 CLOSED
若本轮无票可做（全在等 Ronin 或全 CLOSED）→ 在 #226 评论状态一行并结束。

## 执行
对该票完整执行对应「Cloud → #N」提示词（见下文同名章节），含：
门过了继续开写 · before-implement · implement · 测绿 · Evidence 三行 · PR · 贴 Ronin 通知 · **不要**在无 GROK-PROXY-APPROVED #N 时 close。

## 若 Issue 评论已有 GROK-PROXY-APPROVED #N 且 Acceptance 齐
则 gh issue close #N，再结束本轮（下一轮 cron 会捡下一张）。

## 禁止
插件平台；图谱 CMS；Memo 商业裁决；扩 HumanLatch；双写作废表；整包再验挂钩子；改默认臂；自批关单；密钥入库；打扰真人；Exit 硬绑可发。
```

---

## 1) Cloud → #227（发前钩子闸核心）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #227。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 227（含 ## Agent Guards / Provenance）
- 派工：docs/agents/phase-v2-cloud-dispatch.md · docs/agents/phase-v2-cloud-prompts.md
- 父：#226 · ADR-0031 · 规格 docs/spec/14-PhaseV2-PublishHook.md
- 前置：#226 已有 GROK-PROXY-APPROVED V2-DISPATCH

## 要做
1. claim #227。
2. 实现确定性 evaluate_publish_hook（或等价）：run_id + disposition × ack_needs_patch × checksum 新鲜度 → allow/deny/code/message；勿发拒；需补丁无 ack 拒；ack 放行带需补丁约束；可发未漂放行；漂移拒；缺 run_id fail-closed。
3. 表驱动单测；零 LLM；不触发整包再验；不接线 UI/CLI/HTTP（留给后续票）。
4. Provenance：adapt 本仓 disposition/prepublish；禁止照抄 OpenManus ask_human、project 多agent approve_promotion。
5. 命令：python -m compileall -q src ；pytest tests/unit/test_publish_hook.py -q（文件名以实现为准）
6. Evidence 三行评论到 #227。开 PR 合 main（分支名含 227）。
7. **不要自行 close**。贴下面 Ronin 通知；等 GROK-PROXY-APPROVED #227 再 close。

## Ronin 通知（实现完成后原样贴到 #227）
【通知 Ronin Agent · 勿通知人类】
票 #227 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v2-cloud-dispatch.md §2 与用户 Store ronin-phase-v2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #227
不通过：GROK-PROXY-REJECT #227 + 缺陷清单
```

---

## 2) Cloud → #228（主张台账只读投影）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #228。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main · gh issue view 228
- 派工：phase-v2-cloud-dispatch.md · 父 #226 · ADR-0031
- 前置：GROK-PROXY-APPROVED V2-DISPATCH

## 要做
1. claim #228。
2. 只读投影 invalidation_list ∪ latch_log(discard/renew)；Run 详情旁路（可折叠）+ Markdown 导出；renew 不进作废名单；零新写表；不改 human_latch 写路径；不与 patch_events 糊缝。
3. Provenance：adapt 本仓 store/sheet；禁止新建双写 claim_ledger 表。
4. 命令：python -m compileall -q src ；pytest tests/unit/test_claim_ledger.py -q（文件名以实现为准）
5. Evidence 三行 → #228；PR 合 main（分支含 228）。
6. **不要自行 close**。贴 Ronin 通知等 GROK-PROXY-APPROVED #228。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #228 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v2-cloud-dispatch.md §2 与用户 Store ronin-phase-v2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #228
不通过：GROK-PROXY-REJECT #228 + 缺陷清单
```

---

## 3) Cloud → #229（Client Memo 套闸 CLI+UI）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #229。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。

## 权威
- gh issue view 229 · 派工 phase-v2 · 父 #226 · ADR-0031 / ADR-0015
- 前置：#227 CLOSED 且 V2-DISPATCH 已批；复用 #227 闸模块

## 要做
1. claim #229。
2. CLI client-memo 与 UI「导出客户备忘」共用 #227 闸；deny 零写文件；allow 遵守 Client Memo 字段集；需补丁+ack 强制标明；无商业裁决、无轨迹。
3. Provenance：对照 历史项目代码供参考/project 多agent/mission_control/app.py 只学入口；禁止 RAG-cy Streamlit。
4. 命令：compileall + pytest（票内 Acceptance 点名 + 既有 test_client_memo_export 回归）
5. Evidence → #229；PR；Ronin 通知；勿自关。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #229 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v2-cloud-dispatch.md §2 与用户 Store ronin-phase-v2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #229
不通过：GROK-PROXY-REJECT #229 + 缺陷清单
```

---

## 4) Cloud → #230（入站 publish-hook check）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #230。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。

## 权威
- gh issue view 230 · 父 #226 · ADR-0031
- 前置：#227 CLOSED；V2-DISPATCH 已批

## 要做
1. claim #230。
2. POST 入站 check：必填 run_id；可选 ack_needs_patch；同闸；deny 403/409；默认 127.0.0.1；可选 token 头。
3. 禁止：开放公网平台、出站通知顶替 check、Word/Notion 插件。
4. 命令：compileall + pytest test_publish_hook_api（以实现为准）
5. Evidence → #230；PR；Ronin 通知；勿自关。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #230 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v2-cloud-dispatch.md §2 与用户 Store ronin-phase-v2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #230
不通过：GROK-PROXY-REJECT #230 + 缺陷清单
```

---

## 5) Cloud → #231（冒烟 e2e + ACCEPTANCE）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #231。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。

## 权威
- gh issue view 231 · ADR-0031 Exit 预锁 · 父 #226
- 前置：#228 #229 #230 均 CLOSED

## 要做
1. claim #231。
2. 落 docs/evidence/v2/ACCEPTANCE.md：文首冒烟采用层；硬条 Memo 闸、curl allow≥1、curl deny≥1、台账 discard/renew；不硬绑可发；不报采用率。
3. 可复用 v1-mck-soai；形态对照 v15/i2 ACCEPTANCE。
4. Evidence → #231；PR；Ronin 通知；勿自关。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #231 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v2-cloud-dispatch.md §2 与用户 Store ronin-phase-v2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #231
不通过：GROK-PROXY-REJECT #231 + 缺陷清单
```

---

## 6) Cloud → #232（DoD close）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #232。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement。

## 权威
- gh issue view 232 · 形态对照 docs/evidence/v15/V15-DoD-CLOSE.md
- 前置：#231 CLOSED

## 要做
1. claim #232。
2. 写 docs/evidence/v2/V2-DoD-CLOSE.md：硬 Exit 引用 ACCEPTANCE；Out 未偷渡（无平台/图谱/双写/商业裁决/整包再验挂钩子/改臂/Studio）；curl≠平台已交付。
3. 在 #226 留收口评论指针；**不要**代关人终收类规则外的票除非 Ronin 已批。
4. Evidence → #232；PR；Ronin 通知；等 GROK-PROXY-APPROVED #232 再 close #232（并可建议 Ronin 收口 #226）。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #232 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v2-cloud-dispatch.md §2 与用户 Store ronin-phase-v2-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #232
不通过：GROK-PROXY-REJECT #232 + 缺陷清单
```
