# TASK / ticket — RET-01.3

## Ticket
- **ID**: RET-01.3
- **Title**: `spike(eval): x1 混合语料与分型金标人审入库`
- **Paths**:
  - 新建 `data/exp/x1/corpus/t0/*.md`、`data/exp/x1/corpus/t1/*.md`
  - 新建 `data/exp/x1/traps/t0/*.md`、`data/exp/x1/traps/t1/*.md`
  - 新建 `data/exp/x1/config.json`
  - 新建 `data/exp/x1/SOURCES.md`
  - 新建 `data/exp/x1/flag-notes.json`（模型疑点，非金标）
  - 新建 `data/eval/retrieve_x1.json`
- **Executor**: **人步骤。禁止 `/implement`。** Agent 可以按 RET-01.2 的脚本出草稿，不得把草稿直接写成 gold，不得代填 `relevant` / `distractors` / `qtype`。
- **先读**: `tasks/RET-01.md` 语料来源表、许可白名单、主人待定三项

## 人要交什么

1. 主人先定两件事，未定之前停在这一步：
   - `decontam_8gram_max` 的数值（候选 0.5 尚未批准）。写入 `config.json`，禁止留 `null`。
   - P1 逐条摘录清单（条号、发文机关官网 URL、检索日期）。允许在清单阶段否掉草稿里的某一条，或按 RET-01 的未决项改 P2 的统计粒度；改动写进 `SOURCES.md`，不改 RET-01 的硬门槛。
2. 按 RET-01 来源表准备语料。frontmatter、`## pN`、`load_corpus` 的 t0/t1 镜像、`source_type` 三值，都按父票。合成正文不得整段改写版权原文。P1 只放已经列入 `SOURCES.md` 的官网正文条文。
3. 题目进 `data/eval/retrieve_x1.json`。字段与地板以 RET-01.1 的检查器为准（每型 ≥30，n≥90，trap/adversarial ≥30%，multi_hop 跨 doc，chunk ≥600，合成 ≥60%，公开 ≤40%，美政府作品与 CC0 / CC BY 的 chunk 数为 0）。
4. `qwen-plus`（非思考）只通过 RET-01.2 的抽检子命令把疑点写入 `flag-notes.json`。人读疑点后改题或维持。gold 以人写入的 JSON 为准。
5. 另一人（或另一会话，且不是写下 gold 的同一次操作）复核至少 20% 的题。复核比例、复核范围、日期写进 `SOURCES.md` 末节，供 RET-01.4 抄进 PREREG。
6. temperature 与 seed 用这次生成实际使用的值写入 `config.json`。不要依赖模型默认。

`config.json` 的其余键等于 RET-01「配置键」里的已锁值。免费额度是否还在，不影响本步；不要为了省钱换模型或换维度。

已知错标 `hard-c4-paraphrase`、`hard-c6-paraphrase` 说明旧 hard 集不能当锚点质量的样板。不要去改 `retrieve_hard_gold.json`。新题的锚必须和块内事实一致。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given `config.json` 里 `decontam_8gram_max` 已是主人写下的数字，When `python scripts/check_x1.py --corpus data/exp/x1/corpus --traps data/exp/x1/traps --questions data/eval/retrieve_x1.json --config data/exp/x1/config.json`，Then 退出码 0，输出中 chunk ≥600、每个 qtype ≥30、trap/adversarial ≥30%、去污染命中 = 0、许可违规 = 0。
  2. Given `data/exp/x1/SOURCES.md`，When 人阅读，Then 每个 public 文件有官网 URL、发布者、检索日期；P1 条号可在该 URL 正文中找到；P2 数字与所引统计局页面一致，叙述标明「引自国家统计局网站 www.stats.gov.cn」。
  3. Given `flag-notes.json` 与 `retrieve_x1.json`，When 对比，Then 没有任何一道题的 `relevant` 被脚本从 sidecar 自动覆盖。金标文件的作者是人。
  4. Given 本票 diff，When `git diff --stat main -- src docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps data/dense/index.sqlite reports`，Then 输出为空。
- **Tests**: waived（人入库；检查器的单测在 RET-01.1。本票用 `scripts/check_x1.py` 验收，不新增 pytest）
- **Rollback**: 删除 `data/exp/x1/` 与 `data/eval/retrieve_x1.json`
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 与生产默认臂（保持 `bm25`）
  - `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 的冻结结论，以及同目录 RERUN 证据（`RERUN-20261003.md`、`RERUN-20261003-259.md`）
  - GitHub issue #260
  - `data/eval/retrieve_hard_gold.json`（`hard-c4-paraphrase`、`hard-c6-paraphrase` 只作背景，不改该文件）
  - `data/dense/index.sqlite`
  - `reports/retrieve-hard-gold-*`
  - ADR-0033 正文（`docs/adr/0033-hard-gold-过线与改臂授权闸.md`）
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`src/**`

### Provenance status
- result: pass
- notes: 新产品数据，不改既有代码。公开条文清单仍待主人，故本票保持 blocked。

### Evidence *(after Matt `/implement`)*
- typecheck: n/a（人步骤，不改 src）
- tests: waived
- paths:

## Handoff
`2026-10-06 | RET-01.3 | blocked | 等 RET-01.2，并等主人锁定阈值与条文清单。不要 /implement`

## Blocked by
- RET-01.1
- RET-01.2
- 主人决策：`decontam_8gram_max`（0.5 仅为未批准候选）
- 主人决策：P1 逐条摘录清单
