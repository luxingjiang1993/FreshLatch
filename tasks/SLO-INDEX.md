# 生产补丁/放行 SLO · 票清单

> 规格：`docs/spec/24-生产补丁放行SLO.md`  
> 运营真源：`docs/ops/生产补丁放行SLO.md`  
> ADR-0034 · 评估见 `docs/research/生产补丁放行SLO设计评估.md`  
> **Frontier：无**（SLO-01…07 均已 `/implement`，待人 Watch 合入）  
> 合入顺序见文末「PR 栈」。

| ID | Title | Status | PR |
|----|-------|--------|-----|
| SLO-01 | 文档闭环与禁词扫描 | implement-done | [#509](https://github.com/luxingjiang1993/FreshLatch/pull/509) |
| SLO-02 | 硬闸违例计数清单 | implement-done | [#512](https://github.com/luxingjiang1993/FreshLatch/pull/512) |
| SLO-03 | 改侧抽检协议 A2/A3/A4 | implement-done | [#510](https://github.com/luxingjiang1993/FreshLatch/pull/510) |
| SLO-04 | 再验失败率周报 A6 | implement-done | [#513](https://github.com/luxingjiang1993/FreshLatch/pull/513) |
| SLO-05 | 误放/误拒成对观测 B2/B3 | implement-done | [#514](https://github.com/luxingjiang1993/FreshLatch/pull/514) |
| SLO-06 | 作废率与 override C1/C2 | implement-done | [#511](https://github.com/luxingjiang1993/FreshLatch/pull/511) |
| SLO-07 | 复验主业 D1/D3/D4 | implement-done | [#515](https://github.com/luxingjiang1993/FreshLatch/pull/515) |

## enrich 摘要

全票已填 ID · Acceptance(≥1) · Paths；触旧码票含 Provenance。无 Gate（无 auth/db/pay）。默认 Trust=Watch。

## 维度覆盖核对

- 改：SLO-03（A2/A3/A4）· SLO-04（A6）  
- 放行：SLO-05（B2/B3）· SLO-02（B6/B7）  
- 人审：SLO-06（C1/C2）· SLO-02（C3/C5）  
- 复验：SLO-07（D1/D3/D4）  
- 文档/边界：SLO-01（含与 RESULT-Y 丙防火墙）  

## PR 栈（建议合入顺序）

并行枝可在 #509 合入后任意顺序合入；串行枝须按依赖：

1. **#509** SLO-01 → `main`
2. 并行（base 均为 SLO-01 枝）：**#512** SLO-02 · **#510** SLO-03 · **#513** SLO-04 · **#511** SLO-06  
3. 串行：**#514** SLO-05（base=SLO-03）须在 #510 之后；**#515** SLO-07（base=SLO-02）须在 #512 之后  

全部 draft；人批 Watch 后再标 ready / merge。Agent 不自批 Gate。
