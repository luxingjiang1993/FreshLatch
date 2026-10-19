# WIPE_NOTE · 2026-10-16

Opening `http://127.0.0.1:8000/` runs the sheet page `boot()`, which **POSTs `/api/import`**. That call replaces in-memory `_state` with a fresh synthetic docket and a new prepublish run. It does **not** reload the live reverify result.

## What was wiped

The completed Start reverify (ended 2026-10-16 12:48:49 +08, HTTP 200, **137s**) was still in process memory when screenshot capture began. Authoritative capture, already on disk:

- `api-evidence/20-reverify-live.meta.json` — disposition **勿发**, latch pending **8** (`c1,c2,c3,c7,c9,c10,c11,c12`), status hist stale 4 / fresh 4 / unknown 4, `sheet_usable: true`
- `api-evidence/20-reverify-live.json` and `20-reverify-live.raw.json` — same sheet: run `run-e39047098a`, run_status 待人审, thread `reverify-round-20261016-124848`
- `api-evidence/21-claims-after-reverify.json` (+ `.raw.json`)

After `boot()` → `POST /api/import`, `GET /api/claims` showed disposition **需补丁**, run `run-3f713a3376` (已落档), **latch pending 0**, all 12 claims `unknown` with empty `t1_evidence_ids`. Budget 6/18 and 19/24 was left over from the reverify (import does not clear budget). The 勿发 run remains only as a **prepublish list row** (updated `2026-10-16T04:48:49+00:00`, status 复验中). Opening that row's「打开详情」goes to `/`, which boots and imports again — it does **not** restore the sheet. That link was not clicked.

## Screenshots in this folder

| File | What it actually shows |
|---|---|
| `J1a-step4-sheet-after-boot-wipe.png` | Live page **after** the import wipe. **Not** the 勿发 reverify render. 包结论 需补丁, run `run-3f713a3376`, 逐条闸结果 all `unknown`. |
| `J1a-step4-prepublish-勿发-run.png` | `/prepublish` list. Second row is the reverify round: 包结论 **勿发**, `2026-10-16T04:48:49+00:00`, Run 状态 复验中. Top row is the later import (需补丁). |
| `J2-step2-evidence-after-run.png` | Post-wipe sheet only. Clicked `t0-competitor-notes#p2`. `#pane` shows T0《竞品访谈笔记》with p2 highlighted. Not the 勿发-sheet evidence state. |
| `J3-step2-renew-after-run.png` | Post-wipe sheet. 续命 on claims without T1 evidence is **disabled** (`title`: 本轮无已检索 T1 原文块,续命不可用). DOM check: first 续命 `disabled=true`. |

Server PID **2081100** was not killed. **开始复验** was not clicked again (no second `/api/reverify`).
