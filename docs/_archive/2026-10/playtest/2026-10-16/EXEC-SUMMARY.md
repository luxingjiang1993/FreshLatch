# EXEC-SUMMARY · FreshLatch Playtest P0 · 2026-10-16 (Asia/Shanghai)

**Synthetic UX only — not RESULT-Y 乙. Not a release gate.**

## Go / No-Go (UX P0 — operator draft for parent; **not** judge verdict)

| Call | Rationale |
|------|-----------|
| **Conditional Go (API/shell)** | J3 fail-closed **held** on all exercised renew-without-T1 paths (`RENEW_NO_EVIDENCE` / `RENEW_EVIDENCE_UNRESOLVED` / reverify-without-T1 HTTP 400). UI reachable HTTP 200. J2 discard API ok. |
| **Hold full Go** |「跑」Start reverify **attempted and succeeded** (HTTP 200, 137s, sheet live). Control Δ still n/a if J1b not re-run. Independent judge not yet run. |

Do **not** treat this file as `judgement.jsonl` pass.

## Top findings

1. **J3 fail-closed OK (API + UI)** — renew without valid T1 blocked (API `RENEW_*` / HTTP 400; UI `#续命` disabled, title 续命不可用). Screenshot `J3-step1-renew-disabled.png`.
2. **UI up + screenshots** — SYNTHETIC + `#btn-run` 开始复验; T1 synthetic selected; evidence pane shows T0 text (`J2-step1-evidence-pane.png`).
3. **J1 Start reverify under「跑」** — `POST /api/reverify` HTTP 200 in 137s; 12 claims; latch pending 8; disposition 勿发; trajectory `run-20261016-124848.jsonl`. Sheet usable. Control Δ still may be n/a (J1b not re-run).
4. **J2** — prior sheet claims + click-through to `#pane` OK; API discard also OK.
5. **Screenshots done** — J1a×3, J1b×1, J2×1, J3×1 under `screenshots/` (mirrored). Independent judge still pending.

## Control Δ

**Not measurable** this run (no paired J1a/J1b full sheet completions; J1b only re-opened landing).

## Infra melt flags

| Flag | Status |
|------|--------|
| Start reverify >8 min | **No** — completed in 137s (<8 min melt) |
| Paid LLM spend | **Used under「跑」** (authorized); wall 137s |
| UI start blocker | None |
| Port 8000 | Serving |

## UI process

- Command: `cd /workspace/freshlatch && PYTHONPATH=/workspace/freshlatch/src /workspace/freshlatch-formal-venv/bin/python -m freshlatch.ui.app`
- PID: **2081100**
- URL: http://127.0.0.1:8000 → HTTP 200

## Artifacts

`/workspace/freshlatch-playtest-2026-10-16/` (+ mirror `docs/playtest/2026-10-16/`)

## 「跑」(authorized live reverify)

- Attempted: yes (`POST /api/t1-source/synthetic` then `POST /api/reverify`)
- Result: HTTP **200**, wall **137s**, sheet **usable**
- Claims: 12 (stale4 / fresh4 / unknown4); latch pending **8**; disposition **勿发**
- Evidence: `api-evidence/20-reverify-live.json`, `20-reverify-live.meta.json`, `21-claims-after-reverify.json`
- Control Δ: still **n/a** (J1b not re-run this arm)
- Browser after-run screenshots: parent follow `BROWSER_AFTER_RUN.md`

## Judge pass #2 (independent UX · 2026-10-16)

Independent judge re-scored after authorized「跑」+ wipe note. **Not** operator self-pass.

| Journey | task_success | Key delta |
|---------|--------------|-----------|
| J1a | **pass** | API live reverify 137s / 勿发 / sheet_usable; **not** infra_timeout. Live 勿发 sheet **UI wiped** by `boot()`—do not treat `*-after-boot-wipe` as 勿发 render. `evidence_ok` still insufficient (no click on live 勿发 sheet). |
| J1b | insufficient_evidence | Control Δ still **n/a** |
| J2 | partial | evidence_ok pass (prior pane); discard UI still unscored |
| J3 | pass | renew_without_t1 **blocked** stands |

**Full UX Go: still held** (Control Δ n/a + live 勿发 sheet UI not captured). See `JUDGE_NOTES.md` / `judgement.jsonl`.
