# 离线产品质量闸

入口（零付费 LLM）：

`python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md`

| 文件 | 状态 |
|---|---|
| [PREREG.md](PREREG.md) | QG-02 已冻结。`owner_freeze: confirmed`。 |

通过线仍是 TBD 的列只报告数值，并与神经基线描述对照。A1、should-refuse / should-pass、new-over-old 保持 `unregistered`。QG-04 的 1 次基线重跑不在这条命令里。
