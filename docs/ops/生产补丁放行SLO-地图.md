# 地图：生产补丁 / 放行 SLO

> **生产观测 ≠ 乙尺。** 本变更未编辑 `RESULT-Y` / `PREREG-Y` / SESOI。  
> 本页改编自未合并 program draft [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) @ `b24b6f5`。  
> 本波交付真源：[`生产观测最小6-索引.md`](生产观测最小6-索引.md) · [#557](https://github.com/luxingjiang1993/FreshLatch/issues/557) · Parent [#556](https://github.com/luxingjiang1993/FreshLatch/issues/556)。  
> Destination：把生产观测收口为最小 6 SLI（可周报 / 可机检 / 可挂 Watch 或离线 canary），并重申实验—生产防火墙。  
> **不是**复活 patch_events 路线 Y，**不是**改判丙。`#508` **Keep draft · No merge until Matt**。

## Notes

- 本波层身份：观测/Watch + 离线 canary。硬闸支撑留在 defer 的 #512，不进本波主 SLI。  
- Y 结果丙只读冻结（tip `2a3fadd`）；生产绿不得改判该页。  
- 禁：同页二跑、金标进生产 score、把 phase-2 六项升成第 7+ 主 SLI。  
- 宽表 SLO-01…07 的票正文留在 #508；本仓只留 [`tasks/SLO-INDEX.md`](../../tasks/SLO-INDEX.md) 指针。  
- 防火墙 ADR 编号为 **ADR-0042**。#508 草案曾写 ADR-0034；该文件名在 tip 上已被 `docs/adr/0034-patch-events-route-b-identifiable-fixed-k.md` 占用，本程不覆盖。  

## Decisions so far

| 日期 | 决议 | 摘要 |
|------|------|------|
| 2026-10-09 | #508 program draft（未合入） | 硬防火墙 + 宽表分层 + 起步阈值。评估留在 #508，不复制。草案自编号 ADR-0034。运营宽表 `docs/ops/生产补丁放行SLO.md`。规格卷 24。 |
| 2026-10-09 | #508 /to-tickets（未合入） | SLO-01…07 宽表票在 #508 分支；Frontier 曾为 SLO-01。本程不把该清单当第二套交付真源。 |
| 2026-10-12 | SLO-min6 grill 锁「按推荐」 | 最小 6 钉死；phase-2 只挂附录。仓外锁，本页只镜像。 |
| 2026-10-12 | T1 #557 文档对齐 | 索引 + 防火墙重申 + 下方一行模板可挂。**本行不是已发的 GitHub Decisions 评论**；人不审完不合并。 |
| 2026-10-12 | T2 #558 协议摘字段 | SLI 1·2 成对协议落 `docs/ops/抽检-放行误放误拒.md`（adapt #514 @ `948db415`）。#514 仍 candidate，不合并。本行不是已发的 GitHub Decisions 评论。 |
| 2026-10-12 | T3 #559 协议摘字段 | SLI 4 override 周报落 `docs/ops/人审-override周报.md`（adapt #511 @ `70286694`，主字段 C2，C1 旁注）。#511 仍 candidate，不合并。本行不是已发的 GitHub Decisions 评论。 |
| 2026-10-12 | T4 #560 三分协议 | SLI 3 unknown/abstention 协议落 `docs/ops/判定-unknown三分协议.md`（new + adapt ADR-0028/I1 · 仓内 fresh/stale/unknown · #508 program）。对照 HALT-RAG / Confident AI，不新建主名。#508 仍 keep，不合并。本行不是已发的 GitHub Decisions 评论。 |

## Decisions 一行模板（grill G17 · 可粘贴）

挂到人指定的地图评论即可。本票不代发、不关单、不合并。`code_pin` / `canary_pin` 留空位；tip 只读锚是 `2a3fadd`，不是把丙页改写成当周 pin。

```text
SLO-min6（grill 锁「按推荐」· Asia/Shanghai）：6 SLI 已钉；防火墙未破（未改 RESULT-Y/PREREG-Y/SESOI；未称乙）；PR 去留=#508 keep / #514+#511 candidate / #515+#513+#512 defer / #510+#509 low / #417 recommend-close；phase-2 已挂 Provenance；code_pin=<sha>·canary_pin=<id>。
```

模板字样保持 grill 锁文。执行状态另记：#417 已于 2026-10-12 由人关闭（相对 main `hybrid+rerank` 过时）。本程不重开 #417，也不改模板原文。

## PR 去留（镜像 · 不执行关合）

| PR | 去留 | 与最小 6 |
|----|------|----------|
| #508 | Keep · program draft · 不合并 | 宽表总锚 |
| #514 | Candidate · 不合并 | SLI 1·2 协议已摘入 `docs/ops/抽检-放行误放误拒.md`（T2 #558） |
| #511 | Candidate · 不合并 | SLI 4 协议已摘入 `docs/ops/人审-override周报.md`（T3 #559） |
| #515 | Defer | SLI 6 口径可摘；不本波合 |
| #513 | Defer | 非最小 6 |
| #512 | Defer | 硬闸支撑，非主 SLI |
| #510 | Low | 改侧抽检扩展 |
| #509 | Low | 文档机检 |
| #417 | 已关闭（人） | 模板仍写 recommend-close |

## Out of scope

- 回写 `PREREG-Y` / `RESULT-Y` / `formal-generations-y` / SESOI / \(k_{\min}\) / Cond / 选取 R  
- 同页二跑；把本程称作实验成立或主实验成功  
- 金标当在线放行器或生产 score  
- 合并 #508–#515 或本 PR（No merge until Matt）  
- 实现 T5–T6（#561–#562）；改 `src/` 放行谓词  
- 把 abstention 重标成 false-accept / false-reject；把 unknown 当作失败或压进 FA/FR 分母；新建平行失败三分法 KPI  
- 大屏运营 UI；改生产默认检索臂；扩 HumanLatch 动词  
