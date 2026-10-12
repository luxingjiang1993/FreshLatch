# SENS-LIVE-2-ACTIVATION · 人审激活记录

日期：2026-10-12 14:46:42 +0800（Asia/Shanghai · UTC+8）
票：PE-Y-SENS-LIVE-2-ACTIVATION · GitHub #548
授权人：Oriental Ronin
grill：已锁 2026-10-12「按推荐」（G1–G22 取推荐默认 · Asia/Shanghai）
层身份：人审落盘。不改 LIVE-2 跑时正文。

**activation_prerequisite_met=是**

**下一步允许：SMOKE-LIVE = 是**（另票 PE-Y-SMOKE-LIVE；本记录不开 SMOKE，不跳 SMOKE）

本记录不等于乙成立，不等于自动 GATE，不等于 RESULT-Y 有数。`gate_passed` 仍为否。

## 1. 证据锚

只认下列 live 报告。不认 stub，不认 #538 失败页，不认 DIAG-1A 分，不认未合 #543。

| 项 | 值 |
|---|---|
| LIVE-2 路径 | `docs/evidence/patch-events/SENS-LIVE-2.md` |
| commit | `c4b921aa7559b672f657c3ccdc44c0b7913c9224` |
| blob sha | `9671b009ce1f3591fe4fc26da003e2fa8774301c` |
| 冻结 S sha256 | `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19` |
| 正式 S | `docs/evidence/patch-events/SENS-S-FREEZE-formal-S.jsonl`（26 条 sample） |
| sensitivity_passed | 是 |
| S2 | 0.9000（18/20；S1–S4 过现行 ρ） |
| gate_passed | 否 |
| LIVE-2 跑时句 | `activation_prerequisite_met：否`（历史句保留，本文件不改写） |

跑前与跑后回显的冻结 sha256 同为 `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`。仪器为 mDeBERTa-v3 XNLI · τ=0.5 · 现行 `ok`（ADR-0040），与报告一致。τ 未放宽。ρ 未下调（S2 门槛仍 0.90）。`run_kind=live`。

## 2. 勾选单

来自阶段3 SPEC §4。本记录勾选完成。

- [x] sensitivity_passed=是（live 报告：docs/evidence/patch-events/SENS-LIVE-2.md · commit c4b921aa7559b672f657c3ccdc44c0b7913c9224 · blob sha 9671b009ce1f3591fe4fc26da003e2fa8774301c）
- [x] τ 未为凑绿而放宽（仍 0.5）；ρ 未事后下调（S2 门槛仍 0.90）
- [x] S 版本针一致：冻结 sha256 e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19 与报告一致；仪器 ADR-0040 针与报告一致
- [x] stub 报告未用于本勾选（run_kind=live）
- [x] Trust L1 抽检：11/26 保持、0 争议（够锁）
- [x] CHEF-03/04 对有效（好侧 ok=True）；未另立坏侧须 False
- [x] 授权人：Oriental Ronin / 时间（Asia/Shanghai · UTC+8）：2026-10-12 14:46:42 +0800
- [x] activation_prerequisite_met = 是（圈选：是）
- [x] 下一步允许：SMOKE-LIVE = 是（激活=是时默认「是」；须另票；禁跳 SMOKE）

## 3. Trust L1

抽检 11/26 保持、0 争议，够锁本阶段人审。不强制补至半仓。

若事后发现争议条：停激活、重冻 S、重跑 LIVE。禁止边激活边改金标。

## 4. CHEF-03/04

按 LIVE-2 §4，两对均有效。好侧 `ok=True`。本激活不另立「坏侧须 ok=False」。

| pair_id | 冻结 token_overlap | 好侧 ok | 坏侧 ok | 对 |
|---|---:|---|---|---|
| DIAG-CHEF-03 | 0.875000 | True | True | 有效 |
| DIAG-CHEF-04 | 1.000000 | True | True | 有效 |

坏侧 `ok=True` 已计入 S2 分母（18/20 = 0.9000）。这是报告里的读数，不是新门槛。

## 5. 边界

- 下一步允许另开 PE-Y-SMOKE-LIVE。本票未开 SMOKE，未开 GATE-Y，未开 PE-Y-05，未开 n=400。
- 未改 τ，未改 ρ，未改 `ENTAILMENT_TAU`，未改 ADR-0040，未改冻结 S 字节。
- 未复活 #507。未合并 #543。过早哈希不作本冻结。
- 未改写 #538 失败结论（S2 实测 0.7000、未通过仍以该页为准）。
- 未估 δ，未跑 discordant，未锁正式冲乙预注册页。
- 激活不等于乙成立，不等于自动 GATE。
