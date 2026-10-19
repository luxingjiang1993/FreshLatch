# TASK / ticket — one slice

## Ticket
- **ID**: L4-C-04-formal-run
- **Title**: `eval(c04): formal establishment run (qwen-flash + mDeBERTa; built_n=91)`
- **Trust**: Gate
- **Paths**:
  - `docs/evidence/patch-establishment/PREREG.md` (Amendment-02 + 「跑」)
  - `docs/evidence/patch-establishment/RESULT.md`
  - `docs/evidence/patch-establishment/manifest.json`
  - `docs/evidence/patch-establishment/measurement.json`
  - `docs/evidence/patch-establishment/formal-generations.jsonl`
  - `docs/evidence/patch-establishment/primary-tc.json`
  - `src/freshlatch/eval/patch_establishment_formal.py`
  - `src/freshlatch/eval/__main__.py`
  - `tests/unit/test_l4_c_04_patch_establishment.py`
  - `tasks/L4-C-04-formal-run.md`

## Agent Guards
- **Blast**: experiment-claim / evidence
- **Trust**: Gate
- **Acceptance**:
  1. 主人明文「跑」+ Amendment-02 锁解码；正式针用 qwen-flash + 真 mDeBERTa；禁止 LMS。
  2. 分数只在测量后写入 RESULT / measurement；T−C L1；n=built_n=91；不得假装 100。
  3. 不改 floors / gold / x1 / production arm；`second_formal_y=false`；不得标 L5。
  4. 成本 ≤¥10。
- **Do-not-touch**: floors / gold / x1 / production arm / RESULT-Y / PREREG-Y / quality-gate floors

### Provenance status
- result: pass (run completed; establishment not_established)
- notes: T−C point≈0.1515；ci95_low≈−0.074 → L1 不成立；k=33；spend≈¥0.03–0.08
