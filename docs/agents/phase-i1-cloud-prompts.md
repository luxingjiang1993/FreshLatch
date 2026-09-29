# Phase I1 — Cloud 全量提示词 + Ronin 通知（复制即用）

> 编排：`docs/agents/phase-i1-cloud-dispatch.md` · 父票 #183 · ADR-0028  
> **用法**：每票一 Cloud 会话；提示词整段粘贴。含「门过了继续开写」。  
> 真人默认零打扰；审核只走 Ronin。

---

## 0) 编排器检查清单（开跑前）

- [ ] #184 CLOSED 且 PR 已合入 `main`（否则后续票从 main 起会缺 `i1_events`）
- [ ] `docs/agents/phase-i1-cloud-dispatch.md` 已在 `main`
- [ ] #185/#186/#187 的 `blocked_by` = 0
- [ ] 并行派：#185 ∥ #186 ∥ #187；三者 + Ronin 批准后派 #188

---

## 1) Cloud → #185（重标 W4/假绿 ≥3）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #185。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 185（含 ## Agent Guards / Executor）
- 派工：docs/agents/phase-i1-cloud-dispatch.md · 提示词包：docs/agents/phase-i1-cloud-prompts.md
- 父：#183 · ADR-0028 · 账本已由 #184 落地（i1_events）

## 要做
1. claim #185（assignee @me 若可行）。
2. 用既有 I1 账本 API，从 docs/evidence/w4/ 可引用假绿/对照与既有轨迹**重标** ≥3 条漏拦/误拦：
   - 每条同时有 err_kind∈{漏拦,误拦} 与 fail_bucket∈{找不到,找错,没用上}
   - 每条 evidence md（文首答辩/冒烟）+ events.jsonl 行 + trajectory_ptr/对照锚
   - 更新短索引列出 ≥3 条 sample_id 与主键标签
3. 禁止：编造无轨迹样本；作废假绿运行当有效源；改 W4 预登记通过线/作废线；改生产枚举。
4. 命令：python -m compileall -q src ；pytest tests/unit/test_i1_events.py -q（及本票新增测）
5. Evidence 三行评论到 #185。
6. **不要自行 close**。实现完成后在 #185 发下面「Ronin 通知」整段，然后停止等 GROK-PROXY-APPROVED #185；批准后再 gh issue close 185。
7. 开 PR（分支名含 185）合回 main。

## Ronin 通知（实现完成后原样贴到 #185）
【通知 Ronin Agent · 勿通知人类】
票 #185 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i1-cloud-dispatch.md §2 与用户 Store ronin-phase-i1-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #185
不通过：GROK-PROXY-REJECT #185 + 缺陷清单
```

---

## 2) Cloud → #186（eval/轨迹评测挂标）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #186。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 186（含 ## Agent Guards / Executor）
- 派工：docs/agents/phase-i1-cloud-dispatch.md · docs/agents/phase-i1-cloud-prompts.md
- 父：#183 · ADR-0028 · I1 JSONL 字段与 #184 对齐

## 要做
1. claim #186。
2. 在 eval/轨迹侧挂与 I1 JSONL **同名**字段（至少 fail_bucket、err_kind）：
   - 历史代码供参考：src/freshlatch/runner.py（_dump_trajectory/claim_final）、src/freshlatch/eval/runner.py
   - 只加评测挂标面；**不改** claim_final 生产终态语义
3. Do-not-touch：human_latch.VALID_ACTIONS；disposition.DISPOSITIONS
4. 测试：tests/unit/test_i1_trajectory_labels.py（挂得上 + 生产语义未漂 + 枚举未扩）
5. 命令：python -m compileall -q src ；pytest tests/unit/test_i1_trajectory_labels.py tests/unit/test_i1_events.py -q
6. Evidence 三行评论到 #186。
7. **不要自行 close**。贴下面 Ronin 通知；等 GROK-PROXY-APPROVED #186 再 close。
8. 开 PR（分支名含 186）。

## Ronin 通知（实现完成后原样贴到 #186）
【通知 Ronin Agent · 勿通知人类】
票 #186 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i1-cloud-dispatch.md §2 与用户 Store ronin-phase-i1-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #186
不通过：GROK-PROXY-REJECT #186 + 缺陷清单
```

---

## 3) Cloud → #187（McK ≥1 runnable=true 金样）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #187。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 187（含 ## Agent Guards / Executor）
- 派工：docs/agents/phase-i1-cloud-dispatch.md · docs/agents/phase-i1-cloud-prompts.md
- 父：#183 · ADR-0028 · V1 包 data/packs/v1-mck-soai/

## 要做
1. claim #187。
2. 从顾问垂直 McK SoAI 新跑并落档 ≥1 条 runnable=true 金样：
   - evidence 页含可复跑命令 + 模型/temperature/seed/日期
   - 写入 docs/evidence/i1/ 页 + events.jsonl（err_kind×fail_bucket，package_disp 可选）
   - 文首冒烟；诚实写托管漂移/跨会话复现为近似
3. Do-not-touch：HumanLatch 封闭集、disposition 聚合、PRODUCTION_RETRIEVAL_MODE
4. 禁止：仅用 runnable=replay_trace_only 顶本票 Exit 金样；改生产算法凑样本
5. 若无 LLM Key：仍须给出 runnable=true 的可复跑路径（脚本+命令+decoding 记录）；不得只用看日志冒充
6. 命令：python -m compileall -q src ；pytest tests/unit/test_i1_events.py -q
7. Evidence 三行评论到 #187。
8. **不要自行 close**。贴下面 Ronin 通知；等 GROK-PROXY-APPROVED #187 再 close。
9. 开 PR（分支名含 187）。

## Ronin 通知（实现完成后原样贴到 #187）
【通知 Ronin Agent · 勿通知人类】
票 #187 实现已完成。请读取 Evidence/报告，按 docs/agents/phase-i1-cloud-dispatch.md §2 与用户 Store ronin-phase-i1-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #187
不通过：GROK-PROXY-REJECT #187 + 缺陷清单
```

---

## 4) Cloud → #188（Exit · 仅当前三者 CLOSED 且均已 APPROVED 后派）

```text
你是 FreshLatch Cloud 实现 Agent。只做 GitHub Issue #188。

## 门过了继续开写
本会话授权：/before-implement 通过后，同一会话继续 /implement，不要停等新会话。

## 前置自检（缺一即停并评论到 #183）
- #185/#186/#187 均为 CLOSED
- 三票评论区均存在 GROK-PROXY-APPROVED #<id>

## 权威
- 仓：luxingjiang1993/FreshLatch · 从 main 启动
- 读：gh issue view 188
- 派工：docs/agents/phase-i1-cloud-dispatch.md · docs/agents/phase-i1-cloud-prompts.md

## 要做
1. claim #188。
2. 短索引一眼：漏/误 ≥3 且 runnable=true ≥1。
3. 落 docs/evidence/i1/ACCEPTANCE.md（文首冒烟；指向索引/金样；不报方差）。
4. 更新 docs/contribution-boundary.md：I1 行含「失败三分法 + 可复盘误判样本」+ 冒烟口径。
5. 契约测：tests/unit/test_i1_exit_contract.py（或等价）锁计数 + 生产枚举未扩。
6. 命令：python -m compileall -q src ；pytest tests/unit/test_i1_events.py tests/unit/test_i1_exit_contract.py -q
7. Evidence 三行评论到 #188。
8. **不要自行 close**。贴下面 Ronin 通知；等 GROK-PROXY-APPROVED #188 再 close（Exit 由 Ronin 代批，勿 @真人）。
9. 开 PR（分支名含 188）。

## Ronin 通知（实现完成后原样贴到 #188）
【通知 Ronin Agent · 勿通知人类】
票 #188 实现已完成（I1 Exit）。请读取 Evidence/ACCEPTANCE/贡献清单，按 docs/agents/phase-i1-cloud-dispatch.md §2 与用户 Store ronin-phase-i1-proxy-brief.md 代审。
通过：GROK-PROXY-APPROVED #188
不通过：GROK-PROXY-REJECT #188 + 缺陷清单
```

---

## 5) Ronin 代审回复模板（Ronin bot 用）

**通过：**

```text
GROK-PROXY-APPROVED #<ID>

代审清单（勾选摘要）：
- …
依据：Issue Evidence 三行 + 相关路径抽检。层=答辩/冒烟，不升格统计。
```

**不通过：**

```text
GROK-PROXY-REJECT #<ID>

缺陷清单：
1. …
请 Cloud 修复后再次 【通知 Ronin Agent · 勿通知人类】。
```

---

## 6) 编排器 → Issue 派工评论模板

**并行波（#184 已合 main 后贴到 #183）：**

```text
## 编排：并行派 #185∥#186∥#187
前置：#184 CLOSED + 实现已在 main。
Cloud 提示词全文见 docs/agents/phase-i1-cloud-prompts.md §1–§3。
Ronin：子票出现【通知 Ronin Agent】后按 ronin-phase-i1-proxy-brief.md 代审。
真人零打扰。
```

**Exit 波（三票均 APPROVED+CLOSED 后贴到 #183）：**

```text
## 编排：派 #188 Exit
前置：#185/#186/#187 均 CLOSED 且均有 GROK-PROXY-APPROVED。
Cloud 提示词见 docs/agents/phase-i1-cloud-prompts.md §4。
Ronin 代批 Exit。真人零打扰。
```
