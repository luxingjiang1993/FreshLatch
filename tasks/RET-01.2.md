# TASK / ticket — RET-01.2

## Ticket
- **ID**: RET-01.2
- **Title**: `spike(eval): x1 embedding 内容哈希缓存与重建脚本可选路径`
- **Paths**:
  - 新建 `src/freshlatch/store/embed_cache.py`
  - 新建 `tests/unit/test_x1_embed_cache.py`
  - 改 `scripts/build_dense_index.py`（只加可选参数；不传参时的路径常量与「直接调用 `embed_texts`、不打开缓存」保持为代码里的旧行为）
- **Executor**: `/implement`。本票不得发起真实 DashScope 调用，不得执行不带参数的 `python scripts/build_dense_index.py`。
- **先读**: `tasks/RET-01.md`。草稿生成在 RET-01.7，不在本票。

`RET-01.2a` 这个名字不符合工单 ID 正则，本票就是缓存与重建参数那一半。

## 行为

### 缓存

`embed_cache.py` 包一层 `embed_texts`，不改 `src/freshlatch/store/embeddings.py`。

- 键 = `sha256_hex((model + "\n" + str(dim) + "\n" + text).encode("utf-8"))`，用 `freshlatch.store.checksum.sha256_hex`
- 值用 `pack_vec` / `unpack_vec` 存进**单独**的 sqlite 文件，表名 `embed_cache`。不 `ALTER`、不打开 `data/dense/index.sqlite`
- `dim` 由调用方传入（x1 为 1024）。model 或 dim 任一变化即不命中
- 命中不调用 `embed_texts`
- 未命中才调用。返回后先断言 `len(vec) == dim`，不相等则报错并且**不写入**该行。相等才写入
- 单测注入假 `embed_texts`，不读 `DASHSCOPE_API_KEY`，不发网络请求

### 重建脚本的可选参数

`build_dense_index.py` 增加可选 `--corpus`、`--traps`、`--db`、`--report`、`--cache`。

- 五个都不传时，代码仍指向模块级常量 `CORPUS` / `TRAPS` / `DB` / `REPORT`，`BATCH` 仍是 8，不打开缓存，直接调用 `embed_texts`。这是 #259 那条命令的路径。本票的实现会话**不得运行**这条命令
- 调用方显式传入 `--db`，且解析后的路径等于默认 `DB`（`data/dense/index.sqlite`）：退出非 0，不写该文件
- 传入 `--db` 且该路径不是默认 `DB`：必须同时传入 `--cache`，否则退出非 0
- 抽出「解析参数 → 路径」的函数。单测只调用这个函数，**不得调用 `main()`**，不得以空参数跑重建

## Agent Guards
- **Blast**: none（新 sqlite 文件是缓存，不改产品库 schema，不碰 auth）
- **Trust**: Watch（改了既有 `scripts/build_dense_index.py`，按仓库规则不用 Auto）
- **Acceptance**:
  1. Given 单测，When `python -m compileall -q src` 且 `python -m pytest tests/unit/test_x1_embed_cache.py -q`，Then 退出码 0。测试不发 DashScope 请求。
  2. Given 空参数交给路径解析函数（不是 `main()`），When 与模块常量比较，Then corpus/traps/db/report 相同，且 cache 为空（不启用）。
  3. Given 显式 `--db` 等于默认 `DB`，When 解析，Then 拒绝。单测不调用 `main()`。
  4. Given 同一文本，When 缓存键的 model 或 dim 改变，Then 假 `embed_texts` 被再次调用。
  5. Given 假 `embed_texts` 返回的向量长度不等于 `dim`，When 缓存未命中，Then 报错，且缓存文件里没有该键。
  6. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/__main__.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/store/embeddings.py src/freshlatch/store/ingest.py src/freshlatch/llm.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。`scripts/build_dense_index.py` 的 diff 只有可选参数、显式 `--db` 等于默认库时拒绝、以及「无参数时不启用缓存」的代码路径。开工前与收工后各跑 `python -c "import hashlib; from pathlib import Path; p=Path('data/dense/index.sqlite'); print('absent' if not p.is_file() else hashlib.sha256(p.read_bytes()).hexdigest(), 'absent' if not p.is_file() else p.stat().st_mtime)"`，两行相同。
- **Provenance**:
  - Kind: adapt
  - Source: `scripts/build_dense_index.py#_load_pairs,main`；`src/freshlatch/store/embeddings.py#embed_texts,EMBED_MODEL`；`src/freshlatch/store/pipeline.py#pack_vec,unpack_vec`；`src/freshlatch/store/checksum.py#sha256_hex`
  - Pin: 仓内现行文件（main@`18b5172`）
  - What changed: 重建脚本增加可选路径与可选缓存；新模块按 model+dim+文本哈希缓存向量，维度不符不落盘
  - Why not copy as-is: `_load_pairs` / `main` 把路径写死到 `data/corpus`、`data/traps`、`data/dense/index.sqlite`、`reports/dense-rebuild.md`。直接复用会覆盖 #259 证据。`embed_texts` 不接受缓存路径，也不核对维度
  - License note: 仓内代码。仓库根目录无 `LICENSE` 文件（`README.md` 已说明）
- **Tests**: added（`tests/unit/test_x1_embed_cache.py`）
- **Rollback**: 删除 `src/freshlatch/store/embed_cache.py` 与 `tests/unit/test_x1_embed_cache.py`；还原 `scripts/build_dense_index.py`
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 与生产默认臂（保持 `bm25`）
  - `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 的冻结结论，以及同目录 RERUN 证据（`RERUN-20261003.md`、`RERUN-20261003-259.md`）
  - GitHub issue #260
  - `data/eval/retrieve_hard_gold.json`（`hard-c4-paraphrase`、`hard-c6-paraphrase` 只作背景，不改该文件）
  - `data/dense/index.sqlite`
  - `reports/retrieve-hard-gold-*`
  - ADR-0033 正文（`docs/adr/0033-hard-gold-过线与改臂授权闸.md`）
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`src/freshlatch/eval/__main__.py`、`src/freshlatch/eval/retrieve_eval.py`、`src/freshlatch/store/embeddings.py`、`src/freshlatch/store/ingest.py`、`src/freshlatch/llm.py`、`src/freshlatch/store/base.py`

### Provenance status
- result: pass
- notes: adapt 源均在 `18b5172` 上核对过符号名。本票不依赖 RET-01.1。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-06 | RET-01.2 | ready | /before-implement RET-01.2。不要跑无参数重建，不要打真实嵌入接口`

## Blocked by
None (can start immediately).
