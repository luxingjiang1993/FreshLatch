# SENS-DIAG-1A · 敏感性诊断跑报告（非正式过线）

日期：2026-10-12（UTC+8）
仪器：mDeBERTa-v3 XNLI · τ=0.5 · ok 当且仅当 argmax 为 entailment 且 P(entailment)≥τ（冻结回显）
model_id：`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`
tau：`0.5`
输入锚：#538 假阳性 `S-日期-op2`、`S-日期-op3`、`S-条款-op2`、`S-删除-op0`、`S-删除-op1`、`S-删除-op3`
刺激锁：commit `17b1677`（先写入夹具，后跑分）
Trust：票面 L1（诊断证据；非正式过线；不可激活）。用户抽检 ≥30% 未做，**不得标 L1 完成**。
本文不把诊断分写成敏感性通过，也不写成激活前置已满足。

## 1. 目的与范围

目的：在冻结现行仪器下，对 #538 的 6 条 construct_bad 假阳性做平行诊断小集，按跑前锁死的 P1 规则写出偏 1A / 偏 1B / 混合。

非目的：敏感性过线、激活、乙、改 τ/ρ、正式 LIVE-2、估计 δ 或 k。

**DIAG ≠ S2。** 本页分数不能代替正式集合 S 的 S2。若要声称「S2 仍不及格」，须在阶段 2B 之前用冻结仪器对跑前锁定的新 S 或正式 S 复测 S2。本探针偏 1A，不进入 2B grilling，也不在本票开启阶段 2A 的正式 LIVE-2。

## 2. 仪器冻结声明

| 项 | 冻结值 | 本跑 |
|---|---|---|
| model_id | `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | 同左，来自 `XNLI_MODEL_ID` |
| tau | `0.5`（`ENTAILMENT_TAU`） | 同左，未改源文件 |
| ok | argmax=entailment 且 P(entailment)≥τ | 与 `verify_edit` 逐条布尔一致 |
| premise / hypothesis | evidence_text / after_text | 同 ADR-0040 |
| 权重 | 仓内既有 Hugging Face 本地缓存 | `/home/ubuntu/.cache/huggingface/hub/models--MoritzLaurer--mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` |
| 栈 | transformers 4.57.6 | 同 #538 注释 |
| torch | #538 注释为 2.8.0+cpu | 本机 2.8.0+cu128，CUDA 不可用，走 CPU |
| 密钥 | 无 secret_names，无新开云密钥 | 只读本地缓存 |

`src/freshlatch/eval/patch_events_verify.py` sha256：`58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918`（跑前跑后相同，故 `ENTAILMENT_TAU = 0.5` 字节未改）。

ok=False 时 `verify_edit` 的 score 为负无穷；下表 `P_entail` 是同一前向的 softmax 概率，供诊断阅读。每条另调用 `verify_edit`，ok 一致；ok=True 时 score 与 P_entail 一致。

### 2.1 与 #538 基线对照

六条假阳性原文复跑仍为 ok=True。六位小数对照如下（本跑给出 10 位，避免把舍入写成新分数）。

| id | #538 报告 score | 本跑 P_entail | 本跑 ok |
|---|---:|---:|---|
| S-日期-op2 | 0.998473 | 0.9984726310 | True |
| S-日期-op3 | 0.993608 | 0.9936077595 | True |
| S-条款-op2 | 0.834962 | 0.8349623680 | True |
| S-删除-op0 | 0.975588 | 0.9755883217 | True |
| S-删除-op1 | 0.980788 | 0.9807876348 | True |
| S-删除-op3 | 0.958588 | 0.9585874081 | True |
| S-正确-日期01 | 0.503976 | 0.5039777756 | True |

前五条假阳性按六位小数四舍五入后与 #538 页相同。`S-删除-op3` 差 0.000001，正确对照差 0.000002。差别停在 1e-6，与 torch 构建（+cu128 CPU 路径对 +cpu）相符，不构成换型号或改 τ。

## 3. 诊断集说明

平行小集只存在于 `DIAG-` 前缀文件，没有写入 `SENSITIVITY_SET_S`。

| 文件 | 角色 |
|---|---|
| `docs/evidence/patch-events/DIAG-sens-1a-fixtures.jsonl` | 跑前锁定的刺激、金标、`nli_construct_ok`、词重叠 |
| `docs/evidence/patch-events/DIAG-sens-1a-scores.csv` | 跑后全列分表 |

词重叠（跑前锁，阈值 0.8 只约束 CHEF）：

```text
token_overlap = |set(jieba 内容词(a)) ∩ set(jieba 内容词(b))| / min(|set(a)|, |set(b)|)
```

内容词去掉空白与纯标点。CHEF 的 `token_overlap` 是两侧 after 的表面重叠。其他行的该列是 after 对 evidence，只作描述，不是有效对门闩。jieba 不参与金标。

| stratum | 条数 | 上限 | 是否进入 P1 分母 |
|---|---:|---:|---|
| baseline_fp | 6 | 8 | 否 |
| hans | 8 | 12 | 是（金标坏且 nli_construct_ok=yes） |
| attrscore（含 1 条正确对照） | 7 | 12 | 否 |
| chef 对 | 6 对 / 12 行 | 8 对 | 仅有效对的 chef_bad |
| vitaminc | 0（未跑） | 8 对 | 否 |
| 合计刺激行 | 33 | 40 | 见下 |

HANS 按 G11：保留高词重叠，并写入与 evidence 冲突的义务、例外、日期或主体至少一项。不另写废止法名或版本陷阱去刷分。CHEF 坏侧与 HANS 的 (evidence, after) 不重复，避免同一刺激计两次。

VitaminC / Contrast pair：**未跑**。余力不足，按最小集 defer。

## 4. 探针结果

变红：金标坏且 ok=False。仍绿：金标坏且 ok=True。baseline_fp 不进分母。

### 4.1 HANS 式切片

8/8 变红。合格条件 `nli_construct_ok=yes` 已在跑前写下。

| id | subcase | heuristic | P_entail | ok | readout_tag |
|---|---|---|---:|---|---|
| DIAG-HANS-001 | 日期op2 | argument_swap | 0.0094981939 | False | turn_red |
| DIAG-HANS-002 | 日期op2 | argument_swap | 0.0004841118 | False | turn_red |
| DIAG-HANS-003 | 日期op3 | argument_swap | 0.0011600856 | False | turn_red |
| DIAG-HANS-004 | 条款op2 | lexical_overlap | 0.1859738678 | False | turn_red |
| DIAG-HANS-005 | 条款op2 | argument_swap | 0.0059149591 | False | turn_red |
| DIAG-HANS-006 | 删除op0 | lexical_overlap | 0.0104973661 | False | turn_red |
| DIAG-HANS-007 | 删除op1 | lexical_overlap | 0.2253425717 | False | turn_red |
| DIAG-HANS-008 | 删除op3 | lexical_overlap | 0.0131626641 | False | turn_red |

`DIAG-HANS-007` 的 after 对 evidence 词重叠为 0.75。0.8 不是 HANS 门闩。该条仍因显式例外冲突变红。

### 4.2 AttrScore 构念探针

标注人：Ronin 起草。日期：2026-10-12。未训练分类器。没有第二标注者。用户抽检未做。

争议条不计入 Extrapolatory 多数：`DIAG-ATTR-日期-op3`（「本办法」可被读成新办法，也可被读成未指明）。

非争议假阳性 5 条：

| 标签 | 条数 | id |
|---|---:|---|
| Attributable | 2 | DIAG-ATTR-日期-op2，DIAG-ATTR-删除-op0 |
| Extrapolatory | 2 | DIAG-ATTR-删除-op1，DIAG-ATTR-删除-op3 |
| Contradictory | 1 | DIAG-ATTR-条款-op2 |

Extrapolatory 不是多数（2/5）。正确对照 `DIAG-ATTR-正确-日期01` 标 Attributable，ok=True，P_entail=0.5039777756，不进多数。

`DIAG-ATTR-条款-op2` 为 Contradictory 且 ok=True（P_entail=0.8349623680）。这是单条强 1B 叠加信号：原文假阳性在构念上矛盾，仪器仍放行。它不在 P1 分母里。VitaminC 未跑，AttrScore **不得单独否决**已经满足 P1 的 HANS∩CHEF 偏 1A。

Attributable 但产品金标为坏的两条（日期 op2、删除 op0）说明原假阳性有一部分是测题/金标与 NLI 构念不一致，不是仪器把干净矛盾句放行。这与基线 `nli_construct_ok=no` 一致。

### 4.3 CHEF 式高重叠翻转

六对的表面 `token_overlap` 均 ≥0.8，且好侧 ok=True。六对全部有效，坏侧全部进入分母。

| pair_id | overlap | 好侧 ok | 坏侧 P_entail | 坏侧 ok | 坏侧 readout |
|---|---:|---|---:|---|---|
| DIAG-CHEF-01 | 0.900000 | True | 0.0008691100 | False | turn_red |
| DIAG-CHEF-02 | 0.857143 | True | 0.2559724152 | False | turn_red |
| DIAG-CHEF-03 | 0.875000 | True | 0.8668648601 | True | still_green |
| DIAG-CHEF-04 | 1.000000 | True | 0.9547298551 | True | still_green |
| DIAG-CHEF-05 | 0.888889 | True | 0.0005860778 | False | turn_red |
| DIAG-CHEF-06 | 0.875000 | True | 0.0009108762 | False | turn_red |

有效坏侧 6 条中变红 4 条。仍绿的两条留在分母里，不删行：

- `DIAG-CHEF-03-bad`：年限 5 年改成 3 年，P_entail=0.8668648601，仍绿。
- `DIAG-CHEF-04-bad`：删掉「大约」，P_entail=0.9547298551，仍绿。

这两条是亚型残留（数字替换、删弱化词），不是「够坏仍系统性绿」。HANS 上对应的显式义务冲突（`DIAG-HANS-007`、`DIAG-HANS-008`）已经变红。

### 4.4 VitaminC

未跑 VitaminC。没有 insensitive 读数。因此 AttrScore 不能单独否决 P1 偏 1A。

## 5. 金标 meta-eval

主金标是二元坏/好。WiCE 只作笔记，不进主读法。

删除类 `nli_construct_ok`：

| id | gold | nli_construct_ok | wice_note | 备注 |
|---|---|---|---|---|
| DIAG-BASE-删除-op0 | bad | no | supported | 主张是被肯定例外的子串 |
| DIAG-BASE-删除-op1 | bad | partial | partially_supported | 弱主张被强证据蕴含 |
| DIAG-BASE-删除-op3 | bad | partial | partially_supported | 删「大约」，不是干净矛盾 |
| DIAG-HANS-006 | bad | yes | not_supported | 已废止限定被说成仍然有效 |
| DIAG-HANS-007 | bad | yes | not_supported | 插入与年限相反的例外 |
| DIAG-HANS-008 | bad | yes | not_supported | 义务否定 |
| DIAG-CHEF-03-bad | bad | yes | not_supported | 年限数字翻转 |
| DIAG-CHEF-04-bad | bad | yes | not_supported | 删「大约」 |
| DIAG-CHEF-06-bad | bad | yes | not_supported | 例外极性翻转 |

日期 op2 / 删除 op0 的原文假阳性：`nli_construct_ok=no`，不进 P1 分母。它们说明 #538 的一部分假阳性在蕴含构念下本来就算支撑。

争议条：仅 `DIAG-ATTR-日期-op3`。已退出 Extrapolatory 多数。

## 6. 原始分表

全列 CSV：`docs/evidence/patch-events/DIAG-sens-1a-scores.csv`。同一张表附在文末附录。

`readout_tag` 只是分表展示列，不参与 P1 计数。取值：attrscore 且标签为 Extrapolatory 时记 `extrapolatory`；否则金标坏且 ok=False 记 `turn_red`；金标坏且 ok=True 记 `still_green`；其余 `n/a`。未跑 VitaminC，不用 `insensitive`。

tau 列恒为 0.5。model_id 列恒为 `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`。

## 7. 结论

- [x] 偏 1A
- [ ] 偏 1B
- [ ] 混合

一句话依据：P1 合格分母 14 条（HANS 8 条 + 有效 CHEF 坏侧 6 条；全部为金标坏且 `nli_construct_ok=yes`；不含 baseline_fp）上变红 12 条。跑前锁是 ≥4 偏 1A、≤1 偏 1B、2–3 混合。12≥4，结论为偏 1A。出口不用召回比例上升。

分层核对（同一把锁，防止把分层相反误叫成混合）：

| 分层 | 合格分母 | 变红 | 按同一阈值 |
|---|---:|---:|---|
| hans | 8 | 8 | 偏 1A |
| chef_bad（有效对） | 6 | 4 | 偏 1A |
| 合计 HANS∩CHEF | 14 | 12 | 偏 1A |

两边都 ≥4，不是分层相反。变红条数不是 2–3，所以不进入混合，也没有做第二轮 1A 补强。

AttrScore 叠加：Extrapolatory 非多数；Contradictory 仍绿 1 条（`DIAG-ATTR-条款-op2`）。VitaminC 未跑，AttrScore 不得单独否决已经满足 P1 的 HANS∩CHEF 偏 1A。

下一步：可交接阶段 2A（正式 LIVE-2 须另开 wayfinder，跑前另锁新 S，Acceptance 用 sens-gate §6.3）。本票不打开 LIVE-2，不实装 1B，不 create-adr。交接时必须带上仍绿残留 `DIAG-CHEF-03-bad` 与 `DIAG-CHEF-04-bad`：数字替换和删弱化词在高重叠下仍被放行，正式坏槽不能只换成极端极性句。

**DIAG ≠ S2。** 偏 1A 不是 S2 已及格，也不是 S2 已复测。

## 8. 明确未做

- 未改 `ENTAILMENT_TAU`，未改 S2/S3 ρ，未换型号，未改 ADR-0040。
- 未把敏感性通过写成是，未把激活前置写成是，未激活 PREREG-Y。
- 未开 PE-Y-05，未复活 #507，未开 GATE-Y 真探针。
- 未估计 δ，未跑 k 或 discordant 门闩，未声称乙，未写功效。
- 未实装 1B，未 create-adr。
- 未跑 VitaminC。
- 未改 #538 的失败结论句。
- 用户抽检 ≥30% 未完成，Trust 不得标 L1 完成。
- 无 secret_names。

## 9. Provenance

- HANS：词重叠 / 子序列 / 论元对调启发式（McCoy 等，Right for the Wrong Reasons）。
- CHEF：中文高重叠、标签相反的配对纪律。本页门闩为表面 token_overlap≥0.8 且好侧 ok=True。
- VitaminC / Contrast Sets（Gardner）：本票 defer，未跑。
- AttrScore 三分类：Attributable / Extrapolatory / Contradictory。Ronin 起草，无分类器。
- 仓内 #521：legal-hallucination-bench / verified-chinese-law-kb 协议同族。本页不引用仓外准确率当过线。
- sens-gate §5：诊断探针读法。出口计数以阶段 1 计划 P1/G13 为准，不用该节里单独的「召回上升」句子当出口。
- 输入文本来自 #538 评论与 `GATE-Y-SENSITIVITY.md` 中的六条假阳性原文。

## 10. Grill 锁（G1–G24，跑前已锁，本页只引用）

| # | 本跑采用的锁 |
|---|---|
| G1 | 仪器与 #538 同款，τ=0.5 |
| G2 | 平行小集，不改正式 S |
| G3 | 允许 baseline_fp，且不进分母 |
| G4 | 不动 ADR-0040 / verify_edit / 型号 |
| G5 | 二元坏/好；WiCE 只作笔记 |
| G6 | Ronin 起草金标；用户抽检 ≥30% 尚未做 |
| G7 | 删除类记 `nli_construct_ok` |
| G8 | AttrScore 由 Ronin 起草；抽检未做；争议条退出多数 |
| G9 | 最小集：HANS + CHEF + AttrScore；VitaminC defer |
| G10 | 每层 ≤12；总行 33≤40 |
| G11 | 高重叠加至少一项义务/例外/日期/主体冲突 |
| G12 | CHEF：token_overlap≥0.8 且好侧 ok=True，否则对无效 |
| G13 | 分母=金标坏且 nli_construct_ok∈{yes,partial} 的 hans/chef_bad，不含 baseline_fp；≥4 偏1A；≤1 偏1B；2–3 混合 |
| G14 | 与 G13 相同；够坏仍系统性绿才是偏 1B |
| G15 | Extrapolatory 多数才叠加偏 1B；无 VitaminC 时不得单独否决 P1 偏 1A |
| G16 | VitaminC 未跑，本条不产生读数 |
| G17 | 混合才补强一轮；本跑不是混合，未补强 |
| G18 | 产物为本页 + DIAG- 夹具；#538 只加链接 |
| G19 | 不写敏感性通过为是 |
| G20 | 不改 τ/ρ，不复活 #507，不开 PE-Y-05 |
| G21 | 无 secret_names |
| G22 | 不 create-adr |
| G23 | 不估计 δ；SESOI=0.05 与 k_min=10 只引用 |
| G24 | DIAG ≠ S2；本结论是偏 1A，不是「S2 仍不及格」的正式复测 |

## 11. 正式 S 名单哈希

哈希对象：`SENSITIVITY_SET_S` 的 24 条，字段 `sample_id, stratum, operator, gold, kind, after_text, evidence_text, note`，JSON `ensure_ascii=false`、`sort_keys=true`、分隔符 `(',', ':')` 的 UTF-8 sha256。

| 时点 | sha256 |
|---|---|
| 写入 DIAG 夹具之前 | `958638ca0f3dc51323db710a69f4eacacc2fcff10186a99b07aecc47821d838b` |
| 跑分并写入本页之后 | `958638ca0f3dc51323db710a69f4eacacc2fcff10186a99b07aecc47821d838b` |

`patch_events_sensitivity.py` sha256：`6a94996bb076cc21a61bcc8562210867cdb022c85a01ac9f89a02c206f7a0ef1`。

## 12. 票面 Acceptance 如何被本页覆盖

可直接核对的项：τ 未改；model_id 与 tau 已回显；标题含 DIAG；无升格句；结论为偏 1A；分表列在 CSV 与第 6 节；删除类有 `nli_construct_ok`；夹具前缀 `DIAG-`；正式 S 哈希未变；CHEF 门闩已执行；VitaminC defer 已写明；DIAG ≠ S2 已写明；AttrScore 不得单独否决已写明；未改代码路径。

尚未完成、不能勾成完成的项：用户抽检 ≥30% 或第二标注。在该勾选完成之前，Trust 不得标 L1 完成。

## 附录 · 全列分表



| id | source_fp_id | stratum | heuristic | subcase | gold | wice_note | nli_construct_ok | attrscore_label | attrscore_annotator | token_overlap | pair_id | evidence_text | after_text | P_entail | ok | tau | model_id | readout_tag | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DIAG-BASE-日期-op2 | S-日期-op2 | baseline_fp | none | 日期op2 | bad | supported | no | n/a | n/a | 1.000000 |  | 公布日期为 2022 年 7 月 7 日；施行日期为 2022 年 9 月 1 日。 | 施行日期为 2022 年 9 月 1 日。 | 0.9984726310 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | #538 假阳性原文。主张与证据中施行日同角色逐字相符，金标坏在 NLI 构念下不成立。 argmax=entailment；P_neutral=0.000992；P_contradiction=0.000536；verify_reason=支撑成立 |
| DIAG-BASE-日期-op3 | S-日期-op3 | baseline_fp | none | 日期op3 | bad | partially_supported | partial | n/a | n/a | 0.900000 |  | 旧办法自 2020 年 1 月 1 日起施行；新办法自 2022 年 9 月 1 日起施行。 | 本办法自 2022 年 9 月 1 日起施行。 | 0.9936077595 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | #538 假阳性原文。本办法未在证据中出现，需等同新办法。 argmax=entailment；P_neutral=0.003681；P_contradiction=0.002711；verify_reason=支撑成立 |
| DIAG-BASE-条款-op2 | S-条款-op2 | baseline_fp | none | 条款op2 | bad | not_supported | yes | n/a | n/a | 0.571429 |  | 个人信息出境应当适用标准合同办法。 | 关键个人信息出境认证办法适用于本条。 | 0.8349623680 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | #538 假阳性原文。认证办法与标准合同办法不是同一适用依据。 argmax=entailment；P_neutral=0.155010；P_contradiction=0.010028；verify_reason=支撑成立 |
| DIAG-BASE-删除-op0 | S-删除-op0 | baseline_fp | none | 删除op0 | bad | supported | no | n/a | n/a | 1.000000 |  | 留存不少于 5 年这一限定已废止。除金融机构外这一例外仍然有效。 | 除金融机构外这一例外仍然有效。 | 0.9755883217 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | #538 假阳性原文。主张是证据所肯定例外的子串，金标坏在 NLI 构念下不成立。 argmax=entailment；P_neutral=0.020749；P_contradiction=0.003663；verify_reason=支撑成立 |
| DIAG-BASE-删除-op1 | S-删除-op1 | baseline_fp | none | 删除op1 | bad | partially_supported | partial | n/a | n/a | 1.000000 |  | 个人信息应当依法处理，留存不少于 5 年。 | 个人信息应当依法处理。 | 0.9807876348 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | #538 假阳性原文。弱主张被强证据蕴含；产品坏点是删掉仍支持的年限。 argmax=entailment；P_neutral=0.018825；P_contradiction=0.000387；verify_reason=支撑成立 |
| DIAG-BASE-删除-op3 | S-删除-op3 | baseline_fp | none | 删除op3 | bad | partially_supported | partial | n/a | n/a | 1.000000 |  | 处理者应当大约保存记录。 | 处理者应当保存记录。 | 0.9585874081 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | #538 假阳性原文。删掉大约使义务语气变硬，不是干净矛盾。 argmax=entailment；P_neutral=0.036580；P_contradiction=0.004833；verify_reason=支撑成立 |
| DIAG-HANS-001 | S-日期-op2 | hans | argument_swap | 日期op2 | bad | not_supported | yes | n/a | n/a | 1.000000 |  | 公布日期为 2022 年 7 月 7 日；施行日期为 2022 年 9 月 1 日。 | 公布日期为 2022 年 9 月 1 日。 | 0.0094981939 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 把施行日错挂为公布日。高词重叠，显式日期角色冲突。 人工 meta-eval：金标坏在 NLI 构念下成立（主张不被证据蕴含）。 argmax=contradiction；P_neutral=0.002781；P_contradiction=0.987720；verify_reason=核验不过 |
| DIAG-HANS-002 | S-日期-op2 | hans | argument_swap | 日期op2 | bad | not_supported | yes | n/a | n/a | 1.000000 |  | 公布日期为 2022 年 7 月 7 日；施行日期为 2022 年 9 月 1 日。 | 施行日期为 2022 年 7 月 7 日。 | 0.0004841118 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 把公布日错挂为施行日。高词重叠，显式日期角色冲突。 人工 meta-eval：金标坏在 NLI 构念下成立（主张不被证据蕴含）。 argmax=contradiction；P_neutral=0.000925；P_contradiction=0.998591；verify_reason=核验不过 |
| DIAG-HANS-003 | S-日期-op3 | hans | argument_swap | 日期op3 | bad | not_supported | yes | n/a | n/a | 1.000000 |  | 旧办法自 2020 年 1 月 1 日起施行；新办法自 2022 年 9 月 1 日起施行。 | 旧办法自 2022 年 9 月 1 日起施行。 | 0.0011600856 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 旧办法错取新办法施行日。高词重叠，显式主体冲突。 人工 meta-eval：金标坏在 NLI 构念下成立（主张不被证据蕴含）。 argmax=contradiction；P_neutral=0.001135；P_contradiction=0.997705；verify_reason=核验不过 |
| DIAG-HANS-004 | S-条款-op2 | hans | lexical_overlap | 条款op2 | bad | not_supported | yes | n/a | n/a | 0.833333 |  | 个人信息出境应当适用标准合同办法。 | 个人信息出境应当适用认证办法。 | 0.1859738678 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 义务句架保留，办法名称与证据冲突。 人工 meta-eval：金标坏在 NLI 构念下成立（主张不被证据蕴含）。 argmax=neutral；P_neutral=0.642572；P_contradiction=0.171454；verify_reason=核验不过 |
| DIAG-HANS-005 | S-条款-op2 | hans | argument_swap | 条款op2 | bad | not_supported | yes | n/a | n/a | 0.857143 |  | 个人信息出境应当适用标准合同办法。 | 关键信息基础设施运营者出境应当适用标准合同办法。 | 0.0059149591 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 办法名与应当保留，主体错挂。 人工 meta-eval：金标坏在 NLI 构念下成立（主张不被证据蕴含）。 argmax=neutral；P_neutral=0.989749；P_contradiction=0.004336；verify_reason=核验不过 |
| DIAG-HANS-006 | S-删除-op0 | hans | lexical_overlap | 删除op0 | bad | not_supported | yes | n/a | n/a | 1.000000 |  | 留存不少于 5 年这一限定已废止。除金融机构外这一例外仍然有效。 | 留存不少于 5 年这一限定仍然有效。 | 0.0104973661 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 把已废止的年限限定说成仍然有效。例外极性冲突，不是另写废止法名陷阱。 人工 meta-eval：金标坏在 NLI 构念下成立（主张不被证据蕴含）。 argmax=contradiction；P_neutral=0.008477；P_contradiction=0.981026；verify_reason=核验不过 |
| DIAG-HANS-007 | S-删除-op1 | hans | lexical_overlap | 删除op1 | bad | not_supported | yes | n/a | n/a | 0.750000 |  | 个人信息应当依法处理，留存不少于 5 年。 | 个人信息应当依法处理，但留存可以少于 5 年。 | 0.2253425717 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 保留原句架，插入与年限义务相反的例外。 人工 meta-eval：金标坏在 NLI 构念下成立（主张不被证据蕴含）。 argmax=contradiction；P_neutral=0.044769；P_contradiction=0.729889；verify_reason=核验不过 |
| DIAG-HANS-008 | S-删除-op3 | hans | lexical_overlap | 删除op3 | bad | not_supported | yes | n/a | n/a | 0.833333 |  | 处理者应当大约保存记录。 | 处理者不应当保存记录。 | 0.0131626641 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 保留处理者与保存记录，插入义务否定。 人工 meta-eval：金标坏在 NLI 构念下成立（主张不被证据蕴含）。 argmax=contradiction；P_neutral=0.019543；P_contradiction=0.967295；verify_reason=核验不过 |
| DIAG-ATTR-日期-op2 | S-日期-op2 | attrscore | none | 日期op2 | bad | supported | no | Attributable | Ronin起草 | 1.000000 |  | 公布日期为 2022 年 7 月 7 日；施行日期为 2022 年 9 月 1 日。 | 施行日期为 2022 年 9 月 1 日。 | 0.9984726310 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | 标注日 2026-10-12。主张「施行日期为 2022 年 9 月 1 日」与证据同角色逐字相符。 假设：人工三分类，未训练分类器；自动化仅辅助未使用。 争议=否。 用户抽检未完成。 argmax=entailment；P_neutral=0.000992；P_contradiction=0.000536；verify_reason=支撑成立 |
| DIAG-ATTR-日期-op3 | S-日期-op3 | attrscore | none | 日期op3 | bad | partially_supported | partial | Extrapolatory | Ronin起草 | 0.900000 |  | 旧办法自 2020 年 1 月 1 日起施行；新办法自 2022 年 9 月 1 日起施行。 | 本办法自 2022 年 9 月 1 日起施行。 | 0.9936077595 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | extrapolatory | 标注日 2026-10-12。争议条：本办法未出现，可被读成新办法（偏 Attributable）或未指明（偏 Extrapolatory）。不计入 Extrapolatory 多数。 假设：人工三分类，未训练分类器；自动化仅辅助未使用。 争议=是。 用户抽检未完成。 argmax=entailment；P_neutral=0.003681；P_contradiction=0.002711；verify_reason=支撑成立 |
| DIAG-ATTR-条款-op2 | S-条款-op2 | attrscore | none | 条款op2 | bad | not_supported | yes | Contradictory | Ronin起草 | 0.571429 |  | 个人信息出境应当适用标准合同办法。 | 关键个人信息出境认证办法适用于本条。 | 0.8349623680 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | 标注日 2026-10-12。证据指定标准合同办法，主张改挂认证办法，适用依据冲突。 假设：人工三分类，未训练分类器；自动化仅辅助未使用。 争议=否。 用户抽检未完成。 argmax=entailment；P_neutral=0.155010；P_contradiction=0.010028；verify_reason=支撑成立 |
| DIAG-ATTR-删除-op0 | S-删除-op0 | attrscore | none | 删除op0 | bad | supported | no | Attributable | Ronin起草 | 1.000000 |  | 留存不少于 5 年这一限定已废止。除金融机构外这一例外仍然有效。 | 除金融机构外这一例外仍然有效。 | 0.9755883217 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | 标注日 2026-10-12。主张是证据中被肯定例外的子串，逐字可归因。 假设：人工三分类，未训练分类器；自动化仅辅助未使用。 争议=否。 用户抽检未完成。 argmax=entailment；P_neutral=0.020749；P_contradiction=0.003663；verify_reason=支撑成立 |
| DIAG-ATTR-删除-op1 | S-删除-op1 | attrscore | none | 删除op1 | bad | partially_supported | partial | Extrapolatory | Ronin起草 | 1.000000 |  | 个人信息应当依法处理，留存不少于 5 年。 | 个人信息应当依法处理。 | 0.9807876348 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | extrapolatory | 标注日 2026-10-12。主张是证据子串，但删掉证据仍支持的留存年限。按 sens-gate 删除弱化记 Extrapolatory。 假设：人工三分类，未训练分类器；自动化仅辅助未使用。 争议=否。 用户抽检未完成。 argmax=entailment；P_neutral=0.018825；P_contradiction=0.000387；verify_reason=支撑成立 |
| DIAG-ATTR-删除-op3 | S-删除-op3 | attrscore | none | 删除op3 | bad | partially_supported | partial | Extrapolatory | Ronin起草 | 1.000000 |  | 处理者应当大约保存记录。 | 处理者应当保存记录。 | 0.9585874081 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | extrapolatory | 标注日 2026-10-12。删掉大约使义务语气变硬，证据只有弱化表述。非逐字可归因，也未直接否定证据。 假设：人工三分类，未训练分类器；自动化仅辅助未使用。 争议=否。 用户抽检未完成。 argmax=entailment；P_neutral=0.036580；P_contradiction=0.004833；verify_reason=支撑成立 |
| DIAG-ATTR-正确-日期01 | S-正确-日期01 | attrscore | none | 日期op | good | supported | n/a | Attributable | Ronin起草 | 0.900000 |  | 本办法自公布之日起施行；公布日为 2024 年 3 月 22 日。 | 本办法自 2024 年 3 月 22 日起施行。 | 0.5039777756 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | n/a | 标注日 2026-10-12。正确对照，#538 贴边例。公布日即施行起算日，主张可归因。争议=否。用户抽检未完成。 argmax=entailment；P_neutral=0.299596；P_contradiction=0.196426；verify_reason=支撑成立 |
| DIAG-CHEF-01-good | S-日期-op2 | chef_good | argument_swap | 日期op2 | good | supported | n/a | n/a | n/a | 0.900000 | DIAG-CHEF-01 | 本办法公布日期为 2022 年 7 月 7 日，施行日期为 2022 年 9 月 1 日。 | 本办法施行日期为 2022 年 9 月 1 日。 | 0.9970442653 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | n/a | 同句架，施行日取公布日。 好侧。有效对还须跑后 ok=True，否则整对无效。 argmax=entailment；P_neutral=0.001877；P_contradiction=0.001078；verify_reason=支撑成立 |
| DIAG-CHEF-01-bad | S-日期-op2 | chef_bad | argument_swap | 日期op2 | bad | not_supported | yes | n/a | n/a | 0.900000 | DIAG-CHEF-01 | 本办法公布日期为 2022 年 7 月 7 日，施行日期为 2022 年 9 月 1 日。 | 本办法施行日期为 2022 年 7 月 7 日。 | 0.0008691100 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 同句架，施行日取公布日。 坏侧。人工 meta-eval：金标坏在 NLI 构念下成立。 argmax=contradiction；P_neutral=0.001893；P_contradiction=0.997238；verify_reason=核验不过 |
| DIAG-CHEF-02-good | S-条款-op2 | chef_good | lexical_overlap | 条款op2 | good | supported | n/a | n/a | n/a | 0.857143 | DIAG-CHEF-02 | 本条个人信息出境应当适用标准合同办法。 | 本条个人信息出境应当适用标准合同办法。 | 0.9493734837 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | n/a | 同句架，办法名称翻转。 好侧。有效对还须跑后 ok=True，否则整对无效。 argmax=entailment；P_neutral=0.047483；P_contradiction=0.003144；verify_reason=支撑成立 |
| DIAG-CHEF-02-bad | S-条款-op2 | chef_bad | lexical_overlap | 条款op2 | bad | not_supported | yes | n/a | n/a | 0.857143 | DIAG-CHEF-02 | 本条个人信息出境应当适用标准合同办法。 | 本条个人信息出境应当适用认证办法。 | 0.2559724152 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 同句架，办法名称翻转。 坏侧。人工 meta-eval：金标坏在 NLI 构念下成立。 argmax=neutral；P_neutral=0.561216；P_contradiction=0.182811；verify_reason=核验不过 |
| DIAG-CHEF-03-good | S-删除-op1 | chef_good | lexical_overlap | 删除op1 | good | supported | n/a | n/a | n/a | 0.875000 | DIAG-CHEF-03 | 个人信息应当依法处理，留存不少于 5 年。 | 个人信息应当依法处理，留存不少于 5 年。 | 0.9216354489 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | n/a | 同句架，年限数字翻转。 好侧。有效对还须跑后 ok=True，否则整对无效。 argmax=entailment；P_neutral=0.062620；P_contradiction=0.015745；verify_reason=支撑成立 |
| DIAG-CHEF-03-bad | S-删除-op1 | chef_bad | lexical_overlap | 删除op1 | bad | not_supported | yes | n/a | n/a | 0.875000 | DIAG-CHEF-03 | 个人信息应当依法处理，留存不少于 5 年。 | 个人信息应当依法处理，留存不少于 3 年。 | 0.8668648601 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | 同句架，年限数字翻转。 坏侧。人工 meta-eval：金标坏在 NLI 构念下成立。 argmax=entailment；P_neutral=0.054756；P_contradiction=0.078379；verify_reason=支撑成立 |
| DIAG-CHEF-04-good | S-删除-op3 | chef_good | subsequence | 删除op3 | good | supported | n/a | n/a | n/a | 1.000000 | DIAG-CHEF-04 | 处理者应当大约保存出境记录。 | 处理者应当大约保存出境记录。 | 0.9086972475 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | n/a | 同句架，删掉大约。坏侧像支撑。 好侧。有效对还须跑后 ok=True，否则整对无效。 argmax=entailment；P_neutral=0.082505；P_contradiction=0.008798；verify_reason=支撑成立 |
| DIAG-CHEF-04-bad | S-删除-op3 | chef_bad | subsequence | 删除op3 | bad | not_supported | yes | n/a | n/a | 1.000000 | DIAG-CHEF-04 | 处理者应当大约保存出境记录。 | 处理者应当保存出境记录。 | 0.9547298551 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | still_green | 同句架，删掉大约。坏侧像支撑。 坏侧。人工 meta-eval：金标坏在 NLI 构念下成立。 argmax=entailment；P_neutral=0.040857；P_contradiction=0.004413；verify_reason=支撑成立 |
| DIAG-CHEF-05-good | S-日期-op3 | chef_good | argument_swap | 日期op3 | good | supported | n/a | n/a | n/a | 0.888889 | DIAG-CHEF-05 | 旧办法自 2020 年 1 月 1 日起施行；新办法自 2022 年 9 月 1 日起施行。 | 新办法自 2022 年 9 月 1 日起施行。 | 0.9964175224 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | n/a | 同句架，新办法错取旧办法日期。 好侧。有效对还须跑后 ok=True，否则整对无效。 argmax=entailment；P_neutral=0.002275；P_contradiction=0.001308；verify_reason=支撑成立 |
| DIAG-CHEF-05-bad | S-日期-op3 | chef_bad | argument_swap | 日期op3 | bad | not_supported | yes | n/a | n/a | 0.888889 | DIAG-CHEF-05 | 旧办法自 2020 年 1 月 1 日起施行；新办法自 2022 年 9 月 1 日起施行。 | 新办法自 2020 年 1 月 1 日起施行。 | 0.0005860778 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 同句架，新办法错取旧办法日期。 坏侧。人工 meta-eval：金标坏在 NLI 构念下成立。 argmax=contradiction；P_neutral=0.001949；P_contradiction=0.997465；verify_reason=核验不过 |
| DIAG-CHEF-06-good | S-删除-op0 | chef_good | lexical_overlap | 删除op0 | good | supported | n/a | n/a | n/a | 0.875000 | DIAG-CHEF-06 | 留存不少于 5 年这一限定已废止。除金融机构外这一例外仍然有效。 | 除金融机构外这一例外仍然有效。 | 0.9755883217 | True | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | n/a | 同句架，例外极性翻转。不是废止法名陷阱。 好侧。有效对还须跑后 ok=True，否则整对无效。 argmax=entailment；P_neutral=0.020749；P_contradiction=0.003663；verify_reason=支撑成立 |
| DIAG-CHEF-06-bad | S-删除-op0 | chef_bad | lexical_overlap | 删除op0 | bad | not_supported | yes | n/a | n/a | 0.875000 | DIAG-CHEF-06 | 留存不少于 5 年这一限定已废止。除金融机构外这一例外仍然有效。 | 除金融机构外这一例外不再有效。 | 0.0009108762 | False | 0.5 | MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 | turn_red | 同句架，例外极性翻转。不是废止法名陷阱。 坏侧。人工 meta-eval：金标坏在 NLI 构念下成立。 argmax=contradiction；P_neutral=0.000607；P_contradiction=0.998482；verify_reason=核验不过 |
