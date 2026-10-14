# TASK / ticket — one slice (copy to `tasks/<ID>.md`)

Matt `/to-tickets` may create this file; `/enrich-tickets` fills **Agent Guards**. Humans mainly set **Trust** and skim Acceptance / Paths / Provenance.

## Ticket
- **ID**: L4-FC-CITE
- **Title**: `feat(tools): claim 引用必须落在本轮 evidence registry`
- **Paths**:
  - `src/freshlatch/evidence.py`（`check_evidence_ids`、`TurnRegistry`、`cite_outside_registry`）
  - `src/freshlatch/roles/lead.py`（`_seen_evidence` 钉成 turn-scoped registry；`reverify_claim` / `mark_stale`）
  - 轨迹写入（`Runner._dump_trajectory` 所消费的 `ctx.events`：`cite_registry_refusal` / `cite_registry_judgment`）
  - `tests/unit/test_l4_fc_cite.py`
  - `CONTEXT.md`（`cite_outside_registry`、`TurnRegistry`）
  - `tasks/L4-FC-CITE.md`

## Agent Guards
- **Blast**: api
- **Trust**: Watch
- **Acceptance**:
  1. Given 本轮 retrieve 返回集合 S，When `reverify_claim` 或 `mark_stale` 传入 S 之外的 id，Then 该 call 被拒绝，reason 可枚举（`cite_outside_registry`），不产生 fresh。
  2. Given 传入的 id 都在 S 中且为 `@T1`，When 其余闸条件满足，Then 本票不额外拒绝。
  3. Given 一次成功判定，When 读轨迹事件，Then 能看到所用 evidence id 列表。
  4. Given diff，When 检索 `score_citation_overlap` 与 `cite_sentence.json`，Then 本票不修改它们，也不把注册 A1 的地板写入新断言。
- **Provenance**:
  - Kind: adapt
  - Source: `check_evidence_ids`；`LeadReverifier._seen_evidence`；清单 A-EV-02 的 registry 半边；诊断 §4.2
  - Pin: main `1ac137d15d5c1fe52c596276f1e549fc75d793f4`（#606 / L4-RAG-03）
  - What changed: 把本轮 retrieve 见过的 id 显式定为 TurnRegistry；拒因用 `cite_outside_registry`；轨迹记录判定所用 id
  - Why not copy as-is: 现有检查已能拒陌生 id。缺的是轨迹上的 registry 记录，以及与金标 C∩R 脱钩的测试名
  - License note: 不迁入外部 citation 评测仓库，不读取 `cite_sentence.json` 打分
- **Tests**: added `tests/unit/test_l4_fc_cite.py`（`cite_outside_registry_rejected`、`cite_subset_ok`；不调用付费 LLM）
- **Rollback**: 还原上述 Paths。`score_citation_overlap` 与质量闸预注册无改动，可单独回退角色层
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 的字符串值（保持 `hybrid+rerank`）
  - `docs/evidence/patch-events/RESULT-Y.md` 与 `PREREG-Y.md`
  - `docs/evidence/quality-gate/PREREG.md` 的 floors / segment_registered / owner_freeze / fingerprints
  - `docs/evidence/neural-rerank/summary.json` 与 `per-query.json`
  - `data/eval/guard_should.json`、`cite_sentence.json`、`temporal_new_over_old.json`、`gold.json`
  - `data/exp/x1/`
  - `RRF_K`、`NEURAL_RERANK_K`、fastembed pin、本地模型名
  - 不发明 SESOI，不把 `counted_as_pass` 设为 true，不在 224 题上拟合阈值
  - 不引进 langgraph，不挂 `web_search`，不默认挂 `LEAD_TOOLS_W9`
  - 不新增绕过 `tool_tier` / 权限的写工具
  - 不修改 `score_citation_overlap` 实现语义，不把注册 A1 地板写入新断言
  - 夹具只放 `tests/`，不放 `data/exp/x1/`

### Provenance status
- result: pass
- notes: 依赖 L4-RAG-01 的 `insufficient_evidence` 已在 main。本票拒因是另一枚码 `cite_outside_registry`。不依赖 FC-01

### Evidence *(after Matt `/implement`)*
- typecheck: （实现后补）
- tests: （实现后补）
- paths: （实现后补）

## Handoff
`L4-FC-CITE | 工单已落盘 | 实现前 | TurnRegistry + cite_outside_registry`
