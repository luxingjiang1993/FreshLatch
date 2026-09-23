# β+ 档 3a ACCEPTANCE

> 验收层声明：写侧启用 = invariant（确定性闸行为）；不得升格「fresh checksum 半边已启用 = 统计结论」「Agent 绿灯带 basis = latch 已证明」「demo 展示完整 list = 产品验证成功」。
> 决策锁：ADR-0024、ADR-0017；规格 `#148`；实装 `#149` → `#150` → `#151`。
> 本文件不改 `data/eval/gold.json`。不自动 void。不重开 ADR-0024 / ADR-0025。

## 1. 预锁 invariant（改字 = 本批 invariant 验收作废并须重登）

> 档 3a：Agent fresh 路径须在进入 `rule_gate` 前，由 `t1_evidence_ids` 按 `doc_id` 去重构造 `validity_basis` 为 `[{doc_id, checksum}, …]`（checksum 为入库指纹）；闸对 list 全员用语料现算 sha256 比对（禁读库列），任一不符 → `CHECKSUM_MISMATCH` 不得 fresh。renew 写一元 list；存量单对象经显式批迁为一元 list，验收无双读残留；UI/导出展示完整 list。本句不得升格为统计结论或「checksum 已证明 latch」。

## 2. 主缝与负例勾选

主缝：Agent fresh 构造 `validity_basis` list（`src/freshlatch/runner.py:build_fresh_validity_basis`）→ `rule_gate` 逐项比对（`src/freshlatch/gates/rule_gate.py`）→ 仅绿后写回 claim；renew 写一元 list（`src/freshlatch/gates/human_latch.py`）；UI/导出完整 list（`src/freshlatch/ui/app.py`、`src/freshlatch/sheet.py`）。

| 负例 | 期望 | 落点 | 勾选 |
|---|---|---|---|
| 多 doc evidence 去重构造 list | `claim.validity_basis` 为 `[{doc_id, checksum}, …]`，按 doc_id 去重 | `tests/unit/test_fresh_validity_basis.py` | [x] |
| 篡改 list 中非首元 doc 的语料 | `CHECKSUM_MISMATCH`，不得 fresh | `tests/unit/test_fresh_validity_basis.py` | [x] |
| evidence 点不回 chunk | 不可构造 basis，禁止空 list 充绿 | `tests/unit/test_fresh_validity_basis.py` | [x] |
| 存量单对象 basis | 显式批迁后为一元 list，无 dict 残留 | `tests/unit/test_fresh_validity_basis.py` | [x] |
| UI/导出展示 | 完整 list，禁止只显示 `[0]` | `tests/unit/test_beta_plus_3a_acceptance.py` | [x] |
| 与档 3b 交界 | 带 basis 的 Agent-fresh 篡改语料后可被 `apply_rot` 掉灯 | `tests/unit/test_beta_plus_3a_acceptance.py` | [x] |

## 3. 禁升格声明

- 本批 ACCEPTANCE **不得**升格为：checksum 已证明 latch；Agent 绿灯带 basis = 产品已验证；写侧启用 = 统计结论；demo 展示完整 list = 测量可信。
- `checksum_fn` 必须语料现算；禁读与 basis 同源库列（套套逻辑硬禁）。
- 人审动词仍仅 `discard|renew`；机械行 `basis_rot` 的 override 不得为 true。
- 不改 gold；不自动 void；无 basis 的 Agent fresh 仍受既有不变量约束。

## 4. 测试挂载

- 构造与闸：`tests/unit/test_fresh_validity_basis.py`（`#150`）
- 跨轮腐烂（档 3b 共享模块）：`tests/unit/test_basis_rot.py`、`tests/unit/test_ui_basis_rot.py`
- 本文件自检：`tests/unit/test_beta_plus_3a_acceptance.py`（`#151`）
