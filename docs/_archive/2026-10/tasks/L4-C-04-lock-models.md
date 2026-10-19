# TASK / ticket — one slice

## Ticket
- **ID**: L4-C-04-lock-models
- **Title**: `chore(c04): lock generator/nli from MODEL_REGISTRY (built_n=91)`
- **Trust**: Watch
- **Paths**:
  - `docs/evidence/patch-establishment/manifest.json`
  - `docs/evidence/patch-establishment/PREREG.md`
  - `src/freshlatch/eval/patch_establishment.py`
  - `tests/unit/test_l4_c_04_patch_establishment.py`
  - `tasks/L4-C-04-lock-models.md`

## Agent Guards
- **Blast**: experiment-claim / evidence
- **Trust**: Watch
- **Acceptance**:
  1. `manifest.json` 的 `model.generator_model` 等于 `MODEL_REGISTRY["default_llm"].model`，也等于 `qwen-flash`。`model.nli_model` 等于 `MODEL_REGISTRY["nli"].model`，也等于 `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`。写入器读 `DEFAULT_MODEL` 与 `NLI_MODEL`，不另造模型 id。
  2. `data/patch-establishment/v1/SPLIT.json` 的 `built_n` 仍是 91，`gap_n` 仍是 9。语料 path 与 sha256 不重冻，缺额不补到 100。
  3. `measurement.json` 与 `RESULT.md` 仍是 `run_status=unrun`。本票不写 RESULT 分数，不开正式跑，不发明 SESOI。`generator_sha256` 与 `nli_sha256` 仍是 null。
  4. floors / gold / x1 / production arm 的字节与 `PRODUCTION_RETRIEVAL_MODE=hybrid+rerank` 不变。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/models.py` 的 `MODEL_REGISTRY["default_llm"]` 与 `MODEL_REGISTRY["nli"]`（#636）；C-04 manifest 在 #635 把两格留空
  - What changed: 只把型号两格从 null 锁成登记册默认
  - Why not copy as-is: 激活批注故意把型号留空，等主人锁登记册默认；hash 与「跑」仍未齐
- **Tests**: `tests/unit/test_l4_c_04_patch_establishment.py`。零 LLM
- **Rollback**: 把 `generator_model` 与 `nli_model` 改回 null，并还原预注册页的模型锁定批注
- **Do-not-touch**:
  - floors / gold / x1 / production arm
  - `docs/evidence/quality-gate/PREREG.md`
  - `docs/evidence/patch-events/RESULT-Y.md` 与 `PREREG-Y.md`
  - `docs/evidence/neural-rerank/*`
  - `data/patch-establishment/v1` 的冻结核与 `built_n`
  - 不发明 SESOI
  - 不写 `docs/evidence/patch-establishment/RESULT.md` 的分数
  - 不开 C-04「跑」

### Provenance status
- result: pass
- notes: 型号取登记册别名。`built_n=91`。`run_status=unrun`。

### Evidence *(after implement)*
- typecheck: `python -m compileall -q src` exit 0；`ruff check` 触及文件 exit 0
- tests: `tests/unit/test_l4_c_04_patch_establishment.py` 12 passed；连同 `tests/unit/test_model_registry.py` 共 18 passed
- paths: `manifest.json`；`PREREG.md`；`patch_establishment.py`；`test_l4_c_04_patch_establishment.py`
