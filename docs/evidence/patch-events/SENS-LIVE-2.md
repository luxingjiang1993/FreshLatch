# SENS-LIVE-2 · 正式敏感性 LIVE-2 报告

日期：2026-10-12（UTC+8）
票：PE-Y-SENS-LIVE-2 · GitHub #542
仪器：mDeBERTa-v3 XNLI · τ=0.5 · ok 当且仅当 argmax 为 entailment 且 P(entailment)≥τ
model_id：`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`
tau：`0.5`
冻结名单 sha256：`baf33f5b9e0ea801c736d67385a94546fb6bd24af1ada0e4f27d1b9f5da1fa8c`
Trust：L1（正式 LIVE-2 证据）。过现行 ρ 也只供后续人审，本页不升格激活。

## 1. 协议锁（跑前）

书面锁见 `docs/evidence/patch-events/SENS-LIVE-2-PROTOCOL.md`。
冻结清单见 `docs/evidence/patch-events/SENS-LIVE-2-set-S.jsonl`。
真跑日志 `SENS-LIVE-2-run.log` 在打分之前打印同一 sha256。
跑后复核哈希未变。名单在开跑之后没有增删。

算子仍是四层 × mod4，外加原有四条废止/版本陷阱。
坏槽保持 20 条，与 #538 同口径，不用额外易拒句稀释 S2。
两条 must-carry 在冻结名单内：`DIAG-CHEF-03-bad`（5 年改为 3 年）、`DIAG-CHEF-04-bad`（删「大约」）。
HANS 义务冲突入集：`DIAG-HANS-002`、`DIAG-HANS-003`、`DIAG-HANS-004`、`DIAG-HANS-006`。
`DIAG-HANS-008` 的「不应当」极端否定不入集。

CHEF 对门闩：两侧 after 的 token_overlap ≥ 0.8，且好侧 ok=True，否则对无效。
无效对只影响配对读法。S2 分母仍是全部 gold=坏。

## 2. 仪器冻结

- 型号：`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`（须 = ADR-0040 `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`）
- τ：`0.5`（`ENTAILMENT_TAU`，未放宽）
- 坏→ok=False 下限：`0.9`（未降低）
- 正确→ok=True 下限：`0.7`（未降低）
- `patch_events_verify.py` sha256：`58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918`
- 运行环境：transformers 4.57.6；torch 2.8.0+cu128；cuda_available=False；verify_edit 未调用 cuda()，与 ADR-0040 同一函数；权重来自本地 Hugging Face 缓存；无 secret_names
- 无 secret_names，无新开云密钥。

## 3. S1–S4（现行 ρ）

本表是这次冻结 S 的真权重结果。DIAG 分不进入分子或分母。

| # | 条件 | 结果 |
|---|---|---|
| S1 | 无 score=None；ok=False → score=−∞ （none=0；reject=18；−∞=18） | 通过 |
| S2 | 坏→ok=False ≥ 0.9 （实测 0.9000；坏 20） | 通过 |
| S3 | 正确→ok=True ≥ 0.7 （实测 1.0000；正确 6） | 通过 |
| S4 | 型号/τ = ADR-0040（`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` · `0.5`） | 通过 |

**sensitivity_passed（S1∧S2∧S3∧S4）**：是

**gate_passed**：否

**activation_prerequisite_met**：否

本页不解锁 PE-Y-05，不开 GATE-Y 真探针，不开 formal-y n=400，不复活 #507。

#538 失败结论句保持原样，不改写成过线：S2 坏→ok=False ≥ 0.9（实测 0.7000）未通过；该次 sensitivity_passed 为否。

**DIAG ≠ S2。** SENS-DIAG-1A 的变红条数与 P_entail 不能代替本页 S2。

### 3.1 同文仪器复核（不入 S2）

下表只核对与 SENS-DIAG-1A 同文的本跑 P_entail。S2 仍只用本跑 ok，分母是本冻结集的全部坏槽。

| id | 本跑 P_entail | DIAG 页 P_entail | 绝对差 |
|---|---:|---:|---:|
| DIAG-HANS-002 | 0.0004841118 | 0.0004841118 | 0.0000000000 |
| DIAG-HANS-003 | 0.0011600856 | 0.0011600856 | 0.0000000000 |
| DIAG-HANS-004 | 0.1859738678 | 0.1859738678 | 0.0000000000 |
| DIAG-HANS-006 | 0.0104973661 | 0.0104973661 | 0.0000000000 |
| DIAG-CHEF-03-bad | 0.8668648601 | 0.8668648601 | 0.0000000000 |
| DIAG-CHEF-03-good | 0.9216354489 | 0.9216354489 | 0.0000000000 |
| DIAG-CHEF-04-bad | 0.9547298551 | 0.9547298551 | 0.0000000000 |
| DIAG-CHEF-04-good | 0.9086972475 | 0.9086972475 | 0.0000000000 |
| S-正确-日期01 | 0.5039777756 | 0.5039777756 | 0.0000000000 |


## 4. 逐条结果

| sample_id | stratum | heuristic | subcase | gold | pair_id | token_overlap | nli_construct_ok | ok | P_entail | score | pair_valid |
|---|---|---|---|---|---|---:|---|---|---:|---|---|
| S-数值-op0 | 数值 | lexical_overlap | 数值op0 | 坏 |  | 0.857143 | yes | False | 0.0018955959 | −∞ | n/a |
| S-数值-op1 | 数值 | lexical_overlap | 数值op1 | 坏 |  | 0.800000 | yes | False | 0.0376208425 | −∞ | n/a |
| S-数值-op2 | 数值 | argument_swap | 数值op2 | 坏 |  | 0.833333 | yes | False | 0.0046314951 | −∞ | n/a |
| S-数值-op3 | 数值 | lexical_overlap | 数值op3 | 坏 |  | 0.800000 | yes | False | 0.4070456922 | −∞ | n/a |
| S-日期-op0 | 日期 | lexical_overlap | 日期op0 | 坏 |  | 0.900000 | yes | False | 0.0043387418 | −∞ | n/a |
| S-日期-op1 | 日期 | lexical_overlap | 日期op1 | 坏 |  | 0.888889 | yes | False | 0.0264161620 | −∞ | n/a |
| DIAG-HANS-002 | 日期 | argument_swap | 日期op2 | 坏 |  | 1.000000 | yes | False | 0.0004841118 | −∞ | n/a |
| DIAG-HANS-003 | 日期 | argument_swap | 日期op3 | 坏 |  | 1.000000 | yes | False | 0.0011600856 | −∞ | n/a |
| S-条款-op0 | 条款替换 | lexical_overlap | 条款op0 | 坏 |  | 0.857143 | yes | False | 0.0018698263 | −∞ | n/a |
| S-条款-op1 | 条款替换 | argument_swap | 条款op1 | 坏 |  | 0.777778 | yes | False | 0.3162308037 | −∞ | n/a |
| DIAG-HANS-004 | 条款替换 | lexical_overlap | 条款op2 | 坏 |  | 0.833333 | yes | False | 0.1859738678 | −∞ | n/a |
| S-条款-op3 | 条款替换 | none | 条款op3 | 坏 |  | 0.333333 | yes | False | 0.0080267889 | −∞ | n/a |
| DIAG-HANS-006 | 删除 | lexical_overlap | 删除op0 | 坏 |  | 1.000000 | yes | False | 0.0104973661 | −∞ | n/a |
| DIAG-CHEF-03-bad | 删除 | lexical_overlap | 删除op1 | 坏 | DIAG-CHEF-03 | 0.875000 | yes | True | 0.8668648601 | 0.866865 | 有效 |
| S-删除-op2 | 删除 | none | 删除op2 | 坏 |  |  | yes | False | 0.0078747226 | −∞ | n/a |
| DIAG-CHEF-04-bad | 删除 | subsequence | 删除op3 | 坏 | DIAG-CHEF-04 | 1.000000 | yes | True | 0.9547298551 | 0.954730 | 有效 |
| S-废止-trap01 | 条款替换 | lexical_overlap | 废止trap | 坏 |  | 0.750000 | yes | False | 0.0046763993 | −∞ | n/a |
| S-废止-trap02 | 条款替换 | lexical_overlap | 废止trap | 坏 |  | 0.666667 | yes | False | 0.0012190399 | −∞ | n/a |
| S-版本-trap01 | 条款替换 | argument_swap | 版本trap | 坏 |  | 0.625000 | yes | False | 0.0051305089 | −∞ | n/a |
| S-版本-trap02 | 条款替换 | argument_swap | 版本trap | 坏 |  | 0.545455 | yes | False | 0.1520473212 | −∞ | n/a |
| S-正确-数值01 | 数值 | lexical_overlap | 数值正确 | 正确 |  | 1.000000 | n/a | True | 0.9943641424 | 0.994364 | n/a |
| S-正确-日期01 | 日期 | lexical_overlap | 日期正确 | 正确 |  | 0.900000 | n/a | True | 0.5039777756 | 0.503978 | n/a |
| S-正确-条款01 | 条款替换 | lexical_overlap | 条款正确 | 正确 |  | 0.888889 | n/a | True | 0.7590352893 | 0.759035 | n/a |
| S-正确-删除01 | 删除 | subsequence | 删除正确 | 正确 |  | 1.000000 | n/a | True | 0.8788937926 | 0.878894 | n/a |
| DIAG-CHEF-03-good | 删除 | lexical_overlap | 删除op1 | 正确 | DIAG-CHEF-03 | 0.875000 | n/a | True | 0.9216354489 | 0.921635 | 有效 |
| DIAG-CHEF-04-good | 删除 | subsequence | 删除op3 | 正确 | DIAG-CHEF-04 | 1.000000 | n/a | True | 0.9086972475 | 0.908697 | 有效 |

## 5. 删除类 meta-eval

主金标是二元坏/好。WiCE 只作笔记。下面的 `nli_construct_ok` 在开跑前按 DIAG 交接写死，不按本跑分数改判。

| id | gold | nli_construct_ok | wice_note | 跑前判断 |
|---|---|---|---|---|
| DIAG-HANS-006 | 坏 | yes | not_supported | 已废止限定被说成仍然有效，主张不被证据蕴含 |
| DIAG-CHEF-03-bad | 坏 | yes | not_supported | 5 年改为 3 年。数字不是证据里的年限。金标坏在 NLI 构念下成立 |
| DIAG-HANS 未入集的 007 |  |  |  | DIAG 里插入相反例外已变红。本正式 S 不另加该易拒句，以免稀释 must-carry |
| S-删除-op2 | 坏 | yes | not_supported | 空证据。硬拒对照，不是高重叠坏槽 |
| DIAG-CHEF-04-bad | 坏 | yes | not_supported | 删「大约」是义务硬化。产品协议定为坏槽。DIAG 已标 yes，本跑不改成 partial 或 no |
| DIAG-CHEF-04 对照 |  |  |  | #538 原文 S-删除-op3 曾标 partial（不是干净矛盾）。正式条用 CHEF-04 文本，不把那条 partial 事后改写 |

删「大约」：证据只有弱化义务，主张把「大约」拿掉后语气更硬。
这不是干净矛盾句。金标仍按跑前锁为坏，因为产品协议把义务硬化算坏改。
不回头改金标，也不改 τ/ρ。

### 5.1 本跑读数

gold=坏 且 ok=True 共 2 条。它们留在 S2 分母里。
- `DIAG-CHEF-03-bad`：ok=True，P_entail=0.8668648601。heuristic=lexical_overlap，stratum=删除。
- `DIAG-CHEF-04-bad`：ok=True，P_entail=0.9547298551。heuristic=subsequence，stratum=删除。

删除亚型（分数来自本跑，不是 DIAG 表）：
- `DIAG-CHEF-03-bad`：ok=True，P_entail=0.8668648601，nli_construct_ok=yes（跑前锁，未改）。
- `DIAG-CHEF-04-bad`：ok=True，P_entail=0.9547298551，nli_construct_ok=yes（跑前锁，未改）。
- `DIAG-HANS-006`：ok=False，P_entail=0.0104973661，nli_construct_ok=yes（跑前锁，未改）。
- `S-删除-op2`：ok=False，P_entail=0.0078747226，nli_construct_ok=yes（跑前锁，未改）。
删「大约」本跑仍为 ok=True。仪器对义务硬化放行。金标保持坏。这条不是过线被藏起来的失败，它已经算进 S2 的未拒绝数。
5 年改为 3 年本跑仍为 ok=True。数字替换亚型仍被放行，同样留在分母里。

## 6. 边界

- 未改 `ENTAILMENT_TAU`，未降低 S2/S3 ρ，未换型号，未改 ADR-0040 的 ok 公式。
- 未写 activation_prerequisite_met=是。
- 未开 PE-Y-05，未开 GATE 真探针，未开 n=400，未复活 #507。
- 未把 DIAG 分写成正式 S2。
- 未声称乙。

S1–S4 过现行 ρ。这里只登记敏感性真过证据，供后续人审。人未审之前，激活前置仍为否。
