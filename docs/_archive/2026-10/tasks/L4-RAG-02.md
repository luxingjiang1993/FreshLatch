# TASK / ticket — one slice (copy to `tasks/<ID>.md`)

Matt `/to-tickets` may create this file; `/enrich-tickets` fills **Agent Guards**. Humans mainly set **Trust** and skim Acceptance / Paths / Provenance.

## Ticket
- **ID**: L4-RAG-02
- **Title**: `feat(rag): retrieve 边 CRAG 三态，Agent 只消费 grade`
- **Paths**:
  - `src/freshlatch/roles/lead.py`（RAG-01 检索观察上挂 grade;fresh 写入前只消费该 grade）
  - `src/freshlatch/roles/retrieve_grade.py`（与 `retrieve_sufficiency.py` 相邻的纯函数:三态 + 是否再检索一次 + 是否拒 fresh）
  - `src/freshlatch/roles/loop.py`（本票不改;循环不另写 grade,不引进 langgraph）
  - `tests/unit/test_retrieve_grade.py`
  - `CONTEXT.md`（`CRAG grade`、`grade_incorrect_exhausted`、`grade_ambiguous`）

## Agent Guards
- **Blast**: api
- **Trust**: Watch
- **Acceptance**:
  1. Given 夹具把检索标成 Incorrect,When 跑短路径,Then 再检索一次后仍失败并拒答;reason code 为 `grade_incorrect_exhausted`;轨迹与工具名不出现 `web_search`。
  2. Given 夹具标成 Correct 且规则闸条件满足,When 跑同一路径,Then 本票不强制拒答。
  3. Given Ambiguous 夹具,When 跑完,Then 轨迹含 `grade=ambiguous`,且不把该状态写成 fresh。
  4. Do-not-touch 路径无改;离线质量闸 exit 0,G1/A1/T1/R1 `value=` 与改前一致。
- **Provenance**:
  - Kind: adapt
  - Source: 清单 A-RAG-02;前沿 CRAG 三态（Correct / Incorrect / Ambiguous）。挂点固定在 retrieve
  - Pin: main `e7b44f46`（#602 / L4-RAG-01 已合）
  - What changed: 检索观察增加 grade;Incorrect 再检索一次后拒答;Ambiguous 不写 fresh;Agent 只读 grade
  - Why not copy as-is: 上游含网络回退,本仓 `web_search` 保持未挂载
  - License note: 不迁入 CRAG 仓库
- **Tests**: added `tests/unit/test_retrieve_grade.py`
- **Rollback**: 还原上述 Paths;规则闸与 `loop.py` 无改动
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
  - 不改规则闸「无 t1_evidence_ids 不得 fresh」语义

### Provenance status
- result: pass
- notes: grade 由检索边纯函数给出;夹具注入 `crag_grade`;无注入时只看 `@T1` 后缀。Ambiguous 不从两条 T1 矛盾推断

### Evidence *(after Matt `/implement`)*
- typecheck: `python -m compileall -q src/freshlatch/roles/lead.py src/freshlatch/roles/retrieve_grade.py`
- tests: `pytest tests/unit/test_retrieve_grade.py tests/unit/test_retrieve_sufficiency.py`;离线质量闸退出码 0,G1/A1/T1/R1 `value=` 未漂移
- paths: `roles/lead.py` · `roles/retrieve_grade.py` · `tests/unit/test_retrieve_grade.py` · `CONTEXT.md` · `tasks/L4-RAG-02.md`

## Handoff
`L4-RAG-02 | 实装 retrieve 边 CRAG 三态 | Agent 只消费 grade | 无 web_search,规则闸未改`
