# FreshLatch · Messaging one-pager (2026-10-16 · Asia/Shanghai)

> Guardrail against narrative drift. Interview / demo / external copy: use only this page.  
> Authority anchors: near-term plan `freshlatch-near-term-plan-2026-10-16` (out-of-repo); RESULT-Y=丙 ([`docs/evidence/patch-events/RESULT-Y.md`](evidence/patch-events/RESULT-Y.md)); Sprint(A) P0–P9 + MUM merged ≠ statistical pass.

> Structure overview (2026-10): [`docs/architecture/2026-10-overview.md`](architecture/2026-10-overview.md)

---

## 1. Dual-track framing

| Ruler | Current state | May say | Must not say |
|------|---------------|---------|--------------|
| **Product / PMF** | CONDITIONAL GO; no paid customers; RESULT-Y **丙**; registered G1/A1/T1/R1 = `counted_as_pass=false` | Keep building; sell the reverify latch for voids and gaps | Sellable / PMF / SaaS / product ready |
| **Engineering (in-repo A-layer / M8)** | **Engineering L4 / regressible refusal product** (Sprint(A) + observation hooks) | fail-closed, negative-result literacy, min-6 observation, HumanLatch | "L4 already delivered to a production team"; Meta E4 equivalent |
| **Externally honest band** | ≈ **L3+ / weak-L4** single-machine refusal prototype | typed abstain + hybrid+rerank + fixture CI | Domain benchmark / L5 / registration pass |
| **Primary experiment** | RESULT-Y=丙: k=151, T−C point ≈0.0927, 95% lower bound ≈−0.0065≤0 → **not established** | Preregistered negative result, reproducible needle | Near a pass / practically significant / regrade to 乙 |

**90-day kill (kills only the "product ready" narrative, not the portfolio):**  
Through about 2027-01-14, if still missing (a) a regressible refusal-edge fixture, (b) ≥1 design-partner per-session log, and (c) min-6 weekly report continuous dry-runs → drop "product ready" talk; demote to engineering portfolio + L3 research track.

---

## 2. Production defaults (docs aligned with code)

- `PRODUCTION_RETRIEVAL_MODE = hybrid+rerank` (local `BAAI/bge-reranker-base`, reranks hybrid top-10)
- BM25 only via `set_retrieval_switch("bm25")` fallback; **not** the production default
- Hard-Gold / #259 evidence is citable; **not** a closed statistical product pass
- Interview/demo UI runs are **合成语料 · 本机 demo** only (#735) — never present them as a customer deployment or live service

---

## 3. Interview do-not-say list (one-strike)

1. L5 / domain benchmark / registration pass / counted_as_pass=true  
2. RESULT-Y 乙, primary experiment success, near a pass, better than RARR/KPR  
3. Sprint(A) / MUM merge = statistical pass or method validated  
4. Production-team L4 / Meta E4 equivalent  
5. PMF, paying customers, SaaS ready  
6. Open `web_search` as main path / chat-primary UI already delivered

---

## 4. Interview / demo one-liner (memorize)

> Sell the T0→T1 reverify latch for voids and gaps; Reverify Sheet + HumanLatch; in-repo regressible refusal and observation hooks; primary experiment is an honest negative (RESULT-Y=丙); next is partner logs and online citation audit — not faster summaries.

Immunity oral (primary experiment):  
> Point estimate T−C≈0.0927 is still RESULT-Y=丙 because the 95% lower bound ≤0; a positive point ≠ a pass; Sprint(A) merge ≠ a pass.

---

## 5. Near-term in progress (narrative bounds)

| Item | Narrative identity |
|------|--------------------|
| E1 min-6 weekly dry-run | Observation scaffolding; write honesty when sample is thin; ≠ 乙 |
| E2 partner per-session log | Product evidence contract; ≠ synthetic customer success |
| G1 cite-emit | Engineering behavior ruler; ≠ gaming registered A1 |
| 丙-path arXiv | Protocol + negative result + reproducibility; do not submit Industry/Demo/Findings (day-19 decision: arXiv 丙 only, no Industry/Demo/Findings) |

---

## 6. Do-not-touch (forever)

floors / gold / x1 / `PRODUCTION_RETRIEVAL_MODE` / RESULT-Y·PREREG established grade; no auto-spend before paid "run"; Ronin default does not dispatch (needs "agree").
