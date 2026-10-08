# ADR-0036: patch_events 路线 B · T/B1 同 after 再分叉与抬 k（L1）

- **状态**: Accepted
- **日期**: 2026-10-08
- **相关**: [#466](https://github.com/luxingjiang1993/FreshLatch/issues/466)、[#467](https://github.com/luxingjiang1993/FreshLatch/issues/467)、评估 `docs/research/patch_events-路线B-T与B1可执行差与抬k设计评估.md`；协议 `docs/evidence/patch-events/PREREG-B.md`（激活前修订）；父 ADR-0034（选取 R）
- **编号**: **0036**（平行轨对照探针占用 ADR-0035；本文件禁止再写第二个 0035）

## 背景

仓外门闩（#438）未过：T−B1 固定 k 误放差为 0，且 k=3&lt;10。回放显示 T/B1 路径高度同构（各自 rewrite + 同一 `verify_edit` + 核验不过 hard reject），生成噪声掩盖 `_bound_t1` 决策差；抬 k 的主矛盾在正确样核验假阴性，不在绑定过严。

三条件齐备：

- **难反转**：后续门闩复测、激活前修订与正式主跑将引用「同 after + 闸分叉」为 T/B1 可执行定义；事后改回各自生成会使绑定缝对照失效。
- **反直觉**：对照臂 B1 与 T **共享** after，却仍主张可分离——分离来自闸，不来自生成噪声。
- **真实取舍**：D1 vs 削弱 B1（D2/D3）；L1 提示纪律 vs 放宽核验；激活前修订 vs 另开 B2 / 改成立定义。

## 决策

1. **D1 同 after 再分叉**  
   `run_arms` 对 T/B1 只发一次 rewrite（请求形态 `arm=T`），两边记录共用同一 `after_text`，再分叉闸判：T = 绑定 ∧ 核验（attested fail-closed）；B1 = 仅核验；核验不过则拒绝。C/B2 仍各自生成。

2. **不削弱 B1 / 不放松 T**  
   否 D2（B1 soft）、D3（双核验标准）、L2（放宽逐字）、L3（放松绑定）。

3. **L1 降正确假阴性**  
   提示词补定：对齐 evidence 时 `after_text` 须与 `evidence_text` 去空白后逐字相同。目标是正确样更常过闸，不是放宽闸。

4. **门闩复测序**  
   夹具 → 只读旧生成冒烟 →（可选）人授小探针；均不进主表；默认零 LLM。报告缝可扔。

5. **预注册形态**  
   `PREREG-B` **激活前修订**（实验组可执行定义 + 修订记录）；文首保持未激活；不改选取 R、不改成立定义；不另开 PREREG-B2。

6. **词表**  
   `CONTEXT.md` 增补「同 after 再分叉」；甲/乙/丙成立细则不进词表。

## 后果

- #467 实装 `patch_events_arms` / 生成提示 / `patch_events_gate_retest` + 夹具单测。  
- 未过门：不得激活、不得 #440 正式主表生成、不得填 RESULT 称甲。  
- 违例：削弱 B1 凑差；金标进 score；改成立定义；平行轨旁路污染冲甲主链；再写 ADR-0035 撞号。

## 替代方案（被否决）

- **D2/D3**：削弱 B1 或双标准凑差。  
- **L2/L3/L4/L5**：放宽闸 / 加 n / 夹具伪抬 k。  
- **S4 直接正式 n=100**：未过门非法。  
- **另开 PREREG-B2 / 改 R 或成立定义**：分裂或 HARKing。  
- **占用 ADR-0035**：与平行轨撞号。
