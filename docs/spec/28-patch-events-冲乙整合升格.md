# 规格卷 28 — patch_events 冲乙整合升格（仪器 · 门闩 · PE-Y 继承切分）

> **to-spec 来源**: 地图 [#517](https://github.com/luxingjiang1993/FreshLatch/issues/517) · 决议 #518/#519/#520（均「按推荐」）· Matt `/to-spec`（本仓按 [to-spec 模板](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md) 合成，**不再访谈**）  
> **ADR**: ADR-0039 · ADR-0040 · ADR-0041（继任 ADR-0037 / 0038）  
> **协议**: `docs/evidence/patch-events/PREREG-Y.md`（**未激活** · 已合入整合升格 / 仪器 / 门闩 Amendment）  
> **评估**: `docs/research/冲乙预注册载体相对PREREG-Y设计评估.md` · `冲乙共享仪器最小集设计评估.md` · `冲乙门闩与冒烟功率条款设计评估.md`  
> **先验卷**: 卷 27（路线 Y 只冲乙骨架；本卷为其**增量升格**，不废卷 27 已派 PE-Y-01…04 的继承价值）  
> **卷号**: 28  
> **语言**: 中文。技术词保留 English 原词。  
> 本页不是论文，不激活正式主跑，不发模型，不回写 B/C 冻结页，不填 RESULT-Y 成立格冒充已跑，**不保证乙**。

## Problem Statement

冲乙决议已齐（载体=升格 `PREREG-Y`、仪器最小集、门闩/冒烟），但工程侧仍停在「卷 27 旁路骨架 + 语料扩容」与「仪器/敏感性尚未实装」之间：`verify_edit` 仍逐字且 `score` 恒空；敏感性闸与 n=30 冒烟无缝；GATE-Y 人令序未写入敏感性硬前置。若不把 **PE-Y 资产继承切分**写清，实现票会误开 Z 页、误改 n、或跳过敏感性直接探针。

## Solution

在**不另开字母预注册页**的前提下，把 #518/#519/#520 合入升格未激活 `PREREG-Y`，并派工：哪些 PE-Y 资产**原样继承**、哪些**修订重开**、哪些**新开**。主缝仍是旁路 formal-y / GATE-Y / 敏感性与冒烟报告 / `verify_edit` 赋分——**不**新造 `compare_*`。过敏感性与过门闩之前不得正式主跑。

## 主缝（Testing Seams）

优先既有缝，少开新缝：

1. **`verify_edit` 出缝**（改实现，保 `ok`/`score`/`reason` 键）：NLI + 非空分 / `−∞`。  
2. **`compare_primary` 入缝**（只读消费）：固定 k 排序吃非空分；禁止为乙新造比较器。  
3. **报告旁路缝**：`GATE-Y-SENSITIVITY.md` · `SMOKE-Y-N30.md` · 既有 `GATE-Y-PROBE.md`（可扔；不进 RESULT-Y）。  
4. **formal-y 激活守卫缝**（继承 PE-Y-01）：未激活 / 无人令拒绝发送。

## PE-Y 继承切分（本卷核心表）

| 资产 / 票 | 处置 | 说明 |
|---|---|---|
| PE-Y-01 `formal-y` 旁路 | **原样继承** | 默认不发；激活守卫；路径 `formal-generations-y.jsonl` |
| PE-Y-02 `GATE-Y-PROBE` 过门 Cond | **继承 Cond · 修订前置** | 过门仍 k≥10∧T−C点>0；须接敏感性硬前置 + ADR-0040 机制针 |
| PE-Y-03 n=400 名单 / CORPUS | **原样继承** | 缺额纪律 ADR-0038；扩容针可加载≠激活 |
| PE-Y-04 RESULT-Y 成立口径 | **原样继承** | 仅 T−C∧点>0.05∧下界>0；禁甲 |
| PE-Y-05 激活+正式主跑 | **仍 Gate · 前置加严** | 敏感性→冒烟→真数据过门→双人令后才可派 |
| PE-Y-06 消融/抽检（可选） | **留位** | 不改成立格 |
| `verify_edit` / score 空分 | **作废重开** | 换 NLI；released 有限分；reject=`−∞` |
| 敏感性闸 | **新开** | `GATE-Y-SENSITIVITY`；ρ 预锁 |
| n=30 冒烟 | **新开** | `SMOKE-Y-N30`；坍缩检测；不作过门 |
| 旧 `PREREG.md` / B / C | **不承载** | 主证据作废关系保持；禁止回写 |
| 另开 `PREREG-Z` | **弃** | #518 已否 |

## User Stories

1. As a 评测工程师, I want `verify_edit` 对绑定 chunk 与 `after_text` 给出 NLI `ok` 与非空 `score`, so that 固定 k 不再退化为 claim_id。  
2. As a 评测工程师, I want rejected 样本 `score=−∞`, so that hard reject 不能靠字典序挤进固定覆盖。  
3. As a 纪律官, I want 敏感性闸在真数据探针前强制通过, so that 带病核验器不能进 GATE-Y。  
4. As a 纪律官, I want n=30 冒烟报告三臂 fixed 集是否坍缩, so that 仪器卫生问题在发模型前可见。  
5. As a 纪律官, I want 冒烟与敏感性永不单独构成 `gate_passed`, so that 门闩层身份不被倒置。  
6. As a 纪律官, I want GATE-Y 过门仍只看 k≥10 与 T−C 点>0, so that 门闩不是乙成立尺（0.05）的预演。  
7. As a 抄表守门人, I want RESULT-Y 成立口径保持仅 T−C∧点>0.05∧下界>0, so that #518 拍板不被 to-spec 改矮。  
8. As a 路径守门人, I want formal-y / GATE-Y / n=400 名单原样继承, so that 不因仪器票重写整条旁路。  
9. As a 密钥守门人, I want 探针令与正式激活令分开且敏感性前置写死, so that Agent 不能自批主跑。  
10. As an 面试讲解者, I want 继承切分表可指, so that 「为什么不新开 Z / 为什么改 verify」有文档锚。  
11. As a wayfinder, I want 新票只覆盖仪器·敏感性·冒烟·GATE 前置修订, so that 不重复派已 DONE 的 PE-Y-01…04。  
12. As a 预注册守门人, I want Amendment 落在未激活 `PREREG-Y`, so that 不回写已跑旧页、不另开字母页。  
13. As a 复现者, I want 型号 id 与 τ 写入协议, so that 换卡必须 Amendment。  
14. As a 统计读者, I want C 臂仍走 `coverage_c` 且无核验分, so that 第一主比较对照语义不变。  
15. As a 臂维护者, I want B1/B2 拒识口径抄死且乙不强行差异化, so that 实现不发明甲式拉开。  
16. As a 文档守门人, I want 可扔报告路径固定, so that 敏感性/冒烟/GATE 不污染 RESULT-Y。  
17. As a 止损官, I want 敏感性失败只允许未激活收紧 τ 一次并重测, so that 禁止放宽凑绿。  
18. As a 地图维护者, I want 本卷派工后可 enrich / before-implement, so that #517 Destination「决议清晰→to-spec」闭合。  

## Implementation Decisions

1. **载体**：升格未激活 `PREREG-Y`（ADR-0039）；禁止 `PREREG-Z`。  
2. **正式 n**：400；缺额不可激活（ADR-0038）。  
3. **成立尺**：仅 T−C；点>0.05∧下界>0；不得甲。  
4. **主核验**：本地 mDeBERTa-v3 XNLI；`ok`⇔entailment∧P≥τ；released `score`=P(entailment)；rejected=`−∞`（ADR-0040）。  
5. **比较器**：不改 `compare_primary` 数学；不新造 `compare_y`。  
6. **门闩 Cond**：继承 k≥10∧T−C点>0；方向门 ≠ 成立尺。  
7. **前序**：敏感性 →（可选夹具）→ n30 冒烟 → 真数据 GATE-Y → 激活批注 → 正式人令 → formal-y 一次（ADR-0041）。  
8. **模块**：`patch_events_verify`（重开）；GATE-Y 探针模块（修订前置检查）；新敏感性/冒烟报告写入器；formal-y（继承）。  
9. **产物路径**：`GATE-Y-SENSITIVITY.md` · `SMOKE-Y-N30.md` · 既有 `GATE-Y-PROBE.md` · `formal-generations-y.jsonl`。  
10. **解码**：生成仍 `qwen-flash` / temp=0 / Decoding.seed=`20261007` / API seed=`None`（继承）。  

## Testing Decisions

- 好测试只断言缝外行为：给定核验入参得到 `ok`/`score`；给定固定夹具得到敏感性通过布尔；给定三臂记录得到 `collapse`；GATE 判定表与层身份「可扔」。  
- 不测 NLI 内部张量；不把仓外 XNLI Acc 写成验收绿。  
- 先验：`tests/unit/test_pe_gate_y_probe.py` · formal-y / compare_primary 单测族。  
- 零密钥默认；发模型仅人令票。  

## Out of Scope

- 激活 `PREREG-Y`；正式 n=400 主跑；填 RESULT-Y 成立格；保证乙  
- 冲甲 / Findings / AIS 盲审；复活 A；回写 B/C；另开 Z  
- 改生产 `PRODUCTION_RETRIEVAL_MODE`；金标进 score  
- Industry/Demo 投稿物料另图  
- 本会话 `/implement` 业务代码（留给 enrich → before-implement → 新会话 implement）  

## Further Notes

- 卷 27 派工的 PE-Y-01…04 若仍在开 PR 未合入 main：合入序建议 CORPUS/名单 → formal-y/GATE-Y/RESULT-Y → 本卷仪器/敏感性/冒烟修订票。  
- 探针人令逐字：「授权路线 Y 仓外探针发模型；不得激活。」  
- 正式人令逐字：「批准激活 PREREG-Y 并正式主跑一次。」  

## 票序建议（供 `/to-tickets` · enrich）

| 序 | 票 ID | 内容 | 继承关系 | Trust |
|---|---|---|---|---|
| 1 | PE-Y-INST-01 | `verify_edit`→NLI；score 有限/`−∞`；禁 None | **重开** verify 缝 | Watch |
| 2 | PE-Y-SENS-01 | `GATE-Y-SENSITIVITY` 夹具+通过线 S1–S4 | **新开** | Watch |
| 3 | PE-Y-SMOKE-01 | `SMOKE-Y-N30`（k/方向/坍缩/score） | **新开** | Watch |
| 4 | PE-Y-GATE-REV | GATE-Y 接敏感性前置 + ADR-0040 机制针文案/守卫 | **修订** PE-Y-02 | Watch |
| 5 | PE-Y-01…04 | formal-y / GATE Cond / n400 / RESULT-Y | **原样继承**（合入既有 PR） | Watch |
| 6 | PE-Y-05 | 激活+一次正式主跑 | **Gate**；前置=敏感性∧冒烟∧过门∧人令 | **Gate** |
