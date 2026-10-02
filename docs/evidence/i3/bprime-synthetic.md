# I3 · B′ 合成夹具说明（#250）

> **层身份：冒烟 / 面试加固（I3）。**  
> **合成夹具 · 非真事故复盘。** 不声称修过真生产事故。不做 Memory/多 Agent。不把整包再验挂回 `publish_hook`。

## 硬条

1. **超时/假绿 → 结构化错误**：`AGENT_TIMEOUT` / `SYNTHETIC_FALSE_GREEN` + 短中文；不静默绿。模块：`src/freshlatch/i3_hardening.py`（Runner 可经 `guarded_agent_call` 组合）。
2. **人审重放不双写**：discard 已幂等；renew 同 claim+evidence 重放幂等跳过，不新增 `latch_log` 坏账行。
3. **闸分布一页**：`python -m freshlatch.i3_gate_dist <trajectory.jsonl> [--out out.md]`

## 复跑

```bash
python -m compileall -q src
PYTHONPATH=src pytest tests/unit/test_i3_agent_hardening.py -q
```
