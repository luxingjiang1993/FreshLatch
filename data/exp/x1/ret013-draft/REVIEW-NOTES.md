# RET-01.3 review v4 — Ronin 代理人审核记录

> **性质声明**：本表 116 行（影响打分的分歧 95、抽样行 9、内容修正 12）由 **Ronin 代理人（模型）** 受 owner 委托于 2026-10-07 审核，**不是人工逐条审核**。所有判断、改动和法条核实都由模型完成，需要人工签字的地方（三类陷阱定义、qtype 规则本身、下文"没把握"的行）仍需 owner 确认。

## 1. 方法

- **输入（只读）**：`v4/RET-01.3-review-v4.xlsx`、`v4/merged-gold-v4.json`、`v2/gold-draft-v2.json`（A）、B 盲标 json、v2 drafts 语料（`load.C`）。原文件一律没有改动，产出只写在 `ronin-review/` 和 `/tmp/x1-ronin/`。
- **逐行做法**：每一行都打开 relevant、A/B 提名的干扰和同批全部 chunk 的原文（按批次导出到 `work/dump2.md`），先独立回答题目，再按六点对照：①题面清楚、前提为真、在该 as_of 池内答案唯一；②relevant 恰好是作答所需（只定位题干限定语的 chunk 算错）；③要点准确、完整、不多余、不是幻觉；④arm/护栏；⑤category；⑥干扰含同快照冲突块、且不含 relevant。「建议」列只作参考，判断与它不同时以原文为准。
- **qtype**：规则锁定为 kw-v1（说明!B3=kw），没有改规则。「改」行的 qtype 一律写成显式值：默认就是用 `rules_v4.qtype_kw` 对最终题面/relevant/要点重算的结果；只有「冗余证据被规则判成 multi_hop」时才逐题改成 paraphrase，并写明理由（共 8 行：s3-d0-02-q5、s3-d0-02-q1、s3-d3-01-q3、s6-d1-c2-q1、s6-mh-12-new、s5-d0-t1-02-q2、s7-d1-t0-03-q3、s7-d2-t1-04-q3；另有合并行 s3-d1-01-q1 只改 qtype）。
- **不手填**：relevant / distractors 只从 A∪B∪绿色预填提名过的 chunk 里选；所有「改」行都用脚本校验过：要点是 relevant 原文的子串、arm 证据都在 as_of 快照内、护栏题带 T0 干扰、relevant 与干扰不重叠、提名集合不越界（`work/build_final.py`，0 问题）。
- **审核口径（逐行套用）**：
  1. **定位块**：只用来定位题干限定语（如"渗透率回落到66.2%的那家公司"）的 chunk 从 relevant 和要点里移出，可以留作干扰。recall 按命中计（任一 relevant 进前 k 就算命中），定位块会把"答对限定语、没答对问题"也算成命中。
  2. **变化题的 arm/护栏**：沿用建议列的口径。T1 块自己写出前一状态或变化（"原定…调整为""尽管前期…"）的算 arm；必须靠 T0 块才能答的算护栏；只问 T0 内容的题改问 T1 现状（trap-supersede 形式）。
  3. **冗余证据**：几块各自都能独立答对时，可以都放进 relevant（命中口径下无害），但不能算 multi_hop，因为 multi_hop 全命中要求每块都召回。只有题面要求合并（两个子问分在不同文档，或明确要求"列出哪几种/各自"）才保留 multi_hop。
  4. **S3 比价批次**：5 个批次都用泛称"竞品A/B/C"，题面不带批次限定就在 T1 池里不唯一，补限定语（取该批次独有的事实）。
  5. **S6-D0 批次**：同一变更在 memo/patch/channel（或 internal/memo/report）里各写一遍。题面点名某份文档时，其他文档里的同句算元陈述近重复，作干扰。
  6. **要点**：明显答的是另一个问题（问依据却给建议、问局限却给后果）的删；截断的补全；ap-merge-v1 `repair()` 接上的下一句残片（见 §9）截掉；缺主语且主语重要的补主语。
  7. 不为改而改：只是措辞、但不影响作答或打分的地方不动。
- **内容修正**：12 条逐条对照官方原文（cac.gov.cn 令11/13/16，npc.gov.cn 公司法 2023 修订），抓取后在本地全文比对条文，URL 和关键句见 §6。

## 2. 决定计数

| 表 | 决定 | 行数 |
|---|---|---|
| 影响打分的分歧（95） | 合并 | 50 |
| | 改 | 43 |
| | 用A | 1 |
| | 用B | 1 |
| | 删 | 0 |
| 抽样行（9） | 通过 | 7 |
| | 改 | 2 |
| | 删 | 0 |
| 内容修正（12） | 通过 | 11 |
| | 改 | 1 |
| | 不改 | 0 |

合计：改 45（分歧 43 + 抽样 2），删 0。改动的 45 行里，改 relevant 的 22 行（其中 s5-d0-t0-01-q1 同时改题面），只改要点和/或干扰的 19 行，只改题面（S3 补批次限定语）的 4 行，详见 §5。所有「改」行的 qtype 都由「按规则」写成显式值（apply 要求）。

## 3. 与建议不同的行（共 48 行）

「建议」列在 95 行里全是「合并…」；抽样行的默认是「通过」。下表列出所有与之不同的行：45 行「改」、用A 1 行、用B 1 行，外加只改 qtype 的合并行 s3-d1-01-q1。

| 表 | 序号 | 题目 id | 建议 | 我的决定 | 理由（摘要） |
|---|---|---|---|---|---|
| 分歧 | 3 | s3-d3-01-q4 | 合并（实质同 B） | 改 | arm/MH/relevant 接受(三家各一块, T1 块自含"上调至119元""取消固定高价""取消阶梯加价"); 要点补主体与定价动作(原要点"目标客户转向中大型组织"无主体); 干扰去掉 memo#p1@T1(其"价格竞争力下降"本身是 A 的定位变化, 部分相关不宜作干扰) |
| 分歧 | 10 | s1-d0-05-q3 | 合并（含改题） | 改 | 改题限定安全团队合理(B 指出同快照 warn 预警不唯一); 但要点"建议维持现有监控强度，暂不调整部署资源"是建议而非判断依据, 删去; 依据=memo#p2@T0"周边势力活动频率在近两周内维持低位，无明显升级信号" |
| 分歧 | 11 | s7-d1-t0-03-q3 | 合并 | 改 | relevant 取并集(claim#p1/p3、fact#p2)接受; 要点"某政策评估报告中多次出现‘广泛共识认为……’…等表述"是现象描述、"当多个元陈述叠加出现时，其影响力呈指数级放大"不是判断方法, 换成 claim#p3 的"形成闭环论证"一句; 保留 B 的两条; qtype 显式 paraphrase: "如何判断"任一块(claim#p1 来源过窄/fact#p2 选择性引用/claim#p3 闭环论证)单独即可作答, 不应要求三块全命中(原则3) |
| 分歧 | 15 | s7-d2-t1-04-q3 | 合并 | 改 | relevant claim#p3+memo#p3 接受; 要点"…即对内容真实性本"截断, 补全为"…即对内容真实性本身的宣称与实际内容不符"; 删"元陈述层面指出：“本报告不包含任何未经验证的数据"(例子, 非风险); qtype 显式 paraphrase: claim#p3 与 memo#p3 各自独立回答"元陈述与实际不符的检索风险"(B 已指出), 冗余证据非多跳(原则3) |
| 分歧 | 17 | s1-d0-04-q3 | 合并（实质同 B） | 改 | risk#p2@T1(三条海运通道)只定位题干限定词, 移出 relevant 及要点"三条主要海运通道临时关闭"→单 doc, 不再是 multi_hop; arm 保留: memo#p3@T1"尽管平均满意度维持在4.3分，但…负面评论数量同比增加37%"在 T1 内即可表达变化(与建议列"T1 块是否写出 T0 状态"口径一致) |
| 分歧 | 18 | s3-d0-02-q5 | 合并（实质同 B） | 改 | 三块(a#p3 69元/c#p3 69元/b#p3 免费基础版)各自独立答出"C公司", 是冗余证据而非多跳, kw 规则因要点措辞不同误判 multi_hop; qtype 逐题改为 paraphrase(去掉 MH 后规则结果); 要点去掉与问题无关的"限制功能数量…/用户留存率低于行业平均…" |
| 分歧 | 19 | s3-d1-01-q1 | 合并（实质同 A） | 合并 | qtype 逐题改 paraphrase: memo#p1@T1 与 report#p1@T1 各自独立给出"调涨至每月349元…高级功能模块纳入主套餐", 冗余证据非多跳, kw 规则误判 multi_hop; relevant/要点不变 |
| 分歧 | 22 | s4-d2-t1-04-q1 | 合并 | 改 | 题问"相比旧版提升了多少", 只有 memo#p2@T1"误差率由原先的8.7%降至4.3%"给出前后对比; summary#p1"平均预测精度达95.7%"只给现值、无旧版基线, 单独命中答不了题却会被命中制计为命中, 且使题目被规则判成 multi_hop; relevant 仅 memo#p2, summary#p1 移出(不作干扰, 属旁证) |
| 分歧 | 23 | s1-d0-04-q2 | 合并 | 改 | memo#p1(实际值为66.2%)只定位题干限定词, 移出 relevant 与要点"实际值为66.2%"; relevant=memo#p2@T1"某关键节点延误率上升至11%，暴露出单一依赖风险" |
| 分歧 | 27 | s2-d3-01-q1 | 合并 | 改 | 绿色第1要点被截断("…渠道反馈实", 原文"渠道反馈实际转化率低于预期", 因原文"原定 15% 的"含空格自动补全失败), 补全; memo#p2@T1(合作方缩减至单一)讲合作方数量不是"合作目标", 移出 relevant 改作干扰(同 B); arm 保留(同块"原定15%…调整为8%") |
| 分歧 | 28 | s3-d0-01-q3 | 合并（实质同 A） | 改 | memo#p3@T1 单块即答"结束促销…恢复至每月99元…捆绑视频会员的新组合方案"(arm, 同块自含); report#p3@T1 只讲调整后效果(流失率下降/营收增长15%)不是所问"具体变化", 移出 relevant 与要点→不再 multi_hop(否则 MH 全命中被迫要求非必需块) |
| 分歧 | 31 | p1-mh-03-new | 合并（含改题） | 改 | 旧办法 o13#p2 标准合同条件同时要求"处理个人信息不满100万人的"，题问"卡在多少人"未限定出境数，补此要点 |
| 分歧 | 35 | s3-d3-01-q2 | 合并（实质同 B） | 改 | 题面"竞品B在两个时间点…"在 T1 池有 5 个竞品B(s3-d0-01/d0-03/d0-04/d1-01/d2-01), 不唯一; 加限定词"在竞品A附带云存储的那份比价里"; 护栏与两口径要点(129/99)保留 |
| 分歧 | 37 | s7-d1-t0-03-q1 | 合并（含改题） | 改 | 改题"材料给出了哪几种解释"后, reason#p1@T0"部署流水线中各组件更新节奏不一致，造成同一时间点下多版本共存的快照冲突"也是一种使相反状态同时为真的解释, 不能当干扰, 移入 relevant(B 提名); 仍多跳 |
| 分歧 | 41 | s1-d2-01-q4 | 合并（含改题） | 改 | 改题合理; 但第3要点"需重新评估债务可持续性"是后果不是"依据", 删去; 依据=analysis#p3@T1"下调短期展望至负面观察""外部融资成本已开始攀升" |
| 分歧 | 47 | s3-d2-01-q2 | 合并 | 改 | 题面"以自动化报告为卖点的竞品B"同时符合 s3-d0-03 的竞品B(T0"新增自动化报表生成功能", T1 也"新增30天免费试用"), 答案不唯一; 加限定词"在竞品C月费调到195元的那份比价里"; arm 保留(p2@T1"在新版本基础上增加30天免费试用期…优化了报告生成算法"自含) |
| 分歧 | 48 | s3-d3-01-q3 | 合并（实质同 B） | 改 | qtype 显式 paraphrase: memo#p3@T1"取消阶梯加价，统一为89元/月，涵盖全部功能模块"与 report#p3@T1"所有功能模块统一纳入89元基础包"各自独立作答(冗余证据, 原则3)；"竞品C的报价结构…"在 T1 池有 5 个竞品C 均有调价(s3-d1-01 新增按月订阅也是结构调整), 不唯一; 加限定词"在竞品A附带云存储的那份比价里"; arm 保留("取消阶梯加价，统一为89元"同块自含) |
| 分歧 | 53 | s6-d1-c2-q1 | 合并 | 改 | relevant = o16#p7 + o11#p2(题问"和以前比", T1 池内令11 原文为必需) + memo#p1/p2/p3(memo#p3 一块写全新旧门槛; memo#p2 给敏感信息1万人线, A 已提名, 绿色漏了); 要点改为新旧两条原句, 去掉孤立的"自上年1月1日起累计"(且缺"当年"新起点); 建议理由已说"不按 multi_hop"但绿色仍是按规则(=multi_hop), 显式改 paraphrase |
| 分歧 | 54 | s6-d1-c3-q1 | 合并 | 改 | relevant(memo#p1 + o13#p2 + o16#p8)接受; memo#p3"敏感个人信息累计出境未满一万人的，同样落在这一区间，应当订立标准合同或通过认证…"与 o16#p8 一致, 是正确信息不应作干扰, 移出; 保留 o16#p5(C4)、o16#p7 |
| 分歧 | 55 | s1-d2-01-q1 | 合并（实质同 B） | 改 | analysis#p3@T1(评级负面观察)只定位题干限定词, 移出 relevant/要点→单 doc paraphrase; arm 保留: memo#p1@T1"尽管前期数据显示通胀回落，最新数据揭示核心通胀存在反弹苗头"自含前后对比 |
| 分歧 | 56 | s3-d0-01-q1 | 合并 | 改 | 题面"竞品A的基础套餐在T0与T1之间的价格变化"在 T1 池不唯一(s3-d3-01 竞品A 同为99→119, s3-d1-01 竞品A"基础套餐调涨至每月349元"); 加限定词"在流量通话套餐比价里"(同批 q3/q4 用法); 护栏与 relevant 保留(report#p1@T1"竞品A的119元定价"为独立可答块) |
| 分歧 | 57 | s3-d0-02-q1 | 合并 | 改 | 同上: a#p1/b#p1/c#p1 各自给出 A公司99元, 冗余证据, qtype 改 paraphrase; 删要点"该版本在发布初期获得市场关注…"(与定价无关) |
| 分歧 | 60 | s4-d2-t1-04-q4 | 合并（实质同 B） | 改 | 题面直接对应 memo#p3@T1"后续将基于真实流量数据持续优化参数，确保长期适应性"; B 补的 report#p3"将模型输出与预算分配系统联动…防止超支风险"与模型长期适用性无关, internal#p2/p3 是讨论建议/测试流程, 均非必需; 改为仅 memo#p3(同 A 的 relevant), 并删 A 的非措施要点"新版模型已集成至核心调度系统"; report#p3 作干扰 |
| 分歧 | 61 | s5-d0-t1-02-q2 | 合并 | 改 | 绿色要点"值得注意的是，2020年一份独立研究尝试复现该数据，发现实际监测结果与转述版本存"被截断(原文"存在显著差异"), 且它是案例不是"为何"的理由, 删去(memo#p2 的确认偏误要点已覆盖); relevant memo#p2/p3+summary#p3 接受; qtype 显式 paraphrase: memo#p3"即使原始数据无法验证，只要被多次引用并嵌入正式论述，便可能成为“事实”本身…更高的质疑门槛"一块即覆盖引用行为与制度惯性两个角度, 三块是可并列的独立论据, 不应要求全命中(原则3) |
| 分歧 | 62 | s5-d1-t1-03-q1 | 合并 | 改 | relevant memo 三块接受; 删复述题干背景的要点"在2020年的一份内部报告中，某机构曾提及2018年消费者行为调查的初步结果"(不是"为何"); 42/46/48% 要点去掉接上的半句 |
| 分歧 | 63 | s5-d1-t1-03-q4 | 合并 | 改 | 题面"多份来源对同一事件的描述存在数值差异…确保汇编叙述的可信度"对应 summary 文档的案例(1.3万 vs 9800)与方法: summary#p2"经交叉验证…"+summary#p3"分层标注法…确保合成叙述的严谨性"; 绿色把 summary#p2 当干扰不对, note#p3"数据转述日志"针对单份幻灯片篡改、非多源数值差异, 改作干扰(采 B, 推翻建议与 A) |
| 分歧 | 64 | s7-d3-t1-05-q2 | 合并 | 用B | 87%仍视为达标只在 memo#p2@T1; memo#p3 未提87%, 只讲检索危险, 属多余; A 的要点一条截断、一条答非所问 |
| 分歧 | 67 | s3-d0-01-q4 | 合并 | 改 | 护栏 relevant(B 三块覆盖均价+B+C, A 价在 report#p1)可接受; 但要点"价格上调至每月219元""标准套餐恢复至每月99元"丢了主体(三家竞品并列时主体是关键), 补全为"竞品B在高端套餐基础上新增家庭共享功能，价格上调至每月219元""竞品C已于本季度初结束促销活动，标准套餐恢复至每月99元" |
| 分歧 | 71 | s4-d0-t0-01-q4 | 合并（实质同 B） | 改 | 题问"已采取"的协同措施; plan#p2@T0 是"拟开发可视化对比工具"(未采取), 不应入 relevant, 改作干扰; relevant 仅 plan#p3@T0"已启动跨团队协作机制，确保模型变更前完成影响评估与沟通预案"(同 A, 推翻建议) |
| 分歧 | 74 | s4-d0-t1-02-q6 | 合并 | 改 | 题问评审"提出了哪些建议"; review#p3@T1 是"会议决定成立跨职能工作组…"(决定非建议), 移出 relevant 与要点, 改作干扰(同 B); relevant=review#p2"一是…成本敏感度分析功能；二是扩展对云服务阶梯定价的支持"; 保留 A 的干扰 report#p3(报告里的建议) |
| 分歧 | 75 | s4-d1-t0-03-q4 | 合并（实质同 B） | 改 | 三块 plan 均为未来能力(接受 B); 但题问"预期达到什么效果", 要点"增加成本敏感度分析模块"截掉了效果, 补为"增加成本敏感度分析模块，帮助识别关键影响因子，辅助管理层制定策略调整预案" |
| 分歧 | 76 | s4-d2-t1-04-q3 | 合并（实质同 B） | 改 | report#p1@T1(边缘节点低19.6%)只定位题干限定词, 移出 relevant 与要点, 改作干扰; report#p2"弹性伸缩阈值优化…资源浪费减少31%" + memo#p1"精细化建模…动态权重调整机制"(两方都选, 接受) 保留, 仍 multi_hop |
| 分歧 | 77 | s4-d3-t0-05-q4 | 合并（实质同 B） | 用A | 题问"采取了哪些具体措施", 只有 report#p2@T0"实施缓冲区大小动态调整策略，并引入周期性垃圾回收机制"; report#p1 讲问题所在(非措施), A 把它作干扰正确; 推翻建议 |
| 分歧 | 78 | s5-d0-t0-01-q1 | 合并（实质同 B） | 改 | 原题"综合多份文档概述主要成效与核心挑战"开放无界: T0 池里写成效/挑战的块至少 10 个(report#p1/p2、analysis#p1/p2、memo#p1/p2、summary#p1/p2、internal#p1、press#p2), A/B 只重合 2 块, MH 全命中要求的是任意子集; 改题收窄为"响应速度/响应时间上的量化成效 + 推广面临的三大挑战", relevant=report#p1(约40%)+analysis#p1(2.3小时)+summary#p2(三大挑战), memo#p2 改作干扰 |
| 分歧 | 79 | s5-d0-t0-01-q2 | 合并 | 改 | 题面点名"某市智慧协作平台"; 同一平台的直接矛盾是 press#p1"零延迟…创新典范" vs press#p2"实际覆盖范围仅限于主城区…存在信息孤岛现象", 绿色列漏了 press#p2(A 提名过), 补入 relevant 与要点; memo#p2 保留 |
| 分歧 | 82 | s5-d0-t1-02-q1 | 合并 | 改 | relevant 接受; 要点"…便可能成为“事实”本身。尤其当新数据与既有叙事冲突时"是 repair 残片, 截回到"…成为“事实”本身" |
| 分歧 | 83 | s5-d0-t1-02-q3 | 合并 | 改 | relevant report#p2/p3 接受; 要点"…实为“中位数时间”。这种语义微调虽无恶意"为残片且与另一要点重复, 截回到"…原始定义实为“中位数时间”" |
| 分歧 | 84 | s5-d0-t1-02-q4 | 合并 | 改 | 盲点在 analysis#p3"此事件暴露了内部数据整合机制中的结构性盲点：权威性不等于准确性，一致性也不代表全面性"; analysis#p2 是案情经过, 非必需却被 MH 全命中强制要求, 移出(同 A 的 relevant); 其要点还带残片"…未能获得同等权重。这说明" |
| 分歧 | 86 | s5-d2-t0-04-q3 | 合并（实质同 B） | 改 | relevant(B 五块覆盖三份文档)接受; 但干扰 memo#p2@T0"虽未发表于学术期刊，但在本地论坛中被多次转引"本身就是"未经证实信息被转引"的例子, 不能作干扰, 移除 |
| 分歧 | 87 | s6-d0-t1-01-q1 | 合并（实质同 B） | 改 | 题面限定"顾问备忘中", 答案=memo#p1@T1"原定两周的复验周期现已延长至三周。旧版中的两周窗口仅保留用于历史对照参考"; patch#p1"系统内复验窗口配置已由14天调整为21天"是补丁记录里的同一变更, 作干扰(同 A, 推翻建议) |
| 分歧 | 88 | s6-d0-t1-01-q2 | 合并（实质同 B） | 改 | 题面限定"渠道纪要中", 答案=channel#p1@T1"已从主文迁移至附录，此举旨在分离操作细节与核心政策声明…"; memo#p2 未提渠道纪要, 是顾问备忘里的同类表述, 作干扰(同 A) |
| 分歧 | 89 | s6-d0-t1-01-q3 | 合并（实质同 B） | 改 | "结论段"是 memo#p3@T1 的用语("结论段落已更新为“待复验”…反映当前评估仍需进一步验证"), 也只有它给出"为何"; patch#p2 是系统状态字段的补丁记录, 其要点"该变更同步至前端展示与审批流节点"不回答所问, 改作干扰(同 A) |
| 分歧 | 91 | s6-d1-c1-q1 | 合并（实质同 B） | 改 | o16#p9@T1 一块即可作答(有效期3年/届满前60个工作日申请/可延长3年); memo#p1"有效期已由原令11规定的2年调整为令16规定的3年"、memo#p2"…经国家网信部门批准后，评估结果可再延长3年"独立作答, 与 c2/c3 的处理一致并入 relevant(冗余证据, 非多跳, 仍 paraphrase); 第二条要点带 repair 残片"…申请。经国家网信部门批准", 截掉; 干扰保留同快照冲突 o11#p13/p14, memo#p3(不能续期的情形, 内容正确)移出干扰 |
| 分歧 | 93 | s6-d2-g3-q1 | 合并 | 改 | relevant 与要点接受(memo#p1 给2018→2023变化, call#p1 补"负有责任的董事应当承担赔偿责任"这一新责任主体, 真多跳); 但干扰 call#p3"由公司其他股东按照其出资比例足额缴纳相应出资"与 memo#p3"已过缴纳期限仍未缴足就转让的，由转让双方在差额内连带担责"都是2023法关于未按期出资责任的正确条文, 移出; call#p4(未届期加速到期)作近邻干扰保留 |
| 分歧 | 94 | s6-mh-12-new | 合并 | 改 | 第二问"受让人没交，原股东还要担什么责"memo#p3"受让人到期不缴的，原股东负补充责任"与 call#p5 同样能答, 绿色把 memo#p3 当干扰不对, 移入 relevant(同 B); 全题可由 memo 一份文档(p1+p3)答全, 冗余证据, 显式改 paraphrase |
| 分歧 | 95 | s6-mh-15-new | 合并 | 改 | 题面前半"顾问备忘说存量公司要调整出资期限"是前提, 真正问的是"新法本身给新设公司的缴足期限"→ p1-colaw-capital#p1@T1"自公司成立之日起五年内缴足"; g2-memo#p1/g1-memo#p2 只定位前提, 按原则1 移出 relevant 与要点(g1-memo#p2 含正确的"新设公司直接适用五年期限", 不作干扰); 不再多跳 |
| 抽样 | 7 | s4-d0-t0-01-q3 | 通过（A=B 抽样） | 改 | 题问局限性, 要点后半"建议后续补充边缘场景训练样本，以增强泛化能力"是建议不是局限, 截去; 保留"当前模型仍存在对非标准流程的覆盖不足问题" |
| 抽样 | 9 | s7-d0-t0-01-q3 | 通过（A=B 抽样） | 改 | relevant memo#p3@T0 正确; 要点1"元陈述表明：“本系统当前无已知安全漏洞"是题干复述, 删; 要点2 开头带孤立的"”", 改为"该声明发布于一次重大补丁前，且未说明其时效性"; 保留"可能误将“无漏洞”视为绝对事实" |

## 4. 推翻 A 和 B 的行

按「最终结论 A、B 都没提出」统计：

| 题目 id | A、B 的结论 | 我的结论 | 依据 |
|---|---|---|---|
| s7-d1-t0-03-q1 | A、B 的 relevant 都是 memo#p2 + reason#p2；B 把 reason#p1 当干扰 | relevant 加入 reason#p1@T0 | 改题后问"材料给出了哪几种解释"，reason#p1"部署流水线中各组件更新节奏不一致，造成同一时间点下多版本共存的快照冲突"也是一种解释 |
| s6-mh-15-new | A、B 都判 multi_hop（法条 + 一块备忘） | 只留 p1-colaw-capital#p1@T1，paraphrase | 题面前半"顾问备忘说存量公司要调整出资期限"是前提，真正问的是"新法本身给新设公司的缴足期限"（"自公司成立之日起五年内缴足"）；两块备忘只定位前提 |
| s6-mh-12-new | A、B 都判 multi_hop | relevant 收 memo#p3（同 B），qtype 改 paraphrase | memo#p1 + memo#p3 同一份文档就能答全，法条 call#p5 是冗余证据 |
| s5-d0-t1-02-q2 | A=lexical，B=multi_hop | paraphrase | memo#p3 一块已覆盖"引用行为与制度惯性"两个角度，三块是可并列的独立论据 |
| s3-d3-01-q2、s3-d3-01-q3、s3-d2-01-q2、s3-d0-01-q1 | A、B 都接受原题面 | 补批次限定语 | 原题"竞品B/竞品C/竞品A…"在 T1 池里有 5 个批次的同名竞品，答案不唯一 |
| s5-d0-t0-01-q1 | A、B 都接受"概述主要成效与核心挑战" | 改题为"响应速度/响应时间的量化成效 + 三大挑战" | 原题开放，A、B 的 relevant 各取各的（memo#p2、summary#p1 都不是"成效/挑战"的直接陈述）；改题后答案收敛到 report#p1、analysis#p1、summary#p2 |

另外 3 行我采用了一方、推翻了另一方和建议：s4-d3-t0-05-q4（用A）、s7-d3-t1-05-q2（用B）、s5-d1-t1-03-q4（采 B 的 relevant，推翻建议和 A）。S6-D0-t1-01 的 3 题采 A 的口径，推翻 B 和建议。

## 5. 改 / 删 汇总

删：0 行。没有题目错到改不了；有问题的都能在提名集合内修好。

改：45 行。

| 题目 id | 改动字段 | 最终 qtype（规则结果） | 改动后 relevant |
|---|---|---|---|
| s3-d3-01-q4 | 要点、干扰、qtype | multi_hop（规则 multi_hop） | s3-d3-01-memo#p3@T1<br>s3-d3-01-report#p1@T1<br>s3-d3-01-report#p2@T1 |
| s1-d0-05-q3 | 要点、qtype | paraphrase（规则 paraphrase） | s1-d0-05-memo#p2@T0 |
| s7-d1-t0-03-q3 | 要点、qtype | paraphrase（规则 multi_hop） | s7-d1-t0-03-claim#p1@T0<br>s7-d1-t0-03-claim#p3@T0<br>s7-d1-t0-03-fact#p2@T0 |
| s7-d2-t1-04-q3 | 要点、qtype | paraphrase（规则 multi_hop） | s7-d2-t1-04-claim#p3@T1<br>s7-d2-t1-04-memo#p3@T1 |
| s1-d0-04-q3 | relevant、要点、干扰、qtype | paraphrase（规则 paraphrase） | s1-d0-04-memo#p3@T1 |
| s3-d0-02-q5 | 要点、qtype | paraphrase（规则 multi_hop） | s3-d0-02-a#p3@T0<br>s3-d0-02-b#p3@T0<br>s3-d0-02-c#p3@T0 |
| s4-d2-t1-04-q1 | relevant、要点、qtype | paraphrase（规则 paraphrase） | s4-d2-t1-04-memo#p2@T1 |
| s1-d0-04-q2 | relevant、要点、干扰、qtype | paraphrase（规则 paraphrase） | s1-d0-04-memo#p2@T1 |
| s2-d3-01-q1 | relevant、要点、干扰、qtype | paraphrase（规则 paraphrase） | s2-d3-01-memo#p1@T1 |
| s3-d0-01-q3 | relevant、要点、qtype | paraphrase（规则 paraphrase） | s3-d0-01-memo#p3@T1 |
| p1-mh-03-new | 要点、qtype | multi_hop（规则 multi_hop） | p1-cac-o13#p2@T1<br>p1-cac-o16#p8@T1 |
| s3-d3-01-q2 | 题面、qtype | paraphrase（规则 paraphrase） | s3-d3-01-memo#p2@T1<br>s3-d3-01-report#p2@T1 |
| s7-d1-t0-03-q1 | relevant、要点、干扰、qtype | multi_hop（规则 multi_hop） | s7-d1-t0-03-memo#p2@T0<br>s7-d1-t0-03-reason#p1@T0<br>s7-d1-t0-03-reason#p2@T0 |
| s1-d2-01-q4 | 要点、qtype | paraphrase（规则 paraphrase） | s1-d2-01-analysis#p3@T1 |
| s3-d2-01-q2 | 题面、qtype | paraphrase（规则 paraphrase） | s3-d2-01-competitor-pricing#p2@T1 |
| s3-d3-01-q3 | 题面、qtype | paraphrase（规则 multi_hop） | s3-d3-01-memo#p3@T1<br>s3-d3-01-report#p3@T1 |
| s6-d1-c2-q1 | relevant、要点、qtype | paraphrase（规则 multi_hop） | p1-cac-o16#p7@T1<br>p1-cac-o11#p2@T1<br>s6-d1-c2-memo#p1@T1<br>s6-d1-c2-memo#p2@T1<br>s6-d1-c2-memo#p3@T1 |
| s6-d1-c3-q1 | 干扰、qtype | lexical（规则 lexical） | s6-d1-c3-memo#p1@T1<br>p1-cac-o13#p2@T1<br>p1-cac-o16#p8@T1 |
| s1-d2-01-q1 | relevant、要点、干扰、qtype | paraphrase（规则 paraphrase） | s1-d2-01-memo#p1@T1 |
| s3-d0-01-q1 | 题面、qtype | lexical（规则 lexical） | s3-d0-01-memo#p1@T1<br>s3-d0-01-report#p1@T1 |
| s3-d0-02-q1 | 要点、qtype | paraphrase（规则 multi_hop） | s3-d0-02-a#p1@T0<br>s3-d0-02-b#p1@T0<br>s3-d0-02-c#p1@T0 |
| s4-d2-t1-04-q4 | relevant、要点、干扰、qtype | paraphrase（规则 paraphrase） | s4-d2-t1-04-memo#p3@T1 |
| s5-d0-t1-02-q2 | 要点、qtype | paraphrase（规则 multi_hop） | s5-d0-t1-02-memo#p2@T1<br>s5-d0-t1-02-memo#p3@T1<br>s5-d0-t1-02-summary#p3@T1 |
| s5-d1-t1-03-q1 | 要点、qtype | paraphrase（规则 paraphrase） | s5-d1-t1-03-memo#p1@T1<br>s5-d1-t1-03-memo#p2@T1<br>s5-d1-t1-03-memo#p3@T1 |
| s5-d1-t1-03-q4 | relevant、要点、干扰、qtype | paraphrase（规则 paraphrase） | s5-d1-t1-03-summary#p2@T1<br>s5-d1-t1-03-summary#p3@T1 |
| s3-d0-01-q4 | 要点、qtype | paraphrase（规则 paraphrase） | s3-d0-01-memo#p2@T1<br>s3-d0-01-memo#p3@T1<br>s3-d0-01-report#p1@T1 |
| s4-d0-t0-01-q4 | relevant、要点、干扰、qtype | paraphrase（规则 paraphrase） | s4-d0-t0-01-plan#p3@T0 |
| s4-d0-t1-02-q6 | relevant、要点、干扰、qtype | paraphrase（规则 paraphrase） | s4-d0-t1-02-review#p2@T1 |
| s4-d1-t0-03-q4 | 要点、qtype | paraphrase（规则 paraphrase） | s4-d1-t0-03-plan#p1@T0<br>s4-d1-t0-03-plan#p2@T0<br>s4-d1-t0-03-plan#p3@T0 |
| s4-d2-t1-04-q3 | relevant、要点、干扰、qtype | multi_hop（规则 multi_hop） | s4-d2-t1-04-memo#p1@T1<br>s4-d2-t1-04-report#p2@T1 |
| s5-d0-t0-01-q1 | 题面、relevant、要点、干扰、qtype | multi_hop（规则 multi_hop） | s5-d0-t0-01-report#p1@T0<br>s5-d0-t0-01-analysis#p1@T0<br>s5-d0-t0-01-summary#p2@T0 |
| s5-d0-t0-01-q2 | relevant、要点、qtype | multi_hop（规则 multi_hop） | s5-d0-t0-01-memo#p2@T0<br>s5-d0-t0-01-press#p1@T0<br>s5-d0-t0-01-press#p2@T0 |
| s5-d0-t1-02-q1 | 要点、qtype | multi_hop（规则 multi_hop） | s5-d0-t1-02-memo#p1@T1<br>s5-d0-t1-02-memo#p3@T1<br>s5-d0-t1-02-summary#p1@T1<br>s5-d0-t1-02-summary#p2@T1 |
| s5-d0-t1-02-q3 | 要点、qtype | paraphrase（规则 paraphrase） | s5-d0-t1-02-report#p2@T1<br>s5-d0-t1-02-report#p3@T1 |
| s5-d0-t1-02-q4 | relevant、要点、qtype | multi_hop（规则 multi_hop） | s5-d0-t1-02-report#p3@T1<br>s5-d0-t1-02-analysis#p3@T1 |
| s5-d2-t0-04-q3 | 干扰、qtype | multi_hop（规则 multi_hop） | s5-d2-t0-04-analysis#p3@T0<br>s5-d2-t0-04-memo#p1@T0<br>s5-d2-t0-04-memo#p3@T0<br>s5-d2-t0-04-report#p1@T0<br>s5-d2-t0-04-report#p2@T0 |
| s6-d0-t1-01-q1 | relevant、要点、干扰、qtype | lexical（规则 lexical） | s6-d0-t1-01-memo#p1@T1 |
| s6-d0-t1-01-q2 | relevant、要点、干扰、qtype | lexical（规则 lexical） | s6-d0-t1-01-channel#p1@T1 |
| s6-d0-t1-01-q3 | relevant、要点、干扰、qtype | lexical（规则 lexical） | s6-d0-t1-01-memo#p3@T1 |
| s6-d1-c1-q1 | relevant、要点、干扰、qtype | paraphrase（规则 paraphrase） | p1-cac-o16#p9@T1<br>s6-d1-c1-memo#p1@T1<br>s6-d1-c1-memo#p2@T1 |
| s6-d2-g3-q1 | 干扰、qtype | multi_hop（规则 multi_hop） | p1-colaw-capital-call#p1@T1<br>p1-colaw-capital-call#p2@T1<br>p1-colaw-capital-call#p5@T1<br>p1-colaw-capital-transition#p2@T1<br>s6-d2-g3-memo#p1@T1 |
| s6-mh-12-new | relevant、干扰、qtype | paraphrase（规则 multi_hop） | p1-colaw-capital-call#p5@T1<br>s6-d2-g3-memo#p1@T1<br>s6-d2-g3-memo#p3@T1 |
| s6-mh-15-new | relevant、要点、qtype | paraphrase（规则 paraphrase） | p1-colaw-capital#p1@T1 |
| s4-d0-t0-01-q3 | 要点、qtype | paraphrase（规则 paraphrase） | s4-d0-t0-01-memo#p3@T0 |
| s7-d0-t0-01-q3 | 要点、qtype | paraphrase（规则 paraphrase） | s7-d0-t0-01-memo#p3@T0 |

## 6. 内容修正核实表

全部 12 条都在官方原文核到了，没有「未能在官方原文核实」的。抓取时间 2026-10-07，抓取副本在 `/tmp/x1-ronin/src/*.txt`。

| 序号 | 修正 id | 决定 | 官方原文（URL） | 核实结论 / 关键句 |
|---|---|---|---|---|
| 1 | s6-d2-g1-memo-e1 | 通过 | http://www.npc.gov.cn/c2/c30834/202312/t20231229_433999.html | 已核：公司法(2023修订)第四十七条"全体股东认缴的出资额由股东按照公司章程的规定自公司成立之日起五年内缴足"；第二百六十六条第二款"本法施行前已登记设立的公司，出资期限超过本法规定的期限的…应当逐步调整至本法规定的期限以内"。改文"新设公司直接适用五年期限；…存量公司按过渡规定逐步调整"与两条一致，删去无出处的"适用于所有新设立及存续"正确。来源 http://www.npc.gov.cn/c2/c30834/202312/t20231229_433999.html |
| 2 | s6-d2-g2-memo-e1 | 通过 | http://www.npc.gov.cn/c2/c30834/202312/t20231229_433999.html | 已核：公司法第二百六十六条第二款主体是"本法施行前已登记设立的公司，出资期限超过本法规定的期限的"，原文"旧法施行后设立""出资周期超过五年以上"不符；改文与条文一致("章程约定的出资期限"对有限责任公司对应第四十七条"按照公司章程的规定")。来源 http://www.npc.gov.cn/c2/c30834/202312/t20231229_433999.html |
| 3 | s6-d2-g2-memo-e2 | 改 | http://www.npc.gov.cn/c2/c30834/202312/t20231229_433999.html<br>https://www.gov.cn/zhengce/zhengceku/202407/content_6960377.htm | 已核：第二百六十六条第二款"对于出资期限、出资额明显异常的，公司登记机关可以依法要求其及时调整。具体实施办法由国务院规定。"，删去无出处的"不影响既往法律效力，仅针对未来出资行为"正确。但 T1 快照日 2026-10-06 时国务院已于 2024-07-01 公布《国务院关于实施〈中华人民共和国公司法〉注册资本登记管理制度的规定》(国令第784号, https://www.gov.cn/zhengce/zhengceku/202407/content_6960377.htm)，建议改文的"具体办法由国务院另行规定"读作尚未出台、对 T1 不准确；改为条文原话"具体实施办法由国务院规定"。来源 http://www.npc.gov.cn/c2/c30834/202312/t20231229_433999.html |
| 4 | s6-d2-g3-memo-e1 | 通过 | http://www.npc.gov.cn/c2/c30834/202312/t20231229_433999.html | 已核：公司法第八十八条第一款"股东转让已认缴出资但未届出资期限的股权的，由受让人承担缴纳该出资的义务；受让人未按期足额缴纳出资的，转让人对受让人未按期缴纳的出资承担补充责任"；第二款"未按照公司章程规定的出资日期缴纳出资…的股东转让股权的，转让人与受让人在出资不足的范围内承担连带责任；受让人不知道且不应当知道存在上述情形的，由转让人承担责任"。改文与之一致(第二款"非货币财产实际价额显著低于认缴额"一情形未写，属概括，不构成错误)。来源 http://www.npc.gov.cn/c2/c30834/202312/t20231229_433999.html |
| 5 | s6-d1-c1-memo-e1 | 通过 | https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm | 已核：令16"自公布之日起施行"(2024-03-22)；第九条未出现"适用于所有新提交的评估申请"，删去正确。另：核对提醒写"令16 第7–9、11条"，官方文本中"与本规定不一致的，适用本规定"是第十三条，第十一条是数据安全保护义务，提醒里的"11条"应为"13条"。来源 https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm |
| 6 | s6-d1-c1-memo-e2 | 通过 | https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm | 已核：令16第九条"…可以在有效期届满前60个工作日内通过所在地省级网信部门向国家网信部门提出延长评估结果有效期申请。经国家网信部门批准，可以延长评估结果有效期3年。"改文一致。来源 https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm |
| 7 | s6-d1-c2-memo-e1 | 通过 | https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm | 已核：令16第七条(二)"关键信息基础设施运营者以外的数据处理者…自当年1月1日起累计向境外提供100万人以上个人信息（不含敏感个人信息）"，是"数据出境安全评估"、是"向境外提供"而非"处理"。改文一致。来源 https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm |
| 8 | s6-d1-c2-memo-e2 | 通过 | https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm | 已核：令16第七条(二)"…或者1万人以上敏感个人信息"，统计口径为"自当年1月1日起累计向境外提供"。改文一致。来源 https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm |
| 9 | s6-d1-c2-memo-e3 | 通过 | https://www.cac.gov.cn/2022-07/07/c_1658811536396503.htm<br>https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm | 已核：令11第四条(三)"自上年1月1日起累计向境外提供10万人个人信息或者1万人敏感个人信息的数据处理者向境外提供个人信息"(https://www.cac.gov.cn/2022-07/07/c_1658811536396503.htm)；令16第七条(二)为当年起累计100万人以上/1万人以上敏感(https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm)。"放宽"方向正确。剩余简化：令11第四条(二)还有"处理100万人以上个人信息的数据处理者向境外提供个人信息"一项触发条件，改文未提；它在令16下的地位需结合第十三条解释，我未在官方原文找到明文表述，故不替它下结论、不改文。 |
| 10 | s6-d1-c3-memo-e1 | 通过 | https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm<br>https://www.cac.gov.cn/2023-02/24/c_1678884830036813.htm | 已核：令16第八条"…应当依法与境外接收方订立个人信息出境标准合同或者通过个人信息保护认证"(https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm)；令13第四条(三)"自上年1月1日起累计向境外提供个人信息不满10万人的"(https://www.cac.gov.cn/2023-02/24/c_1678884830036813.htm)。"方可适用"把令13第四条四项同时满足的条件简化为一项必要条件，不算错。 |
| 11 | s6-d1-c3-memo-e2 | 通过 | https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm | 已核：令16第八条是"应当…订立…标准合同或者通过个人信息保护认证"，不是"可选择"。改文一致。来源 https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm |
| 12 | s6-d1-c3-memo-e3 | 通过 | https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm | 已核：令16第八条"…或者不满1万人敏感个人信息的，应当…订立个人信息出境标准合同或者通过个人信息保护认证"；第七条(二)"…100万人以上个人信息（不含敏感个人信息）或者1万人以上敏感个人信息"须申报评估。改文的上限补充正确(第三至六条豁免情形另行适用，见第八条第二款)。来源 https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm |

补充说明：
- 核对提醒写"令16 第7–9、11条"。官方文本中，"与本规定不一致的，适用本规定"是**第十三条**（语料里是 o16#p11），第十一条讲的是数据安全保护义务。提醒里的条号应改成 13。
- 语料现在的 memo 文字（v2 drafts）看起来已经是建议改文。apply 只把决定写进 `content-fixes-decisions.json`，不改语料。如果采用 g2-memo-e2 的改文，需要另行把 `s6-d2-g2-memo#p3@T1` 里的"具体办法由国务院另行规定"改成"具体实施办法由国务院规定"。
- c2-memo-e3 还剩一处简化没改：令11 第四条（二）"处理100万人以上个人信息的数据处理者向境外提供个人信息"也是触发条件。它在令16 下怎么处理，要结合第十三条解释，我没有在官方原文里找到明文，所以没有替它下结论。

## 7. 最没把握的 10 行

| # | 题目 id | 决定 | 为什么没把握 |
|---|---|---|---|
| 1 | s5-d1-t1-03-q4 | 改 | 采 B 的读法，把题面锚定到 summary 文档的案例（1.3万 vs 9800），note#p3"数据转述日志"改作干扰；题面"应采取何种方法"也可以宽读成"任何溯源方法都算"，那样 note#p3、report#p3 都该进 relevant |
| 2 | s6-d2-g3-q1 | 改 | 题面宽（"责任主体和责任形式发生了哪些变化"），memo#p1 把"加速到期""未届期转让"也列为新规；我只留 call#p4 作干扰（未届期，非未按期），把 call#p3、memo#p3 移出干扰。干扰取舍有主观成分 |
| 3 | s6-d0-t1-01-q2 | 改 | 按"题面点名渠道纪要"把 memo#p2 作干扰；但生成规格里写的是"渠道纪要把口头折扣从备忘正文挪到附录"，memo#p2 也可能是同一事件的正当证据 |
| 4 | s5-d0-t1-02-q4 | 改 | 移出 analysis#p2（案情经过），认为盲点只在 analysis#p3；也可以认为 p2 的"非公开、非标准的数据若具备正面结论倾向，更容易被采纳"本身就是盲点 |
| 5 | s6-mh-15-new | 改 | 这是专门造的多跳题，我按"前提块不算证据"拆成单跳；如果 owner 认为前提也要检索，应恢复 multi_hop |
| 6 | s4-d0-t1-02-q1 | 合并 | report#p1@T1"响应速度提升45%"也是改进点，但 A、B 都没提名，按"不手填"没加 |
| 7 | s1-d0-05-q4 | 合并 | 题面偏泛，warn#p1 + warn#p3 作答可以接受，但答案边界不清 |
| 8 | s5-d0-t0-01-q6 | 合并 | 要点里"列为优先改进项"带判断，relevant 四块的取舍有主观成分 |
| 9 | s5-d0-t0-01-q1 | 改 | 题面是我改写的（收敛到量化成效 + 三大挑战）；改写会改变这道题原来的考察意图 |
| 10 | s6-d1-c4-q1 | 合并 | category 按规则判 trap（C4 两侧都在），A、B 都判 hard；三类陷阱定义还没签字 |

## 8. 配额重算与 check_x1

按事实判断完以后重算（apply 输出 + check_x1，口径同 `check_v4.py`）：

| 指标 | 审核前（merged 预填） | Ronin 审核后 | 门槛 | 是否通过 |
|---|---|---|---|---|
| n（保留题数） | 211 | 211（删 0） | — | — |
| n_arm | 168 | 168 | ≥ 90 | 通过 |
| lexical（arm） | 53 | 51 | ≥ 30 | 通过 |
| paraphrase（arm） | 66 | 83 | ≥ 30 | 通过 |
| multi_hop（arm） | 49 | **34** | ≥ 30 | 通过（余量 4） |
| trap+adversarial / arm | 30.95%（52/168） | 30.95%（52/168） | ≥ 30% | 通过（余量 1 题） |
| check_x1 exit_code | — | **0** | 0 | 通过 |

check_x1 的其他输出：chunks 692，synthetic 80.49%，public 19.51%，decontam_hits 0，lcs_flags 0，license_violations 0，messages 为空；sanity 检查（要点子串、arm 同快照、护栏带 T0 干扰、relevant 与干扰不重叠）0 问题。

- multi_hop 从 49 降到 34，减少 15 行：15 行 multi_hop→paraphrase，另有 2 行 lexical→paraphrase。原因分两类。一是定位块、答非所问的块或前提块移出 relevant：s1-d0-04-q3、s1-d2-01-q1、s3-d0-01-q3、s4-d2-t1-04-q1、s4-d2-t1-04-q4、s5-d1-t1-03-q4、s6-mh-15-new。二是冗余证据不算多跳：s3-d0-02-q1、s3-d0-02-q5、s3-d1-01-q1、s5-d0-t1-02-q2、s6-d1-c2-q1、s6-mh-12-new、s7-d1-t0-03-q3、s7-d2-t1-04-q3。lexical→paraphrase 的 2 行（s2-d3-01-q1、s3-d3-01-q3）是 relevant/题面改动后按规则重算或逐题改判的结果。**配额没有跌破下限，不需要补题。**
- **风险**：这次只审了 104 行。没审的 rule-merged 70 行和 consensus 37 行里，很可能也有同样的"定位块进 relevant""冗余证据判成 multi_hop"问题。如果按同一口径复查，multi_hop 余量只有 4，很可能跌破 30。建议先复查剩余的 multi_hop 题（尤其 S3、S4、S6 批次）。万一跌破，按缺口补**跨 ≥2 个 doc_id、两个子问分在不同文档**的新题。缺几题就补几题，再加 3–5 题余量。优先 p1 法条对（令11/13/16、公司法）和 S6-D2，这些批次天然有"备忘 + 法条"两份文档。
- trap+adv 余量只有 1 题。如果以后删掉或改判任何一道 arm 的 trap/adversarial 题，就会跌破 30%。补法：新增 trap 题时，补成 arm 的同快照冲突题（C1–C4 条文对）最稳。

## 9. 系统性问题（供后续修规则/复查用）

1. **ap-merge-v1 的 `repair()` 有缺陷**：要点本身以"。"结尾时，它仍把下一句的前半截接上，例如"…未能获得同等权重。这说明""…成为“事实”本身。尤其当新数据与既有叙事冲突时"。审到的行都已修好。没审的行里还有 5 处同类残片：s5-d1-t1-03-q3、s5-d3-t1-05-q1、s5-d3-t1-05-q2、s7-d3-t1-05-q1、s7-d3-t1-05-q4。这几行我没有动（不在本次 116 行内）。（2026-10-07 后续任务里已按纯文本修好，见 §13。）另外，A 的 40 字截断，在原文含空格或引号时没被补全（如 s2-d3-01-q1 的"原定 15% 的"、s7-d2-t1-04-q3 的"…真实性本"）。
2. **定位块进 relevant** 在 S1、S4 的"那家公司/那版模型"式限定题里很常见。命中口径会把它算成正确召回，建议把这一条写进 PROTOCOL。
3. **kw-v1 的 mh_struct 不识别冗余证据**：几块都能单独作答时，它仍判 multi_hop。规则本身锁定没改，但建议在 PROTOCOL 里给 owner 逐题改判留一条明确口径。
4. **S3 的泛称竞品** 让不带限定语的题在 T1 池里不唯一。我只改了审到的行，建议用同一口径扫一遍 S3 的其余题。
5. 核对提醒的条号（令16 第11条应为第13条），见 §6。

## 10. 来源（provenance）字段

`apply_review_v4.py` 写死了 `source = owner-resolved`（分歧表）/ `owner-audited`（抽样表），`annotators` 里追加 `owner`，`meta.protocol` 写"owner reviewed …"，`gold.final.json` 的 status 写 `owner-reviewed`。**这与事实不符**：这 104 行和 12 条修正是 owner 委托 Ronin 代理人（模型）审的，真实来源应写作「**owner 委托 Ronin 代理人（模型）审核**」。

建议的字段改法（脚本没改，用后处理补丁实现）：

- `source`：`owner-resolved` → `owner-delegated-agent-resolved`，`owner-audited` → `owner-delegated-agent-audited`
- 新增 `source_label_zh`：`owner 委托 Ronin 代理人（模型）审核`
- 新增 `reviewer`：`{kind: model, name: Ronin 代理人, delegated_by: owner, human_row_review: false, date: 2026-10-07}`
- `annotators` 里的 `owner` → `ronin-agent (model, owner-delegated)`
- `meta.protocol` 改写为"由 Ronin 代理人（模型）受 owner 委托审核，非人工逐条"，新增 `meta.review_delegation`
- `gold.final.json` status：`owner-reviewed` → `owner-delegated-model-reviewed`
- `content-fixes-decisions.json` 每条加 `reviewer` 和 `source_label_zh`

补丁脚本是 `ronin-review/patch_provenance.py`：从输入目录复制到一个新的空目录，只改上述字段，并断言 queries 内容没变。演示结果在 `/tmp/x1-ronin/out-patched`：counts 为 rule-merged 70、consensus 37、owner-delegated-agent-resolved 95、owner-delegated-agent-audited 9。如果要长期使用，建议直接在 apply 里加一个 `--reviewer` 参数（需要 owner 同意改脚本）。

## 11. 文件与复现

- `ronin-review/RET-01.3-review-v4-ronin.xlsx`：填好的审核表，说明页第 34 行写有委托声明。
- `ronin-review/REVIEW-NOTES.md`：本文件。
- `ronin-review/check_ronin.py`：照 check_v4.py 跑 check_x1。
- `ronin-review/patch_provenance.py`：来源字段后处理补丁。
- `ronin-review/work/`：逐行记录 `notes.txt`、改动定义 `edits.py`、校验 `build_final.py`、写表 `write_xlsx.py`、内容修正 `cfix.py`、批次原文导出 `dump2.md`。
- 输出：`/tmp/x1-ronin/out`（apply）、`/tmp/x1-ronin/out-patched`（补丁演示）、`/tmp/x1-ronin/check/check-results-ronin.json`。
- 后续任务（§12–§16）的文件见 §16。

```bash
cd /workspace/x1-labeling/v4
env -u DASHSCOPE_API_KEY python3 apply_review_v4.py ../ronin-review/RET-01.3-review-v4-ronin.xlsx --a ../v2/gold-draft-v2.json \
  --b /workspace/cloud-agent-artifacts/bc-08c03b6b-f68a-58e3-9a94-9cf628851e7b/gold-blind-b.json --merged merged-gold-v4.json --out /tmp/x1-ronin/out
cd ../ronin-review
X1_OUT=/workspace/x1-labeling/v2/drafts env -u DASHSCOPE_API_KEY /workspace/venv-fl/bin/python check_ronin.py /tmp/x1-ronin/out
env -u DASHSCOPE_API_KEY python3 patch_provenance.py /tmp/x1-ronin/out /tmp/x1-ronin/out-patched
```

全程没有调用 DashScope 或任何付费 API，没有 commit/push，没有改 v2/v3/v4 原文件和仓库受控文件。

## 12. owner 决定（2026-10-07）

**性质说明**：下面 9 条是 owner（Oriental Ronin 本人）2026-10-07 04:38（上海时间）在聊天中亲自确认的**口径和流程决定**，全部按 Ronin 代理人的建议执行。owner 确认的只是这 9 条。116 行的逐行审核仍由 **Ronin 代理人（模型）** 完成，不是人工逐条审核；最终文件里 `reviewer.kind = model`、`human_row_review = false` 都没有变。

| # | 决定 | 落实情况 |
|---|---|---|
| 1 | 只帮着定位题干限定语（哪家公司/哪一版）的块不算答案证据，不进 relevant | 116 行审核里已逐行套用（§1 口径 1）；写进 PROTOCOL 补丁草稿 |
| 2 | 几块都能各自单独答全的题不算 multi_hop，改判 paraphrase | 已套用（§1 口径 3，8 行逐题改判）；写进 PROTOCOL 补丁草稿 |
| 3 | s6-mh-15-new 维持单跳（paraphrase） | 已体现，没有再改 |
| 4 | s5-d1-t1-03-q4 维持窄读法（只有 summary 案例算 relevant） | 已体现，没有再改 |
| 5 | s6-d2-g3-q1 维持干扰取舍（只留 call#p4） | 已体现，没有再改 |
| 6 | s6-d0-t1-01-q2 维持 memo#p2 为干扰 | 已体现，没有再改 |
| 7 | 采用来源字段补丁（owner-delegated-agent-*） | `final/` 已按 §10 打补丁 |
| 8 | 采用 g2-memo-e2 法条改文“具体实施办法由国务院规定”，同步改语料块 s6-d2-g2-memo#p3@T1 | 见 §13 B；只在 `final/corpus-patch/` 出补丁，没有改 v2 drafts 原文件 |
| 9 | 剩下 107 行（rule-merged 70 + consensus 37）不全审，抽 20 行按同一口径复查 | 见 §14 |

这 9 条以 `meta.owner_decisions` 写进 `final/` 的三个 JSON（`confirmed_by: owner (Oriental Ronin)`，`channel: chat`，`confirmed_at: 2026-10-07T04:38+08:00`，并注明 scope 只是口径/流程决定）。决定 1、2 的 PROTOCOL 补丁草稿是 `ronin-review/PROTOCOL-patch-draft.md`（附 `.diff`，`patch --dry-run` 能干净应用），**没有改 `v4/PROTOCOL.md`**。

## 13. final/ 的生成：来源补丁、语料补丁、文本修正

**A. final/ 目录。** 生成顺序如下：
1. `/tmp/x1-ronin/out`（apply 输出，只读用）
2. `followup_fix.py` → `/tmp/x1-ronin/out-followup`（只改 11 行的 answer_points）
3. `patch_provenance.py`（新增可选参数 OWNER_DECISIONS.json，并只放行 `ronin-review/final` 这一个 x1-labeling 下的目标）→ `ronin-review/final/`

脚本断言 final 的 queries 与 out-followup 完全一致，并断言 11 行修正只动了 answer_points（relevant、distractors、qtype、category、score_role 都不变）。

来源计数：

| source | 行数 |
|---|---|
| owner-delegated-agent-resolved | 95 |
| owner-delegated-agent-audited | 9 |
| rule-merged | 61 |
| rule-merged+agent-ap-fix | 9 |
| consensus | 35 |
| consensus+agent-ap-fix | 2 |

改过的 11 行，每行都带 `agent_fixes`，内容为 `{by: ronin-agent (model), human_row_review: false, kind, field: answer_points, note}`。三个 JSON 的 meta 里都有 `followup_fixes`。

**B. 语料补丁（决定 8）。**
- 先核对现行文本：v2 drafts 里的 `corpus/t1/s6-d2-g2-memo.md` 和 `/tmp/x1-v2/combined` 里的同名文件逐字节相同。其 `## p3` 写的是“…具体办法由国务院另行规定。”，与目标文本不同，所以需要改。
- 把文件复制到 `final/corpus-patch/corpus/t1/s6-d2-g2-memo.md`，只把这一处改成“具体实施办法由国务院规定”。diff 在 `final/corpus-patch/s6-d2-g2-memo.p3.diff`，只有 p3 这一行变化。改后的 p3 与 `content-fixes-decisions.json` 里 g2-memo-e2 的 final_text 逐字相同，该条记录也补了 `corpus_patch` 字段，注明 `applied_to_v2_drafts: false`。
- 对要点的影响：没有任何题的 relevant 或干扰用到 s6-d2-g2-memo#p3@T1；本批只有 s6-d2-g2-q1，它用的是 memo#p1（relevant）和 memo#p2（干扰）。也没有任何要点含“国务院另行规定”或“具体实施办法”。所以要点子串匹配不受影响。check 时用的是打了补丁的整份语料副本 `/tmp/x1-ronin/combined-patched`（与原 combined 只差这一个文件），sanity 检查的要点子串也从这份语料取原文，结果 0 问题。
- v2/drafts 原文件没有改。要把补丁并入正式语料，需要 owner 另行决定（见 §15）。

**C 中的文本修正（11 行，只改 answer_points）：**

| id | 来源 | 类型 | 改动 |
|---|---|---|---|
| s5-d1-t1-03-q3 | rule-merged | repair 残片 | 截掉接上的半句“此类微调虽未改变整体趋势”（下一条要点已有整句） |
| s5-d3-t1-05-q1 | rule-merged | repair 残片 | 截掉“。部分媒体和报告仍沿用旧数据”（下一条要点已有整句） |
| s5-d3-t1-05-q2 | rule-merged | 两句并一条 | 按句拆成两条 |
| s7-d3-t1-05-q1 | rule-merged | 两句并一条 | 按句拆成两条 |
| s7-d3-t1-05-q4 | rule-merged | repair 残片 | 前后两段与第 1、3 条重复，只留中间新增的事实句 |
| s6-d2-g2-q1 | consensus | 抽样：要点漏答 | 补回“旧法（2018修正）的施行日期为二〇〇六年一月一日”（A、B 都有，被复述过滤误删） |
| s2-d0-03-q1 | rule-merged | 抽样：多余要点 | 删掉答满意度的那条 |
| s4-d3-t0-05-q1 | rule-merged | 抽样：多余要点 | 删掉背景句 |
| s7-d0-t0-01-q6 | rule-merged | 抽样：题干复述 | 删掉截断的题干复述 |
| s7-d1-t0-03-q4 | rule-merged | 抽样：题干复述 | 删掉前提复述 |
| s7-d2-t1-04-q2 | rule-merged | 抽样：要点只复述前提 | 换成 data#p3 的判断句 |

用 `rules_v4.qtype_kw` 对这 11 行在修正前后各算一次，qtype 都不变（s5-d3-t1-05-q2 仍是 multi_hop）。

## 14. 抽样复查（20 / 107）

**抽样方法**（`work/followup/sample.py`，结果在 `sample.json`）：
- seed = 20261007。
- 按“来源 × 是否 multi_hop”分 4 层，每层用 `random.Random(seed).sample` 抽，层按名称排序依次抽。
- multi_hop 层多抽，因为 multi_hop 余量只有 4。

| 层 | 总数 N | 抽 n |
|---|---|---|
| rule-merged / 非 MH | 64 | 10 |
| rule-merged / MH | 6 | 3 |
| consensus / 非 MH | 29 | 3 |
| consensus / MH | 8 | 4 |

rule-merged 与 consensus 抽了 13 : 7，大致与 70 : 37 成比例；MH 层抽了 7/14，非 MH 层抽了 13/93。

**做法**：每行打开题面、终稿标注、A/B 标注和同批全部 chunk 原文（`work/followup/dumpS.md`），独立作答后按 §1 的六点口径和 owner 决定 1、2 判断。审核者是 Ronin 代理人（模型），不是人工。

| id | 层 | 判定 | 说明 |
|---|---|---|---|
| p1-mh-05-new | RM/MH | 正确 | o20#p9（2026-01-01 施行）+ o16#p8（人数区间），多跳成立 |
| p1-mh-14-new | RM/MH | 正确 | o11#p17 + o13#p8 @T0 |
| s5-d3-t1-05-q2 | RM/MH | 正确 | 三个例子分在三份材料，多跳成立；要点文本残片属已列 5 处之一，已修，不计为抽样错误 |
| p1-lx-01-new | RM/非MH | 正确 | o11#p13“有效期为2年” |
| s1-d3-01-q1 | RM/非MH | 正确 | 限定语块 report#p2@T1 在干扰里，不在 relevant；需要 T0 判断，判护栏正确 |
| s2-d0-03-q1 | RM/非MH | 小问题（要点） | 多一条答满意度的要点，已删 |
| s4-d0-t0-01-q2 | RM/非MH | 正确 | |
| s4-d1-t0-03-q1 | RM/非MH | 正确 | |
| s4-d3-t0-05-q1 | RM/非MH | 小问题（要点） | 多一条背景句要点，已删 |
| s6-d3-t1-03-q1 | RM/非MH | 正确 | 两块各自答全，判 lexical（非多跳）正确 |
| s7-d0-t0-01-q6 | RM/非MH | 小问题（要点） | 截断的题干复述要点，已删 |
| s7-d1-t0-03-q4 | RM/非MH | 小问题（要点） | 前提复述要点，已删 |
| s7-d2-t1-04-q2 | RM/非MH | 小问题（要点） | 唯一的要点只复述前提，没回答“怎么判断”，已换 |
| s1-d2-01-q5 | C/非MH | 正确 | 判护栏、trap 正确 |
| s4-d0-t0-01-q6 | C/非MH | 正确 | |
| s6-d2-g2-q1 | C/非MH | 小问题（要点） | 第三问的要点被复述过滤误删，已补回 |
| p1-mh-06-new | C/MH | 正确（有待定事项） | capital#p1 + transition#p1 各答一问。内容修正后，s6-d2-g1-memo#p2@T1 一块就能答全两问，A/B 都没提名，没改，见 §15 |
| p1-mh-10-new | C/MH | 正确 | liquidation#p5 + call#p4 |
| p1-mh-11-new | C/MH | 正确 | equity#p1 + call#p5；g3-memo#p3 只覆盖第二问 |
| s5-d2-t0-04-q1 | C/MH | **影响打分（relevant 漏块，偏边界）** | 题问三份材料“各自给出了哪些增长数字”，memo#p3@T0（“综合多份匿名访谈记录…用户活跃度较前一年提升约22%”）也是 memo 里的增长数字，却不在 relevant。也可以把题面读成“三处被引用的来源各一个数字”，那样现标注就是对的，所以这一判定偏边界。A、B 都没提名这块，按“不手填”规则**没改**，见 §15 |

**错误率：**

| 类别 | 抽样发现 | 原始比率 | Wilson 95% 区间 | 按层加权估计（107 行中） | 其余 87 行估计还剩 |
|---|---|---|---|---|---|
| 影响打分（relevant/qtype/category/角色/唯一性） | 1 | 5%（1/20） | 0.9%–23.6% | 约 2 行（1.9%） | 约 1 行 |
| 只是要点/干扰小问题 | 6 | 30%（6/20） | 14.6%–51.9% | 约 42 行（39%） | 约 36 行 |

- 7 道 multi_hop 抽样题按决定 2 都不需要改判，qtype/category 错误 0。
- 如果把 s5-d2-t0-04-q1 按宽读法算作正确，影响打分的错误是 0/20。两种算法都不超过 5%。
- 唯一一处影响打分的错误出在 consensus 行，A、B 漏了同一块，不是合并规则造成的。
- 小问题全部是要点问题：5 处在 rule-merged，1 处在 consensus。成因都是 ap-merge-v1：①合并时把 A 的题干复述/截断要点和 B 的要点一起保留；②复述过滤把真正的答案（s6-d2-g2-q1）当成复述删掉了；③repair() 接残片。干扰项在 20 行里没有发现问题。

## 15. 结论（D）与需要 owner 决定的事项

**结论：建议放行（用于检索打分）。**
- 影响打分的错误原始比率 5%（1/20），没超过 5% 的门槛；按层加权约 1.9%。
- 修正后 check_x1：exit 0；lexical 51 / paraphrase 83 / multi_hop 34；n_arm 168（护栏 43）；trap+adv 52/168 = 30.95%。配额全部达标，与审核后数字相同，抽样修正没有改变任何配额。
- 需要说明的是，20 行样本很小，影响打分错误率的 95% 上界约 24%，所以“≤5%”是点估计，不是保证。
- 要点层面的问题估计还有约 36 行。它们不影响 recall 打分，但如果以后要用 answer_points 评生成答案，应先改 ap-merge-v1 再统一重跑：
  - 删除整句复述题干或前提的要点。
  - 复述过滤只在要点去掉与题干重合的部分后没有新信息时才删。
  - repair() 遇到要点已以句号结尾时不再接下一句。
- 不建议扩大到全审。

**需要 owner 决定的事项（附我的建议）：**
1. **s5-d2-t0-04-q1 漏了一块答案（memo#p3@T0，“用户活跃度较前一年提升约22%”）。** 补它需要手填一个 A、B 都没提名的块，规则不允许我自己补。建议：授权补进 relevant，并加要点“线上二手平台用户活跃度较前一年提升约22%”。这题仍是 multi_hop，配额不变。另一种做法是保持现状，接受“三处来源各一个数字”的读法。改题面也能消除歧义，但那是改 query，要重跑去污染检查，不推荐。
2. **p1 法条多跳题里有 S6 备忘“一块答全”的捷径（例：p1-mh-06-new 与 s6-d2-g1-memo#p2@T1）。** 内容修正后这块备忘一句话就同时写了“新设五年”和“存量逐步调整”。建议：维持现状，并在 PROTOCOL 里写明“p1 法条题以法条原文为证据，S6 备忘只在 S6 题里算证据”。如果 owner 认为备忘也该算，这题按决定 2 要改成 paraphrase，multi_hop 会降到 33（仍 ≥ 30），并需要授权手填。
3. **语料补丁是否并入正式语料**（v2/drafts 的 s6-d2-g2-memo.md 和后续生成的 combined 语料）。建议：并入，补丁只改一句，对要点和配额都没有影响。并入需要 owner 同意改受控文件，我没有改。
4. **PROTOCOL 补丁草稿是否并入 v4/PROTOCOL.md。** 建议：并入，并顺带写上第 2 条的“法条题证据口径”。
5. **ap-merge-v1 是否修规则后重跑要点。** 只在 answer_points 要用于评分时才需要。建议：先放行检索评测，要点问题另开一个小任务处理。

## 16. 后续任务的文件与复现

- `ronin-review/final/`：最终产物。
  - `questions.final.json`、`gold.final.json`、`LABELING-PROVENANCE.json`、`content-fixes-decisions.json`
  - `corpus-patch/`：补丁后的 memo 文件和 diff
  - `followup/`：`owner-decisions.json`、`sample-recheck.json`、`check-results-final.json`、`followup_fix.py` 副本
- `ronin-review/followup_fix.py`：11 行要点修正。
- `ronin-review/patch_provenance.py`：新增 owner_decisions 参数和 final/ 放行。
- `ronin-review/check_ronin.py`：新增 COMBINED_DIR 和 CHECK_OUT_DIR 参数。
- `ronin-review/PROTOCOL-patch-draft.md` 和 `.diff`
- `ronin-review/work/followup/`：`sample.py`、`sample.json`、`dumpS.py`、`dumpS.md`、`sample-recheck.json`、`owner-decisions.json`
- 修改前的本文件备份：`/tmp/x1-ronin/REVIEW-NOTES.before-followup.md`

```bash
cd /workspace/x1-labeling/ronin-review
env -u DASHSCOPE_API_KEY python3 followup_fix.py /tmp/x1-ronin/out /tmp/x1-ronin/out-followup
env -u DASHSCOPE_API_KEY python3 patch_provenance.py /tmp/x1-ronin/out-followup /workspace/x1-labeling/ronin-review/final work/followup/owner-decisions.json
# 语料补丁：final/corpus-patch/（见 §13 B）；check 用打过补丁的整份语料副本
cp -a /tmp/x1-v2/combined /tmp/x1-ronin/combined-patched && cp final/corpus-patch/corpus/t1/s6-d2-g2-memo.md /tmp/x1-ronin/combined-patched/corpus/t1/
X1_OUT=/workspace/x1-labeling/v2/drafts env -u DASHSCOPE_API_KEY /workspace/venv-fl/bin/python check_ronin.py final /tmp/x1-ronin/combined-patched /tmp/x1-ronin/check-final
```

后续任务同样没有调用 DashScope 或任何付费 API，没有 commit/push，没有改 v2/v3/v4 原文件、.scratch、data/exp/x1/ 或仓库受控文件，也没有发任何外部消息。

## 17. 第二轮 owner 决定（2026-10-07 04:48）与执行结果

**性质说明**：owner（Oriental Ronin 本人）2026-10-07 04:48（上海时间）在聊天中确认：§15 列的 5 件事全部按建议执行，并明确授权第 3、4 件修改 v2/drafts 语料和 v4/PROTOCOL.md。owner 确认的是这 5 条决定和一次授权手填；逐行审核（116 行 + 20 行抽样）以及手填、改文件这些具体操作，都由 **Ronin 代理人（模型）** 完成，不是人工逐条审核。这 5 条作为第 10–14 条追加进 `meta.owner_decisions`（`round: 2`，`confirmed_at: 2026-10-07T04:48+08:00`），并同步到 `final/followup/owner-decisions.json`。

| # | 决定 | 结果 |
|---|---|---|
| 1 | 授权手填 s5-d2-t0-04-q1 | 已完成。relevant 加 `s5-d2-t0-04-memo#p3@T0`；要点加“线上二手平台用户活跃度较前一年提升约22%”，已逐字核对，是语料原文的精确子串（clean_text 口径同样匹配）。按 kw-v1 + 决定 2 重判 qtype 仍为 **multi_hop**：覆盖率 0.50，r8 0.00，relevant 跨 3 个 doc_id，三份材料各给不同数字，没有单块答全。category 仍为 trap（S5 规则）。来源改为 `consensus+owner-authorized-agent-handfill`，`source_label_zh` 为“owner 授权、模型手填”，`agent_fixes` 记录了授权人、时间和执行者（model）。 |
| 2 | p1 法条多跳题维持现状 | 已完成。p1-mh-06-new 仍为 multi_hop；口径写进 PROTOCOL：法条题以法条为证据，备忘只在 S6 题里算证据。 |
| 3 | s6-d2-g2-memo p3 补丁并入 v2/drafts | 已完成，见下方“改动的受控外文件”。 |
| 4 | PROTOCOL 补丁（决定 1、2 + 法条题证据口径）并入 v4/PROTOCOL.md | 已完成，三段新增，没有删任何原文。 |
| 5 | 放行检索评测；要点合并规则另开小任务 | 只写了任务卡 `ronin-review/TASK-ap-merge-fix.md`，没开 issue，没修。 |

**改动的受控外文件**（只有这两个；改前改后对 v2/ v3/ v4/ 全部文件做了 sha256 清单比对，其余文件都没变）：

| 文件 | 改前 sha256 | 改后 sha256 |
|---|---|---|
| v2/drafts/corpus/t1/s6-d2-g2-memo.md | e70483acc1557ffecd89fc13b3a5c40fb2f4bc4e091b25ed319f7d1d8d497248 | 89e86ce3de61b87b162bf83a9d43d57e245d36dd75e3d06197e6c614ca41fcf3 |
| v4/PROTOCOL.md | 381f05bef00ba3370c4f5c52e30a52ba6cae8883e94b996a867bf08f4fb7b021 | 79cd22f726dcf5b1995df20d195e3eb92510e708da8de6f40aadaf70cfd140a2 |

原样副本、完整 sha256 和实际 diff 在 `ronin-review/backup-20261007/`（`SHA256.md`、`*.applied.diff`）。回滚方法：把备份复制回原路径。

**final/ 的变化**：
- 只有 s5-d2-t0-04-q1 一行标注变化，其余都是 meta/provenance。
- `content-fixes-decisions.json` 的 g2-memo-e2 改成 `applied_to_v2_drafts: true`，并带前后 sha256。
- 第二轮之前的 final/ 副本在 `/tmp/x1-ronin/final-round1`。
- 脚本 `ronin-review/round2_apply.py` 可重复运行，结果不变。
- 来源计数：

| source | 行数 |
|---|---|
| owner-delegated-agent-resolved | 95 |
| owner-delegated-agent-audited | 9 |
| rule-merged | 61 |
| rule-merged+agent-ap-fix | 9 |
| consensus | 34 |
| consensus+agent-ap-fix | 2 |
| consensus+owner-authorized-agent-handfill | 1 |

**check_x1**（口径同 check_v4.py）：
- 语料用的是更新后的正式 v2 语料，即 v2/drafts 的 corpus + traps，加上仓库 data/exp/x1/corpus 的公开法条（只读复制），组装在 `/tmp/x1-ronin/combined-v2official`。它与原 combined 只差 s6-d2-g2-memo.md 一个文件。
- 结果：
  - exit 0
  - lexical 51 / paraphrase 83 / multi_hop 34
  - n_arm 168，护栏 43
  - trap+adv 52/168 = 30.95%（余量 1 题）
  - chunks 692，synthetic 80.49%，public 19.51%
  - decontam 0，lcs 0，license 0，sanity 0，messages 为空
- 配额都没有跌破。结果存档在 `final/followup/check-results-round2.json`；`check-results-final.json` 是第一轮的结果。

**复现**：
```bash
cd /workspace/x1-labeling/ronin-review
python3 round2_apply.py
D=/tmp/x1-ronin/combined-v2official; mkdir -p $D && cp -a ../v2/drafts/corpus ../v2/drafts/traps $D/ \
  && cp -n /workspace/x1-run/data/exp/x1/corpus/t0/*.md $D/corpus/t0/ && cp -n /workspace/x1-run/data/exp/x1/corpus/t1/*.md $D/corpus/t1/
X1_OUT=/workspace/x1-labeling/v2/drafts env -u DASHSCOPE_API_KEY /workspace/venv-fl/bin/python check_ronin.py final $D /tmp/x1-ronin/check-round2
```

## 18. 下一步：把 final 金标并入仓库或提 PR 需要的步骤（只列步骤，未做）

1. **owner 先定范围和放法**：仓库 `data/exp/x1/` 目前只有公开法条 corpus、config.json、draft-spec.json、SOURCES.md，还没有题目文件和合成语料。需要定：
   - 题目文件名（如 `data/exp/x1/questions.json`）；
   - 合成语料 + traps 是否一起入库（放 `data/exp/x1/corpus/`、`traps/`，还是只入题目、语料另存）；
   - LABELING-PROVENANCE / content-fixes / PROTOCOL 放在哪里。
2. **owner 定分支**：工作副本 `/workspace/x1-run` 当前在 `x1-drafts-run` 分支，且有一个不是本次产生的未跟踪文件 `data/exp/x1/flag-notes.json`。建议从最新主分支新开分支，不要混入这个文件，除非 owner 另有安排。
3. **转换格式**：把 `final/questions.final.json` 转成仓库题目格式（字段集合与 `v2/drafts/questions.json` 相同，check 时已生成同格式文件 `/tmp/x1-ronin/check-round2/questions-ronin.json` 可作参照），去掉内部字段，保留 qtype、category、score_role、conflict_pair、eval_intent。
4. **语料和许可**：复制 v2/drafts 的 corpus/traps（已含 p3 补丁）；SOURCES.md 补合成语料条目（provenance/license = synthetic）；确认 public 比例 ≤40%。
5. **来源说明随附**：一并放入 LABELING-PROVENANCE.json，并在 README/SOURCES 里写明：两份模型标注，加 Ronin 代理人（模型）受 owner 委托审核，owner 在聊天中确认了口径决定和一次手填授权；不是人工逐条审核。
6. **在仓库里离线验证**：用仓库自带的 check_x1（`src/freshlatch/eval/x1_checks.py`）和 `data/exp/x1/config.json` 跑一遍，确认 exit 0、配额达标，结果应与本节数字一致；跑仓库测试（pytest）；不设 DASHSCOPE_API_KEY；不改 PRODUCTION_RETRIEVAL_MODE。
7. **提交**：需要 owner 明确同意后，才能在新分支 commit、push，并开 PR（PR 描述同样写明是模型审核）。这些是对外可见的操作，本次都没做。
8. **合并前**：owner 在 PR 上过目，CI 通过后再合并；合并后的检索评测按放行决定进行。answer_points 的修正按 TASK-ap-merge-fix.md 另行处理。


## 19. 第三轮（2026-10-07，owner 04:54 同意；模型产出，未经人工复核）

只做了第 4、6 项核查和第 5 项起草；第 7 项（开 PR）没做；v2/v3/v4、final/、仓库文件都没改。

- 第 4 项 `item4-frontmatter-check.md`：frontmatter 在切块前被 ingest.py 的 META_RE 剥掉，所有臂和 check_x1 共用 load_corpus/chunk.text。离线扫描 692 个 chunk，frontmatter 特征命中为 0；BM25 词表里 frontmatter 键的 df 为 0。结论：无泄漏，无需修复。
- 第 6 项 `SOURCES-revision-check.md`、`SOURCES.md.patch-draft`：
  - 公司法 2023 仍有效，之后没有新修正。
  - 令11、令13、令16、令20 官网未见修改或废止公告（属间接证据）。
  - 国令784 有效。
  - 发现语料问题 s6-d2-g2-q1：memo#p1 写旧法（2018 修正）施行日为 2006-01-01，flk 记录为 2018-10-26。处理方案 A/B/C 待 owner 定。
- 第 5 项 `TRAP-DEFINITIONS-draft.md`：
  - 推荐采用 CONTEXT 三类（快照取代 / 同快照冲突陈述 / 元陈述），按证据结构判定。
  - 试算 arm trap+adv 为 15/168 = 8.93%，比 30% 缺 36 题。
  - 沿用 category-rule-v1 为 52/168。
  - 方案丙为 26/168。
  - s6-d1-c4-q1 改判 hard 时，比例分别为 51/168（rule-v1）和 14/168（推荐版）。
  - 待 owner 选 D1–D5。
