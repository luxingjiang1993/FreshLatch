# TASK / ticket — SLO-06

## Ticket
- **ID**: SLO-06
- **Title**: `feat(slo): 人审作废率与 override rate 周报（C1/C2）`
- **Paths**: `src/freshlatch/store/sqlite_store.py`, `src/freshlatch/gates/human_latch.py`, `src/freshlatch/claim_ledger.py`, `docs/ops/生产补丁放行SLO.md`, `scripts/` 或 `reports/`

## What to build
从 latch_log / 作废名单只读聚合用户作废率与 override rate，输出周报字段。override ≠ 模型变好（ADR-0023）。不新增 HumanLatch 动词。

## Blocked by
SLO-01

## Agent Guards
- **Blast**: api
- **Trust**: Watch
- **Acceptance**:
  - Given 含 discard/renew 与 override 0/1 的 latch_log 夹具, When 运行 C1/C2 聚合, Then 输出作废率与 override rate（含分母）。
  - Given 聚合文档/输出头, When 阅读, Then 含「override 不作模型变好 / 不作验收绿灯」声明。
  - Given 输出, When 对照 ops 周报, Then C1/C2 可填。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/store/sqlite_store.py`（latch_log override）· ADR-0023 · `docs/research/ε-override与void事件管道字段设计评估.md`
  - What changed: 只读周报聚合
  - Why not copy as-is: 需对齐 C1/C2 运营定义
- **Tests**: added
- **Do-not-touch**: 新增 override action；Client Memo 塞入 override；RESULT-Y

### Provenance status
- result: pass
- notes: adapt latch_log；遵守 ADR-0023

### Evidence *(after Matt /implement)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-09 | SLO-06 | ready | blocked by SLO-01`
