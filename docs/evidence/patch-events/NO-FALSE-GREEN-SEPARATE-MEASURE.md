# 「不能保持绿」另开测量 · 边界说明

> **路径写死（#446）**:本页是唯一边界载体。  
> **Parent**:[#436](https://github.com/luxingjiang1993/FreshLatch/issues/436) · 本票:[#446](https://github.com/luxingjiang1993/FreshLatch/issues/446)  
> **日期**:2026-10-08 · **Trust**:Gate（人）· **本页只立边界，不跑数、不填表、不改缝**  
> **关联**:路线 B 协议 `PREREG-B.md` · ADR-0034 · 规格 `docs/spec/24-patch-events-路线B冲甲.md` · 评估 `docs/research/patch_events-路线B冲甲可识别选取设计评估.md`

## 1. 明文：产品机制句 ≠ 结果甲

**产品机制句**（产品北星 / 词表导语，见 `CONTEXT.md` 与产品页）逐字：

> 过期、冲突、无 T1 原文支持的主张不得保持绿灯，人决定作废或续命。

这句话描述的是**主张复验产品机制**：已签发主张在 T1 上是否仍可复验；绿/红/黄与人闩（作废/续命）。它**不是**论文实验的成立判据，也**不是**投稿分界。

**结果甲**（路线 B / 旧 `DECISION-LOG` 投稿映射）定义为：

> 第一、第二、第三主比较（T 对 C、T 对 B1、T 对 B2）在预注册意义下均成立——固定放行率下的 false-accept rate 配对差点估计 > 0 且 95% bootstrap 区间下界 > 0。

两条句子**禁止互替、禁止互证**：

| 禁止写法 | 为何违例 |
|---|---|
| 「产品不得保持绿」已实现 → 结果甲成立 / 可冲甲 | 机制句无 false-accept 主比较数字 |
| 结果甲成立 → 产品已证明「过期/冲突/无 T1 不得保持绿」 | 甲测的是 attested edit 误放相对臂差，不是主张绿灯复验闭环 |
| 把产品机制句塞进 `RESULT` / `RESULT-B` 主表当一行指标 | 主表只抄 `compare_primary` 的三条 false-accept |

本页把产品机制句标为**另轨叙事**。要测量它，必须另开测量图 / 另写预登记；不得塞入 false-accept 主表。

## 2. 与路线 B 冲甲主表的防火墙

路线 B 冲甲主证据链（激活后）唯一合法主表路径：

1. `compare_primary`（选取 **R**）产出三条 false-accept 与固定 k；  
2. 抄入 `RESULT-B.md` 成立格（不得手填）；  
3. 甲/乙/丙分界继承 `DECISION-LOG.md`，不放宽。

本页相对该主表的防火墙：

| 本页允许 | 本页禁止 |
|---|---|
| 写清「产品机制句 ≠ 结果甲」 | 改 `PREREG-B.md` 选取 / 成立定义 / 门闩 |
| 声明「不能保持绿」须另测 | 把本主题指标并进主表三条 false-accept |
| 指出真跑须真人另开测量图 | 用本页任何句子填 `RESULT-B` / 旧 `RESULT` 成立格 |
| 与 #444（盲审附加预注册）、#445（检索金标另轨）同级并行 | 挡硬门 #437–#438；削弱 B1/B2；夹具填甲 |
| — | 金标 / 评委 / 产品绿灯读数进 `score` |

**主表只认 false-accept。**「不能保持绿」无论 demo / 冒烟 / 统计哪一层，读数都**不进**冲甲主比较，也不改乙/丙收口定义。

## 3. 不改 RESULT-B / 旧 RESULT 主比较

本票零 diff 下列文件的主比较与成立格（含「未填」格子）：

- `docs/evidence/patch-events/RESULT.md`（旧 n=30；不得当冲甲主证据）  
- `docs/evidence/patch-events/RESULT-B.md`（若尚无壳，本票也不建壳、不预填）  
- `docs/evidence/patch-events/PREREG.md` 判据正文  
- `docs/evidence/patch-events/PREREG-B.md` 选取 / 成立 / 门闩正文  

不改 `compare_primary`（及任何等价缝）实现或测试。硬门仍归 [#437](https://github.com/luxingjiang1993/FreshLatch/issues/437)。

## 4. 不复活路线 A（#419–#430）

路线 A（继续旧 `PREREG.md`→n=100、同集差锁 0）整链已废（ADR-0034 · #432）。本页：

- **禁止**重开或续写 #419–#430；  
- **禁止**回写旧 `PREREG.md` 凑甲；  
- **禁止**把「不能保持绿另测」写成路线 A 的替身或补丁；  
- 旧 n=30 数字唯一合法用途仍是：说明旧选取下 T/B1/B2 结构锁零（动机附录），不得进新主表成立格。

## 5. 另图是否需要真人再开地图（wayfinder）

**需要，若目标是真跑读数。**

| 本票（#446）已交付 | 本票不交付 |
|---|---|
| 边界说明页（本文件） | 测量图 Destination / In / Out / Exit |
| 「机制句 ≠ 甲」与主表防火墙 | 通过线 / 作废线 / decoding 预登记 |
| 另轨指针 | 跑数、报告、成立叙事 |

裁定（Gate 人可覆核）：

1. **只立边界**：合并本页即满足 #446 Acceptance；**不**自动开测量图。  
2. **若要测量「过期/冲突/无 T1 不得保持绿」**：必须由**真人**另开 wayfinder 地图（建议标题含「不能保持绿 · 测量」），在图内先锁通过线与层级（demo / 冒烟 / 统计），再开施工票；预登记页另写，**不得**回改 `PREREG-B` 主比较。  
3. **显式排除「永远不测」**：本裁定是「不塞入 false-accept 主表 / 本票不跑」，不是作废产品机制句或禁止未来测量图。  
4. 与既有「另开测量图」先例同构：K3 / K6-4 / Auditor 压绿——边界或模板已锁 ≠ 本图执行（见 `docs/research/Auditor维度闸压住该活的绿后是否另开实验设计评估.md`）。

## 6. 可引用句（本页范围）

允许对外 / 对内引用：

> 「不能保持绿」（过期/冲突/无 T1 不得保持绿灯）是产品机制句，与路线 B 结果甲（三条 false-accept 主比较）不是同一主张；另开测量，不塞入 false-accept 主表。边界见 `docs/evidence/patch-events/NO-FALSE-GREEN-SEPARATE-MEASURE.md`（#446）。

禁止升格为：

- 「产品机制已由冲甲主表证明」；  
- 「本页已授权正式跑数 / 已锁通过线」；  
- 「路线 A 复活」或「旧 RESULT 成立」。

## 7. Out / Do-not-touch（本票）

- `src/` 业务代码；`compare_primary`  
- 旧/新 RESULT 成立格；`PREREG` / `PREREG-B` 判据正文  
- 路线 A 工单；正式生成；激活 `PREREG-B`  
- 五处冻表面；`PRODUCTION_RETRIEVAL_MODE`；主张复验金标文件  
- 平行轨 #434 成立定义；#444 / #445 正文（并行另票）
