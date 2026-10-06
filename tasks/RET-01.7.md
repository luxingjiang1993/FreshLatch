# TASK / ticket — RET-01.7

## Ticket
- **ID**: RET-01.7
- **Title**: `spike(eval): x1 草稿生成与 qwen-plus 抽检标记`
- **Paths**:
  - 新建 `scripts/gen_x1_drafts.py`
  - 新建 `tests/unit/test_x1_drafts.py`
- **Executor**: `/implement`。本票不得发起真实 DashScope 调用。单测注入假客户端。
- **先读**: `tasks/RET-01.md`、`tasks/RET-01.1.md`

这是评审里的「RET-01.2b」。`RET-01.2b` 不符合 `^[A-Z]+-[0-9]+(\.[0-9]+)?$`，所以用 RET-01.7。缓存与重建参数在 RET-01.2，本票不改 `build_dense_index.py`。

`qwen-plus` 非思考离线抽检是主人批准的、对 `docs/spec/06-护栏预算与成本.md` §6.5「开发期统一 qwen-flash」的例外。只标记疑点，不进入 Lead 循环，不写 gold。

## 行为

`scripts/gen_x1_drafts.py` 把 `src` 插入 `sys.path`（对齐 `scripts/build_dense_index.py` 文件头）：

- 复用 `LLMClient` 与 `DecodingParams`，不改 `src/freshlatch/llm.py`
- 生成文档与题目草稿只用 `draft_model`（锁死 `qwen-flash`）。temperature 与 seed 从配置读取。二者任一为 `null` 或未传入：退出非 0，禁止落到 `DecodingParams` 的 temperature 0 默认
- 抽检子命令只用 `flag_model`（`qwen-plus`）且 `flag_thinking` 必须为 false。输出写到调用方指定的 sidecar JSON（建议路径 `data/exp/x1/flag-notes.json`，由人步骤决定是否入库）。sidecar 不得包含对 `relevant` 的改写。脚本不得写 `data/eval/retrieve_x1.json`
- 没有 `--out` 时退出非 0。`--out` 不得位于 `data/corpus`、`data/traps`、`data/eval`、`docs/evidence/hard-gold-arm`、`reports` 之下
- 草稿落盘前调用 RET-01.1 的检查函数，把违规打印出来。检查失败仍只写 `--out` 里的草稿，不写正式语料目录
- 单测注入假 `LLMClient`，断言：未传 temperature 时不调用模型；抽检结果不含 gold 字段写入；测试进程不发 HTTP

托管模型的 seed 不作为复现手段。本票不声称重跑脚本会得到同一篇草稿。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 单测，When `python -m compileall -q src` 且 `python -m pytest tests/unit/test_x1_drafts.py tests/unit/test_x1_checks.py -q`，Then 退出码 0。无 DashScope 请求。
  2. Given `draft_temperature` 为 `null`，When 运行生成脚本的参数解析，Then 退出非 0 且假客户端调用次数为 0。
  3. Given 抽检子命令与假 `qwen-plus` 客户端，When 写出 sidecar，Then 文件里没有被写成 gold 的 `relevant`，且请求记录里的模型名是 `qwen-plus`、思考开关为关。
  4. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/__main__.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/store/embeddings.py src/freshlatch/store/ingest.py src/freshlatch/llm.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。开工前与收工后各跑 `python -c "import hashlib; from pathlib import Path; p=Path('data/dense/index.sqlite'); print('absent' if not p.is_file() else hashlib.sha256(p.read_bytes()).hexdigest(), 'absent' if not p.is_file() else p.stat().st_mtime)"`，两行相同。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/llm.py#LLMClient,DecodingParams,TokenUsage`；`src/freshlatch/eval/x1_checks.py`（RET-01.1 新建，本票只调用）
  - Pin: `llm.py` 为 main@`18b5172`；`x1_checks.py` 以 RET-01.1 落地后的文件为准
  - What changed: 新脚本只向 `--out` 写草稿，抽检子命令只写 sidecar
  - Why not copy as-is: 仓内没有「生成 x1 草稿」的入口。`DecodingParams` 的 temperature 默认 0 不能被本脚本悄悄沿用
  - License note: 仓内代码。仓库根目录无 `LICENSE` 文件
- **Tests**: added（`tests/unit/test_x1_drafts.py`）
- **Rollback**: 删除本票两个新文件
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 与生产默认臂（保持 `bm25`）
  - `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 的冻结结论，以及同目录 RERUN 证据（`RERUN-20261003.md`、`RERUN-20261003-259.md`）
  - GitHub issue #260
  - `data/eval/retrieve_hard_gold.json`（`hard-c4-paraphrase`、`hard-c6-paraphrase` 只作背景，不改该文件）
  - `data/dense/index.sqlite`
  - `reports/retrieve-hard-gold-*`
  - ADR-0033 正文（`docs/adr/0033-hard-gold-过线与改臂授权闸.md`）
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`src/freshlatch/eval/__main__.py`、`src/freshlatch/eval/retrieve_eval.py`、`src/freshlatch/store/embeddings.py`、`src/freshlatch/store/ingest.py`、`src/freshlatch/llm.py`、`src/freshlatch/store/base.py`、`scripts/build_dense_index.py`

### Provenance status
- result: pass
- notes: `LLMClient` 符号在 `18b5172` 存在。`x1_checks.py` 依赖 RET-01.1。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-06 | RET-01.7 | blocked | 等 RET-01.1。不要打真实接口`

## Blocked by
- RET-01.1
