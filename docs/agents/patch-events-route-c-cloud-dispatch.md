# patch_events 路线 C · 云端派工说明

> 父图 [#482](https://github.com/luxingjiang1993/FreshLatch/issues/482) · 决议 [#483](https://github.com/luxingjiang1993/FreshLatch/issues/483) · 规格卷 26  
> **硬前置**：四件套已落；`PREREG-C` **未激活**；不得发模型除非人授探针票。

## 链

```text
grill-with-docs(#483) → to-spec(卷26) → to-tickets → enrich-tickets → before-implement → /implement
```

## 边界

| 允许 | 禁止 |
|---|---|
| 强制抄句缝、夹具、GATE-C 可扔报告 | 激活 PREREG-C；正式 n=100 进主表（未过门） |
| RESULT-C 壳 + B 附录句 | 改 PREREG-B / RESULT-B / formal-generations-b |
| 继承 R / 同 after 行为 | 放松 hard reject；金标进 score；复活 A |
| ALT 附录指针 | ALT 并主表；改主 compare_primary 追甲 |

## 失败止损

C 正式主跑若丙或未过门长期无解：关 C 相关票、删 C 功能分支；**保留** A/B/ALT 归档。

## 基线依赖

工程实现宜叠在 B 机制已合入的针上（选取 R · 同 after · 核验硬门）。若 B PR 尚未合 main，feat 票须写明 base 分支 / 依赖 PR，禁止假装从空分 top-k 重开。
