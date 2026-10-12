# 判定协议：unknown / abstention 三分（SLI 3）

> **生产观测 ≠ 乙尺。**  
> 本页是 SLO-min6 T4（[#560](https://github.com/luxingjiang1993/FreshLatch/issues/560) · Parent [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556)）的 unknown / abstention 协议。SLI 3 与 `fresh` / `stale` **三分并存**。拒识算能力，不是失败。  
> 交付真源是 #556 / #560 与本页，以及 [`生产观测最小6-索引.md`](生产观测最小6-索引.md)。未合并的 [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) 仍是 program draft，不是第二套交付真源。  
> phase-2 P2（failure attribution 3-way）不进本页主行。协议在 [`挂标-失败归因三桶.md`](挂标-失败归因三桶.md)（[#572](https://github.com/luxingjiang1993/FreshLatch/issues/572) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）。**ADR-0028 ≠ fresh/stale/unknown**。本页不报 `fail_bucket`，不与那三桶互改标，不改本页 fresh/stale/unknown 定义。未改 RESULT-Y。未称乙。  
> Provenance：**new**（本 ops 协议页）+ **adapt** 种子：ADR-0028 / I1 的失败三分法标签（评测/答辩，不改生产枚举）；仓内 `fresh` / `stale` / `unknown` 三档（`Claim.status`、ADR-0009）；[#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) head `cursor/prod-slo-ops-aee8` @ `b24b6f573652b156a798dfa3f3fd1985a9e3348d` 宽表里「再验得明确 fresh/stale/unknown」的既有句子（A5，不新编号）。  
> 对照（不新建主名）：HALT-RAG 的 abstention；Confident AI 的 abstention / groundedness。  
> **本变更未编辑** `RESULT-Y` / `PREREG-Y` / SESOI / \(k_{\min}\) / Cond / 选取 R。未改 `src/` 放行谓词，未改 `src/freshlatch/gates/rule_gate.py`。金标不进生产 score。未实现、未调用 `compare_primary`。  
> 防火墙：ADR-0042。#508 草案曾写 ADR-0034；tip 上该号已被 `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md` 占用，本页引用 ADR-0042，不覆盖。硬继承只读：ADR-0028 · ADR-0009。  
> `#508` **Keep draft · No merge until Matt**。本协议所在 PR 同样不合并，直到 Matt 审。  
> 日期：2026-10-12（Asia/Shanghai）。落地基线 `00a9225cdc7e9c168b3ce278e0ec55443828284f`（含 #565）。路线 Y 结果丙的只读锚仍是 `2a3fadd`。  
> 禁止把本页称作：乙、软乙、接近乙、主实验成功。生产变绿不得改判丙。

层身份：观测 / Watch。本页的占比不作本波 Gate 生死。「装绿=0」是指向既有硬闸的指针，不是第 7 个主 SLI，也不是新的宽表 ID。

---

## 0. 目的

同一周报窗口里同时看见 `fresh`、`stale`、`unknown` / abstain。第三态占多少，要能填。拒识留在第三态里，算系统有能力在该弃时弃，不算失败。

| 要看见的 | 不在本页交付 |
|----------|----------------|
| 三格同窗：`fresh_n`、`stale_n`、`unknown_n`，以及 unknown/abstain 占比 | 把 abstention 改记成 false-accept 或 false-reject |
| 分母 = 判定出口里这三档之和 | 把 unknown 压进 SLI 1·2 的分母，伪装放行成功率 |
| 「装绿=0」指向既有硬闸；无证不得填 0 | 新编一条「装绿率」KPI，或把 unknown 记成失败 |
| 对照 HALT-RAG / Confident AI 的字段习惯 | 新建 HALT-* 或 Confident-* 主名 |
| ADR-0028 三桶只读 | 把「找不到 / 找错 / 没用上」升成平行失败三分周报 |

---

## 1. 字段定义（三分）与分母

窗口内的判定出口，指机器落档后的主张状态，封闭三值里的 `fresh`、`stale`、`unknown`（`src/freshlatch/models.py` 的 `Status`；运行时默认 `unknown`）。`void` / `voided` 是人的终态（ADR-0006），不进本分母。`renew` 是人审动词，不是第四个判定档。

| 档 | SLI 角色 | 操作定义 | 计入 |
|----|----------|----------|------|
| `fresh` | 三分之一 | 落档状态为 `fresh`。绿灯只来自既有绿格（ADR-0009：全 fresh 才绿） | `fresh_n`；并进入分母 |
| `stale` | 三分之二 | 落档状态为 `stale` | `stale_n`；并进入分母 |
| `unknown` / abstain | **SLI 3** | 显式输出 `unknown`（含证据不足时的诚实未知、闸把无依据 fresh 打回后的 `unknown`） | `unknown_n`；并进入分母。这是占比的分子，不是失败分子 |

占比 = `unknown_n / N_exit`。`N_exit` = `fresh_n + stale_n + unknown_n`。三格与占比使用同一个窗口。只留一格或两格 = 本协议违例。

### 1.1 分母细则

- **分母** `N_exit` = 窗口内已经完成判定落档的出口中，`status` 为 `fresh`、`stale` 或 `unknown` 的条数。完成判定，指本窗口的复验单上经过 Lead / Auditor / 规则闸写下的状态，而不是主张库存的全表。  
- **分子** `unknown_n` = 其中显式落档为 `unknown` 的条数。abstain 与这个状态是同一个生产字段，不另起一列主名。`reverify_claim(..., "unknown", ...)`（证据不足时 `mark_gap` 之后的出口）算显式第三态。  
- 尚未进入复验、只因 `Claim.status` 的 schema 默认值停在 `unknown` 的主张，不进 `N_exit`，也不进 `unknown_n`。导出分不出「显式落档」和「默认值」时，整窗走 §4，禁止把默认 `unknown` 当成拒识占比。  
- `void`、`voided=true` 的人工作废不进 `N_exit`。人审 override 的比率在 [`人审-override周报.md`](人审-override周报.md)，不在本页改分母。  
- 金标档名 `must_unknown` / `must_fresh` / `must_stale` 解释「诚实未知 / 该红 / 该绿」在离线尺上的意思。它们**不**进入 `unknown_n` 或 `N_exit`，不进入生产 score，也不充当入样键。本页计数的是生产判定出口的 `status`，不是 `gold.json` 的命中条。  
- 分母为 0，或本周无法划定窗口时，三格占比都写「样本不足」。禁止记成 0、0.0 或 0%。  
- 分母大于 0，且确实数到 `unknown_n=0` 时，占比写 `0 / N_exit`，notes 写明：这是第三态计数，不是失败率为 0，也不是装绿违例已经清零。装绿违例格仍按 §3 单独填。

### 1.2 与 false-accept / false-reject 的分界

SLI 1·2 的人标协议在 [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md)。两页字段并存，互不改标。

| 字段 | 属于 | 本页处置 |
|------|------|----------|
| `false_accept`（B2） | 已放行样本里，人标认为不该放 | 留在 SLI 1。不得把 `status=unknown` 改记进这一格 |
| `false_reject`（B3） | 人标认为该放、却被拦 | 留在 SLI 2。不得把 abstention 改记进这一格来压低误拒或抬高「看起来的正确」 |
| 抽检标签 `insufficient_context` | 人标无法判定该放或不该放；不进 B2/B3 比率分母 | 不是本页 `unknown` 的别名。不得改记成 false-accept 或 false-reject，也不得拿来充当 `unknown_n` |
| `status=unknown` | 机器判定出口的第三态 | 只进 SLI 3。不进入 B2 分母，不进入 B3 分母 |

把 unknown 从三分里挪走、再拿剩下的 fresh 出口计算放行成功率，视为用分母伪装成功率，本协议违例。

### 1.3 单条出口怎么归档（最小集）

每条计入 `N_exit` 的出口只归一档：

| 落档 `status` | 周报档 | 是否失败 |
|---------------|--------|----------|
| `fresh` | fresh | 不在本页判失败。放行之后的坏改仍由 B2 在抽检页计 |
| `stale` | stale | 不在本页判失败 |
| `unknown` | unknown/abstain | **不算失败**。拒识留在本档 |

不存在第四个生产档把 abstention「翻译」成误放或误拒。

---

## 2. 窗口

- **窗口**：过去 7 个自然日，或本发布列车窗口。周报写明起止，时区 Asia/Shanghai。三格使用这同一个窗口。  
- **频率**：每周（或每发布列车）一轮。三格同一轮出报。  
- **取数**：只读复验单 / sheet 导出里的主张 `status`（`src/freshlatch/sheet.py` 导出字段 `status`）。导出划不出窗口边界时，走 §4，不按全库历史凑比率。  
- 本页不新写聚合脚本，不改 `src/`。

起步姿态是把三格和分母报出来。本页不锁 unknown 占比的通过线，也不把「unknown 变少」写成成功。

---

## 3. 「装绿=0」硬闸指针

无证不得装绿：没有满足既有绿格条件时，出口不得写成 `fresh` 或绿灯。这个目标已经在硬闸上，本页只给指针。周报列名仍叫「装绿违例」，身份是指针，不是新 KPI ID，也不是最小 6 的第 7 个成员。

| 既有闸 | 只读锚 | 指针句 |
|--------|--------|--------|
| `stale` / `unknown` 不得绿灯 | `rule_gate` 校验项 1；`GateResult.green` 对非绿请求恒为 false | unknown 落档可以计数，不发绿 |
| 无 `t1_evidence_ids` 不得 `fresh` | `rule_gate` 校验项 2 | 无证不得装绿 |
| Auditor 缺席或未判 fresh 却已是 fresh | ADR-0009；`seal_no_unfounded_fresh` 打回 `unknown` | 无依据的 fresh 回到第三态，不保留绿灯 |
| 无 T1 绿灯次数 | 宽表 D3；ADR-0042 | 目标 = 0 |
| Agent 自红转绿 | 宽表 C5；ADR-0042 | 目标 = 0 |

支撑这些硬闸的违例计数仍在 defer 的 #512，不因本页升成主 SLI。

周报「装绿违例」格的填法：

- 当周已经读过上表某一条的既有计数：只抄违例次数，并注明抄的是 D3、C5，还是无证 fresh 被打回。不把抄来的数升成新 ID。  
- 当周没有读、没有计数：写「未计」。禁止无证填写 0、0.0 或 0%。  
- 目标句固定为「目标 0（硬闸指针）」。目标句不是当周测量值。`unknown_n=0` 不能代替本格。

unknown 落档本身不是装绿违例。把本应 unknown 的出口写成 fresh，才是装绿。

---

## 4. 样本不足

`N_exit` 为 0，或窗口划不出来时，周报使用下面的句式。fresh、stale、unknown/abstain 三格都写「样本不足」。禁止把任一格写成 0%、0.0 或 0。

```text
本周样本不足：判定出口 N_exit=0（或窗口不可划定），不报 fresh/stale/unknown 占比；三格写「样本不足」。unknown 仍不是失败。装绿违例另格：未计则写「未计」，不拿样本不足填 0。
```

同时禁止：

- 三格里删掉 unknown，只报 fresh 与 stale  
- 分母为 0 时宣称拒识已达标，或宣称本波 Gate 通过  
- 用金标 `must_unknown` 条数、实验固定 k 或生产 score 补 `N_exit`  
- 把「样本不足」改写成 0% 以便看起来平稳  

---

## 5. 对照映射（不新建主名）

| 对照 | 落在本页的哪一句 | 不做什么 |
|------|------------------|----------|
| HALT-RAG abstention | 拒识 / unknown 是合法输出。该弃则弃。第三态与 fresh/stale 并存 | 不新建 HALT-* 指标名。不把弃答记成错误 |
| Confident AI abstention | 对照 unknown/abstain 占比 | 不新建 Confident-* 主名 |
| Confident AI groundedness | 对照 §3「无证不得装绿」的既有闸 | 不把 groundedness 写成新的生产分数，也不把它改记成 B2/B3 |
| 仓内 fresh/stale/unknown | 本页主三分。词表已在 `Claim.status` 与 ADR-0009 | 不改生产枚举，不改 `rule_gate` |
| ADR-0028 / I1 | 评测标签三桶：找不到、找错、没用上。漏拦/误拦须另标 `err_kind`，且**禁止**改生产 status 来承载这三桶 | 不把这三桶升成周报主行 |

phase-2 的 failure attribution 3-way 复用 ADR-0028 这组种子，协议正文在 [`挂标-失败归因三桶.md`](挂标-失败归因三桶.md)（[#572](https://github.com/luxingjiang1993/FreshLatch/issues/572) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）。本页不报 `fail_bucket`，不另起一套失败三分的名字。本页三分（fresh / stale / unknown）与 ADR-0028 三桶不是同一套词，也不互相改标。**ADR-0028 ≠ fresh/stale/unknown**。

[#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) 宽表 A5 已经写「改完再验得明确 fresh/stale/unknown」。那是流程库存，不是 SLI 3 的占比定义。本页不把 A5 改号，不新编 B9 或 SLO-08。#508 保持 OPEN draft，head 仍为 `b24b6f573652b156a798dfa3f3fd1985a9e3348d`，不合并。

---

## 6. 叙事

可接受的观测叙事：

- 「同一窗口 fresh_n、stale_n、unknown_n 同在；unknown/abstain 占比 = unknown_n / N_exit；拒识不是失败」  
- 「N_exit=0，三格写样本不足，不报点估计」  
- 「装绿违例未计，指针在 D3、C5 与无证不得 fresh」

不可接受的叙事：

- 「把 abstention 改记成误拒之后，误拒下降了」  
- 「把 unknown 剔出分母之后，放行成功率上去了」  
- 「unknown 少了，所以模型变好」或「unknown 少了，所以验收通过」  
- 「装绿违例 = 0」，而本周没有读过 §3 的既有硬闸计数  
- 任何把本页数字写成实验成立、或拿来改判路线 Y 的句子

本波 SLI 3 为观测/Watch。把占比升成 Gate，或锁定一条 unknown 通过线，须另决议，并事先锁定判据。

---

## 7. 周报表格（最小列 · 三分必填）

填入 [`docs/evidence/slo-min6/周报骨架.md`](../evidence/slo-min6/周报骨架.md) 的 SLI 3 格，以及 [`生产补丁放行SLO.md`](生产补丁放行SLO.md) §6 的对应行。只抄摘要。禁止把数字写入 `RESULT-Y` 成立格。禁止写「接近乙」。本骨架页不预填比率。

| 列 | 说明 |
|----|------|
| `window` | 起止，Asia/Shanghai。三格同一窗 |
| `fresh_n` | 落档 `fresh` 的条数。无数字时留空，禁止编造 |
| `stale_n` | 落档 `stale` 的条数 |
| `unknown_n` | 落档 `unknown` 的条数。拒识算能力，不是失败分子 |
| `N_exit` | 分母 = 三者之和。为 0 则三格占比写「样本不足」，禁止写 0% |
| `unknown_rate` | `unknown_n / N_exit`。不足则「样本不足」 |
| `fresh_share` / `stale_share` | 同窗并列。禁止只报 unknown，或只报 fresh |
| `装绿违例` | §3 指针。未计数写「未计」，禁止无证填 0。目标句：「目标 0（硬闸指针）」 |
| `notes` | 写明未把 abstention 改记成 false-accept / false-reject；未把 unknown 压进 B2/B3 分母 |

---

## 8. 账本指针（只读）

| 指针 | 用途 |
|------|------|
| `Claim.status` | `fresh` \| `stale` \| `unknown` \| `void`。本页分母只用前三档。定义在 `src/freshlatch/models.py` |
| `src/freshlatch/sheet.py` | 导出字段 `status`。只读 |
| `src/freshlatch/roles/lead.py` | 证据不足时 `mark_gap` 后 `reverify_claim` 到 `unknown`。只读，本票不编辑 |
| `src/freshlatch/gates/rule_gate.py` | 校验项 1、2 与 `seal_no_unfounded_fresh`。本票不编辑 |
| ADR-0009 | 3×3 落档。全 fresh 才绿。Auditor 缺席不构成绿格 |
| ADR-0028 | 失败三分法标签。评测/答辩种子。不改生产枚举 |
| [`挂标-失败归因三桶.md`](挂标-失败归因三桶.md) | phase-2 P2。ADR-0028 三桶的挂标协议。本页不改标、不报 `fail_bucket` |
| ADR-0042 | 实验—生产防火墙。硬闸目标句的权威 |
| [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md) | B2/B3 分母。unknown 不并入 |
| [`生产观测最小6-索引.md`](生产观测最小6-索引.md) | 最小 6 成员表。本页是其中 SLI 3 |

聚合结果不回写为放行特征，不进入生产 score，不改 `compare_primary`，不改实验预注册。

---

## 9. 验收勾（本页范围）

- [x] 判定出口含 fresh/stale/unknown 时，周报可以同时填三格和 unknown/abstain 占比  
- [x] 协议禁止把 abstention 重标成 false-accept / false-reject  
- [x] 「装绿=0」指向既有硬闸；无证不得填 0；unknown 不算失败  
- [x] HALT-RAG 与 Confident AI 只作对照；ADR-0028 三桶不升成平行失败三分  
- [x] unknown 不进入 B2/B3 分母  
- [x] 未改 `RESULT-Y` / `PREREG-Y`；未把金标写入生产 score  

---

## 10. 非目标

- 合并 #508，或合并 #509–#515  
- 编辑 `RESULT-Y` / `PREREG-Y` / `formal-generations-y` / SESOI / \(k_{\min}\) / Cond / 选取 R  
- 实现或调用 `compare_primary`；改 `src/` 放行谓词或 `rule_gate` 语义  
- 把金标放进生产 score 或在线放行器  
- 把 abstention 重标成 false-accept / false-reject  
- 把 unknown 当作失败，或压进 FA/FR 分母  
- 新建平行失败三分法 KPI；把 ADR-0028 的三桶写进生产周报主行  
- 新编宽表 ID 或 `tasks/SLO-08.md`  
- 实现 T5–T6（#561–#562）  
- 把本页称作实验成立或主实验成功
