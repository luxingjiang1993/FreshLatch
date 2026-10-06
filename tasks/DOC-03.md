# TASK / ticket — DOC-03

## Ticket
- **ID**: DOC-03
- **Title**: `docs(spec): W1–W4 汇编历史化与关键句回填`
- **Paths**: `docs/spec/README.md` · `docs/spec/00-架构总览.md` · `docs/spec/01-目录与模块.md`

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 规格索引与 00/01 文首，When 新读者打开，Then 可见「历史汇编；冲突以 ADR + CONTEXT 为准」（或等价横幅）。
  2. Given 00 现行叙述（非明确标为历史的句子），When 读 Agent 组成，Then 不得把 Auditor 与 Lead/Critic 并列成三个带工具真 Agent；须指向单轮 structured-output、不得拥有放行权。
  3. Given 00 现行叙述，When 读 Lead 检索，Then 不得写「自主决定改写查询」为现行能力；须指向主张查询变换。
  4. Given 00/01 现行叙述，When 读检索管线与 HumanLatch，Then 不得把「后两级空实现」「续命 disabled 占位」当作现在时；须写评测臂可跑、生产默认 BM25、续命已实装。
  5. Given 规格索引标题/导语，When 阅读覆盖范围，Then 不再暗示全书只有 W1–W4；卷 21 已在分卷表（可已存在则保持）。
- **Provenance**:
  - Kind: adapt
  - Source: `docs/spec/00-架构总览.md`、`01-目录与模块.md`、`docs/spec/README.md`；权威 ADR-0009、CONTEXT 主张查询变换、ADR-0003 修订后的评测臂
  - Pin: 仓内现行文件
  - What changed: 横幅 + 最少关键句回填，不重画整张数据流图
  - Why not copy as-is: W1–W4 汇编未随 V1–I3 回填
  - License note: 仓内文档
- **Tests**: waived（纯文档）
- **Rollback**: 还原上述三文件
- **Do-not-touch**: 删除历史规格正文；改闸/角色 Python；新 ADR；重跑评测

### Provenance status
- result: pass
- notes: 早期规格与词表冲突，属 adapt

### Evidence *(after Matt `/implement`)*
- typecheck: n/a
- tests: waived
- paths: `docs/spec/README.md` · `docs/spec/00-架构总览.md` · `docs/spec/01-目录与模块.md`

## Handoff
`done | DOC-03 | 历史横幅+关键句 | 未提交`

## Blocked by
- DOC-01
