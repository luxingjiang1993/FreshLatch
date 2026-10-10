# GATE-Y-SENSITIVITY（可扔 · 敏感性闸）

**层身份**：夹具/stub 层 · 非真模型过线

> 本报告不进 `RESULT-Y` 成立格；不构成 `gate_passed`；不单独过门；
> 不保证乙；不激活 `PREREG-Y`。夹具/stub 绿 ≠ 可激活前置已满足。

## Pin

- 型号：`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`（须 = ADR-0040 / #527 `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`）
- τ：`0.5`（须 = `ENTAILMENT_TAU`；失败仅允许未激活收紧一次并整闸重测；**禁止放宽**凑绿）
- 坏→`ok=False` 下限：`0.9`
- 正确→`ok=True` 下限：`0.7`
- 集合 S 条数：24（坏 20 · 正确 4）

## S1–S4

| # | 条件 | 结果 |
|---|---|---|
| S1 | 无 `score=None`；reject/`ok=False` → `score=−∞` （none=0；reject=20；−∞=20） | 通过 |
| S2 | 坏→`ok=False` ≥ 0.9 （实测 1.0000） | 通过 |
| S3 | 正确→`ok=True` ≥ 0.7 （实测 1.0000） | 通过 |
| S4 | 型号/τ = ADR-0040（`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` · `0.5`） | 通过 |

**sensitivity_passed（S1∧S2∧S3∧S4）**：是

**gate_passed**：否（敏感性报告永不单独过门）

**activation_prerequisite_met**：否

## τ 收紧纪律（未激活）

- 失败时仅允许未激活收紧 τ **一次**并整闸重测。
- 禁止放宽 τ / ρ 凑绿。
- 本票未改 `ENTAILMENT_TAU`；未激活 `PREREG-Y`。

## 逐条结果

| sample_id | stratum | op | gold | kind | ok | score | reason |
|---|---|---:|---|---|---|---|---|
| S-数值-op0 | 数值 | 0 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-数值-op1 | 数值 | 1 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-数值-op2 | 数值 | 2 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-数值-op3 | 数值 | 3 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-日期-op0 | 日期 | 0 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-日期-op1 | 日期 | 1 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-日期-op2 | 日期 | 2 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-日期-op3 | 日期 | 3 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-条款-op0 | 条款替换 | 0 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-条款-op1 | 条款替换 | 1 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-条款-op2 | 条款替换 | 2 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-条款-op3 | 条款替换 | 3 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-删除-op0 | 删除 | 0 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-删除-op1 | 删除 | 1 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-删除-op2 | 删除 | 2 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-删除-op3 | 删除 | 3 | 坏 | construct_bad | False | −∞ | 核验不过 |
| S-废止-trap01 | 条款替换 |  | 坏 | abolish_trap | False | −∞ | 核验不过 |
| S-废止-trap02 | 条款替换 |  | 坏 | abolish_trap | False | −∞ | 核验不过 |
| S-版本-trap01 | 条款替换 |  | 坏 | version_trap | False | −∞ | 核验不过 |
| S-版本-trap02 | 条款替换 |  | 坏 | version_trap | False | −∞ | 核验不过 |
| S-正确-数值01 | 数值 |  | 正确 | correct | True | 0.910000 | 支撑成立 |
| S-正确-日期01 | 日期 |  | 正确 | correct | True | 0.910000 | 支撑成立 |
| S-正确-条款01 | 条款替换 |  | 正确 | correct | True | 0.910000 | 支撑成立 |
| S-正确-删除01 | 删除 |  | 正确 | correct | True | 0.910000 | 支撑成立 |

## 防火墙复述

- 不进 RESULT-Y；≠ 乙；≠ `gate_passed`。
- 未通过 → 不得真数据探针、不得激活、不得正式跑。
- 禁止：金标进 score；夹具升格过门；放宽凑绿。
