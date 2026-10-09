# PE-Y-01 · formal-y 旁路骨架（默认不发）

## Parent

规格卷 27 · ADR-0037 · PR [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493)

## Destination

克隆 `patch_events_formal_b` 为 `patch_events_formal_y`：激活守卫读 `PREREG-Y`；产物 `formal-generations-y.jsonl`；默认不发模型。不激活、不改 B/C 归档。

## Acceptance criteria

- [ ] 未激活时 `--authorize-send` 拒绝并非零退出
- [ ] 默认入口不发模型；`--recompute-only` 可零 LLM
- [ ] 禁止写入 `formal-generations-b/c.jsonl` 与旧 `formal-generations.jsonl`
- [ ] 解码针与 B 一致（qwen-flash / temp=0 / Decoding.seed=20261007 / API seed=None）
- [ ] `python -m compileall -q src` 与相关 `pytest` 绿

## Agent Guards

- **ID**: PE-Y-01 · **Trust**: Watch · **Blast**: none  
- **Paths**: `src/freshlatch/eval/patch_events_formal_y.py`；`tests/unit/test_pe_formal_y.py`  
- **Do-not-touch**: B/C 归档；`compare_primary` 成立数学；C 抄句主路径；金标进 score  

## Blocked by

建议 base = B 机制 tip（R+同 after+软对齐）。若 main 无 B 缝，票须写明依赖分支。
