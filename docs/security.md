# FreshLatch security demos (I2)

> **Layer: smoke.** This page is not a penetration certification, does not report a security pass rate, and does not report variance. Hard Exit is only the three hard-table rows below.
> Authority: ADR-0030 · parent spec #213. Fixture bodies land via #214 / #215; this page is a thin cross-link table only. Do not bump `docs/_archive/2026-10/research/adversarial/INDEX.md`; do not treat a catalog version bump as I2 Done.

## Hard table

| threat | demo_id | layer | repro_cmd | expected | smoke_note |
|--------|---------|-------|-----------|----------|------------|
| Cross-tenant recall | `acl-t001` | `RetrievalStore.retrieve` with explicit `tenant_id` | `pytest tests/unit/test_i2_retrieve_trust.py -q -k acl_t001` | Results for `tenant_id=B` contain no tenant A | smoke · deterministic · no LLM |
| Indirect injection | `inj-t001` | `rule_gate` + `Runner._finalize` | `pytest tests/unit/test_rule_gate.py tests/unit/test_i2_injection_gate.py -q` | Contaminated T1 must not yield a `fresh` green light | smoke · zero LLM · no `meta_gate` · **dual-marker substrings** (both an "ignore instructions"-class and a "mark as fresh"-class hit required to refuse); old call sites without `t1_evidence_texts` do not enable this |
| Retrieval poisoning | `poison-t001` | `retrieve` drops `poison`/`untrusted` metadata | `pytest tests/unit/test_i2_retrieve_trust.py -q -k poison_t001` | High-scoring poison chunks do not enter the result set | smoke · deterministic · no unlabeled heuristic |

Short index: `docs/evidence/i2/INDEX.md`. Acceptance hard checks: `docs/evidence/i2/ACCEPTANCE.md`.

## Reference-repo boundary (oral · does not raise Exit)

When interviewers ask "why not the reference-repo setup," use the three lines below; **not** a new hard gate, and do not report ASR / pass rates.

| Reference | What they prove | What we deliberately do not |
|-----------|-----------------|------------------------------|
| PoisonedRAG | Unlabeled corpus corruption: adversarial passages score high into recall | Poison hard door only recognizes explicit `poison`/`untrusted`; we do not pretend to detect unlabeled corruption |
| TRIM / rag-evidence-inject · rag-redteam | In-evidence injection benchmarks, instruction masking, canary ASR, CI red-team probe matrices | Injection lands on existing Gate fail-closed + 1× real-path smoke; not a TRIM middleware or red-team product |
| ogx-evals | Enterprise multi-tenant ABAC, CTLR/AVR eval matrices | Thin `tenant_id` real `retrieve` filtering is enough; no tenant admin surface / full RBAC |
| SafeRAG | RAG security benchmark panorama (Noise/Conflict/Toxicity/DoS, …) | I2 = interview security-round three-case smoke; ≠ security platform or penetration certification |

Local index: historical project code under 供参考/FreshLatch-roadmap-refs/ (if the manifest is not in-repo, local path only — do not link dangling docs).

## Optional (not counted toward I2 Exit)

idea #4 stale-masquerade `adv-fresh-t001` may ship in the same wave as interview ammo; evidence page `docs/evidence/i2/adv-fresh-t001.md`. **Not counted toward I2 Exit; not a fourth hard-table row.** I2 ≠ #4.

## Thin ACL scope (A-P4)

薄 ACL ≠ 完整 SaaS 多租户. Thin ACL ≠ full SaaS multi-tenancy. CI matrix `tests/unit/test_acl_cross_tenant_matrix.py` only locks cross-tenant read/write/session denial under server-side credential mapping: identity comes from `FRESHLATCH_SERVING_API_KEYS`; a client-supplied `tenant_id` alone is not access. No tenant admin UI, SSO, billing isolation, or full RBAC. This section is not a new I2 hard-table row.

## Red-team paired regression (A-P6)

红队成对回归 ≠ 完整对抗安全认证. Red-team paired regression ≠ full adversarial security certification. `tests/unit/test_redteam_accept_reject_pairs.py` feeds should-deny and should-not-deny pairs through the same fixture path: should-deny must deny or abstain; should-not-deny must not false-refuse on that path. Pairs that touch ACL / Serving fail-closed across tenants and when unauthorized; identity still comes from `FRESHLATCH_SERVING_API_KEYS` server-side mapping. This section is not a new I2 hard-table row, does not report attack success rate, and does not replace penetration certification.

Optional scan: garak may run in a private environment. 本仓 CI 不调用 garak, and 付费或外网 garak is not a merge gate. This repo's CI does not invoke garak, and paid or external-network garak is not a merge gate. Sample and block-ship bar: `docs/ops/可选-garak-tool-injection扫描.md`. Default: not required CI.
