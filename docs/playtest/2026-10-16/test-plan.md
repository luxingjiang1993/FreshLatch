# FreshLatch Playtest P0 · test-plan · 2026-10-16 (Asia/Shanghai)

> Scope (user「开跑 E3」/ Playtest P0 default): **J1a + J1b + J2 + J3**  
> Persona primary: **P-Lead** (anchors A1–A5); J3 also **P-Assoc / P-Adversary**  
> Synthetic UX only — **not** a release gate; do **not** claim RESULT-Y 乙.  
> Plan: `/workspace/freshlatch-synthetic-user-eval-plan.md` v1.1 · Rubric: `freshlatch-synthetic-user-judge-rubric.md`  
> Judge: **separate chat** (see JUDGE_HANDOFF.md). Operator must not self-pass.

## Environment

| Item | Value |
|------|-------|
| Project root | `/workspace/freshlatch` |
| Start | `cd /workspace/freshlatch && PYTHONPATH=/workspace/freshlatch/src /workspace/freshlatch-formal-venv/bin/python -m freshlatch.ui.app` |
| URL | http://127.0.0.1:8000 |
| Pack | active resolve → thesis-1 / synthetic corpus (UI SYNTHETIC) |
| LLM | Cloud keys present in env (`DASHSCOPE_API_KEY` etc.); **full Start reverify deferred** this run to minimize paid spend — see status |

## Personas & anchors (P0)

### P-Lead (primary)
| # | Anchor | Expectation for this run |
|---|--------|--------------------------|
| A1 | README「does that judgment still hold?」 | Product job = reverify, not new brief |
| A2 | Main CTA = **Start reverify** / **开始复验** | Find `#btn-run` cold |
| A3 | Sell voiding and gaps | Not faster summaries / auto decisions |
| A4 | CONTEXT: expired/conflict/no-T1 cannot stay green | Human void or renew |
| A5 | T1 Source Picker required | No pretend latest facts without T1 |

### P-Assoc / P-Adversary (J3)
| # | Anchor | Expectation |
|---|--------|-------------|
| B4/B5/D1 | renew needs ≥1 T1 `evidence_id`; no `t1_evidence_ids` → not fresh | J3 must block |

## Journeys

### J1a — cold Control
- **Do not** open README.
- Open URL → select synthetic T1 (`#t1-card-synthetic`) → **开始复验** → readable sheet → ≥1 evidence click-through.
- Record: success / partial / fail, TTFM, wrong_product.
- Infra >8 min or model 5xx → `infra_timeout` partial (not UX P0).

### J1b — README-script Control
- Allow README Quick start three steps.
- Same synthetic pack / same judge rubric.
- Record Δ vs J1a (doc dependence); Δ is explanatory only, not a release gate alone.

### J2 — evidence click-through + discard
- After pending red/yellow: open claim → T0/T1 original in pane.
- **discard** stale → ledger/timeline visible; must not read as 可发 green.

### J3 — fail-closed renew without valid T1
- Attempt renew with missing / empty / unresolved T1 evidence → **must block** (0 allows).
- Also: Start reverify with T1 not ready → HTTP 400.
- Bucket if allowed: `renew_without_t1_allowed` (**P0 accident**).

## Out of scope this P0 file
J4 patch, J5 Partner 30s, J6 full adversary suite (P1).

## Evidence expected
- API JSON under `api-evidence/`
- Browser screenshots via computerUse (see BROWSER_NEEDED.md) — pending if not yet taken
- Independent `judgement.jsonl` from separate judge chat

## Do-not-touch
floors / gold / x1 / PRODUCTION_RETRIEVAL_MODE / RESULT-Y / PREREG-Y · no git push/merge by operator.
