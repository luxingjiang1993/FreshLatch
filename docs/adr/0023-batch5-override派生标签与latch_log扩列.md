# ADR-0023: Batch 5（ε）override 派生标签与 latch_log 扩列

- **状态**: Accepted
- **日期**: 2026-09-23
- **相关**: `docs/research/ε-override与void事件管道字段设计评估.md`、ADR-0006、ADR-0015、地图 #96 / 工单 #108

## 背景

人审 discard/renew 需要可机检的审计迹，以支持「人对抗机器判定」的可见性；若新增 `override` action，或把 override 率当成模型变好，会同时破坏 HumanLatch 动词封闭集与品类叙事。另建事件表则与「人审唯一写路径」漂移。

三条件齐备：难反转（表字段与谓词一旦被审计/导出依赖）；反直觉（override 不是第三按钮）；真取舍（派生标签 vs 新 action；扩 latch_log vs 新表）。

## 决策

1. **不**新增 action；仍为 `discard` | `renew`。
2. `override` 为写入时派生的 **bool 标签**：
   - `discard` ∧ `machine_status_before == fresh` → true
   - `renew` ∧ `machine_status_before ∈ {stale, unknown}` → true
   - 其余成功人审 → false
3. 扩 `latch_log`：必填 `machine_status_before`、`override`；可选 `run_id`；`reviewer_note` 可选沿用。`invalidation_list` 仍为作废单一真相；`rerun_log` 分立。
4. 时间线挂主张卡片；审计视图可滤 override；**不**进 Client Memo。
5. **禁止** override⇒模型变好；本批不锁 Override Rate 通过线，不声称动力学已验证。
6. 本 ADR 不授权 wayfinder 会话内 `/implement`（契约留给 Batch 5 `/to-spec`）。

## 后果

- to-spec/implement 须按本谓词与字段机检；不得用 override 计数作验收绿灯。
- 与 C1「Override Rate → Batch 5+」对齐：管道先于指标，指标仍未锁。

## 替代方案（被否决）

- 新 action=`override`。
- 新建 `latch_events` 表双写。
- 凡人审一律 override=true。
- 事件投影进 Client Memo。
- 本批锁定 Override Rate 通过线。
