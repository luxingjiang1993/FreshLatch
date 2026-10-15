# TASK · A-P4 ACL 越权矩阵进 CI

## Ticket
- **ID**: A-P4
- **Title**: `test(acl): cross-tenant deny matrix in CI`
- **Paths**: `tests/` (matrix), optional `src/freshlatch/store/tenant_acl.py` / serving glue, `docs/`
- **Trust**: Watch
- **Blast**: auth | none

## Agent Guards
- **Acceptance**:
  1. Pytest matrix: ≥3 cross-tenant deny cases (read/write/session) fail-closed.
  2. Identity from server mapping (A-P2 pattern); client tenant_id alone never grants.
  3. Docs scope: 薄 ACL ≠ 完整 SaaS.
- **Provenance**: adapt tenant_acl + serving authorize_session patterns.
- **Do-not-touch**: floors / gold / x1 / PRODUCTION_RETRIEVAL_MODE / SESOI / C-04 / RESULT-Y
- **Tests**: added (the matrix IS the deliverable)

## Handoff
Draft PR A-P4. pytest green. No paid「跑」.
