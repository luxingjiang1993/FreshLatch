# TASK / ticket — DOC-01

## Ticket
- **ID**: DOC-01
- **Title**: `docs(roadmap): 过线未换臂口径自洽`
- **Paths**: `docs/roadmap.md`

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 现行路线图（文首 NOW、Phase cheat-sheet Backlog 行、文末「一句话」），When 作为现在时阅读，Then 不得出现未划线的「复跑未跑」指称 Hard-Gold 复跑状态。
  2. Given 上述同一现行段，When 读 Hard-Gold/改臂，Then 必须同时可读出：已过线、未换臂、待 Gate 人终收；不得写成已换 hybrid。
  3. Given 修订记录表，When 保留 #258/#259 历史行，Then 不得为自洽而删史。
  4. Given 本票 diff，When 检查默认检索臂叙述，Then 仍为 bm25（本票不改任何 Python）。
- **Provenance**:
  - Kind: adapt
  - Source: `docs/roadmap.md` 文首 NOW（已写 #259 过线）vs cheat-sheet/一句话（仍写复跑未跑）；证据 `docs/evidence/hard-gold-arm/`；ADR-0033
  - Pin: 仓内现行文件（无独立 SHA 要求）
  - What changed: 只改现行状态句，使与文首及 ADR-0033 一致
  - Why not copy as-is: 文首已正确，文末/表行过时
  - License note: 仓内文档
- **Tests**: waived（纯文档；不新增 pytest）
- **Rollback**: 还原 `docs/roadmap.md`
- **Do-not-touch**: `PRODUCTION_RETRIEVAL_MODE`、金标、ADR 正文、GitHub 改臂实现票、LICENSE

### Provenance status
- result: pass
- notes: 既有路线图自相矛盾，属 adapt

### Evidence *(after Matt `/implement`)*
- typecheck: n/a（无 src）
- tests: waived
- paths: `docs/roadmap.md`（现行句 = #259 已过线 · 未换臂 · 待 Gate 人终收）

## Handoff
`done | DOC-01 | 现行口径自洽 | 未提交`

## Blocked by
None (can start immediately).
