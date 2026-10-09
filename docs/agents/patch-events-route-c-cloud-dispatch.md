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

## 票序进度（Cloud）

| 序 | 票 | 状态 |
|---|---|---|
| 1 | 强制抄句 · #485 / PE-C-01 | DONE |
| 2 | formal-c 默认不发 · #487 | DONE |
| 3 | GATE-C 夹具 · #486 / PE-C-02 | DONE |
| 4 | RESULT-C 壳 · #488 / PE-C-03 | DONE（未激活·成立格未跑） |
| 5 | **激活 + 一次正式主跑 + RESULT-C 抄表** · #490 / PE-C-04 | **DONE · 结果丙**（k=93；不得称甲） |
| 6 | 消融/抽检 | Watch · 后置 · 未开 |
| 7 | ALT 附录测量（不进主成立） | Watch · 可选 · 未开 |

**人令闸**

- 正式人令已执行（2026-10-09）：激活 + 一次主跑完成；同一预注册禁止第二次正式主跑。
- 探针令仍仅用于可扔探针，不得再激活/二跑。

## 基线依赖

工程实现宜叠在 B 机制已合入的针上（选取 R · 同 after · 核验硬门）。若 B PR 尚未合 main，feat 票须写明 base 分支 / 依赖 PR，禁止假装从空分 top-k 重开。
