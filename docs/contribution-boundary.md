# Contribution Boundary — writable claims and banned talk

> **Update (2026-10):** Rewritten after the post–Hard-Gold default-arm change. Production retrieval default is now `hybrid+rerank`.
> **Current framing:** [`docs/messaging-one-pager.md`](messaging-one-pager.md) + [`CONTEXT.md`](../CONTEXT.md) (glossary pointer) + [`docs/evidence/retrieval-decision.md`](evidence/retrieval-decision.md).
> **Scope:** Externally writable contribution boundary. Not proof that the full pre-send loop is delivered, and not a registration pass or product-ready claim.
> **Prior:** v0 (I0) pinned production default to BM25 and banned saying "dense / hybrid / rerank is already the production default." That ban does not hold after the 2026-10-07 decision and was removed from the blacklist.

---

## 1. Production retrieval (current)

- Default arm: `hybrid+rerank`. Rerank is local `BAAI/bge-reranker-base`, only reranking the hybrid top-10.
- BM25 is fallback only: `set_retrieval_switch("bm25")`. It does not change the constant `PRODUCTION_RETRIEVAL_MODE`, and it is not the production default.
- Lexical-only rerank: `set_retrieval_switch("hybrid+rerank_lexical")`.
- Missing vectors record `bm25_fallback`. Reranker failure records `last_rerank_mode=lexical_fallback`.
- Hard-Gold / #259 evidence is citable. That is not a closed statistical product pass, and not "BM25 is statistically significantly best."

Decision chain: `docs/evidence/retrieval-decision.md`. I3 skeleton spec archived: `docs/_archive/2026-10/hard-gold.md` (section 6 is the 2026-10-07 change log). Current default follows this page and the messaging one-pager.

---

## 2. Writable contributions (honest)

| Writable | Meaning |
|----------|---------|
| **Measurable retrieve subsystem** | `claim→query transform→retrieve→ordered evidence_id + retrieval_mode`; Agent is caller only and cannot pick the production arm |
| **Eval arm ≠ production arm** | Eval may force bm25 / dense / hybrid / hybrid+rerank / bm25_fallback. Production default is `hybrid+rerank`. BM25 only via `set_retrieval_switch("bm25")` fallback |
| **Honest degradation** | Vector failure → BM25 marked `bm25_fallback`; no silent empty results |

Combined claim: the retrieval subsystem is independently measurable and degradable. Since 2026-10-07 the production default is `hybrid+rerank` with local `BAAI/bge-reranker-base` (hybrid top-10 only). BM25 is fallback, not default.

Historical Phase A smoke re-run entry lives on the archive page `docs/_archive/2026-10/eval-retrieve.md`. That page records why BM25 still held then; do not read its present tense as the current default arm.

---

## 3. Banned talk (blacklist · oral and docs)

1. "We built **agentic RAG**" (explicit Phase A Out)
2. "Eval **proves** BM25 is **statistically significantly** best," or treating smoke-level ties as statistical proof for an arm change
3. "**First** evidence-bound edit" or presenting formal **proof-carrying / PCC** externally
4. "**Phase A = full pre-send loop delivered**" (pre-send loop is V1+; Evidence-bound is V1.5)
5. **SaaS / PMF / L5 / registration pass** (including `counted_as_pass=true`, domain benchmark, product ready)
6. **Open chat as formal verdict** (open `web_search` as main path, chat-primary UI delivered, dialogue changing formal verdict)

Related Work ancestors (RARR / PAVE / fact-checking, etc.) may be acknowledged. Boundary phrasing: "pre-send freshness reverify protocol." Do not cast v0 smoke as the completed full protocol, and do not describe the current default arm as BM25.

Removed old ban: "must not say dense / hybrid / rerank is already the production default." As of 2026-10 the production default is `hybrid+rerank`; that sentence may be said within §1's scope.

---

## 4. Stage landing record (smoke band · default arm at landing time)

The table below is the contribution surface each stage added. Smoke band does not report variance and is not statistical significance. Sentences that say production default was still `bm25` at landing describe that day only, not the post–2026-10-07 current default (see §1).

| Stage | Contribution surface added / already written |
|-------|-----------------------------------------------|
| V1 | Single-vertical pre-send path; T1 ingest; package disposition; `patch_events` starts |
| I1 | Failure triad + reviewable misjudgment samples (smoke-layer framing: does not report variance; not statistical significance) |
| V1.5 | Evidence-bound / attested patch (human confirm + forced re-verify); paper primary experiment |
| I2 | Security three-case reproducible demos: cross-tenant recall · indirect injection · retrieval poisoning (≠ idea #4; ADR-0030) |
| V2 | Publish hook (Memo UI+CLI + inbound check) + claim-ledger read-only projection (smoke · adoption layer; ADR-0031) |

- **V1 landed (smoke, 2026-09-29):** Pre-send loop main seam in-repo (advisor sample pack `v1-mck-soai`, allowlisted thin URL, package disposition, human review, `patch_events` starts). Evidence: `docs/evidence/v1/V1-DoD-CLOSE.md`. Band=smoke. Production default arm was still `bm25` at landing. Not Hard-Gold; not a retrieval-arm eval promotion.
- **I1 landed (smoke, 2026-09-29):** Failure triad + reviewable misjudgment samples in-repo. Short index `docs/evidence/i1/INDEX.md` at a glance: miss/false-alarm ≥3, and ≥1 `runnable=true` (gold sample `i1-s005`). Evidence: `docs/evidence/i1/ACCEPTANCE.md`. Band=smoke; does not report variance; production Gate / disposition / HumanLatch enums not extended; not Hard-Gold.
- **V1.5 landed (smoke, 2026-09-29):** Form Evidence-bound (independent `propose_patch`/`confirm_patch`, attested overwrite, single-claim re-verify, export); thin dialogue Out this wave (not implemented, not stubbed); HumanLatch `VALID_ACTIONS` not extended; no C|T switch on pre-send; Exit not hard-bound to "OK to send." Eval: `docs/_archive/2026-10/research/V1.5-Evidence-bound补丁设计评估.md`; ADR-0029; hard Exit `docs/evidence/v15/ACCEPTANCE.md`; close `docs/evidence/v15/V15-DoD-CLOSE.md`. Band=smoke. At landing: not Hard-Gold, not C vs T significance, not a default-arm change.
- **I2 landed (smoke, 2026-09-29):** Security three cases (ACL tenant filter · injection Gate refuse-green · poison metadata drop) reproducible; injection 1× Lead→Auditor smoke fail-closed; thin table `docs/security.md`. Eval: `docs/_archive/2026-10/research/I2-安全三例设计评估.md`; ADR-0030; hard Exit `docs/evidence/i2/ACCEPTANCE.md`; close `docs/evidence/i2/I2-DoD-CLOSE.md`. Band=smoke; ≠ #4; not a penetration certification, not a security pass rate, not Hard-Gold. At landing: production default arm unchanged.
- **V2 landed (smoke · adoption layer, 2026-09-30):** Publish hook (Memo UI+CLI same gate + inbound check allow/deny) + claim-ledger read-only projection (discard∪renew); zero new write tables; no Word/Notion/open webhook platform; no graph/CMS; no Memo commercial verdict; no whole-pack re-verify on the hook; Studio not unfrozen. Eval: `docs/_archive/2026-10/research/V2-发前钩子与主张台账设计评估.md`; ADR-0031; hard Exit `docs/evidence/v2/ACCEPTANCE.md`; close `docs/evidence/v2/V2-DoD-CLOSE.md`. Band=smoke · adoption layer; `curl` ≠ platform delivered; not hard-bound to "OK to send"; no adoption-rate claim; not Hard-Gold. At landing: default arm unchanged.

Full-protocol framing (only ingested T1 may decide; `web→disk→re-verify`; patches ⊆ T1; human confirm; dialogue does not change formal verdict) follows `docs/messaging-one-pager.md` and `CONTEXT.md`. Historical stage roadmap: archived `docs/_archive/2026-10/roadmap.md`.

---

## 5. Pointers

- Interview / external: [`docs/messaging-one-pager.md`](messaging-one-pager.md)
- Glossary SSOT: [`docs/glossary.md`](glossary.md) · short pointer [`CONTEXT.md`](../CONTEXT.md)
- Retrieval decision chain: [`docs/evidence/retrieval-decision.md`](evidence/retrieval-decision.md)
- Phase A smoke narrative (historical; header marks 2026-10-07 default change): [`accounting-card.md`](_archive/2026-10/accounting-card.md)
- Spec: `docs/_archive/2026-10/spec/10-PhaseA-RAG.md` (contract; not a substitute for this contribution list)
- Structure overview: [`docs/architecture/2026-10-overview.md`](architecture/2026-10-overview.md)
