# I1 失败复盘短索引（#185 + #187 · #188 Exit）

> **层身份：答辩 / 冒烟**。一眼列出已重标漏拦/误拦样本；不报方差，不作统计升格。
> **一眼（#188 Exit）**：漏拦/误拦 **5** 条（门槛 ≥3）；`runnable=true` **1** 条（`i1-s005`，门槛 ≥1）。
> **#239 post-fix**：`i1-s005` 历史漏拦叙事保留；修复后重跑见金样页 post-fix 段（`machine_status=stale` · `gold_hit=true` · 2026-09-30；不改账本行、不声称 Hard-Gold）。
> 账本：`docs/evidence/i1/events.jsonl` · API：`src/freshlatch/i1_events.py`
> 作废假绿（`docs/evidence/w4/false-green-control.md` 2026-09-21 格子）**不得**当有效对照读数；`i1-s001` 仅借该页作 `replay_trace_only` 挂标锚。

| sample_id | claim_id | err_kind × fail_bucket | runnable | evidence 页 | trajectory_ptr / 对照锚 |
|-----------|----------|------------------------|----------|-------------|-------------------------|
| `i1-s001` | c2 | 漏拦 × 找错 | replay_trace_only | [i1-s001-c2-漏拦-找错.md](./i1-s001-c2-漏拦-找错.md) | `docs/evidence/w4/false-green-control.md`（作废印仍有效；只作回放锚） |
| `i1-s002` | c6 | 误拦 × 找错 | replay_trace_only | [i1-s002-c6-误拦-找错.md](./i1-s002-c6-误拦-找错.md) | `reports/w5w8_acceptance/k6_4/trajectories/run-20260922-033855.jsonl` |
| `i1-s003` | c3 | 漏拦 × 找不到 | replay_trace_only | [i1-s003-c3-漏拦-找不到.md](./i1-s003-c3-漏拦-找不到.md) | `reports/w5w8_acceptance/k3/seed_11/trajectories/run-20260922-034310.jsonl` |
| `i1-s004` | c8 | 误拦 × 没用上 | replay_trace_only | [i1-s004-c8-误拦-没用上.md](./i1-s004-c8-误拦-没用上.md) | `reports/w5w8_acceptance/gold_n1/trajectories/run-20260922-033202.jsonl` |
| `i1-s005` | mck-1 | 漏拦 × 没用上 | true | [i1-s005-mck-1-漏拦-没用上.md](./i1-s005-mck-1-漏拦-没用上.md) | `docs/evidence/i1/trajectories/i1-s005-mck-1-20260929.jsonl` |

**计数（机读）**：漏/误（同时含 `err_kind` 与 `fail_bucket`）≥3；`runnable=true` ≥1（`i1-s005`）。
