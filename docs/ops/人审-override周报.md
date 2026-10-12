# 人审协议：HumanLatch override 周报（SLI 4 · C2）

> **生产观测 ≠ 乙尺。**  
> **≠模型变好 / ≠验收绿灯**（ADR-0023）。override rate 不作验收绿灯，也不作模型变好的信号。  
> 本页是 SLO-min6 T3（[#559](https://github.com/luxingjiang1993/FreshLatch/issues/559) · Parent [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556)）的 HumanLatch override 周报协议。SLI 4 = C2 override rate。C1 用户作废率只作旁注。  
> 交付真源是 #556 / #559 与本页，以及 [`生产观测最小6-索引.md`](生产观测最小6-索引.md)。未合并的 [#511](https://github.com/luxingjiang1993/FreshLatch/pull/511) 仍是 candidate draft，不是第二套交付真源。  
> Provenance：**adapt** from #511 head `cursor/slo-06-c1-c2-latch-rates-8a67` @ `70286694b30bf2d06df863b4a48e2ff3447b9644` 的 C2 聚合定义（`scripts/slo_c1_c2_latch_rates.py` 的 `aggregate_c2`；C1 的 `aggregate_c1` 只旁注）。宽 SLO-06 收口为本页的最小 6 周报，不另起平行 KPI 名。本分支不合入该脚本，也不合入其单测。  
> **本变更未编辑** `RESULT-Y` / `PREREG-Y` / SESOI / \(k_{\min}\) / Cond / 选取 R。未改 `src/` 放行谓词，未改 `src/freshlatch/gates/human_latch.py` 动词集。金标不进生产 score。未实现、未调用 `compare_primary`。  
> 防火墙：ADR-0042。#511 / #508 草案曾写 ADR-0034；tip 上该号已被 `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md` 占用，本页引用 ADR-0042，不覆盖。硬继承只读：ADR-0023 · ADR-0006。  
> `#511` **Keep candidate · No merge until Matt**。本协议所在 PR 同样不合并，直到 Matt 审。  
> 日期：2026-10-12（Asia/Shanghai）。落地基线 `e926a0b4c75f89a8eacfe87e327c7d2c7c6d9e38`（含 #564）。路线 Y 结果丙的只读锚仍是 `2a3fadd`。  
> 禁止把本页称作：乙、软乙、接近乙、主实验成功。生产变绿不得改判丙。

层身份：观测 / Watch。本页数字不作本波 Gate 生死，不锁 Override Rate 通过线（ADR-0023）。

---

## 0. 目的

同一周报窗口里看见人推翻机器判定的比率，并看见分母。比率高低只表示人机分权是否被记下来，不表示模型变好或变差。

| 要看见的 | 不在本页交付 |
|----------|----------------|
| C2 override rate，分子与分母同时出现 | 把 override rate 写成验收绿灯或模型变好 |
| 分母可操作：`latch_log` 里已带 override 标签的人审行 | 新增 HumanLatch 动词，或把 `override` 做成第三个 action |
| 分母为 0 时写「样本不足」 | 把缺样本写成 0% |
| C1 作废率作为旁注 | 把 C1 升成最小 6 的第二个主字段，或另起平行 KPI 名 |
| 只读 `latch_log` | 改 `src/`、改闸语义、回写路线 Y 成立格、把金标写进生产 score |

judge–human calibration 留在 phase-2 旁表 [`旁表-人机校准.md`](旁表-人机校准.md)（[#573](https://github.com/luxingjiang1993/FreshLatch/issues/573) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)），不进本页主行。那一页与本页分列：它报同窗可配对样本上的一致率和分歧谱，不改下面 §5 的 C2 列。与 C2 的差写在那一页 §1.1，不在本页重写 C2。

---

## 1. 字段定义（C2）与分母

窗口内的人审行，指 `latch_log.action` 为 `discard` 或 `renew` 的行。动词封闭集仍是这两项（ADR-0023 · ADR-0006）。`override` 是写入时派生的 bool 标签，不是动词。

| ID | SLI | 名称 | 操作定义 | 分子 / 分母 | 层 |
|----|-----|------|----------|-------------|-----|
| **C2** | 4 HumanLatch override | Override rate | 已带派生标签的成功人审里，人推翻机器判定的行占比 | `override=1` 的人审行数 / `override` 为 0 或 1 的人审行数 | 观测/Watch |

定义句（与 #511 `aggregate_c2` 同义，收口到本页）：时间窗内 `latch_log.override=1` 的人审行数 / `override` 为 0 或 1 的人审行数。分母 = 带派生标签的成功人审事件，也就是 `latch_log` 可计事件。

### 1.1 分母细则

- **可计事件** = 窗口内 `action` 为 `discard` 或 `renew`，且 `override` 列已经写成 0 或 1 的 `latch_log` 行。这就是 C2 分母 `override_labeled_n`。  
- **分子** `override_true_n` = 上述行里 `override=1` 的行数。比率 = 分子 / 分母。  
- `action` 不是 `discard` 或 `renew` 的行（含 `rerun`）不进人审集合，也不进 C2 分母。  
- `override` 列缺失或为空的人审行不进分母。缺列不得改记成 0 来压低比率。  
- 失败落档与幂等跳过不新增人审行（既有写路径的行为，本页不改）。它们不进分母。  
- 分母为 0 时，C2 写「样本不足」。禁止记成 0、0.0 或 0%。  
- 金标、Hard-Gold id、实验臂、生产 score、在线放行器分数不能充当本分母，也不能充当入样键。

### 1.2 派生标签谓词（只读 · 不在本页重写代码）

ADR-0023 已钉死的写入谓词，本页只引用：

- `discard` 且 `machine_status_before == fresh` → `override` true  
- `renew` 且 `machine_status_before` 为 `stale` 或 `unknown` → `override` true  
- 其余成功人审 → `override` false  

周报按库里已经写下的标签计数。本页不新增动词，不把 `override` 收进 `VALID_ACTIONS`，不改 `src/freshlatch/gates/human_latch.py`。

### 1.3 C1 作废率（旁注-only）

C1 可以出现在同一周报，身份是旁注。它不是 SLI 4 的主字段，也不新编一个最小 6 编号。

旁注定义（与 #511 `aggregate_c1` 同义）：时间窗内 `latch_log.action=discard` 的去重 `claim_id` / `action` 为 `discard` 或 `renew` 的去重 `claim_id`。分母是人审主张数，不是 C2 的行分母。

旁注可以另列两笔交叉计数，它们都不是比率分母：

- `discard` 且 `machine_status_before=fresh` 的去重主张数  
- `invalidation_list` 的条数（作废名单交叉；#511 脚本按全库计数，周报若抄这个数，必须注明「非窗口分母」）

C1 分母为 0 时同样写「样本不足」，禁止写成 0%。C1 升高或降低都不构成验收绿灯。

---

## 2. 窗口

- **窗口**：过去 7 个自然日，或本发布列车窗口。周报写明起止，时区 Asia/Shanghai。C2 主字段与 C1 旁注使用这同一个窗口。  
- **频率**：每周（或每发布列车）一轮。  
- **半开区间**：若用日历周，`start` 含当日，`end` 不含结束日。指定起始日且未写结束日时，结束日 = 起始日 + 7 天。这与 #511 候选聚合的窗口注记同义；本页不把未合并脚本的命令写成 tip 上的操作步骤。  
- 未跑、库不可读、或窗口内没有可计行时，走 §3。禁止编造比率。

本页不设完成量门槛，也不锁通过线。起步姿态是先把分母报出来。

---

## 3. 样本不足

`override_labeled_n` 为 0，或本周没有可计的人审行时，周报使用下面的句式。C2 格子写「样本不足」。禁止把该格写成 0%、0.0 或 0。

```text
本周样本不足：override 已标注的人审行 override_labeled_n=0，不报 C2 点估计；格子写「样本不足」。声明仍为：≠模型变好 / ≠验收绿灯。
```

C1 旁注分母为 0 时，C1 格子同样写「样本不足」，C2 格子按自己的分母单独填写。缺 C1 不删 C2；缺 C2 不拿 C1 顶上。

同时禁止：

- 分母为 0 时宣称 override 已达标，或宣称本波 Gate 通过  
- 用金标条、实验固定 k 或生产 score 补分母  
- 把「样本不足」改写成 0% 以便看起来平稳  

---

## 4. 文首声明（ADR-0023）

每份抄了本协议数字的周报，文首保留下面这句：

```text
≠模型变好 / ≠验收绿灯（ADR-0023）。override rate 不作验收绿灯。生产观测 ≠ 乙尺。
```

可接受的观测叙事：

- 「同一窗口内 override rate = override_true_n / override_labeled_n，只记录人机分权」  
- 「本周 override 已标注人审行为 0，C2 写样本不足，不报点估计」

不可接受的叙事：

- 「override 少了，所以模型变好」  
- 「override 多了，所以验收通过」或「override 少了，所以验收通过」  
- 「作废率下来了，所以可以放行」（C1 是旁注）  
- 任何把本页数字写成实验成立、或拿来改判路线 Y 的句子

本波 C2 为观测/Watch。升 Gate 或锁定通过线须另决议，并事先锁定判据。ADR-0023 明确本批不锁 Override Rate 通过线。

---

## 5. 周报表格（最小列）

填入 [`docs/evidence/slo-min6/周报骨架.md`](../evidence/slo-min6/周报骨架.md) 的 SLI 4 格，以及 [`生产补丁放行SLO.md`](生产补丁放行SLO.md) §6 的 C2 行。只抄摘要。禁止把数字写入 `RESULT-Y` 成立格。禁止写「接近乙」。本骨架页不预填比率。

| 列 | 说明 |
|----|------|
| `window` | 起止，Asia/Shanghai |
| `override_true_n` | 分子：`override=1` 的人审行数 |
| `override_labeled_n` | 分母：`override` 为 0 或 1 的人审行数。为 0 则 C2 写「样本不足」 |
| `c2_rate` | override rate = 分子 / 分母。不足则「样本不足」，禁止 0% |
| `声明` | ≠模型变好 / ≠验收绿灯（ADR-0023） |
| `c1_discard_claim_n` | 旁注分子：窗口内 discard 的去重主张数 |
| `c1_reviewed_claim_n` | 旁注分母：窗口内 discard 或 renew 的去重主张数。为 0 则 C1 写「样本不足」 |
| `c1_rate` | 旁注-only。不得作为成功格，不得顶替 C2 |
| `notes` | 写明未新增动词；若抄了 `invalidation_list` 条数，注明它不是分母 |

上表列到此为止。不新增一致率列、六格列或方向列。

### 5.1 与 P3 旁表分列（不占上表）

judge–human calibration 的协议在 [`旁表-人机校准.md`](旁表-人机校准.md)。摘要进 phase-2 周报附录的 P3 行，不进上表。

上表的 `c2_rate`、`override_true_n`、`override_labeled_n` 仍只服务 SLI 4。不把一致率、分歧谱或方向计数写进这些格子。

C2 是已标注人审行上的单一 override rate。P3 是可配对样本上的谱。分母可以不同。一致率不是本页的 `c2_rate`，也不是用 `1 - c2_rate` 填出来的验收格。本页不把 P3 升成 Gate，不新增 HumanLatch 动词。

---

## 6. 账本指针（只读）

| 指针 | 用途 |
|------|------|
| `latch_log` | C2 与 C1 的取数口。列：`ts`、`claim_id`、`action`、`evidence_id`、`actor`、`machine_status_before`、`override`、`run_id`、`reviewer_note`（后四列见 ADR-0023） |
| `invalidation_list` | 作废名单单一真相（ADR-0006）。只作 C1 旁注的交叉计数，不是 C2 分母 |
| `src/freshlatch/gates/human_latch.py` | 动词封闭集的只读锚：`discard` \| `renew`。本票不编辑 |

聚合结果不回写为放行特征，不进入生产 score，不改 `compare_primary`，不改实验预注册。

[#511](https://github.com/luxingjiang1993/FreshLatch/pull/511) 上的 `scripts/slo_c1_c2_latch_rates.py` 是上述字段的候选只读聚合。它留在该 draft，head 仍为 `70286694b30bf2d06df863b4a48e2ff3447b9644`。tip 上没有这个脚本。本页不把它的命令写成当前分支的操作步骤。

---

## 7. 非目标

- 合并 #511，或合并 #508–#510、#512–#515  
- 把 `scripts/slo_c1_c2_latch_rates.py` 或其单测合进本分支  
- 新增 HumanLatch 动词；编辑 `src/freshlatch/gates/human_latch.py` 的动词集；把 `override` 做成 action  
- 锁定 Override Rate 通过线；把 C2 升为本波 Gate  
- 把 C1 升成最小 6 的主字段，或另起一套作废 / override KPI 名  
- 编辑 `RESULT-Y` / `PREREG-Y` / `formal-generations-y` / SESOI / \(k_{\min}\) / Cond / 选取 R  
- 实现或调用 `compare_primary`；改 `src/` 放行谓词  
- 把金标放进生产 score 或在线放行器  
- 实现 T4–T6（#560–#562）  
- 新建 `tasks/SLO-06.md` 把宽表票升成第二真源（指针只在 `tasks/SLO-INDEX.md`）  
- 把 judge–human calibration 从 phase-2 升进本页（§5.1 只互指旁表，不把 P3 数字写入 §5 主列）
