# 仓外抬 k 探针报告（可扔）

> **可扔 · 非甲 · 不进主表 · 不得升格为正式 RESULT-B。**
> 本页是机制缝（选取 R + T/B1 同 after + 生成对齐）齐备后的**仓外抬 k 探针**旁路产物。
> 本会话成功 ≠ 甲成立。最多「可建议人审激活」；**不**自行激活 `PREREG-B`，**不**开 #440。
> 旧 #438/#460/#470/#477 门闩页与夹具绿 **不得**升格为已过门。

## 探针协议（跑前写死 · 禁止 HARKing）

### 过门判据（须同时）

1. T 自然放行 k ≥ 10
2. T−B1 固定 k 误放差方向为正（点估计 > 0）
3. T−B2 固定 k 误放差方向为正（点估计 > 0）

任一条不满足 → `gate_passed=false`；建议句必须写：**不得激活 PREREG-B；不得开 #440**。

### 机制约束（不得放松）

- **选取**：R（#437 / PR #458）
- **同 after**：T/B1 共用 T rewrite after，再分叉（#469 / PR #476）
- **生成对齐**：T/B1 提示要求 after 与 evidence 去空白逐字相同（#471 / PR #474）
- **T 闸**：绑定 ∧ 核验；不过 hard reject
- **B1 闸**：仅核验；不过 hard reject
- **禁止**：金标/评委/用户裁决进 score；改 verify_edit 或放宽 reject 凑 k；加 n 伪抬 k

### 样本针

- **n** = 30（`load_pe_v2_formal_n30()`，与正式同构造配额）
- **claim_id 顺序**：`a005,a006,a007,a008,a009,a010,a011,a012,b005,b006,b007,b008,b009,b010,b011,b012,c005,c006,c007,c008,c009,c010,c011,c012,d004,d005,d006,d007,d008,d009`
- 旁路生成：`docs/evidence/patch-events/gate-k-probe-generations.jsonl`（禁止写入 `docs/evidence/patch-events/formal-generations.jsonl`）

### 解码针

- model = `qwen-flash`（登记 `qwen-flash`）
- temperature = `0`
- Decoding.seed = `20261007`（run_arms 作废检查）
- API seed = `None` — live_chat / DecodingParams 未传 seed；Decoding.seed 仅供 run_arms 作废检查

## 基线与代码针

- **代码针**：76e7d06
- **基线**：cursor/470-gate-separation-remeasure-b867（R+#469）+ cherry-pick #471/#474 生成对齐
- 机制缝：#458（R）+ #476（同 after）+ #474（生成对齐）已合入本分支

## 发送状态

- **本会话未获明文「授权发模型」** → 停在可发送边界。
- 状态：**等待授权发模型**
- 入口已搭好：见文末「复算 / 发送入口」。

## 探针主表（旁路生成）

（未跑 / 无旁路生成。）

## 只读冻结对照（非探针 · 非过门证据）

> 回放 `docs/evidence/patch-events/formal-generations.jsonl`：旧生成**吃不到** #471 对齐提示；仅作机制后差方向对照。
> **不得**把本对照升格为抬 k 过门。

| 臂 | 自然放行 | 自然误放 | 固定 k 误放 |
|---|---:|---:|---:|
| T | 3 | 0 | 0 |
| B1 | 4 | 1 | 0.3333333333333333 |
| B2 | 30 | 15 | 0.6666666666666666 |
| C | 30 | 15 | 0.6666666666666666 |

- **k** = 3
- **T−B1** 固定 k 误放差 = 0.3333333333333333
- **T−B2** 固定 k 误放差 = 0.6666666666666666
- **gate_passed** = `False`

## 门闩三条件判定（探针主路径）

| # | 条件 | 观测 | 满足？ |
|---|---|---|---|
| 1 | T 自然放行 k ≥ 10 | k = None | 否 |
| 2 | T−B1 差方向为正 | 点估计 = 无定义 | 否 |
| 3 | T−B2 差方向为正 | 点估计 = 无定义 | 否 |

**gate_passed = `False`**

## 结论与建议

- **gate_passed=false**。
- **不得激活 PREREG-B；不得开 #440。**
- 冲甲本波仍停在丁；禁止改甲定义续命。
- 不得把夹具绿或旧 #460/#477 升格为已过门。

- 本会话：**等待授权发模型**（入口见下）。

## 复算 / 发送入口（零歧义）

```bash
# 默认：写本报告 + 只读对照 + 不发模型（停在可发送边界）
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_k_probe

# 只打印判定，不写盘
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_k_probe --no-write

# 若旁路生成已存在：只复算（零 LLM）
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_k_probe --recompute-only

# 仅在人/编排器本会话明文「授权发模型」之后：
PYTHONPATH=src python -m freshlatch.eval.patch_events_gate_k_probe --authorize-send
```

## 边界

- 可扔；非甲；不进主表；不得升格 RESULT-B。
- 不改甲/乙/丙定义；不复活路线 A；不改主 compare_primary 成立语义。
- 不金标打分；不放宽 hard reject；不加 n 凑 k。
