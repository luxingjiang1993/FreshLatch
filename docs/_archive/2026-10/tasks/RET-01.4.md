# TASK / ticket — RET-01.4

## Ticket
- **ID**: RET-01.4
- **Title**: `docs(eval): 冻结 x1 预登记 PREREG`
- **Paths**:
  - 新建 `docs/evidence/retrieve-x1/PREREG.md`
- **Executor**: `/implement` 只写这一份文档，指纹行按下面的固定块填写，`owner_freeze` 只能写 `pending`。冻结确认是人步骤：主人把该行改成 `owner_freeze: confirmed` 并合入 `main`。在此之前不得开始 RET-01.6。
- **先读**: `tasks/RET-01.md` 已锁决策与仍开放的主人待定；RET-01.3 入库结果。`owner_freeze` 只能写 `pending`

## 文件必须写明的预锁内容

层身份写在文首：实验 / 冒烟；不报方差；不作统计显著；不是改臂授权；`PRODUCTION_RETRIEVAL_MODE` 仍为 bm25。

判据（先于任何臂分数写死）：

- 分型领先：该型 R@10（hybrid − bm25）≥ `lead_delta`（0.10）为领先；≤ −0.10 为落后；其余持平
- hybrid 不赢是合格归档，不是复跑失败
- `arm_pass_line` 出现在将来的报告里时只作参考，不授权改臂
- 跑分开始后改题、改 `decontam_8gram_max`、改 `lead_delta`、改语料、改 qtype 规则（qtype-kw-v1 的阈值 0.8、停用词表、分词器版本）、改下面的指标归属 = 本预登记作废
- `decontam_8gram_max` 必须写成主人已批准的 **0.2**。比较是严格大于：比例 > 0.2 判污染，等于 0.2 不判。不得写 null，不得用「建议 0.5」代替这个数。0.5 不是正式门

去污染的次要分析，事先写死，跑分后不得加口径：

- 主判据不变：正式配置是 0.2，`check_x1.py` 在正式题集上去污染命中必须为 0。字符 LCS / 问句长度 ≥ 0.8 是 RET-01.1 的复核旗标，不是门
- 三个稳健子集，都在冻结后的正式题集上算，不在看过臂分数之后再挑：
  - 子集 a：8-gram 比例 = 0
  - 子集 b：8-gram 比例 ≤ 0.1
  - 子集 c：字符 LCS(query, relevant 块) / len(query) < 0.8
- 每个子集按 qtype 报 n、三臂 R@10、MRR@10、hybrid − bm25 的 Δ，以及按 `lead_delta` 判出的领先 / 持平 / 落后
- 子集 n ≥ 15，且该 qtype 的领先 / 持平 / 落后与全集一致，才写「稳健」。不一致就写「不稳健」并列出题号，不改主结论。n < 15 只报 n，不称稳健，不报方差。构造阶段希望每个子集都 ≥15；不足是如实记录，不是事后把 0.2 放宽
- 门的松紧：对 RET-01.7 草稿（人改写之前）用 0.2 / 0.35 / 0.5 三份临时 config 跑检查器，报各自命中数。三份临时 config 都不入 `data/exp/x1/config.json`。这组数来自 RET-01.3 写入 `SOURCES.md` 的记录，PREREG 照抄。正式题集按构造应全部 ≤ 0.2，所以在正式题集上再报更松的阈值没有信息量

指标归属，事先写死。陷阱三类的操作化定义（同快照冲突 / 取代 / 未重测）主人尚未签核，PREREG 不得把那三类定义写成已批准。已批准、必须写入的只有：

- 臂对比的 R@10、MRR@10、干扰命中@10、逐题胜平负：只统计 `score_role` 不为 `guardrail` 的题。跨快照旧版陷阱不进这些指标
- 护栏，单独的通过/失败：`score_role: guardrail` 的 T1 查询，对旧快照块的命中数必须为 0。不过即失败。不计入 recall / MRR
- **conflict-pair ordering accuracy**：带 `conflict_pair`（`in_force` 与 `superseded`，同一 `as_of`）的配对里，现行条文排名严格高于被取代条文的占比。被取代条未返回、现行条返回了，算正确；两者都没返回，或只有被取代条返回，算不正确。不并进主 R@10。同快照 hard negative 的例子是令 11 第十四条「2年」与令 16 第九条「3年」，令 16 第十三条规定新规优先
- 可选诊断：关掉 `as_of` 过滤再跑。单独一节。不进主结论。没跑就写「未跑」。主跑的过滤保持打开
- 法规标题不前置进 chunk。三臂同样不做。contextual retrieval 不在本期，不写成某一臂的差异

`as_of` 过滤本身不改。生产臂保持 bm25。

指纹是文件里单独的三行，键名固定，RET-01.5 只解析这三行，不从正文里搜别的 hex：

```text
corpus_aggregate_sha256: <64位小写hex>
questions_aggregate_sha256: <64位小写hex>
config_sha256: <64位小写hex>
owner_freeze: pending
```

主人确认冻结时只把最后一行改成 `owner_freeze: confirmed`。起草会话不得写 `confirmed`。

计算（不改 `checksum.py`）：

- `corpus_aggregate_sha256`：`aggregate_checksum`，文件为 `data/exp/x1/corpus` 与 `data/exp/x1/traps` 下全部 `.md`，`root=data/exp/x1`
- `questions_aggregate_sha256`：`aggregate_checksum`，文件为 `data/eval/retrieve_x1.json`，`root=data/eval`
- `config_sha256`：`sha256_hex` 对 `data/exp/x1/config.json` 的原始字节

并抄录：`decontam_8gram_max` 的已批准数字 **0.2**（不得写 null，不得写「建议 0.5」来代替）、`lead_delta`、`top_k`、`rrf_k`、embed 模型与维度、draft 模型 / temperature / seed、flag 模型与非思考、各 qtype 的 n、trap/adversarial 比例、chunk 数、合成/公开比例、预算帽 ¥10、标注协议（两个独立模型标注者及其身份；主人审核范围：影响打分的分歧行数、抽样比例与种子 20261007、内容修正条数；规则合并的字段与规则版本；A / B 一致率与 κ；审核日期，均来自 `SOURCES.md`）、qtype 规则 qtype-kw-v1（阈值 0.8，分词器 jieba 0.42.1）及各 qtype 的 n、草稿上 0.2 / 0.35 / 0.5 的命中数（来自 `SOURCES.md`）。flk 核对的日期与结论也从 `SOURCES.md` 抄来；SOURCES 里没有这一节就不要冻结。

免费额度与端点是否同价：写「未核实」，不要写成已经抵扣。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given RET-01.3 的语料、题集与配置，When 执行：

```bash
PYTHONPATH=src python -c "from pathlib import Path; from freshlatch.store.checksum import aggregate_checksum, sha256_hex; root=Path('data/exp/x1'); files=sorted((root/'corpus').rglob('*.md'))+sorted((root/'traps').rglob('*.md')); c=aggregate_checksum(files, root=root); q=aggregate_checksum([Path('data/eval/retrieve_x1.json')], root=Path('data/eval')); cfg=sha256_hex(Path('data/exp/x1/config.json').read_bytes()); text=Path('docs/evidence/retrieve-x1/PREREG.md').read_text(encoding='utf-8');
need=[f'corpus_aggregate_sha256: {c}', f'questions_aggregate_sha256: {q}', f'config_sha256: {cfg}', 'owner_freeze: pending'];
missing=[n for n in need if n not in text];
assert not missing, missing; print('prereg-fingerprints-ok')"
```

     Then 退出码 0。文件含 `decontam_8gram_max` 的数字 0.2，且不含 `owner_freeze: confirmed`（那一行等人写、并随后合入 `main`）。起草行保持 `owner_freeze: pending`。
  2. Given 该文件，When `python scripts/check_x1.py --corpus data/exp/x1/corpus --traps data/exp/x1/traps --questions data/eval/retrieve_x1.json --config data/exp/x1/config.json`，Then 退出码 0（正式阈值已是 0.2、去污染命中为 0）。
  3. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/__main__.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/store/embeddings.py src/freshlatch/store/ingest.py src/freshlatch/llm.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。本票新增路径只有 `docs/evidence/retrieve-x1/PREREG.md`。开工前与收工后各跑 `python -c "import hashlib; from pathlib import Path; p=Path('data/dense/index.sqlite'); print('absent' if not p.is_file() else hashlib.sha256(p.read_bytes()).hexdigest(), 'absent' if not p.is_file() else p.stat().st_mtime)"`，两行相同。
  4. Given 该文件正文，When 人阅读，Then 写明三个子集（比例 = 0、比例 ≤ 0.1、LCS < 0.8）与 n≥15 才称稳健的规则，写明草稿上 0.2 / 0.35 / 0.5 的命中数，写明跨快照旧版只进护栏、conflict-pair ordering accuracy 不并进主 R@10、`as_of` 关闭的诊断不进主结论。陷阱三类操作化定义没有被写成已批准。LCS ≥ 0.8 被写成复核旗标，不是门。写明 qtype 按 qtype-kw-v1 计算（关键词覆盖率 ≥ 0.8 或 r8 > 0.2 → lexical；multi_hop 结构 → multi_hop；其余 paraphrase），且 8-gram 只作去污染门。
- **Tests**: waived（纯文档；指纹用已有 checksum 函数核对，不新增 pytest）
- **Rollback**: 删除 `docs/evidence/retrieve-x1/PREREG.md`。若已有臂分数，回滚预登记等于宣布该轮分数无效，须在 RESULT 写明
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 与生产默认臂（保持 `bm25`）
  - `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 的冻结结论，以及同目录 RERUN 证据（`RERUN-20261003.md`、`RERUN-20261003-259.md`）
  - GitHub issue #260
  - `data/eval/retrieve_hard_gold.json`（`hard-c4-paraphrase`、`hard-c6-paraphrase` 只作背景，不改该文件）
  - `data/dense/index.sqlite`
  - `reports/retrieve-hard-gold-*`
  - ADR-0033 正文（`docs/adr/0033-hard-gold-过线与改臂授权闸.md`）
  - 同时不改：`data/corpus/**`、`data/traps/**`、`data/exp/x1/**`、`data/eval/retrieve_x1.json`、`reports/dense-rebuild.md`、`src/freshlatch/eval/__main__.py`、`src/freshlatch/eval/retrieve_eval.py`、`src/freshlatch/store/embeddings.py`、`src/freshlatch/store/ingest.py`、`src/freshlatch/llm.py`、`src/freshlatch/store/base.py`（指纹不一致时退回 RET-01.3，不要在本票改题）

### Provenance status
- result: pass
- notes: 新文档。指纹函数是既有 `aggregate_checksum` / `sha256_hex`，本票不改该模块，故不单列 adapt。

### Evidence *(after Matt `/implement`)*
- typecheck: n/a
- tests: waived
- paths:

## Handoff
`2026-10-06 | RET-01.4 | blocked | 等 RET-01.3 入库。正式阈值抄 0.2。起草只能写 owner_freeze: pending`

## Blocked by
- RET-01.3
