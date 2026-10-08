# TASK / ticket — ALT-04

## Ticket
- **ID**: ALT-04
- **Title**: `test(eval): 平行轨防火墙（主缝零 diff / 禁写主表）`
- **Paths**:
  - 新建 `tests/unit/test_pe_alt_firewall.py`
  - 可选：旁路写入辅助若存在，须注入可测的 path guard
- **Executor**: `/implement`（零 LLM）
- **先读**: 规格防火墙验收；ADR-0035 §防火墙

本票把防火墙写成回归门。不改产品行为，只加测。

## 行为

1. 断言旁路模块导入/比较不写 `docs/evidence/patch-events/PREREG.md`、主 `RESULT.md`。
2. 断言本平行轨测试目录不含「甲成立」升格用语（可与 ALT-02 合并检查）。
3. 断言 `compare_primary` 仍可被既有主链单测调用（跑一条现有 pe primary 冒烟或 import 完整性）。
4. 不改五处冻表面文件。

## Agent Guards
- **Blast**: none
- **Trust**: Watch
- **Acceptance**:
  1. Given 防火墙单测，When `pytest tests/unit/test_pe_alt_firewall.py -q`，Then 退出码 0。
  2. Given 模拟旁路「写结果」入口（若有），When 目标路径为旧 PREREG 或主 RESULT，Then 拒绝/抛错。
  3. Given `git diff --stat` 对本票，When 查看五处冻表面相关路径（README 导语等若在 Do-not-touch 列表），Then 本票未改。
- **Provenance**:
  - Kind: new
  - Source: ADR-0035；规格防火墙节
  - What changed: 防火墙测试
- **Tests**: added
- **Do-not-touch**: 五处冻表面内容；主预注册正文

### Provenance status
- result: pass
- notes: 新测试；建议 ALT-01 后跑。

### Evidence *(after Matt `/implement`)*
- typecheck: `python -m compileall -q src` → exit 0
- tests: `pytest tests/unit/test_pe_alt_firewall.py tests/unit/test_pe_alt_natural.py -q` → 11 passed, exit 0
- paths: ok · `tests/unit/test_pe_alt_firewall.py`（未触 Do-not-touch：五处冻表面 / 主预注册 / `compare_primary`）

## Handoff
`2026-10-08 | ALT-04 | implemented | 待收口；勿自行 close #453`

## Blocked by
ALT-01（建议；若仅静态路径断言可先开，但仍标依赖旁路模块存在）

## GitHub
- Issue: #453
