# SENS-LIVE-2 跑前协议（#542）

日期：2026-10-12（UTC+8）
票：PE-Y-SENS-LIVE-2 · GitHub #542
父图：#517
Depends-on：#544 / #545 已合入 main 的正式冻结

本页锁的是本跑顺序与读法。正式 S 的文本、金标、重叠不在本页重写。
名单以 `docs/evidence/patch-events/SENS-S-FREEZE-formal-S.jsonl` 为准。
协议锁以 `docs/evidence/patch-events/SENS-S-FREEZE-PROTOCOL.md` 为准。
本页若与那两份冲突，以冻结 jsonl 与冻结协议为准，并停止开跑。

## 1. 正式冻结

冻结 sha256（26 条 `record_type=sample`，按 `canonical_index` 排序后的规范 JSON UTF-8）：

`e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`

必须入集：

- `DIAG-CHEF-03-bad`：证据「不少于 5 年」，主张「不少于 3 年」
- `DIAG-CHEF-04-bad`：证据含「大约」，主张删掉「大约」

禁止把下列哈希当作本冻结：

- 过早 PR #543：`baf33f5b9e0ea801c736d67385a94546fb6bd24af1ada0e4f27d1b9f5da1fa8c`
- 代码内 24 条 `SENSITIVITY_SET_S`：`958638ca0f3dc51323db710a69f4eacacc2fcff10186a99b07aecc47821d838b`

不合 #543，不在其分支上继续改。G20=B。

## 2. 打分顺序

1. 读冻结 jsonl，按协议 §7 计算 sha256。
2. 打印 `FROZEN_S_SHA256 <digest>`。此时还不得调用 `predict_xnli_probs`。
3. digest 必须等于上一节的正式冻结。否则拒绝开跑，不写过线。
4. 打印 `BEGIN_SCORING` 之后才允许加载 NLI 权重并打分。
5. 打分结束再读同一文件，再哈希。打印 `FROZEN_S_SHA256_AFTER <digest>`。
6. 跑后哈希或文件字节与跑前不一致：整跑作废，不写过线。

仪器是现有 `verify_edit`。premise = `evidence_text`，hypothesis = `after_text`。
`ok` 当且仅当 argmax 为 entailment 且 P(entailment) ≥ τ。
`ok=False` 时 `score` 为 −∞。不另写第二套 ok 公式。

## 3. 门槛（只回显，不改）

| 项 | 锁 |
|---|---|
| model_id | `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` |
| tau | `0.5`（`ENTAILMENT_TAU`） |
| S2 ρ | 坏 → ok=False ≥ 0.90 |
| S3 ρ | 正确 → ok=True ≥ 0.70 |
| S2 分母 | 全部 `gold=坏` 的 20 条，含两条 must-carry |

CHEF 对有效的两个条件：冻结 `token_overlap` ≥ 0.8，且本跑在冻结文本上测得好侧 `ok=True`。
缺一则整对无效。无效对的坏侧仍留在 S2 分母里。不改好侧文本。

`DIAG-CHEF-03-good` 的年限保持 5 年，与证据同文。本跑重测该侧 `ok`，不用 DIAG 页的 ok 代替。

## 4. 读法

主读法是 S1–S4。`heuristic` / `stratum` 只作描述列。
删除类 `nli_construct_ok` 是 meta-eval，不进主读法，不改 τ，不改 ρ，不改分母。

DIAG 分不是本页 S2。
#538 的 `GATE-Y-SENSITIVITY.md` 写 S2 实测 0.7000、未通过。本跑不改写那句。

## 5. 禁升格

- 不写 `activation_prerequisite_met=是`。本跑锁 `activation_prerequisite_met=否`。
- 过现行 ρ 只是 L1 证据，供人审。
- 不过则诚实失败，不放宽 τ，不降低 ρ，不凑绿。
- 不解锁 PE-Y-05，不开 GATE 真探针，不开 n=400。
- 无 secret_names。
