# ADR-0040: patch_events 冲乙共享仪器最小集（非空 score · NLI 核验 · B 臂记账）

- **状态**: Accepted
- **日期**: 2026-10-10
- **相关**: `docs/research/冲乙共享仪器最小集设计评估.md`；[#519](https://github.com/luxingjiang1993/FreshLatch/issues/519)；父图 [#517](https://github.com/luxingjiang1993/FreshLatch/issues/517)；载体 ADR-0039 / #518；上游 ADR-0037；仓外原料 #521 / PR #522；门闩接口 #520；整合参考 `docs/research/冲甲冲乙行动方案整合.md` §2
- **说明**: 编号顺延开 PR 上的 0034–0039 之后。仪器写入**升格未激活** `PREREG-Y`，不另开字母页；不回写已跑旧 `PREREG.md` / B / C。

## 背景

旧 `RESULT` 链上 `verify_edit` 的 `score` 恒 `None`，`compare_primary` 固定 k 经 `_top_positions` 退化成 `claim_id` 序，三臂同批 → T−B* 差结构性不可测。整合方案要求非空支撑分、拒识不得混进固定 k、支撑度核验替代逐字一致。#521 给出 pe_v2 中文域候选可操作性；#518 已钉载体为修订升格 Y。本窗拍最小可执行仪器集。

三条件齐备：

- **难反转**：后续 `/to-spec`、`verify_edit` 实装、#520 敏感性闸与一次正式主跑将引用本公式与型号；事后改回逐字或放宽允许 `None` 会使仪器针作废。
- **反直觉**：冲乙不判 B1/B2 成立，却仍把拒识口径写入预注册；主核验选通用多语 NLI 而非「形更近」的英文 MiniCheck/AttrScore。
- **真实取舍**：−∞ vs 仅放行集过滤；mDeBERTa vs 英文零样本 vs 逐字；乙记账 vs 乙强制拉开 B 臂。

## 决策

1. **非空 `score`（默认针）**  
   - **released**：有限非空支撑置信；推荐 `score = P(entailment) ∈ [0,1]`。禁止 `None`。  
   - **rejected**：`score = −∞`（浮点）。禁止 `None` 混池；不得靠字典序进固定 `k`。  
   - **C**：无核验分；固定 `k` 仍 `coverage_c`。  
   - 禁止金标 / 评委 / 用户裁决进 `score`。高分只用于固定 k **排序**，不单独定义放行。  
   - **允许等价形**：自然放行集内再按分取前 k（reject 物理不进池）。预注册须写死默认针或等价形之一；推荐默认针（贴现行全体候选 `_top_positions`）。

2. **主核验 = 本地 mDeBERTa-v3 XNLI**  
   - 型号：`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`。  
   - `premise = evidence_text`（绑定 chunk），`hypothesis = after_text`。  
   - `ok` ⇔ `argmax = entailment` 且 `P(entailment) ≥ τ`；`τ` 跑前小标定锁死。  
   - 敏感性闸与通过线细则归 #520；可收紧 τ，禁止事后放宽凑绿。  
   - Limitations：MT 训练降质；通用 NLI ≠ 法条支撑；#521 仓外 Acc ≠ 本仓过线。  
   - **留位**：MiniCheck / AttrScore / SummaC / TRUE / ALCE / FActScore 不为主核验。  
   - **标定原料（非打分器）**：`verified-chinese-law-kb`、`legal-hallucination-bench`。  
   - **弃**：逐字一致作主核验；LLM 评委接管 `verify_edit`。

3. **B1/B2：乙只记账 + 拒识口径抄死**  
   - 乙成立只判 T−C；B1/B2 报告-only。  
   - 四臂共用同一 `verify_edit` 公式。预注册继承并抄死：  
     - T：绑定失败 reject；核验不过 **hard reject**。  
     - B1：事后核验不过 **hard reject**；**不要求**策略 ≠ T。  
     - B2：核验不过 **不** hard reject；`reverify_ok` 记账。  
   - 乙不强行差异化 B1/B2；拉开拒识属甲图 Out。

4. **载体与词表**  
   - 写入升格未激活 `PREREG-Y` Amendment（#518）。  
   - `CONTEXT.md` 可收「支撑度核验（pe_v2 NLI 闸）」；τ/公式/成立细则不进词表。

## 后果

- `/to-spec` 可换 `verify_edit`、赋分、夹具证明 reject 不进固定 k；仍不得激活主跑。  
- #520 在本公式之上锁敏感性/冒烟/激活门闩。  
- 违例：`score=None` 混池；金标进 score；回写旧 PREREG/B/C；把 #521 数字当乙；乙强制甲式 B 臂差；未过门激活。

## 替代方案（被否决）

- **保留 score=None**：仪器坍缩。  
- **英文 MiniCheck/AttrScore 作主核验**：无中文法律一手；装过线。  
- **继续逐字主核验**：根因未除。  
- **LLM 评委主核验**：漂移；非本地针。  
- **乙省略拒识口径**：实现易发明。  
- **乙强制 B1≠T**：甲前置；Out。  
- **评委/金标进 score**：泄漏；禁令。
