# Batch 5（ε）ACCEPTANCE

> 验收层声明：管道字段 = invariant；读法源可见性 = demo/文案；对抗目录 = RESEARCH 文档纪律。禁止跨层升格。
> 决策锁：ADR-0022、ADR-0023；评估见 `docs/research/ε-如何读复验文案链设计评估.md`、`docs/research/ε-对抗套件目录与版本化设计评估.md`、`docs/research/ε-override与void事件管道字段设计评估.md`。
> 本文件不改 `data/eval/gold.json`。不锁 Override Rate 通过线。不报对抗统计通过率。不重审假绿对照是否成立。

## 1. 读法源（文案 / demo，非缝）

预锁可引用句（改字 = 本批文案验收作废并须重登）：

> 「如何读复验」读法源已投影至复验单旁路与 Client Memo 附注；ACCEPTANCE 仅表明误读边界（非法律/非自动、void≠stale、demo≠验证）可被核对在场，不表明产品验证成功、付费意愿或对抗仪器已过。

投影出口（单一真相 `src/freshlatch/reading_source.py`，变体 C）：

| 出口 | 取自 | 可观察表面 |
|---|---|---|
| 复验单旁路 | 身份 / 机器 / 人 / 边界缩写 | UI `#how-to-read`；复验单 Markdown |
| Client Memo 附注 | 边界 + 人/机一句 | `render_client_memo_markdown` 附注；免责仍为非法律/非自动 |
| ACCEPTANCE | 上列预锁整句 | 本节 |

主叙事仍卖作废。Client Memo 不进人审事件流，不含 Lead/Critic，不含「建议进入/不进入」。

禁止升格：Time-to-Sheet/rubric ⇒ 付费或一期闭合；demo 可读 ⇒ 付费或验证成功；文案在场 ⇒ 对抗仪器已过。

非缝测试：`tests/unit/test_reading_source.py`。

## 2. override 管道（invariant，主缝）

主缝：HumanLatch 人审写路径 `apply_decisions` → `latch_log` 行形状。

谓词（ADR-0023，成功人审）：

| 条件 | override |
|---|---|
| discard 且 machine_status_before == fresh | true |
| renew 且 machine_status_before ∈ {stale, unknown} | true |
| 其余成功 | false |

失败或幂等跳过 discard 不新增对抗语义行。动词仍仅 discard|renew。`invalidation_list` 仍为作废单一真相。`rerun_log` 分立。不新增 override action，不新建 `latch_events` 表。

主张时间线可读人审作废/续命，并带 override 标记。审计侧可滤 override=true（`list_latch_rows(override=True)` 与审计视图「只看 override=true」）。过滤不是模型变好。

禁止升格：override⇒模型变好。本批不锁 Override Rate 通过线。

主缝测试：`tests/unit/test_override_latch.py`。

## 3. 对抗目录（RESEARCH 纪律，非缝）

`docs/research/adversarial/README.md` 与 `INDEX.md` 在仓，`catalog_version` 为 `0.1.0` 骨架。INDEX 无 `pass_rate` 列/字样。ATK-FG-01..03 与 ATK-CS-01..04 只指针，不复制通过线正文。

目录存在 ≠ 仪器已过 / 对抗成立。本批不跑对抗夹具、不报统计通过率、不把 skeleton 行写成仪器已过。

非缝测试：`tests/unit/test_batch5_acceptance.py`。
