# FreshLatch glossary (English SSOT)

This is the single English glossary SSOT; CONTEXT.md is a short pointer only.

**Claim.** A previously issued statement under reverify (e.g. pricing still holds). Avoid: “conclusion,” free-form “statement” as the product noun.

**registered dimension.** Closed six-value enum on the issuance docket (same vocabulary as focus); compared by the dimension cross-check gate (ADR-0011). Values keep English literals: `competitor_pricing` / `regulatory_stance` / `interview_reversal` / `cost_model` / `market_structure` / `tech_ecosystem`. Semantics = evidence-source type that made the claim true, not a topic tag (#31).

**T0 / T1.** T0 = issuance-time corpus snapshot; T1 = reverify-time corpus snapshot. Judgment ground truth is T1 source text.

**disposition.** Sheet-level aggregate (I-09 / #688 / #694). Closed four values — Chinese literals are code-locked and must appear verbatim: `可发（全部仍成立）` / `可发（含作废）` / `需补丁` / `勿发`. Aggregate of claim-level `fresh`/`stale`/`unknown` plus human close-out; does not rename underlying enums. Priority: open stale → 勿发; else untreated unknown/gap → 需补丁; else split the two OK-to-send rows by whether any void exists. Both OK-to-send rows export equally; 需补丁 needs explicit ack; 勿发 is deny.

**HumanLatch.** Human review workflow: void (`discard`), renew (must cite T1 evidence_id), or `disputed` (writes conclusion to latch_log; reopenable; does not change machine `Claim.status`; does not write frozen gold / floors). Agents cannot turn red back to green.

**hybrid+rerank.** Production retrieval mode: BM25+dense RRF (k=60) then local cross-encoder rerank of hybrid top-10 (`BAAI/bge-reranker-base`). BM25-only via `set_retrieval_switch("bm25")` is fallback, not default.

**PRODUCTION_RETRIEVAL_MODE.** Code constant for the production default arm; current value `hybrid+rerank`. Eval may force other arms without rewriting this constant.

**RESULT-Y / PREREG-Y.** Route Y preregistered product track after B/C 丙 archive: protocol `docs/evidence/patch-events/PREREG-Y.md`; artifacts `RESULT-Y` / `formal-generations-y`. Protocol lock ≠ activated formal main run. RESULT-Y=丙 is the established grade for the primary experiment (not 乙).

**Evidence-bound patch (attested patch).** Whole-claim text replace whose citations ⊆ this Run’s ingested T1; human confirm required; then forced single-claim re-verify. Product path is always attested (`arm=T`). Prefer this name over proof-carrying externally (ADR-0029).

**Verify+.** Pre-send product shape: Gate + T1 ingest + disposition + Evidence-bound patch + publish hook. Thin dialogue reserved, not shipped; Studio frozen. Shape: `Gate ⊂ Verify+ ⊂ Studio`.

**publish hook.** Deterministic adoption gate before export/pack: reads Run disposition and T1 checksum/`run_id` freshness; decides whether Client Memo (and same-gate exits) may leave. Hard exits this wave = Memo UI+CLI + inbound HTTP check (ADR-0031).

**claim ledger.** Read-only projection of void list (`invalidation_list`) plus HumanLatch log (`latch_log` discard/renew/disputed); beside the Reverify Sheet / Run detail; Markdown-exportable. `disputed` carries a conclusion, is reopenable, does not enter the void list, does not write frozen gold / floors. Not a second write table; not `patch_events` (ADR-0031).

See also: messaging [`docs/messaging-one-pager.md`](messaging-one-pager.md); retrieval decision [`docs/evidence/retrieval-decision.md`](evidence/retrieval-decision.md); contribution boundary [`docs/contribution-boundary.md`](contribution-boundary.md).
