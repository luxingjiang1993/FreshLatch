# ADR-0036: patch_events 路线 C · 强制抄句（copy-constrained）冲甲旁路

- **状态**: Accepted
- **日期**: 2026-10-09
- **相关**: `docs/research/patch_events-路线C强制抄句冲甲设计评估.md`、[#482](https://github.com/luxingjiang1993/FreshLatch/issues/482)、[#483](https://github.com/luxingjiang1993/FreshLatch/issues/483)；上游路线 B：[#431](https://github.com/luxingjiang1993/FreshLatch/issues/431)/[#432](https://github.com/luxingjiang1993/FreshLatch/issues/432)/[#466](https://github.com/luxingjiang1993/FreshLatch/issues/466)、ADR-0034、ADR-0035、[#480](https://github.com/luxingjiang1993/FreshLatch/issues/480) RESULT-B 丙归档；平行轨 ALT：[#435](https://github.com/luxingjiang1993/FreshLatch/issues/435)/[#455](https://github.com/luxingjiang1993/FreshLatch/issues/455)（不抢主表）
- **说明**: 编号避撞 B 的 ADR-0034/0035 与 ALT 旁路卷号；本文件只钉 C 增量与防火墙，不回写 B 成立格。

## 背景

路线 B 在选取 R、T/B1 同 after、生成对齐提示齐备并过仓外门闩后，正式主跑一次仍为**结果丙**（#480：k=42；T−C/T−B1/T−B2 点估计>0，95% CI 下界均≤0）。结构上可识别，统计上效应偏小。同页二跑 B、降 CI、拿掉 B1、复活 A、并 ALT 主表追甲均已禁。旁路开路线 C：新预注册 + 强制抄句加大可辩护 T 相对差；叙事收窄为 attested/copy-constrained。

三条件齐备：

- **难反转**：后续 `/to-spec`、生成缝、门闩与一次正式主跑将引用本闸；事后改矮甲定义或同页翻 B 会使实验作废。
- **反直觉**：B 已过门仍再开旁路；冲甲却收窄主张为「只能抄证据句」；失败要删 C 分支而留 B 丙归档。
- **真实取舍**：强制点在生成器 vs 仅构造；ALT 并表 vs 仅附录；继承 B 门闩 vs 沿用探针绿。

## 决策

1. **路线 C**  
   新预注册 `docs/evidence/patch-events/PREREG-C.md`；结果 `RESULT-C.md`；生成 `formal-generations-c.jsonl`（或 `patch-events-c/`）。不删、不改 A/B/ALT 归档。C 失败：关 C 票、删 C 分支。

2. **继承 B 机制包（默认基线）**  
   选取 R；k 下限 10；成立定义不放宽；T/B1 同 after 再分叉；不放松 hard reject/绑定/逐字核验；同一预注册一次正式主跑；结果只抄同一次主比较。禁止金标/评委进 score；禁止复活 A。

3. **增量 = 强制抄句（二者 · 生成器主）**  
   T 的 `after_text` 由硬契约产出，去空白后与请求内 `evidence_text` 逐字相同（非 B 软提示）。B1 消费同一 after 再分叉。构造保证正确槽可抄；不可抄则槽作废。叙事 = attested / copy-constrained；不称自由 rewrite SOTA / 优于 RARR·KPR。

4. **ALT 仅附录**  
   B1′ / 同文四闸 / `compare_alt_*` 不进 C 主表；不改主 `compare_primary` 追甲。

5. **门闩与 n**  
   正式 n=100。门闩三条件继承 B，须对 C 机制新出可扔报告；禁止把 #479 探针绿升格为 C 已过门。未过不得激活。

6. **B 负结果附录**  
   对外固定引用 #480 丙与「效应偏小」教训；禁止同页翻 B、禁止把 B 数字抄进 RESULT-C 成立格。

7. **反 HARKing**  
   见 B 丙后改成立定义、同页二跑、并 ALT 凑差 = 禁止。正式主张只来自 `PREREG-C` 激活后的一次主跑。

8. **层身份**  
   门闩/探针 = 可扔冒烟层。甲/乙/丙细则不进 `CONTEXT.md`；词表只收路线 C / copy-constrained / PREREG-C 产品级词。

## 后果

- 可 `/to-spec`：协议骨架 + 强制抄句缝 + 门闩夹具派工。  
- 门闩未过：`PREREG-C` 保持未激活；禁止正式生成进主表。  
- 违例：改 B 归档；复活 A；ALT 并主表；放松 reject 凑 k；未过门激活；保证甲；称全面 SOTA。

## 替代方案（被否决）

- **同页翻 B / 降 CI / 拿掉 B1**：HARKing / 改矮甲。  
- **仅构造强制**：相对 B 增量弱。  
- **仅生成无构造保证**：假阴性压 k。  
- **ALT 进主表**：破防火墙；夹具升格。  
- **沿用 #479 绿当 C 过门**：门闩倒置。  
- **复活 A / 空分 top-k**：差锁 0。  
