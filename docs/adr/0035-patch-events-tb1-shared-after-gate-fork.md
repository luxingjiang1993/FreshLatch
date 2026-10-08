# ADR-0035: patch_events 路线 B · T/B1 同 after 再分叉与抬 k 杠杆

- **状态**: Accepted
- **日期**: 2026-10-08
- **相关**: `docs/research/patch_events-路线B-T与B1可执行差与抬k设计评估.md`、[#465](https://github.com/luxingjiang1993/FreshLatch/issues/465)、[#466](https://github.com/luxingjiang1993/FreshLatch/issues/466)；上游 ADR-0034 · [#431](https://github.com/luxingjiang1993/FreshLatch/issues/431)/[#432](https://github.com/luxingjiang1993/FreshLatch/issues/432)；协议页 `docs/evidence/patch-events/PREREG-B.md`（激活前修订 · 正式主跑未激活）；门闩冒烟 [#438](https://github.com/luxingjiang1993/FreshLatch/issues/438)

## 背景

选取 R（ADR-0034）落地后，仓外门闩 #438 仍未过：T−B1 固定 k 误放差 = 0，T 的 k = 3 &lt; 10。回放显示失败主因不是「又同集」，而是 T/B1 在独立生成 + 同核验 hard reject 下高度同构，唯一绑定缝被生成噪声盖住；同时 T 上正确样假阴性全来自核验不过。需要在**不改选取 R、不放宽成立定义、不激活正式主跑**的前提下，钉死可执行对照差与抬 k 杠杆，并重申复测协议。

三条件齐备：

- **难反转**：后续 `run_arms` / 生成与门闩复测夹具将引用本闸；事后把 B1 改成核验失败仍放行、或放松 T hard reject 凑 k，会摧毁对照与实验意义。
- **反直觉**：冲甲却先做「同 after」；B1 名帖「先改后验」却仍硬拒核验失败；见门闩失败仍不改成立定义。
- **真实取舍**：D1 同 after 再分叉 vs D2/D3 削弱 B1 凑差；L1 降假阴性 vs L2 松闸；激活前修订 vs 另页 B2。

## 决策

1. **T/B1 最小可执行差 = 同 after 再分叉（D1）**  
   同一 `claim_id` 上 T 与 B1 消费同一份 rewrite `after_text`（及同一候选 `evidence_id`），再分叉决策：T = 已入库 T1 绑定 ∧ 核验 ok 才 release；B1 = 不跑绑定闸，仅核验 ok 才 release。两边核验不过均为 hard reject。禁止本期 D2（B1 核验失败仍放行/soft）、D3（B1 弱核验）。

2. **抬 k 主杠杆 = 降正确样核验假阴性（L1）**  
   不放松 T 的逐字核验或 hard reject；不放松绑定凑 k；不加 n / 夹具伪抬 k。验收叙事是「正确样过 T 变多」。

3. **门闩复测协议**  
   机制改完：夹具 + 只读旧生成冒烟；真分离/k 量级再用人授小探针。规则与 `PREREG-B` 的 R 一致。报告可扔、不进主表。三条件全过才允许激活批注；未过不得正式生成进主表。

4. **预注册形态 = 激活前修订**  
   在 `PREREG-B.md` 写入 T/B1 可执行定义修订与修订记录；**不**另开 PREREG-B2；**不**改选取 R 或成立定义；文首保持未激活。

5. **反 HARKing**  
   #438 数字只证明「机制同构 / 假阴性压 k」；正式主张只来自激活后的新跑。D1 后仍 T−B1≤0 → 改冲乙或另决议，禁止改成立定义追甲。

6. **词表**  
   `CONTEXT.md` 收：同 after 再分叉、PREREG-B 激活前修订（产品级）。甲/乙/丙细则与门闩数字不进词表。

## 后果

- 可 `/to-spec` 增量：第一张工程票 = T/B1 行为差缝 + 门闩复测夹具（Acceptance 含同 after 上自然放行集可不同，及复测报告格式）。  
- 不得激活 `PREREG-B`、不得开 #440 进主表，直至复测三条件全过。  
- 违例：D2/D3；放松 T hard reject 凑 k；金标进 score；未过门激活；另开 B2 却悄悄改成立定义；复活 A。

## 替代方案（被否决）

- **维持独立生成（D0）**：门闩已证差=0。  
- **B1 核验失败仍放行（D2）/ 弱核验（D3）**：削弱对照凑差。  
- **放宽 T 核验或绑定抬 k**：把 T 做成 B1 / 伤 attested。  
- **未过门正式 n=100**：门闩倒置。  
- **另页 PREREG-B2（本期）**：成立定义与 R 未变，同页修订足够。  
- **见 0 后改成立定义或选取 R**：HARKing。  
