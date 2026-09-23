# Batch 4（δ）ACCEPTANCE

> 父规格：[#127](https://github.com/luxingjiang1993/FreshLatch/issues/127)
> 实现票：[#128](https://github.com/luxingjiang1993/FreshLatch/issues/128) / [#129](https://github.com/luxingjiang1993/FreshLatch/issues/129) / [#130](https://github.com/luxingjiang1993/FreshLatch/issues/130)
> 决策锁：ADR-0019 / ADR-0020 / ADR-0021
> 主缝：`active_pack`（`tests/unit/test_active_pack.py`）
> 释放规矩：`docs/research/C4-合成数据释放协议草稿.md`

## 验收层（不得跨层升格）

| 层 | 内容 | 读法 |
|---|---|---|
| invariant | 软 Port / FP 可观察部分 | 切到 P1 后路径、gold 键同构、claim_id 隔离、冻结面契约 |
| demo | 切包可见性、synthetic | 页面/API 能看到包名或问题句，并标明 synthetic |
| 文档 | C4 引用 | 卡在仓且被本文件引用；默认未释放 |
| smoke | 可选 P1 `run_gold` | **本批未跑**。未跑不得写入 Port 通过线 |

Port 通过线不含 LLM 采样。单次 `run_gold` 即使将来补跑，也只是 smoke / 仅表明，须写明模型、温度、日期、n；失败不得靠改第一课题 gold 或改闸通过。

## 1. 主缝 invariant

- 默认 `active_pack` = `thesis-1`：corpus / docket / gold / SQLite 与切换前第一课题路径一致。
- `FRESHLATCH_ACTIVE_PACK=p1-quotettl` 时，路径指向 `data/packs/p1-quotettl/`。
- P1 gold 顶层键与第一课题 gold 同构；最小桶各至少 1 条 must_stale / must_fresh / must_unknown；must_quarantine 为空；must_stale 的 causal_chain 含 `t1_doc` 与 `anchor`。
- claim_id 使用 `q*`，与第一课题 `c*` 不相交。
- 装载器（`freshlatch.packs`）只解析路径并打开对应 DB，不 import `gates` / `roles` / `latch`。
- 六维枚举仍为既有六值。SQLite 既有 SCHEMA 不加列（无 `pack_id` 列）。
- 第一课题 `data/eval/gold.json`、`data/t0_docket.json`、`data/corpus/**` 字节锁在主缝测试里。本批不为 P1 改它们凑绿。

## 2. demo

切到 P1 后，`/api/claims` 的 `pack.pack_id`、`pack.synthetic` 与问题句可观察。同一导入 → T1 三卡合成入口仍可用，界面既有 SYNTHETIC 徽章保留。无新主 CTA。

## 3. C4 文档纪律

引用 `docs/research/C4-合成数据释放协议草稿.md`。

**默认未释放。** 推进 main ≠ 已释放。C4 卡存在不等于数据集已对外可用。「已释放」须同时满足该卡 §6 门闩（SPDX + 人批 + 语义化版本 + 分发物一致）。本批不执行对外发布。

## 禁止升格

不得把本批读成下列任何一句：

- 「多垂类已 Port」
- 「数据集已对外可用」
- 「软 Port 过 = 产品已验证」

δ backlog（P3→P5→P2→P8→P4→P9）与 P10/P11 不在本批交付。本批没有 QuoteTTL 字段引擎、含税守恒、ERP、真连接器、自动商业裁决或 Mem0。
