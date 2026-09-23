# ADR-0024: β+ 档 3a 方向锁 list（本批不实装）

- **状态**: Accepted
- **日期**: 2026-09-23
- **相关**: ADR-0017、ADR-0006 §4、`docs/research/checksum链激活契约.md` §6、`docs/research/β+-档3a-fresh-validity_basis设计评估.md`、工单 #110

## 背景

ADR-0017 钉死 Batch 2：**renew 半激活、fresh 半边结构性空转**。档 3a（Agent fresh 补构造 `validity_basis`）另票。若不锁形状，后人易用「单 doc 主证据」廉价上线，在多 `t1_evidence_ids` 下形成假牙；若本批直接实装 list，则未单独预登记负例与迁移就动 schema+闸。

三条件齐备：

- **难反转**: 方向写成 list 同构后，实装与 3b 意图层会按此展开；事后改回单 doc 等于推翻已否假牙结论。
- **反直觉**: renew 已有牙，读者会默认「fresh 也应立刻补单 doc basis」。
- **真实取舍**: 诚实空转（现状）vs 单 doc 假牙 vs list 真牙（方向锁、本批不付实现代价）。

## 决策

1. **本批不实装档 3a**：Agent fresh **继续不构造** `validity_basis`；不得宣传 fresh checksum 半边已启用；不从本票自动派生实装票。
2. **方向 = list 同构**：将来若做，目标形状为 `[{doc_id, checksum}, …]`；由 `t1_evidence_ids` **按 `doc_id` 去重**构造；闸对**每一项**现算比对，**任一不符**即 `CHECKSUM_MISMATCH`；套套逻辑硬禁不变。
3. **renew 同构**：将来实装时 schema 统一为 list；renew 仍人选一条证据，写**一元 list**；不改人审「选一条」交互。
4. **存量**：实装时把已有单对象 `validity_basis` **迁成一元 list**；读路径不长期双形状。
5. **否决**：以「单 doc 主证据」或「闸只抽检子集」作为 fresh 激活方向。
6. **实装门闩**：仅显式新开实装/规格票，且构造规则与负例已预登记（见评估 §7）；档 3b 发现讲不圆可作为信号，不得替代门闩。
7. **与档 3b**：方向清晰即解阻；设计须分开**事实层**（今日仅 renew 写单对象）与**意图层**（将来 list）。

## 后果

- CONTEXT「checksum 半激活」补方向指针；操作句仍不进词表。
- `checksum链激活契约.md` §6 档 3a 行改为「方向已锁·本批未实装」。
- 本 ADR 不授权 wayfinder 会话内 `/implement`，不改 gold。

## 替代方案（被否决）

- **明确永不做 3a**：放弃 list 意图，3b 无法对齐将来写侧。
- **本批直接实装**：未另票预登记负例/迁移即动 schema。
- **方向锁单 doc 主证据**：假牙，违背不变量闭合动机。
- **只补丁 ADR-0017 附录**：档 2 激活与档 3a 方向糊成一团。
- **关单即开 ready-for-agent**：把「锁方向」偷换成「已排期实现」。
