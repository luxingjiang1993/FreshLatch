# PE-C-02 · GATE-C 可扔门闩报告格式与复测夹具

## Parent

Part of #484（spec）· #486 · 地图 #482 · 决议 #483

## Destination

为路线 C 强制抄句机制提供可扔门闩报告格式与复测夹具；三条件与选取 R 一致。报告不进 `RESULT-C`。不激活、不发模型（人授探针另票）。

## Acceptance criteria

- [ ] 报告模板含：各臂自然放行/自然误放、固定 k 误放、T−B1/T−B2 差与方向、k、三条件判定、激活建议、代码针、是否发模型
- [ ] 路径建议 `docs/evidence/patch-events/GATE-C-*.md`；文首标明可扔·非甲·不进主表
- [ ] 夹具可驱动「过/不过」两种结论分支（测绿即可；不冒充真数据过门）
- [ ] 明确禁止把 #479 GATE-K-PROBE 升格为 C 已过门
- [ ] 未激活 `PREREG-C`；未写 RESULT-C 成立格

## Agent Guards

- **ID**: PE-C-02 · **Trust**: Watch · **Blast**: none  
- **Paths**: `docs/evidence/patch-events/GATE-C*.md`（或模板）；`src/freshlatch/eval/` 复测入口；`tests/unit/`  
- **Do-not-touch**: RESULT-C 成立格；B 归档；正式 formal-generations-c 主跑  

## Blocked by

建议在 PE-C-01 机制缝可测之后；可与 C-01 同波次但 Acceptance 分开。
