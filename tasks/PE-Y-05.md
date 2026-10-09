# PE-Y-05 · 激活 PREREG-Y + 一次正式主跑 + RESULT-Y 抄表（Gate）

## Parent

规格卷 27 · ADR-0037 · PR #493 · 前置 PE-Y-01…04

## Destination

人令齐备且 `GATE-Y-PROBE` 过门后：写激活批注 → 一次 `--authorize-send` → 同一次主比较抄入 RESULT-Y。不保证乙。禁止称甲。禁止改 B/C 归档。

## 人令闸（缺则停 · 禁止自批）

本票 **Blocked**，直至会话出现真人令原文（逐字）：

> 批准激活 PREREG-Y 并正式主跑一次。

探针令不得当作本票授权。

## Acceptance criteria

- [ ] 会话含上述正式人令；否则不得改激活态、不得 `--authorize-send`、不得填成立格
- [ ] `GATE-Y-PROBE` `gate_passed=true`（真数据层）；激活批注登记日期/仓库针/报告路径
- [ ] 仅一次正式写入 `formal-generations-y.jsonl`（n 行=1600 四臂×400，或实现票写死等价）；禁写 b/c/旧 jsonl
- [ ] RESULT-Y 成立格只抄同一次比较；分层按 Y 口径；Evidence 三行
- [ ] 未改 B/C 冻结页；未称甲

## Agent Guards

- **ID**: PE-Y-05 · **Trust**: Gate · **Blast**: eval + evidence  
- **Paths**: `PREREG-Y.md`；`RESULT-Y.md`；`formal-generations-y.jsonl`；`patch_events_formal_y.py`  
- **Do-not-touch**: B/C 归档；甲定义；reject 放宽；同页二跑；加 n  

## Blocked by

PE-Y-01…04 齐 · GATE-Y 过门 · 正式人令。
