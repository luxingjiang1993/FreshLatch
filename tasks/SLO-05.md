# TASK / ticket — SLO-05

## Ticket
- **ID**: SLO-05
- **Title**: `docs(slo): 放行误放/误拒成对观测协议（B2/B3）`
- **Paths**: `docs/ops/生产补丁放行SLO.md`, `docs/ops/抽检-放行误放误拒.md`（新建）

## What to build
生产侧误放/误拒成对观测（或抽检折算）协议：分母定义、与实验固定 k 尺分轨声明、禁止单独放行率当成功。不实现实验 compare_primary，不回写 Y。

## Blocked by
SLO-01, SLO-03

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  - Given 协议文档, When 打开, Then 同时定义 B2 与 B3，并要求成对周报。
  - Given 协议, When 搜索「固定 k」「T−C」「RESULT-Y」, Then 标明实验-only / 只读 / 不进生产 KPI。
  - Given 协议成功标准节, When 阅读, Then 明确禁止「仅放行率升高」算成功。
- **Provenance**:
  - Kind: new
  - Source: `docs/ops/生产补丁放行SLO.md` §3.2；DECISION-LOG 投稿映射（只读）
  - What changed: 新建放行观测协议
  - Why not copy as-is: n/a
- **Tests**: waived（documentation）
- **Do-not-touch**: PREREG-Y / RESULT-Y / compare_primary 语义

### Provenance status
- result: pass
- notes: 新文档；实验尺只读引用

### Evidence *(after Matt /implement)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-09 | SLO-05 | ready | blocked by SLO-01, SLO-03`
