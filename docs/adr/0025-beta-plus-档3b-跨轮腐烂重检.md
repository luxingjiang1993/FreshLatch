# ADR-0025: β+ 档 3b 跨轮腐烂重检（双触发 → unknown）

- **状态**: Accepted
- **日期**: 2026-09-23
- **相关**: ADR-0017、ADR-0024、ADR-0006、`docs/research/checksum链激活契约.md` §4/§6、`docs/research/β+-档3b-跨轮腐烂重检设计评估.md`、工单 #111

## 背景

契约 §4 盘点：`validity_basis` **只写不读**，跨轮腐烂（续命后语料变更）抓不到。档 2 已激活 renew 写 basis；档 3a（ADR-0024）锁 list 方向但未实装。若不做 3b，validity 产品承诺继续空转；若只在 UI 提示或自动 void，则牙齿假活或侵占人审 L0。

三条件齐备：

- **难反转**: 启用跨轮降级会改变已续命绿灯的生命周期与复验入口行为。
- **反直觉**: 有人会以为「checksum 半激活」已含跨轮，或认为应先 3a 再 3b，或应降为 stale/dead。
- **真实取舍**: 只写不读 vs 复验入口+UI 双触发持久化；unknown 机械码 vs 伪造 stale 反证。

## 决策

1. **启用跨轮腐烂重检（产品行为）**：本 ADR 锁行为；实装/规格另票，须预登记负例；本决策会话不 `/implement`。
2. **双触发、同一套函数**：复验/迷你复验**入口机械前置**，以及 **UI 拉单/渲染**；共用 `check_basis` + `apply_rot`，**两条路径均持久化** claim 状态。
3. **范围**：仅 `status==fresh` 且 `validity_basis` 非空；`voided` 跳过；无 basis 的 fresh **不检**（维持半激活诚实；不等待 3a 实装）。
4. **不符处置**：`apply_rot` → `status=unknown` + 机械码（如 `BASIS_CHECKSUM_MISMATCH`）；复验入口**不进 Lead**；**禁止**自动 `void`；不伪造 stale 反证叙事。
5. **字段**：保留 `validity_basis` 与 `last_confirmed_at`；重复检到仍不符则幂等保持 `unknown`。
6. **形状**：今日比单对象；若值为 list，按 ADR-0024 **全员受检、任一不符即腐烂**；禁止只比首元素。
7. **审计**：`apply_rot` 写 `latch_log` 机械条目；不得解释为模型变好/变差。
8. **比对源**：`checksum_fn` 语料现算 sha256；**禁止**读与 basis 同源库列。

## 后果

- CONTEXT / 契约 §6 登记档 3b 方向已锁；β+ 方向地图在 3a+3b 决策齐后可关，实装另开承接票。
- 预锁 invariant 句见评估 §4；不得升格为「checksum 已证明 latch」或统计结论。

## 替代方案（被否决）

- **继续只写不读**：放弃跨轮产品承诺。
- **仅 UI 提示不写库 / 仅 UI 触发**：假牙或状态谎言。
- **降为 stale 或新增 claim 态 dead**：伪造反证或扩 Status 字面量过载。
- **自动 void**：侵占人审 L0。
- **无 basis 的 fresh 也失败**：偷开档 3a。
- **先实装 3a 再允许 3b**：颠倒读写依赖，拖延已有 renew basis 的牙齿。
