# FreshLatch UI API map (Playtest P0 · 2026-10-16)

Base: `http://127.0.0.1:8000`  
Entry: `PYTHONPATH=/workspace/freshlatch/src python -m freshlatch.ui.app`  
Main CTA (UI): **开始复验** (`#btn-run`) — not Generate answer. Marked **SYNTHETIC**.

## Journeys ↔ routes

| Journey | Routes | Expected |
|---------|--------|----------|
| J1a/J1b select T1 | `GET /api/t1-source` → `POST /api/t1-source/synthetic` | `ready:true`, `synthetic:true`, ingested_chunks>0 |
| J1a/J1b Start reverify | `POST /api/reverify` | 200 + claims sheet **or** infra melt; **400** if T1 not ready |
| J2 evidence click | `GET /api/source/{doc_id}?as_of=T0\|T1` | 200 + `sections[]` with anchors |
| J2 discard | `POST /api/latch/decide` `{action:"discard"}` | ok=true; claim `voided=true`; status machine value retained (not silent green) |
| J3 renew no T1 | `POST /api/latch/decide` renew without / empty / unresolved `evidence_id` | `ok=false`, `RENEW_NO_EVIDENCE` or `RENEW_EVIDENCE_UNRESOLVED` |
| J3 shell gate | `POST /api/reverify` when T1 `ready=false` | **HTTP 400** 未选定合法 T1 |

## Full route list (from FastAPI)

| Method | Path |
|--------|------|
| GET | `/` Reverify Sheet HTML |
| GET | `/prepublish` |
| GET | `/api/claims` |
| GET | `/api/claim-ledger` |
| GET | `/api/claim-ledger/export.md` |
| POST | `/api/client-memo/export` |
| GET | `/api/prepublish/runs` |
| GET | `/api/prepublish/runs/{run_id}` |
| POST | `/api/publish-hook/check` |
| POST | `/api/import` |
| POST | `/api/import/draft` |
| GET | `/api/t1-source` |
| POST | `/api/t1-source/paste` |
| POST | `/api/t1-source/confirm` |
| POST | `/api/t1-source/synthetic` |
| POST | `/api/t1-source/upload` |
| POST | `/api/t1-source/url` |
| POST | `/api/reverify` |
| POST | `/api/latch/decide` |
| POST | `/api/latch/rerun` |
| GET | `/api/latch/status` |
| POST | `/api/patch/propose` |
| POST | `/api/patch/confirm` |
| POST | `/api/patch/discard-draft` |
| GET | `/api/source/{doc_id}?as_of=T0\|T1` |

## J3 fail-closed (exact)

1. **No T1 selected:** `POST /api/reverify` → HTTP 400  
   `{"error":"未选定合法 T1 来源,不得假装已有最新事实(请先完成 T1 来源三卡)"}`
2. **Renew missing/empty evidence_id:** latch decide → HTTP 200 body with `results[0].ok=false`, `error_code=RENEW_NO_EVIDENCE`
3. **Renew unresolved evidence_id:** `ok=false`, `error_code=RENEW_EVIDENCE_UNRESOLVED`
4. **UI:** renew button disabled when claim has no `*@T1` evidence ids; title `本轮无已检索 T1 原文块,续命不可用`

Evidence files: `api-evidence/02-reverify-no-t1.json`, `api-evidence/10-j3-renew-without-t1.json`
