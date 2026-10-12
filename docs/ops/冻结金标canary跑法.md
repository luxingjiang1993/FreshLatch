# 冻结金标 canary 跑法（SLI 6 · frozen gold canary pass rate）

> **生产观测 ≠ 乙尺。**  
> **Canary ≠ 乙尺。**  
> 本页是 SLO-min6 T6（[#562](https://github.com/luxingjiang1993/FreshLatch/issues/562) · Parent [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556)）的离线 canary 跑法协议。SLI 6 的主名只有 **frozen gold canary pass rate**。  
> 交付真源是 #556 / #562 与本页，以及 [`生产观测最小6-索引.md`](生产观测最小6-索引.md)。未合并的 [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) 仍是 program draft，不是第二套交付真源。  
> Provenance：**new**（本 ops canary 跑法）+ **adapt**（只读摘）[#515](https://github.com/luxingjiang1993/FreshLatch/pull/515) head `cursor/slo-07-d1-d4-observability-857a` @ `29c57b737133810a5e632832f681910971d46fce` 的 SLO-07 **D1/D5** 口径。`#515` **Defer · 本波不合并**。不合入其 `src/freshlatch/slo_d1_d4_observability.py`、`scripts/slo_d1_d4_observability.py` 或测试。  
> 对照（不新建主名）：arXiv **2608.26385** 的冻结 canary 集、版本针、pass rate；Confident AI 的 canary / regression 习惯。字段落在本页的 pass rate 与 pin 上。不新建 Confident-* 主 KPI 名，不把 regression 另立为本波第 7 个主 SLI。  
> **本变更未编辑** `RESULT-Y` / `PREREG-Y` / SESOI / \(k_{\min}\) / Cond / 选取 R。未改 `src/` 放行谓词，未改闸语义。金标不进生产 score，不进在线放行器。未实现、未调用 `compare_primary`。  
> 防火墙：ADR-0042。#508 草案曾写 ADR-0034；tip 上该号已被 `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md` 占用，本页引用 ADR-0042，不覆盖。Hard-Gold 骨架只读对照 ADR-0032 / ADR-0033。  
> `#508` **Keep draft · No merge until Matt**。`#515` **Defer · 不合并**。本协议所在 PR 同样不合并，直到 Matt 审。  
> 日期：2026-10-12（Asia/Shanghai）。落地基线 `642733bc97ff1fa7183aeb21aa68f4651b327f6d`（含 #567）。路线 Y 结果丙的只读锚仍是 `2a3fadd`。  
> 禁止把本页称作：乙、软乙、接近乙、主实验成功。生产变绿不得改判丙。canary 掉线不得改判丙。

层身份：离线 canary。本页数字不作本波 Gate 生死，不改生产放行谓词，不把 pass rate 写进在线放行器。

版本针的预锁记录在 [`docs/evidence/slo-min6/canary-pin.md`](../evidence/slo-min6/canary-pin.md)。那一页只钉集与 pin，不填 pass rate。

---

## 0. 目的

在发布列车之前，或在周报窗口里，用一份事先钉死的金标子集看主业有没有掉到当前金标门以下。看见的是这一份冻结集上的通过率，不是生产看板变绿，也不是路线 Y 的成立格。

| 要看见的 | 不在本页交付 |
|----------|----------------|
| 冻结 canary 集的大小，以及 code pin / dataset pin | 跑完之后再换集、换门 |
| 发布前或周跑的 pass rate | 把该率写进生产 score 或在线放行器 |
| 掉到当前金标门以下 → 停发列车讨论 | 把掉线写成 RESULT-Y 改判信号，或回写 Y |
| 只读摘 #515 的 D1/D5 口径 | 本波合并 #515，或合入其脚本与 `src/` |
| 对照 arXiv 2608.26385 与 Confident AI 的 canary / regression 习惯 | 新建 Confident-* 或另一套主 KPI 名 |

---

## 1. 冻结 canary 集

本波 SLI 6 的分母只有一套集。主名不拆成两个率。

| 项 | 预锁 |
|----|------|
| 文件 | `data/eval/gold.json`（只读） |
| dataset pin / canary_pin | git blob `c7a14683de82bb795fd67bbb505bd6f7128b7c2a`（tip `642733bc97ff1fa7183aeb21aa68f4651b327f6d` 上该文件的 blob，与 `git rev-parse HEAD:data/eval/gold.json` 一致） |
| 桶 | `must_stale` |
| 成员 | `c1`、`c2`、`c3`、`c7` |
| 集大小 | 4 |

这四条是主张金标里「必须判死」的桶，不是检索 Hard-Gold 的 20 条。集大小 = 该 pin 上 `must_stale` 的条数。周报写这个大小。禁止把别的桶（`must_fresh`、`must_unknown`、`must_fresh_distractor`）并进分母来改大小。

预锁先于任何 pass rate。本页不填通过率。事后改成员、改桶或改门来凑绿 = 本页作废，须另决议。

`data/eval/retrieve_hard_gold.json`（blob `615eeca6aa04752842513f3594b14841985e7531`，`version=v0`，`level=hard_gold_skeleton`，n=20）**不**进入这个分母。理由在 §7。

---

## 2. 版本针

每次 canary 开跑之前写下两根针。跑完不得改写。

| 针 | 写什么 | 不写什么 |
|----|--------|----------|
| dataset pin（周报列名 `canary_pin`） | 实际读取的金标文件的 git blob，加桶名 `must_stale`。与 §1 预锁不一致则本跑作废，先停，不改门 | 用 pass rate 反推「当时大概是哪一版金标」 |
| code pin | 实际执行的代码 git sha（完整 40 位） | 把本协议的落盘基线 `642733bc97ff1fa7183aeb21aa68f4651b327f6d` 填进「已跑」行。那是文档切出点，不是一次 canary 执行 |

索引附录里的 version tags 仍是 phase-2。这两根针是 SLI 6 的占位，不把 version tags 升成主 SLI。

若该次调用了既有的 LLM 金标入口，逐遍另记 model、temperature、seed、日期（Asia/Shanghai）。`temperature=0` 时 seed 不构成独立样本，多遍相同结果不得当成多次独立证据。本协议不发起这种跑，不改 `src/freshlatch/eval/`。托管端点会漂移，跨会话复现只能是近似的；这个限制写在当周 notes，不写进生产 score。

---

## 3. pass rate

发布前一轮，或每周一轮（窗口：过去 7 个自然日，或本发布列车窗口；时区 Asia/Shanghai）。未跑写「未跑」。

沿用 #515 D1 写死的遍数：**N = 3**。N=3 小于 30，文首框定为**冒烟检查**，不报总体方差，不报统计显著。这是冒烟读数，不是测量结论。单次运行（N=1）不得用来宣布过门或掉线已定性；要报掉线，三遍都要有记录。禁止为了凑独立样本把 `temperature` 留在 0 还宣称换了 seed。

一门（D1，不得低于当前金标门）：

- 期望判定 = `stale`（与 `src/freshlatch/eval/matrix.py` 的 `EXPECTED_VERDICT["must_stale"]` 一致；本票不改该文件）
- 某一遍的 hits = 该遍里判定等于 `stale` 的 `must_stale` 条数
- 缺判记 missing，不算命中
- 该遍过门 ⟺ `hits == |must_stale|`（本冻结集上即 hits == 4）
- 低于这一门 = 掉线。本页不另设百分数门槛

pass rate = 过门遍数 / N。

D5 明细（同一率的附表，不是第二个主名）：每个 id 的 pass@k = 该 id 被判为 `stale` 的遍数 / N。用来防止只看单次幸运绿。周报主格仍叫 pass rate。禁止把 pass@k 登记成另一条主 KPI。

n 即使以后加大到 ≥30，本页仍只报 pass rate、过门遍数与 pass@k 明细，不报总体方差。方差要另决议，并事先声明那是哪一层测量。

机检一行（占位，禁止填假数字）：

```text
pass_rate=<过门遍数/N|未跑|样本不足> canary_pin=<blob>|must_stale code_pin=<sha|未跑> canary_set_size=<|must_stale|> drop=<未跑|未掉线|停发列车讨论>
```

人读表格与上面这行是同一组数。

| 情形 | pass rate |
|------|-----------|
| 这一窗或这一趟发布没有跑 | 未跑。禁止写 0、0%、100% 或 1 |
| dataset pin 对不上 §1 的 blob，或 `|must_stale|` 不是 4 | 样本不足。先停。禁止改集之后照报 |
| N 不足 3，或某一遍没有逐条判定 | 未跑。禁止用跑完的那一遍外推成 3 遍 |
| 三遍都在，且每遍 hits == 4 | 3/3。notes 写明：冒烟，不报总体方差。这不是放行成功，也不是实验成立 |
| 三遍都在，且至少一遍 hits < 4 | 过门遍数/3。掉线处置走 §6 |

分母大于 0 且确实三遍都全中时，写 `3/3`，不要写成「已过乙」或「可以发车」。全中只说明这三遍冒烟没有低于当前金标门。

本票不新增跑法脚本，不把 `python -m freshlatch.eval run --gold` 放进 CI，不调用它。那条入口若由人在里程碑上手动使用，结果仍只进离线周报，并经 §2 的两根针对上本页。本票不生成该结果。

---

## 4. 只读摘 #515 的 D1/D5

摘的是口径，不是票，不是代码。

| ID | 摘来的句子 | 落在本页 |
|----|------------|----------|
| D1 | 离线评测层。must_stale multi-run。不得低于当前金标门：每遍全命中（hits == \|must_stale\|，期望判定 stale）。默认 3 遍。n 小不报总体方差。金标只读 | §1 的集、§3 的门与 N=3 |
| D5 | 同金标多跑的 pass@k，外加方差的诚实框定。防单次幸运绿 | §3 的明细列。不升主名 |

不摘进本 SLI 主行的：D3 无 T1 绿灯（硬闸，目标 0，仍在宽表与 defer 的 #512）、D4 包结论分布（观测，不是 canary 率）。#515 票面还写了 D3/D4 的脚本出口；那些留在未合并的草稿里。

`#515` 保持 OPEN draft，`merged=false`。本波不合并。不把它的周报样例 `reports/slo/d1_d4_week.md` 抄进本分支，避免把一份冒烟样例当成已经跑过的 pass rate。

---

## 5. 金标只读

- 不写 `data/eval/gold.json`，不改 `must_stale` 成员来换门。  
- canary 使用的标签只出现在离线读取与周报。生产 score 与在线放行器不读这些标签。  
- #515 草稿里列出的生产路径（`publish_hook.py`、`prepublish.py`、`evidence_bound.py`、`disposition.py`、`sheet.py`、`claim_ledger.py`、`export`、`ui/app.py`）不得把 `gold.json`、`load_gold` 或 `must_stale` / `must_fresh` / `must_unknown` 当作放行特征。本票不新增扫描脚本，也不改这些文件。  
- 周报数字只写 [`docs/evidence/slo-min6/周报骨架.md`](../evidence/slo-min6/周报骨架.md) 或当周副本。禁止写入 `RESULT-Y` 成立格。

---

## 6. 掉线 → 停发列车讨论

掉线 ⟺ 按 §3 已经跑满 3 遍，且至少一遍 `hits < |must_stale|`。

当周「掉线处置」写：**停发列车讨论**。含义是：这一趟发布列车先停下来，由人讨论能不能发。讨论记录写在周报 notes。本页不把讨论结果自动写成放行或拒发。

同时成立的读法：

- 掉线是发布风险。  
- 掉线不是 RESULT-Y 的改判信号。不得据此把丙改成别的成立格，不得回写 `PREREG-Y`。  
- 掉线不是生产放行谓词的输入。`src/` 闸语义保持原样。  
- 未跑不是掉线，也不是过门。未跑保持「未跑」。  
- `3/3` 不是放行绿灯，不是验收绿灯，不是实验成立。

停发讨论不调用 `compare_primary`，不改 SESOI。

---

## 7. Hard-Gold 只读对照

ADR-0032：Hard-Gold 骨架与冒烟检索金标分文件；骨架跑过不等于改臂。  
ADR-0033：主张金标 `eval run --gold` 不得顶替 Hard-Gold 过线门；过线不等于已换臂。生产默认臂后来的拍板在 ADR-0033 的后续段与 `docs/evidence/issue-284/DECISION-16.md`，本票不改 `PRODUCTION_RETRIEVAL_MODE`。

因此本页把两套集分开：

| 集 | 路径 | 在 SLI 6 的位置 |
|----|------|-----------------|
| 冻结 canary 集 | `data/eval/gold.json` 的 `must_stale` | 唯一分母 |
| Hard-Gold 检索骨架 | `data/eval/retrieve_hard_gold.json` | 不进入 pass rate。不混报增益门 |

从 Hard-Gold 继承的只有纪律：集事先冻结、分文件、不把冒烟说成统计显著、不授权改臂、金标不进生产 score。不继承成第二个主 KPI，也不把检索题的 n=20 加进 canary 集大小。

---

## 8. 对照映射（不新建主名）

| 对照 | 落在本页的哪一句 | 不做什么 |
|------|------------------|----------|
| arXiv 2608.26385 | 冻结 canary 集、版本针、发布前或周跑的 pass rate → §1–§3 | 不把论文里的指标名抄成第二套主 KPI |
| Confident AI canary / regression | 固定集上的回归；掉了当发布风险 → §3 的 pass rate 与 §6 的停发讨论 | 不新建 Confident-* 主名；不把 regression 升成第 7 个主 SLI |
| #515 D1/D5 | 金标门与 pass@k 明细 | 不合并该 PR，不合入其脚本 |
| ADR-0032 / ADR-0033 | 冻结、分文件、不混报、不改臂 | 不重跑 Hard-Gold，不改默认检索臂 |
| #508 宽表 D1/D5 行 | 名字已在宽表。本页不新编号 | 不合并 #508 |

---

## 9. 叙事

可接受的观测叙事：

- 「canary_pin 是 `c7a14683de82bb795fd67bbb505bd6f7128b7c2a` 的 must_stale，集大小 4；本周未跑，pass rate 写未跑」  
- 「code_pin 是本次执行的 sha；协议落盘基线不是已跑针」  
- 「3 遍冒烟，过门遍数不足 3，掉线处置写停发列车讨论；不回写 Y」  
- 「3/3 只说明这三遍没有低于当前金标门；Canary ≠ 乙尺」

不可接受的叙事：

- 「canary 过了，所以路线 Y 可以改判」  
- 「掉线了，所以把 RESULT-Y 写成另一种成立」  
- 「未跑，pass rate 记 0%」或「未跑，记 100%」  
- 「把 retrieve_hard_gold 的 20 条算进 pass rate」  
- 「pass@k 是另一条主指标」  
- 任何把本页数字写成实验成立、软乙、接近乙或主实验成功的句子

---

## 10. 周报表格（最小列）

填入 [`docs/evidence/slo-min6/周报骨架.md`](../evidence/slo-min6/周报骨架.md) 的 SLI 6 格，以及 [`生产补丁放行SLO.md`](生产补丁放行SLO.md) §6 的对应行。只抄摘要。禁止把数字写入 `RESULT-Y` 成立格。本骨架不预填 pass rate。

| pass rate | canary_pin | code_pin | 掉线处置 |
|-----------|------------|----------|----------|
| `<未跑>` | `<blob>\|must_stale` | `<未跑>` | 未跑。不回写 Y |

字段：

| 列 | 说明 |
|----|------|
| `window` | 起止，Asia/Shanghai。发布前跑则写列车标识 |
| `canary_set_size` | 冻结集大小。本预锁为 4。对不上 pin 写「样本不足」 |
| `canary_pin` | dataset pin。预锁 blob 见 §1 |
| `code_pin` | 本次执行 sha。未跑则「未跑」 |
| `n_runs` | 3。不足 3 则 pass rate 写「未跑」 |
| `pass rate` | 过门遍数/3。未跑写「未跑」，禁止写 0% 或 100% |
| pass@k 明细 | D5。每个 `must_stale` id 的命中遍数/3。不升主名 |
| `掉线处置` | 未跑 / 未掉线（仍非绿灯）/ 停发列车讨论。禁止写成 RESULT-Y 改判 |
| `notes` | 冒烟，不报总体方差。Canary ≠ 乙尺。金标不进生产 score |

---

## 11. 账本指针（只读）

| 指针 | 用途 |
|------|------|
| [`docs/evidence/slo-min6/canary-pin.md`](../evidence/slo-min6/canary-pin.md) | 集与两根针的预锁。无 pass rate |
| `data/eval/gold.json` | 只读。blob `c7a14683de82bb795fd67bbb505bd6f7128b7c2a`。本票不编辑 |
| `data/eval/retrieve_hard_gold.json` | 只读对照。不进分母。本票不编辑 |
| `src/freshlatch/eval/matrix.py` | `must_stale` 期望 `stale`；缺判不算命中。本票不编辑 |
| ADR-0042 | 实验—生产防火墙。金标不进生产 score |
| ADR-0032 / ADR-0033 | Hard-Gold 骨架与过线闸。主张金标不顶替该门 |
| #515 @ `29c57b737133810a5e632832f681910971d46fce` | D1/D5 口径来源。不合并 |
| [`生产观测最小6-索引.md`](生产观测最小6-索引.md) | 最小 6 成员表。本页是其中 SLI 6 |
| [`生产补丁放行SLO.md`](生产补丁放行SLO.md) | 宽表 D1/D5 行。本 SLI 不新编号 |

聚合结果不回写为放行特征，不进入生产 score，不改 `compare_primary`，不改实验预注册。

---

## 12. 验收勾（本页范围）

- [x] 冻结 canary 集已钉：`must_stale` = `c1` `c2` `c3` `c7`，大小 4；dataset pin = `c7a14683de82bb795fd67bbb505bd6f7128b7c2a`  
- [x] code pin 的写法已钉：跑前记录执行 sha；落盘基线不是已跑针  
- [x] 发布前或周跑的 pass rate 已定义；未跑不得写成 0% 或 100%；金标只读，不进生产 score  
- [x] 掉线 → 停发列车讨论；该处置不是 RESULT-Y 改判；本页不回写 Y  
- [x] D1/D5 口径摘自 #515；#515 本身 defer，不合并，不合入其脚本与 `src/`  
- [x] 对照 arXiv 2608.26385 与 Confident AI canary/regression；未新建平行主名或 Confident-* 主名  
- [x] Canary ≠ 乙尺；未改生产放行谓词  

---

## 13. 非目标

- 合并 #508，或合并 #515，或合并 #509–#514，或合并本协议所在 PR（No merge until Matt）  
- 编辑 `RESULT-Y` / `PREREG-Y` / `formal-generations-y` / SESOI / \(k_{\min}\) / Cond / 选取 R  
- 编辑 `data/eval/gold.json` 或 `data/eval/retrieve_hard_gold.json`  
- 实现或调用 `compare_primary`；改 `src/` 放行谓词或闸语义  
- 把金标放进生产 score 或在线放行器  
- 把 canary 掉线写成 RESULT-Y 改判，或据此回写 Y  
- 新建 Confident-*、Phoenix-* 或平行的 pass@k 主 KPI 名  
- 把 Hard-Gold 检索集混进本 pass rate；改生产默认检索臂  
- 新编宽表 ID，或把 version tags 从 phase-2 升成主 SLI  
- 本票实际跑 LLM 金标、填写 pass rate、或把 N=3 冒烟说成统计测量  
- 回改 T1–T5 协议语义  
- 把本页称作实验成立或主实验成功
