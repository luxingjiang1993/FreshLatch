# category-rule-v2（草稿）

Ronin 代理人（模型）起草，未经人工审核；依据 owner 2026-10-07 13:16 的决定。实现见 `../build_round4.py` 的 `category_v2`。

按下列顺序判断，取第一条成立的：

1. **K1 快照取代**：`score_role = guardrail` → `trap`（不进比例分母）。
2. **K2 同快照冲突陈述**：同一 `as_of` 下，两块对同一对象的说法不能同时成立，而且这对冲突跟问句有关，满足其一即可：
   - 错误的一侧在 distractors；
   - 问句问两侧或问变化，两侧都在 relevant。

   满足任一条件即判 `trap`：
   - 带 `conflict_pair`；
   - C1–C4 条文对的新旧两侧都在 relevant ∪ distractors（D3：s6-d1-c4-q1 计 trap）；
   - 逐题判定的合成冲突（TRAP-DEFINITIONS-draft §5，D5 边界题暂计入）。

   冲突只写在同一块里，不算。
3. **K3 元陈述**：同快照的 distractors 里有一块，其决定性内容是封闭词表里的元陈述（未复测 / 不再列入跟踪 / 无新数据 / 待发布 / 未入账），而问句问的是实质事实 → `trap`。如果问句问的就是状态本身，不算。
4. **adversarial**：问句本身含操纵指令或错误前提。现有题里没有。
5. 其余 → `hard`（D4：s7-d3-t1-05-q3 → hard）。

K2、K3 中靠逐题判定的部分写在题目的 `trap_kind`、`trap_mechanism` 字段里，盲标时应由 B 独立判断。
