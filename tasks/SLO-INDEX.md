# 生产补丁/放行 SLO · 票指针

> **生产观测 ≠ 乙尺。** 本页未编辑 `RESULT-Y` / `PREREG-Y` / SESOI。  
> Provenance：adapt [#508](https://github.com/luxingjiang1993/FreshLatch/pull/508) `tasks/SLO-INDEX.md` @ `b24b6f5`。  
> **只做指针。** SLO-01…07 的票正文留在未合并的 #508，不抄进本分支（其中若干 Paths 指向 `src/`，本票 Blast=docs/obs）。  
> 本波交付真源：[#556](https://github.com/luxingjiang1993/FreshLatch/issues/556) / [#557](https://github.com/luxingjiang1993/FreshLatch/issues/557)（索引）· [#558](https://github.com/luxingjiang1993/FreshLatch/issues/558)（SLI 1·2 协议）· [`docs/ops/生产观测最小6-索引.md`](../docs/ops/生产观测最小6-索引.md)。  
> `#508` **Keep draft · No merge until Matt**。`#514` 同样保持 candidate，不合并。  
> SLO-05 的协议正文在 [`docs/ops/抽检-放行误放误拒.md`](../docs/ops/抽检-放行误放误拒.md)（#558）。本页只留指针，不另建 `tasks/SLO-05.md`。T3–T6 仍不做。

| ID | #508 上的题目 | 与最小 6 | PR 去留 | 本波票 | 本 PR |
|----|----------------|----------|---------|--------|-------|
| SLO-01 | 文档闭环与禁词扫描 | 不是主 SLI | #509 low | — | 指针 |
| SLO-02 | 硬闸违例计数 | 支撑层，不是主 SLI | #512 defer | — | 不做 |
| SLO-03 | 改侧抽检 A2/A3/A4 | 不是主 SLI | #510 low | — | 不做 |
| SLO-04 | 再验失败率 A6 | 不是主 SLI | #513 defer | — | 不做 |
| SLO-05 | 误放/误拒 B2/B3 | SLI 1·2 | #514 candidate · 不合并 | T2 #558 | 指针 → 抽检协议 |
| SLO-06 | 作废率与 override C1/C2 | SLI 4 主用 C2；C1 旁注 | #511 candidate | T3 #559 | 不做 |
| SLO-07 | 复验主业 D1/D3/D4 | D1/D5 可喂 SLI 6 | #515 defer | T6 #562 另摘口径 | 不做 |

另三张本波票没有宽表 ID，避免新编号：T4 #560 unknown/abstention（SLI 3）、T5 #561 P95+fallback（SLI 5）。定义在索引，不在这里升成 SLO-08/09。

规格 `docs/spec/24-生产补丁放行SLO.md` · 防火墙 ADR-0042 · 宽表 `docs/ops/生产补丁放行SLO.md`。
