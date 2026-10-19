# FreshLatch metrics map (thin pointer · 2026-10-20)

> In-repo pointer page for the out-of-repo metrics system research. Ticket [#737](https://github.com/luxingjiang1993/FreshLatch/issues/737) · Parent [#734](https://github.com/luxingjiang1993/FreshLatch/issues/734) · Brief `org-os/runbooks/briefs/IR-PACK.md` §C.
> Source of truth: `org-os/research/20261020-freshlatch-metrics-system.md` (out-of-repo; 2026-10-20 Asia/Shanghai; Driver PL, Approver Owner). This page summarizes and points; it does not extend or replace the source.
> Scope of this ticket: map + pointers only. **Not opened here:** METRICS-P1-FILL (fill B1–B3), METRICS-E1-LOCAL (cross-model pack D1–D3), METRICS-TELEMETRY (A2/B4), METRICS-AUDIT (G2).

---

## 1. One layer, one picture (North Star → Guardrails)

```
North Star (product)   B2 人审有效动作率 — human effective-action rate:
                       real discard|renew actions / reviewable claims (window)
         ↑
Input / Leading        partner per-session log (B1) · Sheet completion (B5) ·
                       evidence-click rate (B4)
         ↑
Delivery               Phase gates (0 honesty / 1 value / 2 privacy / 3 portability)
         ↑
Quality Guardrails     false-accept · no-fake-green=0 · no-T1-green=0 · RESULT-Y firewall
         ↑
Cost / Latency Guard   e2e P95 · tokens per claim · $ per reverify (or local GPU·h)
```

**North Star = B2.** Cost, latency, pytest counts, and scorecard grades are guardrails — never the North Star.

**Hard bans** (from source §5, adopted here):
- No composite "health score" blending RESULT-Y (丙) with human metrics into one green dot.
- No synthetic/local dry-runs substituting for B1 partner logs.
- No re-writing RESULT-Y / frozen gold to look better on local runs.
- No NPS/intent survey standing in for kill criterion (b).
- Smoke ≠ formal RESULT; nothing on this page may be written into RESULT-Y / PREREG-Y.

## 2. Catalog skeleton (IDs only — definitions live in the source)

| Group | IDs | In-repo ruler already? |
|-------|-----|------------------------|
| A · Discovery & narrative (demo/interview) | A1–A3 | A3 anchored by #735 assertions; A2/A4 telemetry not shipped |
| B · Activation & habit — **North Star zone** | B1–B5 | B1 protocol exists, no data yet; B2/B3 protocol exists (latch_log / override report); B4/B5 thin |
| C · Quality & evidence — **not proof the product works** | C1–C5 | C1 = RESULT-Y 丙 (frozen, do not edit); C2–C5 protocols exist |
| D · Model portability (E1) — **gap pack, separate ticket** | D1–D4 | No formal pack; D3 is a declaration gate, Owner decides |
| E · Trust & privacy | E1–E3 | Not productized |
| F · Cost & latency guardrails | F1–F4 | Protocols exist (SLI 5 / cost report / 发车检查单) |
| G · Engineering health | G1–G3 | G1 exists; G2 baseline missing; G3 is PR discipline |

Cadence (source §3): weekly = min-6 skeleton + B1/B2/B3 (write "样本不足" when thin); biweekly = F1/F2 + A1 notes; release = C4 + F4 + G1 + floors; kill window (→ ~2027-01-14) = kill trio + B1 threshold; model/privacy-tier switch = D1–D3 must pass first.

## 3. Firewall self-check (this ticket)

- [x] RESULT-Y / PREREG-Y / SESOI untouched; no smoke promoted to RESULT
- [x] Frozen faces untouched (gold / floors / x1 / `PRODUCTION_RETRIEVAL_MODE` / disposition four values)
- [x] No METRICS-P1-FILL / E1 / TELEMETRY implementation opened
- [x] No composite health score; North Star pinned to B2

## 4. See also

- [`docs/messaging-one-pager.md`](../messaging-one-pager.md) — narrative guardrail + one-line pointer
- [`docs/glossary.md`](../glossary.md) — **North Star (B2)** term entry
- [`docs/ops/生产观测最小6-索引.md`](生产观测最小6-索引.md) — the in-repo SLI rulers this map reuses (no new names)
- [`docs/evidence/patch-events/RESULT-Y.md`](../evidence/patch-events/RESULT-Y.md) — C1, frozen, read-only
