# Phase V1.5 — Cloud 全量提示词 + Ronin 通知（复制即用）

> 编排：`docs/agents/phase-v15-cloud-dispatch.md` · 父票 #196 · ADR-0029  
> **用法**：每票一 Cloud 会话；提示词整段粘贴。含「门过了继续开写」。  
> 真人默认零打扰；审核只走 Ronin。  
> **前置**：#196 已有 `GROK-PROXY-APPROVED V1.5-DISPATCH`。

---

## 0) 编排器检查清单（开跑前）

- [ ] #196 评论含 `GROK-PROXY-APPROVED V1.5-DISPATCH`
- [ ] `docs/agents/phase-v15-cloud-dispatch.md` 与本文件已在 `main`
- [ ] 按阻塞图只派无 open blocker 的票
- [ ] 顺序：#197 → #198 →（#199 ∥ #200 ∥ #201）→ #202 → #203

---

## 1) Cloud → #197（patch_events before/after）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #197。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 197（含 ## Agent Guards）
- 派工：docs/agents/phase-v15-cloud-dispatch.md · docs/agents/phase-v15-cloud-prompts.md
- 父：#196 · ADR-0029 / ADR-0027

## 要做
1. claim #197。
2. 扩展 patch_events：正式确认可写 before_text/after_text；旧行缺字段可读；产品写 T 约定；发前无 C/T 开关。
3. 命令：python -m compileall -q src ；pytest tests/unit/test_patch_events.py -q
4. Evidence 三行评论到 #197。
5. Watch：Acceptance 全勾后 gh issue close 197；开 PR 合 main。
6. 禁止改 HumanLatch / 做薄对话 / 做完整 propose/confirm（属 #198）。
```

---

## 2) Cloud → #198（propose/confirm 核心）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #198。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 198（含 ## Agent Guards / Provenance）
- 派工：docs/agents/phase-v15-cloud-dispatch.md · docs/agents/phase-v15-cloud-prompts.md
- 父：#196 · ADR-0029 · 依赖 #197 已合 main

## 要做
1. claim #198。
2. 实现 propose_patch（暂存零写）与 confirm_patch（资格闸+T1硬闸+覆盖正文+patch_events arm=T+before/after+返回 disposition）。再验可留钩子，真接线属 #199。
3. VALID_ACTIONS 仍仅 discard|renew。禁止 C|T UX、薄对话、renew 改正文、照抄 ask_human/approve_promotion。
4. 命令：python -m compileall -q src ；pytest tests/unit/test_evidence_bound_patch.py -q
5. Evidence 三行评论到 #198。开 PR。
6. **不要自行 close**。贴下面 Ronin 通知；等 GROK-PROXY-APPROVED #198 再 close。

## Ronin 通知（实现完成后原样贴到 #198）
【通知 Ronin Agent · 勿通知人类】
票 #198 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v15-cloud-dispatch.md §2 与用户 Store ronin-phase-v15-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #198
不通过：GROK-PROXY-REJECT #198 + 缺陷清单
```

---

## 3) Cloud → #199（单条再验）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #199。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 199 · 派工 phase-v15-cloud-dispatch.md
- 依赖 #198 已合 main

## 要做
1. claim #199。
2. confirm 成功后触发单条再验（同构 latch rerun 粒度）；reverify=true；重算 disposition；禁止整包唯一路径。
3. 命令：python -m compileall -q src ；pytest tests/unit/test_evidence_bound_patch.py tests/unit/test_ui_latch.py tests/unit/test_latch.py -q
4. Evidence 三行；开 PR；**不要自行 close**；贴 Ronin 通知。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #199 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v15-cloud-dispatch.md §2 与用户 Store ronin-phase-v15-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #199
不通过：GROK-PROXY-REJECT #199 + 缺陷清单
```

---

## 4) Cloud → #200（补丁 UI 条带）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #200。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 200（Provenance=adapt mission_control + 本仓 UI）
- 依赖 #198 已合 main

## 要做
1. claim #200。
2. 复验单/Run 详情增量补丁条带：after_text、本 Run 已入库 t1 多选、minutes、确认/丢弃；走 propose/confirm。无薄对话、无独立补丁台、无 C|T 开关。
3. Provenance：可参考 历史项目代码供参考/project 多agent/mission_control/app.py IA，勿抄编排角色名；禁 Streamlit 第二栈。
4. 命令：python -m compileall -q src ；pytest tests/unit/test_ui_latch.py tests/unit/test_evidence_bound_ui.py -q
5. Evidence；开 PR；**不要自行 close**；贴 Ronin 通知。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #200 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v15-cloud-dispatch.md §2 与用户 Store ronin-phase-v15-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #200
不通过：GROK-PROXY-REJECT #200 + 缺陷清单
```

---

## 5) Cloud → #201（导出包）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #201。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 201 · 依赖 #198 已合 main

## 要做
1. claim #201。
2. 导出 JSON + 短 Markdown：before/after、t1 指针、确认者、再验前后 disposition；与 Client Memo 分轨；禁 Streamlit。
3. 命令：python -m compileall -q src ；pytest tests/unit/test_evidence_bound_export.py -q
4. Evidence；开 PR；**不要自行 close**；贴 Ronin 通知。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #201 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-v15-cloud-dispatch.md §2 与用户 Store ronin-phase-v15-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #201
不通过：GROK-PROXY-REJECT #201 + 缺陷清单
```

---

## 6) Cloud → #202（e2e + ACCEPTANCE）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #202。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 202 · 依赖 #199+#200+#201 均 CLOSED 且合 main
- ADR-0029 Exit 预锁脚本

## 要做
1. claim #202。
2. 落 docs/evidence/v15/ACCEPTANCE.md（文首冒烟）；硬条四勾；升可发仅加分；预锁 discard mck-1&4 → patch mck-3 → confirm → 再验 → 导出（夹具等价可）。
3. 命令：python -m compileall -q src ；pytest tests/unit/test_evidence_bound_e2e.py tests/unit/test_prepublish_e2e.py -q
4. Evidence；开 PR；**不要自行 close**；贴 Ronin 通知。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #202 实现已完成。请读取 Evidence/报告与 docs/evidence/v15/ACCEPTANCE.md，按 docs/agents/phase-v15-cloud-dispatch.md §2 与用户 Store ronin-phase-v15-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #202
不通过：GROK-PROXY-REJECT #202 + 缺陷清单
```

---

## 7) Cloud → #203（DoD · Ronin 代 Exit）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #203。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 203 · 依赖 #202 CLOSED
- 形态对齐 docs/evidence/v1/V1-DoD-CLOSE.md

## 要做
1. claim #203。
2. 关门摘要：硬 Exit 可引用；Out 未偷渡；冒烟口径；路线图/README 叙事一致。不升格 Hard-Gold。
3. 命令：python -m compileall -q src ；rg -n "Evidence-bound|薄对话|V1.5" README.md docs/roadmap.md docs/evidence/v15/ACCEPTANCE.md
4. Evidence；开 PR；**不要自行 close**；贴 Ronin 通知（本票 Exit 由 Ronin 代批，勿 @真人）。

## Ronin 通知
【通知 Ronin Agent · 勿通知人类】
票 #203 实现已完成（V1.5 DoD）。请按 docs/agents/phase-v15-cloud-dispatch.md §2 与用户 Store ronin-phase-v15-proxy-brief.md 代 Exit。
通过：GROK-PROXY-APPROVED #203
不通过：GROK-PROXY-REJECT #203 + 缺陷清单
```
