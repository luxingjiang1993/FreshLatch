# TASK · A-P6 红队成对回归

## Ticket
- **ID**: A-P6
- **Title**: `test(security): red-team accept/reject pair fixtures in CI`
- **Paths**: `tests/unit/test_redteam_accept_reject_pairs.py`, `src/freshlatch/redteam_pairs.py`, `docs/security.md`, `tasks/A-P6.md`
- **Trust**: Watch
- **Blast**: none

## Agent Guards
- **Acceptance**:
  1. ≥3 accept/reject pairs in pytest (应拒 must deny/abstain; 不应拒 must not false-refuse on the fixture path).
  2. Fail-closed on cross-tenant / unauthorized where pair touches ACL/serving.
  3. Docs: 红队范围句；garak optional note only (no mandatory paid/external scan).
- **Provenance**: OpenAI FC strict / Guardrails spirit; reuse abstain/ACL fixtures if present.
  - Kind: adapt
  - Source: `src/freshlatch/gates/rule_gate.py#rule_gate`；`src/freshlatch/roles/conflict_evidence.py#fresh_refusal_for_conflicting_evidence`；`src/freshlatch/tools.py#tool_schema_error`；`src/freshlatch/serving/acl.py#enforce_mapped_action`；`src/freshlatch/store/tenant_acl.py#write_for_session`
  - What changed: 六对夹具走 `run_redteam_fixture`。应拒为 deny 或 abstain；不应拒是近邻措辞、同值前提、声明过的工具字段，或服务端映射下的本租户读/写/会话。ACL 对复用 A-P2 凭证映射与 A-P4 的 fail-closed。
  - Why not copy as-is: 既有单测各自覆盖一条拒绝。本刀把应拒与不应拒绑在同一入口，避免只测拒绝、不测误拒。
- **Tests**: added（成对夹具即交付物）
- **Do-not-touch**: floors / gold / x1 / PRODUCTION_RETRIEVAL_MODE / SESOI / C-04 / RESULT-Y

### Provenance status
- result: pass
- notes: 未改规则闸、冲突拒答、工具 schema、Serving 鉴权与写入 ACL 的既有判定。新模块只把两侧夹具送进这些入口。

### Evidence
- typecheck: `python -m compileall -q src/freshlatch/redteam_pairs.py`
- tests: `python -m pytest tests/unit/test_redteam_accept_reject_pairs.py -q` → 8 passed；无付费 API；未调用外网 garak
- paths: `src/freshlatch/redteam_pairs.py` · `tests/unit/test_redteam_accept_reject_pairs.py` · `docs/security.md`

## Handoff
2026-10-15 | A-P6 | done | draft PR；pytest 8 passed；无付费 API；未调用外网 garak

## Grill 锁（2026-10-15）
1. 成对夹具：应拒 / 不应拒 ≥3 对进 pytest
2. 可选 garak：文档说明可选；本刀不强制外网/付费扫描
3. 与 ACL/Serving 身份一致：拒答路径 fail-closed 可测
4. Docs：红队范围句（≠ 完整对抗安全认证）

不做：改 floors/gold/x1；付费外网扫；发明 SESOI。
