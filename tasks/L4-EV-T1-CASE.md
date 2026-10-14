# TASK / ticket — one slice (copy to `tasks/<ID>.md`)

Matt `/to-tickets` may create this file; `/enrich-tickets` fills **Agent Guards**. Humans mainly set **Trust** and skim Acceptance / Paths / Provenance.

## Ticket
- **ID**: L4-EV-T1-CASE
- **Title**: `test(quality-gate): 冻结名次上的 T1 个案锁`
- **Paths**:
  - `tests/unit/test_quality_gate_t1_cases.py`（紧邻 `tests/unit/test_quality_gate.py` 的新测试;不改质量闸源码）
  - 只读 `docs/evidence/neural-rerank/per-query.json`
  - 只读 `data/eval/temporal_new_over_old.json`
  - `tasks/L4-EV-T1-CASE.md`

## Agent Guards
- **Blast**: none
- **Trust**: Auto
- **Acceptance**:
  1. Given 冻结 `k10.neural_ranked`，When 测试读 `s6-d1-c1-q1`，Then `in_force` 的下标小于 `superseded`。
  2. Given 同一文件，When 读 `s6-d1-c2-q1`，Then `superseded` 的下标小于 `in_force`。
  3. Given 同一文件，When 读 `s6-d1-c3-q1`，Then `in_force` 与 `superseded` 都不在列表中。
  4. Given `tno-trap-supersede-1`，When 在 per-query 的 id 集合里查找，Then 不存在，与 `unresolved` 一致。
  5. Given 质量闸源码 diff，When 检索，Then 本票没有把 conflict-pair 或 T1 设成 `counted_as_pass=true`，没有新的百分数地板。
- **Provenance**:
  - Kind: adapt
  - Source: `freshlatch.eval.retrieve_typed.conflict_pair_correct`；诊断 `docs/evidence/l4-system-diagnosis-2026-10-14.md` §4.3
  - Pin: main `e7b44f469ab32ac89926af66c557c82cb246f7bb`
  - What changed: 把 c1 / c2 / c3 / trap 写成只读断言。质量闸仍只打印聚合 `value=`
  - Why not copy as-is: 质量闸只打印聚合 `value=`。个案锁把反序与双缺失两种失败分开，聚合地板仍然只描述、不判产品通过
  - License note: 仓内
- **Tests**: added `tests/unit/test_quality_gate_t1_cases.py`
- **Rollback**: 删除本测试文件与本票
- **Do-not-touch**:
  - `docs/evidence/neural-rerank/per-query.json` 与 `summary.json`（只读断言）
  - `data/eval/temporal_new_over_old.json`、金标、`docs/evidence/quality-gate/PREREG.md`、`data/exp/x1/`、`docs/evidence/patch-events/RESULT-Y.md`
  - 不新增通过线 / 百分数地板；不把 `counted_as_pass` 设为 true；不发明 SESOI
  - 不改质量闸退出码语义

### Provenance status
- result: pass
- notes: 名次只读 `k10.neural_ranked`；`in_force` / `superseded` 只读金标条。`conflict_pair_correct` 不读 `precedence`。trap 的 `source_refs` 不在 224 行里，计分 `unresolved`

### Evidence *(after Matt `/implement`)*
- typecheck: `python -m compileall -q src` exit 0
- tests: `pytest tests/unit/test_quality_gate_t1_cases.py` 5 passed; `pytest tests/unit/test_quality_gate.py` 39 passed; 离线质量闸 exit 0, G1/A1/T1/R1 与 conflict-pair 的 `value=` 与诊断 §3 一致
- paths: `tests/unit/test_quality_gate_t1_cases.py` · `tasks/L4-EV-T1-CASE.md` ok

## Handoff
`L4-EV-T1-CASE | 只读个案锁已落 | 质量闸 value token 未漂 | 待人合并`
