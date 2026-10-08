# TASK / ticket — ALT-02

## Ticket
- **ID**: ALT-02
- **Title**: `test(eval): 平行轨夹具可分开（T vs B2 / B1′）`
- **Paths**:
  - 扩展或新建 `tests/unit/test_pe_alt_fixtures.py`（可与 ALT-01 测文件合并，但 Acceptance 独立可指）
  - 可选夹具数据：`docs/evidence/patch-events-alt/fixtures/`（若落盘）
  - 依赖 ALT-01 导出的闸判 / `compare_alt_natural`
- **Executor**: `/implement`（零 LLM）
- **先读**: 规格 §夹具与升级数字、PROBE-LOCK 升级闸

本票把「夹具层可分开」写成可执行断言。正式语料另说。不发模型。

## 行为

夹具最小集：

1. 坏修改 + 同文 → T reject、B2 release → T-B2 自然误放差 > 0。
2. 坏修改 + 同文 → T reject、B1′ release（B1′ 无 binding id）→ T-B1 自然误放差 > 0。
3. 至少一条正确修改使整集 T 自然放行数 ≥ 1，且 T 自然放行率 ≥ max(1/n, 0.05)。
4. 文档/测试名不得出现「甲成立」。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given ALT-01 已合入，When `python -m pytest tests/unit/test_pe_alt_fixtures.py -q`（或约定文件），Then 退出码 0。
  2. Given 上列三条夹具，When `compare_alt_natural`，Then T-B2 与 T-B1 差均 > 0，且 T 放行数/率满足门槛。
  3. Given 测试源码，When `rg -n '甲成立|结果甲' tests/unit/test_pe_alt_*.py`，Then 无匹配。
- **Provenance**:
  - Kind: new
  - Source: 规格夹具节；ALT-01 API
  - What changed: 夹具断言
  - Why not copy as-is: 新探针层
- **Tests**: added
- **Do-not-touch**: 主 PREREG/RESULT；`compare_primary`；未授权发模型

### Provenance status
- result: pass
- notes: 新夹具测；依赖 ALT-01。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-08 | ALT-02 | ready | 依赖 ALT-01；/before-implement ALT-02 后新会话 /implement`

## Blocked by
ALT-01

## GitHub
- Issue: #451
