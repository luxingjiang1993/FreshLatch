# ADR-0037: patch_events 路线 Y · 只冲乙（仅锁 T−C）

- **状态**: Accepted
- **日期**: 2026-10-09
- **相关**: `docs/research/patch_events-路线Y只冲乙仅锁T-C设计评估.md`；上游 ADR-0034 / ADR-0035（Draft · R / 同 after）；对照 ADR-0036（C 抄句 · **非** Y 主路径）；协议页 `docs/evidence/patch-events/PREREG-Y.md`（未激活）；冻结归档 `PREREG-B`/`RESULT-B`（#480 丙）、`PREREG-C`/`RESULT-C`（丙 · 非乙主路径）
- **说明**: 编号顺延 Draft 上 0034–0036 之后。本文件只钉 Y 增量与甲防火墙；不回写 B/C 成立格；不重复定义 R / 同 after。

## 背景

路线 B 在选取 R、同 after、软对齐并过仓外门闩后正式主跑一次仍为**结果丙**（k=42；T−C 点≈0.119、ci95_low≈−0.056）。路线 C 强制抄句正式主跑亦丙（k=93；T−C 下界=0），且已禁以抄句为主路径翻盘。人拍板：新开预注册**只冲乙**，成立仅锁 T−C，放弃甲，抬 n 并预登记止损。

三条件齐备：

- **难反转**：后续 `/to-spec`、formal-y、门闩与一次正式主跑将引用本闸；事后改回「可称甲」或同页翻 B/C 会使实验作废。
- **反直觉**：冲乙却仍跑满三行主比较；点估计须 >0.05 才算乙成立（严于经典点>0）；即便 B1/B2 均过也不得称甲。
- **真实取舍**：新页 vs 回写 B；B 软对齐 vs C 抄句；n=400 功效 vs 成本；放弃甲 vs 保留甲后门。

## 决策

1. **路线 Y**  
   新预注册 `docs/evidence/patch-events/PREREG-Y.md`；结果 `RESULT-Y.md`；生成 `formal-generations-y.jsonl`；门闩 `GATE-Y-PROBE.md`。不删、不改 A/B/C/ALT 冻结归档。

2. **机制继承 B（默认基线）**  
   选取 R；k 下限 10；T/B1 同 after；**软对齐**（非 C 强制抄句）；bootstrap 10000、种子 `20261007`；同一预注册一次正式主跑；结果只抄同一次 `compare_primary`。禁止金标/评委进 score；禁止复活 A；禁止新造比较器。

3. **成立尺（本页增量）**  
   三行仍计算并上表。**参与成立的唯有 T−C**：点估计 **>0.05** 且 95% bootstrap 下界 **>0**。B1/B2 报告-only。本页分层只可能乙或丙，**不得称甲**。

4. **功率与止损**  
   正式 n=400。止损：正式后若 T−C 点≤0.05 或下界≤0（含无定义）→ 丙收口；禁止加 n、改选取、改成立尺、同页二跑。

5. **门闩**  
   过门须同时：T 的 k≥10；T−C 固定 k 误放差点估计>0。B1/B2 差必报、不作过门。须对 Y 机制出真数据可扔报告；禁止升格 `#479` GATE-K-PROBE 或 GATE-C-FIXTURE。夹具/ALT 不进主表。

6. **解码锁定**  
   生成：`qwen-flash`；temperature=0；Decoding.seed=`20261007`；API seed=`None`（与 RESULT-B 跑针一致）。

7. **反 HARKing 与词表**  
   见 B/C 丙后回写、以 C 为主路径、并 ALT 凑差、口头 soft-甲 = 禁止。`CONTEXT.md` 只收产品级「路线 Y / PREREG-Y」；乙成立细则与止损频率不进词表。

## 后果

- 可 `/to-spec`：formal-y 旁路、GATE-Y 克隆、n=400 名单、RESULT-Y 抄表（Acceptance 含「仅 T−C∧点>0.05∧下界>0」）。  
- 门闩未过：`PREREG-Y` 保持未激活；禁止正式生成进主表。  
- 违例：改 B/C 归档；复活 A；C 抄句当 Y 主路径；放松 reject 凑 k；未过门激活；称甲；保证乙。

## 替代方案（被否决）

- **同页翻 B / 只改成立尺重跑**：HARKing。  
- **C 强制抄句作 Y 主路径**：人禁；RESULT-C 反模式。  
- **事后 250→400 加 n**：钓鱼。  
- **甲三条件门闩 / soft-甲后门**：与放弃甲冲突。  
- **新造 compare_***：双真相源；违 #416 纪律。  
- **升格旧门闩绿**：门闩倒置。
