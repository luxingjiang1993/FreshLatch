# checksum 链激活契约(留位登记,本期不动代码)

- **状态**:契约登记(2026-09-21,#23 实装后盘点;判定人拍板「只登记不动手」)
- **相关**:ADR-0003(存储/检索)、ADR-0006 §4(续命生效链)、`docs/research/HumanLatch闭环设计评估.md` §4/§5、规格 §1.3 / §2.5
- **触发**:续命闭环(#23)落地时把 `checksum_fn` 做成注入点,顺带盘出本链真实状态与激活陷阱。

## 1. 一句话现状

**校验逻辑真实存在且单测通过,但生产上 checksum 链一次都不会触发** —— 不是因为一个开关没打开,而是三层空位叠在一起,最深那层与 `checksum_fn` 是否为 `None` 完全无关。

## 2. 三层空位(实测,非推测)

| 层 | 位置 | 实况 |
|---|---|---|
| **数据层** | `data/corpus/*/*.md` frontmatter `checksum:` | 28 个语料文件**字段全在、值全空**;灌库后 `documents` 28 行 / `chunks` 84 行,非空 checksum = **0** |
| **读取层** | `ingest.py:35`、`runner.py:247` | `checksum = meta.get("checksum", "")`;`_checksum_fn` 直接 `return None`;store 无「按 `(doc_id, as_of)` 取当前 checksum」读口 |
| **构造层(最深)** | `runner.py:179-187` `_gate_decision` | **根本不构造 `validity_basis`** → `rule_gate.py:174` 的 `if decision.validity_basis:` 恒假 → **不变量 3 的「checksum 对不上不得 fresh」那半边结构性空转** |

第三层是关键:**把 `checksum_fn` 接成真函数,Agent 的 fresh 路径也照样一次不触发**。当前唯一会构造 `validity_basis` 的调用点是续命(`human_latch.py:142`)。

## 3. 核心陷阱:套套逻辑(tautology)

激活时第一个要躲的坑,**不在代码量在判断力**:

- ❌ `checksum_fn` 若读库里的 `chunks.checksum` —— 那正是 `basis["checksum"]` 的来源(`human_latch.py:142`)。同一个值比它自己 → `claimed == actual` 恒成立 → 闸永不触发,**「激活」等于没激活**,还会留下一条永远绿的假不变量。
- ✅ `checksum_fn` 必须**读当前文档现算**(从 `data/corpus/{as_of}/{doc_id}.md` 算 sha256),与「入库时记录的指纹」比对。

这不是本文新推的设计,`HumanLatch闭环设计评估.md:219` 原文即「读当前文档算 checksum 对比」、`:264`「后端闸**再算一遍** checksum,对不上直接拒」。#23 的实装形状恰好扛得住这个区分:`basis` 取 `chunk.checksum`(入库时记录的指纹),`checksum_fn` 是独立注入函数(`human_latch.py:147`、`pipeline.py:121`)—— 接错接对这个注入点,是将来唯一的踩坑面。

## 4. 第三个洞:`validity_basis` 只写不读

全仓 grep 结论:`claim.validity_basis` 只有三处碰 —— 续命写(`human_latch.py:154`)、闸在**当次调用内**读(`rule_gate.py:174`)、UI 展示(`app.py:74`)。**没有任何代码跨时间重读它。**

推论:checksum 即使激活,能抓到的只有「入库 → 续命之间语料文件被改」这种**同调用内竞态**。本期语料是静态合成快照,该场景实际不发生。

真正有价值的那半 —— **跨轮腐烂**(人对着 T1-v2 续命,后来 T1 变 v3,绿灯该降级)—— 抓不到,因为没人去比。

## 5. 激活步骤(档 2:renew 半边,可执行但价值趋零)

1. `parse_document` 从内容算 sha256 填 `checksum`(优于手填 frontmatter:自洽、不怕填错);
2. 实现现算版 `checksum_fn(doc_id, as_of)` → 读语料文件算 sha256;
3. 接线:`ui/app.py::_latch()` 与 `runner._checksum_fn` 都换真实现;
4. 重灌语料 + 单测:篡改临时语料文件 → 续命打回 `CHECKSUM_MISMATCH`。

**成本半天;但档 2 单独做抓不到实际发生的场景,演示不出价值,还要背一次重灌。故不单做。**

## 6. 档 3:让闸有牙齿(两个真取舍,届时走决议单)

| # | 取舍 | 难点 |
|---|---|---|
| 3a | fresh 路径补构造 `validity_basis` | Lead 常引多个跨 doc 的 `t1_evidence_ids`,而 `validity_basis` 是**单 doc 结构** —— 取主证据(脆弱)还是改 list(动 schema + 动闸)? |
| 3b | 跨轮重检 | 谁比、何时比(新一轮 reverify 开头 / UI 渲染时)、不符降级到哪。**是改产品行为**,不是补校验 |

档 3 是价值全部所在,但动产品行为 → 判据须 pre-registration(Anthropic 纪律 #5),且不与当前关键路径(#31)抢窗口。

## 7. 工程手段总登记册

| 手段 | 原理 | 优势 | 代价 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| checksum 比对逻辑 | 记录指纹 vs 现算指纹 | 机械、零模型意见 | 三层空位未填前恒不触发 | ADR-0003 / 规格 §1.3 | **留位**(已实装,未启用) |
| `checksum_fn` 注入点 | 闸纯函数零 I/O,校验源由调用方给 | 可测、可换真/假实现 | 接错来源 = 套套逻辑 | ADR-0001(闸零 I/O) | **承载**(#23 已留) |
| `validity_basis` 写回 | 绿灯依据落档可溯 | 跨轮可检的前提 | 当前只写不读,无牙齿 | ADR-0006 §4 | **留位** |
| 跨轮腐烂检测 | basis.checksum vs 现算,不符降级 | 兑现 validity_basis 的产品承诺 | 改产品行为,须决议 + pre-registration | 无 | **弃**(本期),转档 3 决议 |
| 语料 frontmatter 手填 checksum | 人工维护指纹 | 直观 | 易错、与内容脱钩 | — | **弃**(改 ingest 现算) |

## 8. 面试讲法(grilling 预案)

**Q:你说「checksum 对不上不得 fresh/续命」,现在真的在拦吗?**
A:不在拦,而且我主动把它写进了留档而不是含糊过去。三层空位:语料 checksum 全空、store 无读口、最深一层是 runner 的 fresh 路径根本不构造 `validity_basis`,闸那行 `if decision.validity_basis:` 恒假。所以「不得 fresh」那半边今天结构性空转,跟开关没关系。

**Q:那把开关打开不就行了?**
A:打开之前有个陷阱要先判:`checksum_fn` 读什么。读库列就是拿 `basis` 的来源比它自己,恒等,闸永不触发 —— 那会留下一条永远绿的假不变量,比没有更糟。必须读当前文档现算。这点原评估文档就写了「后端闸再算一遍」,我是盘点时把它从一句话落成硬约束。

**Q:那这链现在有价值吗?**
A:续命那半激活后只能抓「入库到续命之间文件被改」,本期静态合成语料下不发生。真正的价值在跨轮腐烂 —— 人对 T1-v2 续命、T1 变 v3、绿灯该降级 —— 但 `validity_basis` 现在只写不读,没牙齿。要兑现得动产品行为,所以我建议走决议单而不是在实装单里顺手做掉。

**Q:为什么不在 #23 里顺手做完?**
A:#23 的验收条款是「校验项按规格 §1.3 落齐」,我落齐了并且负例单测真的在打回。跨轮检测是新产品行为,判据得 pre-registration,塞进实装单等于绕过决议纪律。判定人拍板本期只登记契约。

## 9. 本期处置

**留位,不动代码。** 本契约的目的是:将来任何人(包括我自己)来激活这条链时,先读到 §3 的套套逻辑陷阱和 §4 的只写不读,再决定做档 2 还是档 3。
