# TASK / ticket — PE-B-03

## Ticket
- **ID**: PE-B-03 / GitHub #439
- **Title**: `feat(#436): 路线 B n=100 正式名单确认与缺额缝`
- **Paths**: `docs/evidence/patch-events/SPLIT-pe-v2-route-b.json`；`src/freshlatch/eval/patch_events_split.py`；`src/freshlatch/eval/patch_events_formal.py`；`tests/unit/test_pe_route_b_split.py`

## Agent Guards
- **Blast**: eval split / evidence
- **Trust**: Watch
- **Acceptance**:
  1. n=100 名单路径写死；pilot id 不进入正式 n。
  2. 缺额可写入结果字段；不得为凑齐改小 `PREREG-B` 配额。
  3. 不激活正式主跑；不发模型。
  4. `python -m compileall -q src` 与相关 pytest 绿。
- **Provenance**:
  - Kind: adapt
  - Source: `docs/evidence/patch-events/SPLIT-pe-v2.json` n100
  - Pin: `cursor/437-compare-primary-fixed-k-r-8da7` `4c972c8`
  - What changed: 写死路线 B 名单路径与语料缺额结果语义
  - Why not copy as-is: 路线 B 需独立路径与缺额字段，且不以旧 n=30 为主门槛
- **Do-not-touch**: PREREG-B 配额表；主张复验金标；正式主跑激活；发模型

### Provenance status
- result: pass

### Evidence *(after Matt `/implement`)*
- typecheck: `python -m compileall -q src` · exit 0
- tests: `pytest tests/unit/test_pe_route_b_split.py …` · green
- paths: `SPLIT-pe-v2-route-b.json` · `patch_events_split.py` · `patch_events_formal.py` ok

## Handoff
`done | PE-B-03 | next=human Watch acceptance on #439`
