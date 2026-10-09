# patch_events 路线 Y · 云端派工说明

> 四件套 PR [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493) · 规格卷 27 · ADR-0037  
> **硬前置**：`PREREG-Y` **未激活**；不得发模型除非人授探针票；不得改 B/C 冻结归档。

## 链

```text
grill-with-docs → 四件套(#493) → to-spec(卷27) → to-tickets → enrich-tickets → before-implement → /implement
```

## 边界

| 允许 | 禁止 |
|---|---|
| formal-y 旁路、GATE-Y 可扔报告、n=400 名单 | 激活 PREREG-Y；正式 n=400 进主表（未过门） |
| RESULT-Y 壳 + Y 成立口径单测 | 改 PREREG-B/C / RESULT-B/C / formal-generations-b/c |
| 继承 R / 同 after / 软对齐 | C 强制抄句当 Y 主路径；放松 hard reject；金标进 score；复活 A |
| B1/B2 报告-only | 称甲 / soft-甲；新造 compare_*；ALT/夹具进主表 |

## 票序进度（Cloud）

| 序 | 票 | 状态 |
|---|---|---|
| 1 | formal-y 旁路 · PE-Y-01 | **DONE** · PR [#494](https://github.com/luxingjiang1993/FreshLatch/pull/494) · [agent](https://cursor.com/agents/bc-5a2978df-d5a8-5696-88cc-5a2d80343cf0) |
| 2 | GATE-Y-PROBE · PE-Y-02 | **DONE** · PR [#495](https://github.com/luxingjiang1993/FreshLatch/pull/495) · [agent](https://cursor.com/agents/bc-e1bba9e6-7fa1-5f6f-ab30-1cf841c76882) |
| 3 | n=400 名单 · PE-Y-03 | **云端派工中** · [agent](https://cursor.com/agents/bc-a6bec02d-5347-5236-8a03-f5645a506912) |
| 4 | RESULT-Y 口径 · PE-Y-04 | **云端派工中** · [agent](https://cursor.com/agents/bc-acb51ccd-10ae-5a03-862c-c9177bfb35d4) |
| 5 | 激活 + 一次正式主跑 · PE-Y-05 | **Gate · 不派**（过门+人令） |
| 6 | 消融/抽检（可选）· PE-Y-06 | 未开票 |

## 人令闸

- **探针令**（示例）：「授权路线 Y 仓外探针发模型；不得激活。」→ 仅 PE-Y-02 真数据探针。  
- **正式令**（逐字）：「批准激活 PREREG-Y 并正式主跑一次。」→ 仅 PE-Y-05。  
- 同一预注册禁止第二次正式主跑。

## 基线依赖

优先叠 `origin/cursor/prereg-b-formal-main-9809`（或 B 已合入 `main` 的等价针）：R + 同 after + 软对齐。**不要**以 C 抄句分支作 Y 主 base。

## 失败止损

正式若丙或门闩长期无解：关 Y 实现票、可删 Y 功能分支；**保留** A/B/C/ALT 归档。
