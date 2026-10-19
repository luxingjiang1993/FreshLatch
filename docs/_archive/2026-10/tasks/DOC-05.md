# TASK / ticket — DOC-05

## Ticket
- **ID**: DOC-05
- **Title**: `docs(satellite): 立项切片与 grill-prep 指针`
- **Paths**: `docs/product/FreshLatch.md` · `docs/grill-prep.md`

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 立项切片现行「产品怎么跑」，When 读 Lead，Then 不得把自由改写查询、`spawn_auditor` 写成现行工具；须与主张查询变换、ADR-0009 一致。
  2. Given 同一切片，When 读定价/日活，Then 不新增「已在售 SaaS」含义；保持合成/切片语境。
  3. Given grill-prep 文首原则，When 代理开 grill，Then 不再把「未钉死前不要 implement V1」当作现行禁令；须标明本页为历史阅读包，现行 frontier 指向路线图 NOW（改臂 Gate 人终收 / C′）。
- **Provenance**:
  - Kind: adapt
  - Source: `docs/product/FreshLatch.md` §4；`docs/grill-prep.md` 文首；权威 CONTEXT、ADR-0009、DOC-01 后的路线图 NOW
  - Pin: 仓内现行文件
  - What changed: 关键句与指针，不重写切片全篇
  - Why not copy as-is: V1 已实现后指针未改
  - License note: 仓内文档
- **Tests**: waived（纯文档）
- **Rollback**: 还原上述两文件
- **Do-not-touch**: `CONTEXT.md` 新增卫生词；LICENSE；实现 V1 功能；代关 GitHub 票

### Provenance status
- result: pass
- notes: 卫星页相对词表/阶段过时

### Evidence *(after Matt `/implement`)*
- typecheck: n/a
- tests: waived
- paths: `docs/product/FreshLatch.md` · `docs/grill-prep.md`（切片角色表已合 Cloud 禁 spawn_auditor；grill-prep 仍用本机 #259 已过线，未合 Cloud #258 未过线）

## Handoff
`done | DOC-05 | 切片+grill-prep 指针 | 未提交`

## Blocked by
- DOC-01
