# TASK / ticket — one slice (copy to `tasks/<ID>.md`)

Matt `/to-tickets` may create this file; `/enrich-tickets` fills **Agent Guards**. Humans mainly set **Trust** and skim Acceptance / Paths / Provenance.

## Ticket
- **ID**: L4-RAG-04
- **Title**: `feat(rag): hit 可测分与 rerank 开关记录`
- **Paths**:
  - `src/freshlatch/roles/lead.py#_t_retrieve`（观察块补 `scores`；观察补已有的 `retrieval_mode` / `rerank_mode`；不改 grade 字段）
  - `src/freshlatch/store/pipeline.py`、`src/freshlatch/store/neural_rerank.py`（只抄现有分，不改融合公式）
  - `src/freshlatch/runner.py`（运维开关写入点：显式 `bm25` 绑定，以及 manifest）
  - `tests/unit/test_l4_rag_04_hit_scores.py`
  - `CONTEXT.md`（`hit 可测分`、`rerank 开关记录`、`bm25_fallback`）

## Agent Guards
- **Blast**: api
- **Trust**: Auto
- **Acceptance**:
  1. Given 一次 hybrid+rerank 检索夹具，When 读工具观察，Then 每个 hit 含可区分的分字段，且 `retrieval_mode` 仍不能由模型参数改写（传入则返回现有错误「生产路径不可指定 retrieval_mode」）。
  2. Given 同一小夹具分别走神经精排与词面精排，When 读两次 manifest，Then 能看出 rerank ON 与 OFF，且两次都不改 `PRODUCTION_RETRIEVAL_MODE`。本票不重跑 224 题，不替换 `neural-rerank/summary.json`。
  3. Given 运维开关切到 `bm25`，When 读 `last_retrieval_mode`，Then 值不是 `bm25_fallback`。`bm25_fallback` 仍只表示缺可用向量。
  4. 质量闸重放 token 不变。
- **Provenance**:
  - Kind: adapt
  - Source: `LeadReverifier._t_retrieve` 现返回 `blocks` 与 `retrieval_used`；轨迹事件已有 `retrieval_mode` / `rerank_mode`；清单 A-RAG-04
  - Pin: main `aa7f2a5537f0a5236bde8337dc73fd16d55c4c0f`（#604 / L4-RAG-02 已合）
  - What changed: 工具观察补上当次 BM25 / dense / RRF / rerank 分，以及轨迹里已有的臂字段；小夹具 manifest 用 `rerank=on|off` 分开神经精排与词面精排；显式 BM25 绑定不再与缺向量共用记法
  - Why not copy as-is: 工具观察和轨迹字段今天不一致。本票把已有臂信息补进观察，不新做精排器
  - License note: 不迁入 sec-rag-analyst / xai-rag 仓库
- **Tests**: added `tests/unit/test_l4_rag_04_hit_scores.py`
- **Rollback**: 还原上述 Paths；`base.py` 的 `InMemoryStore.retrieve` 与融合公式无改动
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 常量值（`src/freshlatch/store/base.py` 整文件不改，避免与 L4-RAG-02 的路径锁冲突）
  - `docs/evidence/patch-events/RESULT-Y.md` 与 `PREREG-Y.md`
  - `docs/evidence/quality-gate/PREREG.md`
  - `docs/evidence/neural-rerank/summary.json` 与 `per-query.json`
  - `data/eval/guard_should.json`、`cite_sentence.json`、`temporal_new_over_old.json`、`gold.json`
  - `data/exp/x1/`
  - `RRF_K`、`NEURAL_RERANK_K`、fastembed pin、本地模型名
  - 不发明 SESOI，不把 `counted_as_pass` 设为 true，不在 224 题上拟合阈值
  - 不把 langgraph 引进 `roles/loop.py`，不挂 `web_search`
  - 不改融合公式 / reranker 模型

### Provenance status
- result: pass
- notes: 分从现有 BM25、余弦、RRF、精排抄出。`base.py` 不改；`try_retrieve` 用 ContextVar 接住这次调用已经算出的分。grade / sufficiency 字段保持 L4-RAG-02 的形状

### Evidence *(after Matt `/implement`)*
- typecheck: `python -m compileall -q src` exit 0
- tests: `pytest tests/unit/test_l4_rag_04_hit_scores.py` 及相邻检索测试 exit 0；离线质量闸 exit 0，G1 value=1.0，A1 recall value=0.42857142857142855，A1 precision value=0.6，T1 value=0.3333333333333333，R1 Recall@10 value=0.9732142857142857，R1 MRR@10 value=0.8381855867346939，counted_as_pass=false
- paths: `roles/lead.py` · `runner.py` · `store/pipeline.py` · `store/neural_rerank.py` · `tests/unit/test_l4_rag_04_hit_scores.py` · `CONTEXT.md` · `tasks/L4-RAG-04.md` ok

## Handoff
`L4-RAG-04 | hit 可测分与 rerank 开关 manifest | 显式 bm25 不记 bm25_fallback | 不重跑 224`
