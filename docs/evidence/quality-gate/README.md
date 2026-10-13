# 离线产品质量闸

入口（零付费 LLM）：

`python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md`

| 文件 | 状态 |
|---|---|
| [PREREG.md](PREREG.md) | QG-02 已冻结。`owner_freeze: confirmed`。 |
| [QG-04-RESULT.md](QG-04-RESULT.md) | QG-04 冒烟重跑。k10 名次与 hit 0/1 相对冻结基线逐题一致。 |

通过线仍是 TBD 的列只报告数值，并与神经基线描述对照。A1、should-refuse / should-pass、new-over-old 保持 `unregistered`。QG-04 的 1 次基线重跑不在这条命令里，结果见 [QG-04-RESULT.md](QG-04-RESULT.md)。
