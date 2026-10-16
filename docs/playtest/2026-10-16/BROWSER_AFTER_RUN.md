# BROWSER_AFTER_RUN · after「跑」live reverify · 2026-10-16

UI still serving: **http://127.0.0.1:8000** (PID **2081100** — do not kill).

Live Start reverify already completed via API (HTTP 200, 137s). Sheet state is in memory: 12 claims, latch pending 8, disposition **勿发**. Parent agent with computerUse should capture screenshots only — **do not** re-POST `/api/reverify` unless intentionally starting a new paid run.

Save PNGs under `/workspace/freshlatch-playtest-2026-10-16/screenshots/` (mirror to `docs/playtest/2026-10-16/screenshots/`).

## Exact screenshot steps

### 1) Landing after sheet (J1a post-run)

1. Open a cold or fresh tab → `http://127.0.0.1:8000/`
2. Wait for claims list / Reverify Sheet to render (should already show post-reverify state; if empty shell, click **开始复验** `#btn-run` only if API state was lost — prefer reload first).
3. Confirm visible: SYNTHETIC badge, disposition bar showing **勿发** (or equivalent disposition UI), claim cards with stale/fresh/unknown mix.
4. Screenshot full viewport → `J1a-after-run-landing.png`

### 2) Claims list

1. Scroll the claims / sheet list so multiple claim cards are visible (include at least one **stale**, one **fresh**, one **unknown** if possible: e.g. c1 stale, c4 fresh, c9 unknown).
2. Screenshot → `J1a-after-run-claims-list.png`

### 3) Evidence click (J2 substrate on live sheet)

1. Click a claim card that has T1 evidence (e.g. **c1** — SeaDesk pricing / stale).
2. Wait for right evidence pane (`#pane` or source panel) to show T0/T1 section text with anchors.
3. Screenshot claim selected + evidence pane → `J2-after-run-evidence-click.png`

### 4) Disposition bar

1. Ensure the disposition / gate strip is in view (disposition value **勿发** from live run).
2. Screenshot disposition bar + nearby latch/pending affordances → `J1a-after-run-disposition-bar.png`

### 5) Optional latch pending strip

1. If UI shows HumanLatch pending queue (8 pending: c1,c2,c3,c7,c9,c10,c11,c12), screenshot it → `J1a-after-run-latch-pending.png`
2. **Do not** complete discard/renew decisions unless the parent task explicitly asks — this pack is evidence capture after「跑」.

## Do not

- Kill PID 2081100
- `git push`
- Touch floors/gold/x1/PRODUCTION_RETRIEVAL_MODE/RESULT-Y/PREREG-Y
- Start another reverify unless authorized again (paid LLM)

## API cross-check (already captured)

- `api-evidence/20-reverify-live.meta.json` — http_status 200, wall_seconds 137, sheet_usable true
- `api-evidence/21-claims-after-reverify.json` — 12 claims summary
