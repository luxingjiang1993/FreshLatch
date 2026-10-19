# 诊断事实备忘:假绿 must_stale 全 unknown

> **工单**:[调研:假绿全unknown的构念与已有格子事实](https://github.com/luxingjiang1993/FreshLatch/issues/72)(地图 [#71](https://github.com/luxingjiang1993/FreshLatch/issues/71))
> **层级**:诊断事实拼装(demo / 仪器层)。**不是**对照成立;不得据此改通过线、改 `CONTROL_PROMPT`、改 `gold.json`,或重跑 LLM 凑绿。
> **方法**:主张跟到本仓一手来源(预登记、作废备忘、`control.py`、两份有效跑 JSON、作废跑 JSON)。本票未新开 LLM。

---

## 1. 预登记构念如何预测 `unknown` vs `alive`

### 1.1 构念(期望假绿 = `alive`)

假绿对照测的是:同模型、无工具、上下文里只有 T0 摘录时,被问「该主张**现在是否仍然成立**」,**已死主张应被判 `alive`(假绿)**;本产品必须红。对照成立才说明复验相对这条无工具基线真在起作用。

测的**不是** T0 阅读理解(「仅根据材料,主张是否成立」)。

- 来源:`docs/evidence/w4/false-green-control-prereg.md` §构念;`CONTEXT.md`「假绿对照」。

### 1.2 锁定 prompt(删禁外信息句后)

`src/freshlatch/eval/control.py` 的 `CONTROL_PROMPT`(与预登记锁定段逐字一致)现为:

- 角色 +「数周前签发」的主张 +「签发时所依据的文档摘录:`{t0_excerpt}`」
- 问句:**「请判断:该主张现在是否仍然成立?」**
- 输出契约:JSON `{"verdict": "alive"|"dead"|"unknown"}`
- **已删**:「只依据给定材料回答,不要引入材料之外的信息。」
- **保留**:「现在是否仍然成立」
- 禁止:加回禁外信息句;改成「仅根据以上给定材料,该主张是否成立」;出现 T1 / 快照 / 复验 / 金标 / must_stale / gold

- 来源:`docs/evidence/w4/false-green-control-prereg.md` §锁定 prompt;`src/freshlatch/eval/control.py` L25–33。

### 1.3 通过线 vs 作废线(与 `unknown` 的关系)

| 口径 | 规则 | 来源 |
|---|---|---|
| 通过线(对照成立) | `gold.json` `must_stale` = c1/c2/c3/c7 **四条均为 `alive`** | 预登记 §通过线;`control_pass` = `len(false_green_must_stale)==4`(`control.py` L90–103) |
| 未满 4/4 | **对照不成立**(可引用为「新仪器下对照未成立」),**不得**改通过线 | 预登记 §通过线 |
| 作废线 | 仅:矛盾句回潮 / 红线泄漏 / must_stale 任一条 `unparseable` / 事后改判据 | 预登记 §再次作废 |
| `unknown` / `dead` | **再多也不作废**,只算对照不成立 | 预登记 L48;评估 `docs/research/新假绿对照预登记设计评估.md` D3-(a) |

### 1.4 预登记对「删禁外信息后仍大量 unknown」的显式预测

评估与面试讲法已写死:**校准模型在「现在还成不成立、手里只有旧摘录」时可能大量 `unknown` → 对照不成立**(合法负结果),**不是**再作废一次;禁止为救出叙事改回蕴涵问法。

- 来源:`docs/research/新假绿对照预登记设计评估.md` §工程手段「构念保留「现在仍成立」」代价行;面试讲法 Q「如果新 prompt 跑出来大量 unknown?」。

**预测对照表(构念 → 格子)**:

| 桶 / 情形 | 构念期望 | 仪器层含义 |
|---|---|---|
| must_stale → `alive` | 假绿命中 | 对照朝通过线推进 |
| must_stale → `unknown` | 模型对「现在」弃权 | 对照不成立;不作废 |
| must_stale → `dead` | 基线已判死(亦非假绿) | 对照不成立;不作废 |
| must_stale → `unparseable` | 契约破坏 | **作废** |
| must_fresh 只读 T0 | 倾向 `alive`(只记录) | 不进通过线 |
| must_unknown → `alive` | 盲判绿信号(只记录) | 不进通过线 |

---

## 2. 三次跑的桶差异(两有效 + 一作废)

### 2.1 跑次身份

| 标签 | 路径 | `recorded_at` | 仪器身份 | 可引用性 |
|---|---|---|---|---|
| 作废跑 | `reports/report-20260921-222242.json`;摘录 `docs/evidence/w4/false-green-control.md` | `2026-09-21T14:22:42Z` | **矛盾 prompt**(「现在」+「不要引入材料之外」) | **整次作废**;格子不得当对照读数。备忘:`docs/evidence/w4/false-green-control-20260921-void.md` |
| 有效跑 A | `reports/w5w8_acceptance/report-20260922.json` | `2026-09-21T19:30:10Z` | 预登记仪器(删禁外信息句后) | 对照**不成立**、不作废;#56 原料(现非 canonical) |
| 有效跑 B | `reports/w5w8_acceptance/report-20260922-160056.json` | `2026-09-22T08:00:56Z` | 同上 | 对照**不成立**、不作废;#70 追跑 **canonical**(`ACCEPTANCE_SUMMARY.md` L113) |

decoding 三跑均为:`qwen-flash` / `temperature=0.0` / `seed=null` / n=1(见各 JSON `decoding` 块;与预登记 §decoding 一致)。

`CONTROL_PROMPT` 删禁外信息句的代码落点:`git` commit `0ea5b4a`(改 `src/freshlatch/eval/control.py`);作废跑使用改前矛盾模板(作废备忘 §仪器自相矛盾)。

### 2.2 must_stale(通过线四条)

| claim | 作废跑 | 有效 A | 有效 B |
|---|---|---|---|
| c1 | unknown | unknown | unknown |
| c2 | **alive** | unknown | unknown |
| c3 | unknown | unknown | unknown |
| c7 | unknown | unknown | unknown |
| 假绿条数 | 1/4(`false_green_must_stale=["c2"]`) | **0/4**(`[]`) | **0/4**(`[]`) |
| `control_pass` | false | false | false |

来源:作废 JSON L17–42 + L74–76;有效 A L17–44 + L74–80;有效 B L17–44 + L74–79。

**要点**:两次有效跑 must_stale **稳定全 `unknown`**。删禁外信息句后,**并未**救出 4/4;相对作废跑,唯一假绿 c2 在有效跑中变为 `unknown`(不得用该对比校准通过线——作废备忘已禁)。

### 2.3 其它桶(只记录,不进通过线)

| 桶 / 项 | 作废跑 | 有效 A | 有效 B |
|---|---|---|---|
| must_fresh alive | 无(c4–c8 皆 unknown) | c4, c6 | c6 |
| must_unknown 盲判绿 | c9 | c9, c12 | c12 |
| 干扰项 c13/c14 | 皆 unknown | 皆 unknown | 皆 unknown |
| `unparseable` | 无 | 无 | 无 |
| `dead` | 无(14 条均为 alive\|unknown) | 无 | 无 |

来源:三份 `results` + `blind_green_must_unknown` + `distractor_baseline`。

**要点**:有效跑**不是**「模型只会输出 unknown」——同次跑内 must_fresh / must_unknown 仍有 `alive`。must_stale 四条与干扰项则持续弃权。

### 2.4 作废 vs 不成立(纪律边界)

- 作废跑不可引用格子的理由是 **prompt 自相矛盾**,不是「unknown 众数」本身(作废备忘 L19–36;预登记 L48「不得用 2026-09-21 的 12/14 unknown … 设定」作废线)。
- 有效跑全 unknown = 预登记已预见的**对照不成立**,ACCEPTANCE 唯一可引用句已锁(`reports/w5w8_acceptance/ACCEPTANCE_SUMMARY.md` L42–43 / L117–119)。

---

## 3. T0 摘录在跑对照时的形态

### 3.1 代码路径(对照时如何拼装)

`run_control`(`src/freshlatch/eval/control.py` L73–79):

1. 对每条主张的每个 `t0_evidence_ids`:`doc_id, _, anchor = eid.partition("#")`
2. `store.get_chunk(doc_id, anchor, as_of="T0")`;命中则取 `chunk.text`
3. `t0_excerpt = "\n\n".join(excerpt_parts)` —— **未命中则该段不进摘录**(静默跳过;若全部未命中 → 空串仍送模型)
4. 报告 JSON **只落** `verdict` + `raw`(模型返回前 500 字),**不落**送入的 `t0_excerpt` 正文或长度

### 3.2 已有报告能证明什么 / 不能证明什么

| 事实 | 状态 | 来源 |
|---|---|---|
| 有效跑 A/B 的模型输出均为可解析的 `alive`\|`unknown` | 已证实 | 两份 `report-20260922*.json` 的 `raw` |
| 跑对照时**实际送入**的 `t0_excerpt` 字符串 | **报告未存档** → 登记为缺口 | `control.py` 返回结构 L92–109 无 excerpt 字段 |
| 当前库按同一拼装逻辑能否拼出非空摘录 | 可离线复现(见下;非跑时快照) | 本票只读 `data/freshlatch.db` + `data/t0_docket.json`,**未**调 LLM |

### 3.3 离线复现(当前库 = 对照同一 `get_chunk` 路径)

对金标 12 + 干扰项 2,按 `control.py` 逻辑查询 `SQLiteStore('data/freshlatch.db')`:

| claim | 桶 | `t0_evidence_ids` | chunk 命中 | `len(t0_excerpt)` |
|---|---|---|---|---|
| c1 | must_stale | `t0-competitor-notes#p2` | 1/1 | 116 |
| c2 | must_stale | `t0-regulatory-memo#p2` | 1/1 | 109 |
| c3 | must_stale | `t0-channel-interviews#p2` | 1/1 | 116 |
| c7 | must_stale | `t0-trade-press#p2` | 1/1 | 100 |
| c4–c6,c8 | must_fresh | 各 1 条 `#p2` | 1/1 | 102–113 |
| c9–c12 | must_unknown | 各 1 条 `#p2` | 1/1 | 83–105 |
| c13/c14 | distractor | 各 1 条 `#p2` | 1/1 | 97–103 |

docket 主张与 id:`data/t0_docket.json`。W4 检查表另记「12 条 `t0_evidence_ids` … 检索库全命中(12/12)」(零 LLM):`docs/evidence/w4/checklist.md` L52。

**形态结论(在「当前库 ≈ 跑时库」假设下)**:

- **不是空摘录**:must_stale 四条均命中,摘录约 **100–116 字**(单段 `## p2` 块级文本)。
- **偏短、单锚点**:每条仅 1 个 evidence id、一个 clause;相对「整篇 T0 文档」是短摘录。
- **缺口**:有效跑 JSON **未**记录当时 excerpt,故不能在字节级证明「跑对照那一刻」与上表完全一致;若需字节级,须另开探针/改落档(本票不做)。

红线单测用语料前 2000 字做 format 后扫泄题(`tests/unit/test_control.py` `_t0_excerpt`),与 `run_control` 的 **chunk 级**摘录不是同一条路径——不得把单测的全文截断长度误当成对照送入长度。

---

## 4. 已排除的原因 vs 仍开放的假说

### 4.1 已排除(仓库内证据足够否决)

| # | 假说 | 否决依据 |
|---|---|---|
| E1 | 有效跑仍是「矛盾 prompt」作废态 | 现 `CONTROL_PROMPT` 无「只依据给定材料 / 不要引入材料之外」(`control.py` L27–33);与预登记锁定段一致;ACCEPTANCE 写明「无矛盾句回潮」 |
| E2 | must_stale 机械解析失败(`unparseable`)触发作废/脏读 | 两有效跑 `raw` 均为 `{"verdict": "unknown"}`;无 `unparseable`;`control_pass=false` 来自 0 条 alive 而非解析失败 |
| E3 | 模型在该 decoding 下**只会**输出 `unknown` | 有效 A:c4/c6/c9/c12=`alive`;有效 B:c6/c12=`alive` |
| E4 | 通过线被误算成「全 unknown 也过」或报告写错桶 | `false_green_must_stale=[]`,`must_stale_total=4`,`control_pass=false`;ACCEPTANCE 登记 0/4 |
| E5 | 「unknown 众数 ⇒ 又一次作废」 | 预登记作废线不含 unknown 众数;评估 D3-(b) 已否;ACCEPTANCE「不作废」 |
| E6 | T0 摘录在当前拼装路径下为空(因而模型无材料可依) | 离线同路径 14/14 命中、must_stale 摘录 ≥100 字(§3.3);**但**跑时原文未落档,故 E6 排除的是「当前代码+库必然送空」,不是「跑时字节已归档为空」 |

### 4.2 仍开放(本票事实拼装无法裁定)

| # | 假说 | 为何仍开放 | 若要裁定需要什么(仅登记,本票不执行) |
|---|---|---|---|
| O1 | **构念层弃权**:问「现在是否仍然成立」+ 仅旧摘录时,qwen-flash(temp=0)对 must_stale **系统性选 `unknown`**(预登记已预见的负结果形态) | 两次有效跑 must_stale 全 unknown 稳定;同跑其它桶仍有 alive | 地图 #71 / #73 裁是否开不可引用探针;本备忘不建议改通过线 |
| O2 | **时间框诱导谨慎**:「数周前签发」+「现在」鼓励模型拒绝把 T0 外推到「现在」 | 与 O1 同构、难拆;作废跑在矛盾句下也曾大量 unknown | 消融问句属新仪器 C,须另票+新预登记 |
| O3 | **摘录过短 / 单锚点**削弱「材料看起来仍成立」的假信心 | 摘录 ~100 字且非空;但 must_fresh 同量级摘录上仍有 alive → 长度单独不足以解释 must_stale 全 unknown | 若开探针:记录 excerpt 长度/正文;仍不得改通过线凑绿 |
| O4 | **端点漂移 / 单次冒烟噪声** | temp=0、n=1;A/B 在 c4/c9 上不一致,但 must_stale 两跑一致 | 预登记禁止把本仪器改成 K3 式多样本;多样本属另案 |
| O5 | 模型用参数知识知道 must_stale 已死故不假绿 | 若「知道已死」更预期 `dead`;实测为 `unknown` 而非 `dead` → 更贴弃权而非判死 | 需另设计探针区分「弃权」与「隐式判死」;本票无该格子 |

### 4.3 硬禁重申(本备忘边界)

- **不得**建议放宽 4/4 / 改 `gold.json` / 改 `CONTROL_PROMPT` / 改预登记通过线。
- **不得**把「全 unknown」写成对照成立,或写成「仪器已证明产品无假绿」。
- **不得**用 2026-09-21 作废跑的 1/4 校准任何数字。
- 诊断事实 ≠ 执行新仪器 C;是否建议开 C 由 [#73](https://github.com/luxingjiang1993/FreshLatch/issues/73) 裁。

---

## 5. 一句话收口(给父代理 / #73)

在同一预登记仪器下,两次有效跑 must_stale 假绿均为 **0/4 全 `unknown`**(对照不成立、不作废);已排除矛盾 prompt 残留、`unparseable`、模型全局只输出 unknown、以及(当前库路径下)空 T0 摘录。最贴合已有事实的开放主假说是:**「现在是否仍然成立」+ 仅 T0 短摘录 → 模型对已死主张系统性弃权**(预登记已预测的负结果),而非仪器再次作废。
