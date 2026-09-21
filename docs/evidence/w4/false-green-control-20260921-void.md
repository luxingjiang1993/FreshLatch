# 备忘:2026-09-21 假绿对照运行作废

> 本备忘可引用的唯一事实:**2026-09-21 这次假绿对照运行作废,其判定表不得作为对照读数引用。**
> 不得摘引下表条数去论证「对照成立/不成立」、语料陷阱是否够像、或通过线该定在哪。
> 工单:[落盘:2026-09-21 假绿对照运行作废备忘](https://github.com/luxingjiang1993/FreshLatch/issues/44)
> 纪律:ADR-0007(判据预先锁定;事后改判据 = 该次运行无效;demo 层不得假装成测量结论)。

## 作废对象

- 运行时刻(UTC):`2026-09-21T14:22:42.374205+00:00`
- 原始摘录:`docs/evidence/w4/false-green-control.md`
- 原始报告:`reports/report-20260921-222242.md` + `reports/report-20260921-222242.json`(`kind=control_run`)
- 同一次编排器写入的机器层摘要:`docs/evidence/w4/machine-results.md`「假绿对照」节
- 模型 / 解码:`qwen-flash`;`temperature=0.0`;`seed=None`(temp=0 时 seed 无采样意义,ADR-0007 §5)

本备忘**不**改写上述文件里的原始格子;只宣布它们不可引用。`gold.json`、`report-20260921-134134`、W4 检查表已锁定判据、产品代码均不动。

## 仪器自相矛盾(作废理由)

`src/freshlatch/eval/control.py` 的 `CONTROL_PROMPT`(本工单**未改**这一段)同时要求两件事:

1. 「该主张**现在**是否仍然成立」——问的是签发之后的当下。
2. 「只依据给定材料回答,**不要引入材料之外的信息**」——给定材料只有签发时的 T0 摘录。

对照设计要测的是:同模型无工具、只读 T0 时,已死主张应被自信地判 `alive`(假绿),产品必须红。prompt 却把「现在」设成问题,又禁止使用 T0 以外的任何信息。对「现在」的诚实答案是 `unknown`,不是假绿。

这次读数与该矛盾同构,因此不能当对照结果用:

| 口径 | 格子 |
|---|---|
| 14 条(金标 12 + 干扰项 c13/c14) | 12 条 `unknown` |
| must_stale | 仅 c2 为 `alive`;c1/c3/c7 为 `unknown` |
| must_unknown | c9 为 `alive`(其余 unknown) |
| 干扰项(期望基线 `alive`) | c13/c14 均为 `unknown` |

这些数字只证明仪器在问不可答的「现在」,不证明语料、金标或产品闸。

## 本工单明确不做的事

- **不改** `CONTROL_PROMPT`。prompt 仍停在仓库现状;改它属于新仪器,不是对这次运行的勘误。
- **不重跑** LLM。作废不靠再跑一遍同一支矛盾 prompt 来「确认」。
- **不得用** 这次的 1/4(must_stale 假绿)去校准下一次通过线——那是看到结果之后改判据,ADR-0007 称为 HARKing,会把下一次运行一并作废。
- **不新开 ADR**。ADR-0007 已覆盖:判据先于运行写死;事后修改 = 该次无效;层级必须标明。宣布一次有缺陷仪器的运行不可引用,是在执行该纪律,不是新的难反转取舍。新对照的判据、作废线、decoding 由尚未落盘的预登记决定,见 [决议:新假绿对照预登记](https://github.com/luxingjiang1993/FreshLatch/issues/46)。

## 新对照的门闩

[决议:新假绿对照预登记](https://github.com/luxingjiang1993/FreshLatch/issues/46) 已落盘:`docs/evidence/w4/false-green-control-prereg.md`(评估见 `docs/research/新假绿对照预登记设计评估.md`)。

此后改 `CONTROL_PROMPT` 必须逐字拷贝该预登记锁定正文;新运行必须用该通过线 / 作废线 / decoding。仍不得用 2026-09-21 格子校准任何数字。未按锁定件改 prompt 就跑,读数不可引用。
