# Findings · Playtest P0 · 2026-10-16

> Failure buckets per plan §2. Severity: P0 / P1 / P2.  
> **Not** a self-judged pass — judge chat owns pass/fail.

## Status of exercise

| ID | Exercise mode | Bucket if incomplete |
|----|---------------|----------------------|
| J1a | API shell: landing HTTP 200, SYNTHETIC + CTA present in HTML, T1 synthetic ready, import 12 claims. **Full Start reverify not run** (LLM spend deferred). Browser cold path pending computerUse. | pending screenshot → judge may use `insufficient_evidence` for task_success; shell CTA/T1 = observable |
| J1b | Not separately browser-run; README path documented. Control Δ **not measurable** until both arms complete sheet or legitimate partial. | Control Δ = n/a |
| J2 | API TestClient discard ok; live `GET /api/source/t0-competitor-notes?as_of=T1` returns 3 sections. UI discard modal / ledger screenshot pending. | API discard pass substrate; UI pending |
| J3 | **API + gate FAIL_CLOSED_OK** (see api-evidence/10-j3-renew-without-t1.json). Live reverify-without-T1 → 400. Browser renew-disabled screenshot pending. | no `renew_without_t1_allowed` observed in exercised paths |

## Findings table

| ID | Journey | Persona | Failure bucket | Severity | Screenshot | Repro | Suggestion | Gate/copy | Control arm |
|----|---------|---------|----------------|----------|------------|-------|------------|-----------|-------------|
| F-01 | J1a/b | P-Lead | `infra_timeout` (deferred spend) | — (non-UX) | pending | Operator skipped `POST /api/reverify` to avoid cloud LLM burn despite keys present | Optional: fixture/pre-stored sheet path for UX-only days; or approved short reverify budget | melt §7 | J1a/b |
| F-02 | J1a | P-Lead | (observation) cold CTA present in HTML | P2 if later cold fail | pending browser | GET `/` contains `#btn-run` 开始复验 + SYNTHETIC | Confirm cold findability with computerUse | copy/IA | J1a |
| F-03 | J2 | P-Lead | none on API discard | — | pending UI | TestClient discard → voided=true, status stays stale | Screenshot ledger after discard | HumanLatch | na |
| F-04 | J3 | P-Adversary | none — blocked | — | api JSON | renew None/"" → `RENEW_NO_EVIDENCE`; fake eid → `RENEW_EVIDENCE_UNRESOLVED`; reverify no T1 → 400 | Keep UI disabled path + backend gate | HumanLatch | na |
| F-05 | J1 | P-Lead | `copy_wrong_job` risk (hypothesis) | P2 hyp | n/a | Unverified without browser: ensure UI never reads as “Generate answer” | computerUse confirm no wrong CTA | docs | J1a |

## Bucket rollup (observed this run)

| Bucket | Count | Notes |
|--------|------:|-------|
| `renew_without_t1_allowed` | 0 | All exercised renew-without-T1 paths blocked |
| `infra_timeout` | 1 (deferred) | Intentional skip of paid Start reverify — not product UX P0 |
| `t1_not_selected` | 0 (gate works) | Live 400 when ready=false |
| `evidence_not_clickable` | 0 API | Source endpoint returns sections; UI click pending screenshot |
| `humanlatch_blocked` | 0 accidental | Expected blocks only |
| `status_misread_as_green` | insufficient_evidence | Needs browser + judge |
| `copy_wrong_job` | insufficient_evidence | Needs browser |
| `retrieval_empty` / `grade_insufficient` / `tool_tier_denied` | n/a | No full reverify |

## Explicit gaps

1. No screenshots yet → judge should not invent pass for J1 task_success / evidence_ok UI.
2. Control Δ (J1b − J1a) not measurable.
3. Full sheet after Start reverify not produced this session.
