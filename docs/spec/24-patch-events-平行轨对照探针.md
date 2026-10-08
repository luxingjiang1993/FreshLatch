# patch_events 平行轨 · 可识别更干净对照探针规格

> 来源：wayfinder #434 / grilling #435 → `/to-spec`  
> 词表：`CONTEXT.md`（patch_events 平行轨 · 同文四闸 · B1′ · 平行轨升级闸）  
> 权威 ADR：`0035`；评估：`docs/research/patch_events-平行轨可识别对照设计评估.md`  
> 旁路锁页：`docs/evidence/patch-events-alt/PROBE-LOCK.md`  
> 冲甲主链（平行、零 diff）：#431 / #432 / ADR-0034（若已合入）  
> **测试主缝（预锁）**：旁路同文四闸 → `compare_alt_natural` 产出自然放行率/自然误放率，且夹具上 T 相对 B2 与相对 B1′ 的自然误放差可非零；主 `compare_primary` 与旧/冲甲预注册正文本规格期间零 diff。  
> 语言：中文。技术词保留 English 原词。本规格**不**授权 wayfinder 会话内 `/implement`；**不**默认发模型。

---

## Problem Statement

冲甲主链用固定 k（路线 B 选取 R）追结果甲的可识别性。旧 n=30 在空分固定 k 下 T-B1/T-B2 差锁 0，说明现页仪表不可识别，但不回答：是否存在更干净、更贴产品叙事的对照（同文比闸、自然率、真事后 B1′）。若把这些改动直接写进主 `compare_primary` 或冲甲预注册，等于见主链结果后改主仪器，构成 HARKing。需要一条旁路规格：只新增 `compare_alt_*` 与 `docs/evidence/patch-events-alt/`，用夹具（及授权后小 n）检验设计是否「可分开」，再经预锁升级闸决定是否另开主论文级新预注册文件。

## Solution

交付平行轨**旁路探针缝**（冒烟 / 设计探针层）：

1. **同文四闸**：共享一份 `after_text`，C / T / B1′ / B2 只做闸判（信息集见下）。  
2. **主表 API**：`compare_alt_natural` —— 各臂自然放行率 + 自然误放率；T 相对 B1′、相对 B2 的自然误放差。  
3. **附录 API**：`compare_alt_fixed_k_appendix` —— 固定 k 误放（可只读复用 R 语义思想），**不**进升级闸。  
4. **夹具**：构造允许 T 拒、B2 放（及 B1′ 与 T 可分）的可非零自然误放差；零 LLM。  
5. **防火墙**：不改 `compare_primary`；不回写 `PREREG.md` / 冲甲预注册；不写主 `RESULT.md` 成立格；不称甲。  
6. **升级闸**：可分开 / 分不开 / 不值得升级 —— 本规格只把闸抄进可执行 Acceptance；升级决议另票。

证据根：`docs/evidence/patch-events-alt/`（PROBE-LOCK 已锁；夹具读数与可选小 n 只写本目录）。

## User Stories

1. As a 设计探针作者, I want 同文四闸在旁路缝可跑, so that 比较的是闸差不是四臂改写噪声。
2. As a 设计探针作者, I want 主表只报自然放行率与自然误放率, so that 不与冲甲固定 k 仪表糊在一起。
3. As a 设计探针作者, I want 固定 k 误放只走附录函数, so that 升级闸不会被固定 k 同集病绑架。
4. As a 对照守护者, I want B1′ 禁止看见 evidence id/绑定且延迟见正文, so that 事后核验是真对照而非近 T。
5. As a 对照守护者, I want B1′ 的拒绝不得记成 T, so that 臂身份不串。
6. As a 对照守护者, I want T 仍要求 attested 绑定（id∈已入库 T1）+ 同时刻核验不过 hard reject, so that attested 语义不丢。
7. As a 对照守护者, I want C 在同文下恒放行且不见 evidence, so that 无闸对照稳定。
8. As a 对照守护者, I want B2 核验不过不自动 hard reject, so that 松闸语义保留。
9. As a 夹具作者, I want 零 LLM 夹具能让 T−B2 与 T−B1′ 自然误放差方向为正, so that 「可分开」冒烟可自动化。
10. As a 夹具作者, I want 放行数为 0 时自然误放率无定义且禁止记 0, so that 「全拒装干净」被看见。
11. As a 防火墙守护者, I want 本规格实现不修改 `compare_primary` 源码语义, so that 冲甲主缝零 diff。
12. As a 防火墙守护者, I want 测试断言旁路写入不得改 `docs/evidence/patch-events/PREREG.md` 与主 `RESULT.md`, so that 禁回写可执行。
13. As a 防火墙守护者, I want 对外/文档不得把旁路读数称作结果甲, so that 层身份不混。
14. As a 产品叙事守护者, I want 「不能假绿」指标不出现在本轨主表与升级闸 Acceptance, so that 构念不污染（#428）。
15. As a 升级守门人, I want 升级三档条件预锁在 PROBE-LOCK 与本规格, so that 见结果后改闸作废。
16. As a 升级守门人, I want 「可分开」只允许另开新预注册文件候选而不自动激活、不填冲甲 RESULT, so that 升级≠甲。
17. As a 成本守护者, I want 默认测试与夹具探针不发模型、不读密钥, so that 云端默认安全。
18. As a 复现者, I want 授权后小 n 真数据只写入 `patch-events-alt/`, so that 与主 formal 文件隔离。
19. As an AFK agent, I want 本规格可拆成带 Acceptance/Paths 的工单, so that `/to-tickets` → enrich → before-implement → 新会话 `/implement`。
20. As a 面试讲解者, I want 能讲清旁路 vs 改主缝、同文 vs 分头、B1′ vs 现 B1、可分开 ≠ 甲, so that 平行轨纪律可答。

## Implementation Decisions

### 主缝与模块

- **新模块（建议）**：`src/freshlatch/eval/patch_events_alt.py`（或拆 `patch_events_alt_gates.py` + `patch_events_alt_metrics.py`，实现自洽）。  
- **禁止**：修改 `compare_primary` 的选取/成立定义；修改 `docs/evidence/patch-events/PREREG.md`；修改冲甲 `PREREG-B.md`（若存在）；把旁路结果写入主 `RESULT.md` 成立格。  
- **可只读复用**：`verify_edit`、旧 jsonl 行、既有 record 规范化（`normalize_experiment_record`）、构造金标字段。  
- **同文输入**：候选记录须含共享 `after_text`、`claim_id`、`construction_gold`（`正确`|`坏`）、T 用 `evidence_id`/`evidence_text`、已入库 T1 集合。B1′ 闸判阶段**不得**读到正确 `evidence_id`。  
- **臂名**：旁路记录臂字段用 `C` / `T` / `B1` / `B2`（B1 语义按 B1′ 信息集）；文档称 B1′。不得新增第五主臂名进冲甲主表。

### 闸判契约（同文模式）

| 臂 | 输入可见 | 放行规则 |
|---|---|---|
| C | 仅 `after_text` | 恒 `release`（同文下无核验） |
| T | `after_text` + `evidence_id` + `evidence_text` | id∉已入库 T1 → `reject`；`verify_edit` 不过 → `reject`；过 → `release` |
| B1′ | 同文锁定后：`after_text` + `evidence_text`；**无** `evidence_id` | `verify_edit`（或等价「正文一致」核验）不过 → `reject`；过 → `release`；该 `reject` 的 `arm` 必须是 B1，不得写成 T |
| B2 | `after_text`；可不绑定 | 有 `after_text` 即 `release`；核验结果只进 `reverify_ok`，不因此 hard reject |

分头四臂生成**不**在本规格主缝；附录另票。

### API 契约

```text
compare_alt_natural(rows|gate_outputs) -> {
  arms: {C|T|B1|B2: {自然放行数, 自然放行率, 自然误放率|None, ...}},
  contrasts: [
    {name: "T-B1", natural_false_accept_delta, ...},
    {name: "T-B2", natural_false_accept_delta, ...},
    # T-C 可报但不进升级闸硬条
  ]
}

compare_alt_fixed_k_appendix(...) -> { ... }  # 附录 only；升级闸禁止读取其成立字段
```

- 自然误放率分母 = 该臂自然放行数；为 0 → `None`/无定义，禁止写成 0.0 充「干净」。  
- 差方向：对照自然误放率 − T 自然误放率（与主链「对照 − T」同号约定；正值表示 T 更严/更干净）。若实现选「T − 对照」必须在函数文档与夹具断言写死并全仓一致——**本规格拍板沿用主链：对照 − T**。  
- 附录固定 k：不得成为 `upgrade_tier` 输入。

### 夹具与升级数字（跑前锁）

夹具最小集（零 LLM）：

1. 至少 1 条：坏修改 + 同文 → T `reject`、B2 `release` → 对 B2 自然误放差可正。  
2. 至少 1 条：坏修改 + 同文 → T `reject`、B1′ `release`（B1′ 无 id 却因正文核验策略放行的构造，或 T 绑错 id 而拒、B1′ 仅看正文放行——夹具作者选一种并写进测试名）→ 对 B1′ 差可正。  
3. 至少 1 条：正确修改 → T `release`，用于挡住「T 全拒装干净」：整夹具集上 T 自然放行数 ≥ 1。  

升级闸数字（与 PROBE-LOCK 一致，本规格抄死）：

- T 自然放行数 ≥ 1  
- T 自然放行率 ≥ max(1/n, 0.05)  
- 可分开硬条（夹具层）：夹具断言 T−B2 与 T−B1′ 自然误放差均 > 0，且上两条满足  
- 真数据小 n：仅明文授权后；只写 `patch-events-alt/`；仍冒烟，不报方差充总体  

### 防火墙验收（必须进测）

- `inspect.getsource(compare_primary)` 或等价：本 PR 的实现票 diff **不含**对 `compare_primary` 成立/选取逻辑的行为变更（允许文件未触碰为最简证明）。  
- 旁路写入路径不得打开 `docs/evidence/patch-events/PREREG.md` / 主 `RESULT.md` 作写。  
- 单测或文档夹具禁止出现把旁路差称作「甲成立」的断言字符串。

### 建议票序（供 `/to-tickets`）

| 序 | 建议 ID | Kind | Destination 摘要 |
|---|---|---|---|
| 1 | ALT-01 | feat | 同文四闸闸判 + `compare_alt_natural`；Paths：`patch_events_alt*.py`、单测 |
| 2 | ALT-02 | test | 夹具：T vs B2、T vs B1′ 自然误放差可非零；T 未全拒；误放无定义≠0 |
| 3 | ALT-03 | feat | `compare_alt_fixed_k_appendix` + 单测证明升级路径不消费它 |
| 4 | ALT-04 | test | 防火墙：主 `compare_primary`/旧 PREREG/主 RESULT 不被旁路写入；五处冻表面本轨不改 |
| 5 | ALT-05 | feat | （**Gate·须人授**）小 n 真数据旁路写入 `patch-events-alt/`；默认不发模型 |
| 6 | ALT-06 | docs/grilling | 升级/放弃决议：是否另开 `PREREG-ALT.md`；不实现代码 |

一票一会话。ALT-05 未授权不得开 `/implement`。ALT-06 不走业务代码 implement。

## Testing Decisions

- **好测试**：只断言旁路外部行为与防火墙；零 LLM；小夹具 n；不报方差。  
- **主测**：同文四闸决策表；`compare_alt_natural` 差方向；放行 0 → 误放无定义；附录不进升级输入；不写主 PREREG/RESULT。  
- **Prior art**：`tests/unit/test_pe_primary_rates.py`、`test_pe05_risk_coverage.py`、`patch_events_verify.py`、`patch_events_arms._decide`。  
- **层标签**（证据/报告文首强制）：

```text
层身份：设计探针 / 冒烟（平行轨）。不报方差；不作统计显著；
可分开 ≠ 甲；本轨数字不得填冲甲 RESULT。
```

## Out of Scope

- 复活路线 A（#419–#430）  
- 回写旧 `PREREG.md`；改冲甲预注册正文；改主 `compare_primary` 追甲  
- 本规格期间发模型（除非 ALT-05 获明文授权）  
- 称探针为甲；假绿仪器进本轨主表  
- 检索评测冒充本轨结论；改五处冻表面  
- `/writing-plans`；分头生成主缝；Pareto 主指标  
- 自动激活 `PREREG-ALT` 或取代冲甲页  

## Further Notes

- 本页不是论文，不是冲甲预注册，不是结果甲。  
- 与 #431 冲甲轨并行时：两边可各自 `/to-spec`，但**禁止**交叉改对方预注册与主/旁路成立定义。  
- 下一跳：`/to-tickets` → `/enrich-tickets` → `/before-implement <ID>` → **新会话** `/implement`。  
