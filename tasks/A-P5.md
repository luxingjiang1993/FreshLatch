# TASK · A-P5 成本/延迟硬门

## Ticket
- **ID**: A-P5
- **Title**: `feat(ops): cost+latency hard gate on release checklist`
- **Paths**: `src/freshlatch/sli/release_gate.py`, `src/freshlatch/sli/__init__.py`, `tests/unit/test_a_p5_release_gate.py`, `docs/ops/发车检查单-成本延迟硬门.md`
- **Trust**: Watch
- **Blast**: none

## Agent Guards
- **Acceptance**:
  1. Callable gate: relative to baseline, cost ≥1.5× OR e2e P95 over SLA → fail (发车红).
  2. Pytest: inject over-budget → fail; within budget → pass. No paid API.
  3. Hook/read A-P3 primary SLI fields when useful (`e2e_p95_ms`, rates); objective/SLA numbers passed in by caller (no invent SESOI).
  4. Docs: release checklist item + rollback env; cost 不伪装质量.
- **Provenance**: adapt sli/alert.py patterns from A-P3; Databricks latency budget spirit.
  - Kind: adapt
  - Source: `src/freshlatch/sli/alert.py#measure_primary_sli`（`a25889d`）
  - What changed: 新模块 `check_release_gate` 读主 SLI 的 `e2e_p95_ms` 与 abstain/fallback 率。成本相对调用方基线 ≥1.5 倍，或 e2e P95 超过调用方 SLA，发车检查单记发车红。两率不参与红绿。
  - Why not copy as-is: `alert.py` 是 multiwindow burn-rate page。本票是发车检查单硬门，基线与 SLA 仍由调用方传入，不把 1.5 倍写成 SESOI。
- **Do-not-touch**: floors / gold / x1 / PRODUCTION_RETRIEVAL_MODE / SESOI / C-04 / RESULT-Y
- **Tests**: added（`tests/unit/test_a_p5_release_gate.py`）
- **Rollback**: `FRESHLATCH_RELEASE_GATE=off`（仍记下破线，`blocked=false`，检查单为关闸）

### Provenance status
- result: pass
- notes: 未改检索默认臂，未发明 SESOI。基线与 SLA 无默认数。成本不伪装质量。

### Evidence
- typecheck: `python -m compileall -q src/freshlatch/sli` 通过
- tests: `python -m pytest tests/unit/test_a_p5_release_gate.py tests/unit/test_a_p3_sli_page.py -q` → 21 passed（A-P5 11 passed）；无付费 API
- paths: `src/freshlatch/sli/release_gate.py` · `tests/unit/test_a_p5_release_gate.py` · `docs/ops/发车检查单-成本延迟硬门.md`

## Handoff
Draft PR A-P5. draft=true. 无付费 API。

## Grill 锁（2026-10-15）
1. 热路径相对基线：成本 ≥1.5× 或 e2e P95 超 SLA → 发车检查单红
2. 可测：pytest 注入超标样本 → gate fail；基线内 → pass
3. 与 A-P3 SLI 数字衔接（可读 primary SLI / 合成窗）；不发明 SESOI
4. Docs：发车检查单勾选项 + 回滚关闸 env
