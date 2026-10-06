# TASK / ticket — RET-01.5

## Ticket
- **ID**: RET-01.5
- **Title**: `spike(eval): x1 分型三臂打分脚本（单测，不跑真分）`
- **Paths**:
  - 新建 `src/freshlatch/eval/retrieve_typed.py`
  - 新建 `scripts/run_retrieve_x1.py`
  - 新建 `tests/unit/test_retrieve_x1.py`
- **Executor**: `/implement`。本票禁止对 x1 语料打真实 embedding，禁止写 `reports/x1/retrieve-x1-arm-compare.md` 的真分，禁止写 `RESULT-*.md`。
- **先读**: `tasks/RET-01.md` 的报告列与领先定义；RET-01.1 的检查器；RET-01.2 的 `embed_cache`

编码可以在 RET-01.3 / RET-01.4 进行的同时开工。真分仍只属于 RET-01.6。

## 行为

`retrieve_typed.py` 从 `retrieve_eval` **import** 复用 `recall_at_k`、`mrr_at_k`、`arm_pass_line`、`_p95_ms`、`_ingest_eval_corpus`、`_attach_vecs`、`_cached_query_embedder` 的既有语义。不改 `retrieve_eval.py`。x1 需要而旧函数没有的部分写在新模块：

- 按 qtype 与按 trap+adversarial 分桶的 R@10、MRR@10
- multi_hop 全命中：该题每一个 relevant id 都出现在 top 10
- 干扰命中@10：任一 `distractors` id 出现在 top 10 的题占比
- hybrid 相对 bm25 的逐题胜 / 平 / 负（比的是该题 R@10）
- 查询延迟：样本是 `time.perf_counter` 的秒差。p95 直接调用 `_p95_ms`（内部乘 1000 得到毫秒）。p50 用同一排序与 `ceil` 取 0.50 分位，再乘 1000。不要把已经是毫秒的数再送进 `_p95_ms`
- 模式诚实：dense 列的 `last_retrieval_mode` 只能是 `dense`，hybrid 列只能是 `hybrid`。口径同 `run_arm_compare` 里的 `modes_seen`
- `arm_pass_line` 写入报告的「参考」一节。它失败时进程仍可退出 0。hybrid 落后不是脚本错误

`scripts/run_retrieve_x1.py`（同样自行把 `src` 插入 `sys.path`）。参数名与 RET-01.6 的命令一致，不要另起一套：

- `--corpus` 默认 `data/exp/x1/corpus`；`--traps` 默认 `data/exp/x1/traps`；`--questions` 默认 `data/eval/retrieve_x1.json`；`--config` 必填
- `--check-only`：只跑 RET-01.1 的检查。给出 `--prereg` 时核对其中三枚指纹（语料 `aggregate_checksum`、题集 `aggregate_checksum`、配置 `sha256_hex`，口径同 RET-01.4）。不加载向量，不写臂报告
- 正式模式（留给 RET-01.6，本票只做参数拒绝与假向量单测）：`--dense-db`、`--cache`、`--out`、`--prereg`。`--dense-db` 等于 `data/dense/index.sqlite` 时退出非 0
- 查询向量走 `embed_cache`，不重复实现第二套哈希
- `--out` 下写 `retrieve-x1-arm-compare.md` 与同名 `.json`。行必须包含「总体」「lexical」「paraphrase」「multi_hop」「trap+adversarial」
- 不调用 `python -m freshlatch.eval`，不调用 `rerank_lexical`

单测建一个 tmp 小语料，用与 `tests/unit/test_i3_hard_gold.py` 中 `_write_dummy_dense` 相同的手法写占位 vec（`pack_vec`，非全零，dim 可以是 8）。不调用 `embed_texts`。断言分型聚合、全命中、干扰命中、模式诚实，以及 `PRODUCTION_RETRIEVAL_MODE == "bm25"`。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 新单测与既有检索单测，When `python -m compileall -q src` 且 `python -m pytest tests/unit/test_retrieve_x1.py tests/unit/test_x1_checks.py tests/unit/test_i3_hard_gold.py tests/unit/test_hybrid_rrf.py tests/unit/test_dense_arm.py -q`，Then 退出码 0。
  2. Given tmp fixture 与一份含正确指纹的临时 PREREG，When `python scripts/run_retrieve_x1.py --check-only --corpus <tmp>/corpus --traps <tmp>/traps --questions <tmp>/questions.json --config <tmp>/config.json --prereg <tmp>/PREREG.md`，Then 退出码 0。指纹被改一个字符后同一命令退出非 0。
  3. Given `--dense-db data/dense/index.sqlite`，When 解析参数，Then 退出非 0，且该文件的 mtime 不变（测试不要真的去碰仓库里的这个路径；用字符串比较加一个「若路径等于生产默认库则拒绝」的纯函数即可）。
  4. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/eval/__main__.py src/freshlatch/store/embeddings.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/eval/retrieve_eval.py#run_arm_compare,recall_at_k,mrr_at_k,arm_pass_line,_p95_ms,_ingest_eval_corpus,_attach_vecs,_cached_query_embedder`；`tests/unit/test_i3_hard_gold.py#_write_dummy_dense`；`src/freshlatch/store/embed_cache.py`（RET-01.2）；`src/freshlatch/eval/x1_checks.py`（RET-01.1）
  - Pin: 仓内现行文件（main@`18b5172`）
  - What changed: 新模块增加分型、全命中、干扰命中、延迟与成本列的报告；新脚本拒绝生产 dense 库路径
  - Why not copy as-is: `run_arm_compare` 只出单一 R@10，并且默认库指向 `data/corpus` 与 `data/dense/index.sqlite`。直接跑会覆盖 #259 证据，也没有 qtype 行
  - License note: 仓内代码。仓库根目录无 `LICENSE` 文件
- **Tests**: added（`tests/unit/test_retrieve_x1.py`）
- **Rollback**: 删除本票三个新文件
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 与生产默认臂（保持 `bm25`）
  - `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 的冻结结论，以及同目录 RERUN 证据（`RERUN-20261003.md`、`RERUN-20261003-259.md`）
  - GitHub issue #260
  - `data/eval/retrieve_hard_gold.json`（`hard-c4-paraphrase`、`hard-c6-paraphrase` 只作背景，不改该文件）
  - `data/dense/index.sqlite`
  - `reports/retrieve-hard-gold-*`
  - ADR-0033 正文（`docs/adr/0033-hard-gold-过线与改臂授权闸.md`）
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`src/freshlatch/eval/retrieve_eval.py`、`src/freshlatch/eval/__main__.py`、`docs/evidence/retrieve-x1/PREREG.md`（若已存在）

### Provenance status
- result: pass
- notes: 上列 `retrieve_eval` 与 `_write_dummy_dense` 符号在 `18b5172` 存在。新模块只 import，不改原文件。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-06 | RET-01.5 | blocked | 等 RET-01.1 与 RET-01.2。不要等语料才写脚本；不要在本票出真分`

## Blocked by
- RET-01.1
- RET-01.2
