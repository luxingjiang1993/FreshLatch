# β: checksum 与 HumanLatch renew 交界设计评估

> **决议工单**: [β: checksum 与 HumanLatch renew 交界](https://github.com/luxingjiang1993/FreshLatch/issues/99)（地图 [#96](https://github.com/luxingjiang1993/FreshLatch/issues/96)）
> **决议日期**: 2026-09-23（两轮 grilling，Q1–Q6 推荐全部采纳）
> **决议落点**: 本评估、CONTEXT.md 半句指针、工单 #99 决议评论；**不开新 ADR**（挂 ADR-0006 §4 + ADR-0017）
> **上游**: ADR-0017、`docs/research/β-checksum激活契约与空转设计评估.md`、`docs/research/β-checksum攻击面用例集合设计评估.md`（ATK-CS 边界交接）
> **格式基准**: 《β-checksum攻击面用例集合设计评估.md》

---

## 1. 问题 + 前置约束

### 1.1 要拍什么

Batch 2（β）checksum 半激活之后，与 HumanLatch **续命（renew）** 的交界：

1. `validity_basis` **写入时机**；
2. 续命必带 T1 `evidence_id` 与 checksum 校验的**次序**；
3. 失败时**人可见**失败语义；
4. 与 ADR-0006 §4 续命生效链如何对齐；
5. 是否触及**跨轮腐烂**（若触及须预登记产品行为，不得塞进实装顺手做）。

验收层：**invariant**（续命路径确定性；人审出口语义不变；Agent 不得自绿）。

### 1.2 前置约束

| 前置 | 来源 | 锁死作用 |
|---|---|---|
| renew = 人审 L0；不受双判一致 | ADR-0006 §4；CONTEXT | 本票不改出口身份 |
| 档 2 半激活；禁读库列；不升格 latch | ADR-0017 / #97 | 交界不得扩大为全链启用叙事 |
| ATK-CS-01..04 已预登记；人可见/次序留给本票 | #98 评估 §4.3 | 本票补齐交界，不重开用例表 |
| 跨轮 = 档 3b | #111 | 本票若「不触及」须写死 |
| 不自动商业裁决；禁改 gold | 地图 #96 | 失败文案不得做成商业话术 |

### 1.3 代码现状（事实，非决议）

`human_latch._apply_renew` 已是：格式 → 点回 chunk → 用 `chunk.checksum` 组 basis → `rule_gate` → **仅 `gate.green` 后**写 basis/转绿/`latch_log`；失败带 `error_code`+`detail` 零写。

---

## 2. 候选路线

### 维度一：校验次序

- **A. 格式 → 点回 → 组 basis → 闸（含 checksum）→ 成功才写**
- **B. 先 checksum 再点回**
- **C. 并行/不分先后**

### 维度二：basis 写入时机

- **A. 仅闸绿之后写（失败零写）**
- **B. 点回后先写 draft 再闸**
- **C. 跨轮重读旧 basis 再比（3b）**

### 维度三：人可见失败

- **A. `error_code` + 短中文 `detail` 透传；不美化成商业裁决 / 不暗示 Agent 判定**
- **B. 统一模糊「请重试」**
- **C. 失败也改卡片暗示 Agent 判定**

### 维度四：ADR / CONTEXT / 预锁句

- ADR：不开 / 开短 / 只改注释
- CONTEXT：半句指针 / 新词 / 码表进词表
- 预锁句：长句对齐 ATK-CS / 短句 / 锁 UI 逐字

---

## 3. 逐路线评估

| 对照 | 拍板 | 被否理由 |
|---|---|---|
| 次序 A | 与现状、ADR-0006、ATK-CS 假设同构 | B 与「必带 evidence」张力；C 不可复现 |
| 写入 A | 满足 ATK-CS-01 零写 | B 半截状态；C 抢 #111 且须产品预登记 |
| 可见 A | 可对码验收；守 L0/非商业 | B 不可区分 ATK；C 污染 Agent/人审边界 |
| 不开 ADR | 与现状同构，三条件不齐 | 独立 ADR 通胀；无评估缺四件套主文 |
| CONTEXT 半句 | #4 码表不进词表 | 新词/枚举进 CONTEXT 过重 |
| 预锁长句 | 可引用、禁升格写死 | 短句不够；UI 逐字抢 prototype |

**Anthropic**：#1 不升格 latch/商业；#5 预锁句先于实现且本票声明不触及 3b；#4 不进词表枚举；#7 不开 ADR。

---

## 4. 拍板 + 预锁可引用句

1. **次序**：格式校验 → 点回 T1 chunk → 组 `validity_basis`（doc+入库指纹）→ 规则闸（含 checksum 现算比对）→ **仅绿后**写 basis / `last_confirmed_at` / `status=fresh` / `latch_log`。
2. **失败零写**：任一阶段失败不改 claim 续命字段；返回结构化 `error_code` + 短中文 `detail` 供 UI 透传。
3. **人可见语义**：透传即可；**禁止**美化成「建议作废/主张已死」类商业裁决；**禁止**把失败写成 Agent 自绿或机器改判话术。
4. **不触及跨轮**：本批不重读历史 basis 做腐烂降级；该行为属 [#111](https://github.com/luxingjiang1993/FreshLatch/issues/111)，须另预登记。
5. **与 ATK-CS 对齐**：#98 表机械期望不变；本票锁交界语义，不增删 ATK-CS-01..04。
6. **预锁句**（实现前锁死；事后改句 = 本批交界验收作废）：

   > Batch 2 renew 交界：格式→点回→闸（含 checksum）→仅绿后写 `validity_basis`/转绿；失败零写且 `error_code`+短中文透传；**不**启用跨轮重检；不得升格为 checksum 证明 latch / 商业裁决。

7. **本会话**不 `/to-spec`、不 `/implement`、不改 gold。

---

## 5. 工程手段总登记册

| 手段 | 原理 | 优势 | 代价 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| 续命三层校验后写 | 格式/点回/闸全过才落档 | 零写可测 | 无 | human_latch 现状 | **承载**（决议钉死为规格） |
| error_code 透传 UI | 结构化失败 | ATK 可对码 | 文案需短中文 | DecisionResult | **承载** |
| 商业话术美化失败 | 把拒续命讲成商业建议 | — | 品类违例 | 地图禁令 | **弃** |
| 点回后预写 draft basis | 早落档 | — | 失败半截状态 | — | **弃** |
| 跨轮重检塞本批 | 兑现 validity 牙齿 | — | 未预登记产品行为 | #111 | **弃**（留位） |
| 新开 ADR | 再钉一层 | — | 与现状同构无需 | 0006+0017 | **弃** |

---

## 6. 面试讲法

**Q:激活 checksum 后续命流程变了吗？**
A:次序没变，我们把它从「实现形状」钉成 **Batch 2 交界规格**：先证据后闸，绿后才写 basis。变的是 `checksum_fn` 真接线后，闸那一层开始有牙（见 ATK-CS）。

**Q:失败时用户看到什么？**
A:结构化错误码加短中文原因，例如 checksum 对不上。不把它说成「该出局」或「Agent 判死了」——续命仍是人的 L0 出口，失败只是这次没续上。

**Q:为什么不做跨轮？**
A:跨轮是改产品行为（人对 T1-v2 续命后语料变 v3 该降级），必须预登记，已挂 #111。塞进本批实装 = 绕过纪律。

**Q:这证明了 latch 吗？**
A:不证明。预锁句写死不得升格。品类证明仍是作废/Stay-Red，不是 checksum。
