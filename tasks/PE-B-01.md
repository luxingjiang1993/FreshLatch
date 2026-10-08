# TASK / ticket — PE-B-01

## Ticket
- **ID**: PE-B-01 / GitHub #437
- **Title**: `feat(#436): compare_primary 按 PREREG-B 选取 R（硬门）`
- **Paths**: `src/freshlatch/eval/patch_events_metrics.py`；`tests/unit/test_pe_*.py`

## Agent Guards
- **Blast**: eval metrics
- **Trust**: Watch
- **Acceptance**:
  1. 夹具上 T/B1/B2 自然放行集不同 → 固定 k 集合可以不同。
  2. 旧「空分+全体 claim_id 取 k」差锁 0：新主路径拒绝或不再适用。
  3. m<k → 该臂固定 k 误放率无定义。
  4. `python -m compileall -q src` 与相关 pytest 绿；不触网。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/eval/patch_events_metrics.py#compare_primary`
  - Pin: `main` `a5e424c`
  - What changed: 固定 k 选取改为自然放行集 R
  - Why not copy as-is: 旧选取使甲不可识别
- **Do-not-touch**: 旧 PREREG/RESULT 成立格；五处冻表面；未激活正式生成

### Provenance status
- result: pass
- notes: ADR-0034 / PREREG-B

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`pending | PE-B-01 | blocked-on-before-implement | next=/before-implement 437`
