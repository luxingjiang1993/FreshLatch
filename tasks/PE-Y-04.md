# PE-Y-04 · RESULT-Y 抄表口径（仅 T−C · 禁甲）

## Parent

规格卷 27 · ADR-0037 · PR [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493)（`RESULT-Y.md` 壳已落）

## Destination

在同一次 `compare_primary` 输出上实现 Y 分层：乙成立 ⟺ T−C 点>0.05 且下界>0；B1/B2 报告-only；永不判甲；止损点≤0.05 或下界≤0 → 丙。

## Acceptance criteria

- [ ] Given 伪造 `compare_primary` 报告：T−C 点=0.04 且下界>0，且 T−B1/T−B2 均点>0 且下界>0，When `outcome_tier_y`（或等价），Then 返回 **丙**（非乙、非甲）
- [ ] Given 仅 T−C 点=0.06 且下界>0，B1/B2 下界≤0，When 分层，Then 返回 **乙**；渲染文面不含「结果甲」/「称甲」
- [ ] 抄表函数只消费同一次 primary dict；单测禁止手填成立格路径；禁止从 GATE/B/C 路径读数写入成立格
- [ ] `RESULT-Y.md` 保留 B/C 负结果附录句；未主跑时成立格保持「未填」
- [ ] `python -m compileall -q src` 退出 0；`pytest tests/unit/test_pe_result_y.py`（或同名）绿

## Agent Guards

- **ID**: PE-Y-04
- **Title**: `feat(eval): RESULT-Y 乙成立口径与禁甲分层`
- **Trust**: Watch
- **Blast**: none
- **Paths**:
  - `src/freshlatch/eval/patch_events_formal_y.py`（`outcome_tier` / `render_result_y` · adapt）
  - `docs/evidence/patch-events/RESULT-Y.md`（已有壳 · 本票可补渲染对齐，不填真数）
  - `tests/unit/test_pe_result_y.py`（new）
  - 只读：`src/freshlatch/eval/patch_events_metrics.py`::`compare_primary`
- **Provenance**:
  - Kind: adapt
  - Source: `patch_events_formal_b.py`::`outcome_tier` / `render_result_b` @ B tip；壳 `RESULT-Y.md` @ 本 PR
  - Pin: `4ec045b96aa23a19acd2822accdac52658366958`（formal_b）
  - URL: https://github.com/luxingjiang1993/FreshLatch/blob/4ec045b96aa23a19acd2822accdac52658366958/src/freshlatch/eval/patch_events_formal_b.py
  - What changed: 分层只看 T−C 且点>0.05；去掉甲分支；B1/B2 标报告-only
  - Why not copy as-is: B 的甲/乙/丙判定含三行成立；Y 放弃甲并加严点估计地板
  - License note: 同仓
- **Tests**: added
- **Do-not-touch**: `compare_primary` 内部 `established` 布尔语义（可只读消费）；`RESULT-B`/`RESULT-C` 成立格；激活态
- **Rollback**: 恢复 RESULT-Y 壳；移除 Y 分层函数

### Provenance status

- result: pass
- notes: adapt formal_b 抄表/分层；比较器只读；壳已在 #493

### Evidence *(after Matt `/implement`)*

- typecheck:
- tests:
- paths:

## Blocked by

PE-Y-01 骨架（渲染入口）。可与 PE-Y-03 并行。

## Handoff

`enrich done | PE-Y-04 | ready | next: before-implement PE-Y-04`
