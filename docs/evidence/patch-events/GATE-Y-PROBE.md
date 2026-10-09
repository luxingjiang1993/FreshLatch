# 仓外 GATE-Y 探针报告（可扔）

> **可扔 · 非乙成立 · 不进主表 · 不得升格为正式 RESULT-Y。**
> 本页是路线 Y（只冲乙 · 仅锁 T−C）的**仓外门闩探针**旁路产物。
> 本会话成功 ≠ 乙成立。最多「可建议人审激活」；**不**自行激活 `PREREG-Y`，**不**开正式主跑。
> `#479` / `GATE-K-PROBE` / `GATE-C-FIXTURE` 与夹具绿 **不得**升格为本页已过门。
> **层身份**：真数据探针层。夹具绿 ≠ 真数据过门。

## 探针协议（跑前写死 · 禁止 HARKing）

### 过门判据（须同时）

1. T 自然放行 k ≥ 10
2. T−C 固定 k 误放差方向为正（点估计 > 0）

T−B1 / T−B2 差**必报**，**不**作过门条件。

任一条过门条件不满足 → `gate_passed=false`；建议句必须写：**不得激活 PREREG-Y；不得正式主跑。**

### 机制约束（不得放松）

- **选取**：R（#437 / PR #458）
- **同 after**：T/B1 共用 T rewrite after，再分叉（#469 / PR #476）
- **生成对齐**：T/B1 提示软对齐（非 C 强制抄句）
- **T 闸**：绑定 ∧ 核验；不过 hard reject
- **B1 闸**：仅核验；不过 hard reject
- **禁止**：金标/评委/用户裁决进 score；改 verify_edit 或放宽 reject 凑 k；加 n 伪抬 k；以 C 抄句当 Y 主路径

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

## 基线与代码针

- **代码针**：5d7cd17
- **基线**：cursor/pe-y-merge-corpus-eng-be80 @ 5d7cd17（#505 tip）
- 机制缝：B tip R + 同 after + 软对齐；过门条件对齐乙（仅 T−C）

## 发送状态

- **是否发模型**：`是`

- 已按探针人令向旁路路径发送探针生成。
- sent=90；b2_diff_added=30
- path=`/workspace/docs/evidence/patch-events/gate-y-probe-generations.jsonl`

## 探针主表（旁路生成）

| 臂 | 自然放行 | 自然误放 | 固定 k 误放 |
|---|---:|---:|---:|
| T | 11 | 4 | 0.3636363636363636 |
| B1 | 12 | 5 | 0.4545454545454545 |
| B2 | 30 | 15 | 0.5454545454545454 |
| C | 30 | 15 | 0.5454545454545454 |

- **k** = 11
- **T−C** 固定 k 误放差 = 0.1818181818181818（过门条件）
- **T−B1** 固定 k 误放差 = 0.09090909090909088（只报告 · 不过门）
- **T−B2** 固定 k 误放差 = 0.1818181818181818（只报告 · 不过门）
- **gate_passed** = `True`

## 只读冻结对照（非探针 · 非过门证据）

> 回放 `docs/evidence/patch-events/formal-generations.jsonl`：仅作机制后差方向对照。
> **不得**把本对照升格为 GATE-Y 过门；亦不得把 `GATE-K-PROBE` / `GATE-C-FIXTURE` 升格为本页已过门。

| 臂 | 自然放行 | 自然误放 | 固定 k 误放 |
|---|---:|---:|---:|
| T | 3 | 0 | 0 |
| B1 | 4 | 1 | 0.3333333333333333 |
| B2 | 30 | 15 | 0.6666666666666666 |
| C | 30 | 15 | 0.6666666666666666 |

- **k** = 3
- **T−C** 固定 k 误放差 = 0.6666666666666666（过门条件）
- **T−B1** 固定 k 误放差 = 0.3333333333333333（只报告 · 不过门）
- **T−B2** 固定 k 误放差 = 0.6666666666666666（只报告 · 不过门）
- **gate_passed** = `False`

## 门闩判定表（探针主路径 · 冲乙）

| # | 条件 | 观测 | 进 gate_passed？ | 满足？ |
|---|---|---|---|---|
| 1 | T 自然放行 k ≥ 10 | k = 11 | 是 | 是 |
| 2 | T−C 差方向为正 | 点估计 = 0.1818181818181818 | 是 | 是 |
| — | T−B1 差（只报告） | 点估计 = 0.09090909090909088 | **否** | 是 |
| — | T−B2 差（只报告） | 点估计 = 0.1818181818181818 | **否** | 是 |

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

# 仅在人明文探针人令之后（本窗默认不做真探针）：
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_y_probe \
  --authorize-send \
  --probe-auth-phrase '授权路线 Y 仓外探针发模型；不得激活。'
```

## 边界

- 可扔；非乙成立；不进主表；不得升格 RESULT-Y。
- 不改甲/乙/丙定义；不复活路线 A；不回写 B/C 冻结归档。
- 不金标打分；不放宽 hard reject；不加 n 凑 k。
- 禁止把 `#479` / `GATE-K-PROBE` / `GATE-C-FIXTURE` 当作本页已过门依据。
