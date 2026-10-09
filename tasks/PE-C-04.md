# PE-C-04 · 激活 PREREG-C + 一次正式主跑 + RESULT-C 抄表（Gate）

## Parent

Part of #484（spec）· #490 · 地图 #482 · 决议 #483 · 前置壳 #488 / PE-C-03

## Destination

人令齐备后：写 `PREREG-C` 激活批注 → 一次正式主跑（`--authorize-send`）→ 同一次主比较抄入 `RESULT-C` 成立格。不保证甲。禁止改 B 归档、禁止 HARKing、禁止复用 #479 当 C 过门。

## 人令闸（缺则停 · 禁止自批）

本票 **Blocked**，直至会话出现真人令原文（逐字）：

> 批准激活 PREREG-C 并正式主跑一次。

探针令（「授权路线 C 仓外探针发模型；不得激活。」）**不得**当作本票激活/主跑授权。

## Acceptance criteria

- [x] 会话含上述正式人令原文；否则不得改 `PREREG-C` 激活态、不得 `--authorize-send`、不得填 RESULT-C 成立格
- [x] `PREREG-C` 文首改为已激活；激活批注登记日期、仓库针、GATE-C 依据（不得升格 #479）
- [ ] 仅一次正式主跑写入 `formal-generations-c.jsonl`；禁止写 `*-b.jsonl` / 旧 `formal-generations.jsonl`
- [ ] RESULT-C 三行 false-accept 与 k **只抄**同一次主比较；成立格不得手填、不得抄 GATE/B 数字
- [ ] Evidence 三行：typecheck · tests · paths
- [ ] 未改 `PREREG-B` / `RESULT-B` / `formal-generations-b`；未复活 A；ALT 不进主表

## Agent Guards

- **ID**: PE-C-04 · **Trust**: Gate · **Blast**: eval + evidence
- **Paths**: `docs/evidence/patch-events/PREREG-C.md`；`RESULT-C.md`；`formal-generations-c.jsonl`；`src/freshlatch/eval/patch_events_formal_c.py`；相关单测
- **Do-not-touch**: B 归档成立格；甲定义；reject/绑定放宽；金标进 score；同页二跑 B

## Blocked by

人令已到（2026-10-09 会话）。门闩依据诚实登记为 `GATE-C-FIXTURE`（fixture 层）；#479 未升格。
