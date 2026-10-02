# I3 · 政策拒夹具说明（#249）

> **层身份：冒烟 / 面试加固（I3）。**  
> **语义：政策拒 ≠ 新鲜度拒。** 本夹具演示声明式出处禁区旁路，不是 `stale`/`must_stale`，不是元陈述拒，不是 ACL/poison。

## 预锁规则

- 规则文件：`data/policy/source_ban.json`
- 规则 id：`source-ban-demo-001`
- 模式：`banned.example` · `*/leaked-internal/*`
- 命中码：`POLICY_SOURCE_BAN`

## 合成夹具（非真事故）

当 T1 出处命中禁区域名/路径，即使证据「新」、Auditor 判 fresh、已入库，绿灯出口旁路仍不得装可发。

复跑：

```bash
python -m compileall -q src
PYTHONPATH=src pytest tests/unit/test_i3_policy_gate.py -q
```
