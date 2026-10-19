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

`retrieve_typed.py` 从 `retrieve_eval` **import** `recall_at_k`、`mrr_at_k`、`arm_pass_line`、`_p95_ms`、`_attach_vecs`。不改 `retrieve_eval.py`。

查询嵌入：不调用、不包装 `retrieve_eval._cached_query_embedder`（那是单次进程内缓存，而且会直接打 `embed_texts`）。x1 的 query embedder 建在 RET-01.2 的 `embed_cache` 上。单测注入假缓存，不发网络请求。

入库：corpus 与 traps 两个目录都调用 `load_corpus`（断言 `as_of` 与 `t0/`、`t1/` 一致）。不要调用 `_ingest_eval_corpus` 或 `load_trap_corpus`（后者跳过这道断言）。RET-01.1 的检查器同样用 `load_corpus`，跑分前的 `--check-only` 已经覆盖这道门。

x1 需要而旧函数没有的部分写在新模块：

- 按 qtype 与按 trap+adversarial 分桶的 R@10、MRR@10
- multi_hop 全命中：该题每一个 relevant id 都出现在 top 10
- 干扰命中@10：任一 `distractors` id 出现在 top 10 的题占比
- hybrid 相对 bm25 的逐题胜 / 平 / 负（比的是该题 R@10）
- 查询延迟：样本是 `time.perf_counter` 的秒差。p95 直接调用 `_p95_ms`（内部乘 1000 得到毫秒）。p50 用同一排序与 `ceil` 取 0.50 分位，再乘 1000。不要把已经是毫秒的数再送进 `_p95_ms`
- 模式诚实：dense 列的 `last_retrieval_mode` 只能是 `dense`，hybrid 列只能是 `hybrid`。口径同 `run_arm_compare` 里的 `modes_seen`
- `arm_pass_line` 写入报告的「参考」一节。它失败时进程仍可退出 0。hybrid 落后不是脚本错误

`scripts/run_retrieve_x1.py`（同样自行把 `src` 插入 `sys.path`）。参数名与 RET-01.6 的命令一致，不要另起一套：

- `--corpus` 默认 `data/exp/x1/corpus`；`--traps` 默认 `data/exp/x1/traps`；`--questions` 默认 `data/eval/retrieve_x1.json`；`--config` 必填
- `--check-only`：只跑 RET-01.1 的检查。给出 `--prereg` 时只解析这三行并与现算指纹比较，忽略文件里的其他 hex：`corpus_aggregate_sha256:`、`questions_aggregate_sha256:`、`config_sha256:`（口径同 RET-01.4）。不读取 `owner_freeze`（那是 RET-01.6 的门）。不加载向量，不写臂报告
- `--estimate-only`：在任何 `embed_texts` 之前，按缓存未命中的字符数打印 `uncached_chars`、`est_tokens = uncached_chars / 1.39`、`est_cny = est_tokens / 1000000 * 0.5`，然后退出。`est_cny` 大于配置里的 `budget_cny_max` 时退出非 0。本票用假缓存做单测，不对真实 x1 语料发请求
- 正式模式（留给 RET-01.6，本票只做参数拒绝与假向量单测）：`--dense-db`、`--cache`、`--out`、`--prereg`。`--dense-db` 等于 `data/dense/index.sqlite` 时退出非 0。正式模式必须先跑过同一进程内的估算，估算超预算则不调用 `embed_texts`
- 查询向量只走 `embed_cache`。禁止再调用 `_cached_query_embedder`
- `--out` 下写 `retrieve-x1-arm-compare.md` 与同名 `.json`。行必须包含「总体」「lexical」「paraphrase」「multi_hop」「trap+adversarial」
- 不调用 `python -m freshlatch.eval`，不调用 `rerank_lexical`

### 计分范围

主指标与护栏分开。不改 `sqlite_store.retrieve` 的 `as_of` 过滤，不改 `PRODUCTION_RETRIEVAL_MODE`。

- R@10、MRR@10、干扰命中@10、逐题胜平负、multi_hop 全命中：只统计 `score_role` 缺省或为 `arm` 的题。`score_role: guardrail` 的跨快照旧版题不进这些数
- 护栏单独输出：每道 guardrail 题是 T1 查询，返回列表里 `as_of` 为 T0 的块数必须为 0 才算过。护栏失败不改写主 R@10，但要在报告里单独成行。单测用假向量覆盖「T1 池里不出现 T0 块则过、混进 T0 块则不过」
- **conflict-pair ordering accuracy**：题上有 `conflict_pair.in_force` 与 `conflict_pair.superseded`（同一 `as_of`）时，现行条排名严格高于被取代条的配对占比。被取代条不在返回列表、现行条在，算正确；两者都不在，或只有被取代条在，算不正确。报告单列，不并进 R@10。这种题若 `score_role` 为 `arm`，仍同时进入主指标
- 可选诊断：提供一个缺省关闭的开关，关掉本次 x1 跑分的 `as_of` 过滤。缺省不跑。跑了则写到单独文件或主报告的单独一节，不得覆盖主 R@10 / MRR。单测只断言缺省不跑、跑了则与主数字分开。不发网络。诊断不改生产检索
- 三个子集与 0.2 / 0.35 / 0.5 的门命中数是 RET-01.4 / RET-01.6 的报告义务。本票的逐题 JSON 要带上足够字段（qtype、evidence 序、`score_role`），让 RESULT 能按 PREREG 划分子集。子集本身的「稳健」标签不在本票用假向量宣布

单测建一个 tmp 小语料，用与 `tests/unit/test_i3_hard_gold.py` 中 `_write_dummy_dense` 相同的手法写占位 vec（`pack_vec`，非全零，dim 可以是 8）。不调用 `embed_texts`。断言分型聚合、全命中、干扰命中、模式诚实，以及 `PRODUCTION_RETRIEVAL_MODE == "bm25"`。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 新单测与不触网的既有检索单测，When `python -m compileall -q src` 且 `python -m pytest tests/unit/test_retrieve_x1.py tests/unit/test_x1_checks.py tests/unit/test_hybrid_rrf.py tests/unit/test_dense_arm.py -q`，Then 退出码 0。不要把 `tests/unit/test_i3_hard_gold.py` 放进这条命令。`test_hard_arm_compare_same_corpus_as_a0` 自 `833af15` 起在无 `DASHSCOPE_API_KEY` 的 CI 里失败，归 `tasks/CI-01.md`，不是本票。
  2. Given tmp fixture 与一份含正确指纹的临时 PREREG，When `python scripts/run_retrieve_x1.py --check-only --corpus <tmp>/corpus --traps <tmp>/traps --questions <tmp>/questions.json --config <tmp>/config.json --prereg <tmp>/PREREG.md`，Then 退出码 0。指纹被改一个字符后同一命令退出非 0。
  3. Given `--dense-db data/dense/index.sqlite`，When 解析参数，Then 退出非 0，且该文件的 mtime 不变（测试不要真的去碰仓库里的这个路径；用字符串比较加一个「若路径等于生产默认库则拒绝」的纯函数即可）。
  4. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/__main__.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/store/embeddings.py src/freshlatch/store/ingest.py src/freshlatch/llm.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。开工前与收工后各跑 `python -c "import hashlib; from pathlib import Path; p=Path('data/dense/index.sqlite'); print('absent' if not p.is_file() else hashlib.sha256(p.read_bytes()).hexdigest(), 'absent' if not p.is_file() else p.stat().st_mtime)"`，两行相同。
  5. Given tmp 假向量语料里有一道 `score_role: guardrail` 的 T1 题、一道带 `conflict_pair` 的同快照题，When 跑分函数，Then 护栏题不进入主 R@10 的分母；T1 结果里出现 T0 块则护栏失败；conflict-pair ordering accuracy 单独给出，且不改主 R@10。缺省不跑关掉 `as_of` 的诊断。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/eval/retrieve_eval.py#run_arm_compare,recall_at_k,mrr_at_k,arm_pass_line,_p95_ms,_attach_vecs`；`src/freshlatch/store/ingest.py#load_corpus`；`tests/unit/test_i3_hard_gold.py#_write_dummy_dense`（只借鉴占位 vec 的写法，不把该测试文件放进验收命令）；`src/freshlatch/store/embed_cache.py`（RET-01.2）；`src/freshlatch/eval/x1_checks.py`（RET-01.1）
  - Pin: 仓内现行文件（main@`18b5172`）
  - What changed: 新模块增加分型、全命中、干扰命中、延迟与成本列；查询嵌入走 `embed_cache`；两个目录都用 `load_corpus`。主 R@10 不含护栏题。另计护栏通过/失败与 conflict-pair ordering accuracy。关掉 `as_of` 的诊断缺省不跑，且不覆盖主数字
  - Why not copy as-is: `run_arm_compare` 只出单一 R@10，查询嵌入走 `_cached_query_embedder`，traps 经 `load_trap_corpus` 不核对 `as_of`。直接跑还会碰到默认的 `data/dense/index.sqlite`
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
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`src/freshlatch/eval/retrieve_eval.py`、`src/freshlatch/eval/__main__.py`、`src/freshlatch/store/embeddings.py`、`src/freshlatch/store/ingest.py`、`src/freshlatch/llm.py`、`src/freshlatch/store/base.py`、`docs/evidence/retrieve-x1/PREREG.md`（若已存在）、`tests/unit/test_i3_hard_gold.py`

### Provenance status
- result: pass
- notes: 上列 `retrieve_eval` 与 `_write_dummy_dense` 符号在 `18b5172` 存在。新模块 import 打分函数，不改原文件，不调用 `_cached_query_embedder`。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-06 | RET-01.5 | blocked | 等 RET-01.1 与 RET-01.2。计分范围已按护栏 / conflict-pair 分开。不要等语料才写脚本；不要在本票出真分`

## Blocked by
- RET-01.1
- RET-01.2
