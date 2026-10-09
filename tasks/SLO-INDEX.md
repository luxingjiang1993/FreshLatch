# 生产补丁/放行 SLO · 票清单

> 规格：`docs/spec/24-生产补丁放行SLO.md`  
> 运营真源：`docs/ops/生产补丁放行SLO.md`  
> ADR-0034 · 评估见 `docs/research/生产补丁放行SLO设计评估.md`  
> **Frontier：SLO-01**  
> 人批 `/before-implement` 之前禁止业务代码 `/implement`。

| ID | Title | Blocked by | Trust | Blast | Prov | Acceptance? |
|----|-------|------------|-------|-------|------|--------------|
| SLO-01 | 文档闭环与禁词扫描 | — | Watch | none | pass | yes |
| SLO-02 | 硬闸违例计数清单 | SLO-01 | Watch | api | pass | yes |
| SLO-03 | 改侧抽检协议 A2/A3/A4 | SLO-01 | Watch | none | pass | yes |
| SLO-04 | 再验失败率周报 A6 | SLO-01 | Watch | api | pass | yes |
| SLO-05 | 误放/误拒成对观测 B2/B3 | SLO-01, SLO-03 | Watch | none | pass | yes |
| SLO-06 | 作废率与 override C1/C2 | SLO-01 | Watch | api | pass | yes |
| SLO-07 | 复验主业 D1/D3/D4 | SLO-01, SLO-02 | Watch | api | pass | yes |

## enrich 摘要

全票已填 ID · Acceptance(≥1) · Paths；触旧码票含 Provenance。无 Gate（无 auth/db/pay）。默认 Trust=Watch（与 agent-guards 一致）。

## 维度覆盖核对

- 改：SLO-03（A2/A3/A4）· SLO-04（A6）  
- 放行：SLO-05（B2/B3）· SLO-02（B6/B7）  
- 人审：SLO-06（C1/C2）· SLO-02（C3/C5）  
- 复验：SLO-07（D1/D3/D4）  
- 文档/边界：SLO-01（含与 RESULT-Y 丙防火墙）  
