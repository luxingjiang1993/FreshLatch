# TASK / ticket — RET-01.1

## Ticket
- **ID**: RET-01.1
- **Title**: `spike(eval): x1 许可、8-gram 去污染与题集结构检查`
- **Paths**:
  - 新建 `src/freshlatch/eval/x1_checks.py`
  - 新建 `scripts/check_x1.py`
  - 新建 `tests/unit/test_x1_checks.py`
- **Executor**: `/implement`（零 LLM，零网络）
- **先读**: `tasks/RET-01.md` 的已锁决策、配置键、许可白名单

本票只做可执行检查。不造语料，不跑三臂，不写 PREREG。

## 行为

`x1_checks.py` 提供纯函数。`scripts/check_x1.py` 把 `src` 插入 `sys.path`（写法对齐 `scripts/build_dense_index.py` 文件头），然后调用这些函数。CLI：

```bash
python scripts/check_x1.py --corpus <dir> --traps <dir> --questions <json> --config <json>
```

退出码：0 通过；1 有违规；2 配置里 `decontam_8gram_max` 缺键或为 JSON `null`（阈值未锁，不是违规样本）。打印各 qtype 的 n、trap/adversarial 比例、chunk 数、合成/公开比例、去污染命中数、许可违规数。

### 8-gram

1. 清洗：删掉 Unicode 类别 P（标点）与 Z（分隔符，含空白）。不做大小写折叠，不做繁简转换。
2. 8-gram 是清洗后字符串上连续 8 个 Unicode 码位的滑窗。用字符，不用 jieba，不用 UTF-8 字节。
3. 集合口径的重合率 = query 的 8-gram 里、出现在任一 relevant 块清洗正文中的比例。
4. 清洗后 query 短于 8 字：8-gram 集合为空，比例检查不触发。
5. 所有 qtype：清洗后的 query 若有长度 ≥8 的连续子串完整出现在任一 relevant 块清洗正文中，判污染（整句 / 长片段照抄）。
6. 仅 `paraphrase` 与 `multi_hop`：重合率 **>** `decontam_8gram_max` 判污染。等于阈值不判污染。
7. `lexical` 只走第 5 条，不走比例阈值。

证据 id 格式与 `chunk_evidence_id` 相同：`{doc_id}#{clause_id}@{as_of}`。正文用 `load_corpus` 装入 corpus 与 traps 两棵目录。

### 题集

每题必填 `id`、`qtype`、`category`、`relevant`、`distractors`、`eval_intent`、`as_of`。

- `qtype` 只允许 `lexical` / `paraphrase` / `multi_hop`
- `category` 只允许 `hard` / `trap` / `adversarial`
- `multi_hop`：`relevant` 至少 2 条，且 `#` 前的 `doc_id` 至少 2 个
- 地板常量（与 RET-01 配置键一致，配置更松则失败）：每型 ≥30，trap+adversarial / n ≥ 0.30，chunk ≥ 600
- 单测用函数参数覆盖规模，以便小 fixture 测得了判定本身；另有一条测试锁定常量数值 30 / 0.30 / 600，防止改常量放水

### 许可与配比

- `license` ∈ {`synthetic`, `PRC-Copyright-Art5`, `US-Gov-17USC105`, `CC0-1.0`, `CC-BY-4.0`}
- `provenance: synthetic` 当且仅当 `license` 为 `synthetic`；其余白名单许可必须 `provenance: public`
- `domain` ∈ {`D0`,`D1`,`D2`,`D3`}；`genre` ∈ {`S1`…`S7`,`P1`,`P2`}
- `PRC-Copyright-Art5` 与 `CC-BY-4.0` 与 `CC0-1.0` 与 `US-Gov-17USC105`：缺 `source_url` 或 `publisher` 或 `retrieved_at` 即违规
- `CC-BY-4.0` 另须非空 `attribution`
- `genre: P2`：须 `license: synthetic`，且 `data_source_url` 非空，`attribution` 含 `www.stats.gov.cn`
- 合成 chunk 占比 ≥ 0.60，公开原文 ≤ 0.40（分母 = corpus + traps 的 chunk 数）
- `US-Gov-17USC105`、`CC0-1.0`、`CC-BY-4.0` 的 chunk 数必须为 0（白名单仍识别它们，以便误标时失败，而不是静默放行）
- `source_type` ∈ {`private`,`public`,`internal`}

未知 frontmatter 键保持由 `parse_document_text` 忽略。本票不改 `ingest.py`。

### 配置

读取 RET-01 列出的键。`lead_delta` 必须是 0.10，`embed_model` / `embed_dim` / `budget_cny_max` / `top_k` / `rrf_k` / `flag_thinking` 必须等于已锁值。`draft_temperature` 与 `draft_seed` 允许为 `null`（生成脚本另拒）；本检查不把它们当成去污染门槛。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 新测试，When `python -m compileall -q src` 且 `python -m pytest tests/unit/test_x1_checks.py -q`，Then 两者退出码 0。测试不读 `DASHSCOPE_API_KEY`，不打开 `data/dense/index.sqlite`。
  2. Given 一份 tmp 语料：paraphrase 的 8-gram 重合率高于配置阈值、一条 multi_hop 只有一个 `doc_id`、一条 `license` 不在白名单、`decontam_8gram_max` 为 `null` 的第二份配置，When 调用检查函数与 CLI，Then 比例与结构违规退出码 1，未锁阈值退出码 2。
  3. Given 清洗后不足 8 字的 lexical query，且没有长度 ≥8 的照抄，When 检查，Then 去污染命中为 0。
  4. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/__main__.py src/freshlatch/store/ingest.py src/freshlatch/store/embeddings.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md`，Then 输出为空。
- **Tests**: added（`tests/unit/test_x1_checks.py`）
- **Rollback**: 删除本票 Paths 里的三个新文件
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 与生产默认臂（保持 `bm25`）
  - `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 的冻结结论，以及同目录 RERUN 证据（`RERUN-20261003.md`、`RERUN-20261003-259.md`）
  - GitHub issue #260
  - `data/eval/retrieve_hard_gold.json`（`hard-c4-paraphrase`、`hard-c6-paraphrase` 只作背景，不改该文件）
  - `data/dense/index.sqlite`
  - `reports/retrieve-hard-gold-*`
  - ADR-0033 正文（`docs/adr/0033-hard-gold-过线与改臂授权闸.md`）
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`src/freshlatch/eval/__main__.py`、`src/freshlatch/store/ingest.py`

### Provenance status
- result: pass
- notes: Paths 全是新文件。Kind 为 new。检查器调用既有 `load_corpus` / `chunk_evidence_id`，不改它们。仓库默认 Trust 仍是 Watch。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-06 | RET-01.1 | ready | /before-implement RET-01.1 后新会话 /implement`

## Blocked by
None (can start immediately).
