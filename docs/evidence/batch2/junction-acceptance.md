# Batch 2 交界与边界验收注记（#117）

> 层：invariant。单次确定性可复现。不是统计证明，不是产品已验证。
> 预锁句来源：`docs/research/β-checksum与HumanLatch-renew交界设计评估.md` §4；ADR-0017。事后改句 = 本批交界验收作废。

## 预锁可引用句

Batch 2 renew 交界：格式→点回→闸（含 checksum）→仅绿后写 `validity_basis`/转绿；失败零写且 `error_code`+短中文透传；不启用跨轮重检；不得升格为 checksum 证明 latch / 商业裁决。

## 可观察回归

主缝：HumanLatch renew 写路径（`tests/unit/test_renew.py`）。不新开 UI 缝，不新开 runner 行为缝。零 LLM。

- 次序：格式失败（`RENEW_EVIDENCE_MALFORMED`）与点回失败（`RENEW_EVIDENCE_UNRESOLVED`）时 `checksum_fn` 零调用；闸失败（`CHECKSUM_MISMATCH`）才调用；仅闸绿后写 `validity_basis` / `last_confirmed_at` / `status=fresh` / `latch_log`。
- 失败：续命字段零写；返回 `error_code` + 短中文 `detail`。detail 不写成商业裁决，也不写成 Agent 自绿或机器改判。
- fresh 半边仍不构造 `validity_basis`（结构性空转）：`runner.py`、角色、工具、UI 源码不出现 `validity_basis`；`Runner._checksum_fn` 恒返回 `None`。`sheet.py` 只投影续命已写入的字段，不是 fresh 构造。
- 不启用跨轮重检：续命转绿后篡改语料再 `enter_round`，主张保持 fresh，basis 与审计迹不变。档 3b 未实现（留 #111）。
- 档 3a 未实现（留 #110）：fresh 不补 `validity_basis`，无多证据主文档选取。

## ATK-CS 主缝引用

| ID | 测试 |
|---|---|
| ATK-CS-01 | `test_atk_cs_01_tamper_corpus_renew_checksum_mismatch_zero_write` |
| ATK-CS-02 | `test_atk_cs_02_store_column_fn_not_activation_success` |
| ATK-CS-03 | `test_atk_cs_03_empty_claimed_nonzero_actual_blocks_write` |
| ATK-CS-04 | `test_atk_cs_04_renew_with_corpus_sha256_writes_basis` |

四条都在 `tests/unit/test_renew.py`。本批不增删 ATK-CS 期望。

## 禁升格与 gold

- 不得把本注记或 ATK 绿写成 latch 证明，或写成商业裁决。
- 本验收相关改动不修改 `data/eval/gold.json`。
