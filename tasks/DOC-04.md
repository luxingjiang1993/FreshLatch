# TASK / ticket — DOC-04

## Ticket
- **ID**: DOC-04
- **Title**: `docs(src): 管线说明与 spawn_auditor 废弃标注`
- **Paths**: `src/freshlatch/store/pipeline.py` · `src/freshlatch/tools.py`

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 管线模块说明，When 阅读现时能力，Then 不得把 vector/rerank 写成「本期空实现、后续票填实」而不加评测臂已可跑的限定；须写清生产默认仍 BM25。
  2. Given 工具表 `spawn_auditor`，When 阅读挂载叙事，Then 标明 ADR-0009 废止；默认 Lead 白名单叙事不含 spawn_auditor。
  3. Given 本票 diff，When 对比行为，Then 不删除仍被测试引用的符号；不改 `PRODUCTION_RETRIEVAL_MODE` 赋值；不改规则闸谓词。
  4. Given 若改了 `.py`，When 跑权威 typecheck，Then `python -m compileall -q src` 退出码 0。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/store/pipeline.py` 模块 docstring（空实现）；`src/freshlatch/tools.py` `_TOOL_DEFS`/`spawn_auditor`；权威 ADR-0009、`roles/lead.py` 使用 `LEAD_TOOLS_W3`、`sqlite_store` 已分臂
  - Pin: 仓内现行文件
  - What changed: 仅 docstring/注释；符号保留
  - Why not copy as-is: 注释与实现/决议相反
  - License note: 仓内代码
- **Tests**: waived（注释-only；typecheck 见 Acceptance 4；不强制 pytest）
- **Rollback**: 还原两文件
- **Do-not-touch**: 闸逻辑、检索默认臂、Lead 白名单实际元组内容（除非只改旁边注释）、HumanLatch、发前钩子

### Provenance status
- result: pass
- notes: 注释相对代码过时

### Evidence *(after Matt `/implement`)*
- typecheck: `python -m compileall -q src` 退出码 0
- tests: waived
- paths: `src/freshlatch/store/pipeline.py` · `src/freshlatch/tools.py`

## Handoff
`done | DOC-04 | 注释诚实化 | 未提交`

## Blocked by
None (can start immediately).
