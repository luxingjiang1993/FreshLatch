# EXEC-SUMMARY · FreshLatch Playtest P0 · 2026-10-16 (Asia/Shanghai)

**Synthetic UX only — not RESULT-Y 乙. Not a release gate.**

## Go / No-Go (UX P0 — operator draft for parent; **not** judge verdict)

| Call | Rationale |
|------|-----------|
| **Conditional Go (API/shell)** | J3 fail-closed **held** on all exercised renew-without-T1 paths (`RENEW_NO_EVIDENCE` / `RENEW_EVIDENCE_UNRESOLVED` / reverify-without-T1 HTTP 400). UI reachable HTTP 200. J2 discard API ok. |
| **Hold full Go** | J1 **new** sheet via Start reverify not run (spend deferred). Control Δ n/a. Independent judge not yet run. |

Do **not** treat this file as `judgement.jsonl` pass.

## Top findings

1. **J3 fail-closed OK (API + UI)** — renew without valid T1 blocked (API `RENEW_*` / HTTP 400; UI `#续命` disabled, title 续命不可用). Screenshot `J3-step1-renew-disabled.png`.
2. **UI up + screenshots** — SYNTHETIC + `#btn-run` 开始复验; T1 synthetic selected; evidence pane shows T0 text (`J2-step1-evidence-pane.png`).
3. **J1 full reverify skipped** — did **not** click 开始复验 (no paid LLM); journeys partial / spend-deferred per plan §7; **not** UX P0.
4. **J2** — prior sheet claims + click-through to `#pane` OK; API discard also OK.
5. **Screenshots done** — J1a×3, J1b×1, J2×1, J3×1 under `screenshots/` (mirrored). Independent judge still pending.

## Control Δ

**Not measurable** this run (no paired J1a/J1b full sheet completions; J1b only re-opened landing).

## Infra melt flags

| Flag | Status |
|------|--------|
| Start reverify >8 min | Not attempted |
| Paid LLM spend | **Deferred** (keys present: DASHSCOPE/DEEPSEEK/MOONSHOT injected — unused for reverify) |
| UI start blocker | None |
| Port 8000 | Serving |

## UI process

- Command: `cd /workspace/freshlatch && PYTHONPATH=/workspace/freshlatch/src /workspace/freshlatch-formal-venv/bin/python -m freshlatch.ui.app`
- PID: **2081100**
- URL: http://127.0.0.1:8000 → HTTP 200

## Artifacts

`/workspace/freshlatch-playtest-2026-10-16/` (+ mirror `docs/playtest/2026-10-16/`)
