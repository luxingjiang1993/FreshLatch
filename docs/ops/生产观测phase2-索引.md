# 生产观测 phase-2 六项 · 索引

> **生产观测 ≠ 乙尺。**  
> 本页是 SLO-phase2 T1（[#570](https://github.com/luxingjiang1993/FreshLatch/issues/570) · Parent [#569](https://github.com/luxingjiang1993/FreshLatch/issues/569)）的 ops 索引。交付真源是本程规格/票（#569/#570）与本页。  
> **防火墙：ADR-0042**（`docs/adr/0042-生产补丁放行SLO与实验防火墙.md`）。[#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) 草案曾自编号 ADR-0034；tip 上该号已是 `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md`。本页不占用、不覆盖 ADR-0034。  
> **本变更未编辑** `RESULT-Y` / `PREREG-Y` / SESOI / \(k_{\min}\) / Cond / 选取 R。未改 `src/` 放行谓词。金标不进生产 score。未改写 min-6 六个主格。  
> 禁止把本程称作：乙、软乙、接近乙、主实验成功。生产变绿不得改判丙。  
> 层身份：**观测/Watch + 离线**。P1–P6 是附录成员，不占 [`生产观测最小6-索引.md`](生产观测最小6-索引.md) §2 的六个主格。  
> Parent [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556)（min-6 track）**仍 OPEN**。P1–P6 不挂在 #556 下。  
> Provenance：**adapt** from [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) head `cursor/prod-slo-ops-aee8` @ `b24b6f573652b156a798dfa3f3fd1985a9e3348d` 的 `docs/ops/生产补丁放行SLO.md` 与 `docs/ops/生产补丁放行SLO-地图.md`（只读摘字段）+ tip `docs/ops/生产观测最小6-索引.md` §5 名单 + **ADR-0042**。`#508` **Keep draft · No merge until Matt+human**。`#508`–`#515` 本波不合并。  
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

名单与 tip 索引 §5 相同。本波把延期名单收成可挂的附录定义。协议正文属于 T2–T7，不在本页展开。

| # | 项（英文保留） | 操作定义（起步） | 分母 / 单位 | 层 | 复用锚 | 起步姿态 |
|---|----------------|------------------|-------------|----|--------|----------|
| P1 | claim-level faithfulness | 主张粒度上，机器放行/陈述与所依证据一致的占比（或对称的不忠实率） | 抽检主张数；可挂 `claim_id` | 观测/Watch（可离线抽检） | min-6 SLI 1/2 [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md)；Confident AI faithfulness/groundedness 只作对照 | 先协议+抽检表。样本不足写诚实句。不替代 FA/FR 成对周报。不新建 Confident-* 主名 |
| P2 | failure attribution 3-way | 失败样本按 ADR-0028 三桶标注：找不到 / 找错 / 没用上 | 失败样本；每条恰一桶 | 观测/Watch · 离线评测标签 | **ADR-0028 / I1**；[`判定-unknown三分协议.md`](判定-unknown三分协议.md) 已声明该三桶与 fresh/stale/unknown 分列 | 挂标协议。不改生产枚举。不写入 `rule_gate` / disposition / HumanLatch 动词 |
| P3 | judge–human calibration | 同窗机器判定与人终审/人标的一致率 / 分歧谱 | 同窗可配对样本 | 观测/Watch | min-6 SLI 4 [`人审-override周报.md`](人审-override周报.md)；ADR-0023；ADR-0006 | 周报旁表。文首「≠模型变好 / ≠验收绿灯」。不新增 HumanLatch 动词 |
| P4 | version tags | 可机读版本针族：至少 `code_pin` · `dataset_pin`（可扩 `model_pin` / `prompt_pin` / `index_pin`） | 每次周报行 / canary 执行 / 协议发布记录 | 观测/Watch · ops 协议 | SLI 6 [`冻结金标canary跑法.md`](冻结金标canary跑法.md)；[`docs/evidence/slo-min6/canary-pin.md`](../evidence/slo-min6/canary-pin.md)；arXiv 2608.26385 对照 | 针族写成必填列。未跑写「未跑」。有针不等于 canary pass |
| P5 | cost | 与请求/检索窗对齐的成本（token / API / GPU 或规范化单位） | 同窗成功完成请求或计费事件；单位须钉死 | 观测/Watch | SLI 5 [`延迟与检索回退周报.md`](延迟与检索回退周报.md)（已写 cost 留 phase-2）；NVIDIA RAG observability / Arize Phoenix 只作字段习惯 | 独立字段/行，与 SLI 5 同窗分列。不抄离线 `cost.json` 当本周生产格。不新建 Phoenix-* 主名 |
| P6 | implicit feedback | 无显式评分时的下游弱信号（confirm 后回改、重开、latch 再审、补丁回滚迹象） | 协议钉死的事件窗 | 观测/Watch（可离线聚合） | latch 轨迹；ADR-0006；ADR-0023 | 先列信号清单与计入/排除。缺信号写「未计」。弱信号不进生产 score |

字段名停在上表。不新建第 7 个主名，不把 min-6 的 false-accept、false-reject、unknown/abstention、HumanLatch override、e2e P95 + fallback、frozen gold canary 改名或并进本表。

### 附录纪律（协议在后续票）

- P1 细化 SLI 1/2，两侧成对主行仍在 min-6 周报。  
- P2 的三桶与 SLI 3 的 fresh/stale/unknown 分列，两套标签不互改。  
- P3 只描述校准。文首继承 ADR-0023，不作验收绿灯。  
- P4 的针只证明可追溯。canary 成绩仍只在 SLI 6。  
- P5 与 SLI 5 同窗可读，cost 单独成行。  
- P6 是运营线索。不进生产 score，不新增 discard/renew 以外的人审动词。  
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
| P4 | 周报对 D1/D5 写「未跑」；无 pin 族主行 | 针族另列。D1 命中率仍是 SLI 6 的门，有针不等于该率已通过 |
| P5 | #508 周报最小字段不含 cost | 独立附录行。单位在 T6 钉死。不把离线 `cost.json` 抄进本格 |
| P6 | 宽表人审主行是 C1/C2 显式动作 | 弱信号另列。不新增 HumanLatch 动词，不把弱信号写成 C 表新 ID |

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
| #514 | Candidate · 不合并 | 已喂 min-6 SLI 1/2；P1 以后只读该协议 |
| #511 | Candidate · 不合并 | 已喂 min-6 SLI 4；P3 以后只读该协议 |
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
| T2 | #571 P1 claim-level faithfulness | 后续票。本 PR 不写协议 |
| T3 | #572 P2 failure attribution 3-way | 后续票。本 PR 不写挂标协议 |
| T4 | #573 P3 judge–human calibration | 后续票。本 PR 不写旁表协议 |
| T5 | #574 P4 version tags | 后续票。本 PR 不写 pin 族协议 |
| T6 | #575 P5 cost | 后续票。本 PR 不钉单位、不抄 `cost.json` |
| T7 | #576 P6 implicit feedback | 后续票。本 PR 不写信号清单正文 |

#556 仍 OPEN，继续只覆盖 min-6。本 PR 是 draft。No merge until Matt+human。
