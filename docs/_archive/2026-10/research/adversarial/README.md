# 对抗套件目录（Adversarial Catalog）

> **catalog_version**: `0.1.0`  
> **状态**: Batch 5（ε）骨架 — RESEARCH  
> **决议**: [ε: 对抗套件目录与版本化](https://github.com/luxingjiang1993/FreshLatch/issues/107) · ADR-0022 · 评估见 `docs/research/ε-对抗套件目录与版本化设计评估.md`

## 纪律

1. 本目录是**索引骨架**，不是跑分证书。  
2. **目录存在 ≠ 仪器已过 / 对抗成立 / 假绿已根治**。  
3. 本批**不报**统计通过率；INDEX **无** `pass_rate` 列。  
4. 与金标、预登记、既有 ATK-CS **只指针**，不复制通过线正文。  
5. 改条目语义必须 **bump** `catalog_version`；退休用 `status=retired`。  
6. 不重审已关假绿对照是否成立（分条见 #102）。

## 家族

| family | 含义 | 本版 |
|---|---|---|
| `FG` | 假绿 / 对照类仪器指针 | 占位 ATK-FG-01..03（skeleton） |
| `CS` | checksum 攻击面 | **不入库正文**；见 β 评估 ATK-CS-01..04 指针节 |

## 文件

- `INDEX.md` — 条目表  
- 跑次落盘不进本目录（evidence / reports 另路径）
