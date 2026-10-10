# TASK / ticket — SLO-03

## Ticket
- **ID**: SLO-03
- **Title**: `docs(slo): 改侧抽检协议（A2 证据覆盖 · A3 改对率 · A4 错改率）`
- **Paths**: `docs/ops/生产补丁放行SLO.md`, `docs/ops/抽检-补丁改对率.md`（新建）, `data/patch_events/`（只读样例指针，若需）

## What to build
落地人标抽检表与协议：证据覆盖、确认后改对、严重错改（会害客户）定义；样本不足诚实句；Watch 讨论线 &lt;5% 写明观测-only。不把抽检金标化进生产 score。

## Blocked by
SLO-01

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  - Given 抽检协议文档, When 打开, Then 含 A2/A3/A4 字段定义、抽样规则、严重错改操作定义、与 ops 页互指。
  - Given 协议文首, When 阅读层身份, Then 写明观测/Watch 且 &lt;5% 不作本波 Gate 生死。
  - Given 协议, When 搜索「生产 score」「在线放行」, Then 明确禁止金标/抽检标签进生产 score。
- **Provenance**:
  - Kind: new
  - Source: `docs/ops/生产补丁放行SLO.md` §3.1；评估 §4
  - What changed: 新建抽检协议页
  - Why not copy as-is: n/a
- **Tests**: waived（documentation）
- **Do-not-touch**: RESULT-Y；把抽检当 Gate 生死

### Provenance status
- result: pass
- notes: 新文档

### Evidence *(after Matt /implement)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-09 | SLO-03 | ready | blocked by SLO-01`
