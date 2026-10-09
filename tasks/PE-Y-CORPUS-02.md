# PE-Y-CORPUS-02 · 重针 SPLIT-pe-v2-route-y.json（离开不可激活）

> GitHub Issue: [#501](https://github.com/luxingjiang1993/FreshLatch/issues/501) · blocked-by [#500](https://github.com/luxingjiang1993/FreshLatch/issues/500)

## Parent

ADR-0038 · PE-Y-03 / PR [#497](https://github.com/luxingjiang1993/FreshLatch/pull/497) · 前置 **PE-Y-CORPUS-01** / [#500](https://github.com/luxingjiang1993/FreshLatch/issues/500)

## Destination

在 pe_v2 库存已可满 n=400（CORPUS-01 Acceptance 绿）之后，刷新 `docs/evidence/patch-events/SPLIT-pe-v2-route-y.json`：写出恰好 400 条互异 `claim_id` 的正式名单（四层各 100，层内 50/50），与 pilot 无交；`status` 离开「不可激活」；`load_pe_v2_formal_n400` 可加载 400 条。**仍不**激活 `PREREG-Y`；**仍不**派 PE-Y-05；**仍不**改配额表。

## Acceptance criteria

- [x] Given CORPUS-01 后的 pe_v2，When 生成/刷新 `SPLIT-pe-v2-route-y.json`，Then `counts.n400==400` 且 `gaps.n400==0`；四层 `by_stratum.n400.*.gap==0`；层内 correct/bad 各 50
- [x] `n400` 与 pilot（镜像自 `SPLIT-pe-v2.json`）`claim_id` 无交集；400 条互异
- [x] `status` ≠ `不可激活`；`activation.ready`（或等价字段）允许 loader 成功；**但** `PREREG-Y.md` 文首仍为未激活（本票不得写激活批注）
- [x] `load_pe_v2_formal_n400()` 返回恰好 400 条；缺额 `RuntimeError(不可激活…)` 路径保留给将来再次缺额，不得删除 fail-closed 语义
- [x] 共形：针内记录 leftover≥5/层 **或** `conformal_reserve: 未做`；不得为共形改小 `quotas_target`（仍钉 total=400）
- [x] 单测：`pytest tests/unit/test_pe_split_y.py tests/unit/test_pe_formal_y.py` 绿；缺额用例改为「人为制造缺额针」或保留对称负例，**不得**删掉「禁静默改小」断言
- [x] `python -m compileall -q src` 退出 0
- [x] **边界**：未激活 PREREG-Y；未发模型；未开 PE-Y-05；未改 `PREREG-Y` 配额表；未改写 `SPLIT-pe-v2.json` 已发布键成员

## Agent Guards

- **ID**: PE-Y-CORPUS-02
- **Title**: `feat(eval): 重针 pe_v2 路线 Y n=400 名单（离开不可激活）`
- **Trust**: Watch
- **Blast**: none
- **Paths**:
  - `docs/evidence/patch-events/SPLIT-pe-v2-route-y.json`
  - `src/freshlatch/eval/patch_events_formal_y.py`（仅 loader/ready 接线，若需）
  - `tests/unit/test_pe_split_y.py`
  - `tests/unit/test_pe_formal_y.py`
  - `docs/evidence/patch-events/SPLIT-pe-v2.json`（只读来源 · 不改写已发布成员）
- **Provenance**:
  - Kind: adapt
  - Source: PE-Y-03 `SPLIT-pe-v2-route-y.json` + `load_pe_v2_formal_n400`（PR #497）
  - Pin: 实现时记录扩容后 `pe_v2_docket.json` sha256 与 route-y 针 blob
  - What changed: 把缺额空针换成满额 n400 名单；status 离开不可激活
  - Why not copy as-is: PE-Y-03 在 178 池上只能记缺额
  - License note: 同仓
- **Tests**: updated
- **Do-not-touch**: `PREREG-Y` 配额与激活批注；B/C 冻结页；`SPLIT-pe-v2.json` pilot/n30/n100 成员；比较器/成立尺；PE-Y-05；发模型
- **Rollback**: 恢复缺额针（status=不可激活 · n400=[]）；loader 继续 fail-closed

### Provenance status

- result: pass
- notes: Kind=adapt。Blocked by CORPUS-01。Watch。扩容绿 ≠ 过门 ≠ 乙成立 ≠ 已激活。

### Evidence *(after Matt `/implement`)*

- typecheck: `python -m compileall -q src` → 0
- tests: `pytest tests/unit/test_pe_split_y.py tests/unit/test_pe_formal_y.py` → 20 passed
- paths: ok · `SPLIT-pe-v2-route-y.json` status=`名单已齐·可加载` · n400=400 · docket_sha256=`10b351677518ac9432796ded23a58998c118e09569bcf3d6fe5eaf921621addb`

## Blocked by

- **PE-Y-CORPUS-01** Acceptance 全勾（库存可满 400+共形规划）
- PE-Y-03 / `SPLIT-pe-v2-route-y.json` 与 `load_pe_v2_formal_n400` 已在实现基线上（PR #497 或已合入等价针）

## Handoff

`enrich done | PE-Y-CORPUS-02 | blocked-by CORPUS-01 | next: CORPUS-01 绿后 before-implement PE-Y-CORPUS-02`
