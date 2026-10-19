# JUDGE_HANDOFF · Playtest P0 · 2026-10-16

**Independent judge must be a separate chat.** Operator (this playtest) must not self-pass.

## Rubric (paste full file into judge chat)

`/workspace/freshlatch-synthetic-user-judge-rubric.md`

## Operator artifacts (read-only inputs)

Primary folder:

`/workspace/freshlatch-playtest-2026-10-16/`

Mirror (for later PR by parent Cloud Agent — not pushed by operator):

`/workspace/freshlatch/docs/playtest/2026-10-16/`

| File | Role |
|------|------|
| `test-plan.md` | Scope J1a+J1b+J2+J3 |
| `report.md` | First-person narrative + status table |
| `findings.md` | Failure buckets |
| `EXEC-SUMMARY.md` | ≤1 page draft Go/Conditional — **not** judgement |
| `API_ROUTES.md` | Route map + J3 expected behavior |
| `BROWSER_NEEDED.md` | Screenshot checklist (may still be empty of PNGs) |
| `api-evidence/02-reverify-no-t1.json` | Live HTTP 400 no T1 |
| `api-evidence/03-t1-synthetic.json` | Synthetic T1 ready |
| `api-evidence/10-j3-renew-without-t1.json` | J3 FAIL_CLOSED_OK cases |
| `api-evidence/11-j2-discard.json` | Discard API |
| `api-evidence/12-evidence-source-live.json` | Source click substrate |

## Screenshots

Screenshots present (2026-10-16 computerUse): `J1a-step1-landing.png`, `J1a-step2-t1-synthetic.png`, `J1a-step3-cta-ready-no-run.png`, `J1b-step1-landing-after-readme-skip.png`, `J2-step1-evidence-pane.png`, `J3-step1-renew-disabled.png`. Note: Start reverify was **not** clicked (spend deferred) — J1 sheet completion fields may be `partial` / `insufficient_evidence` for full task_success. API JSON still supports J3 `fail_closed_ok` / `renew_without_t1=blocked`.

## Required judge output

`judgement.jsonl` — one JSON object per journey line per rubric fields.  
Place under the same playtest date folder when judge finishes.

## Suggested judge opener

> 你是独立 UX judge，不是用户。严格按 `freshlatch-synthetic-user-judge-rubric.md`。只根据 playtest 报告与截图/API 证据路径打分；缺证据则 `insufficient_evidence`。禁止因文笔流畅抬分。
