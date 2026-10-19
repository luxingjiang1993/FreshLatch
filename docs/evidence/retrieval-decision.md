# Retrieval default decision chain: switched to hybrid+rerank on 2026-10-07

This page is for papers and interviews. It records the decision chain. The 2026-10-07 switch was a human decision, not a model proxy approval.

The production default is now hybrid+rerank. The code constant `PRODUCTION_RETRIEVAL_MODE` is `hybrid+rerank`. Rerank is local `BAAI/bge-reranker-base` (fastembed `TextCrossEncoder`, CPU), only reranking hybrid's top-10. Basis: MRR@10 and nDCG@10 from [PR #293](https://github.com/luxingjiang1993/FreshLatch/pull/293); switch ticket [Issue #294](https://github.com/luxingjiang1993/FreshLatch/issues/294). One-click BM25 rollback: `set_retrieval_switch("bm25")`. Lexical-only rerank: `set_retrieval_switch("hybrid+rerank_lexical")`. Neither changes that constant. Missing vectors still record `bm25_fallback`. Reranker failure records `last_rerank_mode=lexical_fallback`. Warm embedding and reranker weights before switching; see `docs/ops/local-embed.md`. This page does not call Alibaba Cloud DashScope paid APIs. Sentences below that say "still bm25 then" or "rerank was still rerank_lexical then" are records of that day.

Four-decimal figures in tables are copied from each report's main table. Longer decimals in JSON are noted in the matching subsection; they are not re-rounded here.

English names below are used as-is (no alternate translations):

- BM25: BM25Okapi with jieba tokenization.
- dense: embed query and chunk; rank by cosine.
- hybrid: reciprocal rank fusion (RRF, constant k=60) of BM25 and dense ranks. Adds reciprocals of ranks, not a weighted product of scores.
- hybrid+rerank: hybrid first, then rerank the already-returned top-10. After the 2026-10-07 switch ticket, rerank is local `BAAI/bge-reranker-base`. `rerank_lexical` remains for the explicit switch and `lexical_fallback`.
- Recall@10: 1 if any gold-set chunk appears in the top-10, else 0; then average over questions. Not "what fraction of the gold set was recovered."
- MRR@10, nDCG@10, p95.

Goal before 2026-10-07 (user, relayed via Ronin agent): keep the rerank arm; retarget to hybrid+rerank. Rationale: real business corpora are larger and noisier, so rerank is more persuasive. That rationale was not measured on this corpus and remains a registered to-retest hypothesis. Engineering gap tracked in [Issue #286](https://github.com/luxingjiang1993/FreshLatch/issues/286), later merged. On 2026-10-07 Oriental Ronin approved these 16 rows and switched the default. Scope of that approval is those 16 rows only — not line-by-line human review of the full set.

## 1. Timeline

| Time | Event | Source |
|---|---|---|
| 2026-09-28 | BM25 smoke baseline landed: 28 files, 84 chunks, n=36, Recall@10=1.0000, MRR@10=0.7324. BM25 only; no dense. | `reports/retrieve-bm25-baseline.md` |
| 2026-09-29 | I0 acceptance re-ran the same metrics: n=36, Recall@10=1.0000, MRR@10=0.7324. | `docs/evidence/i0/ACCEPTANCE.md` |
| Phase A | Four-arm table on the same smoke set. dense embedding model `text-embedding-v4`. BM25 1.0000, dense 0.9722, hybrid 1.0000, hybrid+rerank 1.0000 (p95=11.4 ms, production default off). Kept BM25; required a separate Hard-Gold. | `reports/retrieve-arm-compare.md`, `reports/retrieve-rerank-compare.md`, `docs/_archive/2026-10/accounting-card.md` (narrative points at Phase A / PR #167) |
| 2026-10-02 | Hard-Gold skeleton merged. n=20, trap or adversarial 8 questions (40%). Acceptance asserted default arm still bm25. | [Issue #251](https://github.com/luxingjiang1993/FreshLatch/issues/251) · [PR #256](https://github.com/luxingjiang1993/FreshLatch/pull/256) · `docs/evidence/i3/ACCEPTANCE.md` |
| 2026-10-03 | Arm-change gate: only after a pass may an implementation ticket open. This round did not change the arm. | [Issue #257](https://github.com/luxingjiang1993/FreshLatch/issues/257) · `docs/adr/0033-hard-gold-过线与改臂授权闸.md` |
| 2026-10-03 | Hard-Gold same-corpus rerun passed; arm not changed. dense embedding still `text-embedding-v4` (1024-d, 94 chunks). BM25 0.6000, dense 0.6500, hybrid 0.7500, hybrid+rerank 0.7500, p95=67.3 ms, rerank gate closed. | [Issue #259](https://github.com/luxingjiang1993/FreshLatch/issues/259) · `docs/evidence/hard-gold-arm/RERUN-20261003-259.md` |
| from 2026-10-03 | Arm-change implementation ticket still awaiting human receipt. This page does not implement it. | [Issue #260](https://github.com/luxingjiang1993/FreshLatch/issues/260) |
| 2026-10-07 | RET-01.3 x1 gold set merged to main, commit `5de99c1`. Two-model labeling; Ronin agent (model) proxy review; `human_row_review=false`. | [PR #282](https://github.com/luxingjiang1993/FreshLatch/pull/282) |
| 2026-10-07 | Four-arm split on x1. dense switched to local embedding `BAAI/bge-small-zh-v1.5`. Config `text-embedding-v4` not run. Written advice discussed hybrid only; rerank preregistration gate closed. | [PR #283](https://github.com/luxingjiang1993/FreshLatch/pull/283) |
| 2026-10-07 | Pre-switch verification ticket: evaluate both hybrid and hybrid+rerank; human final receipt; do not change default. | [Issue #284](https://github.com/luxingjiang1993/FreshLatch/issues/284) |
| 2026-10-07 | Significance, cost, 656 ordered delta checklist rows, one-click BM25 smoke. Written advice: keep bm25. | [PR #285](https://github.com/luxingjiang1993/FreshLatch/pull/285) |
| 2026-10-07 | User retargeted to hybrid+rerank; fill engineering gap first. Switch still waits on human review of 16 questions. This page and that ticket only record; they do not implement. | [Issue #286](https://github.com/luxingjiang1993/FreshLatch/issues/286) |
| 2026-10-07 | Oriental Ronin approved DECISION-16's 16 rows (not full-set line-by-line human review). `s1-d0-05-q4` dropped `s1-d0-05-warn#p1@T1`. Recomputed BM25 vs hybrid from #283 saved top-10: Recall@10 still 0.9196428571428571 vs 0.9732142857142857, delta 0.05357142857142857, 95% CI 0.022321428571428572 ~ 0.08928571428571429, McNemar 2/14/204/4, p 0.004180908203124997. hybrid mean nDCG@10 moved from 0.779488160892922 to 0.7803516716233564. Switch decided by human; `PRODUCTION_RETRIEVAL_MODE` set to `hybrid+rerank`. | `docs/evidence/issue-284/DECISION-16.md` |
| 2026-10-07 | Local neural reranker offline contrast. Decision column K=10: `rerank_lexical` vs `BAAI/bge-reranker-base`. Recall@10 both 0.9732142857142857. nDCG@10 delta 0.06231550367445169, CI 0.03897278888099252 ~ 0.08564412540024816. MRR@10 delta 0.08152458900226757, CI 0.04773198341836735 ~ 0.1171530435090703. Neural p95 434.1544819999399 ms. Decision sentence: "recommend opening a separate switch ticket." Production rerank not changed then. | [Issue #292](https://github.com/luxingjiang1993/FreshLatch/issues/292) · [PR #293](https://github.com/luxingjiang1993/FreshLatch/pull/293) · `docs/evidence/neural-rerank/` |
| 2026-10-07 | Oriental Ronin decided to switch production rerank from `rerank_lexical` to local `BAAI/bge-reranker-base`. Only reranks hybrid top-10. K=30 does not enter production. `PRODUCTION_RETRIEVAL_MODE` remains `hybrid+rerank`. | [Issue #294](https://github.com/luxingjiang1993/FreshLatch/issues/294) |
| 2026-10-07 | fastembed 0.8.1 recheck. Under the same code, chunk and arm-query vectors bit-identical vs 0.7.1. Recall@10, MRR@10, nDCG@10, McNemar discordants match post–gold-revision #285 and #293 K=10. p95 is a new single-run timing. No production code change; no gold change. | `docs/evidence/fastembed-081-recheck/` |

## 2. Smoke set of 36: not all three arms at ceiling

One claim is: BM25, dense, and hybrid all have Recall@10 = 1.0, so no difference is visible, hence keep BM25. The in-repo original table is not that.

`docs/_archive/2026-10/accounting-card.md` labels this table demo / smoke (n=36), reports no variance, and claims no statistical significance. Numbers from `reports/retrieve-arm-compare.md` and `reports/retrieve-rerank-compare.md`:

| Arm | Recall@10 | Report judgment |
|---|---:|---|
| BM25 (A0) | 1.0000 | Pass vs A0; expired-claim replay pass |
| dense | 0.9722 | Below BM25 |
| hybrid (RRF k=60) | 1.0000 | Not below the worse of BM25 and dense; pass-line pass |
| hybrid+rerank | 1.0000 | Not strictly better than hybrid; p95=11.4 ms; production default off |

dense is 0.9722 — not ceiling. BM25 was already at ceiling; hybrid only tied; rerank was not strictly better than hybrid. The preregistered gate required rerank Recall@10 strictly above hybrid **and** p95 ≤ 800 ms before considering rerank as default. Both were not met, so default could not change. hybrid tying BM25 was also not enough to switch arms; a separate Hard-Gold was required. That is the origin of [Issue #251](https://github.com/luxingjiang1993/FreshLatch/issues/251).

This dense run used embedding `text-embedding-v4` (`reports/retrieve-arm-compare.md` states "model: text-embedding-v4"). The rerank compare page states: comparison arm is local lexical overlap rerank, not bge, and not score-weighted. Corpus: 28 files, 84 chunks; baseline report date 2026-09-28. Do not treat this table and later x1 local 512-d embeddings as the same measurement.

`docs/evidence/i0/ACCEPTANCE.md` on 2026-09-29 re-ran BM25 alone: n=36, Recall@10=1.0000, MRR@10=0.7324. That page has no dense 0.9722.

## 3. Hard-Gold small set

The 2026-10-02 skeleton ([PR #256](https://github.com/luxingjiang1993/FreshLatch/pull/256)) split Hard-Gold into its own file: n=20, trap or adversarial 8 questions, 40%. Acceptance asserted default arm still bm25.

The 2026-10-03 same-corpus rerun ([Issue #259](https://github.com/luxingjiang1993/FreshLatch/issues/259)) separated the scores and still did not change the arm:

- BM25 Recall@10 = 0.6000, same as A0
- dense = 0.6500
- hybrid = 0.7500, not below min(0.6000, 0.6500), pass-line pass
- hybrid+rerank = 0.7500, p95 = 67.3 ms, judgment: production default off

This dense index was rebuilt with `scripts/build_dense_index.py`; embedding still `text-embedding-v4`, dimension 1024, chunk count 94 (body 84, traps 10). It is not the same embedding as the next section's `BAAI/bge-small-zh-v1.5` (512-d); the two Recall@10 figures must not be cross-compared.

Written meaning of the pass: an arm-change implementation ticket may be opened for discussion. Production default remained bm25 until a human received that ticket. [Issue #260](https://github.com/luxingjiang1993/FreshLatch/issues/260) was still `ready-for-human` when this page was written.

## 4. RET-01.3 gold set (PR #282)

Merged at commit `5de99c1`. Question set `data/exp/x1/questions.json` has 267 questions. Primary denominator is scoring arm `score_role=arm`, 224 questions. Guardrail questions: 43; they do not enter Recall@10, MRR, nDCG@10, or McNemar.

qtype full-set: lexical 66, paraphrase 156, multi_hop 45. On the scoring arm: 60 / 119 / 45; the extra lexical and paraphrase rows sit in the guardrail. category full-set: ordinary hard 153, trap 114, no adversarial. On the scoring arm: hard 153, trap 71. All 43 guardrail questions are trap. Chunks: 794.

`questions.json` meta: `human_row_review` false; reviewer text "Ronin agent (model), delegated by owner." Category rule category-rule-v2; qtype rule qtype-kw-v1.

Labeling protocol: `data/exp/x1/LABELING-PROVENANCE.json` and `data/exp/x1/ret013-draft/PROTOCOL.md`. Original 211 questions labeled by two models independently. A = assistant draft. B = Cursor cloud agent (GPT-5.6 Sol), labeled without seeing A. Score-affecting disagreements, ~20% of agreeing questions sampled by seed 20261007 (9 questions), and 12 content corrections were reviewed by the Ronin agent (model) under delegation. Remaining disagreements merged by fixed rules. This is not human line-by-line review.

Agreement on the original 211 (`PROTOCOL.md`):

- qtype agree 141/211, κ=0.44
- scoring-arm / guardrail agree 193/211, κ=0.73
- evidence chunk exact agree 141/211, mean Jaccard 0.835
- key-point equivalence 102/211
- category agree 136/211, κ=0.32
- disagree 165, agree 46

### Synthetic template traps, 47 questions as a separate column

`data/exp/x1/SOURCES.md` and `ret013-draft/round4/summary.md`: part two is 16 batches of one template. Each batch: two materials (old framing vs current framing), three questions each, 48 questions. Intersection with the formal set is 47. Missing: `r4n-s2-d0-t1-91-qc`. Blind-label reject reason: question asks for a mean; corpus only has median 11 minutes. These 47 still count in total and trap scores, and are also listed separately so the template does not inflate or deflate the overall score.

Supplement batch `r4n-s6-d2-t1-91` has 3 questions. `labels-supplement.json` states `blind_second_label` false; no second independent A draft. These 3 are not in the 47.

### 100% blind-label agreement is a suspicion point

Round-4 contrast of 54 questions: `data/exp/x1/ret013-draft/round4/blind-b/compare-b.json`. Row counts (n=54):

- evidence chunk equal: 54/54
- category equal: 54/54
- trap subtype equal: 54/54
- qtype equal: 44/54
- key points equal: 44/54
- decisions: accept 53, reject 1 (`r4n-s2-d0-t1-91-qc`)

Evidence, category, and trap subtype are 100% aligned. qtype and key points are not. The rejected question still had aligned evidence; reject reason was answer ambiguity, not different chunks.

This 100% must not be treated as labeling-quality proof:

- Both draft and blind label are Ronin agent (model). In `LABELING-PROVENANCE.json`, round-4 A and blind B share that identity. Blind notes say this session saw the question and corpus first, then compared to A. That is not the same independence as the original 211's GPT-5.6 Sol that never saw A.
- `round4/summary.md` already flags risk: 16 batches are all "two materials plus three questions" with similar ask patterns.
- Merge rule: "accept when evidence and category agree." On template questions, 100% agreement becomes accept immediately. Provenance states round-4 new questions do not draw another 20% sample.

So this gold set may serve as a fixed denominator for internal arm comparison. It is not a human gold set. Round-4 100% field agreement is not inter-annotator reliability.

## 5. PR #283 split results

Source: [PR #283](https://github.com/luxingjiang1993/FreshLatch/pull/283) `docs/evidence/x1-retrieval-modes/RESULT.md`. Layer: experiment / smoke, single run, no variance reported. p95 from single timing; re-runs will jitter by milliseconds. Query embedding computed before timing; p95 excludes model load and network embedding.

Local dense embedding: fastembed `BAAI/bge-small-zh-v1.5`, 512-d. #283 RESULT names the library fastembed only, no version. Version 0.7.1 is in #285 `summary.json` (`fastembed_version`).

Config `data/exp/x1/config.json` says `text-embedding-v4`, 1024-d. That path was not run. Reason in #283 RESULT: that path only requests DashScope in `embeddings.py`; this measurement forbids paid APIs. `embeddings.py` targets DashScope compatible mode; without a key it fails hard and does not fall back to local embedding. So x1 dense scores are not `text-embedding-v4` scores and must not be cross-compared with the prior section's 1024-d Hard-Gold dense scores.

| Slice | n | bm25 Recall@10 | bm25 MRR@10 | bm25 p95_ms | dense Recall@10 | dense MRR@10 | dense p95_ms | hybrid Recall@10 | hybrid MRR@10 | hybrid p95_ms | hybrid+rerank Recall@10 | hybrid+rerank MRR@10 | hybrid+rerank p95_ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| overall | 224 | 0.9196 | 0.7275 | 72.335 | 0.9330 | 0.7601 | 14.594 | 0.9732 | 0.7740 | 84.914 | 0.9732 | 0.7567 | 87.253 |
| lexical | 60 | 1.0000 | 0.9792 | 76.407 | 0.9667 | 0.9281 | 14.644 | 0.9833 | 0.9528 | 84.212 | 0.9833 | 0.9639 | 86.842 |
| paraphrase | 119 | 0.8739 | 0.6455 | 72.335 | 0.8992 | 0.7014 | 14.811 | 0.9580 | 0.7195 | 85.742 | 0.9580 | 0.6795 | 92.001 |
| multi_hop | 45 | 0.9333 | 0.6089 | 68.971 | 0.9778 | 0.6915 | 14.255 | 1.0000 | 0.6798 | 83.496 | 1.0000 | 0.6845 | 83.553 |
| hard | 153 | 0.9216 | 0.7421 | 69.486 | 0.9150 | 0.7459 | 14.466 | 0.9673 | 0.7867 | 83.027 | 0.9673 | 0.7701 | 87.253 |
| trap | 71 | 0.9155 | 0.6962 | 79.295 | 0.9718 | 0.7908 | 15.156 | 0.9859 | 0.7465 | 87.745 | 0.9859 | 0.7277 | 88.335 |
| adversarial | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| synthetic template traps 47 | 47 | 0.9787 | 0.8000 | 81.337 | 1.0000 | 0.8754 | 17.391 | 0.9787 | 0.8440 | 87.745 | 0.9787 | 0.8170 | 92.001 |

Overall Recall@10 deltas vs BM25: dense +0.0134 (p95 14.594), hybrid +0.0536 (p95 84.914), hybrid+rerank +0.0536 (p95 87.253). All three arms' p95 below 800 ms. Under "Recall@10 strictly above BM25 and p95≤800 ms," all three pass that line. #283 still advised discussing hybrid only: on lexical, dense 0.9667 and hybrid 0.9833 are both below BM25's 1.0000; on ordinary hard, dense 0.9150 is below BM25's 0.9216. On template 47, hybrid and BM25 both 0.9787; dense is 1.0000.

Rerank gate vs hybrid: both Recall@10 0.9732, rerank p95 87.253, judgment "production default off." Gate requires Recall@10 strictly above hybrid. `rerank_lexical` only reranks the hybrid top-10; any-hit Recall@10 cannot rise under this implementation.

`summary.json` check_x1: exit 0, `trap_adversarial_ratio` 0.3169642857142857, `synthetic_ratio` 0.8299748110831234, `public_ratio` 0.17002518891687657, decontamination hits 0, license violations 0, longest-common-substring flags 0.

#283 written advice is measurement advice: put only hybrid on the discussion ticket; do not open a separate switch ticket for rerank. It is not authorization to change the default.

## 6. PR #285 significance, cost, and fallback

Source: [PR #285](https://github.com/luxingjiang1993/FreshLatch/pull/285) `docs/evidence/issue-284/RESULT.md`. Method locked before running: bootstrap 10000, seed 20261007, paired delta is right minus left, 95% CI via linear-interpolation percentiles. Order: three Recall@10 pairs, then two rerank MRR pairs, then two rerank nDCG@10 pairs. McNemar on Recall@10 hit/miss, exact binomial, two-sided.

Four-decimal figures below are RESULT.md's main table. Raw values in `significance.json` are longer — e.g. BM25 Recall@10 0.9196428571428571, hybrid Recall@10 0.9732142857142857, delta 0.05357142857142857, McNemar two-sided p 0.004180908203124997. Main table writes 0.9196, 0.9732, +0.0536, 0.004181. Same meaning, different precision. #285 p95 and #283 p95 are not the same timing run; do not merge millisecond columns into one table.

| Pair | Recall@10 left | Recall@10 right | Delta | 95% CI | Left-only hit | Right-only hit | Both hit | Both miss | McNemar p |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| BM25 vs hybrid | 0.9196 | 0.9732 | +0.0536 | +0.0223 ~ +0.0893 | 2 | 14 | 204 | 4 | 0.004181 |
| BM25 vs rerank | 0.9196 | 0.9732 | +0.0536 | +0.0223 ~ +0.0893 | 2 | 14 | 204 | 4 | 0.004181 |
| hybrid vs rerank | 0.9732 | 0.9732 | +0.0000 | +0.0000 ~ +0.0000 | 0 | 0 | 218 | 6 | 1.000000 |

| Pair | Metric | Left | Right | Delta | 95% CI |
|---|---|---:|---:|---:|---|
| BM25 vs rerank | MRR | 0.7275 | 0.7567 | +0.0291 | +0.0045 ~ +0.0538 |
| BM25 vs rerank | nDCG@10 | 0.7268 | 0.7618 | +0.0350 | +0.0140 ~ +0.0561 |
| hybrid vs rerank | MRR | 0.7740 | 0.7567 | -0.0173 | -0.0420 ~ +0.0062 |
| hybrid vs rerank | nDCG@10 | 0.7795 | 0.7618 | -0.0177 | -0.0348 ~ -0.0014 |

Cost (RESULT.md; raw seconds in `cost.json`):

- Model load: reported 0.543 s (`model_load_s` 0.5430166969999846). Weights already locally cached; excludes first download.
- Corpus embedding: reported 5.728 s (`index_build_s` 5.728331330000174), 794 chunks, 512-d, embedding blob 1626112 bytes.
- Query embedding: reported 0.571 s (`query_embed_s` 0.5705401449999954), 224 queries. p95 excludes this and model load.
- Memory: RSS before build 124908 KiB, after 633324 KiB, process peak 643680 KiB.
- Query p95: hybrid 82.543 ms, rerank 90.681 ms, BM25 69.783 ms. Gate 800 ms. Raw `cost.json` `p95_ms`: BM25 69.78307600002154, hybrid 82.5428959999499, rerank 90.68060099980357.
- fastembed 0.7.1 was not yet in `requirements.txt`. RESULT lists package names: huggingface-hub, loguru, mmh3, numpy, onnxruntime, pillow, py-rust-stemmers, requests, tokenizers, tqdm. Version ranges in `cost.json` `fastembed_requires`; this page does not collapse them to a single version.

BM25 rollback smoke used eval mode. At end, production default was still bm25.

- Request hybrid → recorded hybrid, 10 hits.
- Request hybrid+rerank → recorded hybrid+rerank, 10 hits.
- Request BM25 → recorded bm25, 10 hits.
- Online mode rejects forced arm change; exception text "production path cannot force retrieval_mode"; actual retrieval still bm25.
- Clear one same-snapshot chunk embedding, then request hybrid → recorded `bm25_fallback`. After rewriting the embedding, hybrid restores.

Checklist: that PR's `docs/evidence/issue-284/CHECKLIST.md`. Delta definition = evidence-id set or order differs in top-10, so row count far exceeds the 16 Recall@10 disagree questions. Checklist drafted by a model under fixed rules; not yet human-reviewed row by row. Suggested counts:

- BM25 vs hybrid: 224 questions. Keep bm25 172, discuss hybrid 48, discuss hybrid+rerank 0, need question fix 4.
- BM25 vs rerank: 224. Keep bm25 172, discuss hybrid 0, discuss hybrid+rerank 48, need question fix 4.
- hybrid vs rerank: 208. Keep bm25 149, discuss hybrid 36, discuss hybrid+rerank 19, need question fix 4.

224 + 224 + 208 = 656. The discussable 48 includes "both hit, but one ranks the gold set earlier" — not the same as the 16 Recall@10 delta questions in §9.

#285 one-line advice: keep bm25. The user afterward retargeted to hybrid+rerank. That advice is no longer the final product decision. Human review and the engineering gap were not cancelled by the retarget.

## 7. Why not switch immediately then, and what #286 had to fill

Four items were still open before the switch.

1. No human review yet. Gold set is not human line-by-line. The 656 suggestions were model-drafted. Final receipt was the 16 Recall@10 delta questions — not done yet.
2. Gaps went through significance first, rather than changing default on seeing +0.0536. Afterward, BM25 vs hybrid Recall@10 CI was +0.0223 to +0.0893, not crossing 0; McNemar p main-table value 0.004181. That only says, on these 224 questions and this fixed ranking, hybrid any-hit beats BM25. It does not replace human review or prove switching the default is safe. hybrid vs rerank Recall@10 CI is +0.0000 to +0.0000.
3. There is cost. Embeddings must be computed; process peak 643680 KiB; fastembed not yet a production dependency. p95 still below 800 ms, so latency alone was not a veto.
4. Ingest and patch did not yet write embeddings. `parse_document_text` builds chunks without `vec` (default empty). `confirm_paste` calls `add_document` directly after confirm. `add_document` uses `INSERT OR REPLACE` and writes chunk `vec` as-is; empty embeddings overwrite old embeddings. `add_invalidation` only records claim ids; it does not change chunk embeddings. `rank_dense` returns empty if any pool chunk lacks an embedding or has a wrong dimension; callers record that retrieve as `bm25_fallback` and do not label it hybrid. #285 smoke cleared one chunk embedding, requested hybrid, and recorded `bm25_fallback`.

[Issue #286](https://github.com/luxingjiang1993/FreshLatch/issues/286) only fills this gap; it does not implement the switch and does not change `PRODUCTION_RETRIEVAL_MODE`:

- Ingest, patch, and invalidation paths write embeddings in sync so the whole pool does not fall to `bm25_fallback`. Missing embeddings must still record `bm25_fallback`; degraded results must not be labeled hybrid.
- Put fastembed and `BAAI/bge-small-zh-v1.5` (512-d) into production dependencies. Rerank in use then was `rerank_lexical`, needing only jieba already in `requirements.txt`. No new neural rerank package; do not add an unevaluated bge-reranker to dependencies.
- Keep one-click BM25: eval mode `arm_eval_retrieval_mode("bm25")`. Online mode still rejects forced arm change.

Switch is not in #286. Human final receipt after reviewing the 16 questions is separate.

## 8. On this corpus rerank had no Recall@10 gain — and why the arm stayed

`rerank_lexical` (`src/freshlatch/store/pipeline.py`) comment: local lexical-overlap rerank on existing candidates; not bge; not score-weighted. Implementation: jieba.lcut on query and chunk; more overlap sorts earlier; ties keep hybrid order. `rank-bm25` is only for the BM25 arm's BM25Okapi; rerank does not call it. There is no rerank model here.

The hybrid arm does RRF over the full pool, then truncates to top-10. Rerank only permutes those 10 (`InMemoryStore` calls `rerank_lexical` on the fused result in the `hybrid+rerank` branch). A gold-set relevant chunk is either already in those 10 or not. Any-hit Recall@10 therefore cannot rise. hybrid vs rerank Recall@10 delta +0.0000 and discordants 0 vs 0 are this implementation's result, not sampling luck. On ranking, rerank vs hybrid nDCG@10 delta is -0.0177, CI -0.0348 to -0.0014, entirely below 0. MRR delta -0.0173, CI crosses 0.

This corpus also makes Recall@10 differences hard for this rerank to show:

- hybrid scoring-arm Recall@10 is already 0.9732. Both hybrid and rerank miss on 6 questions.
- 794 chunks; `synthetic_ratio` 0.8299748110831234 — mostly synthetic drafts, not open-domain noise piles.
- Traps operationalized per category-rule-v2 (`SOURCES.md`): snapshot supersession, conflicting statements in the same snapshot, meta-statements (not remeasured, no new data, pending publish, not booked, no longer tracked). Questions ask which version still counts. Old and new framings often share vocabulary; token overlap cannot separate which chunk is current.

The reason to keep the rerank arm can only be written as a hypothesis: on larger, noisier business corpora, reordering chunks already in the top-10 may be more persuasive to readers. This experiment did not prove it. Retest needs a larger corpus and whether ranking holds up. Flat Recall@10 here is because rerank only saw the top-10. Even if a later ticket swaps in a cross-encoder, as long as it still only sees those 10, any-hit Recall@10 still will not rise. §12's local cross-encoder contrast measured that: at K=10 both sides' Recall@10 remain 0.9732142857142857. Ranking metrics differ; decision sentence was "recommend opening a separate switch ticket"; the production constant did not change again from that alone. Flat Recall@10 in #283 and #285 neither proves rerank already won nor that rerank should be deleted.

User decision: keep the arm; target hybrid+rerank. #285 stats and engineering did not support an immediate default change. After the retarget, what was still missing was human review of 16 questions and #286's write-embedding paths. When this section was first written the production constant had not changed. After the 2026-10-07 human decision, the constant is `hybrid+rerank` — see §9.

## 9. The 16 questions a human reviewed

These 16 come from the BM25 vs hybrid section of the #285 checklist, reason "gold-set chunk in one arm's top-10 but not the other's." They correspond to McNemar's 2 and 14. BM25 vs rerank Recall@10 deltas share the same id set because rerank does not change that top-10 id set. Stems and three-arm top-10s are in PR #285 `CHECKLIST.md`; this page does not re-paste them. Checklist body: `docs/evidence/issue-284/DECISION-16.md`.

On 2026-10-07 Oriental Ronin agreed all 16. This is not full-set line-by-line human review. Four discussable: `s4-d0-t0-01-q6` counted as any-hit with a note that the metric is loose for multi-evidence questions; `s1-d0-05-q4` dropped `s1-d0-05-warn#p1@T1` from gold, keeping only `#p3@T1`; `s5-d0-t0-01-q3` kept both spans; `r4n-s6-d2-t1-91-qc` gold unchanged (meta-statement trap).

Recomputed BM25 vs hybrid with updated gold and #283 saved top-10 (bootstrap 10000, seed 20261007, no re-embedding, no mixed p95). Recall CI shares #285 first-pair rng start. MRR and nDCG each restart a bootstrap from seed 20261007. Recall@10, MRR, McNemar match the prior section's old gold: 0.9196428571428571 vs 0.9732142857142857, delta 0.05357142857142857, CI 0.022321428571428572 ~ 0.08928571428571429, counts 2/14/204/4, p 0.004180908203124997. MRR 0.7275333049886621 vs 0.7739937641723357, delta 0.04646045918367347, CI 0.02168358489229025 ~ 0.07260558390022674. hybrid mean nDCG@10 moved from 0.779488160892922 to 0.7803516716233564; delta from 0.05272092221584028 to 0.053584432946274525; CI from 0.0313816646625036 ~ 0.07433630682179838 to 0.03201358973245737 ~ 0.07548337519518822. BM25 mean nDCG@10 still 0.7267672386770819. Only `s1-d0-05-q4` changed: one fewer ideal relevant chunk; hybrid rank-3 is still the remaining `#p3@T1`.

Switch decided by human. Production default is now `hybrid+rerank`.

BM25-only hits (2): `p1-lx-06-new`, `s4-d0-t0-01-q6`.

hybrid / rerank-only hits (14): `s1-d0-04-q3`, `s1-d0-05-q4`, `s1-d2-01-q1`, `s2-d0-04-q2`, `s2-d1-01-q3`, `s3-d1-01-q1`, `s4-d0-t1-02-q4`, `s4-d2-t1-04-q1`, `s5-d0-t0-01-q3`, `s5-d0-t0-01-q5`, `s6-d0-t1-03-q3`, `r4m-s5-d3-t1-05-q4`, `r4m-s5-d3-t1-05-q5`, `r4n-s6-d2-t1-91-qc`.

`r4n-s6-d2-t1-91-qc` is in the supplement batch, not in the synthetic template trap 47, and has no second independent blind label.

## 10. Interview oral (~1 minute)

Production default is now hybrid+rerank; the switch was a human decision on 2026-10-07. On the 36-question smoke, BM25 and hybrid Recall@10 were both 1.0; dense was 0.9722 — not all at ceiling. That dense embedding was text-embedding-v4, so BM25 was kept and Hard-Gold came first. Later on 224 scoring questions, hybrid was 0.9732 vs BM25 0.9196, delta +0.0536, CI +0.0223 to +0.0893. After dropping one gold chunk on `s1-d0-05-q4`, that Recall@10 pair was unchanged. Rerank then loaded no model; it only reordered hybrid's top-10 by jieba token overlap, so Recall@10 matched hybrid. This corpus has 794 chunks, synthetic share ~0.83; traps mostly ask which version still counts. On larger, noisier business corpora rerank may help more — not measured here. Gold set is still model-labeled; a human only approved these 16 rows, not line-by-line full-set review. One-click rollback: `set_retrieval_switch("bm25")`. Missing vectors: `bm25_fallback`. After switch, warm `BAAI/bge-small-zh-v1.5` and `BAAI/bge-reranker-base` first. §12 is contrast; §13 is the subsequent switch: production rerank is already `BAAI/bge-reranker-base`, top-10 only. Gold framing unchanged; human review covered only DECISION-16's 16 questions.

## 11. Paper-usable methods and limitations

Methods. Compare four retrieval arms under a fixed gold set and fixed snapshot filter. BM25 arm: BM25Okapi plus jieba. x1 dense arm: local fastembed 0.7.1 `BAAI/bge-small-zh-v1.5`, 512-d cosine. Config DashScope text-embedding-v4 (1024-d) was not called because `embeddings.py` only requests that paid API. hybrid arm merges ranks with reciprocal rank fusion (k=60), not score weighting. hybrid+rerank called `rerank_lexical`, only reranking the hybrid arm's already-returned top-10 by jieba token-overlap count, loading no rerank model. Primary metric: scoring-arm (n=224) Recall@10 — 1 if any relevant chunk appears in top-10, then macro-average. Ranking metrics: MRR@10 and binary-relevance nDCG@10 (ideal ranking puts gold-set relevant chunks first). Significance: paired bootstrap 10000, seed 20261007, 95% percentile CI of paired deltas, plus exact two-sided McNemar on Recall@10 hits. Latency: single-run p95, gate 800 ms, excluding model load and query-embedding precompute. Synthetic template traps 47 listed separately, not removed from the denominator. Early smoke (n=36) and Hard-Gold (n=20) dense arms used text-embedding-v4; report separately from x1's local embedding.

Limitations. Gold set labeled by two models; review by Ronin agent (model) under delegation; `human_row_review=false` — not a human line-by-line gold set. Original 211 evidence exact agree only 141/211. Round-4 54 new questions: same model session drafted then blind-labeled; evidence/category/trap subtype 54/54 agree, of which 48 share one template; qtype aligned only 44/54. That agreement is not independent labeling reliability. Corpus 794 chunks, synthetic share 0.8299748110831234. hybrid arm Recall@10 0.9732. Any-hit Recall@10 is insensitive to lexical overlap that only reorders an existing top-10; flat Recall@10 is a mechanism result. Implementation counts token overlap; loads no rerank model. Traps operationalized as snapshot supersession, same-snapshot conflict, and meta-statements — testing freshness/version, not open-domain relevance noise unrelated by wording. Therefore "rerank is more persuasive on large corpora" is only a to-retest hypothesis; it cannot be extrapolated from this table. p95 is single-run timing. After #286, ingest can write local embeddings; when usable vectors are missing the whole retrieve still records `bm25_fallback`. After the 2026-10-07 human decision, production default is written `hybrid+rerank`. That decision is not full-set line-by-line human review. Post–gold-revision BM25 vs hybrid Recall@10 matches #285 old gold; nDCG@10 has the small change tabulated above. New p95 was not remeasured; do not mix with #283/#285 milliseconds.

## 12. Neural reranker contrast

Source: [Issue #292](https://github.com/luxingjiang1993/FreshLatch/issues/292). Numbers in `docs/evidence/neural-rerank/RESULT.md`; per-query in `per-query.json`; cost in `cost.json`. Framing locked into `PREREG.md` before running; that page was not edited after. This experiment does not change `PRODUCTION_RETRIEVAL_MODE`. Neural reranker is not added to `requirements.txt`. Eval dependency: `requirements-eval-neural-rerank.txt` (fastembed==0.8.1, providing `TextCrossEncoder`). Production interpreter still fastembed 0.7.1. This run's scores used `pip install --target /tmp/nr-packages` then that directory on `PYTHONPATH` because the environment lacked `python3-venv`. Hybrid candidate dump used system fastembed 0.7.1 to avoid drifting from production embeddings. No DashScope; no secrets committed.

Object: x1 scoring arm n=224, gold commit `50adc3251737c318815105b3562a823198b80dc3`. Left arm: `rerank_lexical`. Right arm: local `BAAI/bge-reranker-base`, fastembed `TextCrossEncoder`, CPU, `cuda=False`. Decision column reorders hybrid's top-10. K=30 then take top-10 reported separately; does not change the decision sentence. `BAAI/bge-reranker-v2-m3` not run: fastembed 0.8.1 `TextCrossEncoder` support list lacks it; sentence-transformers / torch not installed separately.

Gold remains two-model labeling plus Ronin agent (model) proxy review; `human_row_review=false`. Human review covers only DECISION-16's 16 questions.

### K=10 (decision column)

Both sides are permutations of the same id set. Per-query id-set disagreements: 0. Identical Recall@10 is a mechanism result. Bootstrap 10000, seed 20261007. This column shares one `random.Random(20261007)`; order Recall, MRR, nDCG.

| Metric | lexical | neural | Delta (neural − lexical) | 95% CI |
|---|---:|---:|---:|---|
| Recall@10 | 0.9732142857142857 | 0.9732142857142857 | 0.0 | 0.0 ~ 0.0 |
| MRR@10 | 0.7566609977324263 | 0.8381855867346939 | 0.08152458900226757 | 0.04773198341836735 ~ 0.1171530435090703 |
| nDCG@10 | 0.7626148790864964 | 0.8249303827609481 | 0.06231550367445169 | 0.03897278888099252 ~ 0.08564412540024816 |

McNemar: lexical-only 0, neural-only 0, both hit 218, both miss 6, p=1.0.

p95 via `retrieve_eval._p95_ms`; samples are only rerank `perf_counter` seconds. lexical 3.2369630007451633 ms, neural 434.1544819999399 ms. Gate 800 ms. Excludes hybrid retrieve and model load. Do not merge this p95 with #283/#285 retrieve p95 into one table.

Per-query MRR@10: neural higher 50, lexical higher 18, tie 156. Per-query nDCG@10: neural higher 68, lexical higher 25, tie 131. Counts on `per-query.json`, not another significance test.

### K=30 take top-10 (add-on report; does not change decision sentence)

K=30 starts a separate rng also seeded 20261007.

| Metric | lexical | neural | Delta | 95% CI |
|---|---:|---:|---:|---|
| Recall@10 | 0.9241071428571429 | 0.9642857142857143 | 0.04017857142857143 | 0.008928571428571428 ~ 0.07589285714285714 |
| MRR@10 | 0.7313704648526077 | 0.8244012188208617 | 0.09303075396825397 | 0.05491939484126986 ~ 0.13284044607426304 |
| nDCG@10 | 0.7262063344259618 | 0.8196633432010152 | 0.09345700877505328 | 0.06327128241344875 ~ 0.12327151337108666 |

McNemar: lexical-only 3, neural-only 12, both hit 204, both miss 5, p=0.03515625000000005.

p95: lexical 7.125296000594972 ms, neural 1371.0923300004652 ms. Neural column exceeds 800 ms. Expanding to 30 then cutting back to 10: lexical Recall@10 0.9241071428571429, neural 0.9642857142857143 — both below the decision-column shared 0.9732142857142857. The extra 20 can crowd out chunks that already hit in the original top-10.

### Cost

- First load (construct `TextCrossEncoder` plus first `rerank` return) 8.242696646000695 s. Not folded into p95.
- Weights deduped by inode: 1129561896 bytes. Of that, `onnx/model.onnx` is 1112459588 bytes. Summing by path double-counts the same cache root and HF snapshot symlinks.
- Extra deps only in `requirements-eval-neural-rerank.txt`. pytest does not download these weights; related tests use pure functions and do not construct `TextCrossEncoder`.

### Decision

Locked before running: look only at K=10, `BAAI/bge-reranker-base`. All four must hold to write "recommend opening a separate switch ticket": nDCG@10 paired-delta 95% CI lower bound > 0, point estimate ≥ 0.01, MRR@10 CI lower bound > 0, neural rerank p95 ≤ 800 ms. All four held this round. Decision sentence: recommend opening a separate switch ticket.

When #293 was written that sentence was not a switch. Then `PRODUCTION_RETRIEVAL_MODE` was still `hybrid+rerank` implemented as `rerank_lexical`. K=30 neural p95 exceeded 800 ms; a switch ticket that enlarges candidates from 10 to 30 cannot treat that column as latency already passing. No v2-m3 numbers. Oriental Ronin later opened a switch ticket on that sentence; production rerank has changed — see §13. K=30 still does not enter production.

### Interview talk track

Production default was still hybrid plus lexical rerank; this section did not change the constant. On n=224, gold `50adc32`, the same hybrid top-10 went to local `BAAI/bge-reranker-base`. Recall@10 both 0.9732142857142857 because the set did not change. MRR@10 from 0.7566609977324263 to 0.8381855867346939, delta 0.08152458900226757, CI 0.04773198341836735 ~ 0.1171530435090703. nDCG@10 from 0.7626148790864964 to 0.8249303827609481, delta 0.06231550367445169, CI 0.03897278888099252 ~ 0.08564412540024816. CPU rerank p95 434.1544819999399 ms, gate 800 ms. All four pre-locked lines passed, so the write-up says "recommend opening a separate switch ticket," not switch in this ticket. K=30-then-top-10 neural p95 1371.0923300004652 ms exceeds the gate, and that column's Recall@10 is below top-10-only. v2-m3 not run. Weights inode-deduped 1129561896 bytes; first load 8.242696646000695 s. Deps in the eval file; production still fastembed 0.7.1. Gold still two-model plus proxy review; human reviewed only DECISION-16's 16.

## 13. Production rerank switched to BAAI/bge-reranker-base

After #293 merged to main (`bfd4838`), Oriental Ronin decided to switch. Switch ticket: [Issue #294](https://github.com/luxingjiang1993/FreshLatch/issues/294). `PRODUCTION_RETRIEVAL_MODE` remains `hybrid+rerank`. What changed is this arm's rerank: local `BAAI/bge-reranker-base`, fastembed `TextCrossEncoder`, CPU, `cuda=False`. Only hybrid's top-10 enter the cross-encoder. K=30 neural p95 1371.0923300004652 ms exceeds 800 ms; production does not adopt it.

Basis: #293 decision column (n=224, gold `50adc3251737c318815105b3562a823198b80dc3`, bootstrap 10000, seed 20261007). MRR@10 from 0.7566609977324263 to 0.8381855867346939, delta 0.08152458900226757, CI 0.04773198341836735 ~ 0.1171530435090703. nDCG@10 from 0.7626148790864964 to 0.8249303827609481, delta 0.06231550367445169, CI 0.03897278888099252 ~ 0.08564412540024816. Recall@10 both 0.9732142857142857. Neural rerank p95 434.1544819999399 ms. First load 8.242696646000695 s. Weights inode-deduped 1129561896 bytes.

Gold framing unchanged. Gold remains two-model labeling plus Ronin agent (model) proxy review. Human review covers only DECISION-16's 16 questions.

Dependency pinned in `requirements.txt` as `fastembed==0.8.1`. `0.7.1` has no `TextCrossEncoder`. Embedding model id remains `BAAI/bge-small-zh-v1.5`. Warm-up script downloads both weight sets; cache dir `FASTEMBED_CACHE_PATH`. fastembed 0.8.1 vs 0.7.1 embedding recheck: §14.

On missing weights or inference error: warn, fall back to `rerank_lexical`, `last_rerank_mode=lexical_fallback`. Retrieval arm still records `hybrid+rerank`. Explicit lexical-only: `set_retrieval_switch("hybrid+rerank_lexical")`, `rerank_mode=lexical`. One-click BM25 remains `set_retrieval_switch("bm25")`.

### Interview talk track

The production arm name is still hybrid+rerank; rerank is now local `BAAI/bge-reranker-base` on hybrid's top-10 only. Basis #293: MRR@10 delta 0.08152458900226757, CI 0.04773198341836735 to 0.1171530435090703; nDCG@10 delta 0.06231550367445169, CI 0.03897278888099252 to 0.08564412540024816; CPU rerank p95 434.1544819999399 ms. Recall@10 unchanged because it is still those 10 ids. K=30 p95 exceeded 800 ms, so the candidate pool was not enlarged. Weights ~1.1GB; first load ~8 s. If the model fails to start: warn, fall back to lexical rerank, write `last_rerank_mode=lexical_fallback`. Switches can also return to lexical only, or `set_retrieval_switch("bm25")` for BM25. Gold still two-model plus proxy review; human reviewed only those 16.

## 14. fastembed 0.8.1 recheck

After [PR #295](https://github.com/luxingjiang1993/FreshLatch/pull/295) merged to main (`a8348df`), x1 scoring arm was re-run on current code with fastembed 0.8.1. n=224, `score_role=arm`, 794 chunks. Bootstrap 10000, seed 20261007. Four arms: bm25, hybrid, hybrid+rerank_lexical, hybrid+rerank (`BAAI/bge-reranker-base`, hybrid top-10 only). Query vectors computed before timing. Rerank-only p95 excludes hybrid retrieve and model load. No production code change; no gold change; no paid API. Evidence: `docs/evidence/fastembed-081-recheck/`.

### embedding

Same current code, same `FASTEMBED_CACHE_PATH`. 0.7.1 via `embed_texts_local` under an isolated prefix; 0.8.1 via the system interpreter. 794 chunk vectors and 224 scoring-arm query vectors bit-identical; `max_abs` 0.0. Conclusion: match.

Saved top-10 orders also match: bm25/hybrid/lexical vs #283/#285 `per-query.json`; hybrid vs #293's 0.7.1 dump; neural and lexical vs #293 `per-query.json`. Order diffs 0; set diffs 0.

### Four arms vs prior numbers

| Arm | Recall@10 | MRR@10 | nDCG@10 | vs prior |
|---|---:|---:|---:|---|
| bm25 | 0.9196428571428571 | 0.7275333049886621 | 0.7267672386770819 | matches post–gold-revision #285 |
| hybrid | 0.9732142857142857 | 0.7739937641723357 | 0.7803516716233564 | matches post–gold-revision #285 |
| hybrid+rerank_lexical | 0.9732142857142857 | 0.7566609977324263 | 0.7626148790864964 | matches #293 K=10 |
| hybrid+rerank | 0.9732142857142857 | 0.8381855867346939 | 0.8249303827609481 | matches #293 K=10 |

BM25 vs hybrid: Recall delta 0.05357142857142857, 95% CI 0.022321428571428572 ~ 0.08928571428571429. MRR delta 0.04646045918367347, CI 0.02168358489229025 ~ 0.07260558390022674. nDCG delta 0.053584432946274525, CI 0.03201358973245737 ~ 0.07548337519518822. McNemar 2/14/204/4, p 0.004180908203124997. BM25-only: `p1-lx-06-new`, `s4-d0-t0-01-q6`. hybrid-only: `s1-d0-04-q3`, `s1-d0-05-q4`, `s1-d2-01-q1`, `s2-d0-04-q2`, `s2-d1-01-q3`, `s3-d1-01-q1`, `s4-d0-t1-02-q4`, `s4-d2-t1-04-q1`, `s5-d0-t0-01-q3`, `s5-d0-t0-01-q5`, `s6-d0-t1-03-q3`, `r4m-s5-d3-t1-05-q4`, `r4m-s5-d3-t1-05-q5`, `r4n-s6-d2-t1-91-qc`. Ids match the post–gold-revision record.

lexical vs neural: Recall delta 0.0, CI 0.0 ~ 0.0. MRR delta 0.08152458900226757, CI 0.04773198341836735 ~ 0.1171530435090703. nDCG delta 0.06231550367445169, CI 0.03897278888099252 ~ 0.08564412540024816. McNemar 0/0/218/6, p 1.0. Discordant ids empty. Matches #293 K=10.

#285 `summary.json` `rank_metrics` still holds pre–gold-revision nDCG means: hybrid 0.779488160892922, then-lexical 0.7617513683560622. This run's hybrid nDCG matches post-revision 0.7803516716233564; lexical nDCG matches #293's 0.7626148790864964. On `s1-d0-05-q4`, hybrid and lexical nDCG are both 0.5; BM25 is 0.0. hybrid vs lexical nDCG delta and CI remain -0.017736792536859957, -0.03478236247276103 ~ -0.0014390192270836006, bit-identical to that #285 paired delta. BM25 vs lexical nDCG delta becomes 0.035847640409414565, CI 0.01456894012455283 ~ 0.05721404238633618. Both MRR paired deltas bit-identical to #285.

### p95

Full-retrieve p95 vs #285 `cost.p95_ms`. Then hybrid+rerank was lexical. Rerank-only p95 vs #293 `p95_ms_k10`. Keep the two columns separate.

| Item | This run | Prior | Source |
|---|---:|---:|---|
| bm25 full-retrieve p95 | 80.69911300117383 | 69.78307600002154 | #285 |
| hybrid full-retrieve p95 | 79.9520560012752 | 82.5428959999499 | #285 |
| lexical full-retrieve p95 | 80.8420590001333 | 90.68060099980357 | #285 then hybrid+rerank |
| lexical rerank-only p95 | 3.3260540003539063 | 3.2369630007451633 | #293 |
| neural rerank-only p95 | 421.38391099979344 | 434.1544819999399 | #293 |

This run's hybrid+rerank full-retrieve p95 is 543.9485819988477 ms, including hybrid and K=10 cross-encoder. #285 hybrid+rerank p95 was lexical full-retrieve. This run neural load 14.809210199000518 s; #293 first load 8.242696646000695 s. All single wall-clock. Neural rerank-only p95 still below 800 ms. This recheck does not change `PRODUCTION_RETRIEVAL_MODE`.

Gold remains two-model labeling plus Ronin agent (model) proxy review. Human review covers only DECISION-16's 16 questions.

## 15. Revision log

This wave only edits `docs/evidence/retrieval-decision.md`. Corrections after checking in-repo sources:

1. Smoke-set dense embedding filled as `text-embedding-v4` (`reports/retrieve-arm-compare.md`), not the later x1 bge-small-zh-v1.5. Corpus filled as 28 files, 84 chunks; baseline report date 2026-09-28; I0 acceptance re-run 2026-09-29. dense Recall@10 stays 0.9722; explicitly not all three arms at ceiling.
2. Hard-Gold #259 dense index filled as `text-embedding-v4`, 1024-d, 94 chunks. Separated from x1's 512-d local embedding so the two Recall@10 figures are not read as one model. Skeleton acceptance date narrowed from a vague 2026-10-03 to 2026-10-02 (`docs/evidence/i3/ACCEPTANCE.md`); pass rerun remains 2026-10-03.
3. Removed "~629 MB." Source only has process peak 643680 KiB.
4. Stated rerank loads no model and does not call `rank-bm25`. Removed "after switching to neural rerank, Recall@10 may rise." A cross-encoder that still only sees the top-10 likewise cannot raise any-hit Recall@10. Rejected the "rerank model too small" explanation.
5. Added why x1 did not run `text-embedding-v4`: `embeddings.py` only requests DashScope; config dimension 1024; #283 forbade paid APIs.
6. Added #286's three gaps: ingest/patch/invalidation write embeddings in sync; fastembed into production deps; keep one-click BM25. That ticket does not implement the switch.
7. Added checklist suggested counts: BM25 vs hybrid 172 / 48 / 4; BM25 vs rerank 172 / 48 / 4; hybrid vs rerank 149 / 36 / 19 / 4. Stated the 16 Recall@10 deltas ≠ the 48 discussable rows.
8. Filled full-set qtypes 66 / 156 / 45; all 43 guardrails are trap; full-set adversarial 0. fastembed 0.7.1 attributed to #285 `summary.json`; #283 RESULT names the library only.
9. #285 main table still uses four decimals. Side notes raw values: Recall@10 0.9196428571428571 and 0.9732142857142857; McNemar p 0.004180908203124997. Cost seconds likewise side-note `cost.json` raws.
10. Chinese rewritten for technical-writing habit. Checked number meanings unchanged.
11. Key technical nouns restored to English originals throughout: BM25, dense, hybrid, rerank, Recall@10, MRR, nDCG@10, p95, embedding, bootstrap, McNemar, chunk, fallback (`bm25_fallback`), gold set. Removed alternate translations such as "lexical / mixed / dense / rerank" glosses. Numbers and other statements unchanged.
12. After 2026-10-07 human decision: backfill. `s1-d0-05-q4` gold dropped `s1-d0-05-warn#p1@T1`. Recomputed BM25 vs hybrid from #283 `per-query.json`; no re-embedding; no paid API; no new p95. Recall@10 still 0.9196428571428571 vs 0.9732142857142857, delta 0.05357142857142857, 95% CI 0.022321428571428572 ~ 0.08928571428571429, McNemar 2/14/204/4, p 0.004180908203124997. MRR still 0.7275333049886621 vs 0.7739937641723357, delta 0.04646045918367347. hybrid mean nDCG@10 from 0.779488160892922 to 0.7803516716233564; delta from 0.05272092221584028 to 0.053584432946274525; CI to 0.03201358973245737 ~ 0.07548337519518822. Switch decided by human. `PRODUCTION_RETRIEVAL_MODE` set to `hybrid+rerank`. `set_retrieval_switch("bm25")` remains one-click rollback. Missing vectors still `bm25_fallback`. This decision covers only DECISION-16's 16 rows, not full-set line-by-line human review. Sections that say "still bm25 then" stay as records of that day.
13. 2026-10-07: added §12 local neural reranker contrast. Decision column K=10, `BAAI/bge-reranker-base`, CPU. Recall@10 both 0.9732142857142857. MRR@10 delta 0.08152458900226757, CI 0.04773198341836735 ~ 0.1171530435090703. nDCG@10 delta 0.06231550367445169, CI 0.03897278888099252 ~ 0.08564412540024816. Neural p95 434.1544819999399 ms. Decision sentence: "recommend opening a separate switch ticket." Production rerank not changed then. K=30 neural p95 1371.0923300004652 ms does not enter the decision sentence. v2-m3 not run. Gold still two-model plus proxy review; human review covers only DECISION-16's 16.
14. 2026-10-07: added §13. Oriental Ronin decided production rerank = `BAAI/bge-reranker-base`, hybrid top-10 only. Basis: prior MRR@10 and nDCG@10. `PRODUCTION_RETRIEVAL_MODE` remains `hybrid+rerank`. Failure records `last_rerank_mode=lexical_fallback`. `set_retrieval_switch("hybrid+rerank_lexical")` returns to lexical overlap; `set_retrieval_switch("bm25")` returns to BM25. Gold framing unchanged; human reviewed only DECISION-16's 16. fastembed pinned to 0.8.1.
15. 2026-10-07: added §14. fastembed 0.8.1 re-ran four arms on current code. Chunk and scoring-arm query vectors bit-identical vs 0.7.1. Recall@10, MRR@10, nDCG@10, McNemar discordants match post–gold-revision #285 and #293 K=10. p95 is new single-run timing; see that section's table. No production code change; no gold change.
16. DOC-EN-SSOT-P1: narrative translated to English; all decimals, Issue/PR numbers, timeline table, and English terms BM25/dense/hybrid/rerank/Recall@10/MRR/nDCG preserved.
