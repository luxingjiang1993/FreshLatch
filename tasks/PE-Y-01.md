# PE-Y-01 · formal-y 旁路骨架（默认不发）

## Parent

规格卷 27 · ADR-0037 · PR [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493)

## Destination

克隆 `patch_events_formal_b` 为 `patch_events_formal_y`：激活守卫读 `PREREG-Y`；产物 `formal-generations-y.jsonl`；默认不发模型。不激活、不改 B/C 归档。

## Acceptance criteria

- [ ] Given `PREREG-Y` 文首为未激活，When 运行 `PYTHONPATH=src python -m freshlatch.eval.patch_events_formal_y --authorize-send`，Then 非零退出且不写 `formal-generations-y.jsonl`
- [ ] Given 默认入口（无 `--authorize-send`），When 运行模块，Then 不发模型；`--recompute-only` 可在无生成文件时安全失败或空跑且零 LLM
- [ ] 任意成功写盘路径不得触及 `formal-generations-b.jsonl` / `formal-generations-c.jsonl` / `formal-generations.jsonl`（单测断言路径常量）
- [ ] `decoding_pin()`（或等价）返回 model=`qwen-flash`、temperature=`0`、Decoding.seed=`20261007`、API seed=`None`
- [ ] `python -m compileall -q src` 退出 0；`pytest tests/unit/test_pe_formal_y.py` 绿

## Agent Guards

- **ID**: PE-Y-01
- **Title**: `feat(eval): formal-y 旁路骨架（默认不发）`
- **Trust**: Watch
- **Blast**: none
- **Paths**:
  - `src/freshlatch/eval/patch_events_formal_y.py`（new · adapt from B）
  - `tests/unit/test_pe_formal_y.py`（new）
  - `docs/evidence/patch-events/PREREG-Y.md`（只读守卫目标；本票不改激活态）
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/eval/patch_events_formal_b.py` @ `origin/cursor/prereg-b-formal-main-9809`
  - Pin: `4ec045b96aa23a19acd2822accdac52658366958`
  - URL: https://github.com/luxingjiang1993/FreshLatch/blob/4ec045b96aa23a19acd2822accdac52658366958/src/freshlatch/eval/patch_events_formal_b.py
  - What changed: 路径/守卫改读 `PREREG-Y`、产物 `formal-generations-y.jsonl`、日志目录 `patch-events-y`；名单入口预留 n=400（可与 PE-Y-03 衔接）
  - Why not copy as-is: 乙页旁路必须与 B 产物/激活态隔离，禁止污染 `formal-generations-b`
  - License note: 同仓代码
- **Tests**: added（`test_pe_formal_y.py`）
- **Do-not-touch**: `PREREG-B`/`RESULT-B`/`formal-generations-b`；`PREREG-C`/`RESULT-C`/`formal-generations-c`；`compare_primary` 成立数学；C 抄句主路径；金标进 score；激活 `PREREG-Y`
- **Rollback**: 删除 `patch_events_formal_y.py` 与对应单测；不回写 B/C

### Provenance status

- result: pass
- notes: adapt 自 B tip 钉死 SHA；URL+路径双源；What changed / Why 已填

### Evidence *(after Matt `/implement`)*

- typecheck:
- tests:
- paths:

## Blocked by

实现 base 建议叠 `origin/cursor/prereg-b-formal-main-9809`（R+同 after+软对齐）。若 `main` 无 B 缝，实现票须写明依赖分支，禁止从空分 top-k 重开。

## Handoff

`enrich done | PE-Y-01 | ready | next: before-implement PE-Y-01（新会话 /implement）`
