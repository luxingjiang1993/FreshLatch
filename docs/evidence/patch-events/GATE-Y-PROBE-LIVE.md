# GATE-Y-PROBE-LIVE

日期：2026-10-12 16:10:30 +0800（Asia/Shanghai · UTC+8）
票：GATE-Y-PROBE-LIVE · GitHub #552
父图：#517
Depends-on：#551 · #549
Trust：L1
Blast：none（本票只新建桥接页与本页，并跑既有探针；未改生产码）

- run_kind: live
- 授权指针: `docs/evidence/patch-events/SENS-LIVE-2-ACTIVATION.md`
  · ACTIVATION 合入: `2b7401ad2257f9c5d42311ca9d7635c5ef951909`（#549）
  · `activation_prerequisite_met`: 是（引用；本页不重判）
- SMOKE: `docs/evidence/patch-events/PE-Y-SMOKE-LIVE.md`
  · main tip / PR: `fee4267e025888d48013b32207c3c43c10861d52` · #551
  · smoke_passed: 是（引用；本页不重判）
- LIVE-2: `docs/evidence/patch-events/SENS-LIVE-2.md`
  · commit `c4b921aa7559b672f657c3ccdc44c0b7913c9224`
  · blob `9671b009ce1f3591fe4fc26da003e2fa8774301c`
- 冻结 S sha256: `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`
- sensitivity_passed: 是（引用 LIVE-2；本页不重判）
- 敏感性桥接: `docs/evidence/patch-events/GATE-Y-SENS-PREREQ-LIVE.md`（方案甲；未改写 `GATE-Y-SENSITIVITY.md`）
- gate_passed: 是
- 层身份: outcome-neutral · ≠ 乙成立 · ≠ 自动开 PE-Y-05 / n=400

`gate_passed=是` 只表示方向门 (C) 成立。它不等于乙成立，不等于自动开 PE-Y-05，不等于 n=400 / formal-y。

## (A) 页头前置

跑前核对，本页不重判敏感性。

| 项 | 核对 |
|---|---|
| ACTIVATION=`是` | `SENS-LIVE-2-ACTIVATION.md` 页首有 `activation_prerequisite_met=是`；合入 `2b7401ad2257f9c5d42311ca9d7635c5ef951909` |
| SMOKE `smoke_passed=是` | `PE-Y-SMOKE-LIVE.md`；main tip `fee4267e025888d48013b32207c3c43c10861d52` |
| LIVE-2 commit | `c4b921aa7559b672f657c3ccdc44c0b7913c9224` |
| LIVE-2 blob | `git rev-parse c4b921aa7559b672f657c3ccdc44c0b7913c9224:docs/evidence/patch-events/SENS-LIVE-2.md` = `9671b009ce1f3591fe4fc26da003e2fa8774301c` |
| 冻结 S | 按 `SENS-S-FREEZE-PROTOCOL.md` §7 现算 sha256 = `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19` |
| sensitivity_passed | 是（LIVE-2 / ACTIVATION 引用；S2=0.9000） |
| 桥接页 | parser 读到层身份=`真模型推理层`、`sensitivity_passed`=是、`activation_prerequisite_met`=是、`allows_real_probe`=是；该判定的 `gate_passed` 仍为否（敏感性不过门） |
| 不认 | stub、口头、旧 #507、夹具 `GATE-Y-PROBE.md`、历史失败页 `GATE-Y-SENSITIVITY.md`（S2 实测 0.7000） |

## (B) 真探针

- 命令:

```bash
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe \
  --authorize-send \
  --probe-auth-phrase '授权路线 Y 仓外探针发模型；不得激活。' \
  --out docs/evidence/patch-events/GATE-Y-PROBE-LIVE.md \
  --sensitivity-report docs/evidence/patch-events/GATE-Y-SENS-PREREQ-LIVE.md \
  --layer-note '真数据旁路 · live · outcome-neutral'
```

- 跑时 HEAD: `b8c2e64df96692666153ca4206075caa307f77ed`（桥接页已提交；探针模块相对 main `fee4267e025888d48013b32207c3c43c10861d52` 无改动）。CLI `--code-pin` 保持默认 `local`（钉死命令未另传）。
- n: 30（`load_pe_v2_formal_n30`）。解码 qwen-flash · temperature=0 · Decoding.seed=20261007。API seed 未传。
- 是否发模型: 是。sent=90；b2_diff_added=30。旁路 120 行 = 30 条主张 ×（C rewrite、T rewrite、B2 claim、B2 diff）。不是 n=120，也不是 formal-y。
- 旁路: `docs/evidence/patch-events/gate-y-probe-generations.jsonl`
- 旁路 sha256: `f72e2bd506a6fa75495efc62babc1db5d3af0185656c36873690709eef9ef8e0`
- exit code: 0
- stdout 摘录: `gate_passed=True k=11 awaiting=False` / `wrote /workspace/docs/evidence/patch-events/GATE-Y-PROBE-LIVE.md`

## (C) 方向门

判据只看探针主路径，不看下方只读冻结对照。

- k (T 自然放行): 11（≥ 10）
- T−C 固定 k 误放差点估计: 0.2727272727272727（> 0）
- T−B1 / T−B2（只报，不过门）: 0.09090909090909094 / 0.2727272727272727
- gate_passed: 是

方向门两条同时成立，所以页首写 `gate_passed: 是`。正式乙的点估计 >0.05 且区间下界 >0 不是本页条件。

## soak / 卫生（不定 gate_passed）

Windows CI（`.github/workflows/ci.yml` 的 ruff + pytest）只作卫生。本页不因 CI 绿或未绿改写方向门。链接随 PR #553 的 `ci` workflow。

## 失败回滚（若 gate_passed=否）

不适用。方向门成立。未改 τ / ρ / k_min / Cond。SMOKE 已过态保持。未开 PE-Y-05。未复活 #507。

## Trust / Blast

Trust L1。Blast none。

## 既有入口落盘正文

下列正文由 `python -m freshlatch.eval.patch_events_gate_y_probe` 按 `--out` 写盘。页首字段是本票要求的报告头，补在入口正文之前。入口正文里的 `gate_passed = True` 对应探针主表 k=11 与 T−C 点估计 >0。只读冻结对照表里的同名布尔不是本票过门证据。

# 仓外 GATE-Y 探针报告（可扔）

> **可扔 · 非乙成立 · 不进主表 · 不得升格为正式 RESULT-Y。**
> 本页是路线 Y（只冲乙 · 仅锁 T−C）的**仓外门闩探针**旁路产物。
> 本会话成功 ≠ 乙成立。最多「可建议人审激活」；**不**自行激活 `PREREG-Y`，**不**开正式主跑。
> `#479` / `GATE-K-PROBE` / `GATE-C-FIXTURE` / 敏感性 / 冒烟 / 夹具绿 **不得**升格为本页已过门。
> **层身份**：真数据旁路 · live · outcome-neutral。夹具绿 ≠ 真数据过门。

## 探针协议（跑前写死 · 禁止 HARKing）

### 敏感性硬前置（ADR-0041 · #530）

- 报告：`docs/evidence/patch-events/GATE-Y-SENSITIVITY.md`（可扔；≠ `gate_passed`）。
- 真数据探针须同时：`sensitivity_passed` ∧ `activation_prerequisite_met=真` ∧ 非 stub/夹具层 ∧ 机制针齐。
- **stub 层绿不得当作可激活/可探针前置已满足**。
- 未通过 → **硬拒绝**真数据探针（不得发探针、不得激活、不得正式跑）。
- 本页读取：`sensitivity_passed`=是；`activation_prerequisite_met`=是；层=`真模型推理层`；允许真数据探针=是。

### 过门判据（须同时 · 方向门 · 不用正式乙点>0.05）

1. T 自然放行 k ≥ 10
2. T−C 固定 k 误放差方向为正（点估计 > 0）

T−B1 / T−B2 差**必报**，**不**作过门条件。

任一条过门条件不满足 → `gate_passed=false`；建议句必须写：**不得激活 PREREG-Y；不得正式主跑。**

### 机制约束（不得放松 · ADR-0040 仪器针）

- **选取**：R（#437 / PR #458）
- **同 after**：T/B1 共用 T rewrite after，再分叉（#469 / PR #476）
- **生成对齐**：T/B1 提示软对齐（非 C 强制抄句）
- **仪器 ADR-0040**：非空 score；reject=−∞；主核验 mDeBERTa-v3 XNLI；B1/B2 拒识口径抄死（乙只记账）
- **敏感性前置**：GATE-Y-SENSITIVITY 通过 ∧ activation_prerequisite_met=真 ∧ 非 stub/夹具层；未过不得真数据探针/激活/正式跑
- **T 闸**：绑定 ∧ 核验；不过 hard reject
- **B1 闸**：仅核验；不过 hard reject
- **禁止**：金标/评委/用户裁决进 score；改 verify_edit 或放宽 reject 凑 k；加 n 伪抬 k；以 C 抄句当 Y 主路径；把 Cond 改成点>0.05；夹具/冒烟/敏感性升格 gate_passed

- **机制针齐**：是

### 样本针

- **n** = 30（`load_pe_v2_formal_n30()`，与正式同构造配额）
- **claim_id 顺序**：`a005,a006,a007,a008,a009,a010,a011,a012,b005,b006,b007,b008,b009,b010,b011,b012,c005,c006,c007,c008,c009,c010,c011,c012,d004,d005,d006,d007,d008,d009`
- 旁路生成：`docs/evidence/patch-events/gate-y-probe-generations.jsonl`（禁止写入 formal / formal-b / formal-y / formal-c）

### 解码针

- model = `qwen-flash`（登记 `qwen-flash`）
- temperature = `0`
- Decoding.seed = `20261007`（run_arms 作废检查）
- API seed = `None` — live_chat / DecodingParams 未传 seed；Decoding.seed 仅供 run_arms 作废检查

### 探针人令（真数据发模型）

- 逐字：`授权路线 Y 仓外探针发模型；不得激活。`
- 无此令时 `--authorize-send` **拒绝**；本令不得当作 PE-Y-05 正式激活令。
- 另须敏感性硬前置已通过；缺前置时即使有人令也**拒绝发探针**。

## 基线与代码针

- **代码针**：local
- **基线**：cursor/528-pe-y-sens-01-gate-y-016f + PE-Y-02/#495 tip + #530
- 机制缝：R + 同 after + 软对齐 + ADR-0040；过门 Cond 仍为 k≥10∧T−C点>0（方向门）

## 发送状态

- **是否发模型**：`是`

- 已按探针人令向旁路路径发送探针生成。
- sent=90；b2_diff_added=30
- path=`/workspace/docs/evidence/patch-events/gate-y-probe-generations.jsonl`

## 探针主表（旁路生成）

| 臂 | 自然放行 | 自然误放 | 固定 k 误放 |
|---|---:|---:|---:|
| T | 11 | 3 | 0.2727272727272727 |
| B1 | 12 | 4 | 0.3636363636363636 |
| B2 | 30 | 15 | 0.5454545454545454 |
| C | 30 | 15 | 0.5454545454545454 |

- **k** = 11
- **T−C** 固定 k 误放差 = 0.2727272727272727（过门条件）
- **T−B1** 固定 k 误放差 = 0.09090909090909094（只报告 · 不过门）
- **T−B2** 固定 k 误放差 = 0.2727272727272727（只报告 · 不过门）
- **gate_passed** = `True`

## 只读冻结对照（非探针 · 非过门证据）

> 回放 `docs/evidence/patch-events/formal-generations.jsonl`：仅作机制后差方向对照。
> **不得**把本对照升格为 GATE-Y 过门；亦不得把 `GATE-K-PROBE` / `GATE-C-FIXTURE` 升格为本页已过门。

| 臂 | 自然放行 | 自然误放 | 固定 k 误放 |
|---|---:|---:|---:|
| T | 17 | 6 | 0.3529411764705883 |
| B1 | 18 | 7 | 0.4117647058823529 |
| B2 | 30 | 15 | 0.5294117647058824 |
| C | 30 | 15 | 0.5294117647058824 |

- **k** = 17
- **T−C** 固定 k 误放差 = 0.1764705882352941（过门条件）
- **T−B1** 固定 k 误放差 = 0.05882352941176466（只报告 · 不过门）
- **T−B2** 固定 k 误放差 = 0.1764705882352941（只报告 · 不过门）
- **gate_passed** = `True`

## 门闩判定表（探针主路径 · 冲乙）

| # | 条件 | 观测 | 进 gate_passed？ | 满足？ |
|---|---|---|---|---|
| 1 | T 自然放行 k ≥ 10 | k = 11 | 是 | 是 |
| 2 | T−C 差方向为正 | 点估计 = 0.2727272727272727 | 是 | 是 |
| — | T−B1 差（只报告） | 点估计 = 0.09090909090909094 | **否** | 是 |
| — | T−B2 差（只报告） | 点估计 = 0.2727272727272727 | **否** | 是 |

**gate_passed = `True`**

## 结论与建议

### 可建议人审激活（清单 · 本缝仍不激活）

> 注意：若本页层身份为夹具/合成，**夹具绿 ≠ 真数据过门**；不得据此激活。

1. 人审本页数字与代码针 / 名单针 / 解码针；确认层身份为真数据探针。
2. 人写 `PREREG-Y` 激活批注（日期、仓库针、本报告路径）。
3. 人决定是否正式主跑（须另授 PE-Y-05 正式令）。
4. **本 Cloud Agent 不激活、不正式主跑、不填 RESULT-Y 成立格。**

## 复算 / 发送入口（零歧义）

```bash
# 默认：写本报告 + 只读对照 + 不发模型（停在可发送边界）
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe

# 只打印判定，不写盘
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe --no-write

# 若旁路生成已存在：只复算（零 LLM）
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe --recompute-only

# 仅在敏感性硬前置已过 + 人明文探针人令之后（本窗默认不做真探针）：
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe \
  --authorize-send \
  --probe-auth-phrase '授权路线 Y 仓外探针发模型；不得激活。'
```

## 边界

- 可扔；非乙成立；不进主表；不得升格 RESULT-Y；未激活 PREREG-Y。
- 不改甲/乙/丙定义；不复活路线 A；不回写 B/C 冻结归档。
- 不金标打分；不放宽 hard reject；不加 n 凑 k；不把 Cond 改成点>0.05。
- 禁止把 `#479` / `GATE-K-PROBE` / `GATE-C-FIXTURE` / 敏感性 / 冒烟当作本页已过门依据。
