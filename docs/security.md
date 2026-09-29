# FreshLatch 安全演示（I2）

> **层：冒烟。** 本页不是渗透认证，不报安全通过率，不报方差。硬 Exit 只有下面硬表三行。
> 权威：ADR-0030 · 父规格 #213。夹具正文由 #214 / #215 落地，本页只做薄表互链。不改 `docs/research/adversarial/INDEX.md`，不把目录升版写成 I2 Done。

## 硬表

| threat | demo_id | layer | repro_cmd | expected | smoke_note |
|--------|---------|-------|-----------|----------|------------|
| 越权召回 | `acl-t001` | `RetrievalStore.retrieve` 显式 `tenant_id` | `pytest tests/unit/test_i2_retrieve_trust.py -q -k acl_t001` | `tenant_id=B` 的结果不含租户 A | 冒烟 · 确定性 · 不绑 LLM |
| 间接注入 | `inj-t001` | `rule_gate` + `Runner._finalize` | `pytest tests/unit/test_rule_gate.py tests/unit/test_i2_injection_gate.py -q` | 污染 T1 不得给出 `fresh` 绿灯 | 冒烟 · 零 LLM · 不挂 `meta_gate` |
| 检索投毒 | `poison-t001` | `retrieve` 按 `poison`/`untrusted` 元数据剔除 | `pytest tests/unit/test_i2_retrieve_trust.py -q -k poison_t001` | 高分毒块不进入结果集 | 冒烟 · 确定性 · 不靠无标签启发式 |

短索引：`docs/evidence/i2/INDEX.md`。验收硬勾：`docs/evidence/i2/ACCEPTANCE.md`。

## 可选（不计入 I2 Exit）

idea #4 过期伪装 `adv-fresh-t001` 可同波作面试弹药，证据页 `docs/evidence/i2/adv-fresh-t001.md`。**不计入 I2 Exit，不是硬表第四行。** I2 ≠ #4。
