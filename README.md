# FreshLatch

> Reverify latch for signed claims — from "once true" to "still verifiable now."

Two weeks later the client asks: **does that judgment still hold?**

FreshLatch does not write a new brief or make the commercial call. It diffs the signed corpus (T0) against the reverify-time corpus (T1) and returns a **Reverify Sheet** you can click back to evidence: what still holds, what must die, and where the gaps are. Expired, conflicting, or T1-unsupported claims **cannot stay green**. A human voids or renews them.

The deliverable is a **forwardable reverify result** (sheet + optional Client Memo) — not a chat answer.

Repo: [luxingjiang1993/FreshLatch](https://github.com/luxingjiang1993/FreshLatch)

---

## Quick start

**Requires:** Python 3.11+. For the LLM main chain, put at least `DASHSCOPE_API_KEY` (OpenAI-compatible) in a root `.env`. Deterministic unit tests do not need a real key.

```powershell
# Windows PowerShell — console UTF-8
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new()

cd <repo-root>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

python -m pytest tests/ -q     # same family as CI
python -m freshlatch.ui.app    # Reverify Sheet → http://127.0.0.1:8000
```

Unix: `source .venv/bin/activate`. Primary CTA is **Start reverify**, not "Generate answer."

If embeddings / vectors are unavailable, retrieval may fall back to BM25 and record that degradation — informed fallback, not a silent change of the production switch.

---

## What it is

A **reverify latch**: signed claims go from "was true at T0" to "still verifiable against T1." Ground truth is source text, not model memory.

**One-line boundary:** sell voiding and gaps — not faster summaries, not auto decisions.

**Single vertical = advisor reports.** Near-term scope is pre-send reverify of already-issued advisor / strategy claims. Sample pack: public McKinsey State of AI insight excerpts under `data/packs/v1-mck-soai/`. Full client PDFs are not in this public repo.

### Per-claim machine states

| Status | Meaning |
|--------|---------|
| **fresh** | Still verifiable — must cite clickable T1 evidence |
| **stale** | Dead — must point to the T1 span that kills it |
| **unknown** | Insufficient evidence, or gate bounce — cannot pretend green |
| **void** | Human voided — machine red alone is not enough |

### Sheet-level disposition

| Disposition | Meaning |
|-------------|---------|
| **OK to send — all still hold** | No voided / must-die blockers |
| **OK to send — includes voided** | Some claims voided; the rest still hold |
| **Needs patch** | At least one claim needs an evidence-bound edit before send |
| **Do not send** | Hard blockers remain |

Also on the path: click-back evidence, HumanLatch (void / renew; agents cannot turn red back to green), optional Client Memo export, async reverify with cancel.

---

## How it works

1. **Import** signed claims (T0: claim + evidence refs)
2. **Pick T1** — upload a pack, paste change notes, or use the built-in synthetic pack
3. **Contrast** — retrieve and read T1 originals
4. **Latch** — `fresh` / `stale` / `unknown`; no T1 evidence → not green
5. **HumanLatch** — void or renew; voided ids cannot go green again on rerun

Production retrieval default is **`hybrid+rerank`** (local `BAAI/bge-reranker-base` on hybrid top-10). One-click rollback to BM25: `set_retrieval_switch("bm25")`. Missing vectors still record `bm25_fallback`.

Warm-up notes: `docs/ops/local-embed.md`.

---

## Honest status

Interview / demo / external copy: only [`docs/ops/口径一页纸.md`](docs/ops/口径一页纸.md).

| | |
|--|--|
| **Runs locally** | Reverify Sheet, main chain, human void/renew, synthetic corpora, gate unit tests |
| **Engineering (in-repo)** | L4 / regressible refusal product (typed abstain + hybrid+rerank + fixture CI) |
| **Externally honest** | ≈ L3+ / weak-L4 single-machine refusal prototype — **not** L5, registration pass, PMF, or live SaaS |
| **Hard-Gold** | Same-corpus rerun gate **passed** (under `docs/evidence/hard-gold-arm/`). Gate pass ≠ closed statistical product pass. |
| **Not claimed** | Paying customers, open-ended live web as main path, chat-as-verdict UI |

---

## Docs

| Topic | Link |
|-------|------|
| Interview / demo one-pager (CN) | [`docs/ops/口径一页纸.md`](docs/ops/口径一页纸.md) |
| Architecture overview (2026-10) | [`docs/architecture/2026-10-overview.md`](docs/architecture/2026-10-overview.md) |
| Product pointer | [`docs/product/FreshLatch.md`](docs/product/FreshLatch.md) |
| Glossary | [`CONTEXT.md`](CONTEXT.md) |
| Contribution boundary | [`docs/contribution-boundary.md`](docs/contribution-boundary.md) |
| Retrieval default decision | [`docs/evidence/retrieval-decision.md`](docs/evidence/retrieval-decision.md) |
| Local embed / rerank warm-up | [`docs/ops/local-embed.md`](docs/ops/local-embed.md) |
| Specs | [`docs/spec/README.md`](docs/spec/README.md) |
| License | [`LICENSE`](LICENSE) |
| Agent norms | [`AGENTS.md`](AGENTS.md) |

附录：[`docs/evidence/`](docs/evidence/)

---

## License & disclaimer

License: MIT — see [`LICENSE`](LICENSE).

**Disclaimer:** FreshLatch outputs reverify contrast and HumanLatch records. **Not legal advice. Not automated commercial decisions.** Synthetic demos explain product shape only; keep real client confidentials out of public portfolios.
