# 生产补丁 / 放行 SLO（运营与产品纪律）

> **生产观测 ≠ 乙尺。** 本页是生产运营纪律的宽表库存（改编自未合并 program draft [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) @ `b24b6f5`）。本波收口的成员、层身份、防火墙与 Decisions 模板以 [`生产观测最小6-索引.md`](生产观测最小6-索引.md) 为交付真源（[#557](https://github.com/luxingjiang1993/FreshLatch/issues/557) · Parent [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556)）。  
> **本变更未编辑** `RESULT-Y` / `PREREG-Y` / SESOI / \(k_{\min}\) / Cond / 选取 R。生产变绿不得改判丙。  
> **权威**：防火墙 ADR-0042（[#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) 草案曾写 ADR-0034；tip `2a3fadd` 上该号已是 `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md`，本程不覆盖）· 评估草案留在 [#508](https://github.com/luxingjiang1993/FreshLatch/blob/b24b6f573652b156a798dfa3f3fd1985a9e3348d/docs/research/生产补丁放行SLO设计评估.md)（不复制进本分支，避免双真源）· 规格 `docs/spec/24-生产补丁放行SLO.md`  
> **层身份**：宽表仍分硬闸 / 观测 / 离线 / 实验-only。**本波主 SLI 只有最小 6**，层身份是观测/Watch + 离线 canary。  
> **冻结**：不改 `PREREG-Y` / `RESULT-Y` / `formal-generations-y`；不改生产放行谓词；金标不进生产 score。`#508` **Keep draft · No merge until Matt**。SLI 1·2 成对协议见 [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md)（[#558](https://github.com/luxingjiang1993/FreshLatch/issues/558)）。[#514](https://github.com/luxingjiang1993/FreshLatch/pull/514) 保持 candidate，不合并。SLI 4 override 周报见 [`人审-override周报.md`](人审-override周报.md)（[#559](https://github.com/luxingjiang1993/FreshLatch/issues/559)）。[#511](https://github.com/luxingjiang1993/FreshLatch/pull/511) 保持 candidate，不合并。本页不实现 T4–T6。

---

## 0. 一页总览

```text
改：     改对率 · 错改率 · 证据覆盖 · 再验失败率
放行：   误放 · 误拒 · （实验-only：固定k误放/差）· 无证拒拦 · 未确认不出门
人审：   作废率 · override · 续命带证 · 自转绿=0
复验：   must_stale · 无T1绿灯=0 · 包结论分布 · multi-run
实验：   实验尺另页 · 一门一跑 · 金标隔离 · 投稿映射（Y=丙只读）
```

本波最小 6（名字与层；定义表只在索引，此处不另编第 7 个宽表 ID）：

| # | 成员 | 层 | 宽表锚 |
|---|------|----|--------|
| 1 | false-accept | 观测/Watch | B2 |
| 2 | false-reject | 观测/Watch | B3 |
| 3 | unknown / abstention | 观测/Watch | 仓内 fresh/stale/unknown 三档（不新编号） |
| 4 | HumanLatch override | 观测/Watch | C2（C1 作废率只旁注） |
| 5 | e2e P95 latency + retrieval fallback rate | 观测/Watch | 不进 A–E 新编号；一行两字段 |
| 6 | frozen gold canary pass rate | 离线 canary | D1/D5 口径可喂；票本身 defer |

---

## 1. 分层词汇（本页内）

| 层 | 含义 | 成败用法 |
|----|------|----------|
| **硬闸** | 单事件可机检；违例即事故 | 目标 0 或 100%；可进回归 |
| **观测 / Watch** | 周报或抽检；需人标或聚合 | 看趋势；本波不作 Gate 生死 |
| **离线评测** | 金标 / Hard-Gold multi-run | 主业不退化；**不进生产 score** |
| **实验-only** | 路线 Y 的预注册实验尺、固定 k、T−C | 只读引用；不进本页 KPI；不是本页层身份 |

---

## 2. 与路线 Y 的边界（硬句）

1. Y 正式主跑结果**丙**冻结；本页不回写成立格。  
2. 生产 SLO 改善 **不得** 自动改写 RESULT-Y 为乙。  
3. 禁止同页二跑凑绿；机制大改 → 新预注册另页。  
4. 文面禁止：「接近乙」「软成立」「软甲」「主实验成功」（指 Y）。  
5. 固定 k 误放差（T−C）等为实验尺；生产只做误放/误拒成对观测（或抽检折算）。

---

## 3. 指标清单

> 下列 A–E 是 [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) 宽表库存，原样保留供对照。**不是**本波第 7+ 主 SLI。本波只收口上表 6 个成员。phase-2 六项见索引附录，不在本节升格。

### 3.1 改（生成 / 补丁质量）

| ID | 指标 | 定义 | 层 | 采集点 | 频率 | 起步 |
|----|------|------|----|--------|------|------|
| A1 | 补丁提案完整率 | 提案含 `after_text` + 合法 `t1_ids` | 硬闸 | `propose_patch` / `confirm_patch` 拒拦 | 连续 | 缺则拒 |
| A2 | 证据覆盖率 | 改动点能在勾选 T1 对上 | 观测 | 人抽检表 | 周 | 基线先建；证据对不上不得 confirm（流程） |
| A3 | 改对率（抽检） | 确认后 after：人审认为与证据一致且事实对 | 观测 | 人标样本 | 周 | 先建基线；主抽检指标 |
| A4 | 错改率 | 放行或确认后仍与真相不符 | 观测 | 与 A3 成对 | 周 | 与误放成对报 |
| A5 | 可复验率 | 改完再验得明确 fresh/stale/unknown | 流程 | confirm 后强制再验 | 连续 | 已有流程 |
| A6 | 再验失败率 | confirm 后单条再验仍失败占比 | 观测 | 再验结果聚合 | 周 | 可周报 |
| A7 | 槽位可核对率 | 数字/日期/专名等可自动核对槽占比 | 观测 | 自动核机制（若有） | 月 | 未产品化 KPI；双管优先 |

### 3.2 放行（闸 / release）

| ID | 指标 | 定义 | 层 | 采集点 | 频率 | 起步 |
|----|------|------|----|--------|------|------|
| B1 | 放行率 | release / 候选 | 观测 | 确认出口 / 钩子 allow | 周 | **禁止**单独升高当成功 |
| B2 | 误放率 | 放行里坏改占比 | 观测 | 抽检折算 | 周 | 高风险优先压；与 B3 成对 |
| B3 | 误拒率 | 该放被拦 | 观测 | 抽检折算 | 周 | 必报 |
| B4 | 固定 k 误放率 | 各臂同 k | 实验-only | PREREG-* | — | 不进生产 KPI |
| B5 | 固定 k 误放差 T−C | 乙尺 | 实验-only | RESULT-Y | — | Y=丙只读 |
| B6 | 无证拒拦率 | 无/非法 t1_ids 被拒 | 硬闸 | confirm 拒 | 连续 | ≈100% |
| B7 | 未确认不出门率 | 未 confirm 不得改正文/正式出口 | 硬闸 | 草案/账本/导出 | 连续 | **100%** |
| B8 | k / 有效放行量 | 自然放行数等 | 实验-only | 实验门闩 | — | 生产只作可用性旁注 |

SLI 1·2 的人标协议（分母、同一窗口、样本不足、B1 只作旁注）：[`抽检-放行误放误拒.md`](抽检-放行误放误拒.md)。B2 即 false-accept，B3 即 false-reject。两侧必须出现在同一周报表。缺一侧写「样本不足」，禁止写成 0%。禁止只报 B1 当成功。禁止单独优化拒拦率。字段改编自 [#514](https://github.com/luxingjiang1993/FreshLatch/pull/514) @ `948db415`。交付真源是 [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556) / [#558](https://github.com/luxingjiang1993/FreshLatch/issues/558)，不把 #514 合并进来，也不在本表外再起一套放行 KPI。

### 3.3 人审 / 自治

| ID | 指标 | 定义 | 层 | 采集点 | 频率 | 起步 |
|----|------|------|----|--------|------|------|
| C1 | 用户作废率 | 人对 Agent 绿灯/主张作废比例 | 观测（北星之一） | latch discard | 周 | 上线观测；最小 6 里只作 SLI 4 旁注 |
| C2 | Override rate | 人推翻机器判定比率（派生标签） | 观测 | `latch_log.override` | 周 | 看分权健康；**≠模型变好 / ≠验收绿灯** |
| C3 | 续命带证率 | renew 带新 T1 id | 硬闸 | renew 受理 | 连续 | **100%** |
| C4 | 补丁确认耗时 | 人确认 minutes | 观测 | `patch_events.minutes` | 周 | 字段有；运营弱 |
| C5 | 无人自动转绿次数 | Agent 自红变绿 | 硬闸 | 状态机 / 审计 | 连续 | **目标=0** |
| C6 | 导出前闸拦截次数 | 发前钩子拦住坏包 | 观测 | publish_hook deny | 周 | 事故前哨 |

SLI 4 的周报协议（C2 override rate、分母、样本不足、文首声明）：[`人审-override周报.md`](人审-override周报.md)。C2 即 HumanLatch override。分母是窗口内 `latch_log` 可计的、已带 override 标签的人审行（`action` 为 `discard` 或 `renew`，且 `override` 为 0 或 1）。分子是其中 `override=1` 的行。分母为 0 时写「样本不足」，禁止写成 0%。文首声明：**≠模型变好 / ≠验收绿灯**（ADR-0023）。C2 不作验收绿灯。C1 用户作废率可以出现在同一周报，身份是旁注，不另起平行 KPI，也不升成最小 6 的第二个主字段。不新增 HumanLatch 动词。字段改编自 [#511](https://github.com/luxingjiang1993/FreshLatch/pull/511) @ `70286694b30bf2d06df863b4a48e2ff3447b9644` 的 C2 聚合定义。交付真源是 [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556) / [#559](https://github.com/luxingjiang1993/FreshLatch/issues/559)。不把 #511 合并进来，不合入 `scripts/slo_c1_c2_latch_rates.py`。

### 3.4 复验主业

| ID | 指标 | 定义 | 层 | 采集点 | 频率 | 起步 |
|----|------|------|----|--------|------|------|
| D1 | must_stale 命中率 | 金标必须红是否红 | 离线评测（北星） | gold multi-run | 发布前/周 | 不低于当前金标门 |
| D2 | must_fresh 不误杀 | 干扰项不被错杀 | 离线评测 | gold multi-run | 同 D1 | 防全红假象 |
| D3 | 无 T1 绿灯次数 | 违规绿灯 | 硬闸 | rule_gate / 出口 | 连续 | **目标=0** |
| D4 | 包结论分布 | 可发 / 需补丁 / 勿发 | 观测 | disposition 聚合 | 周 | 看负载 |
| D5 | multi-run pass@k | 同金标多跑通过率+方差诚实框定 | 离线评测 | eval runner | 同 D1 | 防单次幸运绿；n 小不报总体方差 |

### 3.5 实验 / 论文（切开，只读）

> 下表只指向路线 Y 另页的既有判据，供防火墙对照。本生产页不使用该判据的成立称谓。

| ID | 项 | 纪律 |
|----|-----|------|
| E1 | 乙成立（Y） | T−C：点&gt;0.05 ∧ 下界&gt;0；本次**丙** |
| E2 | 门闩 | k≥10 ∧ T−C 点&gt;0；探针≠乙 |
| E3 | 一页一次主跑 | 禁止二跑凑绿 |
| E4 | 金标不进生产 score | 本页硬纪律 |
| E5 | B1/B2 报告-only（Y） | 不写优于 RARR/KPR |
| E6 | 投稿映射 | 丙→不 Industry 成功叙事（DECISION-LOG） |

---

## 4. 起步阈值（预注册 · 2026-10-09）

| 指标 | 起步 | 层 |
|------|------|-----|
| 无证 / 未确认出门 | **0** | 硬闸 |
| Agent 自红转绿 | **0** | 硬闸 |
| 无 T1 绿灯 | **0** | 硬闸 |
| 续命带证 | **100%** | 硬闸 |
| 确认后严重错改（会害客户）抽检 | 先观测；Watch 讨论线 **&lt;5%** | 观测（样本协议齐备前不升 Gate） |
| 补丁后仍「勿发/需补丁」占比 | 只观测 | 观测 |
| must_stale multi-run | 不低于当前金标 / Hard-Gold 门 | 离线评测 |
| 实验 T−C | 另页；不与生产混写 | 实验-only |

事后为凑绿改本表门槛 = 本页与评估作废，须重签。

---

## 5. 双管验收包（最低集 · 另页可扩）

**改侧**：A3 基线 · A6 可周报 · A2 证据对不上不得 confirm  

**放行侧**：B2/B3 成对周报 · B6/B7 保持硬闸 · 不用单独放行率当成功  

**人审**：最小 6 主字段是 C2（[`人审-override周报.md`](人审-override周报.md)）；C1 只旁注 · C5=0 持续监控  

**复验主业**：D1 multi-run 不掉 · D3=0  

**实验边界**：生产绿 ≠ RESULT-Y 改判乙 · 机制大改 → 新预注册  

---

## 6. 周报最小字段（文档级看板）

本波周报骨架（最小 6）在 `docs/evidence/slo-min6/周报骨架.md`。下面这份是宽表库存字段，多出来的项仍不是本波主 SLI。

每周（或每发布列车）宽表至少能填：

- 硬闸违例计数：B6/B7/C5/D3（期望 0）  
- A3/A4 抽检：样本 n、改对、严重错改  
- A6 再验失败率  
- B2/B3 成对，同一窗口（协议 [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md)）；缺一侧写「样本不足」，禁止写成 0%；B1 只旁注；禁止单独优化拒拦率  
- C2 override rate 与分母（协议 [`人审-override周报.md`](人审-override周报.md)）；分母为 0 写「样本不足」，禁止写成 0%；文首声明 ≠模型变好 / ≠验收绿灯；C1 作废率只旁注；C4 中位 minutes 仍是宽表库存，不是本波主 SLI  
- D4 包结论分布  
- D1/D5：若本周跑了离线评测则抄 multi-run；否则写「未跑」  
- **禁止**填写 RESULT-Y 成立格或「接近乙」句  

---

## 7. 非目标

- 复活 patch_events 冲路线 Y / 同页二跑  
- 把本程称作实验成立或主实验成功  
- 大屏产品 UI（本期）  
- 把评测加严阈值写入 `CONTEXT.md`  
- 合并 `#508`、`#511` 或 `#514`；改 `src/` 放行谓词或 HumanLatch 动词集；实现 T4–T6（#560–#562）  
- 把 override rate 当成验收绿灯或模型变好  
- 把 phase-2 六项或宽表其余 ID 升成本波主 SLI  
- 本决议会话写业务代码（须 before-implement 后另开）
