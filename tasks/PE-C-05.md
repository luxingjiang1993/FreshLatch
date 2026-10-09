# PE-C-05 · 消融/次要指标填格 + 抽检导出（Watch）

## Parent

Part of #484（spec）· #491 · 正式主跑 #490（结果丙）

## Destination

零 LLM 回放 `formal-generations-c`：填 RESULT-C 次要/消融节；导出抽检配对。不改主比较成立格；不发模型；不改 B 归档；不称甲。

## Acceptance criteria

- [x] 消融只在 T 上；另起 bootstrap_ablation；主比较三行 / k 指纹不变
- [x] 次要格只抄函数输出；放行 0 → 误放/可复验为无定义
- [x] 抽检按 spotcheck 流可复现；无用户标签时一致率未填；非真人盲审
- [x] 零 LLM；未改 B 归档；Evidence 三行

## Evidence

- typecheck: `python -m compileall -q src` · 0
- tests: `pytest tests/unit/test_pe_post_c.py` · 5 passed
- paths: `patch_events_post_c.py` · `RESULT-C.md`（PE-C-POST）· `spotcheck-c-export.md/.json`

## Agent Guards

- **ID**: PE-C-05 · **Trust**: Watch · **Blast**: none
- **Paths**: `src/freshlatch/eval/patch_events_post_c.py`；`RESULT-C.md`；`spotcheck-c-export.*`；`tests/unit/test_pe_post_c.py`
- **Do-not-touch**: 主比较成立格手改；B 归档；正式二次发送；甲定义

## Blocked by

无（#490 主跑已完成）。
