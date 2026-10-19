# TASK / ticket — one slice (copy to `tasks/<ID>.md`)

Matt `/to-tickets` may create this file; `/enrich-tickets` fills **Agent Guards**. Humans mainly set **Trust** and skim Acceptance / Paths / Provenance.

## Ticket
- **ID**: L4-RAG-01
- **Title**: `feat(rag): retrieve 边 sufficiency 标签，不足则不发 fresh`
- **Paths**:
  - `src/freshlatch/roles/lead.py`（`_t_retrieve` 返回,以及 fresh 写入前消费该观察）
  - `src/freshlatch/roles/retrieve_sufficiency.py`（与 `loop.py` 相邻的纯函数:标签 + 是否继续写 fresh）
  - `src/freshlatch/gates/rule_gate.py`（只读 fresh 条件,本票不改、不放宽）
  - `tests/unit/test_retrieve_sufficiency.py`
  - `CONTEXT.md`（`insufficient_evidence`）

## Agent Guards
- **Blast**: api
- **Trust**: Watch
- **Acceptance**:
  1. Given 夹具 store 对查询返回零块,When 跑到判定出口,Then 结果不是 fresh,轨迹含 `sufficiency=insufficient` 与 reason code `insufficient_evidence`,且测试不调用付费 LLM。
  2. Given 夹具返回至少一条本轮 `@T1` 块且规则闸会放行的最小输入,When 跑同一出口,Then 本票不把该输入改成拒答。
  3. Given 上述 diff,When 检查 Do-not-touch 列表,Then 那些路径无改动。
  4. Given `python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md`,When 重放,Then 退出码 0,且 G1/A1/T1/R1 的 `value=` 与改前一致。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/roles/lead.py#_t_retrieve`;`src/freshlatch/gates/rule_gate.py` 无 T1 不得 fresh;计划 `docs/evidence/l4-full-build-plan-2026-10-14.md` §5.1;Sufficient Context 只摘「标签 → 选择性拒答」
  - Pin: main `80abec9`（#601 之后）
  - What changed: 拒答前移到检索观察;规则闸仍在
  - Why not copy as-is: 论文实现带分类器与网页回退。本票用空命中夹具,不训练、不联网
  - License note: 不迁入 sufficientcontext 仓库
- **Tests**: added `tests/unit/test_retrieve_sufficiency.py`
- **Rollback**: 还原上述 Paths;规则闸无改动可单独回退角色层
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE`（`src/freshlatch/store/base.py`）
  - `docs/evidence/patch-events/RESULT-Y.md` 与 PREREG-Y
  - `docs/evidence/quality-gate/PREREG.md`
  - `docs/evidence/neural-rerank/summary.json` 与 `per-query.json`
  - `data/eval/guard_should.json`、`cite_sentence.json`、`temporal_new_over_old.json`、`gold.json`
  - `data/exp/x1/`
  - `RRF_K`、`NEURAL_RERANK_K`、fastembed pin、本地模型名
  - 不发明 SESOI,不把 `counted_as_pass` 设为 true,不在 224 题上拟合阈值
  - 不把 langgraph 引进 `roles/loop.py`,不挂 `web_search`

### Provenance status
- result: pass
- notes: 挂点沿用现有 `_t_retrieve` 成功返回;空命中即 `insufficient`

### Evidence *(after Matt `/implement`)*
- typecheck: `python -m compileall -q src/freshlatch/roles/lead.py src/freshlatch/roles/retrieve_sufficiency.py`
- tests: `pytest tests/unit/test_retrieve_sufficiency.py` 及相邻 lead/闸回归通过;离线质量闸退出码 0,G1/A1/T1/R1 `value=` 未漂移
- paths: `roles/lead.py` · `roles/retrieve_sufficiency.py` · `tests/unit/test_retrieve_sufficiency.py` · `CONTEXT.md`

## Handoff
`L4-RAG-01 | 实装检索观察 sufficiency | 不足不写 fresh | 规则闸未改`
