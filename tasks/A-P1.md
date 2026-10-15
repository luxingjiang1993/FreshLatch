# TASK · A-P1 Canary 真跑闭环 + 停发剧本

## Ticket
- **ID**: A-P1
- **Title**: `feat(ops): canary mode off|shadow|active + halt-on-breach`
- **Paths**: `src/freshlatch/canary.py`, `tests/unit/test_canary_halt.py`, `docs/ops/生产路径canary停发.md`, `tasks/A-P1.md`
- **Trust**: Watch
- **Blast**: api | none

## Agent Guards
- **Acceptance**:
  1. Given env/config `CANARY_MODE` in `{off,shadow,active}` (default `off`), When mode is off, Then production path never promotes a canary arm.
  2. Given shadow or active, When a breach is injected in automated test, Then `canary_halted=true` and main path refuses promotion / falls back (executable pytest).
  3. Runbook exists under `docs/ops/` covering: who watches (owner), when to halt, how to roll back to off; notes P3 will consume canary events for paging.
  4. Docs scope sentence: 单机 canary ≠ 多区渐进发布; ≠ 注册分; ≠ L5.
- **Provenance**: Kind=new. Do not confuse with `docs/ops/冻结金标canary跑法.md` (that is frozen-gold eval SLI 6, not release canary).
- **Do-not-touch**: floors / gold / x1 / `PRODUCTION_RETRIEVAL_MODE` default arm / SESOI / C-04 re-run / RESULT-Y
- **Tests**: `tests/unit/test_canary_halt.py`（破线 → `canary_halted`，主路径拒绝晋升）
- **Rollback**: set `CANARY_MODE=off`

### Provenance status
- result: pass
- notes: 新模块。未改发前钩子闸，未改检索默认臂。

## Handoff
Open draft PR titled with A-P1. Trust Watch. pytest green. No paid API「跑」.
