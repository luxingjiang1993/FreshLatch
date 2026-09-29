# I1：失败三分法与 HumanLatch 语料设计评估

> **决议会话**: grill-with-docs · Phase I1 Failure taxonomy + HumanLatch corpus（2026-09-29）  
> **决议日期**: 2026-09-29（两轮 grilling；Round 1 混选 / Round 2 全认；共享理解已确认）  
> **决议落点**: 本评估、ADR-0028、`CONTEXT.md`（评测指针）、`docs/grill-prep.md` §2e、roadmap Phase I1  
> **上游**: roadmap v3.1 Phase I1；ADR-0006（HumanLatch）；ADR-0026（冒烟层）；ADR-0027（V1 包结论）；W4 假绿对照证据

---

## 1. 问题 + 前置约束

冲 mid 需要能指着样本讲清「闸错在哪一层」。仓库已有 HumanLatch 与假绿对照，但**没有**失败三分法操作定义、也没有标题为漏拦/误拦的 I1 corpus。

| 前置 | 来源 | 锁死作用 |
|------|------|----------|
| I1 In：三分法 + ≥3 漏拦/误拦；Exit：讲清层级 + ≥1 可复跑 | roadmap | 本评估不砍 Exit |
| I1 Out：新功能大项；编造无复盘样本 | roadmap | 禁改生产大功能、禁假样本 |
| HumanLatch action 仅 `discard`\|`renew` | ADR-0006 / CONTEXT | 不扩第三动词 |
| 包结论可发/需补丁/勿发为聚合层 | ADR-0027 | 三分法 ≠ 第四套生产 status |
| 演示可过 ≠ 测量可信；词表须上下文无关 | Anthropic 纪律 | 三分法 = 评测标签，不进产品词表正文 |
| 本地 V1 Exit 硬挡 I1 落样本（I1-Q1=c） | grill Round 1 | 远程 CLOSED ≠ Exit |
| ① bare-pytest 卫生先关 | roadmap 本期序 | 写码/落样本叠挡 |

验收层：**答辩·冒烟语料**（非统计结论）。

---

## 2. 候选路线（按决策维）

| 维度 | 候选（含被否） |
|------|----------------|
| V1→I1 依赖 | (a) 远程 CLOSED 即可；(b) 本地 DoD 勾即可；(c) 本地 V1 ACCEPTANCE 齐才落样本 |
| 三分法边界 | (a) 仅检索；(b) 全链三桶；(c) 只口述不映射 |
| 「接门禁」深度 | (a) 文档标签 only；(b) eval/轨迹挂标、生产枚举不动；(c) 改 rule_gate/disposition |
| 样本来源 | (a) 只重标 W4；(b) 只新跑 McK；(c) 重标 ≥3 + ≥1 新可复跑 |
| corpus 形态 | (a) 仅 md 页；(b) 仅 JSONL；(c) 页+JSONL+索引 |
| 漏拦/误拦 | (a) 相对金标/人终审；(b) 只主张级；(c) (a)+强制绑三分法桶 |
| JSONL 位置 | (a) `docs/evidence/i1/events.jsonl`；(b) `data/i1_failure_events/`；(c) 双表 |
| 可复跑 | (a) 必须重跑模型；(b) 只对轨迹；(c) 优先重跑；replay_only 不得作唯一 Exit 金样 |
| ADR | (a) 开短 ADR；(b) 只评估；(c) 细则灌 CONTEXT 正文 |

---

## 3. 逐路线评估（摘要）

| 维度 | 拍板 | 被否理由 |
|------|------|----------|
| V1 依赖 | **(c)** | (a)(b) 把远程关单当 Exit，纸面与可演示脱节 |
| 三分法 | **(b)** | (a) 盖不住闸/人审；(c) 交不出可复盘 corpus |
| 接门禁 | **(b)** | (c) 新功能大项 + 第四套状态词；(a) 过弱，轨迹无法机读挂标 |
| 样本 | **(c)** | 纯重标缺现场复跑；纯新跑浪费已有假绿锚 |
| 形态 | **(c)=a+b** | 单页不便机读；单 JSONL 不便面试指读 |
| 漏/误 | **(c)** | 不绑桶则 Exit「讲清层」落空 |
| JSONL 路径 | **(a)** | I1 非高通量账；跟 evidence 页 |
| 可复跑 | **(c)** | 对齐 I0；禁止唯一金样靠看日志装复跑 |
| ADR | **(a)** | 难反转+反直觉（有标签不改生产词表）+真取舍 |

**Anthropic 清单命中：**
- 原若「三分法进 CONTEXT 当产品词」→ #4 否决（生产判不出）→ 改为评测指针 + ADR/评估细则。  
- 原若「单次轨迹即证明闸可靠」→ #1/#2 否决 → 文首冒烟声明 + 可复跑金样显式 decoding。  
- Exit 桶定义本轮预锁（#5），禁事后改桶凑样本。

**被否原推荐（写透）：** Round 1 曾荐 V1 依赖 (a)；用户改 (c)。评估采纳用户拍板：(a) 在「远程已关、本地 DoD 空」时会让 I1 落在未证明发前闭环上，冲 mid 叙事穿帮。

---

## 4. 拍板 + 子决策

1. **序**：① bare-pytest 卫生 Exit → `docs/evidence/v1/ACCEPTANCE.md` 齐 → I1 to-spec / 落 corpus。  
2. **三分法（全链）**：找不到 / 找错 / 没用上；层映射见 ADR-0028。  
3. **标签面**：只挂 eval/轨迹与 I1 corpus；生产 Gate、disposition、HumanLatch 动词不改。  
4. **漏拦/误拦**：相对金标或人终审；每条必绑一桶。  
5. **产物**：`docs/evidence/i1/<sample>.md` + `docs/evidence/i1/events.jsonl` + 短索引。  
6. **样本**：重标 W4/假绿+轨迹 ≥3；V1 顾问垂直/McK ≥1 真可复跑（`runnable=true`）。  
7. **层标签**：I1 文档文首声明答辩/冒烟；不报方差。  
8. **词表**：细则不进 CONTEXT 产品正文；仅评测区指针。

---

## 5. 工程手段总登记册

| 手段 | 原理 | 优势 | 代价 | 参考先例 | 本期处置 |
|------|------|------|------|----------|----------|
| 全链三分法桶 | 面试分层口述 | 对齐 Exit | 标注成本 | roadmap I1 In | **实装**（标签+文档） |
| eval/轨迹挂标 | 机读复盘 | 不污染生产枚举 | 须约定字段 | I1-Q3 | **实装**（to-spec） |
| evidence 页+JSONL | 人读+机读 | 双形态 | 双写同步 | patch_events 思路 | **实装** |
| 重标 W4 假绿 | 复用已有锚 | 快凑 ≥3 | 标签可能偏检索史 | `docs/evidence/w4/` | **实装** |
| McK/V1 ≥1 可复跑 | 现场答辩 | 真 Exit | 依赖本地 V1 Exit+可能 Key | ADR-0027 垂直 | **触发**（V1 ACCEPTANCE 后） |
| V1 ACCEPTANCE.md | 本地 Exit 证明 | 防远程假齐 | 补纸面工时 | I0 ACCEPTANCE | **实装**（挡 I1 落盘） |
| bare-pytest 卫生 | 裸/模块入口一致 | 减 collection 坑 | 小改导入或 pythonpath | 本期① | **实装**（先于落样本） |
| 生产枚举扩三分法 | 运行时自动分层 | — | 第四套状态、Out | — | **弃** |
| 编造无轨迹样本 | 凑数 | — | Out 明文禁 | — | **弃** |
| 三分法灌 CONTEXT 正文 | 词表统一错觉 | — | 生产判不出 | Anthropic #4 | **弃** |
| replay_only 作唯一金样 | 无 Key 省事 | — | 假复跑 | I0 纪律 | **弃** |

---

## 6. 面试讲法

**Q: 你们怎么证明 Gate 不是假绿仪器？**  
A: I0 讲 retrieve 默认臂；I1 讲失败分层。我指着 ≥3 条漏拦/误拦复盘，每条有「漏|误 × 找不到|找错|没用上」，至少一条能按文档命令复跑。这是冒烟答辩层，不是统计证明。

**Q: 为什么不把「找不到」做成生产 status？**  
A: 生产里机器稳定判不出这三桶；硬塞会变成第四套状态词，和 disposition / fresh|stale|unknown|void 缠死。标签只挂评测与轨迹。

**Q: HumanLatch 和失败三分法什么关系？**  
A: 「没用上」桶可落到人审未收口或续命失败；人审动词仍只有 discard/renew。corpus 描述人审动作，不改封闭集。

**Q: V1 远程票都关了，为什么还不让写 I1 样本？**  
A: 远程 CLOSED ≠ 本地 Exit。我们要求 `docs/evidence/v1/ACCEPTANCE.md`（映射抽检、patch_events 一行、bm25 默认、人审走通）齐了再落 I1 corpus，避免 mid 叙事建在空勾上。
