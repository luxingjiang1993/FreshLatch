# β: checksum 攻击面用例集合设计评估

> **决议工单**: [β: checksum 攻击面用例集合](https://github.com/luxingjiang1993/FreshLatch/issues/98)（地图 [#96](https://github.com/luxingjiang1993/FreshLatch/issues/96)）
> **决议日期**: 2026-09-23（两轮 grilling，Q1–Q6 推荐全部采纳）
> **决议落点**: 本评估（预登记用例表）、CONTEXT.md 半句指针、工单 #98 决议评论；**不开新 ADR**（挂 ADR-0017）
> **上游**: ADR-0017、`docs/research/β-checksum激活契约与空转设计评估.md`
> **格式基准**: 《β-checksum激活契约与空转设计评估.md》

---

## 1. 问题 + 前置约束

### 1.1 要拍什么

Batch 2（β）在半激活边界已定之后，预登记用于 **invariant 验收** 的 checksum **攻击面用例集合**：收哪些、故意排除哪些、每条如何证明「有牙非空转」。

### 1.2 前置约束

| 前置 | 来源 | 锁死作用 |
|---|---|---|
| 主激活档 2（renew）；fresh 结构性空转 | ADR-0017 / #97 | 用例不得逼上 3a/3b |
| 激活预锁句：真 `checksum_fn` + 篡改负例 | ADR-0017 | ATK-CS-01 必须覆盖该句 |
| 套套逻辑硬禁（禁读库列） | ADR-0017 | ATK-CS-02 哨兵 |
| 禁改 gold 凑绿；验收层 invariant | 地图 #96 | 用例不得碰 gold / 不得升格 latch |
| renew 人可见文案、写入次序 | 子票 #99 | 本票不吞 |

---

## 2. 候选路线

### 维度一：IN 集合广度

- **A. 最小四条**：篡改负例 + 套套哨兵 + 空 claimed 拦截 + 未篡改正例
- **B. 加上多 evidence 主文档失败、跨轮重检**（抢 3a/3b）
- **C. 仅文档叙事、无期望 error_code**

### 维度二：OUT 清单

- **A. 明确排除**多证据主文档、fresh 补 basis、跨轮、真实并发窗、改 gold/放宽闸
- **B/C.** 把 3a 或 3b 场景收入本批

### 维度三：表格式

- **A. 四列 +「若仍空转会怎样」**
- **B. 只叙事**
- **C. 每条改 gold**

### 维度四：ADR / CONTEXT / vs #99

- ADR：**不开** / 开短 ADR / 只补丁旧契约
- CONTEXT：不增词+半句指针 / 新词 / 全文进词表
- vs #99：本票只机械牙齿 / 连文案次序一并拍 / 合并进 #99

---

## 3. 逐路线评估

| 对照 | 拍板 A 路 | 被否 |
|---|---|---|
| IN 广度 | 四条咬住 ADR-0017 预锁句与假激活 | B 抢 3a/3b 且未预登记产品行为；C 非预登记 |
| OUT | 边界清晰，下游票仍有内容 | 收入 3a/3b = Anthropic #5 违例风险 |
| 表格式 | 可复现、可作废重登 | B 事后填码=HARKing；C 禁令 |
| ADR | 挂 0017，改表须声明作废 | 独立 ADR 通胀；无评估则四件套缺主文 |
| CONTEXT | 验收仪器不进词表全文（#4） | 新词易把用例表误成品类概念 |
| vs #99 | 职责不叠，可并行 | 抢 #99 或空心化本票 |

**Anthropic 清单**：#1 用例证牙齿不证 latch；#5 表先于实现；#4 表不进 CONTEXT；#7 不开 ADR（难反转/反直觉不足）。

---

## 4. 拍板 + 预登记用例表（实现前锁死）

**纪律**：改本表期望或增删 IN 用例而不声明「Batch 2 攻击面验收作废并重登」= 违例。本会话不 `/implement`、不改 gold。

### 4.1 IN

| id | 前置 | 动作 | 期望 | 若仍空转会怎样 |
|---|---|---|---|---|
| **ATK-CS-01** | 语料已 ingest 且 checksum 非空；真 `checksum_fn`（sha256 现算）已接线 | 篡改对应 `data/corpus/{as_of}/{doc_id}.md` 后 renew | `CHECKSUM_MISMATCH`；claim **零写**（status/basis/latch_log 不变） | `checksum_fn` 恒 None/空 → 不拦，预锁句失败 |
| **ATK-CS-02** | 夹具或契约测试可构造「`checksum_fn` 读库列」的错误接线 | 以 basis 同源库值作为 `checksum_fn` 返回；claimed=该库值 | **不得**仅因恒等而过闸记为激活成功；哨兵用例必须**失败**（暴露假激活）或静态断言禁止该接线 | 误接库列仍「测试全绿」→ 假激活比空转更糟 |
| **ATK-CS-03** | `checksum_fn` 返回非空；`validity_basis.checksum` 为空字符串 | renew/闸校验带该 basis | 拦截（与现闸 `actual and claimed != actual` 一致）；不得绿灯写入 | 空 claimed 被当成「未启用」放过 → 半接线假绿 |
| **ATK-CS-04** | 同 01 但**不**篡改语料；claimed=现算 | renew | 过闸；写入新 `validity_basis` + 审计迹 | 凡 renew 都拒 → 牙齿变成断路，非激活 |

### 4.2 OUT（故意排除）

| 场景 | 排除理由 | 去向 |
|---|---|---|
| 多 evidence 主文档选取失败 | 属档 3a schema/取舍 | [#110](https://github.com/luxingjiang1993/FreshLatch/issues/110) |
| fresh 路径补 `validity_basis` | fresh 半边结构性空转 | ADR-0017；#110 |
| 跨轮腐烂重检 | 产品行为变更 | [#111](https://github.com/luxingjiang1993/FreshLatch/issues/111) |
| 续命窗内真实并发竞态 | 静态合成语料；由 01 确定性篡改覆盖 | 本批不单列 |
| 改 gold / 放宽闸冒充激活 | 地图禁令 | Out of scope |

### 4.3 与 #99 边界

本表只锁**机械**期望（error_code / 零写 / 过闸）。人可见失败文案、`validity_basis` 写入时机、与 T1 evidence_id 校验**次序** → [#99](https://github.com/luxingjiang1993/FreshLatch/issues/99)。

---

## 5. 工程手段总登记册

| 手段 | 原理 | 优势 | 代价 | 参考先例 | 本期处置 |
|---|---|---|---|---|---|
| 预登记攻击面表 | 实现前锁期望 | 防 HARKing | 改表须作废重登 | ADR-0017 预锁句 | **实装**（本文 §4；代码在 /to-spec 后） |
| 语料文件篡改负例 | 现算 vs claimed | 真牙 | 需临时文件夹具 | test_renew 注入式雏形 | **触发**（ATK-CS-01） |
| 套套哨兵 | 禁读库列可测 | 防假激活 | 夹具要显式接错 | 契约 §3 | **触发**（ATK-CS-02） |
| 空 claimed 拦截 | 半接线失效 | 与现闸语义对齐 | 旧空 checksum 续命路径变严 | rule_gate | **触发**（ATK-CS-03） |
| 正例对照 | 非断路 | 防「全拒」假牙 | 无 | test_renew happy path | **触发**（ATK-CS-04） |
| 用例进 gold | 用主张判定冒充闸牙 | — | 禁令 | — | **弃** |
| 本批测 3a/3b | 抢下游 | — | 未预登记 | #110/#111 | **弃** |
| 新开 ADR | 再钉一层 | — | 通胀 | ADR-0017 已够 | **弃** |

---

## 6. 面试讲法

**Q:攻击面用例是不是红队/安全审计？**
A:不是。是 **invariant 仪器**：证明宣称激活的 renew 半边负例打得响、正例过得去、套套接法会被哨兵揭穿。不证明客户会买、不证明 latch。

**Q:为什么只有四条？**
A:ADR-0017 只激活档 2。多证据和跨轮是 3a/3b，另票预登记。把它们塞进本表 = 未预登记改产品/schema。

**Q:ATK-CS-02 怎么测又不实现错误接线？**
A:夹具**故意**注入读库列的 `checksum_fn`，断言该配置不得被当成激活成功；或契约/静态检查禁止生产接线读库列。目的是失败模式可见，不是上线错误实现。

**Q:改表行不行？**
A:技术上容易，实验上要先声明本批攻击面验收作废并重登。可编辑 ≠ 可逆。

**Q:和改 gold 什么关系？**
A:无关且禁止。checksum 牙齿不靠主张金标变色。
