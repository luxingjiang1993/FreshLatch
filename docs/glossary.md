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

## Anchors required by unit contracts (EN SSOT; Chinese lock phrases kept where tests pin them)

**V1 vertical · 顾问报告**:
Near-term sole product vertical (**近端唯一垂直** / **单一垂直**): pre-send reverify of already-issued advisor / strategy claims. Sample primary pack is public McKinsey State of AI insight excerpts (T0≈2025-03 wave / T1≈2025-11 wave); the repo keeps claims, excerpts, and citations only — do not redistribute whole consulting PDFs as open corpus (ADR-0027).
_Avoid_: parallel multi-verticals, research-report primary pack, compliance primary pack (later phase), synthetic topics presented as the chosen vertical.

**产品失败三桶**:
Audit surface labels one failure trajectory with three separate tags: empty retrieval, grade insufficient, and tool_tier_2 deny. Do not collapse them into a single "failure". Empty retrieval = retrieve returned no hits. Grade insufficient = grade incorrect with reason `grade_incorrect_exhausted`, or grade ambiguous with reason `grade_ambiguous`. tool_tier_2 deny = model called a tool_tier_2 tool and was refused with reason `tool_tier_denied`. tool_tier_0 and tool_tier_1 are not this bucket. 产品失败三桶 ≠ ops ADR-0028 评测桶 (找不到 / 找错 / 没用上; see `docs/ops/挂标-失败归因三桶.md`). Do not use these three buckets to re-label frozen gold or floors.
_Avoid_: collapsing the three buckets, using eval-bucket names as audit highlights, writing the three buckets into gold as score inflation.

**tool_tier_0**:
Tool permission tier: read and retrieve. `retrieve`, `read_source`, `list_memories`, and similar may run without approval. This tier is not HumanLatch 人审 L0 (rule-gate preamble literal; semantics unchanged).
_Avoid_: naming this tier after a human-review exit, calling read tools void-or-renew gated.

**tool_tier_1**:
Tool permission tier: write observations. Tools that change claims, gaps, or memory marks (`reverify_claim`, `mark_stale`, `mark_gap`, `flag_*`, `propose_quarantine`, …) must pass an existing HumanLatch pending-review round. Unapproved calls are refused with reason `tool_tier_denied` and leave a trajectory observation; the tool is not invoked. This tier is not HumanLatch 人审 L0.
_Avoid_: executing unapproved writes, inventing a second approval product, silent pass-through.

**tool_tier_2**:
Tool permission tier: production arms and banned calls. Model invocation is fail-closed; these tools are not on the default `LEAD_TOOLS_W3`. Even human approval cannot execute them. This tier is not HumanLatch 人审 L0.
_Avoid_: mounting into Lead default whitelist, using approval to unlock a banned tier.

**CRAG grade (retrieve grade)**:
Closed three-state on one retrieve observation: `correct` | `incorrect` | `ambiguous`. Lives on the retrieval edge; not recomputed inside the agent loop. Fixtures may inject `crag_grade` on hits; without injection the deterministic rule looks at id suffixes only: at least one `@T1` → `correct`, else `incorrect`. `ambiguous` comes only from injection and means the observation is not enough to keep writing a judgment. Not a classifier; no network; no body scoring. Compact trajectory marks: `grade=correct` / `grade=incorrect` / `grade=ambiguous`.
_Avoid_: relevance scores, LLM judge, confidence, calling two contradictory T1s ambiguous.

**verbatim 数字闸**:
Deterministic check before `reverify_claim(fresh)` lands. Extract numeric literals from the claim text (ASCII digits, optional thousands commas, decimal point, adjacent `%`, leading ASCII minus); each must appear as the same literal among numeric literals in the cited `@T1` evidence span. Claims with no numeric literal do not refuse this gate. Leading ASCII letters glued to digits (`T1`, `p1`) are not numeric literals. Ticket tolerance is empty: do not treat `12.5` as `12.50`, or `1,299` as `1299`.
_Avoid_: formula recompute, SESOI, numeric tolerance, full-width folding, model arithmetic pass.

**numeric_mismatch**:
Abstention reason code when a claim's numeric literal does not appear verbatim in the cited `@T1` evidence span. Fake quotes or rewritten numbers take this code; result must not be `fresh` (stay abstain / unknown). Not `grade_ambiguous`.
_Avoid_: model arithmetic pass, writing missing numbers as fresh, `grade_ambiguous`.

**T1 冲突闸**:
Deterministic check before `reverify_claim(fresh)` is handed to the executor. If two `@T1` spans in this turn's retrieve observation give mutually exclusive values for the same decidable premise, refuse. Decidable premises bind literally with empty tolerance: either an in-body `前提「…」：取值` form, or numeric literals (same extract rule as the verbatim numeric gate) / closed antonym pairs inside a window of the same attribute word (定价, 月费, 报价, 价格, 费用, 成本, …). Distinct named objects on both sides (竞品A vs 竞品B, Pro vs Free) are not the same premise. A span that states two numbers is not exclusive against another span that only states one of them. This gate does not pick a side or merge both into fresh.
_Avoid_: model NLI, silent merge, SESOI, calling CRAG Ambiguous this gate.

**conflicting_evidence**:
Abstention reason code when two `@T1` spans are mutually exclusive on the same decidable premise. Result must not be `fresh`. Not `grade_ambiguous` (that is "observation too thin to keep judging," with no exclusivity pair required). Not `numeric_mismatch` (that is claim digits missing from the cited span).
_Avoid_: `grade_ambiguous`, picking the smoother side as fresh, unreviewed conflict merge.

**abstention reason**:
Closed enum of refuse reasons. A trajectory event's `reason_code` counts as an abstention reason only when it is in this list. Members match already-shipped codes: `insufficient_evidence` (no citable `@T1` this turn), `cite_outside_registry` (cite not in this turn's TurnRegistry), `grade_incorrect_exhausted`, `grade_ambiguous`, `numeric_mismatch` (claim digits not verbatim in cited `@T1` span), `conflicting_evidence` (two `@T1` exclusive on one decidable premise). UI reads this list only. Free text may stay in `error` but cannot alone act as the reason.
_Avoid_: parallel spellings, treating error prose as the reason code, folding `unknown_tool` / `illegal_tool_args` / `illegal_dimension` / `NO_T1_EVIDENCE` into this enum.

**有效反证 (valid counter-evidence)**:
Critic-produced counter-evidence that meets acceptance quality: cites ≥1 clickable `t1_evidence_ids`, and the rationale text contains an explicit causal sentence (which T1 sentence overturns which claim premise). Must not be empty phrases like "conflicts with latest docs" alone, and must not rest solely on meta statements (not retested / no longer tracked). The causal sentence must anchor the claim's same premise / 度量维度 — dimension mismatch (e.g. 定价≠成本) is not valid counter-evidence. Stricter eval-mode alignment (span vs gold causal_chain) belongs in eval docs, not this definition.
_Avoid_: "strong rebuttal," "decent counter-evidence" as product nouns.

**North Star (B2 人审有效动作率).** The product's single North Star metric: share of reviewable claims on which a human reviewer records a real `discard` or `renew` (renew must cite T1 evidence) within the window; denominator = reviewable claims from `latch_log`. Cost, latency, pytest counts, and scorecard grades are guardrails, never the North Star. Ban: any composite "health score" blending RESULT-Y with human metrics into one green dot. Map: `docs/ops/metrics-map.md` (#737); source: `org-os/research/20261020-freshlatch-metrics-system.md`.

See also: messaging [`docs/messaging-one-pager.md`](messaging-one-pager.md); retrieval decision [`docs/evidence/retrieval-decision.md`](evidence/retrieval-decision.md); contribution boundary [`docs/contribution-boundary.md`](contribution-boundary.md).
