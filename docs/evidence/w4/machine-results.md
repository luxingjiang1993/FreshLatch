# W4 机器层执行结果(自动生成 2026-09-21T14:22:42Z)

> 本文件由 scripts/run_w4_acceptance.py 生成,只含机器可执行判据;人工判据(J1 人点回/录屏、J2②语义复核、J3-4 复述测试)以 checklist.md 签字为准。

## P2/J1 金标运行(N=1,temperature=0)

- raw JSON: 见 reports/(report-*.json,kind=gold_run,runs=1)
- 机器层点回 8/8: ❌(必要不充分,人点回才算数)

| claim_id | 登记锚段落 | 判定证据命中 |
|---|---|---|
| c1 | t0-competitor-notes#p2@T1 | ✅ |
| c2 | t0-regulatory-memo#p2@T1 | ✅ |
| c3 | t0-channel-interviews#p2@T1 | ✅ |
| c4 | t0-market-census#p2@T1 | ✅ |
| c5 | t0-cost-model#p2@T1 | ❌ |
| c6 | t0-competitor-news#p2@T1 | ❌ |
| c7 | t0-trade-press#p2@T1 | ❌ |
| c8 | t0-tech-ecosystem#p2@T1 | ❌ |
| c9 | 豁免(无 T1 原文) | — |
| c10 | 豁免(无 T1 原文) | — |
| c11 | 豁免(无 T1 原文) | — |
| c12 | 豁免(无 T1 原文) | — |

## J2 有效反证机器层(按主张计;②语义终判归人工复述复核)

| seed | must_stale 机器层有效反证条数 | 该遍 ≥1 条 |
|---|---|---|
| 11 | 4/4 | ✅ |
| 22 | 4/4 | ✅ |
| 33 | 3/4 | ✅ |

- 停止条件机器层读数(≥2/3 遍出现 ≥1 条): ✅ 达成——最终以人工②复核后判定为准
- 反向护栏(must_fresh 无机器层有效反证): ✅

### J2 逐 seed 明细(N=1 各一遍)

seed=11:

| claim_id | 判定 | ①可点回 | ③锚对齐 | ②代理 | 机器层有效 |
|---|---|---|---|---|---|
| c1 | stale | ✅ | ✅ | ❌ | ✅ |
| c2 | stale | ✅ | ✅ | ❌ | ✅ |
| c3 | stale | ✅ | ✅ | ❌ | ✅ |
| c7 | stale | ✅ | ✅ | ❌ | ✅ |

seed=22:

| claim_id | 判定 | ①可点回 | ③锚对齐 | ②代理 | 机器层有效 |
|---|---|---|---|---|---|
| c1 | stale | ✅ | ✅ | ❌ | ✅ |
| c2 | stale | ✅ | ✅ | ❌ | ✅ |
| c3 | stale | ✅ | ✅ | ❌ | ✅ |
| c7 | stale | ✅ | ✅ | ❌ | ✅ |

seed=33:

| claim_id | 判定 | ①可点回 | ③锚对齐 | ②代理 | 机器层有效 |
|---|---|---|---|---|---|
| c1 | stale | ✅ | ✅ | ❌ | ✅ |
| c2 | stale | ✅ | ✅ | ❌ | ✅ |
| c3 | stale | ✅ | ✅ | ❌ | ✅ |
| c7 | stale | ✅ | ❌ | ❌ | ❌ |

## 假绿对照(control)

- must_stale 假绿 1/4;对照成立: ❌
- must_unknown 盲判绿: 1 条(c9)
