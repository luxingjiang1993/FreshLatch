# 弱信号 Watch（P6 · implicit feedback · ≠ 金标）

> **生产观测 ≠ 乙尺。**  
> **弱信号 ≠ 金标。** 下面四行是无显式评分时的下游计数。它们不表示主张为真，不进生产 score，不升硬闸，不作乙尺，也不作 RESULT-Y 的改判信号。  
> 本页是 SLO-phase2 T7（[#576](https://github.com/luxingjiang1993/FreshLatch/issues/576) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）的 implicit feedback 协议。成员名是 **implicit feedback**。层身份是观测/Watch，计数可以离线聚合。  
> 交付真源是 #569 / #576 与本页，以及 [`生产观测phase2-索引.md`](生产观测phase2-索引.md)。未合并的 [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) 仍是 program draft，不是第二套交付真源。  
> Provenance：**adapt** from tip **ADR-0006**（动词封闭集、`latch_log`、`rerun_log` 重跑 · 只读）+ tip **ADR-0023**（不新增 action；`override` 是派生标签 · 只读）+ tip [`生产观测phase2-索引.md`](生产观测phase2-索引.md) P6 起步定义 + tip [`docs/evidence/slo-phase2/周报附录骨架.md`](../evidence/slo-phase2/周报附录骨架.md) P6 行 + **ADR-0042**。可选只读互指：min-6 抽检 [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md)（SLI 1/2）与 min-6 override [`人审-override周报.md`](人审-override周报.md)（SLI 4）。那两页的主列不因本页改写。  
> **本变更未编辑** `RESULT-Y` / `PREREG-Y` / SESOI / \(k_{\min}\) / Cond / 选取 R。未改 `src/` 放行谓词，未改 `src/freshlatch/gates/human_latch.py` 的 `VALID_ACTIONS`。金标不进生产 score。未改写 min-6 六个主格。  
> 防火墙：ADR-0042。#508 草案曾写 ADR-0034；tip 上该号已被 `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md` 占用。本页引用 ADR-0042，不覆盖 ADR-0034。  
> Parent [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556)（min-6 track）**仍 OPEN**。本页挂在 #569 下，不挂在 #556 下。  
> `#508`–`#515` **本波不合并**。本协议所在 PR 是 draft。No merge until Matt+human。  
> 日期：2026-10-12（Asia/Shanghai）。Trust **L1** · Blast **docs/obs**。落地基线 `29beaccbe3334d3184f83b7d0aa892903a578b43`（#584 squash · #575 已在 tip）。该 sha 不是本周弱信号计数。路线 Y 结果丙的只读锚仍是 `666679c6ba09b09da34a46f558f14dab5896ca58`。两个 sha 都不填进下面四行。  
> 禁止把本页称作：乙、软乙、接近乙、主实验成功。生产变绿不得改判丙。弱信号变多或变少不得改判丙。

层身份：观测 / Watch。本页数字不作本波 Gate 生死，不锁「回改低于多少」「重开低于多少」的通过线，不升硬闸，不作乙尺。

---

## 0. 目的

同一周报窗口里，在没有人给显式分数的时候，看见四件下游的事有没有发生：确认过的正文后又被确认成另一段文字、作废主张被人重新打开去重跑、同一主张在窗内被成功人审了不止一次、后一次确认把正文退回到更早那次确认之前的文字。

| 要看见的 | 不在本页交付 |
|----------|----------------|
| 四行信号各自的分子、分母 | 把其中一行写成金标或生产 score |
| 账本不可读、或信号不在清单里时写「未计」 | 用 0 代替没读到的账 |
| 分母为 0 时写「样本不足」 | 用缺样本宣称本窗没有回改、没有回滚 |
| 人审动词仍只是 `discard` \| `renew` | 为「重开」「回滚」「再审」新增 HumanLatch 动词 |
| 与 SLI 1/2、SLI 4 并排只读 | 把弱信号写入 `b2_rate`、`b3_rate` 或 `c2_rate` |

显式评分（人标对错、金标命中、faithfulness 分）不进这四行。有显式评分的抽检仍走各自的协议页。

---

## 1. 信号清单

四行到此为止。第五行固定是「未列信号」，格子永远写「未计」。本波不把「等」展开成新的主名。

| 信号 | 字段 | 看见的事 | 分子 | 分母 |
|------|------|----------|------|------|
| confirm 后回改 | `post_confirm_edit` | 窗内第一次产品确认之后，同主张又有一次产品确认，且 `after_text` 不同 | `n_edit` | `n_confirm` |
| 重开 | `reopen` | 作废主张在窗内出现 `rerun_log` 行（新开 `reverify-{claim_id}-{ts}`） | `n_reopen` | `n_void_eligible` |
| latch 再审模式 | `latch_rereview` | 同主张在窗内有至少两条成功的 `discard` 或 `renew` | `n_rereview` | `n_latched` |
| 补丁回滚迹象 | `patch_rollback_sign` | 后一次产品确认的 `after_text` 等于锚点那次的 `before_text` | `n_rollback_sign` | `n_confirm` |
| 未列信号 | — | 清单以外的任何下游现象 | 未计 | — |

重开这一行的产品按钮仍是 ADR-0006 的「重跑作废主张」。`reopen` 只是本页的 Watch 字段名。它不进入 `VALID_ACTIONS`。

回滚迹象是正文退回的计数，不是一条名叫 rollback 的命令。仓内没有补丁回滚动词。本页不新增。

---

## 2. 窗口

- **窗口**：过去 7 个自然日，或本发布列车窗口。四行使用同一串 `window`。时区 Asia/Shanghai。周报写明起止。  
- **半开区间**：日历周时 `start` 含当日，`end` 不含结束日。指定起始日且未写结束日时，结束日 = 起始日 + 7 天。  
- 锚点和用来比较的后一行都必须落在这个窗口里。更早一周的确认不拿来补本周的分子。跨窗的回改、重开、再审、退回，本窗不补计。  
- 窗口不可划定：四行都写「样本不足」。禁止另开一窗把样本凑齐。

---

## 3. 计入

计数单位是去重后的 `claim_id`。同一主张在同一行里只计一次。本页不新写聚合脚本，不改 `src/`。当周由人按本节读账，离线聚合也可以，读的是下面这些既有账本。

### 3.1 confirm 后回改

产品确认行必须同时满足：

- `human_confirm` 为真  
- `arm` 为 `T`（`append_product_confirm` 的产品路径）  
- `before_text` 与 `after_text` 成对出现  
- `ts` 落在窗口内  

`n_confirm` = 至少有一条这样的行的 `claim_id` 数。

锚点 = 该主张在窗口内按 `ts` 最早的一条产品确认行；`ts` 相同时按文件中的先后。

`n_edit` = 锚点之后、仍在窗口内，又有一条产品确认行，且那一行的 `after_text` 与锚点的 `after_text` 不同。这样的 `claim_id` 数。

相同 `after_text` 的再次确认不计入 `n_edit`。

### 3.2 重开

`n_reopen` = 窗口内 `rerun_log.ts` 落在窗口里的去重 `claim_id` 数。对应的线程形如 `reverify-{claim_id}-{ts}`（ADR-0006）。

`n_void_eligible` = `invalidation_list` 上 `voided_at` 早于窗口结束的去重 `claim_id` 数。这是可重跑的存量，不是本窗新作废的流量。C1 作废率仍只在 SLI 4 的旁注里，本分母不回写 C1。

`latch_log.action=rerun` 是同一次重跑的影子行（`sheet.py` 已规定两表只计一次）。影子行不加入 `n_reopen`。

代码只允许作废名单上的主张重跑。账上出现不在名单里的 `rerun_log` 行：这一行写「分列不一致」，分子分母都不报数。不手改名单把它们凑平。

### 3.3 latch 再审模式

成功人审行必须同时满足：

- `latch_log.action` 为 `discard` 或 `renew`  
- `override` 已经写成 0 或 1  
- `ts` 落在窗口内  

`n_latched` = 至少有一条这样的行的 `claim_id` 数。

`n_rereview` = 至少有两条这样的行的 `claim_id` 数。

幂等跳过不新增行（既有写路径：重复 `discard`、同证据的重复 `renew`）。没有第二行，就不进 `n_rereview`。

四条序列只放备注，不是第五个信号，也不是动词：`discard→discard`、`discard→renew`、`renew→discard`、`renew→renew`。序列没逐条点开时，备注写「序列未计」。`n_rereview` 仍可以按主张数填写。序列四格之和若填写，必须等于 `n_rereview`；和不等于则备注写「序列不一致」，序列四格改写「未计」，主张数保留。

### 3.4 补丁回滚迹象

分母与 §3.1 相同，都是 `n_confirm`。锚点定义也相同。

`n_rollback_sign` = 锚点的 `before_text` 与锚点的 `after_text` 不同，且锚点之后、仍在窗口内，有一条产品确认行的 `after_text` 等于锚点的 `before_text`。这样的 `claim_id` 数。

退回到确认前正文，必然也是一次 `after_text` 的改变。该主张同时进入 `n_edit` 与 `n_rollback_sign`。两行都报，不互减。

锚点本身没有改字（`before_text` 与 `after_text` 相同）时，后一行写成同一段文字不算回滚迹象。

---

## 4. 排除

下列各项不进入任何一行的分子或分母。

| 排除 | 原因 |
|------|------|
| `propose_patch` 的草案、`discard_patch_draft` | 不改正文，不写正式 `patch_events` |
| `arm=C` 的行，以及缺 `before_text` / `after_text` 的旧人审记账行 | 不是产品确认。V1 人审行本来就可以不写正文 |
| 未写入正式 `patch_events` 的正文改动 | 本页只读 JSONL。看不见的改动不把整格改成 0，也不另开采集器 |
| `reviewer_note` 里的「撤销」「回滚」等字样 | 不解析备注当信号 |
| 宽表 A6 再验失败、再验得到的 fresh/stale/unknown | 那是再验结果。不是回改，也不是回滚迹象。A6 仍留在 #508 宽表，本页不收编、不改号 |
| `latch_log.action=rerun` | 只是 `rerun_log` 的影子，不进再审分母 |
| `override` 为空的 `discard` / `renew` | 不能当作再审模式的成功行。窗内有人审、但没有任何一行带上 0/1 时，再审这一格写「未计」 |
| eval 模式 | ADR-0006：评测路径代码级跳过 HumanLatch。没有行就是没有行，不拿评测轨迹补 |
| 金标、Hard-Gold id、`gold.json`、路线 Y 的正式生成 | 不进分母，不进分子 |
| SLI 1/2 的误放误拒、SLI 4 的 `c2_rate`、P1 忠实、P3 一致率 | 只读并排。数字留在各自的页 |
| git revert、RESULT-Y 的丙、任何「改判」句子 | 不是补丁账本上的 `after_text` |

未列信号（点赞、停留、导出次数、显式评分、情绪）整行写「未计」。不为本波临时加第六个字段名。

---

## 5. 未计与样本不足

| 情形 | confirm 后回改 | 重开 | latch 再审 | 补丁回滚迹象 |
|------|----------------|------|------------|----------------|
| 窗口不可划定 | 样本不足 | 样本不足 | 样本不足 | 样本不足 |
| 该行账本不可读 | 未计 | 未计 | 未计 | 未计 |
| 确认行都缺成对正文 | 未计 | 按重开自己的账 | 按再审自己的账 | 未计 |
| 有人审行但 `override` 都空 | 按确认自己的账 | 按重开自己的账 | 未计 | 按确认自己的账 |
| 账本已读，分母为 0 | 样本不足 | 样本不足 | 样本不足 | 样本不足 |
| 账本已读，分母大于 0，分子为 0 | `0`，备注「账本已读」 | 同左 | 同左 | 同左 |
| 重开的行不在作废名单 | — | 分列不一致 | — | — |
| 信号不在 §1 四行里 | — | — | — | 未列信号 = 未计 |

「未计」不是 0。「样本不足」不是 0。只有「账本已读」且分母大于 0 时，分子 0 才写 `0`。

`events.jsonl` 不可读时，回改与回滚迹象一起写「未计」。`rerun_log` 或 `invalidation_list` 有一张不可读时，重开写「未计」，不单用另一张报比率。`latch_log` 不可读时，再审写「未计」。

窗口不可划定时，整句抄：

```text
本周样本不足：窗口不可划定（Asia/Shanghai）。confirm 后回改、重开、latch 再审模式、补丁回滚迹象都写「样本不足」。未列信号写「未计」。不写成 0。弱信号不是金标，不进生产 score，不改判丙。
```

账本不可读时，整句抄。尖括号换成不可读的账本名。

```text
<账本>不可读。对应信号写「未计」。未计不是 0。不拿金标、不拿 RESULT-Y、不拿评测轨迹补数。弱信号不是金标，不进生产 score。
```

账本已读、分母大于 0、分子为 0 时，整句抄：

```text
账本已读。窗口 <起止 · Asia/Shanghai>。该信号分母大于 0，分子为 0。这个 0 是读到的行数。未列信号仍写「未计」。这个 0 不是金标，不是放行成功，不改判丙。
```

分母为 0 时，整句抄：

```text
账本已读。窗口 <起止 · Asia/Shanghai>。该信号分母为 0，格子写「样本不足」。不写成 0。弱信号不是金标，不进生产 score。
```

本页当前不预填分子。样例字段因此不出现整数计数。见 [`docs/evidence/slo-phase2/P6-样例字段.md`](../evidence/slo-phase2/P6-样例字段.md)。

---

## 6. 弱信号 ≠ 金标

这四行回答的是「下游有没有再发生一件事」。它们不回答「这件事对不对」。

同时成立的读法：

- 回改变多，只说明确认后的正文又被确认成了另一段文字。  
- 重开变多，只说明作废主张又被打开去重跑。  
- 再审变多，只说明同一主张在窗内被成功人审了不止一次。ADR-0023：override 不是模型变好。再审也不是。  
- 回滚迹象变多，只说明后一次 `after_text` 回到了锚点的 `before_text`。它不是「补丁被判定为错」的金标。  
- 分子为 0 且备注写了「账本已读」，只说明这四行的账上没有对应主张。它不是放行成功，不是忠实，不是乙。  
- 生产放行是否成立，仍看既有硬闸（无证拒拦、未确认不出门、自红转绿、无 T1 绿灯）。那些谓词的语义在 ADR-0042。本页不改 `src/` 闸。  
- 本页不把某一计数写进 [`生产补丁放行SLO.md`](生产补丁放行SLO.md) §4 的预注册门槛，也不写进 `RESULT-Y` 的成立格。

事后补一条「回改低于 X 即通过」或「回滚迹象为 0 即改判丙」来凑绿 = 本页作废，须另决议。

---

## 7. 人审动词

HumanLatch 动词封闭集仍是 `discard` | `renew`（ADR-0006 · ADR-0023）。`VALID_ACTIONS` 仍是这两项。

| 词 | 在本页的身份 |
|----|----------------|
| `discard`、`renew` | 唯一的人审动词。再审模式只数这两类成功行 |
| `override` | 写入时派生的 bool。不是动词。谓词仍按 ADR-0023，本页不改 |
| `rerun` | 已有的审计字符串，挂在 `rerun_log` 旁边。不是第三动词。重开只数 `rerun_log` |
| `reopen`、`rollback`、`rereview`、`rewrite` | 本页的 Watch 字段或日常说法。不进入 `VALID_ACTIONS`，不新做按钮 |

序列备注里的 `discard→renew` 是两次既有动词的先后，不是一个新 action。

---

## 8. 与 min-6 抽检、override 只读互指

两页都只读。本页不改它们的列，不把四行的数写回去。

| 页 | 它回答的事 | 本页不做什么 |
|----|------------|----------------|
| [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md)（SLI 1/2 · #558 · Parent #556） | 同一窗口的误放与误拒 | 不把回改或回滚迹象写入 `b2_rate` / `b3_rate`。回改不是误放标签 |
| [`人审-override周报.md`](人审-override周报.md)（SLI 4 · #559 · Parent #556） | 已带 override 标签的人审行里，人推翻机器判定的比率 | 不把 `n_rereview` 写入 `c2_rate`。再审不是 override rate |
| [`旁表-人机校准.md`](旁表-人机校准.md)（P3 · #573 · Parent #569） | 同窗可配对样本的一致率与分歧谱 | 不把再审序列写成校准绿灯 |
| [`抽检-主张忠实.md`](抽检-主张忠实.md)（P1 · #571 · Parent #569） | 主张粒度的忠实抽检 | 不把弱信号当成忠实分 |

#556 仍 OPEN。上表里 Parent 为 #556 的两页留在 min-6 track。本页不挂到 #556 下面。

---

## 9. 叙事

可接受的观测叙事：

- 「同一窗口：四行弱信号另表。回改的分母是 `n_confirm`。账本不可读则写未计」  
- 「作废主张本窗有 rerun_log。这是重开计数。按钮仍是重跑作废主张」  
- 「同一主张有两条成功 renew。这是再审模式。不是新动词，也不是模型变好」  
- 「后一次 after_text 回到 before_text。回改与回滚迹象两行都计，不互减」  
- 「未列信号写未计。未计不是 0」

不可接受的叙事：

- 「没有回滚迹象，所以这趟放行成功」  
- 「回改少了，所以主张是真的」或「回改多了，所以模型变差，丙可以改判」  
- 「再审两次，所以 override 已经达标」  
- 把 `reopen` 或 `rollback` 加进 `VALID_ACTIONS`  
- 用金标条、`gold.json` 或路线 Y 的生成补分子  
- 解析 `reviewer_note` 或 git revert 来填回滚迹象  
- 任何把本页数字写成实验成立、或拿来改判路线 Y 的句子

---

## 10. 周报表格（最小列）

填入 [`docs/evidence/slo-phase2/周报附录骨架.md`](../evidence/slo-phase2/周报附录骨架.md) 的 P6 行。只抄摘要。禁止把数字写入 min-6 的六个主格。禁止把数字写入 `RESULT-Y` 成立格。禁止写「接近乙」。本骨架不预填分子。

| 信号 | 计入规则（摘要） | 数值 | 分母 | 备注 |
|------|------------------|------|------|------|
| confirm 后回改 | 窗内后一次产品确认的 `after_text` 与锚点不同 | `<未填>` | `n_confirm=<未填>` | 不进 score |
| 重开 | 窗内 `rerun_log` 的去重主张 | `<未填>` | `n_void_eligible=<未填>` | 影子行不另计 |
| latch 再审模式 | 同主张 ≥2 条成功 `discard`\|`renew` | `<未填>` | `n_latched=<未填>` | 序列可写「序列未计」 |
| 补丁回滚迹象 | 后一次 `after_text` 等于锚点 `before_text` | `<未填>` | `n_confirm=<未填>` | 与回改不互减 |
| 未列信号 | 不在上四行 | 未计 | — | 禁止写成 0 |

机检一块（占位，禁止填假数字）：

```text
window=<起止 · Asia/Shanghai> post_confirm_edit=<n_edit/n_confirm|未计|样本不足|0 账本已读> reopen=<n_reopen/n_void_eligible|未计|样本不足|分列不一致|0 账本已读> latch_rereview=<n_rereview/n_latched|未计|样本不足|0 账本已读> patch_rollback_sign=<n_rollback_sign/n_confirm|未计|样本不足|0 账本已读> unlisted=未计 notes=弱信号≠金标；不进生产 score；不升硬闸；动词仍是 discard|renew
```

---

## 11. 账本指针（只读）

| 指针 | 用途 |
|------|------|
| `data/patch_events/events.jsonl` | 产品确认行。`append_product_confirm`：`arm=T`，`human_confirm`，成对 `before_text` / `after_text`。本票不编辑写入路径 |
| `invalidation_list` | 作废名单单一真相（ADR-0006）。只作重开的存量分母 |
| `rerun_log` | 重开的分子。列：`ts`、`claim_id`、`thread_id`、`verdict`、`nth`、`note` |
| `latch_log` | 再审的取数口。成功行的 `action` 只计 `discard` \| `renew`，且 `override` 为 0 或 1。`action=rerun` 是影子 |
| `src/freshlatch/gates/human_latch.py` | `VALID_ACTIONS = ("discard", "renew")`。本票不编辑 |
| [`docs/adr/0006-humanlatch中断机制与作废续命闭环.md`](../adr/0006-humanlatch中断机制与作废续命闭环.md) | 重跑、人审日志、eval 跳过。本票不改该 ADR |
| [`docs/adr/0023-batch5-override派生标签与latch_log扩列.md`](../adr/0023-batch5-override派生标签与latch_log扩列.md) | 不新增 action。override 是派生标签。本票不改该 ADR |
| [`生产观测phase2-索引.md`](生产观测phase2-索引.md) | P6 成员行。本页是协议正文 |
| [`docs/evidence/slo-phase2/周报附录骨架.md`](../evidence/slo-phase2/周报附录骨架.md) | P6 摘要行 |
| [`docs/evidence/slo-phase2/P6-样例字段.md`](../evidence/slo-phase2/P6-样例字段.md) | 空表。不预填 |
| ADR-0042 | 实验—生产防火墙。放行谓词不因本页改写 |

聚合结果不回写为放行特征，不进入生产 score，不改 `compare_primary`，不改实验预注册。

---

## 12. 样例字段

空表在 [`docs/evidence/slo-phase2/P6-样例字段.md`](../evidence/slo-phase2/P6-样例字段.md)。尖括号是占位，不是测量值。那一页的四行不出现整数分子。未列信号写「未计」。

诚实句抄 §5。不称乙。

---

## 13. 非目标

- 把弱信号写进生产 score、在线放行器、`compare_primary` 或金标  
- 把四行升成硬闸、乙尺，或 RESULT-Y / PREREG-Y / SESOI 的改判信号  
- 新增 `discard` / `renew` 以外的人审动词；把 `override`、`reopen`、`rollback`、`rereview` 做成 action  
- 改写 min-6 六个主格，或把 `n_edit` / `n_rereview` 写入 B2、B3、C2  
- 把本页挂进 #556；#556 仍 OPEN  
- 合并 #508–#515，或合并本协议所在 PR（No merge until Matt+human）  
- 编辑 `RESULT-Y` / `PREREG-Y` / `formal-generations-y` / SESOI / \(k_{\min}\) / Cond / 选取 R  
- 占用或覆盖 ADR-0034；改 ADR-0006、ADR-0023 的动词决议  
- 新写聚合脚本；改 `src/` 放行谓词或 `VALID_ACTIONS`  
- 解析 `reviewer_note`、git revert 或再验失败来填这四行  
- 把未列信号写成 0；用跨窗账本补本周分子  
- 把本页称作实验成立或主实验成功

---

## 14. 本页自检

- [x] 信号清单四行 + 未列信号；每行有计入与排除  
- [x] 账本不可读、正文不成对、override 全空、未列信号：写「未计」；未计不是 0  
- [x] 分母为 0 写「样本不足」；只有账本已读且分母大于 0 时分子 0 才写 0  
- [x] 弱信号 ≠ 金标；不进生产 score；不升硬闸 / 乙尺 / RESULT-Y 改判  
- [x] 未新增人审动词；`VALID_ACTIONS` 仍是 `discard` \| `renew`；重开计的是既有 `rerun_log`  
- [x] 回滚迹象与回改不互减；回滚不是新动词  
- [x] 只读互指 ADR-0006、ADR-0023、phase-2 索引、周报附录 P6、min-6 抽检与 override  
- [x] Parent 是 #569；未挂到 #556；#556 仍 OPEN  
- [x] 防火墙是 ADR-0042，不是 ADR-0034  
- [x] 未合并 #508–#515；未改 RESULT-Y；未称乙；未 rewrite min-6 主列  
- [x] 未改 `src/`
