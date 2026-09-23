# β+ 档 3b ACCEPTANCE

> 验收层声明：降级路径 = invariant（确定性）；不得升格「跨轮重检上线 = 统计结论」「checksum 已证明 latch」「demo 掉灯 = 产品验证成功」。
> 决策锁：ADR-0025；评估见 `docs/research/β+-档3b-跨轮腐烂重检设计评估.md`；规格 #140；实装 #143 / #144。
> 本文件不改 `data/eval/gold.json`。不自动 void。不重开 ADR-0017 / ADR-0024。不等待档 3a。

## 1. 预锁 invariant（改字 = 本批 invariant 验收作废并须重登）

> 档 3b：对 `status==fresh` 且 `validity_basis` 非空的主张，复验入口与 UI 拉单/渲染均须经同一 `check_basis`（语料现算 sha256，禁读库列）；不符则 `apply_rot` → `unknown` + 机械码（如 `BASIS_CHECKSUM_MISMATCH`），写 `latch_log`，保留 basis 与 `last_confirmed_at`，且复验入口不进 Lead。无 basis 的 fresh 不检。本句不得升格为统计结论或「checksum 已证明 latch」。

## 2. 双触发负例勾选

主缝：共享 `check_basis` / `apply_rot`（`src/freshlatch/gates/basis_rot.py`）。两条路径均须持久化（主张 status + `latch_log`），禁止只改展示。

| 路径 | 负例 | 期望 | 落点 | 勾选 |
|---|---|---|---|---|
| 复验入口 | 篡改已续命 basis 对应语料后点复验 | `unknown` + `BASIS_CHECKSUM_MISMATCH` + `latch_log action=basis_rot`；本轮不进 Lead | `tests/unit/test_basis_rot.py` | [x] |
| 复验入口 | 无 basis 的 fresh / voided | 不因本机制降级 | 同上 | [x] |
| 复验入口 | 已 unknown 再触发 | 幂等；不重复写成功降级行 | 同上 | [x] |
| UI 拉单 | 篡改语料后 GET `/api/claims` | 持久化观察点为 `unknown`（非仅响应体）；`basis_rot` 行在库 | `tests/unit/test_ui_basis_rot.py` | [x] |
| UI 拉单 | 无 basis 的 fresh 拉单 | 不因此降级 | 同上 | [x] |

## 3. 禁升格声明

- 本批 ACCEPTANCE **不得**升格为：checksum 已证明 latch；跨轮重检上线 = 统计结论；demo 掉灯 = 产品验证成功；Override Rate / 对抗通过率。
- `checksum_fn` 必须语料现算；禁读与 basis 同源库列。
- 人审动词仍仅 discard|renew；机械行 `basis_rot` 的 override 不得为 true。
- 不改 gold；不自动 void；无 basis 的 Agent fresh 不检（半激活诚实；不偷开档 3a）。

## 4. 测试挂载

- 主缝：`tests/unit/test_basis_rot.py`（#143）
- UI 拉单：`tests/unit/test_ui_basis_rot.py`（#144）
- 本文件自检：`tests/unit/test_beta_plus_3b_acceptance.py`
- 演示录屏 / 面试取材：`DEMO_ORAL.md`（评估 §6 + 本文件预锁句；demo 层，不升格）
