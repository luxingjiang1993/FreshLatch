# RET-01.3 第四轮草稿汇总

Ronin 代理人（模型）起草，2026-10-07。全部内容**未经人工审核**。

本轮只出草稿：v2/v3/v4、final/、仓库都没改；没 commit；没有调用任何 API（题目和语料都是我直接写的）。

## 依据：owner 13:16 的决定
- D2 选甲：category 按证据判，用 TRAP-DEFINITIONS-draft.md 的推荐定义（快照取代 / 同快照冲突陈述 / 元陈述；未重测并入元陈述）。
- D3：s6-d1-c4-q1 计 trap。
- D4：s7-d3-t1-05-q3 计 hard。
- D5：s5-d0-t0-01-q1 暂计入，待 owner 抽看。
- s6-d2-g2-q1 按方案 A 处理。
- 先补题，再开 PR。

## 大白话
1. 按新规则重判后，现有题里真正带陷阱的 arm 题只有 **15/168 = 8.93%**。
2. 新题加进来，分母也会变大。要达到 30%，至少要新增 51 道陷阱题，再留 3 题余量，共 **54 题**。
3. 现有语料里能挖出的真陷阱题只有 **6 题**，其余 **48 题**要配 **新写的语料（32 篇、96 块）**。
4. 全部加上后，离线 check_x1 退出码为 0：arm 222 题，L60 / P117 / MH45，trap+adv **69/222 = 31.08%**（需 67，余 2），去污染 0，LCS 旗标 0。

## 各项

| 项 | 结果 | 文件 |
|---|---|---|
| 1. category-rule-v2 | 211 题中 39 题变动；trap+adv 15/168 = 8.93%，与草案一致 | `category-rule-v2/`：questions.category-v2.json、category-compare.tsv、RULE.md、summary.json |
| 2. s6-d2-g2-q1 方案 A | 题目删去「旧法施行日期」子问；对应要点 4 条减为 3 条；memo 改为「旧法（2018修正）自二〇一八年十月二十六日起施行」，与 flk 一致；剩余 3 条要点仍是原文子串；qtype 仍为 lexical | `s6-d2-g2-A/`：memo 副本、memo.diff、题目 diff、check.json |
| 3. 补题第一部分（现有语料） | 6 题，都是同快照冲突（K2）；P4 / MH2；自查全部通过（P/MH 的 r8 都是 0，LCS < 0.8，要点全是子串） | `part1/questions.part1.json` |
| 4. 补题第二部分（新语料） | 16 个批次、32 篇文档、96 块，全部标 synthetic；48 题：K2 32 题、K3 16 题；L9 / P30 / MH9；自查全部通过 | `part2/units.py`（源稿）、`part2/corpus/`、`part2/questions.part2.json` |
| 预计最终 | arm 222：L60 / P117 / MH45（每型 ≥30），trap+adv 69/222 = 31.08%；check_x1 退出码 0；chunk 788，合成占比 82.9% | `build-summary.json` |

### 缺口怎么算的
- 现有陷阱题 15 道，arm 题 168 道。需要满足 (15 + x) / (168 + x) ≥ 0.30，得 x ≥ 50.57，所以 **x = 51**。
  - 校验：x = 50 时为 65/218 = 29.8%，不够；x = 51 时为 66/219 = 30.14%，够了。
- 加 3 题余量，共 54 题。现有语料挖出 6 题，需要新写 **48 题**。
- 结果 69/222，按 ⌈0.3 × 222⌉ = 67 算还余 2 题。余量只剩 2，是因为分母也跟着变大了。

### 第二部分的结构
每个批次有两篇独立材料，都在同一个快照里：
- 旧口径的一篇：p1 写错误或过时的值，p2 写一句元陈述（「未复测 / 无新数据 / 待发布 / 未入账 / 不再列入跟踪」），p3 是无关内容。
- 权威的一篇：p1 写现行值并说明依据，p2 写实测值，p3 是无关内容。

每个批次出 3 题：
- qa：问现行值，错误的一侧放在 distractors。
- qb：问两边各怎么说，两侧都在 relevant。
- qc：问实测值，元陈述那块放在 distractors。

体裁和快照分布：S2 / S3 / S4 / S6 各 3 批，S1 / S5 各 2 批；领域 D0–D3 都有；T1 11 批，T0 5 批。

## 风险
1. **新题和新语料是模板化写的**：16 个批次都是「两篇材料 + 三题」的结构，问法也相近。可能带来：
   - 题目风格单一；
   - 「哪份更可信」这类线索被模型学到；
   - 语料里的「更正 / 以…为准」等词让词法臂占便宜。
   
   建议 B 盲标时专门看这一点，必要时改写一部分。
2. **新增 96 块会改变 BM25 / dense 的检索环境**：现有 211 题的 qtype 和自查都没变（check 通过），但检索结果会变。这是语料扩充的正常代价，需要在 PREREG 写明。
3. **r4m-s5-d3-t1-05-q6 与现有的 s5-d3-t1-05-q1 题意相近**（一个问最新比例，一个问变化）。可删；删掉后余量变成 1。
4. **余量只有 2 题**：B 盲标若否掉 3 题以上，就会掉到 30% 以下。可以考虑多补几题。
5. **D5 边界题仍算在 15 题里**：若 owner 抽看后不算，缺口加 1，余量变成 1。
6. **新批次 id（`*-91`）不在 draft-spec.json 里**，并入时需要在 spec 和 manifest 里登记。新文档的 frontmatter 没有写「起草人」字段，以免影响解析；起草人记在本文件和各 JSON 的 meta / drafted_by 里。

## 需 owner 决定
1. 第二部分新语料和 48 题能不能并入 v2/drafts。**建议**：先抽看 2–3 个批次，再授权。
2. 要不要删 r4m-s5-d3-t1-05-q6（近重复）。**建议**：保留到 B 盲标后再定。
3. 余量是否加大到 5 题，即再写 1 个批次、3 题。**建议**：加，因为盲标可能否掉题。
4. 抽看 D5 边界题 s5-d0-t0-01-q1。

## 并入步骤（都还没做）
1. owner 授权后，把 `part2/corpus/t0|t1/*.md` 拷进 v2/drafts/corpus。用 `s6-d2-g2-A/s6-d2-g2-memo.md` 替换 memo，并按第二轮做法备份、记录前后 sha256。
2. 把第一部分 6 题和第二部分 48 题交给 **B 模型盲标**：B 只看 query、as_of 和语料，不看我（A）的 relevant、answer_points、distractors 和 category。
3. 按 PROTOCOL 合并：
   - 影响打分的分歧交 owner 审；
   - 一致的题按约 20% 分层抽样复查；
   - qtype 按 kw-v1 计算；
   - category 按 category-rule-v2 计算。
4. 定稿 category-rule-v2：
   - 更新 rules_v4.py、PROTOCOL.md（需授权）；
   - 新题的 trap_kind 和机制写进 eval_intent；
   - final 题集用 category-v2 副本，并加上 s6-d2-g2-q1 的改动。
5. 重跑 check_x1：确认退出码 0、每型 ≥30、trap+adv ≥30%、去污染 0；更新 LABELING-PROVENANCE 和 SOURCES.md 的相关节。
6. 之后才按 REVIEW-NOTES §18 开 PR。

## 复现
```
cd /workspace/x1-labeling/ronin-review/round4
X1_OUT=/workspace/x1-labeling/v2/drafts env -u DASHSCOPE_API_KEY /workspace/venv-fl/bin/python build_round4.py
```
脚本离线运行，临时语料副本放在 /tmp/x1-ronin/round4/。
