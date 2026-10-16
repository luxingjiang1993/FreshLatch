# Findings · Playtest P0 · 2026-10-16

> Failure buckets per plan §2. Severity: P0 / P1 / P2.  
> **Not** a self-judged pass — judge chat owns pass/fail.

## Status of exercise

| ID | Exercise mode | Bucket if incomplete |
|----|---------------|----------------------|
| J1a |「跑」live reverify HTTP 200 / 137s; 12-claim sheet + latch pending 8 + disposition 勿发. Browser sheet screenshots still pending computerUse. | sheet live API; UI screenshot still needed for visual task_success |
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
| `infra_timeout` | 0 (「跑」) | Live reverify finished in 137s; sheet usable — prior deferred-spend note superseded |
| `t1_not_selected` | 0 (gate works) | Live 400 when ready=false |
| `evidence_not_clickable` | 0 API | Source endpoint returns sections; UI click pending screenshot |
| `humanlatch_blocked` | 0 accidental | Expected blocks only |
| `status_misread_as_green` | insufficient_evidence | Needs browser + judge |
| `copy_wrong_job` | insufficient_evidence | Needs browser |
| `retrieval_empty` / `grade_insufficient` / `tool_tier_denied` | n/a this pass | Full reverify returned claims; retrieval_used 19/24 |

## Explicit gaps

1. No screenshots yet → judge should not invent pass for J1 task_success / evidence_ok UI.
2. Control Δ (J1b − J1a) not measurable.
3. Full sheet after Start reverify **produced under「跑」** (API). Browser screenshots still gap.


## 「跑」update (live Start reverify)

Authorized live `POST /api/reverify` completed **HTTP 200 in 137s** (Asia/Shanghai 12:46:32→12:48:49). **J1a sheet now live** — not `infra_timeout`.

| Field | Value |
|-------|-------|
| http_status | 200 |
| wall_seconds | 137 |
| claim_count | 12 (stale4 / fresh4 / unknown4) |
| latch_pending_count | 8 |
| disposition | 勿发 |
| trajectory | reports/trajectories/run-20261016-124848.jsonl |
| sheet_usable | true |
| melt | no (>8 min no sheet did **not** apply) |

Evidence: `api-evidence/20-reverify-live.json`, `20-reverify-live.meta.json`, `21-claims-after-reverify.json`.

F-01 prior “deferred spend / infra_timeout” for J1a full sheet is **superseded** for the API path: sheet produced. Browser screenshot of sheet still pending (`BROWSER_AFTER_RUN.md`). Control Δ still n/a (J1b not re-run).
