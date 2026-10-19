# C 预登记锁与成败可引用句设计评估

> 工单:[决议:C预登记锁与成败可引用句](https://github.com/luxingjiang1993/FreshLatch/issues/77)(grilling)。地图:[地图:新假绿仪器C](https://github.com/luxingjiang1993/FreshLatch/issues/74)。
> 日期:2026-09-22。状态:已拍板。
> 原料:[决议:C构念与旋钮包](https://github.com/luxingjiang1993/FreshLatch/issues/76) / `docs/research/C构念与旋钮包设计评估.md`;[调研:对照并行落点与可用模型档](https://github.com/luxingjiang1993/FreshLatch/issues/75);旧预登记 `docs/evidence/w4/false-green-control-prereg.md`(只读);[决议:假绿追成立的跑前纪律与成败可引用句](https://github.com/luxingjiang1993/FreshLatch/issues/69);ACCEPTANCE 现 canonical 旧仪器句(#70)。
> 配套:ADR-0007(**不新开 ADR**);`CONTEXT.md` 不动(过程词不进词表)。
> 本工单**不跑** LLM、不改 `gold.json` 判定语义、不落盘预登记文件/代码(归 [#78](https://github.com/luxingjiang1993/FreshLatch/issues/78))。

## §问题 + 前置约束

**问题**:在构念与旋钮包已拍板后,锁死 C 的**预登记规格与引用纪律**(跑前):(1) 通过线 / 作废线 / decoding;(2) `CONTROL_PROMPT_C` 逐字 + 并行代码契约 + 私有多锚表 + excerpt 落档;(3) 成败「仅表明」句与旧 canonical 并存规则;(4) 作废后补一刀有效跑与 ACCEPTANCE 分结局改法。

**前置约束(已被钉死,本工单不得违反)**:

| 约束 | 出处 |
|---|---|
| 双主刀=C 私有多锚 + 反默认-unknown 旁句意图;时间框字面保留;冻 qwen-flash 与同构 decoding;共享 docket 只读;全送模主张同加料政策;期望 must_stale→alive | #76 |
| 通过线默认同构 c1/c2/c3/c7 全 alive;代码并行 `CONTROL_PROMPT_C`;旧路径只读;预算一刀有效跑 | 地图 #74 charting |
| 旧预登记 / 旧 `CONTROL_PROMPT` / #70 0/4 不成立句冻结只读;不得用旧 0/4 校准 C | #46/#70;地图继承 |
| 作废⊥不成立;不得第二份「同预登记」软化;禁蕴涵问法;禁多刀有效跑钓鱼 | #46/#56/#69;Out of scope |
| 本票不跑 LLM;不改 gold 判定语义;评测过程词不进 `CONTEXT.md` | 工单 Question;Notes |
| 层级:demo / 仪器冒烟;不报方差;不升格测量闭合 | 地图 Notes;ADR-0007 |

**Anthropic 评审命中记录**(推荐前主动过清单;全采推荐后复核合入):

1. **演示可过 ≠ 测量可信**:成败句钉「仪器冒烟 / 对照成立 ≠ 产品已愈假绿 / ≠ 一期闭合」;成功改缺口不得写成全量验收通过。
2. **单次运行判生死**:decoding 冻 temp=0 / n=1;禁把一刀写成方差/测量闭合;作废补跑不得变成抽绿为止。
3. **默认不是规格**:模型/temperature/seed/n/旁句/多锚表在本票逐字钉死,供 #78 拷贝。
4. **过程词不进 CONTEXT**:预登记、作废、仅表明、多锚叠加不进词表;「假绿对照」定义不变。
5. **止损预登记**:多锚表与 prompt **跑前**写死;见格子后改 +N/选句/旁句 = HARKing。合入修正:**已锁 id 缺 chunk → 整刀作废**(不得静默少拼成「事后单锚」)。
6. **复现两层**:确定性层=`CONTROL_PROMPT_C` 逐字 + 多锚表 + 旧路径可复现;随机层=alive 格子(托管端点近似复现),容差不报方差。
7. **ADR 三条件**:难反转纪律已在 ADR-0007 + 旧预登记只读 + 并行隔离 + #69 句纪律——**不新开 ADR**。

被否的原冲动(写进 §逐路线评估):「放宽通过线」「全 unknown 算作废」「C 失败替换旧 0/4 句」「成功抹掉旧不成立句」「作废无限补跑」「只给 must_stale 加锚」「旁句改蕴涵」。

## §候选路线(每个决策维度的全部候选,含被否项)

### D1 通过线

- **(a)** 同构旧预登记:c1/c2/c3/c7 全 `alive`;`control_pass` 同构;must_fresh / must_unknown / c13/c14 只记录不计 pass。(拍板)
- **(b)** 另定名单或阈值。

### D2 作废线

- **(a)** 继承旧四条(矛盾句回潮 / 红线泄漏 / must_stale 任一条 `unparseable` / 事后改预登记正文)+ C 特有:跑时偏离已锁多锚表、用错非 C prompt、改共享 docket、**已锁 id 缺 chunk**。(拍板)
- **(b)** 只继承旧四条。
- **(c)** 全 unknown / 未满 4/4 也作废。

### D3 反默认-unknown 旁句逐字

- **(a)** `若缺少签发之后的更新材料,不要因此默认 unknown。`(拍板)
- **(b)** 更长「不构成默认判 unknown 的理由;请就现在是否仍然成立作答」。
- **(c)** `材料仅为签发时依据;请勿因材料未覆盖签发之后的世界而输出 unknown。`
- **(d)** 更短 `缺更新材料 ≠ 默认 unknown。`
- **(e)** 蕴涵旁句「仅根据材料是否成立」——禁。

### D4 私有多锚表

- **(a)** 每条送模主张(含干扰项)同 doc `p1`+`p2`+`p3` 源序拼接(+2)。(拍板)
- **(b)** 只加 `p1`。
- **(c)** 只加 `p3`。
- **(d)** 只对 must_stale 加锚——禁。

### D5 作废后补一刀有效跑

- **(a)** 对齐 #69:作废不消耗名额;允许且仅允许再开一刀有效跑;再废关图。(拍板)
- **(b)** 作废即关图不补跑。
- **(c)** 无限补到出有效读数——禁。

### D6 成败句与旧 canonical 并存

- **(a)** 并存:C 成败另句;旧 #70「新假绿对照…0/4」句保留为旧仪器历史,不得被 C 读数改写/删除。(拍板)
- **(b)** C 失败替换旧 0/4 句。
- **(c)** C 成功删除旧不成立句。

### D7 ACCEPTANCE 分结局改法

- **(a)** 成功:已过项增 C 成功句;缺口去掉「须 4/4」;总判改为「旧仪器不成立已冻结;C 对照成立」仍禁一期闭合。失败:未过区增 C 失败句;旧句保留;缺口/总判仍写假绿未成立(可并列)。作废:不改成立/不成立句;另链 void 备忘。(拍板)
- **(b)** 成功也不改总判/缺口。
- **(c)** 成功后撤下旧不成立摘引入口。

### D8 ADR / 词表

- **(x)** 不新开 ADR;`CONTEXT.md` 不动。(拍板)
- **(y)** 新开 ADR。
- **(z)** 词表加过程词。

## §逐路线评估(对照表;被否理由写透)

| 维度 | 候选 | 判定 | 理由 |
|---|---|---|---|
| D1 | (a) 同构 4/4 | **拍板** | charting 默认;与旧仪器/W1-1 对齐;放宽=HARKing |
| D1 | (b) 另定 | **否** | 见格子前改口径;地图禁放宽 |
| D2 | (a) 旧四条+C 特有+缺 chunk 废 | **拍板** | 作废=不可解释;并行串台/静默少拼会把预登记变成事后单锚(清单 #5) |
| D2 | (b) 只旧四条 | 否 | 挡不住用错 prompt / 少拼 |
| D2 | (c) unknown 众数作废 | **否** | 用旧 0/4 拟合;负结果无法引用 |
| D3 | (a) 短旁句 | **拍板** | 意图直达;无蕴涵字面;判断句仍逐字时间框 |
| D3 | (b)/(c)/(d) | 否 | 更长无增量 / 「未覆盖世界」易滑向元推理 / 过短可截歧义 |
| D3 | (e) 蕴涵 | **否(Out of scope)** | 换实验 |
| D4 | (a) 全三 clause | **拍板** | 对称加满邻块;不挑「更像 alive」一侧;仓内每 doc 均有 p1/p2/p3 |
| D4 | (b)/(c) | 否 | 单侧加料=见格子前结构性偏置边缘 |
| D4 | (d) 仅 must_stale | **否(#76 / 清单 #5)** | 通过线对象优待 |
| D5 | (a) 对齐 #69 | **拍板** | 作废≠负结果;兑现恰好一刀有效 |
| D5 | (b) | 否 | Destination 可能从未兑现有效跑 |
| D5 | (c) | **否(清单 #2/#5)** | 钓鱼 |
| D6 | (a) 并存 | **拍板** | 地图钉旧句保留、C 另句;两台仪器 |
| D6 | (b)/(c) | 否 | 抹旧仪器历史 / 用 C 读数改写旧 canonical |
| D7 | (a) 分结局 | **拍板** | C 成功兑现对照成立登记;旧历史保留不阻塞缺口;作废⊥不成立 |
| D7 | (b) | 否 | 与 Destination「成功另条登记成立」冲突 |
| D7 | (c) | 否 | 易抹历史摘引 |
| D8 | (x) | **拍板** | 三条件不齐 |
| D8 | (y)/(z) | 否 | 重复仪式 / 过程词 |

## §拍板 + 逐项子决策

**拍板:D1-(a) + D2-(a) + D3-(a) + D4-(a) + D5-(a) + D6-(a) + D7-(a) + D8-(x)。**

### 1. 通过线 / decoding / 期望

- 通过线:must_stale = **c1、c2、c3、c7** 全部判 `alive`;未满 4/4 = 对照不成立(可引用),不得改线。
- `control_pass` 同构;`must_fresh` / `must_unknown` / `must_fresh_distractor`(c13/c14) 只记录不计 pass。
- decoding:`qwen-flash`;`temperature=0.0`;`seed=None`;每主张 `n=1`;JSON `alive|dead|unknown`。
- 期望构念(继承 #76):仍称假绿对照;失败 ≠ 产品无假绿。

### 2. 作废线

触任一条 → 整刀作废,落 `docs/evidence/w4/false-green-control-c-<date>-void.md`:

1. prompt 再次把「现在/仍然」与「不要使用签发之后 / 只根据材料」绑回同一用户消息(矛盾句回潮);
2. 红线泄漏(T1 / 快照 / 复验 / 金标 / must_stale / gold);
3. must_stale 任一条机判 `unparseable`;
4. 跑后改通过线 / 作废线 / decoding / prompt 正文 / 多锚表;
5. **C 特有**:跑时偏离下方已锁多锚表;使用旧 `CONTROL_PROMPT` 冒充 C;改共享 `t0_docket.json`;已锁 evidence id 在 store 中缺 chunk。

`unknown`/`dead` 再多,只是对照不成立,不作废。

### 3. `CONTROL_PROMPT_C` 逐字锁定件

`src/freshlatch/eval/control.py` 新增常量 `CONTROL_PROMPT_C`(或等价参数化默认仍为旧常量)。**旧 `CONTROL_PROMPT` 与旧预登记锁定段保持不动**。正文在 format 占位与 JSON 花括号转义后须与下列一致:

```
你是市场研判助手。以下是一条数周前签发的研判主张,以及签发时所依据的文档摘录:

主张: {statement}
签发时所依据的文档摘录: {t0_excerpt}

若缺少签发之后的更新材料,不要因此默认 unknown。
请判断:该主张现在是否仍然成立?
只输出 JSON,格式:{{"verdict": "alive"|"dead"|"unknown"}}。
```

禁出现:「仅根据材料是否成立」及同构蕴涵问法;禁删「现在是否仍然成立」;禁删「数周前签发」。

### 4. 并行代码契约(供 #78 实装;本票锁规格)

| 件 | 规格 |
|---|---|
| 常量 | 旁增 `CONTROL_PROMPT_C`;不改/不删 `CONTROL_PROMPT` |
| 运行入口 | CLI 变体(如 `control-c` 或等价旗标)走 C;默认/旧入口仍走旧仪器 |
| 拼装 | 按下方私有多锚表取 chunk,`\\n\\n` 拼接为 `{t0_excerpt}`;共享 docket 只读 |
| 对账 | 通过线/解析可与旧同构;报告须能区分仪器(如 `kind`/`instrument`/`prompt_id=C`) |
| 红线单测 | 旧测继续盯 `CONTROL_PROMPT`;C 另测盯 `CONTROL_PROMPT_C` |
| 验收脚本 | `run_w4_acceptance.py` 等不得默默改成 C |

### 5. C 私有多锚表(跑前写死)

政策:本跑**所有送模主张**(金标 12 + 干扰项 c13/c14)**同政策**;每条同 doc 的 `p1`+`p2`+`p3` 源序;共享 docket 的既有单锚 id **不修改**。

| claim_id | C 私有 `t0_evidence_ids`(序) |
|---|---|
| c1 | `t0-competitor-notes#p1`, `t0-competitor-notes#p2`, `t0-competitor-notes#p3` |
| c2 | `t0-regulatory-memo#p1`, `t0-regulatory-memo#p2`, `t0-regulatory-memo#p3` |
| c3 | `t0-channel-interviews#p1`, `t0-channel-interviews#p2`, `t0-channel-interviews#p3` |
| c4 | `t0-market-census#p1`, `t0-market-census#p2`, `t0-market-census#p3` |
| c5 | `t0-cost-model#p1`, `t0-cost-model#p2`, `t0-cost-model#p3` |
| c6 | `t0-competitor-news#p1`, `t0-competitor-news#p2`, `t0-competitor-news#p3` |
| c7 | `t0-trade-press#p1`, `t0-trade-press#p2`, `t0-trade-press#p3` |
| c8 | `t0-tech-ecosystem#p1`, `t0-tech-ecosystem#p2`, `t0-tech-ecosystem#p3` |
| c9 | `t0-messaging-survey#p1`, `t0-messaging-survey#p2`, `t0-messaging-survey#p3` |
| c10 | `t0-talent-salary#p1`, `t0-talent-salary#p2`, `t0-talent-salary#p3` |
| c11 | `t0-payment-landscape#p1`, `t0-payment-landscape#p2`, `t0-payment-landscape#p3` |
| c12 | `t0-infra-reliability#p1`, `t0-infra-reliability#p2`, `t0-infra-reliability#p3` |
| c13 | `t0-competitor-economics#p1`, `t0-competitor-economics#p2`, `t0-competitor-economics#p3` |
| c14 | `t0-channel-coverage#p1`, `t0-channel-coverage#p2`, `t0-channel-coverage#p3` |

### 6. excerpt 落档契约

有效跑(或作废备忘)报告**必须**含:

- `instrument`: `false_green_control_c`(或等价);
- `prompt_id`: `CONTROL_PROMPT_C`;
- 每条 claim:`t0_evidence_ids_sent`(上表逐字)、`t0_excerpt`(实际送模全文)、`t0_excerpt_char_len`;
- `decoding` 全字段;`recorded_at`;
- 任一条已锁 id 缺 chunk → **不得**静默跳过;整刀走作废线。

### 7. 成败「仅表明」句(与旧句并存)

**旧仪器 canonical(#70)保留不动**:

> 新假绿对照（qwen-flash，temp=0.0，seed=None，n=1，预登记仪器）仅表明 must_stale 假绿 0/4（c1 unknown / c2 unknown / c3 unknown / c7 unknown）→ 对照不成立且不作废；不是仪器已证明产品无假绿，也不是可放宽 4/4 alive，也不是一期评测闭合。

**C 成功句**(4/4 alive 且不作废):

> 假绿仪器 C（qwen-flash，temp=0.0，seed=None，n=1，C 预登记；私有多锚 p1+p2+p3 + 反默认-unknown 旁句）仅表明 must_stale 假绿 4/4（c1/c2/c3/c7 全 alive）→ 对照成立；不是一期评测闭合，不是判定层已愈，不是可改 `gold.json` / 通过线，也不是产品已愈假绿（对照成立只说明无工具基线打出假绿）；亦不改写旧预登记仪器对照不成立句。

**C 失败句模板**(未满 4/4 且不作废):

> 假绿仪器 C（qwen-flash，temp=0.0，seed=None，n=1，C 预登记；私有多锚 p1+p2+p3 + 反默认-unknown 旁句）仅表明 must_stale 假绿 {k}/4（{逐条:如 c1 unknown / c2 alive / …}）→ 对照不成立且不作废；不是仪器已证明产品无假绿，也不是可放宽 4/4 alive，也不是一期评测闭合；亦不改写旧预登记仪器对照不成立句。

### 8. 作废补跑与有效跑配额

- 作废不消耗有效跑名额;修到可跑后**允许且仅允许**再开一刀有效跑。
- 该有效跑再废 → 关图;canonical 回退开跑前态(旧 #70 句);另开努力。
- 有效读数(C 成功或 C 失败不成立)一旦产出 → 本图有效跑配额用尽,不得再抽。

### 9. ACCEPTANCE_SUMMARY 分结局改法

| 结局 | 可引用索引 | 总判 | 缺口 |
|---|---|---|---|
| C 成功 | 已过项**新增** C 成功句;旧 #70 句留在未过/历史区作旧仪器冻结读数 | 去掉「假绿仪器对照不成立仍登记」;改为点明「旧仪器不成立已冻结;C 对照成立」;仍禁一期闭合 / 全量验收 | 去掉「须 4/4 alive 才对照成立」;可注旧仪器冻结 |
| C 失败(有效) | 未过区**新增** C 失败句;旧 #70 句保留 | 仍写假绿未成立(可并列两仪器) | 保持「须 4/4,不得放宽」(相对 C 或总体未成立事实) |
| C 作废 | **不改**任一成立/不成立句;另链 void 备忘;注明是否进入补跑 | 不变 | 不变 |

### 10. 跑前硬门闩(任一项红则禁跑;#78/#79 执行)

1. `CONTROL_PROMPT_C` 与本评估 §3 逐字一致;旧 `CONTROL_PROMPT` 未改。
2. 多锚表与 §5 逐字一致;共享 docket 未改。
3. decoding = qwen-flash / temp=0.0 / seed=None / n=1。
4. 不改 `gold.json` 判定语义;不改本预登记通过线/作废线。
5. 本图尚未消耗有效跑配额(或处于作废后补一刀态)。
6. 本决议已关;成败/作废句与 ACCEPTANCE 改法已锁。

### 11. 预登记落盘路径(归 #78)

建议文件:`docs/evidence/w4/false-green-control-c-prereg.md`——正文从本评估拷贝通过线/作废线/decoding/prompt/多锚表/excerpt 契约;头部注明跑后改本文 = 本刀作废(ADR-0007)。

### 12. 本工单范围

- 只落评估与决议;不跑 LLM;不改代码/预登记文件/ACCEPTANCE;`CONTEXT.md` 不动;不新开 ADR。

## §工程手段总登记册

| 手段 | 一句话原理 | 优势 | 代价 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| 同构 4/4 通过线 | 与旧仪器同一名单 | 禁 HARKing | 可能仍不成立 | #46;charting | **实装**(决议) |
| 作废⊥不成立 + C 特有 | 不可解释才废 | 负结果可引用;防串台 | 端点偶发非 JSON 废整刀 | #46;清单 #5 | **实装** |
| 缺 chunk 即废 | 禁静默少拼 | 预登记不被事后改薄 | 店面数据损坏会废刀 | Anthropic #5 | **实装** |
| 旁句 (a) 逐字 | 打弃权半边 | 短;无蕴涵 | 仍可能 unknown | #76 | **实装**(正文) |
| 全主张 p1+p2+p3 | 对称多锚 | 不挑侧 | 上下文变长 | #76 D4/D9 | **实装**(表) |
| `CONTROL_PROMPT_C` 并行 | 旧路径可复现 | 隔离 | 双 prompt 维护 | #75;地图 | **留位**(#78) |
| excerpt 落档 | 送模可审计 | 复现确定性层 | 报告变大 | 诊断缺口 §3.2 | **留位**(#78/#79) |
| 成败句并存旧 canonical | 两台仪器 | 不抹历史 | 索引变长 | 地图 Notes | **实装**(决议) |
| 作废补一刀对齐 #69 | 作废≠负结果 | 兑现有效跑 | 须第二次废即停 | #69 | **实装** |
| ACCEPTANCE 分结局 | 成功兑现缺口;作废不改句 | 与 Destination 对齐 | 总判措辞要小心 | #69 D5 | **触发**(#79) |
| ADR-0007 承载 | 事后改判据毁实验 | 不重复开 ADR | 细节在评估 | #69/#76 | **承载** |
| 放宽通过线 / unknown 作废 | 易「过」/看上去严 | — | HARKing / 拟合旧格 | D1-(b);D2-(c) | **弃** |
| 蕴涵旁句 / 只 must_stale 加锚 | 易绿 / 省事 | — | 换实验 / 偏置 | D3-(e);D4-(d) | **弃** |
| 失败替换旧句 / 成功删旧句 | 索引干净 | — | 抹旧仪器 | D6-(b)/(c) | **弃** |
| 作废无限补跑 | 总有读数 | — | 钓鱼 | D5-(c) | **弃** |
| 新开 ADR / 进词表 | 仪式 | — | 重复/过程词 | D8 | **弃** |

## §面试讲法(grilling 预案)

**Q:C 和旧假绿对照还是同一个实验吗?**
A:同一词表「假绿对照」:无工具、只读 T0、问现在是否仍然成立、期望 must_stale 假绿(alive)。差分是 C 私有多锚 + 反默认-unknown 旁句;旧仪器冻结只读,成败另句并存。

**Q:为什么通过线还是 4/4?旧仪器不是 0/4 吗?**
A:不得用旧读数校准。放宽 = HARKing(ADR-0007)。未满 4/4 用失败句引用,不作废。

**Q:旁句是不是又在暗示「按材料判成立」?**
A:不是。字面只禁「缺更新 → 默认 unknown」;判断句仍是「现在是否仍然成立」。蕴涵问法在 Out of scope。

**Q:为什么每条都送 p1+p2+p3,不挑 somehow?**
A:对称加满邻块;单侧加料是见格子前的结构性偏置。表在跑前写死;缺 chunk 整刀废,防止事后变回单锚。

**Q:C 成功了是不是可以删掉旧 0/4 句、写一期闭合?**
A:旧句保留为旧仪器历史。成功句与总判改写只登记「C 对照成立」,仍禁一期闭合 / 全量验收 / 产品已愈假绿。

**Q:作废了还能跑吗?**
A:对齐 #69:不消耗名额,允许且仅允许再开一刀有效跑;再废关图。

**Q:为什么不新开 ADR?**
A:预登记纪律在 ADR-0007;构念在 #76;句纪律同构 #69。本票是规格锁死,评估+决议评论足够。
