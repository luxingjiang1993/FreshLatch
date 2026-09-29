# I1 Exit ACCEPTANCE

> **层身份：答辩 / 冒烟**。本页收口 Phase I1 Exit（#188）。不报方差，不作统计显著声明，不是 Hard-Gold。
> **指针**：短索引 [`INDEX.md`](./INDEX.md)；账本 [`events.jsonl`](./events.jsonl)；可复跑金样 [`i1-s005-mck-1-漏拦-没用上.md`](./i1-s005-mck-1-漏拦-没用上.md)（`runnable=true`）。
> **日期：** 2026-09-29。父规格 #183。前置 #185 / #186 / #187 已 CLOSED 且均有 `GROK-PROXY-APPROVED`。

清点是账本行数对照，不是抽样估计。本页不报方差，也不作统计显著声明。

## 1. 门槛（一眼）

| 门槛 | 要求 | 本仓清点 |
|------|------|----------|
| 漏拦/误拦（`err_kind` 与 `fail_bucket` 同时在场） | ≥3 | 5（`i1-s001`–`i1-s005`） |
| `runnable=true` | ≥1 | 1（`i1-s005`，漏拦 × 没用上） |

数字与 `docs/evidence/i1/INDEX.md` 文首「一眼」句、`events.jsonl` 行数一致。契约测 `tests/unit/test_i1_exit_contract.py` 锁这两条计数。

## 2. 短索引与金样

- 短索引：`docs/evidence/i1/INDEX.md`（每条 `sample_id`、漏拦/误拦 × 三分法桶、`runnable`）
- 金样页：`docs/evidence/i1/i1-s005-mck-1-漏拦-没用上.md`（可复跑命令；模型 / `temperature` / `seed` / 日期已入档；托管端点漂移下跨会话复现只能是近似的）
- 金样轨迹：`docs/evidence/i1/trajectories/i1-s005-mck-1-20260929.jsonl`
- 重标页：`i1-s001`–`i1-s004` 为 `replay_trace_only`。作废假绿只作 `i1-s001` 的回放锚，不当有效对照读数。

## 3. 贡献口径

`docs/contribution-boundary.md` 的 I1 行含「失败三分法 + 可复盘误判样本」，并带冒烟层口径（不报方差，不作统计显著）。

## 4. 契约测（零 LLM）

```text
python -m compileall -q src
pytest tests/unit/test_i1_events.py tests/unit/test_i1_exit_contract.py -q
```

生产枚举只读断言：`VALID_ACTIONS` 仍为 `discard|renew`；`DISPOSITIONS` 仍为可发|需补丁|勿发；规则闸 `GREEN_STATUSES` 仍为 `fresh|renew`。三分法桶名与漏拦/误拦未扩进上述集合。

## 5. 可引用句（禁升格）

> I1：短索引能指着 ≥3 条漏拦/误拦讲清闸错层级，且 ≥1 条可复跑（`i1-s005`）；档=冒烟。不是 Hard-Gold，不是统计显著，不授权改生产枚举或默认检索臂。

## 6. 非本票

- 不改生产 Gate / disposition / HumanLatch 枚举定义
- 不把三分法写成生产 status
- 不在代审 `GROK-PROXY-APPROVED #188` 之前关闭 #188
