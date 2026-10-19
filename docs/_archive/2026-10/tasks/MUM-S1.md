# TASK / ticket — one slice

## Ticket
- **ID**: MUM-S1
- **Title**: `refactor(models): S0+S1 模型字面量收进 MODEL_REGISTRY（行为不变）`
- **Trust**: Watch
- **Paths**:
  - `docs/_archive/2026-10/plans/model-unified-mgmt/00-status.md`
  - `docs/_archive/2026-10/plans/model-unified-mgmt/01-plan.md`
  - `src/freshlatch/models.py`
  - `src/freshlatch/eval/patch_events_verify.py`
  - `src/freshlatch/eval/patch_events_sensitivity.py`（仅 `VERIFY_PY_SHA256` 重钉 + 型号比对改读 registry）
  - `src/freshlatch/llm.py`
  - `scripts/run_issue_284_verify.py`
  - `scripts/run_neural_rerank_compare.py`
  - `scripts/run_x1_offline_mode_compare.py`
  - `scripts/run_fastembed_081_recheck.py`
  - `scripts/run_w4_acceptance.py`
  - `scripts/smoke_dashscope_tool_loop.py`
  - `scripts/i1_mck_runnable_gold.py`
  - `tests/unit/test_model_registry.py`
  - `tasks/MUM-S1.md`

## Agent Guards
- **Blast**: types
- **Trust**: Watch
- **Acceptance**:
  1. `MODEL_REGISTRY["nli"].model` 与搬迁前 `XNLI_MODEL_ID` 同为 `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`；`patch_events_verify.XNLI_MODEL_ID` 从 registry 读出。
  2. `LLMClient` 用 `MODEL_REGISTRY["default_llm"].env_key` 读密钥，用该行 `base_url` 做默认端点；已有的 `DASHSCOPE_BASE_URL` 环境变量仍可覆盖。`default_llm.model` 仍是 `qwen-flash`。
  3. `pytest tests/unit/test_model_registry.py tests/unit/test_pe_auto_verify.py tests/unit/test_pe_sensitivity.py -q` 绿。`src/` 与未列入白名单的 `scripts/*.py` 不再出现 registry model 字面量（`models.py` 除外；注释 / docstring / 日志文案沿用原扫描豁免）。
  4. 不改 floors / gold / x1 / production arm。不开 C-04，不写 RESULT。C-04 manifest 的 `generator_model` / `nli_model` 仍为 null。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/models.py#MODEL_REGISTRY`；`src/freshlatch/eval/patch_events_verify.py#XNLI_MODEL_ID`；`src/freshlatch/llm.py#LLMClient.client`；批准稿 `docs/_archive/2026-10/plans/model-unified-mgmt/01-plan.md`
  - What changed: NLI 行收入 registry（同一字符串）；`llm.py` 改读 `env_key` / `base_url`；与 registry 重复的 script 调用点改读别名
  - Why not copy as-is: 字面量散落时换模型要改多处。本票不引入 profile，也不改运行默认
- **Tests**: updated `tests/unit/test_model_registry.py`
- **Rollback**: 还原上述路径；`VERIFY_PY_SHA256` 回到改 `patch_events_verify.py` 之前的 LF 钉
- **Do-not-touch**:
  - floors / gold / x1 / production arm
  - C-04 开跑、RESULT、manifest 的 `generator_model` / `nli_model`（保持 null）
  - S2 profile、S3 运维文档、S5 fit report、S6 连通性、S7 正式闸
  - 不发明 SESOI

### Provenance status
- result: pass
- notes: model id 字符串与 DashScope 默认端点、密钥环境变量名与搬迁前相同

### Evidence
- typecheck: `python -m compileall -q src` 通过；`ruff check` 改动文件通过
- tests: `pytest tests/unit/test_model_registry.py tests/unit/test_pe_auto_verify.py tests/unit/test_pe_sensitivity.py tests/unit/test_token_usage.py -q` → 36 passed
- paths: 见 Ticket Paths。C-04 manifest `generator_model` / `nli_model` 仍为 null

## Handoff
`2026-10-15 | MUM-S1 | done | Watch 审合；S2 另 PR`
