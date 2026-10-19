# TASK / ticket — one slice (copy to `tasks/<ID>.md`)

Matt `/to-tickets` may create this file; `/enrich-tickets` fills **Agent Guards**. Humans mainly set **Trust** and skim Acceptance / Paths / Provenance.

## Ticket
- **ID**: L4-RAG-03
- **Title**: `feat(rag): patch 与有效期过滤先于 RRF`
- **Paths**:
  - `src/freshlatch/store/base.py` 的 `Chunk`（可选 `patch_id` / `valid_from` / `valid_to`；`InMemoryStore.retrieve` 在信任过滤之后调用同一过滤器。不得改 `PRODUCTION_RETRIEVAL_MODE` 那一行）
  - `src/freshlatch/store/pipeline.py` 的 `filter_patch_metadata`（先于 BM25 / dense / RRF）
  - `src/freshlatch/store/sqlite_store.py` 的候选池与三列持久化（不改 `as_of` 的 T0/T1 WHERE）
  - `tests/fixtures/l4_rag_03/`（独立夹具，不放进 `data/exp/x1/`）
  - `tests/unit/test_l4_rag_03_patch_filter.py`
  - `tests/unit/test_active_pack.py` 的 chunks 列集合（补三列）
  - `tests/unit/test_l4_rag_04_hit_scores.py`、`test_retrieve_sufficiency.py`、`test_retrieve_grade.py` 的 diff 锁：不再把 `base.py` 整文件算作不可改。`PRODUCTION_RETRIEVAL_MODE` 字面量仍锁
  - `CONTEXT.md`（`补丁元数据过滤`）
  - `tasks/L4-RAG-03.md`

## Agent Guards
- **Blast**: api
- **Trust**: Watch
- **Acceptance**:
  1. Given 夹具中同一主张有 `patch_id=p1` 与 `patch_id=p2`，查询指定 `p2`，When 检索，Then `p1` 不在候选池。
  2. Given 块的三个新字段皆空，When 对一份与现有单测相同的小库检索，Then 候选 id 序列与本票之前一致。
  3. Given `git diff -- data/exp/x1 docs/evidence/neural-rerank docs/evidence/quality-gate/PREREG.md`，When 检查，Then 无改动。
  4. 质量闸重放 token 不变。
  5. 测试名或断言里不出现「注册 T1 上升」或新的通过率。
- **Provenance**:
  - Kind: adapt
  - Source: `Chunk` 现有列；清单 A-RAG-03；前沿索引 MRAG 的无训练元数据过滤。只摘「先滤再融合」
  - Pin: main `42df3c7371d0d4add7ce7594c3df9adb5edda8a1`（#605 / L4-RAG-04 已合）
  - What changed: 候选池在 RRF 之前按可选 `patch_id` 与 `valid_from` / `valid_to` 收窄。字段为空则空操作
  - Why not copy as-is: MRAG 的语义分×时间分可以以后做。本票只做元数据过滤。训练型时序臂是 C-01，不做
  - License note: 不迁入 `siyue-zhang/MRAG` 仓库
- **Tests**: added `tests/unit/test_l4_rag_03_patch_filter.py`
- **Rollback**: 还原上述 Paths。`PRODUCTION_RETRIEVAL_MODE`、`RRF_K`、`as_of` WHERE 无改动
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 的字符串值（保持 `hybrid+rerank`）
  - `docs/evidence/patch-events/RESULT-Y.md` 与 `PREREG-Y.md`
  - `docs/evidence/quality-gate/PREREG.md` 的 floors / segment_registered / owner_freeze / fingerprints
  - `docs/evidence/neural-rerank/summary.json` 与 `per-query.json`
  - `data/eval/guard_should.json`、`cite_sentence.json`、`temporal_new_over_old.json`、`gold.json`
  - `data/exp/x1/`
  - `RRF_K`、`NEURAL_RERANK_K`、fastembed pin、本地模型名
  - 不发明 SESOI，不把 `counted_as_pass` 设为 true，不在 224 题上拟合阈值
  - 不复用 `doc_version` 做补丁过滤，不改 `as_of` 的 T0/T1 WHERE
  - 不引进 langgraph，不挂 `web_search`
  - 夹具只放 `tests/`，不放 `data/exp/x1/`

### Provenance status
- result: pass
- notes: 依赖 L4-EV-T1-CASE（#603）已在 main。本票不修改 c2/c3 语料，也不把夹具过滤叙述成那两题已修复。c2/c3 仍是冻结名次上的 @T1 对 @T1

### Evidence *(after Matt `/implement`)*
- typecheck: `python -m compileall -q src` exit 0；`ruff check` 上述改动文件 exit 0
- tests: `pytest tests/unit/test_l4_rag_03_patch_filter.py` 及相邻检索测试 exit 0。离线质量闸 exit 0。G1 value=1.0；A1 recall value=0.42857142857142855；A1 precision value=0.6；T1 value=0.3333333333333333；R1 Recall@10 value=0.9732142857142857；R1 MRR@10 value=0.8381855867346939；各行 counted_as_pass=false
- paths: `store/base.py` · `store/pipeline.py` · `store/sqlite_store.py` · `tests/fixtures/l4_rag_03/` · `tests/unit/test_l4_rag_03_patch_filter.py` · `tests/unit/test_active_pack.py` · `tests/unit/test_l4_rag_04_hit_scores.py` · `tests/unit/test_retrieve_sufficiency.py` · `tests/unit/test_retrieve_grade.py` · `CONTEXT.md` · `tasks/L4-RAG-03.md` ok

## Handoff
`2026-10-14 | L4-RAG-03 | done | 质量闸重放 token 未动；不宣称 c2/c3 已修复`
