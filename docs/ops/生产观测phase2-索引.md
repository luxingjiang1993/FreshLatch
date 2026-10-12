# 生产观测 phase-2 六项 · 索引

> **生产观测 ≠ 乙尺。**  
> 本页是 SLO-phase2 T1（[#570](https://github.com/luxingjiang1993/FreshLatch/issues/570) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）的 ops 索引。交付真源是本程规格/票（#569/#570）与本页。  
> **防火墙：ADR-0042**（`docs/adr/0042-生产补丁放行SLO与实验防火墙.md`）。[#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) 草案曾自编号 ADR-0034；tip 上该号已是 `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md`。本页不占用、不覆盖 ADR-0034。  
> **本变更未编辑** `RESULT-Y` / `PREREG-Y` / SESOI / \(k_{\min}\) / Cond / 选取 R。未改 `src/` 放行谓词。金标不进生产 score。未改写 min-6 六个主格。  
> 禁止把本程称作：乙、软乙、接近乙、主实验成功。生产变绿不得改判丙。  
> 层身份：**观测/Watch + 离线**。P1–P6 是附录成员，不占 [`生产观测最小6-索引.md`](生产观测最小6-索引.md) §2 的六个主格。  
> Parent [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556)（min-6 track）**仍 OPEN**。P1–P6 不挂在 #556 下。  
> Provenance：**adapt** from [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) head `cursor/prod-slo-ops-aee8` @ `b24b6f573652b156a798dfa3f3fd1985a9e3348d` 的 `docs/ops/生产补丁放行SLO.md` 与 `docs/ops/生产补丁放行SLO-地图.md`（只读摘字段）+ tip `docs/ops/生产观测最小6-索引.md` §5 名单 + **ADR-0042**。`#508` **Keep draft · No merge until Matt+human**。`#508`–`#515` 本波不合并。  
> P1 协议页 Provenance：**adapt** from tip `docs/ops/抽检-放行误放误拒.md`（min-6 SLI 1/2 · 粗粒度折算起点）+ Confident AI faithfulness/groundedness 对照（不新建主名）+ 可选只读 [#514](https://github.com/luxingjiang1993/FreshLatch/pull/514) @ `948db41565b564f4b3f48861da6b9f36ceff546c`（[#571](https://github.com/luxingjiang1993/FreshLatch/issues/571) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）。交付真源是 #569/#571 与 [`抽检-主张忠实.md`](抽检-主张忠实.md)。`#514` 仍 Candidate，不合并。落地基线 `0cb03b99f71ddc8200ac04771d9338b0ff64e194`。  
> P2 协议页 Provenance：**adapt** from tip `docs/adr/0028-i1-失败三分法评测标签与语料.md`（唯一种子）+ tip [`判定-unknown三分协议.md`](判定-unknown三分协议.md)（明文 ADR-0028 ≠ fresh/stale/unknown）+ 本页 P2 起步定义与 [`docs/evidence/slo-phase2/周报附录骨架.md`](../evidence/slo-phase2/周报附录骨架.md) P2 行 + **ADR-0042**（[#572](https://github.com/luxingjiang1993/FreshLatch/issues/572) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）。交付真源是 #569/#572 与 [`挂标-失败归因三桶.md`](挂标-失败归因三桶.md)。落地基线 `d822cd0cb9402231d6ef42a6bdc6d705bb0d9868`。  
> P3 协议页 Provenance：**adapt** from tip [`人审-override周报.md`](人审-override周报.md)（min-6 SLI 4 · 只读互指 · 分列）+ **ADR-0023** + **ADR-0006** + 本页 P3 起步定义与 [`docs/evidence/slo-phase2/周报附录骨架.md`](../evidence/slo-phase2/周报附录骨架.md) P3 行 + 可选只读 [#511](https://github.com/luxingjiang1993/FreshLatch/pull/511) @ `70286694b30bf2d06df863b4a48e2ff3447b9644`（C2 字段；不合入脚本）+ **ADR-0042**（[#573](https://github.com/luxingjiang1993/FreshLatch/issues/573) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）。交付真源是 #569/#573 与 [`旁表-人机校准.md`](旁表-人机校准.md)。`#511` 仍 Candidate，不合并。落地基线 `814263ec66701abac9670dd404dada53e8a24f7d`。  
> P4 协议页 Provenance：**adapt** from tip [`冻结金标canary跑法.md`](冻结金标canary跑法.md)（min-6 SLI 6 · 只读互指 · 针≠分）+ tip [`docs/evidence/slo-min6/canary-pin.md`](../evidence/slo-min6/canary-pin.md)（占位针继承；不回写金标）+ 本页 P4 起步定义与 [`docs/evidence/slo-phase2/周报附录骨架.md`](../evidence/slo-phase2/周报附录骨架.md) P4 行 + 对照 arXiv 2608.26385（版本针习惯；有针 ≠ pass；不造 URL）+ **ADR-0042**（[#574](https://github.com/luxingjiang1993/FreshLatch/issues/574) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）。交付真源是 #569/#574 与 [`版本针族.md`](版本针族.md)。`#515` 仍 Defer，不合并，不合入其脚本。落地基线 `a7505d66bac24e7b6ffc1e243c86c61ad2a95b96`。该 sha 与 tip `666679c6ba09b09da34a46f558f14dab5896ca58` 都不填进 `code_pin`。  
> P5 协议页 Provenance：**adapt** from tip [`延迟与检索回退周报.md`](延迟与检索回退周报.md)（min-6 SLI 5 · 已钉 cost→phase-2 · 只读互指 · 不占第三格）+ 仓内 `cost.json` 只读对照（`docs/evidence/issue-284/cost.json`、`docs/evidence/neural-rerank/cost.json`、`docs/evidence/fastembed-081-recheck/cost.json`；不抄进生产格）+ 本页 P5 起步定义与 [`docs/evidence/slo-phase2/周报附录骨架.md`](../evidence/slo-phase2/周报附录骨架.md) P5 行 + 对照 NVIDIA RAG observability / Arize Phoenix（映射仓内单位；不新建 Phoenix-* 主名；不绑定完整平台）+ **ADR-0042**（[#575](https://github.com/luxingjiang1993/FreshLatch/issues/575) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）。交付真源是 #569/#575 与 [`成本周报.md`](成本周报.md)。落地基线 `6f9f021996a21319781181413a6d85cc2b00f1d1`。该 sha 不是本周生产 cost。tip `666679c6ba09b09da34a46f558f14dab5896ca58` 仍只是路线 Y 丙的只读锚。  
> P6 协议页 Provenance：**adapt** from tip **ADR-0006**（重跑 / `latch_log` / 动词封闭集 · 只读）+ tip **ADR-0023**（不新增 action · `override` 派生 · 只读）+ tip [`人审-override周报.md`](人审-override周报.md)（min-6 SLI 4 · 只读互指 · 不进 `c2_rate`）+ tip [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md)（min-6 SLI 1/2 · 只读互指 · 不替代成对周报）+ 本页 P6 起步定义与 [`docs/evidence/slo-phase2/周报附录骨架.md`](../evidence/slo-phase2/周报附录骨架.md) P6 行 + **ADR-0042**（[#576](https://github.com/luxingjiang1993/FreshLatch/issues/576) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）。交付真源是 #569/#576 与 [`弱信号Watch.md`](弱信号Watch.md)。落地基线 `29beaccbe3334d3184f83b7d0aa892903a578b43`。该 sha 不是本周弱信号计数。tip `666679c6ba09b09da34a46f558f14dab5896ca58` 仍只是路线 Y 丙的只读锚。
> 日期：2026-10-12（Asia/Shanghai）。grill 锁「按推荐」。tip `origin/main`=`666679c6ba09b09da34a46f558f14dab5896ca58`（RESULT-Y 丙，只读）。Trust **L1** · Blast **docs/obs**。  
> **防火墙未破 · ADR-0042 · #556 仍 OPEN · No merge until Matt+human**

---

## 1. 层身份

本波 phase-2 六项的层身份是 **观测/Watch + 离线**。

| 层 | 本波用法 |
|----|----------|
| 观测/Watch | P1、P3、P5，以及 P2/P4/P6 的周报或抽检侧。本波不作 Gate 生死。 |
| 离线 | P1 可离线抽检；P2 是离线评测标签；P4 的针可挂在离线 canary 记录上；P6 的弱信号可离线聚合。不进生产 score。 |
| 硬闸 | 本波不新增硬闸主 SLI。不变量仍继承 ADR-0042。支撑计数仍在 defer 的 #512。 |
| 实验-only | 路线 Y 另页。只读。不进本索引的成功判据。 |

数值门槛本波只给起步姿态。硬百分数 Gate 须后续决议。事后改门槛凑绿 = 本页作废。

min-6 的层身份（观测/Watch + 离线 canary，主成员六个）写在 [`生产观测最小6-索引.md`](生产观测最小6-索引.md) §1–§2。本页不改那张表。

## 2. phase-2 六成员（附录 · 本波不增删）

名单与 tip 索引 §5 相同。本波把延期名单收成可挂的附录定义。P1 协议正文在 [`抽检-主张忠实.md`](抽检-主张忠实.md)（#571）。P2 协议正文在 [`挂标-失败归因三桶.md`](挂标-失败归因三桶.md)（#572）。P3 协议正文在 [`旁表-人机校准.md`](旁表-人机校准.md)（#573）。P4 协议正文在 [`版本针族.md`](版本针族.md)（#574）。P5 协议正文在 [`成本周报.md`](成本周报.md)（#575）。P6 协议正文在 [`弱信号Watch.md`](弱信号Watch.md)（#576）。

| # | 项（英文保留） | 操作定义（起步） | 分母 / 单位 | 层 | 复用锚 | 起步姿态 |
|---|----------------|------------------|-------------|----|--------|----------|
| P1 | claim-level faithfulness | 主张粒度上，机器放行/陈述与所依证据一致的占比（或对称的不忠实率） | 抽检主张数；可挂 `claim_id` | 观测/Watch（可离线抽检） | [`抽检-主张忠实.md`](抽检-主张忠实.md)（#571）；粗粒度折算起点仍是 min-6 SLI 1/2 [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md)；Confident AI faithfulness/groundedness 只作对照 | 协议+抽检表可挂 `claim_id`。样本不足写诚实句。不替代 FA/FR 成对周报。不新建 Confident-* 主名 |
| P2 | failure attribution 3-way | 失败样本按 ADR-0028 三桶标注：找不到 / 找错 / 没用上 | 失败样本；每条恰一桶 | 观测/Watch · 离线评测标签 | [`挂标-失败归因三桶.md`](挂标-失败归因三桶.md)（#572）；**ADR-0028 / I1**；[`判定-unknown三分协议.md`](判定-unknown三分协议.md) 已声明该三桶与 fresh/stale/unknown 分列 | 挂标协议。每条恰一桶。不另起第四桶。不改生产枚举。不写入 `rule_gate` / disposition / HumanLatch 动词。不与 SLI 3 合流 |
| P3 | judge–human calibration | 同窗机器判定与人终审/人标的一致率 / 分歧谱（含 override 方向分解） | 同窗可配对样本 | 观测/Watch | [`旁表-人机校准.md`](旁表-人机校准.md)（#573）；min-6 SLI 4 [`人审-override周报.md`](人审-override周报.md) 只读互指、分列；ADR-0023；ADR-0006 | 周报旁表。文首「≠模型变好 / ≠验收绿灯」。不新增 HumanLatch 动词。不作验收 Gate。不挤占 SLI 4 主行 |
| P4 | version tags | 可机读版本针族：至少 `code_pin` · `dataset_pin`（可扩 `model_pin` / `prompt_pin` / `index_pin`） | 每次周报行 / canary 执行 / 协议发布记录 | 观测/Watch · ops 协议 | [`版本针族.md`](版本针族.md)（#574）；SLI 6 [`冻结金标canary跑法.md`](冻结金标canary跑法.md) 只读互指、针≠分；[`docs/evidence/slo-min6/canary-pin.md`](../evidence/slo-min6/canary-pin.md) 占位针继承；arXiv 2608.26385 对照 | 针族写成必填列。未跑写「未跑」。有针不等于 canary pass。不回写金标。无营销版号主 KPI |
| P5 | cost | 与 SLI 5 同一窗口的成本。三族分列：token（`token_in` / `token_out` / `token_total`）、API（`api_cny`）、GPU（`gpu_s`） | token 的分母对齐成功完成请求；API 的分母是计费事件；GPU 的分母是 GPU 计量。单位钉死为 `token`、`CNY`、`gpu_s`。不设混合规范化单位 | 观测/Watch | [`成本周报.md`](成本周报.md)（#575）；SLI 5 [`延迟与检索回退周报.md`](延迟与检索回退周报.md) 只读互指、不占第三格；NVIDIA RAG observability / Arize Phoenix 只作字段习惯 | 独立行，与 SLI 5 同窗分列。不抄离线 `cost.json`。不新建 Phoenix-* 主名。不单独用 cost 降当成功 |
| P6 | implicit feedback | 无显式评分时的下游弱信号。四行：confirm 后回改、重开（计 `rerun_log`）、latch 再审模式、补丁回滚迹象。未列信号写「未计」 | 协议窗。分母分别为 `n_confirm`、`n_void_eligible`、`n_latched`、`n_confirm` | 观测/Watch（可离线聚合） | [`弱信号Watch.md`](弱信号Watch.md)（#576）；ADR-0006；ADR-0023；min-6 抽检 / override 只读互指 | 清单与计入/排除已钉。缺信号写「未计」。弱信号 ≠ 金标，不进生产 score，不升硬闸 / 乙尺 / RESULT-Y 改判 |

字段名停在上表。不新建第 7 个主名，不把 min-6 的 false-accept、false-reject、unknown/abstention、HumanLatch override、e2e P95 + fallback、frozen gold canary 改名或并进本表。

### 附录纪律

- P1 细化 SLI 1/2，协议在 [`抽检-主张忠实.md`](抽检-主张忠实.md)。两侧成对主行仍在 min-6 周报。  
- P2 的三桶与 SLI 3 的 fresh/stale/unknown 分列，两套标签不互改。协议在 [`挂标-失败归因三桶.md`](挂标-失败归因三桶.md)。  
- P3 只描述校准。文首继承 ADR-0023，不作验收绿灯。协议在 [`旁表-人机校准.md`](旁表-人机校准.md)。与 SLI 4 分列，不挤占 C2 主行。不新增 HumanLatch 动词。  
- P4 的针只证明可追溯。协议在 [`版本针族.md`](版本针族.md)。canary 成绩仍只在 SLI 6。未跑写「未跑」。有针不等于 canary pass。不回写金标凑针。不发明与 pin 平行的营销版号主 KPI。
- P5 与 SLI 5 同窗可读，cost 单独成行。协议在 [`成本周报.md`](成本周报.md)。单位钉死为 `token`、`CNY`、`gpu_s`。不进 SLI 5 主行第三格。不抄离线 `cost.json`。不单独用 cost 降当成功。
- P6 是运营线索。协议在 [`弱信号Watch.md`](弱信号Watch.md)。四行可计数。缺信号写「未计」。弱信号 ≠ 金标，不进生产 score，不升硬闸 / 乙尺 / RESULT-Y 改判，不新增 discard/renew 以外的人审动词。  
- 单独的放行率或 cost 下降不构成成功句。

## 3. 与 #508 宽表字段的只读对齐

下表只摘 [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) @ `b24b6f573652b156a798dfa3f3fd1985a9e3348d` 的宽表字段，供对照。交付真源是 #569/#570 与本页。宽表库存仍在 tip 的 [`生产补丁放行SLO.md`](生产补丁放行SLO.md)（该页已由 min-6 改编，本票不重写 A–E 表）。`#508` 保持 program draft，不合并。

| phase-2 | #508 @ `b24b6f5` 上的对应字段 | 本程处置 |
|---------|-------------------------------|----------|
| 层身份 | 宽表 §1：硬闸 / 观测/Watch / 离线评测 / 实验-only | 本波只用观测/Watch + 离线。不新增硬闸主 SLI。实验-only 留在路线 Y 另页 |
| 防火墙句 | 宽表 §2：Y 丙冻结；生产改善不得回写成立格；禁同页二跑；金标不进生产 score | 原句继承。权威编号改为 **ADR-0042**。不沿用草案自编号 ADR-0034 |
| 地图决议草稿 | `生产补丁放行SLO-地图.md` 曾写 ADR-0034 与「评估见 docs/research/…」 | 不复制该草稿进本页。Decisions 模板以本页 §5（SPEC §3.7）为准。评估全文仍留在 #508，避免双真源 |
| P1 | A3 改对率（确认后 after 与证据一致）；B2/B3 误放/误拒成对 | 主张粒度细化 A3/B2/B3 所喂的 SLI 1/2。不新编 A/B 号，不替换成对周报 |
| P2 | 宽表 A–E 无此主行 | 种子只在 ADR-0028。不补进 A–E |
| P3 | C2 override rate（派生标签；宽表写 ≠模型变好） | 与 C2 分列的同窗一致率。C2 仍是 min-6 SLI 4 |
| P4 | 周报对 D1/D5 写「未跑」；无 pin 族主行 | 针族另列。协议在 [`版本针族.md`](版本针族.md)。D1 命中率仍是 SLI 6 的门，有针不等于该率已通过 |
| P5 | #508 周报最小字段不含 cost | 独立附录行。单位已在 [`成本周报.md`](成本周报.md) 钉死（`token` / `CNY` / `gpu_s`）。不把离线 `cost.json` 抄进本格。不进 SLI 5 第三格 |
| P6 | 宽表人审主行是 C1/C2 显式动作 | 弱信号另列。协议在 [`弱信号Watch.md`](弱信号Watch.md)。不新增 HumanLatch 动词，不把弱信号写成 C 表新 ID，不进生产 score |

PR 去留与 #508 地图同一张单，本波仍不执行关合：`#508` keep · `#514`/`#511` candidate · `#515`/`#513`/`#512` defer · `#510`/`#509` low。

## 4. 防火墙（本变更自检）

- [x] 文首权威是 ADR-0042，未改 `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md`  
- [x] 未编辑 `docs/evidence/patch-events/RESULT-Y.md`  
- [x] 未编辑 `docs/evidence/patch-events/PREREG-Y.md`  
- [x] 未编辑 SESOI / \(k_{\min}\) / Cond / 选取 R  
- [x] 未把金标写入生产 score 或在线放行器  
- [x] 未改 `src/` 闸语义  
- [x] 未合并 #508–#515，也未合并本 PR  
- [x] 未把本程写成实验成立  
- [x] 未改写 min-6 §2 六个主格；P1–P6 写在本页与周报附录  
- [x] 未把 P1–P6 挂到 #556；#556 仍 OPEN；本票 Parent 是 #569  
- [x] 未在本页实现 T2–T7 的协议正文  
- [x] P1 正文在 `抽检-主张忠实.md`；本页只互指；未改 min-6 B2/B3 主行；未新建 Confident-* 主名  
- [x] P2 正文在 `挂标-失败归因三桶.md`；本页只互指；三桶未写入生产枚举；未与 SLI 3 合流；未另起第四桶  
- [x] P3 正文在 `旁表-人机校准.md`；本页只互指；未与 SLI 4 合流；未新增 HumanLatch 动词；未把一致率写成验收绿灯；未挤占 C2 主行  
- [x] P4 正文在 `版本针族.md`；本页只互指；未把有针写成 canary pass；未回写金标凑针；未发明营销版号主 KPI；未改 SLI 6 的 pass rate  
- [x] P5 正文在 `成本周报.md`；本页只互指；单位钉死为 token / CNY / gpu_s；未把 cost 写入 SLI 5 第三格；未抄 cost.json；未新建 Phoenix-* 主名；未单独用 cost 降当成功  
- [x] P6 正文在 `弱信号Watch.md`；本页只互指；缺信号写「未计」；弱信号 ≠ 金标且未进生产 score；未升硬闸 / 乙尺 / RESULT-Y 改判；未新增 HumanLatch 动词

## 5. Decisions 一行模板（SPEC §3.7 · 可粘贴）

挂到人指定的地图或 Parent #569 评论即可。本票不代发、不关单、不合并。`code_pin=<sha>` 是填空。tip `666679c6ba09b09da34a46f558f14dab5896ca58` 只是只读锚，不填进 `code_pin`。

可挂短句：

```text
防火墙未破 · ADR-0042 · #556 仍 OPEN · No merge until Matt+human
```

整行（SPEC §3.7）：

```text
SLO-phase2（grill 锁「按推荐」· Asia/Shanghai）：P1–P6 已钉（claim-level faithfulness · failure attribution 3-way · judge-human calibration · version tags · cost · implicit feedback）；防火墙未破（ADR-0042；未改 RESULT-Y/PREREG-Y/SESOI；未称乙；未 rewrite min-6；#556 仍 OPEN）；PR 去留=#508 keep / #514+#511 candidate / #515+#513+#512 defer / #510+#509 low；No merge until Matt+human；Trust L1 · Blast docs/obs；code_pin=<sha>。
```

## 6. PR 去留（镜像 · 不执行关合）

| PR | 去留 | 与 phase-2 |
|----|------|------------|
| #508 | Keep · program draft · 不合并 | 宽表总锚。字段只读摘入 §3 |
| #514 | Candidate · 不合并 | 已喂 min-6 SLI 1/2。P1 只读该 head @ `948db415`，协议不合并 #514 |
| #511 | Candidate · 不合并 | 已喂 min-6 SLI 4。P3 只读该 head @ `70286694` 的 C2 字段，协议不合并 #511 |
| #515 | Defer · 不合并 | canary 口径已在 SLI 6；P4 继承占位针，不合并其脚本 |
| #513 | Defer · 不合并 | 非本六项 |
| #512 | Defer · 不合并 | 硬闸支撑，非本六项 |
| #510 | Low · 不合并 | 观测扩展 |
| #509 | Low · 不合并 | 文档机检 |

总闸：No merge until Matt+human。本页不关、不合上述 PR。

## 7. 互指

| 角色 | 路径 |
|------|------|
| 本索引 | `docs/ops/生产观测phase2-索引.md` |
| min-6 索引 §5 附录 | `docs/ops/生产观测最小6-索引.md`（六项名单镜像；主 6 格不在本页） |
| 周报附录骨架 | `docs/evidence/slo-phase2/周报附录骨架.md` |
| P1 主张抽检 | `docs/ops/抽检-主张忠实.md`（#571 · Parent #569；细化 SLI 1/2；不替换 FA/FR 主行；不挂在 #556 下） |
| P2 失败归因挂标 | `docs/ops/挂标-失败归因三桶.md`（#572 · Parent #569；ADR-0028 三桶；≠ fresh/stale/unknown；不挂在 #556 下） |
| P2 样例字段 | `docs/evidence/slo-phase2/P2-样例字段.md`（空表；不预填比率） |
| P3 人机校准旁表 | `docs/ops/旁表-人机校准.md`（#573 · Parent #569；与 SLI 4 分列；文首 ≠模型变好 / ≠验收绿灯；不挂在 #556 下） |
| P3 样例字段 | `docs/evidence/slo-phase2/P3-样例字段.md`（空表；不预填比率） |
| P4 版本针族 | `docs/ops/版本针族.md`（#574 · Parent #569；继承 SLI 6 占位针；有针 ≠ canary pass；不挂在 #556 下） |
| P4 样例字段 | `docs/evidence/slo-phase2/P4-样例字段.md`（未跑记录；不预填 pass rate） |
| P5 成本周报 | `docs/ops/成本周报.md`（#575 · Parent #569；与 SLI 5 同窗分列；单位 `token` / `CNY` / `gpu_s`；不占 SLI 5 第三格；不挂在 #556 下） |
| P5 样例字段 | `docs/evidence/slo-phase2/P5-样例字段.md`（空表；不预填 token / CNY / gpu_s；不抄 cost.json） |
| P6 弱信号 Watch | `docs/ops/弱信号Watch.md`（#576 · Parent #569；四行计入/排除；缺信号写「未计」；弱信号 ≠ 金标；不挂在 #556 下） |
| P6 样例字段 | `docs/evidence/slo-phase2/P6-样例字段.md`（空表；不预填分子；未列信号写「未计」） |
| min-6 周报主行 | `docs/evidence/slo-min6/周报骨架.md`（主 6 格；本波不改） |
| 宽表运营页 | `docs/ops/生产补丁放行SLO.md`（#508 库存；本票只加互指） |
| 地图 | `docs/ops/生产补丁放行SLO-地图.md`（min-6 / #556 链；phase-2 模板不改写其锁文） |
| 防火墙 ADR | `docs/adr/0042-生产补丁放行SLO与实验防火墙.md` |
| 宽表规格 | `docs/spec/24-生产补丁放行SLO.md` |

## 8. 本波票

Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)。下列子票不挂在 [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556) 下。

| 序 | 票 | 本 PR |
|----|----|-------|
| T1 | #570 program / #508 align + 附录骨架 | 本页 + 周报附录骨架 |
| T2 | #571 P1 claim-level faithfulness | [`抽检-主张忠实.md`](抽检-主张忠实.md) |
| T3 | #572 P2 failure attribution 3-way | [`挂标-失败归因三桶.md`](挂标-失败归因三桶.md) |
| T4 | #573 P3 judge–human calibration | [`旁表-人机校准.md`](旁表-人机校准.md) |
| T5 | #574 P4 version tags | [`版本针族.md`](版本针族.md) |
| T6 | #575 P5 cost | [`成本周报.md`](成本周报.md) |
| T7 | #576 P6 implicit feedback | [`弱信号Watch.md`](弱信号Watch.md) |

#556 仍 OPEN，继续只覆盖 min-6。本 PR 是 draft。No merge until Matt+human。
