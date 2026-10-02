# ADR-0032: I3 三轨加固（政策旁路 · B′ 夹具 · Hard-Gold 骨架不改臂）

- **状态**: Accepted
- **日期**: 2026-10-03
- **相关**: `docs/research/I3-面试加固三轨设计评估.md`、`docs/grill-prep.md` §2i、roadmap Phase I3；上游 ADR-0003 / 0026（增益门与默认臂）、ADR-0030（I2 旁路思维）、ADR-0031（禁整包再验挂钩子）

## 背景

V1–V2 / I0–I2 冒烟齐后，拟整合 Backlog 的 B′、Hard-Gold、Policy-as-code（#8）。若不钉「整合形态」与三条硬边界，易出现：(1) 用难金标验收顶替政策 demo；(2) 把禁区塞进 `rule_gate` 改写不变量；(3) 跑过骨架报告就改 `PRODUCTION_RETRIEVAL_MODE`；(4) 无 Trigger 却开 Memory/多 Agent。

三条件齐备：难反转（ACCEPTANCE 与换臂纪律将引用）；反直觉（叫 Hard-Gold 却本波不改臂；三层不同仍共一阶段；#8 旁路而非改 Gate 正文）；真取舍（三轨分列 vs 真融合；骨架 vs 换臂；旁路 vs 塞不变量）。

## 决策

1. **阶段**  
   - 新开 **Phase I3（面试加固三轨）**：一阶段 · 三轨 · 冲 mid。  
   - 主缝：政策旁路能拒绿灯；Agent 假绿/重入不静默；难金标骨架可跑且默认臂仍 bm25。  
   - **三轨验收互不顶替**。

2. **Policy-as-code（thin · #8）**  
   - 声明式禁区规则经 Verify+ **旁路**装入；命中 → **政策拒** → 不得绿灯。  
   - 首条：**出处禁区**（域名/路径模式）。  
   - **禁止** OPA/Cedar 平台；**禁止**改写现有 `rule_gate` 不变量语义。

3. **B′（本波）**  
   - timeout / 结构化错误 / 人审串行幂等（薄）+ 闸分布一页（CLI 或 MD）。  
   - 合成夹具；**不声称**修过真生产事故。  
   - **禁止** Memory 大叙事、多 Agent 拓扑、跨 Provider 对照作硬关门；**禁止**把整包再验挂回发前钩子。

4. **Hard-Gold（本波 = 骨架）**  
   - 与冒烟 `retrieve_gold` **分文件**（如 `retrieve_hard_gold`）；预登记 **n≥20**，traps/对抗类 **≥30%**。  
   - 分列臂报告 + 既有增益门公式复跑。  
   - **本波不改** `PRODUCTION_RETRIEVAL_MODE`；Exit 须断言仍为 `bm25`。  
   - 过线后「讨论改臂」另决议；骨架 ≠ 授权换臂。

5. **票序与证据**  
   - 实现序：#8 → B′ → Hard-Gold → 联合 DoD。  
   - 证据：`docs/evidence/i3/ACCEPTANCE.md`；文首强制冒烟/面试加固层标签（见评估文档模板）。

6. **词表**  
   - `CONTEXT.md`：Hard-Gold、Policy-as-code（thin · #8）、政策拒。  
   - Phase 名不进 glossary。

## 后果

- roadmap Backlog 三项升为 I3 NOW（旁支）；C′ / 图谱 / Studio / High-Recall 仍冻结或另票。  
- 面试可讲「政策拒 ≠ 新鲜度拒」「Hard-Gold 骨架未换臂」「B′ 夹具非事故复盘」。  
- 违例：无层标签报显著；用任一轨 Exit 顶替另一轨；本波改默认臂。

## 替代方案（被否决）

- 真融合为单一产品能力、验收可互替。  
- 本波过增益门即改生产默认臂。  
- 禁区规则写入并改写 `rule_gate` 不变量。  
- 无 Phase 名仅 Backlog 波（Exit/地图弱）。  
- 难金标混入 smoke gold 同一文件。  
- 完整政策引擎或 Memory/多 Agent 硬化作 I3 Exit。
