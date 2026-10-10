# patch_events 路线 Y · 预注册协议页（只冲乙 · 仅锁 T−C）

**状态：协议可锁 · 冲乙正式主跑未激活**

锁死日期：2026-10-09。评估见 `docs/research/patch_events-路线Y只冲乙仅锁T-C设计评估.md`。ADR-0037。决议：本会话 grilling 四题均「按推荐」（Ronin 代理人；真人 Oriental Ronin）。

**冲乙整合升格（#518 / ADR-0039）**：本页为地图 #517 冲乙正式预注册载体（**修订升格**，不另开字母页）。正式 n=400 与 T−C 成立线（点>0.05∧下界>0）维持 ADR-0037。相对旧 `PREREG.md` / B / C 的主证据作废关系保持。仪器与门闩见下节 Amendment（#519 / #520 · ADR-0040 / ADR-0041）。仍未激活。

本页是路线 Y 的预注册载体。激活后：同一预注册只允许一次正式主跑；不得改判据与选取；结果只抄同一次 `compare_primary`（R）写入 `RESULT-Y.md`。

**机制基线**：继承路线 B 的选取 R、T/B1 同 after、**软对齐**（非路线 C 强制抄句）。操作定义以 ADR-0034 / ADR-0035 与 Draft `PREREG-B.md` 为准；本页只写 Y 增量与防火墙。**仪器层**另以 ADR-0040 替换逐字一致主核验与空分（见下）。

本页不改生产。不改 `PRODUCTION_RETRIEVAL_MODE`，不改主张复验金标文件，不调用付费 API（激活且人授之前），不提交密钥。主张收窄为 fail-closed attested edit（B 软对齐）。测量的是「改不改」的风险，不宣称发明了新的 risk-coverage 方法，不宣称优于 RARR·KPR。

结果写在同目录的 `RESULT-Y.md`，不回写本页，不回写 `RESULT-B` / `RESULT-C` / 旧 `RESULT.md`。

## 作废声明（主证据资格）

以下**不得**作为路线 Y / 冲乙的主证据（可作动机或负结果附录）：

- `docs/evidence/patch-events/PREREG.md`（含全部 Amendment）与现 n=30 `RESULT.md` 链  
- 路线 A 工单 #419–#430（整链废除，禁止复活）  
- 路线 B 主跑数字：不得抄进本页 `RESULT-Y` 成立格；只作负结果附录（见文末）  
- 路线 C 主跑数字与强制抄句机制：不得作为 Y 主路径；只作「非乙主路径」对照附录  
- ALT 夹具/探针、旧 `GATE-K-PROBE`、`GATE-C-FIXTURE`：不得升格为乙成立或本页已过门  

禁止回写旧 PREREG / PREREG-B / PREREG-C 凑乙或甲。禁止同页二次主跑 B、C 或 Y。

## 目标分层

1. **纪律目标（必须）**：可识别选取（R）；本页功率/止损；真数据门闩；一次正式主跑；结果只抄同一次 `compare_primary`。  
2. **求验目标（不保证）**：结果乙 = **仅 T−C** 成立（点估计 **>0.05** 且 95% bootstrap 下界 **>0**）。  
3. **诚实收口**：丙仍合法。**放弃甲**：即便 T−B1 与 T−B2 均点>0 且下界>0，本页**不得**称甲。禁止把「设计冲乙」写成「将得到乙」。禁止「接近甲 / soft-甲」。

结果乙 / 丙的投稿映射继承 `docs/evidence/patch-events/DECISION-LOG.md`（乙成立走结果乙场地；丙不得称主实验成功）。本页**不**以结果甲为求验目标，**不**放宽 DECISION-LOG 甲定义。

## 样本框

- 语料与主张：`data/corpus/pe_v2/` 与 `data/pe_v2_docket.json`（继承 #371）。  
- 不用 KPR benchmark，不用医疗指南，不做第二领域。  
- 构造金标两类：`正确` / `坏`；在任何系统输出和评委打分之前写死。  
- 主张按 `claim_id` 字典序取用；槽位做不出则作废换下一条，算子不改成更好做的。语料不够把缺额写进结果，不在本页把配额改小。  
- 名单以 `docs/evidence/patch-events/SPLIT-pe-v2.json` 为起点；路线 Y 正式 n=400 须在激活前确认或另写 `SPLIT-pe-v2-route-y.json`（实现票写死）。pilot 的 id 不进入正式 n。

## 配额

层内正确条数 = floor(层配额/2)，坏条数 = ceil(层配额/2)。余数规则与 B 相同。

| 用途 | 数值 | 日期 | 条款替换 | 删除 | 合计 |
|---|---:|---:|---:|---:|---:|
| pilot（流程，不进主表） | 4（2/2） | 4（2/2） | 4（2/2） | 3（1/2） | 15 |
| n=400（路线 Y 满样本门槛） | 100（50/50） | 100（50/50） | 100（50/50） | 100（50/50） | 400 |

路线 Y **不以** n=100 / n=250 为正式针。功效讨论中的 n≥250 只作动机，**不进** RESULT-Y 成立格。不得为凑乙无限加 n 而不改本页。

共形预留：四层在满样本之后再各留 5 条；不够写「未做」，主比较照常。

## 构造算子

与 `PREREG-B.md`「构造算子」节**逐条相同**（正确四类；坏槽编号 mod 4）。本页不重开算子决议。

## 实验组

四组吃同一批候选。生成只用 `DEFAULT_MODEL`=`qwen-flash`。温度或种子缺省则该次生成作废。

| 组 | 做法 |
|---|---|
| C | 无证据改写。不绑定，不核验，不 hard reject。生成成功即自然放行。 |
| T | attested patch，fail-closed。与 B1 **同 after 再分叉**。绑定已入库 T1 ∧ 核验 ok → release；不过 hard reject。**软对齐**（生成提示要求 after 与 evidence 去空白对齐）；**不是** C 的强制抄句硬契约。 |
| B1 | 同 after 后仅核验；不过 hard reject；不跑绑定闸。禁止核验失败仍放行凑差。 |
| B2 | KPR 式 claim→diff；核验不过不自动 hard reject。 |

检索：`PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"`，本实验不改。

消融只在 T 上，四项与 B 相同，不改主比较判决。

## 指标

与 B 相同：放行率、误放率、误拒率、错改率、可复验率、延迟、成本。主指标=固定放行率下的误放率。误拒率必须同时报。错改率等报但不默认参与成立（见下节谁参与成立）。

## 固定 k 选取（R · 已锁 · 继承）

- **k** := T 的自然放行条数。  
- **k < 10**：不得激活冲乙正式主跑。  
- 各臂自然放行集内：`m ≥ k` 则 `claim_id` 升序取前 k；`m < k` → 该臂固定 k 误放无定义。  
- 禁止空分全体候选 top-k；禁止 `coverage_c` 主路径；禁止金标/评委/用户裁决进 score。  
- 本期不启用 S / S+R。  

## 主比较与成立（Y 增量）

比较顺序写死：T 对 C → T 对 B1 → T 对 B2。配对差 = 对照误放率 − T 误放率。

统计：配对 bootstrap **10000**；流名 `bootstrap`；种子 `random.Random(20261007)`；指标顺序与 B 相同。重抽样固定 k 仍按 R。

结果表三条 false-accept 与 k **只抄**同一次 `compare_primary`（R）。成立格不得手填。禁止把门闩/探针/B/C 数字抄进成立格。

### 谁参与「成立」

- **参与成立**：仅 **T−C**。成立当且仅当：点估计 **>0.05**，且 95% 区间下界 **>0**，且该指标有定义。  
- **不参与成立**：T−B1、T−B2（仍须抄表，标注「报告-only」）。  
- 无定义不是成立。下界 ≤0 或点估计 ≤0.05 → 该条不成立（并触发止损见下）。  

### 甲防火墙（正文锁死）

本页求验目标为结果乙，**放弃甲**。即便 T−B1 与 T−B2 均点>0 且下界>0，分层仍只可能是 **乙或丙**，不得改判甲，不得回写 `DECISION-LOG` 甲定义。对外贡献句（乙成立时）只写相对无证据改写 C 的 fail-closed attested；禁止称优于 RARR·KPR；禁止「接近甲 / soft-甲 / 设计冲甲」。

## 功率 / 止损 / 主跑次数（正文锁死）

- **k 下限**：10。  
- **n**：400（上表）。  
- **止损**：正式主跑完成后，若 T−C 配对差点估计 **≤0.05**，或 95% bootstrap 下界 **≤0**（含无定义）→ 判 **结果丙** 收口；**禁止**加 n、改选取 R、改成立尺、同页二跑冒充原计划。  
- **同一预注册只允许一次正式主跑**。默认不设「看结果后再复核一次」。  

## 仪器最小集（#519 / ADR-0040 · 未激活写入）

废止本页主路径上「`score` 继续为空 / 逐字一致作唯一核验」的补定承载（旧 `PROMPT-AND-VERIFY-GAPS` 对 Y **不**再作主核验真相）。冲乙主核验与赋分如下。

### 主核验

- **型号**：本地 `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`。  
- **形**：`premise = evidence_text`（绑定 chunk），`hypothesis = after_text`。  
- **`ok`**：`argmax = entailment` 且 `P(entailment) ≥ τ`；`τ` 跑前小标定锁死。  
- Limitations：MT 训练降质；通用 NLI ≠ 法条支撑；仓外 Acc ≠ 本仓过线（见 #521 调研）。  
- **留位**：MiniCheck / AttrScore 等不为主核验。未激活可 Amendment 换卡；激活后换卡 = 本预注册作废。

### `score`

| 状态 | `score` |
|---|---|
| released（`decision=release`） | 有限非空；推荐 `P(entailment) ∈ [0,1]` |
| rejected（hard reject / `decision=reject`） | **`−∞`** |
| C | 无核验分；固定 k 仍 `coverage_c` |

禁止 `score=None` 混进可排序池；禁止金标/评委/用户裁决进 score。高分只用于固定 k **排序**，不单独定义放行。

### 臂拒识口径（乙只记账 · 不为乙强行差异化）

四臂共用同一 `verify_edit` 公式。乙成立只判 T−C；B1/B2 报告-only。

1. **T**：绑定失败 → reject；`ok=False` → **hard reject**。  
2. **B1**：事后核验；`ok=False` → **hard reject**；不要求策略 ≠ T。  
3. **B2**：核验不过 **不**因此 hard reject；`reverify_ok` 记账。  

## 仓外试分离门闩（未过 · 激活前）

门闩报告不进主表，可扔。路径：`docs/evidence/patch-events/GATE-Y-PROBE.md`（旁路生成 `gate-y-probe-generations.jsonl`）。规则针与本页 R 一致；机制针 = R · 同 after · 软对齐 · **ADR-0040 仪器**。

过门（同时满足）后才允许写激活批注：

1. T 的自然放行 **k ≥ 10**；  
2. **T−C** 固定 k 误放差方向为正（点估计 > 0）。  

（过门用点>0 作**方向门**；正式乙成立尺仍为点>0.05∧下界>0——门闩 ≠ 成立。）

T−B1 / T−B2 差**必报**，**不**作过门条件。

**禁止**把 `#479` `GATE-K-PROBE`、`GATE-C-FIXTURE`、RESULT-B/C、敏感性报告、n=30 冒烟报告升格为本页已过门。夹具层绿 ≠ 真数据过门。

### 核验敏感性闸（#520 / ADR-0041 · 硬前置）

报告：`docs/evidence/patch-events/GATE-Y-SENSITIVITY.md`（可扔）。集合 S = 构造坏槽（四层×mod4）+ 有限废止/版本陷阱 + 正确对照；名单跑前写死。

通过须同时：无 `score=None`；reject=`−∞`；坏→`ok=False` ≥0.90；正确→`ok=True` ≥0.70；型号与 τ 同 ADR-0040。未通过 → 不得真数据探针、不得激活、不得正式跑。未激活失败可收紧 τ **一次**并整闸重测；禁止放宽 τ 凑绿。

### n=30 冒烟（可扔 · 不作过门）

报告：`docs/evidence/patch-events/SMOKE-Y-N30.md`。必看：T 自然 k；T−C 固定 k 差点估计方向；T/B1/B2 fixed-k `claim_id` 集是否完全相同（`collapse=true` → 停）；score 卫生；B1/B2 差必报。

> n=30 冒烟只描述本 30 条上的仪器与方向可读性；区间只描述这 30 条重抽样噪声，**不**写成总体结论，**不**进 RESULT-Y 成立格，**不**单独构成 `gate_passed`，**不**保证乙。

### 复测协议（激活前）

1. 仪器+名单缝齐 → **敏感性闸通过** → 可选夹具冒烟 → **n=30 冒烟**（`collapse` 则停）→ 人授真数据探针 → 写 `GATE-Y-PROBE`。  
2. 敏感性 / 冒烟 / 小探针均**不进** RESULT-Y 成立格。  
3. 禁止：未过敏感性或未过门激活；未过门正式四臂进主表；看复测失败后改成立尺或 R。  

### 人令顺序（跑前锁死 · ADR-0041）

① 机制缝齐（R · 同 after · 软对齐 · ADR-0040）→ ② **敏感性闸通过** → ③ 可选夹具冒烟 → ④ n=30 冒烟 → ⑤ 人明文「授权路线 Y 仓外探针发模型；不得激活。」→ ⑥ 人审 `GATE-Y-PROBE` → ⑦ 人写本页激活批注 → ⑧ 人明文「批准激活 PREREG-Y 并正式主跑一次。」→ ⑨ 一次 formal-y（n=400）。Agent 不得自行激活/正式主跑/填成立格。

## 反 HARKing

见 B/C 丙后：同页二跑、降 CI、拿掉对照、改成立尺、并 ALT 主表、以 C 抄句改挂 Y 主路径 = 禁止。激活后改本页判据或选取 = 本预注册作废。

## 评委（有效登记）

与 `PREREG-B.md`「评委（有效登记）」表相同（Qwen3-235B / deepseek-flash / kimi-k2.6@0.6）。评分细则、κ、冲突清单、非拒绝类缺失纪律均继承，不放宽。

用户抽检：合计 **20** 条（每层 5：正确 2 / 坏 3；不随 n=400 放大）。`spotcheck` 种子 `20261007`。对外句子：「模型评委加单人抽检」。

## pilot

15 条只查流程，不进主表。若重做 pilot，笔记另写 `PILOT-NOTE-Y.md`，最多一次；不得改本页已锁条款。

## 日志与产物路径

- 正式入口（实现票）：`python -m freshlatch.eval.patch_events_formal_y`（**默认不发**；须激活 + `--authorize-send`）  
- 正式生成：`docs/evidence/patch-events/formal-generations-y.jsonl`  
- **禁止**写入 `formal-generations-b.jsonl`、`formal-generations-c.jsonl`、旧 `formal-generations.jsonl`  
- 评委日志：`data/exp/patch-events-y/judge-logs/`  
- 结果：`docs/evidence/patch-events/RESULT-Y.md`  
- 敏感性（可扔）：`docs/evidence/patch-events/GATE-Y-SENSITIVITY.md`  
- 冒烟（可扔）：`docs/evidence/patch-events/SMOKE-Y-N30.md`  

## 复现

确定性：配额、算子、R、bootstrap / bootstrap_ablation / spotcheck 种子与消费顺序、评分细则、有效 model 与温度、本页成立参与规则（仅 T−C 且点>0.05）、NLI 型号 id、τ、score 公式（released 有限 / rejected=`−∞`）。构造不用随机。

随机层：评委 API 可能漂移；回声不符则作废，不放宽容差。NLI 本地推理应逐位可复现（同型号同输入）。

违例级背离：激活后改本页；未过敏感性或未过门正式生成；回写 B/C；`score=None` 混池 / 空分 top-k 主路径；金标进 score；放行数为 0 时把误放率记成 0；夹具/冒烟/敏感性填乙/甲；称甲；保证乙；放宽 τ/ρ 凑绿。

## Related Work 边界

继承 B：对照的是「改」的风险。Y 额外声明：求验为相对无证据改写的 fail-closed；不装全面优于 RARR·KPR；不以 copy-constrained 为主主张。

## B / C 负结果附录（对外固定引用句）

> 路线 B（`PREREG-B` / `RESULT-B`，#480）在选取 R、同 after、软对齐并过仓外门闩后，正式主跑一次：k=42；T−C 点估计≈0.1190476，95% CI 下界≈−0.05556 → **结果丙**。核心教训是**效应偏小 / 功效不足**。B 全套冻结；禁止同页二次主跑。

> 路线 C（`PREREG-C` / `RESULT-C`）强制抄句正式主跑：k=93；T−C 点估计≈0.032258，下界=0 → **结果丙**。抄句压差，**不得**作为路线 Y 主路径；仅作非主路径对照与层身份教材。

## 激活批注

（未激活。敏感性通过 ∧ 过门 ∧ 人授后填写：日期、仓库针、`GATE-Y-SENSITIVITY.md` / `GATE-Y-PROBE.md` 路径、`gate_passed`、批准原文、约束重申。）

## 修订记录

| 日期 | 工单/会话 | 修订摘要 | 改了什么 | **未**改什么 |
|---|---|---|---|---|
| 2026-10-09 | grill · ADR-0037 | 初锁：路线 Y · 只冲乙 · 仅锁 T−C · n=400 · 门闩未过 | 新预注册页 | R；同 after；比较器；B/C 归档；甲定义 |
| 2026-10-10 | #518 · ADR-0039 | 冲乙整合升格：确认载体=本页 | 升格声明；与整合方案摘要的优先级 | R；软对齐；只判 T−C；n=400；点>0.05；放弃甲；未激活 |
| 2026-10-10 | #519 · ADR-0040 | 仪器最小集 | NLI 主核验；非空 score；reject=−∞；B 臂拒识记账口径 | 成立尺；正式 n；过门方向 Cond；放弃甲 |
| 2026-10-10 | #520 · ADR-0041 | 门闩与冒烟功率 | 敏感性硬前置；n30 冒烟层；人令序；机制针含仪器 | 过门仍 k≥10∧T−C点>0；正式成立尺 0.05；未激活 |
