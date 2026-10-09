# PE-C-03 · RESULT-C 抄表壳与 B 负结果附录句

## Parent

Part of #484（spec）· #488 · 地图 #482 · 决议 #483

## Destination

落 `RESULT-C.md` 抄表壳：字段与 `PREREG-C` 对齐；成立格仅允许从同一次主比较抄入；文面含 B 负结果附录固定引用句。未激活/未主跑时成立格保持未跑。不发模型、不激活。

## Acceptance criteria

- [x] RESULT-C 壳字段与 PREREG-C 对齐；成立格仅允许从同一次主比较抄入
- [x] 文面含 B 负结果附录固定引用句（#480 丙 · 效应偏小）
- [x] 未激活/未主跑时成立格保持未跑；禁止手填、禁止抄 GATE/B 数字进成立格

## Evidence

- typecheck: `python -m compileall -q src` · 0
- tests: `pytest tests/unit/test_pe_result_c_shell.py` · 2 passed
- paths: `docs/evidence/patch-events/RESULT-C.md` · `test_pe_result_c_shell.py`

## Agent Guards

- **ID**: PE-C-03 · **Trust**: Watch · **Blast**: none
- **Paths**: `docs/evidence/patch-events/RESULT-C.md`；`tests/unit/test_pe_result_c_shell.py`
- **Do-not-touch**: RESULT-C 成立格填数；PREREG-C 激活；B 归档；formal-generations-b

## Blocked by

无。壳已随 #483 四件套落盘；本票锁 Acceptance 单测并关单。
