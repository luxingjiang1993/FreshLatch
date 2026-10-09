SLO-07 复验主业观测周报（D1 · D3 · D4）

- 层身份条幅: D1=离线评测层; D3=硬闸(SLO-02 同出口); D4=观测
- recorded_at: 2026-10-09T17:11:43.404139+00:00

【离线评测层】SLO-07 D1 must_stale multi-run

- 层身份: 离线评测层（金标不得进生产 score / 在线放行）
- 运行遍数 n = 3（写死于命令/文档；默认 3）
- 金标门: 不得低于当前金标门：must_stale 每遍全命中（hits == |must_stale|；期望判定 stale）
- 金标门 id: must_stale_full_hit_per_run
- 来源: smoke_fixture
- 方差纪律: n=3 < 30：框定为冒烟检查，不报总体方差（非统计测量）。
- report_population_variance: False

## must_stale 命中汇总（条数；不报百分比）

| run | hits/total | 是否过门 | 漏判 |
|---|---|---|---|
| 1 | 4/4 | 是 | 无 |
| 2 | 4/4 | 是 | 无 |
| 3 | 4/4 | 是 | 无 |

## per-claim 命中次数/n（pass@k；冒烟不报总体方差）

| claim_id | 命中/n |
|---|---|
| c1 | 3/3 |
| c2 | 3/3 |
| c3 | 3/3 |
| c7 | 3/3 |

- 过门遍数: 3/3
- 全部过门: 是

【硬闸】D3 无 T1 绿灯=0（SLO-02 同一出口）

- source: freshlatch.slo_hard_gate_violations / SLO-02
- D3 violations: 0（目标 0）
- D3 blocks: 1
- note: 无 T1 绿灯违例目标=0；计数语义与 SLO-02 仪表同一出口，勿另造冲突语义。

【观测】SLO-07 D4 包结论三值分布

- 层身份: 观测（周报；本波不作 Gate 生死）
- Run 总数: 3

| 包结论 | 计数 | 占比 |
|---|---|---|
| 勿发 | 1 | 33.33% |
| 可发 | 1 | 33.33% |
| 需补丁 | 1 | 33.33% |

【防火墙】生产放行/score 路径金标隔离

- ok: True
- scanned_files: 9
- hits: 0
- note: 金标（gold.json / must_* 桶标签）不得作为生产 score 或在线放行特征；离线评测仅允许在 eval/ 与本观测出口。

