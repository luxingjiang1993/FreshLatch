# Hard-Gold：过线与改臂决议设计评估

> **决议会话**: grill-with-docs · Hard-Gold 过线与改臂（[#257](https://github.com/luxingjiang1993/FreshLatch/issues/257)）  
> **决议日期**: 2026-10-03（三轮 grilling；共享理解已确认）  
> **决议落点**: 本评估、ADR-0033、`CONTEXT.md`、`docs/evidence/hard-gold-arm/`、roadmap Backlog「改臂另决议」  
> **上游**: I3 Hard-Gold **骨架**（ADR-0032 · #251 · `docs/hard-gold.md`）；增益门 I0 / `docs/eval-retrieve.md` §3；ADR-0003 / 0026

---

## 1. 问题 + 前置约束

I3 已交付 Hard-Gold **骨架**（难金标可跑、默认臂断言仍 bm25），但路线图写明：**改生产默认臂须另决议**。若不钉「过线布尔 / dense 前置 / 本波交付边界 / 实现票 Gate」，易出现：(1) 骨架报告或主张金标 all_hit 被误读为已换臂；(2) 无 dense 索引空跑 BM25 却谈过线；(3) grill 会话直接改 `PRODUCTION_RETRIEVAL_MODE`；(4) 事后改增益门凑绿（HARKing）。

| 前置 | 来源 | 锁死作用 |
|------|------|----------|
| 骨架 ≠ 授权换臂 | ADR-0032 · I3 ACCEPTANCE §4 | 本决议不回溯把 I3 升格为已换臂 |
| 增益门公式已预登记 | `docs/eval-retrieve.md` §3 · ADR-0003/0026 | 本波 **不另造门**、不事后改门 |
| 主张金标与 retrieve Hard-Gold 分轨 | CONTEXT · ADR-0026 | all_hit / control-c **不得**顶替本门 |
| 生产默认仍 bm25 | `PRODUCTION_RETRIEVAL_MODE` | 本决议会话 **不改** 该配置 |
| Anthropic 纪律 | CLAUDE.md 清单 | 冒烟/决策闸；不报方差/率；预登记 |

验收层：**冒烟 / 决策闸**（流程钉死；复跑与换臂落地分票）。

---

## 2. 候选路线（按决策维）

| 维度 | 候选（含被否） |
|------|----------------|
| 生死线 | (A) 只复跑难金标仍不改臂；(B) 过线才授权改臂实现票 / 不过线冻 bm25；(C) 过线本波直接改配置 |
| 过线门 | (A) 沿用 I0 增益门于 hard 集；(B) 另锁更严专用门；(C) 本波不谈过线只出报告 |
| 候选臂 | (A) 不适用；(B) hybrid；(C) dense；(D) hybrid+rerank；(E) 过线后实现票再选 |
| dense 前置 | (A) 必须有索引否则不得过线；(B) 无索引也可谈换臂；(C) 本波只跑 BM25 |
| 层身份 | (A) 冒烟/决策闸；(B) 升格测量层；(C) 过线=已换臂 |
| 证据落点 | (A) `docs/evidence/hard-gold-arm/`；(B) 挂 I3 下；(C) 只 ADR 无 ACCEPTANCE |
| 本波交付 | (A) 先四件套钉流程，复跑另票；(B) grill 当场建 dense+判过线；(C) 只改 roadmap 一句 |
| 过线布尔 | (A) dense+臂对比+Hybrid 门成立→授权，Rerank 单记；(B) Hybrid+Rerank 都开；(C) BM25 能跑即过线 |
| 实现票信任 | (A) Gate 人终收；(B) Watch；(C) 评论里直接改配置 |

---

## 3. 逐路线评估

| 维度 | 拍板 | 被否理由 |
|------|------|----------|
| 生死线 | **B** | A 无出口；C 把测量与改配置绑死、难回滚 |
| 过线门 | **A** | B 易 HARKing；C 与「另决议」空转 |
| 候选臂 | **E** | 未跑 hard 臂对比前锁 B/C/D 过早；A 否定生死线 B |
| dense | **A** | B/C 无臂对比则 Hybrid 门不可判 |
| 层身份 | **A** | B 成本高须另锁 N；C 与 Q1=B 冲突 |
| 证据 | **A** | B 与「骨架≠换臂」糊读；C 违验收可勾 |
| 本波交付 | **A** | B 搅 grill/测量；C 违四件套 |
| 过线布尔 | **A** | B 被历史 rerank 持平卡死；C 空过线 |
| 实现票 | **A** | 默认臂难反转；B/C 跳过人 Gate |

**Anthropic 清单命中（主动修正）：**
1. **演示可过 ≠ 测量可信**：本波钉流程 ≠ hard 已过线；骨架报告禁止升格。  
2. **随机系统**：过线主判据为 retrieve 增益门（确定性指标轨），不绑单次主张金标 LLM。  
3. **默认不是规格**：增益门谓词沿用 I0 预登记原文；解码若出现须入报告。  
4. **词表**：过线/改臂授权闸进 CONTEXT；具体 R@10 数字不进 glossary。  
5. **预登记**：过线布尔、dense 前置、证据目录 — **先于复跑写死**。  
6. **复现两层**：门判决与默认臂断言逐位；跨会话托管端点近似复现声明沿用 I0。  
7. **ADR 三条件**：齐备（见 ADR-0033）→ 记 ADR。

**被否原推荐（写透）：**
- 「grill 当场改 `PRODUCTION_RETRIEVAL_MODE`」——否：与 Gate 实现票冲突。  
- 「无 dense 也可过线」——否：Hybrid/Rerank 门失去可判定输入。  
- 「必须 Rerank 门也开才授权」——否：历史持平易永冻；与「实现票再选臂」冲突。  
- 「挂在 I3 evidence」——否：面试易听成 I3 已换臂。

---

## 4. 拍板 + 逐项子决策

1. **生死线**：预锁门 → 复跑 → **过线才开改臂实现票**；不过线则正式冻结 bm25。  
2. **门**：I0 / `docs/eval-retrieve.md` §3 增益门，在 **hard 集**上复跑；禁止事后改门。  
3. **选臂**：本波不定具体默认臂；过线后 **Gate** 实现票再选。  
4. **dense**：复跑前必须 `data/dense/index.sqlite`；建不成 → 不得判过线，标「需索引」，冻 bm25。  
5. **过线布尔**：dense 齐 ∧ hard 臂对比落盘 ∧ **Hybrid 通过线在 hard 上成立** → 书面授权开改臂实现票；Rerank→生产门单独记开/关（不开不挡「可讨论 hybrid」）。  
6. **层身份**：冒烟/决策闸；不报方差/通过率；过线 ≠ 已改生产臂 ≠ 统计显著。  
7. **证据**：`docs/evidence/hard-gold-arm/`（与 I3 骨架分目录）。  
8. **本决议交付**：评估四件套钉流程；**dense+hard 复跑另票**；本会话不改 `PRODUCTION_RETRIEVAL_MODE`。  
9. **改臂实现票**：Trust=**Gate**；须引用 hard 报告路径与门判决。

### Exit 预锁（本决议 = 流程钉死）

| # | 硬条 |
|---|------|
| E1 | 评估 + ADR-0033 + CONTEXT + roadmap 补行齐 |
| E2 | `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 文首声明：流程已钉 · **复跑未跑** · **未过线** · **未换臂** |
| E3 | 跟进票存在：dense 索引 + hard 臂对比复跑（按 Q8 判过线） |

### Out（偷渡一票否决）

本决议直接改 `PRODUCTION_RETRIEVAL_MODE`；宣称 Hard-Gold 已过线/已换臂；用主张金标或 control-c 顶替 retrieve hard 门；无 dense 判过线；事后改增益门；报方差/显著；把 n=36 冒烟称作 Hard-Gold 已过；渗透认证。

---

## 5. 工程手段总登记册

| 手段 | 原理 | 优势 | 代价 | 参考先例 | 本期处置 |
|------|------|------|------|----------|----------|
| 过线布尔预锁 | Hybrid 门@hard + dense 前置 | 可执行、防空转 | 依赖建索引成本 | I0 增益门 | **实装**（流程） |
| 沿用 I0 门公式 | 不另造门 | 防 HARKing | 不能「为本波放宽」 | eval-retrieve §3 | **承载** |
| 选臂推迟到实现票 | 先过线再选 | 避免未跑数锁臂 | 多一跳 | Q3=E | **实装**（流程） |
| 证据分目录 hard-gold-arm | 与 I3 骨架隔离 | 防误读已换臂 | 多一目录 | i3 vs 本决议 | **实装** |
| dense 索引构建 | 臂对比输入 | 门可判 | 需 Key；产物 gitignore | `scripts/build_dense_index.py` | **触发**（复跑票） |
| hard 臂对比复跑 | `eval retrieve --hard` | 数字真相源 | 本波不在 grill 跑 | hard-gold.md | **触发**（复跑票） |
| 改臂实现票 Gate | 人终收改默认臂 | 难反转有闸 | 不能 AFK 偷改 | AGENTS Trust | **留位**（过线后） |
| grill 当场改 PRODUCTION_* | 决议即换臂 | — | 违 Gate/预锁 | — | **弃** |
| 无索引过线 | 只 BM25 hard | — | 门不可判 | — | **弃** |
| 主张金标顶替 | all_hit=换臂 | — | 分轨违纪 | — | **弃** |

---

## 6. 面试讲法（grilling 预案）

**Q: I3 不是已经做过 Hard-Gold 了吗？**  
A: I3 是**骨架**（难卷能跑、默认仍 bm25）。本决议钉的是**过线与改臂授权闸**；骨架绿 ≠ 已换臂。

**Q: 为什么过线了还不直接改默认臂？**  
A: 改 `PRODUCTION_RETRIEVAL_MODE` 难反转，必须 Gate 实现票引用 hard 报告；本决议只授权「可以开那张票」，不替人点合并。

**Q: 为什么 Rerank 门不开也能授权？**  
A: 授权的是「开实现票讨论换臂」；实现票仍须按已开门的路径选臂。Rerank 历史易持平，不宜挡死 hybrid 讨论。

**Q: 主张金标 12/12 能不能当过线？**  
A: 不能。那是另一轨（claim gold）；换臂门只认 retrieve hard 集 + 增益门。

**Q: 这算检索 SOTA 或已换 hybrid 吗？**  
A: 不算。层=冒烟/决策闸；复跑未跑前**未过线**；过线后仍须 Gate 实现才改配置。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-03 | 初版：#257 grill 三轮全认推荐；共享理解确认；四件套落盘 |
