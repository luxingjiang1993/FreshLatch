# PE-C-01 · 强制抄句生成缝 + 同 after 继承夹具

## Parent

Part of #484（spec）· #485 · 地图 #482 · 决议 #483

## Destination

实装路线 C 增量：T `after_text` 强制抄句硬契约；正确槽可抄保证；保持 T/B1 同 after 再分叉。不激活 `PREREG-C`，不发模型，不改 B 归档。

## Acceptance criteria

- [x] T 契约路径产出的 after 去空白后与 `evidence_text` 逐字相同（单测可证；非仅断言提示词含子串）
- [x] 同 after 夹具：绑定缝类坏样上 T reject / B1 release 可复现
- [x] 未放松 `verify_edit` 逐字语义；T 核验不过仍 hard reject
- [x] 未改 `PREREG-B` / `RESULT-B` / `formal-generations-b`；未激活 `PREREG-C`
- [x] `python -m compileall -q src` 与相关 `pytest` 绿

## Evidence

- typecheck: `python -m compileall -q src` · 0
- tests: `pytest tests/unit/test_pe_copy_constrained_c.py` (+ same_after/align 回归) · 15 passed
- paths: `patch_events_copy_constrained.py` · `test_pe_copy_constrained_c.py` · base=`B tip #480` 叠入

## Agent Guards

- **ID**: PE-C-01 · **Trust**: Watch · **Blast**: none  
- **Paths**: `src/freshlatch/eval/patch_events_copy_constrained.py`；`tests/unit/test_pe_copy_constrained_c.py`  
- **Do-not-touch**: B 归档；旧 PREREG；主比较成立定义；ALT 主表；金标进 score  

## Blocked by

无。实现基线已叠入 `origin/cursor/prereg-b-formal-main-9809`（R + 同 after + 核验）。
