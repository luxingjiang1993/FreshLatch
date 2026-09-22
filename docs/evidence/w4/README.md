# W4 验收证据目录(docs/evidence/w4/)

目录登记即 J5 判据的一部分(ADR-0007 后果)。全部材料 commit;录屏 mp4 不进 git(体积),本地留档、检查表记路径。

| 文件 | 内容 | 状态 |
|---|---|---|
| `checklist.md` | 锁定判据检查表(§7.4 底稿,头部锁定语) | ✅ 已落(W4 验收前锁定);逐项签字待终审 |
| `machine-results.md` | 机器层执行结果(P2/J1 表/J2 三 seed/对照/护栏,自动生成) | ✅ 已生成(以 checklist 签字为准) |
| `restatement.md` | 复述测试记录:盲看原话 + 探针回答 + 判定(W4 与 W12 共用仪器) | ⏳ 待真人盲看(P4/J3) |
| `repro-check.md` | AFK 会话复现抽查:基准列已写入,待冷启动会话填复现列 | ⏳ 待抽查(J4) |
| `false-green-control.md` | 2026-09-21 假绿对照原始摘录(格子保留;文首已盖作废印) | 作废,不可引用 |
| `false-green-control-20260921-void.md` | 该次运行作废备忘(可引用的只有「这次运行作废」) | ✅ [落盘:2026-09-21 假绿对照运行作废备忘](https://github.com/luxingjiang1993/FreshLatch/issues/44) |
| `false-green-control-prereg.md` | 新假绿对照预登记(改 prompt / 新运行前锁定:问法、通过线、作废线、decoding) | ✅ [决议:新假绿对照预登记](https://github.com/luxingjiang1993/FreshLatch/issues/46);评估见 `docs/research/新假绿对照预登记设计评估.md` |
| （读数边界,非本目录文件） | 预登记首跑 0/4 → 对照不成立后的唯一可引用句;本阶段不追成立 | ✅ [决议:假绿对照不成立后的可引用边界](https://github.com/luxingjiang1993/FreshLatch/issues/56);评估见 `docs/research/假绿对照不成立后可引用边界设计评估.md` |
| `p1-p5-precheck.md` | W3 预检 P1–P5 留档(P2 机器层✅;P1/P4/P5 待人工) | ⏳ 待人工补录 |
| `reports/report-<date>.md` + raw JSON | 金标运行记录(含 decoding 参数,进 git) | ✅ 编排器落盘(每 seed 一份) |
| 录屏 mp4(本地) | J1 一镜到底点回录屏;J3 红线复核录屏 | ⏳ 待录制,路径登记进 checklist |
