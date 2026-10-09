# PE-Y-02 · GATE-Y-PROBE（可扔 · 真数据过门）

## Parent

规格卷 27 · ADR-0037 · PR [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493)

## Destination

克隆 `patch_events_gate_k_probe` / `GATE-K-PROBE.md` 为 Y：过门 = **k≥10 ∧ T−C 固定 k 误放差点估计>0**；B1/B2 差必报不过门。夹具冒烟可选；真数据探针须人授。报告可扔，不进 RESULT-Y。

## Acceptance criteria

- [x] Given 合成/夹具输入可分别构造「过/不过」，When 跑 gate-y 判定，Then `gate_passed` 仅当 k≥10 且 T−C 点估计>0；T−B1/T−B2 出现在报告但不改变 `gate_passed`
- [x] `docs/evidence/patch-events/GATE-Y-PROBE.md` 文首含「可扔 · 非乙成立 · 不进主表」；含判定表、代码针、是否发模型字段
- [x] 默认 `PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe` **不**发模型；无探针人令时 `--authorize-send` 拒绝
- [x] 单测断言：不得把 `#479`/`GATE-K-PROBE`/`GATE-C-FIXTURE` 路径当作本页已过门依据
- [x] `python -m compileall -q src` 退出 0；`pytest tests/unit/test_pe_gate_y_probe.py` 绿

## Agent Guards

- **ID**: PE-Y-02
- **Title**: `feat(eval): GATE-Y-PROBE 过门判定（可扔）`
- **Trust**: Watch
- **Blast**: none
- **Paths**:
  - `src/freshlatch/eval/patch_events_gate_y_probe.py`（new · adapt）
  - `docs/evidence/patch-events/GATE-Y-PROBE.md`（new · adapt 报告形态）
  - `docs/evidence/patch-events/gate-y-probe-generations.jsonl`（旁路产物；可空壳）
  - `tests/unit/test_pe_gate_y_probe.py`（new）
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/eval/patch_events_gate_k_probe.py` + `docs/evidence/patch-events/GATE-K-PROBE.md` @ B tip
  - Pin: `4ec045b96aa23a19acd2822accdac52658366958`
  - URL: https://github.com/luxingjiang1993/FreshLatch/blob/4ec045b96aa23a19acd2822accdac52658366958/src/freshlatch/eval/patch_events_gate_k_probe.py
  - What changed: 过门条件由「k≥10∧T−B1>0∧T−B2>0」改为「k≥10∧T−C>0」；B1/B2 降为报告行；产物/报告改 Y 路径
  - Why not copy as-is: 冲乙门闩必须对齐求验目标，不能继续用冲甲三条件
  - License note: 同仓代码
- **Tests**: added
- **Do-not-touch**: `RESULT-Y` 成立格；B/C 门闩页内容升格；甲三条件过门；正式 `formal-generations-y` 主跑
- **Rollback**: 删除 gate-y 模块/报告/单测

### Provenance status

- result: pass
- notes: adapt 自 GATE-K-PROBE 管线；SHA 钉死；过门语义差异写明

### Evidence *(after Matt `/implement`)*

- typecheck: `python -m compileall -q src` → 0
- tests: `pytest tests/unit/test_pe_gate_y_probe.py` → 12 passed
- paths: `src/freshlatch/eval/patch_events_gate_y_probe.py` · `docs/evidence/patch-events/GATE-Y-PROBE.md` · `docs/evidence/patch-events/gate-y-probe-generations.jsonl` · `tests/unit/test_pe_gate_y_probe.py`

## Blocked by

可与 PE-Y-01 同波次并行。真数据 `--authorize-send` 另需人授探针令：「授权路线 Y 仓外探针发模型；不得激活。」

## Handoff

`enrich done | PE-Y-02 | ready | next: before-implement PE-Y-02`
