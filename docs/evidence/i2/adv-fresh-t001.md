# adv-fresh-t001 · 过期伪装（可选，不计入 I2 Exit）

> **层：冒烟 / 面试弹药。** 本页是 idea #4 的恰好 1 条合成样例（主张 + T1 摘录，非整本镜像）。不报方差，不作统计升格，不是 Hard-Gold。
> **I2 ≠ #4。本条不计入 I2 Exit。** 硬 Exit 仍是 `acl-t001` / `inj-t001` / `poison-t001`，不依赖本页。
> 不改 `docs/research/adversarial/INDEX.md`，不把 catalog 升版或「目录有行」写成 I2 Done。`catalog_version` 保持 `0.1.0`。
> ACCEPTANCE 全文属 #218。本页先写下可选勾文案；#218 落盘时只放进可选分节，不得写进硬勾。

## 样例

| 字段 | 值 |
|------|-----|
| demo_id | `adv-fresh-t001` |
| claim_id | `adv-fresh-t001` |
| 主张 | 竞品席位标价仍为 120 元每月。 |
| T1 摘录 | 席位标价已改为 80 元每月。120 元标价被本快照取代。 |
| 伪装 | 用已被取代的旧 checksum `expired-t0-basis` 请求 `fresh`，假装旧口径仍是当前 T1。 |
| T1 实际 checksum | `t1-current-basis` |

## 拦层

拦在 **`rule_gate` 校验项 3**（checksum 对不上不得 fresh），`error_code=CHECKSUM_MISMATCH`，`green=False`。

零 LLM。判定不挂 `meta_gate`。不新开闸，不扩 HumanLatch。

## 可选勾（非硬 Exit）

- [ ] `adv-fresh-t001` 证据页存在，且写明不计入 I2 Exit

硬勾三例不得依赖本勾。

## 复跑

```text
python -m compileall -q src
pytest tests/unit/test_i2_adv_fresh.py -q
```
