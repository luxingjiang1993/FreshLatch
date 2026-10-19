# 调研备忘:主链 must_stale 触点与已有读数

> **工单**:[调研:主链must_stale触点与已有读数](https://github.com/luxingjiang1993/FreshLatch/issues/81)  
> **父图**:[地图:产品侧主链抗假绿](https://github.com/luxingjiang1993/FreshLatch/issues/80)  
> **层级**:只读事实清点(demo / 规格 / 验收摘引边界)。**不是**构念/通过线决议;不得据此改 `gold.json`、改 C、放宽已锁 K 线,或宣布「产品已愈假绿」/一期评测闭合。  
> **方法**:主张跟到本仓一手来源(源码行级符号、ADR、spec、ACCEPTANCE_SUMMARY、预登记)。本票未新开 LLM、未改产品逻辑。

---

## 0. 词表与本备忘边界

| 术语 | 本备忘用法 | 来源 |
|---|---|---|
| **must_stale** | 金标桶:`c1,c2,c3,c7`;期望主链终态 `stale` | `data/eval/gold.json`;`CONTEXT.md`「must_stale」 |
| **假绿(产品侧)** | must_stale 被主链判 `fresh`(违例级背离) | `src/freshlatch/eval/runner.py` `REPRO_NOTE`;spec `docs/spec/04-评测纪律.md` §4.7 |
| **假绿对照(仪器)** | 无工具基线:must_stale 判 `alive` = 假绿命中;对照成立 ≠ 产品已愈 | `CONTEXT.md`「假绿对照」;`docs/evidence/w4/false-green-control-c-prereg.md` |
| **主链** | Lead ReAct + 工具白名单 + 规则闸落档(`Runner._finalize`) | `src/freshlatch/roles/lead.py`;`src/freshlatch/runner.py` |

父图钉死:C 对照成立只说明无工具基线打出假绿;产品主张须**异构另条**主链证明——见 [#80](https://github.com/luxingjiang1993/FreshLatch/issues/80) Destination / Notes。

---

## 1. 触点清点(主链 × must_stale / 假绿放行)

### 1.1 评测入口与金标桶

| 触点 | 符号 / 路径 | 与 must_stale 关系 |
|---|---|---|
| 金标名单 | `data/eval/gold.json` → `"must_stale": ["c1","c2","c3","c7"]` | 主矩阵期望终态 `stale`(`EXPECTED_VERDICT`) |
| 金标 runner | `run_gold` · `src/freshlatch/eval/runner.py` L79–191 | 每主张每遍新 `Runner`;`must_stale` 走 J2 有效反证机判(`counterevidence_j2`);违例级背离声明在 `REPRO_NOTE`(L31–32) |
| CLI | `python -m freshlatch.eval run` · `src/freshlatch/eval/__main__.py` L44–72 | 调 `run_gold`;另有 `control` / `control-c`(仪器,非主链) |
| 混淆矩阵 | `src/freshlatch/eval/matrix.py` `BUCKETS` / `EXPECTED_VERDICT` | `must_stale` → 期望 `"stale"` |
| 规格 | `docs/spec/04-评测纪律.md` §4.1–4.2、§4.6–4.7;`docs/spec/02-数据schema与语料清单.md` 金标配比;`docs/spec/09-验收-W5-W8.md` K3/K6-* | 评测纪律与验收预登记字面 |

### 1.2 Lead 工具链(写入口)

| 触点 | 符号 / 路径 | 与假绿放行关系 |
|---|---|---|
| 白名单 | `LEAD_TOOLS_W3` · `src/freshlatch/tools.py` L128–131 | `retrieve` / `read_source` / `reverify_claim` / `mark_stale` / `mark_gap` / `finish_reverify` / `spawn_critic`;**无** `spawn_auditor`(自动触发,见下) |
| `reverify_claim(fresh)` | `LeadReverifier._t_reverify_claim` · `lead.py` L257–302 | fresh 唯一工具写入口;强制 Critic checkpoint + Auditor(ADR-0009);证据须锚 T1 白名单 |
| `mark_stale` | `_t_mark_stale` · `lead.py` L304–353 | stale 唯一工具写入口;元陈述提前打回 → 维度枚举硬校验 → **受理层维度预检** → Auditor(ADR-0010) |
| `finish_reverify` | `_t_finish` · `lead.py` L530–534 | 异议未清时机械拒绝(`FINISH_OBJECTION_REFUSAL`,L95–99) |
| 收口次序闸 | `_precheck_blocked` / `POST_PRECHECK_UNKNOWN_REFUSAL` · `lead.py` L101–107, L265–270 | block 后未成功受理 `fresh` 前拒 `unknown`(ADR-0012 §2;#58/#59) |
| 人格 / 教义 | `LEAD_PERSONA` · `lead.py` L24–55;`skills/reverify/SKILL.md`(Runner 注入) | 语义倾向层;实证上可被漂移击穿(见 §3 先例) |
| Critic | `_auto_critic_checkpoint` / `_spawn_critic` · `lead.py` L362–528;`CRITIC_TOOLS` · `tools.py` L135 | fresh 前反对派至少发言一次;Critic **不得放行** |

### 1.3 维度预检(受理层,先于 Auditor)

| 触点 | 符号 / 路径 | ADR / 规格 |
|---|---|---|
| 比对纯函数 | `dimension_crosscheck_mismatch` · `gates/rule_gate.py` L24–31 | ADR-0011 / ADR-0012:单一真相在闸模块,受理层不得复制逻辑 |
| 预检调用 | `_t_mark_stale` · `lead.py` L321–338 | 错配 → 整 call 拒绝、零 Auditor、置 `_objection` / `_precheck_blocked`;轨迹 `dimension_precheck_block` |
| 额度 | `DIMENSION_RECOVERY_QUOTA = 1` · `lead.py` L70 | 每会话每主张预检打回至多 1 次 |
| 锁档文案 | `MARK_STALE_DIMENSION_PRECHECK` / `MARK_STALE_OBJECTION_QUOTA_REFUSAL` · `lead.py` L75–91 | ADR-0012:登记维度值不进错误文案 |

### 1.4 双判一致与 Auditor 在场

| 触点 | 符号 / 路径 | ADR |
|---|---|---|
| fresh 自动 Auditor | `_auto_auditor_checkpoint(path="fresh")` · `lead.py` L280–282, L375–409 | ADR-0009 |
| stale 自动 Auditor | `_auto_auditor_checkpoint(path="stale")` · `lead.py` L339–342 | ADR-0010(修订 ADR-0009「stale 不强制」) |
| 仲裁真值表 | `arbitrate_fresh` / `arbitrate_stale_mark` · `rule_gate.py` L65–94 | ADR-0009 3×3;ADR-0010 mark_stale 表 |
| 落档消费 | `Runner._finalize` · `runner.py` L162–263 | fresh 唯一绿格 = 双判一致且 `rule_gate` 绿灯;Auditor **无路径改绿** |

### 1.5 规则闸不变量(与 must_stale / 假绿直接相关)

实现:`rule_gate` · `src/freshlatch/gates/rule_gate.py` L97–197;词表总览:`CONTEXT.md`「规则闸」。

| # | 不变量(摘要) | error_code / 行为 | ADR |
|---|---|---|---|
| 1 | stale/unknown 不得绿灯 | 非绿请求可落档但不发绿 | — |
| 2 | 无 T1 evidence 不得 fresh | `NO_T1_EVIDENCE` | — |
| 5 | stale 须可点回 T1 反证 | `NO_STALE_EVIDENCE` | — |
| 6 | stale 反证不得纯元陈述 | `META_ONLY_DISPROOF`;引擎 `gates/meta_gate.py` | ADR-0008(#17) |
| 7 | Auditor 维度异议打回 stale | `DIMENSION_MISMATCH` → unknown + 异议 | ADR-0010 |
| 8 | 登记维 ≠ 反证自标维机械打回 | `DIMENSION_CROSSCHECK_MISMATCH`(闸层兜底) | ADR-0011;Lead 主链上由 ADR-0012 预检先行 |
| 9 | fresh 需双判一致 | `AUDITOR_ABSENT` / `ARBITRATION_MISMATCH` | ADR-0009 |
| — | Auditor 缺席不构成任何 stale 落档 | `AUDITOR_ABSENT`(stale 分支) | ADR-0010 |

**假绿放行(产品侧)的机械含义**:must_stale 主张最终 `claim.status == "fresh"` 当且仅当 Lead 记 `fresh`、Auditor `fresh`、且 `rule_gate` 对 fresh 请求返回 `green=True`(`runner.py` L198–205)。闸**不能**单独把 stale 改绿;假绿需要 Lead+Auditor 同错绿。

### 1.6 finish / soft_close / `_finalize` 路径

| 步骤 | 行为 | 来源 |
|---|---|---|
| 异议置位期间 | `finish_reverify` 拒 | `lead.py` L530–532;ADR-0012 §2 |
| 步数耗尽 | soft_close 注入收尾;未显式收口 → 默认 unknown | `lead.py` run_loop;`runner._finalize` else 分支 L247–260 |
| 预检后未收口 | `_finalize` 挂 `mechanical_precheck` 异议黄卡 | `runner.py` L247–260;ADR-0012 §4 |
| 闸打回 | `claim.status = "unknown"` + `[闸打回:…]` | `runner.py` `_gate_back` L193–196 |

### 1.7 工具约束(与复现 / 假绿相关的硬边界)

| 约束 | 位置 | 说明 |
|---|---|---|
| evidence_id 白名单 | `check_evidence_ids` · `evidence.py`;Lead `_check_evidence_ids` | 须本会话 retrieve 返回过;fresh/stale 须锚 `@T1` |
| `dimension` / `focus` 封闭枚举 | `FOCUS_DIMENSIONS` · `tools.py` L9–16 | 非法值整 call 拒绝 |
| `web_search` 不在任何白名单 | `tools.py` L115–117 | 联网破坏 must_stale 可复现性(spec §4.6) |
| eval 跳过 HumanLatch | `runner.py` `EVAL_MODE_SWITCHES` | 人审不进评测路径 |

---

## 2. 已有读数与可引用边界

**canonical 摘引入口**:`reports/w5w8_acceptance/ACCEPTANCE_SUMMARY.md`「可引用索引」专节(决议 [#57](https://github.com/luxingjiang1993/FreshLatch/issues/57))。

### 2.1 主链 must_stale 相关已过读数(仅表明句 · 逐字边界)

| 项 | 层级 | 核心数字(原料) | **唯一允许摘引** | **不得升格为** |
|---|---|---|---|---|
| **K3** | 统计 | c2 stale 15/15;`must_stale` 判 fresh **0**;`k3/k3_aggregate.json` | ACCEPTANCE「已过项」句 1:`K3…仅表明 c2 stale ≥14/15 且 must_stale 判 fresh 合计为 0,不是一期评测闭合,也不是 must_fresh 已愈,也不改写判定层冒烟未愈。` | 「产品侧抗假绿已证明」;一期闭合;must_fresh 已愈 |
| **K6-2** | 机制冒烟 | must_stale 各 3/3 stale;(开窗前 k6_4 报告) | 已过项句 3(倾向过;temp=0 不估噪声) | 判定层已愈;改写 K6-4 |
| **K6-4 §7.5 同线复验** | 行为冒烟 | c5/c6 fresh 6/6;**回归** must_stale c1/c2/c3/c7 **各 3/3 stale**;`k6_4_s75_reverify/k6_4_score.json` | 已过项句 5(模板亦在 score JSON `cite_template_if_pass`) | 一期闭合;「抗假绿产品证明」;改写闸层/K3 叙事 |
| 金标 N=1 冒烟 | 非判据 | must_stale 4/4;`gold_n1/` | 仅执行记录 | 任何通过线 |

父图 [#80](https://github.com/luxingjiang1993/FreshLatch/issues/80) Notes 显式:**既有 K3 / K6-4 must_stale 读数不得自动升格为本图抗假绿证明**。

### 2.2 仪器读数(非主链;边界对照)

| 项 | 读数 | 可引用句位置 | **不得写成** |
|---|---|---|---|
| 旧假绿仪器 | must_stale 假绿 **0/4**(全 unknown)→ 对照不成立(冻结只读) | ACCEPTANCE 未过项句 10;#70 | 「仪器已证明产品无假绿」;放宽 4/4 |
| **假绿仪器 C** | must_stale 假绿 **4/4 alive**→ **对照成立** | ACCEPTANCE 已过项句 8;#79 | 「产品已愈假绿」;判定层已愈;可改 gold/通过线;改写旧 0/4 句 |

### 2.3 总判硬禁(ACCEPTANCE「明确禁止」+ 总判句)

- 禁止:「W5–W8 全量验收通过」「一期(评测/测量)闭合」;单摘表头「过/倾向过/部分过」。
- 总判已写:假绿仪器 C 对照成立;**不符合**全量验收通过;**不得**写成一期评测闭合。
- 来源:`ACCEPTANCE_SUMMARY.md` L38–54、L85–86。

---

## 3. 可改面先例(不改 gold / C / 已锁 K 线)

父图允许后续在策略票后落修:**闸 / Lead·Critic 策略提示 / 工具约束**([#80](https://github.com/luxingjiang1993/FreshLatch/issues/80) Destination)。本备忘只登记**仓内先例与禁区形状**,不拍修什么。

### 3.1 闸(机械不变量 / 受理层)

| 先例 | 工单 | ADR | 评估文档 | 形态 |
|---|---|---|---|---|
| 元陈述句法闸 | [#17](https://github.com/luxingjiang1993/FreshLatch/issues/17) | ADR-0008 | `docs/research/c9元陈述句法闸设计评估.md` | 闸 + 工具层同函数提前反馈;**明确否掉「仅提示词」** |
| stale 路径双人 + 维度异议闸 | [#25](https://github.com/luxingjiang1993/FreshLatch/issues/25) | ADR-0010 | `docs/research/stale路径双人防线重开设计评估.md` | 在场 hook + 闸消费 flag;**否掉人格第三次加码** |
| 独立标注源机械跨检 | [#28](https://github.com/luxingjiang1993/FreshLatch/issues/28) | ADR-0011 | `docs/research/stale路径维度混淆独立标注源设计评估.md` | 闸不变量 8 |
| 受理层预检 + finish 闸 | [#27](https://github.com/luxingjiang1993/FreshLatch/issues/27) | ADR-0012 | `docs/research/Lead复验行为层设计评估.md` | 强制性住闸/工具边界 |
| block 后 unknown 前置闸 | [#58](https://github.com/luxingjiang1993/FreshLatch/issues/58) → 实装 [#59](https://github.com/luxingjiang1993/FreshLatch/issues/59) | ADR-0012 §2 增补 | `docs/research/K6-4§7.5窗内修复方向设计评估.md` | **不改 gold/通过线**;禁人格凑绿;禁松闸 |

纪律共性:事后撤闸 / 放宽不变量 = 拆已验防线实验意义(各 ADR「后果」条款);改锁档拒绝文案走评审。

### 3.2 Lead · Critic 策略提示(人格 / 教义 / 注入)

| 先例 | 工单 | 评估文档 | 结果形状 |
|---|---|---|---|
| c5 维度锚定人格 + SKILL 同步 | (c5 二修链;见 #19 背景) | `docs/research/c5二修方向设计评估.md` | 单测可绿、行为未愈的教训源 |
| 接线 SKILL + 最小人格 diff + `MARK_STALE_DIMENSION_NOTE` | [#19](https://github.com/luxingjiang1993/FreshLatch/issues/19) | `docs/research/c5c6工程债处置设计评估.md` | 拍板实装;行为验收 [#21](https://github.com/luxingjiang1993/FreshLatch/issues/21) **0/6 → 人格层修复判失效** |
| 人格第三次加码 | 候选于 #25 | `stale路径双人防线重开设计评估.md` D1-甲 | **弃**(同仪器第三次、零新机制) |
| §7.5 窗内「教义加厚」 | 候选于 #58 | `K6-4§7.5窗内修复方向设计评估.md` D1-(d) | **否**;主修机械闸 |

可引用工程教训句形状:「闸管不变量,人格管语义质量」;提示词层已被 c9(#17)与 c5/c6(#21)实证可击穿——见 ADR-0008 背景、ADR-0010 背景。

### 3.3 工具约束

| 先例 | 位置 / 工单 | 形态 |
|---|---|---|
| evidence_id 白名单(#16) | `evidence.py` / Lead `_check_evidence_ids` | 编造 id 整 call 拒绝 |
| `mark_stale.dimension` 必填枚举 | ADR-0011;#28 | 非法值拒绝并回列词表 |
| `focus` 硬校验 | `tools.py` + Lead/Critic | 同构枚举边界 |
| 元陈述工具层提前反馈 | ADR-0008;#17 | 与闸同函数,环内打回 |
| finish / unknown 机械拒绝常量 | ADR-0012;#27/#58/#59 | 工具返回 `error`,不住提示词自觉 |
| 角色白名单 fail-closed | `tools.py`;ADR-0001 | 未挂载 = 模型物理不可见 |

---

## 4. 与 C 的边界(只读)

### 4.1 C 对照成立句位置

- **唯一摘引入口**:`reports/w5w8_acceptance/ACCEPTANCE_SUMMARY.md` 可引用索引「已过项」第 8 条(假绿仪器 C)。
- 原料:`reports/w5w8_acceptance/report-20260922-171500.json`(及同名 `.md`);工单 [#79](https://github.com/luxingjiang1993/FreshLatch/issues/79)。
- 句意要点:must_stale 假绿 4/4 alive → 对照成立;**不是**产品已愈假绿(对照成立只说明无工具基线打出假绿);不改写旧仪器 0/4 句。

### 4.2 `CONTROL_PROMPT_C` / C 预登记只读约束(一句话)

`docs/evidence/w4/false-green-control-c-prereg.md` 与 `src/freshlatch/eval/control.py` 常量 `CONTROL_PROMPT_C` **冻结只读**:本图禁再抽 C、禁改该 prompt/预登记/多锚表或通过线;C 只读作「假绿可诱导」前提,产品侧抗假绿须异构另条主链证明([#80](https://github.com/luxingjiang1993/FreshLatch/issues/80) Out of scope;#77/#78)。

---

## 5. 给后续构念 grilling(#82)的指针(非决议)

1. 产品侧「抗假绿」若定义为 must_stale **不得**落 `fresh`,机械拦截面已在双判+规则闸;已有 K3/K6-4 读数是**同构守线/回归**,父图禁止直接升格为本图证明。  
2. 修窗若开,仓内成功先例偏 **闸/工具边界**;人格主修有预登记失效史(#21)。  
3. 证明跑入口现成:`run_gold` / `python -m freshlatch.eval run`;仪器入口 `control-c` **不得**再抽作本图证明。  
4. 预登记/通过线数字本票**不锁**(留给 #82/#84)。

---

## 6. 本票未做 / 留给父会话

- **未**编辑地图 [#80](https://github.com/luxingjiang1993/FreshLatch/issues/80) Decisions-so-far(请父会话补指针至本文)。  
- **未**手解 [#82](https://github.com/luxingjiang1993/FreshLatch/issues/82)/[#83](https://github.com/luxingjiang1993/FreshLatch/issues/83)/[#84](https://github.com/luxingjiang1993/FreshLatch/issues/84)。  
- **未**改 CONTEXT / ADR / 预登记 / 产品代码 / gold。
