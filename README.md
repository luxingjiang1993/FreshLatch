# FreshLatch

> Reverify latch for signed claims — from "once true" to "still verifiable now."

Two weeks later, the client asks: **does that judgment still hold?**

FreshLatch does not write a new brief. It does not make the commercial call. It diffs the signed corpus (T0) against the reverify-time corpus (T1) and returns a **Reverify Sheet** you can click back to evidence: what still holds, what must die, and where the gaps are. Expired, conflicting, or T1-unsupported claims **cannot stay green**. A human voids or renews them.

Repo: [luxingjiang1993/FreshLatch](https://github.com/luxingjiang1993/FreshLatch)

---

## The problem

Consultants, researchers, and strategy leads ship a defensible judgment. Then the world moves: competitor pricing, regulatory stance, interview reversals. Someone still forwards the **old green** attachment. Getting that wrong once is career risk.

What you actually need is not "write another memo." It is:

> Give me a sheet that points back to T0 and T1 originals — what still holds, what must be voided, and what is missing.

That ask lands about every 2–6 weeks. FreshLatch sells that one reverify and close.

---

## What it is

A **reverify latch**: signed claims go from "was true at T0" to "still verifiable against T1." The primary UI is a Reverify Sheet, not a chat box. Ground truth is source text, not model memory.

One-line boundary: **sell voiding and gaps — not faster summaries, not auto decisions.**

**单一垂直 = 顾问报告**（V1 / ADR-0027）。近端只做已签发顾问/战略主张的发前复验；样例主包为 McKinsey State of AI 公开洞察摘录（T0≈2025-03 → T1≈2025-11），见 `data/packs/v1-mck-soai/`。thesis-1 与 QuoteTTL 可留回归，**不算**第二垂直。仓内不提交整本咨报 PDF。

**V1.5 = Evidence-bound 表单补丁**（ADR-0029 · 冒烟）。对「需补丁」主张：正文替换 + 必填已入库 T1 + 人确认才应用 + 强制单条再验；独立 `propose_patch` / `confirm_patch`（**不**扩 HumanLatch）。**薄对话本期 Out**（不实装、不 stub；对话不改正式裁决）。发前 UX **无** C|T 开关。硬 Exit 见 `docs/evidence/v15/ACCEPTANCE.md`；关门摘要见 `docs/evidence/v15/V15-DoD-CLOSE.md`。档=冒烟；不升格 Hard-Gold。

**I2 = 安全三例**（ADR-0030 · 冒烟 / 面试安全轮）。越权召回 · 间接注入 · 检索投毒各一例可复现（确定性硬门；注入另 1× Lead→Auditor 冒烟）。薄表 `docs/security.md`；硬 Exit `docs/evidence/i2/ACCEPTANCE.md`；关门摘要 `docs/evidence/i2/I2-DoD-CLOSE.md`。**≠ idea #4**。档=冒烟；不是渗透认证，不报安全通过率/方差，不升格 Hard-Gold。

**V2 = 发前钩子 + 主张台账**（ADR-0031 · 冒烟 / 采用层）。Client Memo UI+CLI 同闸 + 入站 `POST /api/publish-hook/check`（本机默认 + 可选 token）+ 主张台账只读投影（discard∪renew）。硬 Exit 见 `docs/evidence/v2/ACCEPTANCE.md`；关门摘要见 `docs/evidence/v2/V2-DoD-CLOSE.md`。档=冒烟·采用层；**不**硬绑「可发」；`curl`/TestClient ≠ 开放 webhook/插件平台已交付；不报采用率；不升格 Hard-Gold。

**I3 = 面试加固三轨**（ADR-0032 · 冒烟 / 面试加固）。政策旁路 · B′合成夹具 · Hard-Gold 骨架。硬 Exit 见 `docs/evidence/i3/ACCEPTANCE.md`；关门摘要见 `docs/evidence/i3/I3-DoD-CLOSE.md`。档=冒烟/面试加固；**不是**改臂授权、政策平台或真事故复盘。

---

## What you get

Each signed claim lands in one of four states:

| Status | Meaning |
|--------|---------|
| **fresh** | Still verifiable — must cite clickable T1 evidence |
| **stale** | Dead — must point to the T1 span that kills it |
| **unknown** | Insufficient evidence, or gate bounce — cannot pretend green |
| **void** | Human voided — machine red alone is not enough |

Also included:

- **Click-back evidence** — verdicts must point to spans, not "the model remembers"
- **HumanLatch** — a person voids or renews (renew requires T1 evidence); agents **cannot** turn red back to green
- **Client Memo (optional export)** — forwardable three columns (still holds / voided / gaps); no "enter / don't enter market" advice

---

## Who it's for

**Fit**

- Independent consultants, industry researchers, strategy leads who already shipped a judgment and own last week's attachment
- Individuals or small teams buying "research / proposal integrity," not another Copilot seat

**Non-goals / not a fit**

- Growth teams that only want faster summaries
- Enterprise SSO / platform-bundle buyers
- Buyers who want the system to auto-decide commercial outcomes
- Treating this repo as a general memory platform or agent middleware

The public repo is a **synthetic local demo**. Real client confidentials do not belong in a portfolio.

---

## How it works

One reverify is roughly this path:

1. **Import** signed claims (T0 docket shape: claim + evidence refs)
2. **Pick T1** — upload a corpus pack, paste change notes (confirm before ingest), or use the built-in synthetic pack (UI labels it `synthetic`)
3. **Contrast** — retrieve and read T1 originals; hunt "still holds" and "already dead"
4. **Latch** — `fresh` / `stale` / `unknown`; rules gate force: no T1 evidence → not green; `stale` / `unknown` cannot stay green
5. **HumanLatch** — void or renew; voided ids cannot go green again on rerun

Under the hood: Lead / Critic / Auditor plus a rules gate. For visitors, remember three lines: **source text is truth, gates control release, humans control void and renew.**

Default demo thesis (synthetic): *"Does the judgment on entering the Southeast Asia SMB AI customer-support market in the next 12 months still hold?"*

---

## Current status

Honest snapshot of this public repo:

| | |
|--|--|
| **Runs locally** | Reverify Sheet UI, main reverify chain, human void/renew, synthetic corpora, gate unit tests |
| **Synthetic** | Demo and eval materials are labeled synthetic — not real client dockets |
| **Not claimed** | Live SaaS, paying customers, "W12 passed," or closed Phase-1 measurement — do not cite this repo that way |
| **V1.5 (smoke)** | Evidence-bound form patch seam is in-repo（propose/confirm + reverify + export）. See `docs/evidence/v15/`. **薄对话** remains Out. Not Hard-Gold. |
| **I2 (smoke)** | Security demos in-repo：ACL tenant filter · injection fail-closed · poison metadata drop. See `docs/evidence/i2/` + `docs/security.md`. ≠ #4. Not penetration cert / Hard-Gold. |
| **V2 (smoke / adoption)** | Publish hook + claim ledger in-repo：Memo UI/CLI gate · inbound check allow/deny · read-only discard∪renew ledger. See `docs/evidence/v2/`. `curl` ≠ webhook/plugin platform Done. Not Hard-Gold; does not hard-bind「可发」. |
| **I3 (smoke / interview hardening)** | Policy bypass · B′ fixtures · Hard-Gold skeleton in-repo. See `docs/evidence/i3/`. Not arm-change authorization / policy platform / real-incident postmortem. |
| **Hard-Gold** | #259 same-corpus rerun **passed the gate**; production default still `bm25`; **not switched**. Next hop = Gate implementation ticket human-final or freeze bm25. See `docs/evidence/hard-gold-arm/`. Do not cite as “already hybrid”. |
| **Known gaps** | Retrieval is still BM25-first (production default `bm25`). Some modules (e.g. memory hygiene) exist in code but are not all on the default main path. A whitelist thin URL (`www.mckinsey.com`) exists for the T1 ingest demo; open-ended live web and an open crawler are still not built. Thin dialogue / chat-as-verdict is deliberately not shipped in V1.5. Word/Notion/open webhook platforms remain Backlog C′ (not V2 Done). Next hop: arm-change Gate human-final **or** freeze `bm25`; C′ stays backlog. |

Layer identity: smoke / adoption / interview hardening — **not** closed statistical measurement.

For engineering acceptance boundaries, read `docs/evidence/` and root `CONTEXT.md`. This README is not a certification.

---

## Quick start

**Requires:** Python 3.11+. For the LLM main chain, put at least `DASHSCOPE_API_KEY` (OpenAI-compatible) in a root `.env`. Deterministic unit tests do not need a real key.

```powershell
# Windows PowerShell — console UTF-8
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new()

cd <repo-root>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:PYTHONPATH = "src"
python -m pytest -q          # unit tests
python -m freshlatch.ui.app  # Reverify Sheet → http://127.0.0.1:8000
```

Unix equivalent: `source .venv/bin/activate`, `export PYTHONPATH=src`. The primary CTA is **Start reverify**, not "Generate answer."

Corpus ingest example: `PYTHONPATH=src python scripts/ingest_corpus.py`

---

## Docs

| Topic | Link |
|-------|------|
| Product brief & boundaries | [`docs/product/FreshLatch.md`](docs/product/FreshLatch.md) |
| Charter slice (CN) | [`docs/product/FreshLatch-立项切片.md`](docs/product/FreshLatch-立项切片.md) |
| Glossary (claim / T0·T1 / gate / HumanLatch) | [`CONTEXT.md`](CONTEXT.md) |
| Architecture & specs | [`docs/spec/README.md`](docs/spec/README.md) |
| Evidence & acceptance | [`docs/evidence/`](docs/evidence/) |
| Agent / contributor norms | [`AGENTS.md`](AGENTS.md) |

---

## Roadmap

Next hop: Hard-Gold **passed** (#259) but **did not switch** the production arm — Gate human-final to change `PRODUCTION_RETRIEVAL_MODE`, or freeze `bm25`. C′ (Word/Notion/open webhook) remains backlog. Live web, if any, is **ingest to T1 disk → then reverify** — not open-ended Q&A as the product. Details live in repo docs and ADRs under `docs/`.

---

## License & disclaimer

No standalone `LICENSE` file yet. Confirm your own compliance needs before use.

**Disclaimer:** FreshLatch outputs reverify contrast and HumanLatch records. **Not legal advice. Not automated commercial decisions.** Synthetic demos explain product shape only; keep real client confidentials out of public portfolios.