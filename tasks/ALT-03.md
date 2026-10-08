# TASK / ticket — ALT-03

## Ticket
- **ID**: ALT-03
- **Title**: `feat(eval): compare_alt_fixed_k_appendix（附录 only）`
- **Paths**:
  - 扩展 `src/freshlatch/eval/patch_events_alt.py`：新增 `compare_alt_fixed_k_appendix`
  - 新建或扩展 `tests/unit/test_pe_alt_appendix.py`
- **Executor**: `/implement`（零 LLM）
- **先读**: 规格附录 API；PROBE-LOCK「固定 k 只进附录」

本票只做附录仪表，证明升级路径不消费它。不改主 `compare_primary`。

## 行为

1. 实现 `compare_alt_fixed_k_appendix`：可按旁路自然放行集取固定 k（思想对齐路线 B 的 R，但函数名与落盘均在 alt）。
2. 提供明确标记/返回结构，使任何 `upgrade_tier` 辅助函数若存在也不得读取附录「成立」字段。
3. 单测：主表 `compare_alt_natural` 结果在调用附录前后不变；升级判定夹具只喂自然率。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 附录函数与单测，When `python -m compileall -q src` 且 `pytest tests/unit/test_pe_alt_appendix.py -q`，Then 退出码 0。
  2. Given 同一输入，When 先 `compare_alt_natural` 再 `compare_alt_fixed_k_appendix`，Then 自然率主表字段不变。
  3. Given 升级判定辅助（若本票引入）或文档化约定测试，When 只提供附录输出，Then 不得判为「可分开」硬通过（须失败或显式拒绝输入）。
- **Provenance**:
  - Kind: adapt
  - Source: `compare_primary` 固定 k 思想（只读）；ALT-01 自然率 API
  - What changed: 附录旁路函数
  - Why not copy as-is: 不得进主缝/升级闸
- **Tests**: added
- **Do-not-touch**: 主 `compare_primary`；冲甲预注册；主 RESULT

### Provenance status
- result: pass
- notes: 附录旁路；依赖 ALT-01。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-08 | ALT-03 | ready | 依赖 ALT-01；可与 ALT-02 并行（若 ALT-01 已合）`

## Blocked by
ALT-01

## GitHub
- Issue: #452
