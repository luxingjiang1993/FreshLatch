# TASK / ticket — PE-B-02

## Ticket
- **ID**: PE-B-02 / GitHub #438
- **Title**: `docs(#436): 仓外试分离门闩报告（不进主表）`
- **Paths**: `docs/evidence/patch-events/GATE-SEPARATION.md`

## Agent Guards
- **Blast**: docs evidence
- **Trust**: Watch
- **Acceptance**:
  1. 报告含自然放行/自然误放/按 R 的固定 k 误放差。
  2. 文首：不进主表、可扔、非甲；写明三条件是否过门。
  3. 未过门不得建议激活；不改 PREREG-B 文首；不发模型除非人授。
- **Provenance**:
  - Kind: new
  - Source: `docs/evidence/patch-events/PREREG-B.md` 门闩节
- **Do-not-touch**: RESULT-B 成立格；PREREG-B 激活批注（仅人在过门后写）

### Provenance status
- result: pass

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`pending | PE-B-02 | after-437 | next=/before-implement 438`
