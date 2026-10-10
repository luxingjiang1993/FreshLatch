# patch_events 冲乙整合升格 · 云端派工说明

> 地图 [#517](https://github.com/luxingjiang1993/FreshLatch/issues/517) · 规格卷 28 · ADR-0039/0040/0041  
> **硬前置**：`PREREG-Y` **未激活**；敏感性未过不得真数据探针；不得发模型除非人授；不得改 B/C 冻结归档。

## 链

```text
grill #518/#519/#520 → 四件套 PR → /to-spec(卷28) → /to-tickets → enrich-tickets → before-implement → /implement
```

## PE-Y 继承切分（派工真相源）

| 资产 | 处置 | 动作 |
|---|---|---|
| PE-Y-01 formal-y | **原样继承** | 合入既有 PR；本波不重写旁路骨架 |
| PE-Y-02 GATE-Y Cond | **继承 Cond · 修订前置** | 新票 PE-Y-GATE-REV：敏感性硬前置 + 仪器机制针 |
| PE-Y-03 n=400 / CORPUS | **原样继承** | 合入扩容/重针 PR；可加载≠激活 |
| PE-Y-04 RESULT-Y | **原样继承** | 成立尺不改 |
| verify / score | **作废重开** | PE-Y-INST-01 |
| 敏感性闸 | **新开** | PE-Y-SENS-01 |
| n30 冒烟 | **新开** | PE-Y-SMOKE-01 |
| PE-Y-05 正式主跑 | **Gate · 不派直至前置齐** | 敏感性∧冒烟∧gate_passed∧正式人令 |
| PREREG-Z | **弃** | — |

## 边界

| 允许 | 禁止 |
|---|---|
| 升格 `PREREG-Y` Amendment；NLI verify；敏感性/冒烟可扔报告 | 激活；正式主跑；保证乙；另开 Z |
| 修订 GATE-Y 前置守卫 | 改过门 Cond 为点>0.05；夹具/冒烟升格过门 |
| 继承 formal-y / n400 / RESULT-Y | 回写 B/C；金标进 score；放松 hard reject 凑 k |
| 合入 CORPUS 解锁针 | 静默改小正式 n |

## 建议票序

| 序 | 票 | Trust | 依赖 |
|---|---|---|---|
| 1 | PE-Y-INST-01（NLI+score） | Watch | ADR-0040；协议仪器节 |
| 2 | PE-Y-SENS-01 | Watch | INST-01 |
| 3 | PE-Y-SMOKE-01 | Watch | INST-01 |
| 4 | PE-Y-GATE-REV | Watch | SENS-01；既有 PE-Y-02 |
| 5 | 合入 PE-Y-01…04 / CORPUS（若未进 main） | Watch | 既有开 PR |
| 6 | PE-Y-05 | **Gate** | 以上全绿 + 人令 |

## 人令闸

- **探针令**（逐字）：`授权路线 Y 仓外探针发模型；不得激活。`  
- **正式令**（逐字）：`批准激活 PREREG-Y 并正式主跑一次。`  
- 同一预注册禁止第二次正式主跑。

## 合入提示

- 文档依赖：#523（ADR-0039）· #524（ADR-0040）· #525（ADR-0041）· 本 to-spec PR。  
- 代码基线：优先 R+同 after+软对齐；**不要**以 C 抄句分支作 Y 主 base。  

## 失败止损

仪器/敏感性长期无解：停 PE-Y-05；可关冲乙实现票；**保留** A/B/C/ALT 与未激活 `PREREG-Y` 文档针。
