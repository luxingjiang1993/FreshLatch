# PE-C-06 · ALT 附录测量（Watch · 不进主成立）

## Parent

Part of #484 · #492 · 先验 ALT #435/#450–#453 · 主跑 #490（结果丙）

## Destination

合入平行轨 `patch_events_alt`；对路线 C 写 `ALT-APPENDIX-C`（夹具可分开 + 正式 C T after 同文四闸附录）；RESULT-C 仅指针。零 LLM；不进主成立；不称甲。

## Acceptance criteria

- [x] ALT 同文四闸 + compare_alt_natural + compare_alt_fixed_k_appendix 可跑（夹具；零 LLM）
- [x] `ALT-APPENDIX-C.md` 层身份标明不进主成立
- [x] RESULT-C 仅 ALT 指针；主比较三行 / k 指纹不变
- [x] 未改 B 归档；未改 compare_primary 行为
- [x] typecheck + 相关 pytest 绿

## Evidence

- typecheck: `python -m compileall -q src` · 0
- tests: `pytest tests/unit/test_pe_alt_*.py` · 23 passed
- paths: `patch_events_alt.py` · `patch_events_alt_appendix_c.py` · `ALT-APPENDIX-C.md` · RESULT-C `PE-C-ALT`

## Agent Guards

- **ID**: PE-C-06 · **Trust**: Watch · **Blast**: none
- **Do-not-touch**: 主成立格；ALT 并主表；B 归档；发模型；甲定义
