# J4 复现抽查记录(闸层逐位复现;判定层按文档化容差)

> 「基准」列 = 编排器 P2/J1 运行(2026-09-20T12:43:19Z,reports/report-20260920.json);
> 「复现」列 = AFK 冷启动会话运行。**两次复现并存记录**:第一次逐位一致,
> 第二次单条翻转——这本身印证「qwen-flash 为活托管端点,跨会话复现只能近似」(§4.7)。

## 执行环境(各次运行登记)

| 项 | 基准(编排器) | 复现1(AFK) | 复现2(AFK) |
|---|---|---|---|
| 运行时间(UTC) | 2026-09-20T12:43:19Z | 2026-09-20T12:54:28Z | 2026-09-20T12:57:32Z |
| 模型版本 | qwen-flash | qwen-flash | qwen-flash |
| temperature / seed | 0.0 / None | 0.0 / None | 0.0 / None |
| 报告 | reports/report-20260920.json | reports/report-20260920-205428.json | reports/report-20260920-205732.json |

## 闸层(逐位复现:must_* 零违例)

| 项 | 基准 | 复现1 | 复现2 | 判定 |
|---|---|---|---|---|
| 判定字典 | c1 stale / c2 **fresh** / c3 stale / c4-c6 fresh / c7 stale / c8 fresh / c9-c12 unknown | 与基准逐位一致 | c9 **stale(翻转)**;其余 11 条与基准逐位一致 | 复现1 ✅ 逐位一致;复现2 ❌ 单条翻转记背离并人查 |

## 判定层(文档化容差:矩阵条数一致;单条判定翻转记背离并人查)

| 项 | 基准 | 复现1 | 复现2 | 判定 |
|---|---|---|---|---|
| 每桶命中条数 | must_stale 3 / must_fresh 4 / must_unknown 4 | 3 / 4 / 4 | 3 / 4 / **3** | 复现1 ✅;复现2 ❌ must_unknown 条数容差外 |
| 漏判条数 | must_stale 1(c2) / must_fresh 0 / must_unknown 0 | 同基准 | must_stale 1(c2) / must_unknown **1(c9)** | 复现1 ✅;复现2 ❌ |

## 人查处置(2026-09-20,开发者会话;AFK 会话按要求未自行排查)

### 背离一:c9 翻转(unknown→stale,仅复现2)

- 轨迹对照:T1 t0-messaging-survey#p2 原文为「本轮未复测 WhatsApp Business 渗透率,指标不再列入跟踪项」——这正是 must_unknown 桶的设计陷阱(未复测=缺口,非推翻)。
- 复现2 的 reason 自述「无法确认其是否仍不低于 70%,原主张前提已失效」,错误一处:把「未复测」当推翻,违反 Lead 人格显式规则(lead.py:25「未复测/无新数据=证据缺口,不是推翻,走 mark_gap+unknown,不得判 stale」;critic.py:29 同口径)。~~另有一处「主张方向读反」~~(2026-09-20 勘误:经 t0_docket.json 核对,c9 主张原文即「不低于 70%」,reason「是否仍不低于 70%」方向一致,原记录误记,撤销该子项;不影响「未复测≠推翻」的定性)。
- 定性:**判定逻辑边界案例 + 端点漂移的组合**。三次 temp=0 运行中 c9 两次 unknown、一次 stale,非确定性;非 must_stale→fresh 方向,不升级违例级。
- 处置:记背离,不改判据;must_unknown 桶命中按最差一次(3/4)如实登记。是否加工程加固(缺口句法闸)归 §7.5 修复窗口统一评估。

### 背离二(重):c2 稳定漏判(must_stale 判 fresh,基准+两次复现 3/3,确定性)

- 轨迹对照:三次运行均检索到金标致死段落 t0-regulatory-memo#p2@T1,并在 reason 中逐字引用印尼 PDP 法条款、自述「构成对『暂无强制要求』的直接反证」——然后判 fresh。推理方向错误,非检索失败。
- 定性:**违例级背离(must_stale 被判 fresh),且确定性复现(temp=0 跨进程一致)= 可修工程问题**。J2 三遍(temp=0.7)中 seed 22/33 的 c2 判 stale、seed 11 判 fresh,判定位于边界;但基准(temp=0)从未判对。
- 加重情节:基准运行全程无 critic_spawn 事件(Lead 自主决策不派驻),§8.5 登记册点名的架构级对冲(Critic 派驻)在该主张上未触发。
- 处置:**§7.5 工程失败类,触发一次性 2 周修复窗口**(到期同一份检查表、同一批判据复验一次,只换新证据,不得续杯;复验再不过 = 立项失败)。修复方向登记:Lead 人格「引用反证后不得判 fresh」显式加固、Critic 派驻触发策略、c2 轨迹入 tests/ 做回归原料。

### 附带发现:harness 实现缺陷(已修,非判据修订)

- J2 机器判据 `check_counterevidence` 缺「判定方向必须 stale」前置条件,导致:must_stale 判 fresh 却引用致死段落(c2)被误计「有效反证」;must_fresh 正确 fresh 判定必然命中支持锚,反向护栏恒假(基准 4/4「违例」实为假阳性)。
- 处置:修复对齐 CONTEXT.md「有效反证=Critic 产出的反证」定义;回归单测 test_counterevidence_fresh_direction_not_counterevidence;J2 数字离线重算(零 LLM):seed 11 = 3/4、seed 22/33 = 4/4,停止条件机器层仍 ✅,反向护栏修正后 ✅。重算留档 machine-results.md。

容差判定人:luxingjiang1993(开发者本人) 日期:2026-09-20
**签认:接受上述处置**——背离一(c9)记背离不升级、must_unknown 按 3/4 登记;背离二(c2)定谳违例级,§7.5 工程失败处置与 2 周修复窗口生效;harness 缺陷修复为工程修复、非判据修订。判据未动一字。

> qwen-flash 是活托管端点,跨会话复现只能近似,此限制为留档声明(§4.7)。

---

## 修复后冒烟(2026-09-20T22:33Z,§7.5 窗口内第一次活跑,n=1 冒烟框定,非窗口关闭验收)

> 修复内容(背离二修复方向①②③,TDD 落地):人格/rubric 三条方向铁律 + fresh 前 Critic 自动 checkpoint + c2 轨迹入 tests/(`tests/unit/test_c2_regression.py` 13 用例先行红灯,全量 122/122 绿)。报告:`reports/report-20260920-223309.json`。

| 项 | 修复前(基准) | 修复后冒烟 | 判定 |
|---|---|---|---|
| c2 | fresh(违例级) | **stale** ✅ | 修复生效;轨迹(run-223141)显示 Lead 直接走 mark_stale,**未进 fresh 路径**(checkpoint 未触发)——人格口径补洞在起作用 |
| must_stale 桶 | 3/4,漏 c2 | **4/4,零漏判** | ✅ 预定验收判据(零 must_stale→fresh)冒烟层通过 |
| c5 | fresh(基准+两次复现 3/3 稳定) | **stale** ❌ 新翻转 | 修复介导副作用,记背离(背离三) |
| c9 | unknown(基准)/stale(复现2) | unknown | 与基准一致 |
| 其余 8 条 | — | 与基准逐位一致 | ✅ |

### 背离三:c5 翻转(fresh→stale,修复介导,非端点抖动)

- **机制链完整(轨迹 run-223219 逐步可追)**:Lead 检索成本模型(T1 复测:我方 0.009 美元/会话,仍低于竞品折算)→ 落 fresh → **自动 checkpoint 触发** → Critic 检索到竞品 notes(Lite 版 39 美元/月/店)→ Critic 把**竞品门售价**当**我方单会话成本**的反证 mark_stale(维度混淆)→ Lead 未独立核对即采纳 Critic 框架改判 stale。
- **错误定性**:Critic 反证不满足实质门槛——主张度量维度是单会话成本,T1 成本模型原文明确「仍低于竞品现值」;39 美元/月/店是定价不是成本,属 rubric 已列的「无因果关系并列」式干扰(与「亏损新闻≠客单价」同类)。Lead 侧亦违规:checkpoint 观察已写明「是否采纳由你基于本会话证据自行判定」,模型未核对维度即镜像 Critic。
- **方向**:must_fresh→stale,**非违例级**(预登记违例定义=must_stale 被判 fresh);must_fresh 按最差一次 3/4 如实登记。
- **处置**:记背离,不改判据;**不立即二修**——一次只改一个变量,窗口关闭验收须对 c2 修复干净归因。二修候选方向登记:① Critic 反证门槛加「反证必须锚在主张同一度量维度」;② Lead 采纳 Critic 前强制独立核对该反证与主张的前提对应(不镜像 Critic 框架)。归 §7.5 窗口评审统一拍板。
- **与 c9 的区别**:c9 是端点漂移(证据逐位一致、判定自发抖动);c5 是修复引入的结构副作用(无 checkpoint 不触发),归因明确,不混入「近似复现」留档。

### 背离三补:二修拍板(2026-09-20,决议四件套落齐)

**拍板:做,①为主 + ②为配套,同一提交分层落地(d91a41e),走 c2 同款三层 TDD 结构(13 用例先行,全量 135 绿)。**
① Critic 人格/rubric 生产侧维度锚定(反证必须锚主张同一前提/度量维度,定价≠成本不得 mark_stale);
② Lead 人格/SKILL 消费侧独立核对 + checkpoint note 确定性注入核对指令。
评估文档:`docs/research/c5二修方向设计评估.md`(候选①②③机器闸④不做逐路线评估,被否项写透;
含 Anthropic 清单自评——初稿原推荐「只做②」被清单 #2/#5/#7 挑战后撤销)。
ADR 三条件不齐(易反转/非反直觉)不记;词表已同步(CONTEXT.md 有效反证 + Critic 条目);
tracker 无对应工单,决议评论以本文件 + 评估文档 + git 提交为留档载体。判据一字未动。

---

## 窗口关闭验收(n=3 temp=0 正式复验,2026-09-20,§7.5 窗口内,只此一次)

> 同一份检查表(checklist.md 判据锁定版)、同一批判据,只换新证据;判据事后修改 = 验收作废(HARKing)。
> 预登记通过线(验收运行前锁定,不得事后修订):① c2 3/3 stale;② 12 条中零 must_stale→fresh;
> ③ c9/c5 按已签口径记背离不升级。再不过 = 按签认口径立项失败(止损线)。

### 执行环境

| 项 | run 1 | run 2 | run 3 |
|---|---|---|---|
| 运行时间(UTC) | 2026-09-20T14:56:26Z | 2026-09-20T14:57:56Z | 2026-09-20T15:00:05Z |
| 模型版本 | qwen-flash | qwen-flash | qwen-flash |
| temperature / seed | 0.0 / None | 0.0 / None | 0.0 / None |
| 报告 | report-20260920-225754.json | report-20260920-230003.json | report-20260920-230156.json |
| 运行时代码状态 | d91a41e(c5 二修已落) | 同左 | 同左 |

命令:`PYTHONPATH=src python -m freshlatch.eval run --gold data/eval/gold.json --temperature 0.0`,连续 3 遍。

### 判定矩阵(12 条 × 3 跑)

| 主张 | 桶 | run 1 | run 2 | run 3 | 判定 |
|---|---|---|---|---|---|
| c1 | must_stale | stale | stale | stale | ✅ |
| **c2** | must_stale | **stale** | **stale** | **stale** | ✅ **3/3(通过线①达成)** |
| c3 | must_stale | stale | stale | stale | ✅ |
| c4 | must_fresh | fresh | fresh | fresh | ✅ |
| c5 | must_fresh | **stale** | **stale** | **stale** | ❌ 背离三未愈,见下 |
| c6 | must_fresh | **stale** | **stale** | **stale** | ❌ 背离四(新),见下 |
| c7 | must_stale | stale | stale | stale | ✅ |
| c8 | must_fresh | fresh | fresh | fresh | ✅ |
| c9 | must_unknown | unknown | **stale** | unknown | ❌ 已知形状,记背离不升级 |
| c10 | must_unknown | unknown | unknown | unknown | ✅ |
| c11 | must_unknown | unknown | unknown | unknown | ✅ |
| c12 | must_unknown | unknown | unknown | unknown | ✅ |

**通过线判定:① c2 3/3 stale ✅(三跑均 Lead 自主 mark_stale,因果句正确,checkpoint 未带偏);
② 12 条零 must_stale→fresh ✅(c1/c2/c3/c7 全部 3/3 stale);③ c9/c5 按已签口径记背离不升级 ✅(见下)。
预登记硬判据全部达成,违例级背离零。** c6 为预登记行之外的新背离,按已签违例定义(must_stale 被判 fresh)
**非违例级**,记背离待人查归因。n=3 诚实框定为冒烟层,不报方差;temp=0 于活托管端点仍是近似复现(§4.7)。

### 背离登记(验收窗口内)

**c5(must_fresh,stale 3/3,背离三未愈)**:二修后行为层未达预期,如实登记。归因更新——三跑中仅 run 3
为 checkpoint 介导(auto spawn,Critic 找回竞品 notes 反证,Lead 采纳);**run 1/run 2 Lead 未依赖 Critic
(auto spawn False,人工派驻的 Critic 空手而归),自行以竞品定价语汇(Lite 版 39 美元/月/店 vs 我方拟定
59 美元/月/店)推翻成本维度主张**。维度混淆从「Critic 产出」扩散到「Lead 自主推理」,二修的口径层约束
(Critic 生产侧 + Lead 采纳侧)未覆盖 Lead 独立判 stale 的路径。结构断言 13 用例全绿 ≠ 行为生效
(Anthropic 纪律 #1)。方向 must_fresh→stale,非违例级;must_fresh 桶按最差登记 2/4。

**c6(must_fresh,stale 3/3,背离四,新)**:此前 4/4 fresh(基准+复现1+复现2+修复后冒烟),本窗口 3/3 翻
stale,反转向翻转。轨迹归因:Lead 以竞品 Lite 定价 notes 推翻『收缩免费版⇒市场窗口打开』的**推论前提**
——与 c5 同类的定价语汇杀结构维度主张,但作用于 Lead 自主推理(2/3 跑人工 spawn Critic 空手后自行判
stale)。时间上与 d91a41e(c5 二修)相邻:不能排除提示词状态介导,也不能排除端点漂移(§4.7);3/3 确定性
+反转向更支持前者,但无对照实验可钉死(窗口只此一次,不得续杯,无法再跑)。按已签违例定义非违例级;
must_fresh 桶按最差登记 2/4;归 W12 前工程债,建议方向:Lead 自主 mark_stale 路径补同维度自查
(人格/rubric),或评测层加 must_fresh 方向护栏。

**c9(must_unknown,run 2 stale,已知形状)**:轨迹 reason『本轮未复测……该指标不再列入跟踪项,因此主张失效』
——再次把「未复测」当推翻,违反人格显式规则(lead.py/critic.py「未复测=证据缺口,走 unknown」),与复现2
同形。定性维持「判定逻辑边界案例 + 端点漂移组合」(背离一),不改判据、不升级;must_unknown 按最差 3/4。

### 验收结论(待容差判定人签认)

预登记通过线三条全部达成(c2 3/3 ✅、零 must_stale→fresh ✅、c9/c5 按签认口径记背离 ✅),违例级背离零。
按 checklist「未过处置」表与 §7.5 止损线口径,**本次窗口关闭验收达成**;c5/c6/c9 三条非违例级背离如上登记,
其中 c5(二修未愈)、c6(新翻转,归因待查)如实暴露——**结构修复 ≠ 行为生效,n=3 冒烟层证据不能报成统计结论**。

容差判定人:luxingjiang1993(开发者本人) 日期:2026-09-20
**签认:接受上述处置,验收达成,背离登记生效**——预登记通过线三条全部达成(c2 3/3 stale、
零 must_stale→fresh、c9/c5 按签认口径记背离),违例级背离零;c5(stale 3/3,二修行为层未愈)、
c6(stale 3/3,新翻转,归因待查)、c9(run 2 stale,已知边界形状)按已签违例定义均非违例级,
背离登记生效;c5/c6 归 W12 前工程债(登记方向:Lead 自主 mark_stale 路径补维度自查,
或评测层加 must_fresh 方向护栏)。判据锁定全程未动一字。
