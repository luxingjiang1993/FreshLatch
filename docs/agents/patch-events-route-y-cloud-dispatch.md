# patch_events 路线 Y · 云端派工说明

> 四件套 PR [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493) · 规格卷 27 · ADR-0037 · **缺额解锁 ADR-0038**  
> **硬前置**：`PREREG-Y` **未激活**；不得发模型除非人授探针票；不得改 B/C 冻结归档；**不得**静默改小 n=400 配额。

## 链

```text
grill-with-docs → 四件套(#493) → to-spec(卷27) → to-tickets → enrich-tickets → before-implement → /implement
         └─ 缺额 grill（ADR-0038）→ PE-Y-CORPUS-* →（齐闸后）才考虑 PE-Y-05
```

## 边界

| 允许 | 禁止 |
|---|---|
| formal-y 旁路、GATE-Y 可扔报告、n=400 名单 | 激活 PREREG-Y；正式 n=400 进主表（未过门/缺额） |
| RESULT-Y 壳 + Y 成立口径单测 | 改 PREREG-B/C / RESULT-B/C / formal-generations-b/c |
| 继承 R / 同 after / 软对齐 | C 强制抄句当 Y 主路径；放松 hard reject；金标进 score；复活 A |
| B1/B2 报告-only | 称甲 / soft-甲；新造 compare_*；ALT/夹具进主表 |
| **扩 pe_v2 至可满 400+预留**（ADR-0038） | **静默改小配额**；第二领域凑数；未扩满派 PE-Y-05 |

## 票序进度（Cloud）

| 序 | 票 | 状态 |
|---|---|---|
| 1 | formal-y 旁路 · PE-Y-01 | **DONE** · PR [#494](https://github.com/luxingjiang1993/FreshLatch/pull/494) · [agent](https://cursor.com/agents/bc-5a2978df-d5a8-5696-88cc-5a2d80343cf0) |
| 2 | GATE-Y-PROBE · PE-Y-02 | **DONE** · PR [#495](https://github.com/luxingjiang1993/FreshLatch/pull/495) · [agent](https://cursor.com/agents/bc-e1bba9e6-7fa1-5f6f-ab30-1cf841c76882) |
| 3 | n=400 名单 · PE-Y-03 | **DONE** · PR [#497](https://github.com/luxingjiang1993/FreshLatch/pull/497) · pe_v2≈178→**缺额不可激活**（未改小配额）· [agent](https://cursor.com/agents/bc-a6bec02d-5347-5236-8a03-f5645a506912) |
| 4 | RESULT-Y 口径 · PE-Y-04 | **DONE** · PR [#496](https://github.com/luxingjiang1993/FreshLatch/pull/496) · [agent](https://cursor.com/agents/bc-acb51ccd-10ae-5a03-862c-c9177bfb35d4) |
| — | **缺额解锁决议** | **DONE** · ADR-0038 · 评估 `docs/research/patch_events-路线Y正式n与语料缺额设计评估.md` · 拍板 **A 扩语料 + C 停泊**；B 改 n 本窗否 |
| 5a | 扩 pe_v2 · **PE-Y-CORPUS-01** | **OPEN** · Issue [#500](https://github.com/luxingjiang1993/FreshLatch/issues/500) · `tasks/PE-Y-CORPUS-01.md` · ready-for-agent |
| 5b | 重针 route-y · **PE-Y-CORPUS-02** | **OPEN** · Issue [#501](https://github.com/luxingjiang1993/FreshLatch/issues/501) · blocked-by #500 · `tasks/PE-Y-CORPUS-02.md` |
| 6 | 激活 + 一次正式主跑 · PE-Y-05 | **不派** · 阻塞：#500+#501 绿 + 真数据过门 + 人令 |
| 7 | 消融/抽检（可选）· PE-Y-06 | 未开票 |

## Wave2 收口后监督备注

- 实现 PR 合入序建议：#494 → #495 → #496 → #497 → 父 [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493)。
- **禁止**为凑 n 静默改 `PREREG-Y` 配额。
- **ADR-0038**：解锁主路径=扩 `pe_v2`；改正式 n 须另开透明决议；此前 PE-Y-05 停泊。

## 激活 PE-Y-05 前置清单（齐了再派）

- [ ] 正式 n 可执行：#500+#501 Acceptance 绿（语料够 400 且 route-y 可加载；**或** 新决议改 n 已锁 —— 后者未批）
- [ ] #494–#497 已合入总分支
- [ ] `GATE-Y-PROBE` **真数据** `gate_passed=true`
- [ ] 人令原文：「批准激活 PREREG-Y 并正式主跑一次。」

## 人令闸

- **探针令**（示例）：「授权路线 Y 仓外探针发模型；不得激活。」→ 仅 PE-Y-02 真数据探针。  
- **正式令**（逐字）：「批准激活 PREREG-Y 并正式主跑一次。」→ 仅 PE-Y-05。  
- 同一预注册禁止第二次正式主跑。

## 基线依赖

优先叠 `origin/cursor/prereg-b-formal-main-9809`（或 B 已合入 `main` 的等价针）：R + 同 after + 软对齐。**不要**以 C 抄句分支作 Y 主 base。

## 失败止损

正式若丙或门闩长期无解：关 Y 实现票、可删 Y 功能分支；**保留** A/B/C/ALT 归档。语料长期无法扩至 400：回到地图另开「透明改 n」grill（B2），**不得**静默改表。

## CORPUS 实现序

```text
before-implement #500 → /implement PE-Y-CORPUS-01
  → before-implement #501 → /implement PE-Y-CORPUS-02
  →（仍不派 PE-Y-05）
```

基线建议叠：ADR-0038 针（本派工父）∪ PE-Y-03/#497（route-y 缺额针与 loader）。**禁止**未绿 #500 就开 #501；**禁止** #501 绿后自行激活。

## 下一窗开场白（复制 · 实现 CORPUS-01）

> 你是路线 Y 语料实现 Agent。只做 GitHub Issue [#500](https://github.com/luxingjiang1993/FreshLatch/issues/500)（PE-Y-CORPUS-01；读全文含 Agent Guards）。ADR-0038：扩 `pe_v2` 至可满 n=400+共形预留。**禁止**激活、发正式模型、开 PE-Y-05、改 `PREREG-Y` 配额表、改写 `SPLIT-pe-v2.json` 已发布成员、做第二领域。先读 ADR-0038、缺额评估、`PREREG-Y`、#371、#500。重针 route-y 留给 #501。
