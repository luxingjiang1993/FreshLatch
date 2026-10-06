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

退出码：0 通过；1 有违规；2 配置里 `decontam_8gram_max` 缺键或为 JSON `null`（阈值未写入这份配置，不是违规样本）。主人已批准的数值是 **0.2**，但检查器不得在缺键或 `null` 时代入 0.2，也不得代入 0.5。正式 `config.json` 由 RET-01.3 创建并写入 0.2；main 上还没有该文件，本票不创建它。打印各 qtype 的 n（分母不含护栏题）、trap/adversarial 比例、chunk 数、合成/公开比例、去污染命中数、许可违规数、LCS 复核旗标数、护栏题数。另对每道题打一行机器可读记录：`q <id> r8=<float|na> lcs=<float|na> lcs_flag=<0|1> decontam=<0|1> score_role=<arm|guardrail>`，供 RET-01.4 / RET-01.6 做子集，不另开票。

### 去污染

清洗：删掉 Unicode 类别 P（标点）与 Z（分隔符，含空白）。不做大小写折叠，不做繁简转换。比较都在清洗后的字符串上进行。

问句里点法规名是合法的。清洗之后、计算任何重合之前，只从 **query** 删除法规名白名单（块正文不删）。先删更长的名字。白名单是清洗后的字面，无书名号：

- 中华人民共和国公司法
- 数据出境安全评估办法
- 个人信息出境标准合同办法
- 促进和规范数据跨境流动规定
- 个人信息出境认证办法
- 公司法

两套规则不要混用。共享任意一个长度 ≥8 的片段，等于共享任意一个 8-gram；若用「任意 ≥8 字片段」当 lexical 的污染条件，重合率阈值永远不会被用到。白名单要先删掉，否则 paraphrase 的短问句只要带上「数据出境安全评估办法」这种 10 字标题，8-gram 比例就会冲过 0.2，RET-01.3 的「去污染命中 = 0」无法达到。lexical 侧同样先删白名单，再做整段子串判断。

1. `lexical`：删完白名单并清洗后的**整段 query** 长度 ≥8，且这段整 query 是任一 relevant 块清洗正文的子串，判污染。短于 8 字的整段 query 不走这条。`lexical` 不计算 8-gram 重合率，`r8` 记 `na`。
2. `paraphrase` 与 `multi_hop`：只算字符 8-gram 重合率。8-gram 是删完白名单的 query 上连续 8 个 Unicode 码位的滑窗（字符，不是 jieba，不是 UTF-8 字节）。集合口径：query 的 8-gram 里、出现在任一 relevant 块清洗正文中的比例。比例 **>** `decontam_8gram_max` 判污染；等于阈值不判污染。删完白名单后不足 8 字则 8-gram 集合为空，比例检查不触发。这两类不使用「整段 query 是子串」规则。
3. `decontam_8gram_max` 为 `null` 或缺键时，不得代入 0.2，也不得代入 0.5。整份 x1 检查退出码 2。此时仍可单独报告 lexical 整段照抄与 LCS 旗标，但不得用任何缺省阈值给 paraphrase / multi_hop 打去污染分。键有数字时，按该数字做严格大于比较。正式配置的数字是 0.2。0.35 与 0.5 只允许出现在 RET-01.4 规定的临时敏感度配置里，那些文件不写入 `data/exp/x1/config.json`。
4. 字符 LCS 是复核旗标，不是门。对每道 paraphrase / multi_hop，取删完白名单的 query 与任一 relevant 块清洗正文的字符 LCS，除以该 query 的长度，多个 relevant 块取最大比。比例 **≥ 0.8** 则 `lcs_flag=1`。它不计入去污染命中，单独不导致退出码 1。query 长度为 0 时不计算 LCS。LCS 是子序列，不要求连续；纯 Python 即可，题量约 90–120、块约 300 字以内。lexical 的 `lcs` 记 `na`，不参与这面旗。

证据 id 格式与 `chunk_evidence_id` 相同：`{doc_id}#{clause_id}@{as_of}`。正文用 `load_corpus` 装入 corpus 与 traps 两棵目录。

### 题集

臂对比题必填 `id`、`qtype`、`category`、`relevant`、`distractors`、`eval_intent`、`as_of`。可选 `score_role`，缺省当 `arm`。护栏题（`score_role: guardrail`）同样必填这些字段，但 `relevant` 允许为空列表。

- `qtype` 只允许 `lexical` / `paraphrase` / `multi_hop`
- `category` 只允许 `hard` / `trap` / `adversarial`
- `score_role` 只允许 `arm` / `guardrail`。护栏题不进入每型 ≥30、n≥90、trap/adversarial 比例的分母，单独打印题数。护栏题的 `qtype` 不得为 `multi_hop`（`relevant` 可以为空，过不了 multi_hop 的结构门）。去污染仍检查有 `relevant` 的护栏题；`relevant` 为空则跳过该题的去污染与 LCS
- `multi_hop` 两条都是门，命中任一条即结构违规（退出码 1）：
  - `relevant` 至少 2 条，且 `#` 前的 `doc_id` 至少 2 个。同一个 `doc_id` 的 `@T0` 与 `@T1` 不算两个文档
  - 必填 `answer_points`：清洗后非空的字符串列表，至少 2 条。清洗后若存在任何一个 chunk（corpus 与 traps 全部块），其正文同时把每一条要点都包含为子串，判单跳捷径，该题不得作为 multi_hop 通过。要点清洗后变成空串，同样算结构违规
- 地板常量（与 RET-01 配置键一致，配置更松则失败）：每型 ≥30，trap+adversarial / n ≥ 0.30，chunk ≥ 600。这三个数的题数分母都不含护栏题
- 单测用函数参数覆盖规模与阈值，以便小 fixture 测得了判定本身；另有一条测试锁定常量数值 30 / 0.30 / 600，并锁定「配置缺键或 null 时不代入 0.2」。防止改常量放水

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

读取 RET-01 列出的键。`lead_delta` 必须是 0.10，`embed_model` / `embed_dim` / `budget_cny_max` / `top_k` / `rrf_k` / `flag_thinking` 必须等于已锁值。`draft_model` 必须是 `qwen-flash`，`flag_model` 必须是 `qwen-plus`。`draft_temperature` 与 `draft_seed` 允许为 `null`（生成脚本另拒）；本检查不把它们当成去污染门槛。`decontam_8gram_max` 缺键或 `null` 时退出码 2。键存在时只要求它是数字，并按严格大于比较；不在本检查里把非 0.2 的数字当成配置违规，否则 RET-01.4 的 0.35 / 0.5 临时对照跑不了。正式文件必须写 0.2 这一条，由 RET-01.3 的验收卡住。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 新测试，When `python -m compileall -q src` 且 `python -m pytest tests/unit/test_x1_checks.py -q`，Then 两者退出码 0。测试不读 `DASHSCOPE_API_KEY`，不打开 `data/dense/index.sqlite`。
  2. Given 一份 tmp 语料：paraphrase 的 8-gram 重合率高于配置阈值、一条 multi_hop 只有一个 `doc_id`、一条 `license` 不在白名单、`decontam_8gram_max` 为 `null` 的第二份配置，When 调用检查函数与 CLI，Then 比例与结构违规退出码 1，未写入阈值退出码 2，且 null 配置下没有用 0.2 或 0.5 给 paraphrase 打去污染分。
  3. Given relevant 块含「数据出境安全评估办法」，lexical query 为「客户追问数据出境安全评估办法是否仍要走评估」（清洗并删掉白名单名之后，整段并不出现在块里），When 检查，Then 该题去污染命中为 0。另有一条 lexical query 在删掉白名单之后仍等于块内连续 ≥8 字的整段，Then 判污染。
  4. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/__main__.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/store/embeddings.py src/freshlatch/store/ingest.py src/freshlatch/llm.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。开工前与收工后各跑 `python -c "import hashlib; from pathlib import Path; p=Path('data/dense/index.sqlite'); print('absent' if not p.is_file() else hashlib.sha256(p.read_bytes()).hexdigest(), 'absent' if not p.is_file() else p.stat().st_mtime)"`，两行相同。
  5. Given 一条 paraphrase：query 在删白名单之前 8-gram 比例高于配置阈值，删掉「数据出境安全评估办法」之后比例不高于阈值，且没有别的违规，When 检查，Then 退出码 0、去污染命中为 0。单测要有对照，证明白名单确实从 query 删除了。
  6. Given 一条 multi_hop，其全部 `answer_points` 清洗后都出现在同一个 chunk，When 检查，Then 退出码 1。要点分属两个 `doc_id`、且没有任何一个 chunk 同时包含全部要点的对照，这条结构检查通过。同一 `doc_id` 只靠 `@T0` 与 `@T1` 凑两个锚的题，退出码 1。
  7. Given 一条 paraphrase 的字符 LCS / 问句长度 ≥ 0.8，但 8-gram 比例不高于阈值且无其他违规，When 检查，Then 退出码 0，LCS 复核旗标数 ≥ 1，去污染命中数不因该旗标增加。比例恰好等于阈值时不判污染。
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
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`src/freshlatch/eval/__main__.py`、`src/freshlatch/eval/retrieve_eval.py`、`src/freshlatch/store/embeddings.py`、`src/freshlatch/store/ingest.py`、`src/freshlatch/llm.py`、`src/freshlatch/store/base.py`

### Provenance status
- result: pass
- notes: Paths 全是新文件。Kind 为 new。检查器调用既有 `load_corpus` / `chunk_evidence_id`，不改它们。仓库默认 Trust 仍是 Watch。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-06 | RET-01.1 | ready | 已写入批准值 0.2、法规名白名单、LCS 复核旗标、multi_hop 单块捷径。缺键或 null 仍退出码 2，不得代入 0.2。/before-implement RET-01.1 后新会话 /implement`

## Blocked by
None (can start immediately).
