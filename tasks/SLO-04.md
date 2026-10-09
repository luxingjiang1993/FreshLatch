# TASK / ticket — SLO-04

## Ticket
- **ID**: SLO-04
- **Title**: `feat(slo): confirm 后再验失败率周报字段（A6）`
- **Paths**: `src/freshlatch/evidence_bound.py`, `src/freshlatch/patch_events.py`, `docs/ops/生产补丁放行SLO.md`, `scripts/` 或 `reports/`（周报输出）

## What to build
从 confirm 后强制再验结果聚合「仍失败」占比，产出可写入周报的 A6 数字或「本周无 confirm」诚实句。不改再验语义，不冲乙。

## Blocked by
SLO-01

## Agent Guards
- **Blast**: api
- **Trust**: Watch
- **Acceptance**:
  - Given 至少 1 条已 confirm 且再验结果可查询的夹具/样例, When 运行 A6 聚合, Then 输出失败率或分数（失败数/分母）并标明时间窗。
  - Given 窗口内 0 条 confirm, When 运行聚合, Then 输出诚实空态（非 0% 伪装完美）。
  - Given 聚合输出, When 对照 ops 周报字段, Then 可直接填 A6。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/evidence_bound.py`（confirm→再验）· `src/freshlatch/patch_events.py` · ADR-0029
  - What changed: 只读聚合出口
  - Why not copy as-is: 需对齐 A6 周报定义
- **Tests**: added
- **Do-not-touch**: 再验判定谓词放宽；RESULT-Y

### Provenance status
- result: pass
- notes: adapt confirm/再验路径

### Evidence *(after Matt /implement)*
- typecheck: `python -m compileall -q src` exit 0
- tests: `pytest tests/unit/test_slo_a6.py -q` → 8 passed；`ruff check` A6 路径 All checks passed
- paths: `src/freshlatch/slo_a6.py` · `scripts/slo_a6_reverify_fail_rate.py` · `reports/slo/` · `tests/unit/test_slo_a6.py` · `docs/ops/生产补丁放行SLO.md`（A6 互指）

## Handoff
`2026-10-09 | SLO-04 | done | A6 只读聚合可周报；空窗诚实空态；未改再验谓词/RESULT-Y`
