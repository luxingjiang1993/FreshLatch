# Auditor 判定臂离线评测报告(I-08,2026-10-18)

- 评测对象:生产判定臂——生产 `Auditor`(freshness_audit 教义注入,单轮 structured-output) + 生产落档真值表闸后 status(模型 `qwen-flash`,非替身)
- 只测不调参:生产模型 / temperature / SLO 门槛常量本期**未改**;不上产品 UI;禁 RESULT-Y / L4 话术。
- 复现条款:判定臂层(Auditor 单轮判定)给定解码参数(temperature=0 同证据包同判定)逐位复现;托管端点在漂移,跨会话复现只能近似,此限制为留档声明。闸后落档经生产真值表(纯函数)逐位复现。

## 运行档案(decoding 逐运行入档,§4.7)

- 模型版本: `qwen-flash`
- temperature: `0.0`
- seed: `None`
- 记录时间(UTC): 2026-10-18T12:51:30.211465+00:00
- 教义注入: `skills/freshness_audit/SKILL.md`(加载成功)
- Auditor 证据包 schema 版本: `1`
- 金标池: `data/eval/auditor_arm_gold.json`(schema `1`)

## 样本量与协议(决议 #691)

- 样本量: 14 条(真人策展 14 条);门槛 ≥100(其中 ≥30 真人)。
- **达标: ❌ 未达标**(协议已文档化,见下)

> 样本量协议(I-08,决议 #691):既有 must_* 人工金标池 = 12 条判分 + 2 条干扰项敏感度探针(W5–W8 / #21 人工因果链策展,human_curated=true)。扩至 ≥100(≥30 真人复审)需新一轮 Trust L1 人审排期:新样本需要新 T1 语料 + 人工因果链标注 + 抽检员复审,不是 Exit/harness 票内能诚实在一夜之间造出的。本期先立 Auditor 判定臂测量尺,交付 14 条全人工策展样本的真实读数;扩池挂后续工单,绝不伪造/合成样本充数(防假绿)。

## 全量 vs 真人子集分栏(决议 #691;本期全量 ⊆ 真人策展,两栏重合)

- 全量 n=12(matrix 桶,判分口径);真人子集 n=12(human_curated=true,W5–W8/#21 人工因果链策展)。
- 本期真人子集 = 全量;扩池引入非人审样本后,本表即成分栏判读(两栏分离)。

| 金标 \ 闸后 | 全量 fresh | 全量 stale | 全量 unknown | 真人 fresh | 真人 stale | 真人 unknown |
|---|---|---|---|---|---|---|
| fresh(活) | 4 | 0 | 0 | 4 | 0 | 0 |
| stale(死) | 0 | 4 | 0 | 0 | 4 | 0 |
| unknown(未知) | 0 | 0 | 4 | 0 | 0 | 4 |

## 闸后 3×3 混淆矩阵(金标 × 落档 status;matrix 桶 12 条)

| 金标 \ 闸后 | fresh | stale | unknown |
|---|---|---|---|
| fresh(活) | 4 | 0 | 0 |
| stale(死) | 0 | 4 | 0 |
| unknown(未知) | 0 | 0 | 4 |

- **false-accept**(金标 stale → 闸后 fresh): 0 条(0.0%)
- **false-reject**(金标 fresh → 闸后 stale): 0 条(0.0%)
- **unknown 率**(闸后 unknown / n): 4/12(33.3%)

> 与 #8 铁律的关系:报条数为判据、率仅随行参考(matrix.py「小样本不报百分比」口径不变);n=12 时率不具统计意义,阈值判读一律以条数为准。

> 口径注:mark_stale 路径上 Auditor 判 fresh/unknown 不拦 stale(安全不对称,ADR-0010)——false-accept 在该路径结构性趋零是设计使然,不是测量豁免;判定臂自身的 fresh 误判见下方原始判定矩阵。

## Auditor 原始判定 3×3(判定臂层读数;金标 × auditor verdict)

| 金标 \ 判定 | fresh | stale | unknown |
|---|---|---|---|
| fresh(活) | 4 | 0 | 0 |
| stale(死) | 0 | 4 | 0 |
| unknown(未知) | 0 | 0 | 4 |

> 层级声明(Anthropic 纪律 #1):n=12 为冒烟层读数,条数优先、率随行;不得冒充 ≥100 金标的统计结论。

## 敏感度附表(乙-i 维度混淆探针:#21 c13 客单价≠毛利 / c14 覆盖率≠渗透率;不进判分矩阵,不计通过线)

| sample_id | gold | auditor | dimension_match | 闸后落档 | 挂异议 |
|---|---|---|---|---|---|
| c13 | fresh | fresh | - | stale | 是 |
| c14 | fresh | stale | false | unknown | 是 |

> 期望:Auditor 识破维度混淆——判 fresh,或 stale 但 dimension_match=false(经闸打回 unknown)。stale + dimension_match=true = 被干扰项骗过,归人工定性。

## 每样本明细

| sample_id | 桶 | 路径 | gold | auditor | dm | 闸后 | 异议 | fallback | 真人策展 |
|---|---|---|---|---|---|---|---|---|---|
| c1 | matrix | mark_stale | stale | stale | true | stale | 否 | 否 | 是 |
| c2 | matrix | mark_stale | stale | stale | true | stale | 否 | 否 | 是 |
| c3 | matrix | mark_stale | stale | stale | true | stale | 否 | 否 | 是 |
| c7 | matrix | mark_stale | stale | stale | true | stale | 否 | 否 | 是 |
| c4 | matrix | fresh_attempt | fresh | fresh | - | fresh | 否 | 否 | 是 |
| c5 | matrix | fresh_attempt | fresh | fresh | - | fresh | 否 | 否 | 是 |
| c6 | matrix | fresh_attempt | fresh | fresh | - | fresh | 否 | 否 | 是 |
| c8 | matrix | fresh_attempt | fresh | fresh | - | fresh | 否 | 否 | 是 |
| c9 | matrix | fresh_attempt | unknown | unknown | - | unknown | 否 | 否 | 是 |
| c10 | matrix | fresh_attempt | unknown | unknown | - | unknown | 否 | 否 | 是 |
| c11 | matrix | fresh_attempt | unknown | unknown | - | unknown | 否 | 否 | 是 |
| c12 | matrix | fresh_attempt | unknown | unknown | - | unknown | 否 | 否 | 是 |
| c13 | sensitivity | mark_stale | fresh | fresh | - | stale | 是 | 否 | 是 |
| c14 | sensitivity | mark_stale | fresh | stale | false | unknown | 是 | 否 | 是 |

## 复现与漂移

- 判定臂层(Auditor 单轮判定)给定解码参数(temperature=0 同证据包同判定)逐位复现;托管端点在漂移,跨会话复现只能近似,此限制为留档声明。闸后落档经生产真值表(纯函数)逐位复现。
- 失败/异议条目归因人工定性;harness 只给机械矩阵,不判语义对错。
