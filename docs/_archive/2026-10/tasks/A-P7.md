# TASK · A-P7 公开可复现 eval 包

## Ticket
- **ID**: A-P7
- **Title**: `feat(eval): reproducible public eval pack + result hash`
- **Paths**: `src/freshlatch/eval/public_pack.py`, `src/freshlatch/eval/__main__.py`, `tests/eval/fixtures/a_p7_public_eval_pack.json`, `tests/unit/test_a_p7_public_eval_pack.py`, `docs/eval-public-pack.md`
- **Trust**: Watch
- **Blast**: none

## Agent Guards
- **Acceptance**:
  1. Scripted one-command (or documented) local replay of a fixed eval pack.
  2. RESULT (or equivalent) emits a stable content hash field; docs show how to verify.
  3. Independent abstain handling documented (RAGAS alone ≠ ground truth).
  4. Docs: 公开可复现 ≠ 登上权威榜；no paid API required for CI path.
- **Provenance**: RAGAS + ARES spirit; reuse existing eval/ fixtures where present.
  - Kind: new
  - Source: 固定夹具 `tests/eval/fixtures/a_p7_public_eval_pack.json`。仓内没有可复用的公开包；未改 gold / x1。
  - What changed: `public-pack` 本地回放，RESULT 带 `content_hash`。abstain 只看 `system_action`。
- **Do-not-touch**: floors / gold / x1 / PRODUCTION_RETRIEVAL_MODE / SESOI / C-04 / RESULT-Y
- **Tests**: `tests/unit/test_a_p7_public_eval_pack.py`（replay/hash smoke）

### Provenance status
- result: pass
- notes: 未改注册 RESULT，未发明 SESOI，未读付费 API。

### Evidence
- typecheck: `python -m compileall -q src/freshlatch/eval/public_pack.py src/freshlatch/eval/__main__.py` 通过
- tests: `python -m pytest tests/unit/test_a_p7_public_eval_pack.py -q` → 7 passed；`python -m freshlatch.eval public-pack --verify` → verify=ok；无付费 API
- paths: `src/freshlatch/eval/public_pack.py` · `tests/unit/test_a_p7_public_eval_pack.py` · `docs/eval-public-pack.md`

## Handoff
Draft PR A-P7. draft=true. No paid「跑」.
