# ADR-0026: I0 冒烟层预登记与 reports 为数字真相源

- **状态**: Accepted
- **日期**: 2026-09-29
- **相关**: `docs/research/I0-冒烟层与数字真相源设计评估.md`、`docs/accounting-card.md`、`docs/eval-retrieve.md`、ADR-0003（#156）、roadmap Phase I0

## 背景

Phase A 已产出 `reports/retrieve-*.md` 对比表，但缺 I0 收敛文档时，面试与后续叙事容易把冒烟 n=36 升格成「已证明 BM25 最优」，或把数字抄进 docs 造成第二真相。另有取舍：无 API Key 时 Exit 是否要求五臂全表。

三条件齐备：难反转（层标签与 SoT 一旦被外部引用）；反直觉（有对比表却仍默认 BM25）；真取舍（reports SoT vs 抄表；冒烟声明 vs 装统计）。

## 决策

1. **冒烟层预登记**：凡引用 Phase A retrieve 对比数字的 I0 文档（至少 `accounting-card`、`eval-retrieve`）文首必须声明：演示/冒烟层（n=36）；不报方差；不作统计显著声明。事后去掉该声明或把冒烟写成统计结论 = 本 ADR 违例。
2. **数字真相源**：可引用数字以仓内 `reports/retrieve-*.md`（及关门汇总）为准；docs 只链接与叙事，**禁止**把整表复制成第二真相；未重跑不得改报告内数字。
3. **无增益不改默认**：与 ADR-0003（#156）一致——评测可跑 dense/hybrid/rerank；生产默认须过预登记增益门，且改臂另走 Hard-Gold（Backlog 另票）。
4. **I0 Exit 复跑下限**：无 dense 索引/API Key 时，BM25（及本地可得 traps/transform）可跑即满足复跑硬门；五臂全表为增强路径。禁止仅用 markdown 报告顶替实跑验收。

## 后果

- I0 三件套与面试口述必须带层标签；mid 不得用本表冒充 Hard-Gold 或统计证明。
- V1 merge / 对外 demo 叙事前须 I0 Exit（表在仓且闭卷可算），骨架编码可并行（见 grill-prep）。

## 替代方案（被否决）

- 把对比表整份抄进 `docs/eval-retrieve.md` 当作唯一数字源。
- I0 Exit 强制五臂全表可复现（绑死密钥）。
- 不开层标签、靠口头说明「别当真」。
- 仅修订 ADR-0003 而不单独钉 SoT/层标签（0003 管选型与增益；本 ADR 管 I0 文档纪律）。
