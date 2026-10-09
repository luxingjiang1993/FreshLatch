# patch_events 路线 B · 冲甲可识别（to-spec）

> 来源：决议 [#432](https://github.com/luxingjiang1993/FreshLatch/issues/432) · 地图 [#431](https://github.com/luxingjiang1993/FreshLatch/issues/431) · ADR-0034 · `/to-spec`  
> 增量决议：[#466](https://github.com/luxingjiang1993/FreshLatch/issues/466) · 地图 [#465](https://github.com/luxingjiang1993/FreshLatch/issues/465) · ADR-0035  
> 评估：`docs/research/patch_events-路线B冲甲可识别选取设计评估.md` · `docs/research/patch_events-路线B-T与B1可执行差与抬k设计评估.md`  
> 协议页：`docs/evidence/patch-events/PREREG-B.md`（协议已锁 · **激活前修订已记** · **正式主跑未激活**）  
> 基线：`main` `a5e424c`（#416）；旧 `PREREG.md` + n=30 `RESULT.md` 不得当冲甲主证据  
> **测试主缝（预锁）**：`compare_primary` 的固定 k 选取边界（R = 各臂自然放行集内取 k）  
> **下一工程主缝（#466 后）**：T/B1 同 after 再分叉 + 门闩复测夹具（见票序 1b）  
> 语言：中文。技术词保留 English 原词。  
> 本页不是论文，不激活正式主跑，不发模型，不回写旧 `PREREG.md`，不填旧 `RESULT.md` 成立格。

## Problem Statement

冲甲要求 T-C、T-B1、T-B2 在预注册意义下均可成立，但旧选取在 `score` 全空时让 T/B1/B2 固定 k 同集，差锁 0，甲结构不可识别。路线 A（只加 n）已废。路线 B 已拍板新预注册与选取 R，但：

1. `compare_primary` 仍走旧空分 top-k，纪律目标（可识别性）未进代码缝；  
2. `PREREG-B.md` 需完整继承样本/配额/算子/评委等条款且保持未激活；  
3. 仓外试分离门闩未过——不得正式生成、不得激活主跑；  
4. 后续名单、生成、抄表、消融、抽检、人轨必须按固定依赖序拆票，且不得复活 A、不得 HARKing。

## Solution

本规格把路线 B 收成：协议页继承齐备（已落）+ 一条可测主缝（R 选取）+ 固定票序。主缝先于正式生成。门闩未过时只允许夹具/仓外探针，不允许激活批注与正式主表。

求验目标（甲）不保证。规划预留乙/丙。禁止把「设计冲甲」写成「将得到甲」。

## User Stories

1. As a 统计读者, I want 固定 k 从各臂自然放行集取样, so that T/B1/B2 在策略不同时固定 k 集合可以不同。
2. As a 统计读者, I want k 仍等于 T 的自然放行数, so that 覆盖率对齐语义不丢。
3. As a 统计读者, I want m≥k 时按 claim_id 升序取 k, so that 选取可复现且不依赖 score。
4. As a 统计读者, I want m<k 时该臂固定 k 误放率为无定义, so that 不会用假分母凑数。
5. As a 统计读者, I want 旧「空分 + 全体 claim_id top-k」不再作为主比较选取, so that 差锁 0 的旧病不再适用。
6. As a 复现者, I want 夹具能构造三臂不同自然放行集并看到不同固定 k 集合, so that 可识别性可测。
7. As a 复现者, I want 用旧选取复现差恒 0 的夹具只作为负例/对照文档, so that 新主路径不会再走那条路。
8. As a 预注册守门人, I want PREREG-B 在未激活时拒绝正式生成进主表, so that 门闩不被绕过。
9. As a 预注册守门人, I want k 下限 10 写进协议与缝的守卫, so that k=3 级不能称冲甲主张。
10. As a 预注册守门人, I want 止损句可被结果页与口径引用, so that 点估计≤0 时不得称甲。
11. As a 工程代理人, I want 第一张实现票只改选取缝, so that 不夹带生成或抄表。
12. As a 工程代理人, I want 样本名单票在 R 缝之后, so that n=100 名单不依赖旧同集假设。
13. As a 密钥守门人, I want 生成票默认不发模型, so that 未授权会话不能烧配额。
14. As a 密钥守门人, I want 正式生成产物走新路径 formal-generations-b.jsonl, so that 不污染旧 120 行冻结链。
15. As a 抄表守门人, I want RESULT-B 只抄 compare_primary 输出, so that 成立格不能手填。
16. As a 抄表守门人, I want 旧 RESULT.md 成立格不被路线 B 回写, so that 旧链保持作废附录身份。
17. As a 消融读者, I want 次要指标与消融不参与成立, so that 主比较不被旁路改判。
18. As a 抽检读者, I want 抽检入口标签由人写, so that 代理人不编用户标签。
19. As a 人轨维护者, I want 盲审附加预注册 / 检索金标 / 「不能保持绿」可并行另票, so that 不堵主比较缝。
20. As a 平行轨守门人, I want #434 平行探针零 diff 本规格主缝语义以外的旁路, so that 平行轨不得改本 compare_primary 追甲叙事时仍可自建 compare_alt_*。
21. As an 面试讲解者, I want 规格写明废 A 与反 HARKing, so that 见 0 改选取不被说成改判据。
22. As a 文档守门人, I want 五处冻表面在甲未成立前不动, so that 对外不假绿。

## Implementation Decisions

### 主缝

**主缝**：`compare_primary`（或同模块内由其唯一调用的选取函数）按 `PREREG-B.md` 的 R 规则选取固定 k 集合，再算三条主比较。

- 正式入口（路线 B 回放/抄表）必须走 R。  
- 允许保留只读的 legacy 选取函数供负例测试「旧病差锁 0」，但**禁止**被路线 B 主表路径调用。  
- bootstrap 重抽样后的固定 k 集合也必须按 R 重算（在重抽样后的自然放行集上取 k）。  
- `coverage_c` 不再参与路线 B 主选取。

### 缺口与关掉方式

| 缺口 | 决定 | 验收时要看见 |
|---|---|---|
| 1. 选取仍是空分 top-k | 主路径改为 R | 夹具：T/B1/B2 自然放行集不同 → 固定 k 集合可以不同；主比较不因同集结构锁死差=0 |
| 2. 旧病仍可被主路径触发 | 主路径拒绝旧选取；负例测试可调用 legacy | 再现「空分+全体 claim_id 取 k」时，要么主路径不再适用该选取，要么显式拒绝将其用于路线 B |
| 3. PREREG-B 继承未齐 | `/to-spec` 已抄入样本/配额/算子/评委等 | `PREREG-B.md` 无「待抄入」占位；文首仍未激活 |
| 4. 门闩未过（#438） | 激活批注空；生成票默认禁发；须按 #466 复测协议重跑 | 未激活时正式生成入口不得写入主表/RESULT-B 成立格 |
| 5. 结果表壳 | 新建 `RESULT-B.md` 空壳（抄表票） | 旧 `RESULT.md` 零回写成立格 |
| 6. 产物路径 | `formal-generations-b.jsonl` + `data/exp/patch-events-b/` | 不追加旧 formal-generations 冻结行 |
| 7. T/B1 可执行同构（#438 根因） | 同 after 再分叉（ADR-0035）；抬 k=降正确假阴性 | 同 after 上 T/B1 自然放行集可不同；B1 核验不过仍 reject；不放松 T hard reject |

### 票序（依赖方向固定）

1. **硬门**：`compare_primary` R 选取缝（本规格主缝；#437）  
1b. **下一张工程票（#466 后第一张）**：T/B1 同 after 再分叉 + 门闩复测夹具与报告格式（Acceptance：同 after 或同候选上 T/B1 自然放行集可不同；复测报告与 PREREG-B R 一致；默认不发模型；不激活）  
1c. **抬 k（可同波次第二张）**：正确样生成质量 / 假阴性路径（禁止松闸凑 k）  
2. **仓外试分离报告复测**（机制后必重跑；不进主表；过门前不可激活）  
3. 样本名单/构造（n=100，按 PREREG-B）  
4. 生成入口（默认不发；仅人授；须门闩过且激活后才可进主表）  
5. 回放 + 抄表（只抄函数；`RESULT-B.md`）  
6. 次要指标/消融（不参与成立）  
7. 抽检入口（标签人写）  
8. 人轨另票（可并行）：盲审附加预注册；检索全库金标；「不能保持绿」另图  

### 与平行轨（#434）防火墙

本规格拥有主 `compare_primary` R 语义。平行轨只许 `compare_alt_*` / `patch-events-alt/`，不得改本缝成立定义，不得用探针数字填 `RESULT-B` 成立格。

## Testing Decisions

好的测试只看缝外面：给定四臂记录（含 `decision` 与 `construction_gold`），`compare_primary` 返回的固定 k 集合与三条比较符合 R。

必须覆盖：

- 臂间自然放行集不同 → 固定 k 集合可以不同；  
- 旧空分全体 claim_id 选取不再用于主路径（或调用即拒绝用于 route B）；  
- m<k → 该臂固定 k 误放率无定义；  
- 不读密钥、不发网络。

本规格会话不落地测试代码；留给硬门实现票（TDD）。

## Out of Scope

- 复活路线 A（#419–#430）  
- 回写旧 `PREREG.md` / 旧 `RESULT.md` 成立格  
- 未过门激活 `PREREG-B` / 正式生成进主表  
- 金标/评委进 score；削弱 B1/B2；夹具填甲  
- S / S+R  
- 改生产检索默认；改五处冻表面  
- 本会话 `/implement` 业务代码；`/writing-plans`  
- 平行轨 D1–D5 设计（#434/#435）  
- 两名真人盲审正文（另附加预注册）  
- Docker  

## Further Notes

仓外门闩报告即使方向为正，也只授权**写激活批注**；激活后仍只有一次正式主跑。甲未成立前，对外口径不得称 T 更好。

**#466 后**：`/to-spec` 增量已落 [`25-patch-events-路线B-T与B1同after.md`](./25-patch-events-路线B-T与B1同after.md)（票序 1b / 2' / 1c）。**不可以**把「设计冲甲」写成「将得到甲」。未过复测门闩不得开 #440 正式生成进主表。
