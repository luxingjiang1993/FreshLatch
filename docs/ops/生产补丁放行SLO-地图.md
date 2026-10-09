# 地图：生产补丁 / 放行 SLO

> 本地地图镜像（GitHub `wayfinder:map` 若稍后开票，以本页 Decisions 为源同步）。  
> Destination：把「改 + 放行 + 人审 + 复验主业」收成可执行生产 SLO / 观测清单并拆票。  
> **不是**复活 patch_events 冲乙。

## Notes

- 北极星：must_stale multi-run + 作废率  
- Y 结果丙只读冻结；生产绿 ≠ 改判乙  
- 禁：同页二跑、称甲/软甲、金标进生产 score  
- 本图终点含决议四件套 + spec + enriched tickets；**before-implement 前人批**；不写业务代码  

## Decisions so far

| 日期 | 决议 | 摘要 |
|------|------|------|
| 2026-10-09 | 生产补丁/放行 SLO grill | **硬防火墙** + 硬闸/观测/离线/实验-only 分层 + 起步阈值预注册。评估见 `docs/research/生产补丁放行SLO设计评估.md`。ADR-0034。运营页 `docs/ops/生产补丁放行SLO.md`。规格卷 24。 |
| 2026-10-09 | /to-spec | `docs/spec/24-生产补丁放行SLO.md` |
| 2026-10-09 | /to-tickets + enrich | SLO-01…SLO-07；Frontier=SLO-01；清单 `tasks/SLO-*.md` |

## Out of scope

- 回写 PREREG-Y / RESULT-Y / formal-generations-y  
- 同页二跑凑乙；称软甲/接近乙/主实验成功（对 Y）  
- 金标当在线放行器  
- before-implement 前业务代码  
- 大屏运营 UI；改生产默认检索臂；扩 HumanLatch 动词  

## 决议评论草稿（供贴 GitHub）

```text
决议拍板（2026-10-09）：生产补丁/放行 SLO。

- 评估：docs/research/生产补丁放行SLO设计评估.md
- ADR-0034：实验—生产防火墙 + 指标分层
- 运营真源：docs/ops/生产补丁放行SLO.md
- CONTEXT：生产补丁/放行 SLO；实验—生产防火墙
- 规格：docs/spec/24-生产补丁放行SLO.md
- 票：SLO-01…07（tasks/）；Frontier=SLO-01
- 硬句：不回写 RESULT-Y；生产绿≠乙；金标不进生产 score；禁同页二跑/软甲
- 下一步：人批 before-implement 后再 /implement；本会话无业务代码
```
