# TASK / ticket — RET-01.2

## Ticket
- **ID**: RET-01.2
- **Title**: `spike(eval): x1 草稿生成、抽检标记与 embedding 内容哈希缓存`
- **Paths**:
  - 新建 `src/freshlatch/store/embed_cache.py`
  - 新建 `scripts/gen_x1_drafts.py`
  - 新建 `tests/unit/test_x1_embed_cache.py`
  - 改 `scripts/build_dense_index.py`（只加可选参数；不传参时路径与嵌入调用方式保持现状）
- **Executor**: `/implement`（单测注入假客户端，零网络）
- **先读**: `tasks/RET-01.md`、`tasks/RET-01.1.md`

## 行为

### 缓存

`embed_cache.py` 包一层 `embed_texts`，不改 `src/freshlatch/store/embeddings.py`。

- 键 = `sha256_hex((model + "\n" + str(dim) + "\n" + text).encode("utf-8"))`，用 `freshlatch.store.checksum.sha256_hex`
- 值用 `pack_vec` / `unpack_vec` 存进**单独**的 sqlite 文件，表名 `embed_cache`。不 `ALTER`、不打开 `data/dense/index.sqlite`
- `dim` 由调用方传入（x1 为 1024）。model 或 dim 任一变化即不命中
- 命中不调用 `embed_texts`。未命中才调用，并把返回向量写入缓存
- 单测注入假 `embed_texts`，断言调用次数

### 重建脚本的可选参数

`build_dense_index.py` 增加可选 `--corpus`、`--traps`、`--db`、`--report`、`--cache`。

- 五个都不传：`CORPUS` / `TRAPS` / `DB` / `REPORT` 仍是现在的模块级常量；`BATCH` 仍是 8；**不**打开缓存；仍直接调用 `embed_texts`。这是 #259 那条命令的路径
- 传入 `--db` 且该路径不是默认 `DB`：必须同时传入 `--cache`，否则退出非 0。避免 x1 索引在无缓存的情况下另建一套库
- 默认 `DB`（`data/dense/index.sqlite`）在任何参数组合下都不得被写入。单测用 tmp_path
- 抽出「解析参数 → 路径」的函数供单测调用，单测不调用 `embed_texts`，不请求网络

### 草稿与抽检

`scripts/gen_x1_drafts.py`：

- 复用 `LLMClient` 与 `DecodingParams`，不改 `src/freshlatch/llm.py`
- 生成文档与题目草稿只用 `draft_model`（锁死 `qwen-flash`）。temperature 与 seed 从配置读取。二者任一为 `null` 或未传入：退出非 0，禁止落到 `DecodingParams` 的 temperature 0 默认
- 抽检子命令只用 `flag_model`（`qwen-plus`）且 `flag_thinking` 必须为 false。输出写到调用方指定的 sidecar JSON（建议路径 `data/exp/x1/flag-notes.json`，由人步骤决定是否入库）。sidecar 不得包含 `relevant` 的改写结果。脚本不得写 `data/eval/retrieve_x1.json`
- 没有 `--out` 时退出非 0。`--out` 不得位于 `data/corpus`、`data/traps`、`data/eval`、`docs/evidence/hard-gold-arm`、`reports` 之下
- 草稿落盘前调用 RET-01.1 的检查函数，把违规打印出来。检查失败仍只写 `--out` 里的草稿，不写正式语料目录
- 单测注入假 `LLMClient`，断言：未传 temperature 时不调用模型；抽检结果不含 gold 字段写入

托管模型的 seed 不作为复现手段。本票不声称重跑脚本会得到同一篇草稿。

## Agent Guards
- **Blast**: none（新 sqlite 文件是缓存，不改产品库 schema，不碰 auth）
- **Trust**: Watch（改了既有 `scripts/build_dense_index.py`，按仓库规则不用 Auto）
- **Acceptance**:
  1. Given 单测，When `python -m compileall -q src` 且 `python -m pytest tests/unit/test_x1_embed_cache.py tests/unit/test_x1_checks.py -q`，Then 退出码 0。
  2. Given 不传参解析出的路径，When 与模块常量比较，Then corpus/traps/db/report 相同，且 cache 为空（不启用）。
  3. Given 同一文本，When 缓存键的 model 或 dim 改变，Then 假 `embed_texts` 被再次调用。
  4. Given `draft_temperature` 为 `null`，When 运行生成脚本的参数解析，Then 退出非 0 且假客户端调用次数为 0。
  5. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/store/embeddings.py src/freshlatch/llm.py src/freshlatch/eval/__main__.py src/freshlatch/eval/retrieve_eval.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps data/dense/index.sqlite reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。`scripts/build_dense_index.py` 的 diff 只有可选参数与「默认不启用缓存」的分支。
- **Provenance**:
  - Kind: adapt
  - Source: `scripts/build_dense_index.py#_load_pairs,main`；`src/freshlatch/store/embeddings.py#embed_texts,EMBED_MODEL`；`src/freshlatch/store/pipeline.py#pack_vec,unpack_vec`；`src/freshlatch/store/checksum.py#sha256_hex`；`src/freshlatch/llm.py#LLMClient,DecodingParams,TokenUsage`；`src/freshlatch/eval/x1_checks.py`（RET-01.1 新建，本票只调用）
  - Pin: 仓内现行文件（main@`18b5172`）；`x1_checks.py` 以 RET-01.1 落地后的文件为准
  - What changed: 重建脚本增加可选路径与可选缓存；新模块按 model+dim+文本哈希缓存向量；新脚本只向 `--out` 写草稿与抽检 sidecar
  - Why not copy as-is: `_load_pairs` / `main` 把路径写死到 `data/corpus`、`data/traps`、`data/dense/index.sqlite`、`reports/dense-rebuild.md`。直接复用会覆盖 #259 证据。`embed_texts` 不回传 usage，也不接受缓存路径
  - License note: 仓内代码。仓库根目录无 `LICENSE` 文件（`README.md` 已说明）
- **Tests**: added（`tests/unit/test_x1_embed_cache.py`）
- **Rollback**: 删除三个新文件；还原 `scripts/build_dense_index.py`
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 与生产默认臂（保持 `bm25`）
  - `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 的冻结结论，以及同目录 RERUN 证据（`RERUN-20261003.md`、`RERUN-20261003-259.md`）
  - GitHub issue #260
  - `data/eval/retrieve_hard_gold.json`（`hard-c4-paraphrase`、`hard-c6-paraphrase` 只作背景，不改该文件）
  - `data/dense/index.sqlite`
  - `reports/retrieve-hard-gold-*`
  - ADR-0033 正文（`docs/adr/0033-hard-gold-过线与改臂授权闸.md`）
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`src/freshlatch/eval/__main__.py`、`src/freshlatch/store/embeddings.py`、`src/freshlatch/llm.py`

### Provenance status
- result: pass
- notes: adapt 源均在 `18b5172` 上核对过符号名。`x1_checks.py` 尚不存在，依赖 RET-01.1 先落地。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-06 | RET-01.2 | blocked | 等 RET-01.1 合并后再 /before-implement`

## Blocked by
- RET-01.1
