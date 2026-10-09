# PE-Y-04 · RESULT-Y 抄表口径（仅 T−C · 禁甲）

## Parent

规格卷 27 · ADR-0037 · PR #493（`RESULT-Y.md` 壳已落）

## Destination

在同一次 `compare_primary` 输出上实现 Y 分层：乙成立 ⟺ T−C 点>0.05 且下界>0；B1/B2 报告-only；永不判甲；止损点≤0.05 或下界≤0 → 丙。

## Acceptance criteria

- [ ] 单测：经典三行皆「点>0∧下界>0」但 T−C 点=0.04 → 分层 **丙**（非乙、非甲）
- [ ] 单测：仅 T−C 过 Y 尺、B1/B2 不过 → 分层 **乙**；文面不含「甲」
- [ ] 抄表禁止手填成立格；禁止抄 GATE/B/C 数字进成立格
- [ ] B/C 负结果附录句保留；pytest 绿

## Agent Guards

- **ID**: PE-Y-04 · **Trust**: Watch · **Blast**: none  
- **Paths**: `patch_events_formal_y` 抄表/分层；`RESULT-Y.md`；`tests/unit/test_pe_result_y*.py`  
- **Do-not-touch**: `compare_primary` 内部成立布尔（可只读）；B/C RESULT 成立格  

## Blocked by

PE-Y-01 骨架。
