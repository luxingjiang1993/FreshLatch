# PE-Y-02 · GATE-Y-PROBE（可扔 · 真数据过门）

## Parent

规格卷 27 · ADR-0037 · PR #493

## Destination

克隆 `patch_events_gate_k_probe` / `GATE-K-PROBE.md` 为 Y：过门 = **k≥10 ∧ T−C 固定 k 误放差点估计>0**；B1/B2 差必报不过门。夹具冒烟可选；真数据探针须人授。报告可扔，不进 RESULT-Y。

## Acceptance criteria

- [ ] `GATE-Y-PROBE.md` 含三条件判定表（过门两条 + B1/B2 报告行）与层身份「可扔」
- [ ] 夹具绿不得单独令 `gate_passed=true` 用于激活建议（须真数据路径或显式层标注）
- [ ] 禁止升格 `#479` / GATE-C-FIXTURE 为已过门
- [ ] 默认不发模型；`--authorize-send` 仅在人授探针令后
- [ ] 相关 pytest 绿；不改 B/C 归档

## Agent Guards

- **ID**: PE-Y-02 · **Trust**: Watch · **Blast**: none  
- **Paths**: `src/freshlatch/eval/patch_events_gate_y_probe.py`；`docs/evidence/patch-events/GATE-Y-PROBE.md`；单测  
- **Do-not-touch**: RESULT-Y 成立格；B/C 门闩页升格；甲三条件过门  

## Blocked by

PE-Y-01 旁路可并行起步；真数据发送须人授探针令。
