# Browser / computerUse checklist (Playtest P0)

UI is running at **http://127.0.0.1:8000** (PID see EXEC-SUMMARY). This agent has **no computerUse**; parent should dispatch screenshots.

## Global selectors

| Element | Selector / text |
|---------|-----------------|
| SYNTHETIC badge | `.syn` / title contains `SYNTHETIC` |
| Main CTA | `#btn-run` text **开始复验** |
| T1 synthetic card | `#t1-card-synthetic` |
| T1 paste card | `#t1-card-paste` |
| T1 upload card | `#t1-card-upload` |
| Claims list | `#claims` |
| Disposition bar | `#disposition-bar` / `#disp-value` |
| Void modal | `#modal` (文案含「作废后重跑不得再绿」) |
| Renew modal | `#renew-modal`, `#renew-evidence`, `#renew-claim` |
| Evidence pane | `#pane` |
| Claim ledger | `#claim-ledger` |
| Banner | `#banner` / 待人工 |

## J1a — cold Control (do NOT open README)

1. Open only `http://127.0.0.1:8000`
2. Screenshot landing: SYNTHETIC + 开始复验 visible?
3. Click `#t1-card-synthetic` → wait ready message
4. Click `#btn-run` **开始复验**
5. Stopwatch TTFM (open → first Start reverify or T1 select)
6. If sheet appears: screenshot claims + disposition; click ≥1 claim → evidence in `#pane`
7. If wait >8 min / model 5xx: screenshot waiting copy only; mark `infra_timeout` / partial — **not** UX P0

## J1b — README-script Control

1. Allow README Quick start: venv, `python -m freshlatch.ui.app`, Start reverify
2. Same T1 synthetic → Start reverify → sheet
3. Record success/partial/fail vs J1a for Control Δ

## J2 — evidence + discard

1. After sheet with stale/unknown pending: open claim → confirm `#pane` shows T0/T1 text
2. Click 作废 → confirm `#modal` → submit 人审
3. Screenshot: voided card (`.claim.voided`), ledger/timeline; must **not** read as 可发 green for that claim

## J3 — renew without valid T1

1. Prefer claim with **no** `@T1` evidence: renew button should be **disabled** (title 续命不可用)
2. If somehow open renew modal: leave `#renew-evidence` empty / cancel — must not succeed
3. Adversary: try submit renew without evidence via UI; expect error on screen
4. Screenshot fail-closed

## Screenshot naming

`docs/playtest/2026-10-16/screenshots/J{1a|1b|2|3}-stepN.png`
