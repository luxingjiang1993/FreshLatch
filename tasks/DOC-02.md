# TASK / ticket — DOC-02

## Ticket
- **ID**: DOC-02
- **Title**: `docs(readme): 现状表对齐 I3 与 Hard-Gold 过线未换臂`
- **Paths**: `README.md`

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given README Current status，When 新读者扫表现状，Then 能读到 I3 为冒烟/面试加固 DONE，以及 Hard-Gold 过线未换臂（不得写成已换 hybrid）。
  2. Given 同一表，When 看下一跳/缺口，Then 仍写生产默认 BM25、薄对话 Out、curl≠平台、C′ 为 backlog 或等价；并指向改臂 Gate 人终收或冻 bm25。
  3. Given README 既有诚实句，When 本票结束，Then 「非 SaaS / 不声称 W12 通过 / 非闭合测量」仍在。
- **Provenance**:
  - Kind: adapt
  - Source: `README.md` Current status（停在 V2）；权威 `docs/roadmap.md` 文首（DOC-01 合入后）、ADR-0032/0033、`docs/evidence/i3/`
  - Pin: 仓内现行文件
  - What changed: 对外现状表补 I3 与过线闸，不扩功能叙事
  - Why not copy as-is: 对外页滞后于已关门 evidence
  - License note: 仓内文档
- **Tests**: waived（纯文档）
- **Rollback**: 还原 `README.md`
- **Do-not-touch**: 把 W12 报告链进「已通过」；升格渗透认证；改 Python；CONTEXT 新词

### Provenance status
- result: pass
- notes: 对外 README 相对 evidence 过时

### Evidence *(after Matt `/implement`)*
- typecheck: n/a
- tests: waived
- paths: `README.md`（I3 / Hard-Gold / Known gaps / Next hop）

## Handoff
`done | DOC-02 | 对外现状已回填 | 未提交`

## Blocked by
- DOC-01
