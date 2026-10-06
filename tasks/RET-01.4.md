# TASK / ticket — RET-01.4

## Ticket
- **ID**: RET-01.4
- **Title**: `docs(eval): 冻结 x1 预登记 PREREG`
- **Paths**:
  - 新建 `docs/evidence/retrieve-x1/PREREG.md`
- **Executor**: `/implement` 只写这一份文档，指纹行按下面的固定块填写，`owner_freeze` 只能写 `pending`。冻结确认是人步骤：主人把该行改成 `owner_freeze: confirmed` 并合入 `main`。在此之前不得开始 RET-01.6。
- **先读**: `tasks/RET-01.md` 已锁决策与主人待定；RET-01.3 入库结果

## 文件必须写明的预锁内容

层身份写在文首：实验 / 冒烟；不报方差；不作统计显著；不是改臂授权；`PRODUCTION_RETRIEVAL_MODE` 仍为 bm25。

判据（先于任何臂分数写死）：

- 分型领先：该型 R@10（hybrid − bm25）≥ `lead_delta`（0.10）为领先；≤ −0.10 为落后；其余持平
- hybrid 不赢是合格归档，不是复跑失败
- `arm_pass_line` 出现在将来的报告里时只作参考，不授权改臂
- 跑分开始后改题、改 `decontam_8gram_max`、改 `lead_delta`、改语料 = 本预登记作废

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

并抄录：`decontam_8gram_max` 的**已批准数字**（不得写 null，不得写「建议 0.5」来代替主人的数）、`lead_delta`、`top_k`、`rrf_k`、embed 模型与维度、draft 模型 / temperature / seed、flag 模型与非思考、各 qtype 的 n、trap/adversarial 比例、chunk 数、合成/公开比例、预算帽 ¥10、第二人复核 ≥20% 的范围与日期（来自 `SOURCES.md`）。

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

     Then 退出码 0。文件含配置里的 `decontam_8gram_max` 数字，且不含 `owner_freeze: confirmed`（那一行等人写、并随后合入 `main`）。
  2. Given 该文件，When `python scripts/check_x1.py --corpus data/exp/x1/corpus --traps data/exp/x1/traps --questions data/eval/retrieve_x1.json --config data/exp/x1/config.json`，Then 退出码 0（阈值已锁、去污染命中为 0）。
  3. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/__main__.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/store/embeddings.py src/freshlatch/store/ingest.py src/freshlatch/llm.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。本票新增路径只有 `docs/evidence/retrieve-x1/PREREG.md`。开工前与收工后各跑 `python -c "import hashlib; from pathlib import Path; p=Path('data/dense/index.sqlite'); print('absent' if not p.is_file() else hashlib.sha256(p.read_bytes()).hexdigest(), 'absent' if not p.is_file() else p.stat().st_mtime)"`，两行相同。
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
`2026-10-06 | RET-01.4 | blocked | 等 RET-01.3 入库且阈值已是主人写下的数字`

## Blocked by
- RET-01.3
