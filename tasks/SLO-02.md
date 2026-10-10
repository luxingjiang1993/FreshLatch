# TASK / ticket — SLO-02

## Ticket
- **ID**: SLO-02
- **Title**: `chore(slo): 硬闸不变量违例计数清单（B6/B7/C5/D3/C3）`
- **Paths**: `docs/ops/生产补丁放行SLO.md`, `scripts/`（若新增计数入口）, `src/freshlatch/evidence_bound.py`, `src/freshlatch/gates/human_latch.py`, `src/freshlatch/gates/rule_gate.py`, `src/freshlatch/publish_hook.py`, `tests/`（硬闸回归挂接）

## What to build
为无证拒拦、未确认不出门、Agent 自红转绿=0、无 T1 绿灯=0、续命带证=100% 提供可执行的违例计数或清单出口（文档字段可填），复用既有闸语义，不放宽 fail-closed。

## Blocked by
SLO-01

## Agent Guards
- **Blast**: api
- **Trust**: Watch
- **Acceptance**:
  - Given 无合法 t1_ids 的 confirm 尝试, When 走既有 confirm 路径, Then 拒绝且计数/清单可观察到 ≥1 次拒拦（B6）。
  - Given 未 confirm 草案, When 检查正式正文/正式 patch_events, Then 未写入（B7）；清单可报告 0 违例或显式扫描通过。
  - Given 试图无 T1 置 fresh 或 Agent 自红转绿, When 走闸, Then 失败且 D3/C5 违例计数目标语义为 0（回归断言保持红灯不得私转绿）。
  - Given renew 无新 T1, When 受理, Then 拒绝（C3）；不得写 validity_basis。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/evidence_bound.py` · `src/freshlatch/gates/human_latch.py` · `src/freshlatch/gates/rule_gate.py` · ADR-0029/0006
  - What changed: 只读聚合/清单挂接；不改闸谓词
  - Why not copy as-is: 需对齐 ops 页 ID（B6/B7/C5/D3/C3）
- **Tests**: added
- **Do-not-touch**: PREREG-Y / RESULT-Y；放宽 fail-closed；金标进生产 score

### Provenance status
- result: pass
- notes: adapt 既有闸；Source 已钉

### Evidence *(after Matt /implement)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-09 | SLO-02 | ready | blocked by SLO-01`
