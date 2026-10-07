# RET-01.3 x1 题集标注协议（v4 精简版）

**标注者。** 211 道草稿题由两个模型各自独立标注：
- **A**：本助手起草的标注（`v2/gold-draft-v2.json`）。
- **B**：Cursor 云端代理（GPT-5.6 Sol）盲标，标注时没看过 A。

两者都是模型，不是人。人不手填 relevant / distractors；qtype 由下面的规则计算，owner 只能逐题改并写明原因。最终取哪个标注由 owner 决定，或按下面写明的固定规则决定。

**一致度（A 对 B）。**
- qtype 一致 141/211，κ=0.44。
- arm/护栏一致 193/211，κ=0.73。
- relevant 完全一致 141/211，平均 Jaccard 0.835。
- answer_points 等价 102/211。
- category 一致 136/211，κ=0.32。

任一字段不一致，或任一方提出问题，这道题记为分歧。分歧 165 题，一致 46 题。

**owner 审核范围（共 116 行）。**
1. 影响打分的分歧 95 题：触发项含 relevant、arm/护栏，或 B 提出问题。category 分歧在同一行里一并列出，由 owner 决定。
2. 一致题中的抽样 9 题（约 20%）：按场景×qtype 分层，用种子 20261007 抽取。
3. 12 条语料内容修正。

**不经 owner、按固定规则处理的题。**
- 其余 70 道分歧题：分歧只出在 qtype / answer_points / distractors / A 的复核旗标上。（任务说明写的是 55 题，实际是 165−95=70 题。）
- 37 道未被抽中的一致题。

规则如下（版本号写进 `LABELING-PROVENANCE.json`）：
- **qtype**（规则 qtype-kw-v1，owner 于 2026-10-07 选定；同一函数用于全部 211 题，owner 审的题可以逐题改）：
  1. 删去法规名白名单后，问句与 relevant 的字符 8-gram 重合率 r8 > 0.2 → lexical。超过 0.2 的题当 paraphrase / multi_hop 就是去污染命中。
  2. 关键词覆盖率 ≥ 0.8 → lexical。
  3. multi_hop 结构成立 → multi_hop。要求：arm 题；relevant 来自 ≥2 个 doc_id；要点 ≥2 条；没有单个 chunk 含全部要点；全部要点不落在同一个 doc_id。
  4. 其余 → paraphrase。

  **冗余证据不算 multi_hop（owner 2026-10-07 决定 2）**：若 relevant 里有两块或以上各自都能单独答全题目（每块单独就含全部要点所需的事实），该题不算 multi_hop，判 paraphrase（lexical 门命中的仍是 lexical）。kw-v1 的 multi_hop 结构判断识别不了这种情况，规则函数本身不改（锁定为 kw-v1），由审核者逐题改判并在 qtype 理由里写“冗余证据，非多跳”。只有题面要求合并时才保留 multi_hop：两个子问的答案分在不同文档，或明确要求“列出哪几种/各自”。理由：multi_hop 全命中要求每块都召回，冗余证据会把单跳题错算成多跳。

  关键词：先删 T0/T1、法规名白名单和条号等出处引用，再取引号片段、拉丁字母编号、数字（含带单位的汉字数量），以及仓库 BM25 分词（jieba 0.42.1）切出的 ≥2 字汉字词。停用词表写死在 rules_v4.py 的 KW_STOP。覆盖率 = 能在 relevant 原文里原样找到的关键词 ÷ 关键词总数。阈值 0.8 在 A、B qtype 一致的 141 题上标定（吻合 120/141），与配额无关。8-gram 只作去污染门，不定义题型；旧的“r8 > 0.2 才算 lexical”口径只能得到 6 道 lexical。
- **relevant（证据口径，owner 2026-10-07 决定 1）**：relevant 只放回答问题所需的块。只用来定位题干限定语（哪家公司、哪一版模型、哪份文档、“渗透率回落到66.2%的那家公司”之类）的块不算答案证据，不进 relevant，也不从中取要点；可以留作干扰。理由：recall 按命中计，定位块进 relevant 会把“找对了限定语、没找到答案”也算成命中。审核时如发现定位块，移出 relevant 后按 kw-v1 重算 qtype。
- **法条题的证据口径（owner 2026-10-07 第二轮决定 2）**：p1 法条题（p1-* 批次）以法条原文块为证据；S6 顾问备忘、解读材料只在 S6 题里算证据。备忘里即使有一句话概括了法条要点，也不进 p1 题的 relevant，不据此把 p1 多跳题改判单跳（例：p1-mh-06-new 维持 multi_hop，s6-d2-g1-memo#p2@T1 不算它的证据）。
- **answer_points**：A、B 合并。被截断的要点补全到原文下一个标点；只保留 relevant 原文的子串；去掉只复述题干的要点；去重时保留较长的一条。
- **distractors**：A ∪ B，去掉 relevant。arm 题只保留同快照的块；护栏题保证至少有一个 T0 块。
- **category**：按顺序套用，取第一条命中的。
  1. 护栏题 → trap。
  2. 带 conflict_pair，或含工单 C1–C4 的同快照新旧条文对 → trap。
  3. S7 → 取 A、B 一致的值，不一致取 trap。
  4. S5 → trap。
  5. 其余 → hard。

  arm 题 trap+adversarial 占 30.9%，比 30% 地板只多 1 题。陷阱三类的定义尚未签核，S5/S7 归为 trap 是本规则的约定，不是已签定义。

**可行性。** 把 95 题全部按建议填、其余按规则，在 /tmp 合并后跑 check_x1：
- 退出码 0。
- lexical 53 / paraphrase 66 / multi_hop 49（与 forced 合并草稿相比有 42 题不同）。
- arm 168 / 护栏 43，chunk 692，合成 80.5%，去污染命中 0。

**溯源。** `LABELING-PROVENANCE.json` 逐题记录以下内容：
- 来源：consensus / rule-merged / owner-resolved / owner-audited；
- 决定和说明；
- 标注者；
- 抽样种子；
- 规则版本；
- 哪些字段来自规则。
