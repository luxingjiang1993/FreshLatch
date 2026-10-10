# TASK / ticket — SLO-01

## Ticket
- **ID**: SLO-01
- **Title**: `docs(slo): 生产补丁/放行 SLO 文档闭环与禁词扫描`
- **Paths**: `docs/ops/生产补丁放行SLO.md`, `docs/ops/生产补丁放行SLO-地图.md`, `docs/research/生产补丁放行SLO设计评估.md`, `docs/adr/0034-生产补丁放行SLO与实验防火墙.md`, `docs/spec/24-生产补丁放行SLO.md`, `CONTEXT.md`, `docs/grill-prep.md`, `docs/spec/README.md`

## What to build
核对运营真源、评估、ADR、规格、CONTEXT、地图互指完整；文面零「接近乙/软甲/主实验成功」；零编辑 PREREG-Y/RESULT-Y/formal-generations-y。可机检链接存在与禁词。

## Blocked by
None（can start immediately）

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  - Given 仓库文档, When 检查 ops↔ADR-0034↔评估↔spec/24↔CONTEXT 词条互指, Then 全部路径存在且互相链接。
  - Given `rg -n '软甲|接近乙|主实验成功' docs/ops/生产补丁放行SLO.md docs/spec/24-生产补丁放行SLO.md docs/adr/0034-生产补丁放行SLO与实验防火墙.md`, When 扫描, Then 无匹配（或仅出现在「禁止」语境且带否定）。
  - Given `git diff --name-only` 相对本票, When 列出变更, Then 不含 `PREREG-Y`/`RESULT-Y`/`formal-generations-y`。
- **Provenance**:
  - Kind: new
  - Source: （新文档链为主；纪律引用 ADR-0029/0031/DECISION-LOG）
  - What changed: 新建运营 SLO 文档链；并对 `CONTEXT.md` / `docs/grill-prep.md` / `docs/spec/README.md` 做词表与索引附属增量（非业务码 adapt）
  - Why not copy as-is: n/a（Kind=new；旧文件仅为决议挂钩增量，不改业务语义）
- **Tests**: waived（documentation-only；Acceptance 为路径/禁词机检）
- **Do-not-touch**: `docs/evidence/patch-events/PREREG-Y.md`, `RESULT-Y.md`, `formal-generations-y*`, 业务 `src/`

### Provenance status
- result: pass（人批 yes · 2026-10-09）
- notes: Kind=new；CONTEXT/grill-prep/spec README 为词表/索引附属增量，非 adapt/port。

### Evidence *(after Matt /implement)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-09 | SLO-01 | gates-pass | Trust=Watch Blast=none Prov=pass → fresh session /implement SLO-01`
