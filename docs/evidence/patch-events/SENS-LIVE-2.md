# SENS-LIVE-2 · 正式敏感性 LIVE-2

日期：2026-10-12（UTC+8）
票：PE-Y-SENS-LIVE-2 · GitHub #542
层身份：真模型推理层（非 stub）
仪器：mDeBERTa-v3 XNLI · τ=0.5 · ok 当且仅当 argmax 为 entailment 且 P(entailment)≥τ
model_id：`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`
tau：`0.5`
冻结名单 sha256：`e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`
正式 S：`docs/evidence/patch-events/SENS-S-FREEZE-formal-S.jsonl`（26 条 sample）
跑前协议：`docs/evidence/patch-events/SENS-S-FREEZE-PROTOCOL.md`
本跑协议：`docs/evidence/patch-events/SENS-LIVE-2-PROTOCOL.md`
Trust：L1（正式 LIVE-2 证据）。过现行 ρ 也只供人审。本页不升格激活。

## 1. 跑前锁

- 打分前打印的 sha256 = `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`，与 #544/#545 正式冻结相同。
- 打分后再哈希，与跑前相同。冻结文件字节未改。
- 禁止把过早哈希 `baf33f5b9e0ea801c736d67385a94546fb6bd24af1ada0e4f27d1b9f5da1fa8c` 当作本冻结。未合 #543。
- 代码内 24 条 `SENSITIVITY_SET_S` 的旧哈希 `958638ca0f3dc51323db710a69f4eacacc2fcff10186a99b07aecc47821d838b` 不是本页正式 S。该元组未改。
- `patch_events_verify.py` sha256：`58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918`。
- 运行环境：transformers 4.57.6；torch 2.8.0+cu128；cuda_available=False；verify_edit 与 predict_xnli_probs 同一 ADR-0040 函数；权重来自本地 Hugging Face 缓存；无 secret_names
- 无 secret_names。未改 ADR-0040，未改 `ENTAILMENT_TAU`，未改 S2/S3 ρ。

## 2. S1–S4（主读法）

S2 分母是全部 `gold=坏` 的 20 条，含 must-carry `DIAG-CHEF-03-bad` 与 `DIAG-CHEF-04-bad`。
CHEF 对无效时，坏侧仍留在分母里。

| # | 条件 | 计数 | 结果 |
|---|---|---|---|
| S1 | 无 `score=None`；`ok=False` → `score=−∞` | none=0；reject=18；−∞=18 | 通过 |
| S2 | 坏→`ok=False` ≥ 0.9 | 18/20 = 0.9000 | 通过 |
| S3 | 正确→`ok=True` ≥ 0.7 | 6/6 = 1.0000 | 通过 |
| S4 | 型号/τ = ADR-0040 | `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` · `0.5` | 通过 |

**sensitivity_passed（S1∧S2∧S3∧S4）**：是

**gate_passed**：否

**activation_prerequisite_met**：否

S1–S4 在现行 ρ 下同时成立。这只是 L1 证据，供人审。不自动解锁激活，不开 PE-Y-05，不开 GATE 真探针，不开 n=400。

## 3. 分层与 heuristic（描述，不是第二条通过线）

| stratum | gold=坏 | 其中 ok=False | heuristic 分布（坏槽） |
|---|---:|---:|---|
| 数值 | 4 | 4 | lexical_overlap, argument_swap |
| 日期 | 4 | 4 | lexical_overlap, argument_swap |
| 条款替换 | 8 | 8 | lexical_overlap, argument_swap, none |
| 删除 | 4 | 2 | lexical_overlap, none, subsequence |

## 4. CHEF 对

好侧 `ok` 在本冻结文本上重测。冻结 `token_overlap` 不重算。
好侧不为 `ok=True` 则整对无效。坏侧不移出 S2 分母。

| pair_id | 冻结 token_overlap | 好侧 id | 好侧 ok | 坏侧 id | 坏侧 ok | 对 |
|---|---:|---|---|---|---|---|
| DIAG-CHEF-03 | 0.875000 | DIAG-CHEF-03-good | True | DIAG-CHEF-03-bad | True | 有效 |
| DIAG-CHEF-04 | 1.000000 | DIAG-CHEF-04-good | True | DIAG-CHEF-04-bad | True | 有效 |

`DIAG-CHEF-03-good` 的 after 与 evidence 仍是「留存不少于 5 年」，年限未改成 3 年。

## 5. 删除类 nli_construct_ok（meta-eval，不进主读法）

下表只回显冻结时写下的 `nli_construct_ok` / `wice_note`。
它不改 `gold`，不改 S2 分母，不改 τ，不改 ρ。

| sample_id | gold | ok | nli_construct_ok | wice_note | 进入主读法 |
|---|---|---|---|---|---|
| DIAG-HANS-006 | 坏 | False | yes | not_supported | 否 |
| DIAG-CHEF-03-bad | 坏 | True | yes | not_supported | 否 |
| S-删除-op2 | 坏 | False | yes | not_supported | 否 |
| DIAG-CHEF-04-bad | 坏 | True | yes | not_supported | 否 |
| S-正确-删除01 | 正确 | True | n/a | supported | 否 |
| DIAG-CHEF-03-good | 正确 | True | n/a | supported | 否 |
| DIAG-CHEF-04-good | 正确 | True | n/a | supported | 否 |

## 6. DIAG ≠ S2

SENS-DIAG-1A 的 P_entail 不是本页 S2。下表只复核同文刺激的仪器读数。
S2 只用本跑 `ok`，分母是本冻结集的 20 条坏槽。

| id | 本跑 P_entail | 本跑 ok | DIAG 页 P_entail | 绝对差 |
|---|---:|---|---:|---:|
| DIAG-HANS-002 | 0.0004841118 | False | 0.0004841118 | 0.0000000000 |
| DIAG-HANS-003 | 0.0011600856 | False | 0.0011600856 | 0.0000000000 |
| DIAG-HANS-004 | 0.1859738678 | False | 0.1859738678 | 0.0000000000 |
| DIAG-HANS-006 | 0.0104973661 | False | 0.0104973661 | 0.0000000000 |
| DIAG-CHEF-03-bad | 0.8668648601 | True | 0.8668648601 | 0.0000000000 |
| DIAG-CHEF-03-good | 0.9216354489 | True | 0.9216354489 | 0.0000000000 |
| DIAG-CHEF-04-bad | 0.9547298551 | True | 0.9547298551 | 0.0000000000 |
| DIAG-CHEF-04-good | 0.9086972475 | True | 0.9086972475 | 0.0000000000 |

#538 的 `GATE-Y-SENSITIVITY.md` 仍写 S2 实测 0.7000、未通过。
本页不改写那句，也不把那次失败改成过线。

## 7. 逐条

| sample_id | stratum | heuristic | op | gold | ok | P_entail | score | pair_valid | must_carry |
|---|---|---|---:|---|---|---:|---|---|---|
| S-数值-op0 | 数值 | lexical_overlap | 0 | 坏 | False | 0.0018955959 | −∞ | n/a | False |
| S-数值-op1 | 数值 | lexical_overlap | 1 | 坏 | False | 0.0376208425 | −∞ | n/a | False |
| S-数值-op2 | 数值 | argument_swap | 2 | 坏 | False | 0.0046314951 | −∞ | n/a | False |
| S-数值-op3 | 数值 | lexical_overlap | 3 | 坏 | False | 0.4070456922 | −∞ | n/a | False |
| S-日期-op0 | 日期 | lexical_overlap | 0 | 坏 | False | 0.0043387418 | −∞ | n/a | False |
| S-日期-op1 | 日期 | lexical_overlap | 1 | 坏 | False | 0.0264161620 | −∞ | n/a | False |
| DIAG-HANS-002 | 日期 | argument_swap | 2 | 坏 | False | 0.0004841118 | −∞ | n/a | False |
| DIAG-HANS-003 | 日期 | argument_swap | 3 | 坏 | False | 0.0011600856 | −∞ | n/a | False |
| S-条款-op0 | 条款替换 | lexical_overlap | 0 | 坏 | False | 0.0018698263 | −∞ | n/a | False |
| S-条款-op1 | 条款替换 | argument_swap | 1 | 坏 | False | 0.3162308037 | −∞ | n/a | False |
| DIAG-HANS-004 | 条款替换 | lexical_overlap | 2 | 坏 | False | 0.1859738678 | −∞ | n/a | False |
| S-条款-op3 | 条款替换 | none | 3 | 坏 | False | 0.0080267889 | −∞ | n/a | False |
| DIAG-HANS-006 | 删除 | lexical_overlap | 0 | 坏 | False | 0.0104973661 | −∞ | n/a | False |
| DIAG-CHEF-03-bad | 删除 | lexical_overlap | 1 | 坏 | True | 0.8668648601 | 0.866865 | 有效 | True |
| S-删除-op2 | 删除 | none | 2 | 坏 | False | 0.0078747226 | −∞ | n/a | False |
| DIAG-CHEF-04-bad | 删除 | subsequence | 3 | 坏 | True | 0.9547298551 | 0.954730 | 有效 | True |
| S-废止-trap01 | 条款替换 | lexical_overlap |  | 坏 | False | 0.0046763993 | −∞ | n/a | False |
| S-废止-trap02 | 条款替换 | lexical_overlap |  | 坏 | False | 0.0012190399 | −∞ | n/a | False |
| S-版本-trap01 | 条款替换 | argument_swap |  | 坏 | False | 0.0051305089 | −∞ | n/a | False |
| S-版本-trap02 | 条款替换 | argument_swap |  | 坏 | False | 0.1520473212 | −∞ | n/a | False |
| S-正确-数值01 | 数值 | lexical_overlap |  | 正确 | True | 0.9943641424 | 0.994364 | n/a | False |
| S-正确-日期01 | 日期 | lexical_overlap |  | 正确 | True | 0.5039777756 | 0.503978 | n/a | False |
| S-正确-条款01 | 条款替换 | lexical_overlap |  | 正确 | True | 0.7590352893 | 0.759035 | n/a | False |
| S-正确-删除01 | 删除 | subsequence |  | 正确 | True | 0.8788937926 | 0.878894 | n/a | False |
| DIAG-CHEF-03-good | 删除 | lexical_overlap |  | 正确 | True | 0.9216354489 | 0.921635 | 有效 | False |
| DIAG-CHEF-04-good | 删除 | subsequence |  | 正确 | True | 0.9086972475 | 0.908697 | 有效 | False |

## 8. 未做

- 未写 `activation_prerequisite_met=是`。
- 未解锁 PE-Y-05，未开 GATE 真探针，未开 n=400。
- 未改 τ，未改 ρ，未改 ADR-0040，未改 `SENSITIVITY_SET_S`。
- 未合并 #543，未沿用其过早哈希。
- 无 secret_names。
