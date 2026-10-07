# ADR-0033: Hard-Gold 过线与改臂授权闸（流程钉死 · 本波不换臂）

- **状态**: Accepted
- **日期**: 2026-10-03
- **相关**: `docs/research/Hard-Gold过线与改臂决议设计评估.md`、[#257](https://github.com/luxingjiang1993/FreshLatch/issues/257)、`docs/evidence/hard-gold-arm/`；上游 ADR-0003 / 0026（增益门与默认臂）、ADR-0032（Hard-Gold 骨架不改臂）

## 背景

I3 交付 Hard-Gold 骨架后，改生产默认臂仍处「另决议」空位。若不钉过线布尔、dense 前置与实现票 Gate，易把骨架报告、主张金标或无索引的 BM25 hard 跑分误读为已授权换臂，或在 grill 会话直接改 `PRODUCTION_RETRIEVAL_MODE`。

三条件齐备：难反转（后续复跑票与改臂实现票将引用本闸）；反直觉（名叫 Hard-Gold 决议却本波不换臂、甚至不在本票复跑；Hybrid 门成立即可授权开票而 Rerank 可不开）；真取舍（流程先钉 vs 当场跑数；沿用 I0 门 vs 另造门；证据分目录 vs 挂 I3）。

## 决策

1. **生死线**  
   - 预锁过线判据 → dense+hard 复跑 → **过线才授权**开改臂**实现票**。  
   - 不过线（含无 dense）→ **正式冻结**生产默认 `bm25`。  
   - 本 ADR / 本决议会话 **不修改** `PRODUCTION_RETRIEVAL_MODE`。

2. **过线门**  
   - 沿用 I0 / `docs/eval-retrieve.md` §3 增益门公式，在 **hard 集**（`retrieve_hard_gold`）上判决。  
   - **禁止**事后改门凑过线（HARKing）。

3. **过线布尔（预锁）**  
   - 同时满足：  
     (a) `data/dense/index.sqlite` 已建；  
     (b) hard 臂对比报告落盘；  
     (c) **Hybrid 通过线**在 hard 集上成立。  
   - → 书面授权开改臂实现票。  
   - **Rerank→生产**门单独记录开/关；不开不阻挡「可讨论 hybrid」。  
   - 缺 (a)(b)(c) 任一 → 不过线。

4. **选臂**  
   - 本波 **不定** 具体默认臂；过线后由 **Gate** 实现票引用报告再选。

5. **层身份与未声称**  
   - 冒烟 / 决策闸；不报方差、不报通过率伪装、不声称统计显著。  
   - 主张金标 `eval run --gold`、假绿 control/control-c **不得**顶替本门。  
   - 过线 ≠ 已换臂。

6. **证据**  
   - `docs/evidence/hard-gold-arm/`（与 I3 骨架证据分目录）。  
   - 文首须能区分：流程已钉 / 复跑状态 / 过线与否 / 是否已换臂。

7. **词表**  
   - `CONTEXT.md`：Hard-Gold 过线与改臂授权闸（见评估链接）。

## 后续（2026-10-07）

本 ADR 正文仍记录 2026-10-03 那一轮：那次会话不改 `PRODUCTION_RETRIEVAL_MODE`。2026-10-07 Oriental Ronin 拍板 `docs/evidence/issue-284/DECISION-16.md` 的 16 条。拍板范围只是这 16 条，不是全库逐行人工审核。生产默认改为 `hybrid+rerank`。一键回退仍是 `set_retrieval_switch("bm25")`。缺向量仍记 `bm25_fallback`。切换后须先预热本地 embedding 权重，见 `docs/ops/local-embed.md`。

## 后果

- roadmap「改臂另决议」指向本 ADR 与 #257；下一跳 = dense+hard 复跑票。  
- 改默认臂必须另开 **Gate** 实现票，且引用 hard 报告与门判决。  
- 违例：无 dense 宣称过线；用 claim gold 顶替；本决议直接改生产臂；骨架报告称作已换臂。

## 替代方案（被否决）

- grill 当场改 `PRODUCTION_RETRIEVAL_MODE`。  
- 无 dense 索引仍判过线。  
- 必须 Hybrid+Rerank 双开才授权。  
- 另造更严门且可事后改谓词。  
- 证据挂在 I3 ACCEPTANCE 下易糊「I3 已换臂」。  
- 只改 roadmap 一句话、不做评估/ACCEPTANCE。
