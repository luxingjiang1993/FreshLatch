# TASK / ticket — ALT-01

## Ticket
- **ID**: ALT-01
- **Title**: `feat(eval): 平行轨同文四闸 + compare_alt_natural`
- **Paths**:
  - 新建 `src/freshlatch/eval/patch_events_alt.py`（或拆分自洽；须导出同文闸判与 `compare_alt_natural`）
  - 新建 `tests/unit/test_pe_alt_natural.py`
  - 只读：`patch_events_verify.py`、`patch_events_exp.py`、`patch_events_arms.py`
- **Executor**: `/implement`（零 LLM，零网络）
- **先读**: `docs/spec/24-patch-events-平行轨对照探针.md`、`docs/evidence/patch-events-alt/PROBE-LOCK.md`、ADR-0035、#448

本票只交付旁路同文四闸与主表比较。不做附录固定 k、不写主 RESULT、不发模型。

## 行为

1. 输入：同文候选（共享 `after_text`、`claim_id`、`construction_gold`、T 用 `evidence_id`/`evidence_text`、`ingested_t1`）。
2. 闸判：C 恒放行；T 须绑定已入库 T1 + `verify_edit` 不过 hard reject；B1′ 无 `evidence_id`、延迟可见 `evidence_text`，核验不过 reject 且 arm 不得写成 T；B2 有 after_text 即放行，核验只记 `reverify_ok`。
3. `compare_alt_natural`：各臂自然放行数/率与自然误放率（放行 0 → 误放无定义，禁止 0.0）；差 = 对照自然误放 − T 自然误放。
4. 不得修改 `compare_primary`。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 新模块与单测，When `python -m compileall -q src` 且 `python -m pytest tests/unit/test_pe_alt_natural.py -q`，Then 退出码 0；测试不读 `DASHSCOPE_API_KEY`。
  2. Given 同文坏修改夹具：T reject、B2 release，When `compare_alt_natural`，Then T-B2 自然误放差 > 0（对照−T）。
  3. Given 某臂自然放行数为 0，When 取自然误放率，Then 为无定义/`None`，不得为 0.0。
  4. Given 本票 diff，When 检查 `docs/evidence/patch-events/PREREG.md` 与主 `RESULT.md` 及 `patch_events_metrics.compare_primary`，Then 本票未改这些文件/函数行为。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/eval/patch_events_arms.py#_decide`、`patch_events_verify.verify_edit`
  - What changed: 新增旁路同文闸与 `compare_alt_natural`
  - Why not copy as-is: 主缝固定 k/分头生成；本轨信息集与指标不同
  - License note: 本仓
- **Tests**: added
- **Do-not-touch**:
  - `compare_primary` 选取/成立定义
  - `docs/evidence/patch-events/PREREG.md`、主 `RESULT.md`、冲甲 `PREREG-B.md`（若存在）
  - 五处冻表面；未授权发模型

### Provenance status
- result: pass
- notes: 新旁路模块 + 只读复用 verify；不改主缝。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-08 | ALT-01 | ready | /before-implement ALT-01 后新会话 /implement`

## Blocked by
None (can start immediately).

## GitHub
- Issue: #450
