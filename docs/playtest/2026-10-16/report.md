# Playtest report (first person) · E3 P0 · 2026-10-16 Asia/Shanghai

I ran FreshLatch Playtest P0 for Oriental Ronin as the operator agent. Scope: J1a + J1b + J2 + J3. I did **not** message the user. I did **not** push git. I did **not** self-score journeys as judge-pass.

## Setup

I used the existing checkout at `/workspace/freshlatch` only. The formal venv at `/workspace/freshlatch-formal-venv` already had deps; I bound the package with `PYTHONPATH=/workspace/freshlatch/src` so the lowercase checkout was the project root.

I started:

```bash
cd /workspace/freshlatch
PYTHONPATH=/workspace/freshlatch/src /workspace/freshlatch-formal-venv/bin/python -m freshlatch.ui.app
```

Uvicorn came up on `http://127.0.0.1:8000` (PID 2081100). `GET /` returned **HTTP 200**. The HTML title is `FreshLatch 复验单 — SYNTHETIC`; the main button is `#btn-run` **开始复验**.

Env already had cloud LLM keys (`DASHSCOPE_API_KEY`, `DEEPSEEK_API_KEY`, `MOONSHOT_API_KEY`). Per plan preference for zero/minimal paid spend, I **did not** call live `POST /api/reverify` after selecting T1. That means J1 did not produce a full Reverify Sheet in this session. I labeled that as spend deferral / partial substrate — **not** a UX P0 invent from infra.

## What I exercised

### Landing + T1 (J1 shell)

1. Confirmed SYNTHETIC badge and 开始复验 in HTML (API-only / HTML parse — **no browser screenshot**).
2. `GET /api/t1-source` → `ready:false`.
3. `POST /api/reverify` **without** T1 → **HTTP 400** with 未选定合法 T1… (good fail-closed shell).
4. `POST /api/t1-source/synthetic` → `ready:true`, `synthetic:true`, `ingested_chunks:84`.
5. `POST /api/import` → 12 claims loaded; pack question visible in run meta.

**J1a cold browser path:** not done (no computerUse).  
**J1b README script browser path:** not done.  
**Full Start reverify sheet:** not done (LLM deferred).

### Evidence substrate (J2 partial)

Live `GET /api/source/t0-competitor-notes?as_of=T1` → HTTP 200, three anchors p1/p2/p3 with text. That is the click-through API behind the right pane. I did **not** click a claim card in a real browser.

### Discard (J2 API-only)

Using FastAPI TestClient + HumanLatch `enter_round` (zero LLM), I submitted `action: discard` for a stale claim. Result: `ok:true`, `voided:true`, machine `status` remained `stale`, id entered invalidation list. UI double-confirm modal and ledger screenshots are **pending**.

### Renew without valid T1 (J3 — API/gate done)

Zero-LLM gate + TestClient:

| Case | Outcome |
|------|---------|
| renew `evidence_id` missing/None | `ok=false` `RENEW_NO_EVIDENCE` |
| renew `evidence_id=""` | `ok=false` `RENEW_NO_EVIDENCE` |
| renew `fake-doc#p1@T1` | `ok=false` `RENEW_EVIDENCE_UNRESOLVED` |
| live reverify when T1 not ready | HTTP 400 |
| UI copy | renew disabled title 本轮无已检索 T1 原文块,续命不可用 present in HTML |

Verdict for exercised paths: **FAIL_CLOSED_OK** — I observed **0** `renew_without_t1_allowed`. Browser renew-modal screenshot still needed for judge visual evidence.

## Journey status table

| Journey | Mode | Status | Notes |
|---------|------|--------|-------|
| J1a | API/HTML shell; browser pending | **partial / pending screenshot** | CTA+SYNTHETIC in HTML; T1 synthetic works; no sheet (LLM deferred) |
| J1b | not run | **pending** | Control Δ n/a |
| J2 | API discard + live source | **API-only pass substrate; UI pending** | discard voided; source sections OK |
| J3 | API + gate (+ live no-T1 reverify) | **API fail-closed OK; UI screenshot pending** | see `api-evidence/10-j3-renew-without-t1.json` |

## Spend / infra

- Paid LLM reverify: **not invoked**
- UI start: OK
- No floors/gold/x1/PRODUCTION_RETRIEVAL_MODE/RESULT-Y/PREREG-Y edits
- No git push

## computerUse still needed?

**Yes** — follow `BROWSER_NEEDED.md` for J1a/J1b screenshots, J2 discard+ledger, J3 disabled renew button.

## Honest limit

I am not the independent judge. Paths for judge input are in `JUDGE_HANDOFF.md`. Missing screenshots should yield `insufficient_evidence` where the rubric requires visible UI proof — I am not inventing pass.
