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
- 复现2 的 reason 自述「无法确认其是否仍不低于 70%,原主张前提已失效」,两处错误:① 把「未复测」当推翻,违反 Lead 人格显式规则(未复测=缺口,走 mark_gap+unknown);② 主张方向读反(主张为「不超过 70%」,reason 写「是否仍不低于 70%」)。
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
