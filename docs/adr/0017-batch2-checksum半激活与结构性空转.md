# ADR-0017: Batch 2 checksum 半激活（档 2 renew）与结构性空转诚实登记

- **状态**: Accepted
- **日期**: 2026-09-23
- **相关**: ADR-0006 §4、`docs/research/checksum链激活契约.md`、`docs/research/β-checksum激活契约与空转设计评估.md`、地图 #96 / 工单 #97

## 背景

`checksum链激活契约.md` 盘点了三层空位，并按**演示价值**写明「档 2 不单做、本期留位不动代码」。地图 #96 将 Batch 2 验收层定为 **invariant**（确定性闸可复现），尺子与旧契约不一致。若继续「全留位」，Batch 2 无牙；若把档 3a/3b 塞进本批，则未预登记就改 fresh 构造或产品行为。

三条件齐备：

- **难反转**: 接线真 `checksum_fn` + ingest 现算并重灌后，再改比对源或回退空转会污染已写 `validity_basis` 与负例基线。
- **反直觉**: 旧文写「档 2 不单做」，读者会默认 Batch 2 仍不动手。
- **真实取舍**: 演示价值趋零 vs invariant 牙齿；全链激活 vs 半边诚实空转。

## 决策

1. **Batch 2 主激活档 2（renew 半边）**：`checksum_fn` 必须对语料文件现算 sha256；**禁止**读取与 `validity_basis.checksum` 同源的库列（套套逻辑硬禁）。
2. **fresh 半边明示结构性空转**：Agent fresh 路径本期仍不构造 `validity_basis`；不得宣传「checksum 全链已启用」。
3. **激活验收（invariant 预锁句）**：真 `checksum_fn` 已接线，且确定性负例（篡改语料文件 → renew 得 `CHECKSUM_MISMATCH`）可复现。本句**不得**升格为「checksum 已证明 latch」。已宣称激活的半边负例打不响 = 假激活 = 验收失败。
4. **档 3a / 3b 不进本批**：另开决策票；不得在实装单里顺手做跨轮重检或未预登记的 fresh basis schema 变更。
5. **旧契约改判范围**：`checksum链激活契约.md` 的事实盘点（§1–§4）仍有效；其「档 2 不单做 / 本期不动代码」在 Batch 2 范围内由本 ADR 取代。

## 后果

- `/to-spec`（Batch 2）须引用本 ADR 与评估文档预锁句；本 ADR 不授权 wayfinder 会话内 `/implement`。
- CONTEXT「规则闸」checksum 措辞改为半激活，不再写「整链留位未启用」。
- 攻击面用例（#98）与 renew 交界（#99）在激活边界之下展开，不得用改 gold / 放宽闸冒充激活。

## 替代方案（被否决）

- **仍全留位**：与 Batch 2 排期冲突，invariant 无测量物。
- **本批直上档 3a/3b**：未预登记 schema/产品行为，违反止损纪律。
- **`checksum_fn` 读库列「先接线」**：恒等假激活，比空转更糟。
- **只补丁旧契约、不升 ADR**：后人无法解释「为何违背不单做」。
