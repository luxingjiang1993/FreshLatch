# I2 安全三例短索引

> **层身份：冒烟。** 一眼列出硬 Exit 三例。不报方差，不作渗透认证，不是 Hard-Gold。
> **一眼**：硬行 3 条 —— `acl-t001` · `inj-t001` · `poison-t001`。#4 不在硬行。
> 薄表：`docs/security.md`。验收：[`ACCEPTANCE.md`](./ACCEPTANCE.md)。父规格 #213 · ADR-0030。

| demo_id | threat | 夹具 | 复跑 |
|---------|--------|------|------|
| `acl-t001` | 越权召回 | [acl-t001.json](./acl-t001.json) | `pytest tests/unit/test_i2_retrieve_trust.py -q -k acl_t001` |
| `inj-t001` | 间接注入 | [inj-t001.md](./inj-t001.md) | `pytest tests/unit/test_rule_gate.py tests/unit/test_i2_injection_gate.py -q` |
| `poison-t001` | 检索投毒 | [poison-t001.json](./poison-t001.json) | `pytest tests/unit/test_i2_retrieve_trust.py -q -k poison_t001` |

夹具正文分别随 #214、#215 落地。本索引不复制夹具全文，也不新写过滤逻辑。

## 可选（不计入 I2 Exit）

| demo_id | 说明 | 证据页 |
|---------|------|--------|
| `adv-fresh-t001` | idea #4 过期伪装。**不计入 I2 Exit。** | [adv-fresh-t001.md](./adv-fresh-t001.md) |
