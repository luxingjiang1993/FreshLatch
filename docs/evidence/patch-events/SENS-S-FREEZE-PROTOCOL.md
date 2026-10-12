# SENS-S-FREEZE 协议锁（跑前冻结正式 S）

日期：2026-10-12（UTC+8）
票：PE-Y-SENS-S-FREEZE · GitHub #544
父图：#517
下游：#542（Depends-on 本冻结哈希；本票不实现 LIVE-2）
状态：协议已锁，正式 S 已冻结。本页不打分，不写 S1–S4，不写过线。

冻结名单 sha256：`e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`

清单：`docs/evidence/patch-events/SENS-S-FREEZE-formal-S.jsonl`
权威名单是该 jsonl 的 26 条 `record_type=sample`。本页若与 jsonl 冲突，以 jsonl 为准，并视为协议锁破损，不得开跑。

## 0. 本页做什么

书面锁正式敏感性集合 S 的修订协议，并把跑前名单冻结到可复核的 sha256。
`DIAG-CHEF-03-bad`（年限 5 年改为 3 年）与 `DIAG-CHEF-04-bad`（删掉「大约」）必须在冻结名单里。

本页不做：

- 不跑 LIVE-2，不加载 NLI 权重，不写分数。
- 不改 τ、不改 ρ、不改 ADR-0040、不改 `ENTAILMENT_TAU`、不改 `ok` 公式。
- 不写 `activation_prerequisite_met=是`，不激活 `PREREG-Y`。
- 不合并、不续写 draft PR #543。
- 不把 `SENSITIVITY_SET_S` 改成新名单。代码里的旧 24 条仍是 #538 口径，哈希见下。接线属 #542。
- 无 secret_names，无新开云密钥。

## 1. 算子锁

沿用 `src/freshlatch/eval/patch_events_construct.py` 的四层生产算子。每一层 operator 0..3 恰好一条 `construct_bad`。本票不改构造器源码。

| 层 | op0 | op1 | op2 | op3 |
|---|---|---|---|---|
| 数值 | 数值约 ±10%（`_numeric_percent`） | 数量级 ×10 或 ÷10 | 错配证据里的另一个数 | 单位沿循环错配 |
| 日期 | 年份 ±1 | 月份平移 | 日期角色对调：施行日取另一个日期 | 绑到过期证据面（生产路径是 T0） |
| 条款替换 | 应当 / 不得翻转 | 主体错配 | 同句架错挂另一办法或另一条款 | 证据块不含该义务 |
| 删除 | 仍有效的限定被删，或已废止限定被说成仍然有效 | 年限 / 阈值被改坏；证据仍支持原阈值 | 空证据硬拒 | 删掉不改变事实的修饰（「大约」等） |

正式槽相对生产函数的唯一改写，是第 5 节的六条退役与替换。替换仍落在同一层、同一 operator，不新开第五层。

废止陷阱、版本陷阱各两条，文本与代码里 `SENSITIVITY_SET_S` 的四条陷阱逐字相同，不新写极端废止句。

## 2. 两库抽取规则

协议同族是 #521 纪要 `docs/research/pe_v2中文法律域支撑度核验候选调研.md` §2.8、§2.9 与文末事实句 7、8。两库只提供抽取纪律。它们的 HVI、逐字 EXACT、KB 覆盖条数都不是本仓过线分。

`legal-hallucination-bench`：

1. 敏感性金标用二元坏/好。不把该库的逐字 1.0/0.0 门禁当成 `verify_edit` 的 `ok`。
2. 废止法陷阱保持有限条：证据写明「同时废止」，主张仍称「有效」或「继续施行」。不把废止法名扩成刷分集。
3. 答案级维度（编造判例、循环引注、自相矛盾）不进入本集合。

`verified-chinese-law-kb`：

1. 版本轴：只有证据已经写下修订或废止，主张仍沿用旧法，才构成版本/废止坏槽。
2. 逐字纪律：主张若是证据里被肯定的子串，不得再标成坏。因此退役 `S-日期-op2` 与 `S-删除-op0`。
3. 不得把该 KB 的存在或下游基准分数写成 FreshLatch 已过线。

## 3. 坏槽定义

坏槽必须同时满足：

1. 金标=坏。
2. 与生产坏改同族：改数字、改日期角色或主体、错挂办法或主体、删或硬化义务、废止或版本错配。
3. 高重叠，但金标仍然是坏。禁止只写入与证据无关、专为过闸准备的极端句。

高重叠的操作定义与 SENS-DIAG-1A 相同，jieba 0.42.1：

```text
token_overlap = |set(jieba 内容词(a)) ∩ set(jieba 内容词(b))| / min(|set(a)|, |set(b)|)
```

内容词去掉空白与纯标点，保留数字。jieba 不参与金标。CHEF 行的 `token_overlap` 是两侧 after 的表面重叠，`token_overlap_role=pair_after`。其余行是 after 对 evidence，`token_overlap_role=after_vs_evidence`。空证据无定义，记 null，`token_overlap_role=undefined`。

冻结时已经算完并写入 jsonl。之后不得用另一版分词器改这些数字。

新换上的 construct_bad，after 对 evidence 的 token_overlap 均 ≥ 0.833333。下列原槽低于 0.8，跑前已经看见，保留，不按分数改句：

| sample_id | 冻结重叠 | 保留原因 |
|---|---:|---|
| `S-条款-op1` | 见 jsonl | 生产主体错配 |
| `S-条款-op3` | 见 jsonl | 证据块不含该义务，低重叠是算子本身 |
| `S-删除-op2` | null | 空证据硬拒对照 |
| 四条废止/版本陷阱 | 见 jsonl | 显式矛盾，不是本轮新写的高重叠坏槽 |

坏槽条数锁死 20，与 #538 同口径。禁止再加易拒句把分母稀释过去。

## 4. 金标、删除类笔记、抽检

主读法是二元坏/好。落盘字段 `gold` 与现行代码字面量对齐：坏写作「坏」，好写作「正确」。协议里的「好」就是 `gold=正确`。没有第三档。WiCE 与 `nli_construct_ok` 不进入主读法，也不能单独改 τ 或 ρ。

删除类（`stratum=删除` 且 `gold=坏`）必须另记：

- `nli_construct_ok`：`yes` / `partial` / `no`。含义是「金标=坏在 NLI 构念下是否成立」。
- `wice_note`：`supported` / `partially_supported` / `not_supported`。

| sample_id | gold | nli_construct_ok | wice_note | 笔记是否进入主读法 |
|---|---|---|---|---|
| `DIAG-HANS-006` | 坏 | yes | not_supported | 否 |
| `DIAG-CHEF-03-bad` | 坏 | yes | not_supported | 否 |
| `S-删除-op2` | 坏 | yes | not_supported | 否 |
| `DIAG-CHEF-04-bad` | 坏 | yes | not_supported | 否 |
| `S-正确-删除01` | 正确 | n/a | supported | 否 |
| `DIAG-CHEF-03-good` | 正确 | n/a | supported | 否 |
| `DIAG-CHEF-04-good` | 正确 | n/a | supported | 否 |

`DIAG-CHEF-04-bad` 沿用 SENS-DIAG-1A 已写的 `nli_construct_ok=yes`，不改成 `partial`。#538 原文 `S-删除-op3` 曾被诊断为 partial，那条文本已退役，不得把 partial 事后改写来解释 CHEF-04。

非删除类里，只有 DIAG 已经写过 meta-eval 的替换条（`DIAG-HANS-002`、`DIAG-HANS-003`、`DIAG-HANS-004`）带上当时的 `nli_construct_ok=yes` 与 `wice_note=not_supported`。其余保留条记 `n/a`，表示本冻结没有新做构念裁决。

签署与抽检计划（计划已写，抽检未做）：

- 金标起草：Ronin。坏/好沿用其在 SENS-DIAG-1A 的 meta-eval，以及 #538 正式 S 里未退役原槽的金标。本文件由 #544 implement 会话落盘，不新造金标。`S-删除-op2` 的删除类笔记在本冻结补记，依据是空证据不蕴含主张，不是模型分。
- 抽检人：用户（Oriental Ronin），或另一名标注者。起草 agent 不能自己勾完成。
- 比例：冻结 26 条，抽检至少 ceil(0.30×26)=8 条。
- 计划必抽：`DIAG-CHEF-03-bad`、`DIAG-CHEF-03-good`、`DIAG-CHEF-04-bad`、`DIAG-CHEF-04-good`、`DIAG-HANS-002`、`DIAG-HANS-004`、`S-数值-op0`、`S-条款-op1`。建议再加 `S-废止-trap01`，使四层与陷阱都有抽检。
- 抽检未完成之前，不得把本页标成「抽检已完成」，也不得把 Trust 标成 L1 完成。本页 Trust 只是协议/冻结产物。

争议计数：

1. 主读法只数二元 `gold`。
2. 只对 `nli_construct_ok` 或 `wice_note` 有异议：不改 `gold`，不把该条移出名单。
3. 对二元 `gold` 有异议：该条标为争议，退出此后任何主读法计数，直到整份 S 重新冻结。禁止在冻结文件里直接改金标。
4. 看见模型分数之后再改金标、改槽或改读法，视为 HARKing，该次运行作废。

## 5. 相对 #538 正式 S 的替换

退役、不得出现在本冻结名单：

| 退役 id | 原因 |
|---|---|
| `S-日期-op2` | 施行日是证据里被肯定的子串。DIAG 记 `nli_construct_ok=no` |
| `S-日期-op3` | 「本办法」未在证据中出现 |
| `S-条款-op2` | 表面重叠 0.571429，低于 0.8 |
| `S-删除-op0` | 主张是被肯定例外的子串。DIAG 记 `nli_construct_ok=no` |
| `S-删除-op1` | 整段删掉年限后，弱主张被强证据蕴含。同族改由 5 年→3 年承担 |
| `S-删除-op3` | 同族删「大约」改由 `DIAG-CHEF-04-bad` 承担，避免近重复 |

换上：

| 新 id | 槽 | 文本要点 |
|---|---|---|
| `DIAG-HANS-002` | 日期 op2 | 施行日取公布日 |
| `DIAG-HANS-003` | 日期 op3 | 旧办法错取新办法施行日 |
| `DIAG-HANS-004` | 条款 op2 | 同句架，标准合同办法改为认证办法 |
| `DIAG-HANS-006` | 删除 op0 | 已废止的年限限定被说成仍然有效 |
| `DIAG-CHEF-03-bad` | 删除 op1 | Must-carry。不少于 5 年改为不少于 3 年 |
| `DIAG-CHEF-04-bad` | 删除 op3 | Must-carry。删掉「大约」 |

刻意不入集：

| id | 原因 |
|---|---|
| `DIAG-HANS-001` | 与 HANS-002 共用证据，方向相反。留一条，避免同一证据计两次 |
| `DIAG-HANS-005` | 条款 op2 已由 HANS-004 承担。不再加第二条易拒句 |
| `DIAG-HANS-007` | 插入相反例外。DIAG 上已变红。不放在 CHEF-03 旁边稀释 must-carry，也不当作年限槽的替身 |
| `DIAG-HANS-008` | 「处理者不应当保存记录」是极端否定。同族由删「大约」承担 |

入集时不用模型分数做筛。DIAG 只用来区分「金标在 NLI 下不成立的旧槽」和「高重叠、金标仍为坏的同族改写」。DIAG 的 P_entail 不是本集合的 S2。

## 6. CHEF 配对门闩

只入两对。两侧文本与 `DIAG-sens-1a-fixtures.jsonl` 逐字相同。

| pair_id | 好侧 | 坏侧 | 冻结 token_overlap | 阈值 |
|---|---|---|---:|---:|
| `DIAG-CHEF-03` | `DIAG-CHEF-03-good` | `DIAG-CHEF-03-bad` | 0.875000 | ≥ 0.8 |
| `DIAG-CHEF-04` | `DIAG-CHEF-04-good` | `DIAG-CHEF-04-bad` | 1.000000 | ≥ 0.8 |

有效对的两个条件缺一不可：

1. 两侧 after 的 `token_overlap` ≥ 0.8。阈值若要改，必须在开跑前另写一版冻结，禁止跑后改。
2. 好侧 `ok=True`。否则整对无效。

无效对的处置：不得把坏侧移出 S2 分母，也不得改写好侧文本去补救。S2 分母是全部 `gold=坏` 的 20 条，含两条 must-carry。好侧同时是正确对照；好侧不为 `ok=True` 时，该对无效，且该条计入正确对照失败。本票不计算 S2/S3。

### 6.1 CHEF-03 好侧年限未扰，且 DIAG 下仍绿

`DIAG-CHEF-03-good` 的 `after_text` 与 `evidence_text` 同为：

`个人信息应当依法处理，留存不少于 5 年。`

年限是 5 年，不是 3 年。坏侧才是「不少于 3 年」。好侧没有被扰动。

SENS-DIAG-1A §4.3 在冻结仪器下记录该好侧 `ok=True`，`P_entail=0.9216354489`，`tau=0.5`，`model_id` 与下节相同。这是配对有效的诊断证据，不是 LIVE-2，也不是 S2。本票不重跑这条。

#542 真跑时必须用本冻结文本再量一次好侧 `ok`。若不为 True，`DIAG-CHEF-03` 对无效。禁止把好侧改成别的句子来维持「仍绿」。

## 7. 冻结哈希与开跑纪律

哈希对象：26 条 sample，按 `canonical_index` 升序。JSON `ensure_ascii=false`、`sort_keys=true`、分隔符 `(',', ':')` 的 UTF-8 sha256。不含 jsonl 首行 header。

```python
import hashlib, json
from pathlib import Path

rows = []
for line in Path("docs/evidence/patch-events/SENS-S-FREEZE-formal-S.jsonl").read_text(encoding="utf-8").splitlines():
    obj = json.loads(line)
    if obj.get("record_type") == "sample":
        rows.append(obj)
rows.sort(key=lambda row: row["canonical_index"])
blob = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
print(hashlib.sha256(blob).hexdigest())
```

冻结 sha256：`e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`

| 对照 | sha256 | 含义 |
|---|---|---|
| 本冻结 26 条 | `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19` | #542 的 Depends-on。开跑前、跑后都必须等于它 |
| 代码 `SENSITIVITY_SET_S` 24 条 | `958638ca0f3dc51323db710a69f4eacacc2fcff10186a99b07aecc47821d838b` | #538 旧名单。本票未改。不得把它当成新正式 S |
| `patch_events_verify.py` | `58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918` | 与 SENS-DIAG-1A 所记相同 |
| `patch_events_sensitivity.py` | `6a94996bb076cc21a61bcc8562210867cdb022c85a01ac9f89a02c206f7a0ef1` | 本票未改该文件 |

开跑纪律（约束 #542，本票自己不跑）：

1. 真跑程序先打印本冻结 sha256，与本页一致，才允许加载权重。
2. 打印之前不得调用 `predict_xnli_probs`。
3. 打分结束后再哈希一次。不一致则整跑作废，不写过线。
4. 冻结后禁止边跑边加槽、换坏槽、改金标、改 τ、改 ρ、改 `ok` 公式。
5. 发现协议洞：停跑，重新锁 S，重新开链。禁止补洞凑绿。
6. 报告不得写 `activation_prerequisite_met=是`。
7. DIAG 分不得代替正式 S2。#538 的失败结论句不得改写成过线。

## 8. 仪器与 ρ（只回显，不改）

| 项 | 锁 | 本票 |
|---|---|---|
| model_id | `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | 未改，未加载 |
| tau | `0.5`（`ENTAILMENT_TAU`） | 未改 |
| ok | argmax 为 entailment 且 P(entailment) ≥ τ | 未改 |
| S2 ρ | 坏 → ok=False ≥ 0.90 | 未改，未计算 |
| S3 ρ | 正确 → ok=True ≥ 0.70 | 未改，未计算 |
| premise / hypothesis | evidence_text / after_text | 未改 |

这些数字来自当前源码常量 `BAD_OK_FALSE_MIN=0.90`、`CORRECT_OK_TRUE_MIN=0.70`、`ENTAILMENT_TAU=0.5`，不是新标定。jsonl header 里的 JSON 数字 `0.9` / `0.7` 是同一浮点值。

## 9. 禁区

- 不跑 LIVE-2，不写 `sensitivity_passed`。
- 不合 #543，不在 #543 的分支上继续改。
- 不改 ADR-0040，不开 PE-Y-05，不复活 #507，不开 GATE 真探针，不估计 δ。
- 无 secret_names。

## 10. 与过早 PR #543 的关系

#543 在 grill 锁与本票之前已经写过一版名单并打了分。G20=B：该 PR 是过早产物，本链不合并、不续写。

#543 名单哈希 `baf33f5b9e0ea801c736d67385a94546fb6bd24af1ada0e4f27d1b9f5da1fa8c` 不是本冻结哈希。字段集合不同，本页也没有把它的分数带进来。#542 的 Depends-on 只认 `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`。

本票不关闭 #543。关闭或作废仍按 G20=B 另处置。

## 11. 冻结索引

| index | sample_id | stratum | op | gold | kind | overlap | role | must_carry | replaces |
|---:|---|---|---:|---|---|---:|---|---|---|
| 0 | `S-数值-op0` | 数值 | 0 | 坏 | construct_bad | 0.857143 | after_vs_evidence | false |  |
| 1 | `S-数值-op1` | 数值 | 1 | 坏 | construct_bad | 0.800000 | after_vs_evidence | false |  |
| 2 | `S-数值-op2` | 数值 | 2 | 坏 | construct_bad | 0.833333 | after_vs_evidence | false |  |
| 3 | `S-数值-op3` | 数值 | 3 | 坏 | construct_bad | 0.800000 | after_vs_evidence | false |  |
| 4 | `S-日期-op0` | 日期 | 0 | 坏 | construct_bad | 0.900000 | after_vs_evidence | false |  |
| 5 | `S-日期-op1` | 日期 | 1 | 坏 | construct_bad | 0.888889 | after_vs_evidence | false |  |
| 6 | `DIAG-HANS-002` | 日期 | 2 | 坏 | construct_bad | 1.000000 | after_vs_evidence | false | S-日期-op2 |
| 7 | `DIAG-HANS-003` | 日期 | 3 | 坏 | construct_bad | 1.000000 | after_vs_evidence | false | S-日期-op3 |
| 8 | `S-条款-op0` | 条款替换 | 0 | 坏 | construct_bad | 0.857143 | after_vs_evidence | false |  |
| 9 | `S-条款-op1` | 条款替换 | 1 | 坏 | construct_bad | 0.777778 | after_vs_evidence | false |  |
| 10 | `DIAG-HANS-004` | 条款替换 | 2 | 坏 | construct_bad | 0.833333 | after_vs_evidence | false | S-条款-op2 |
| 11 | `S-条款-op3` | 条款替换 | 3 | 坏 | construct_bad | 0.333333 | after_vs_evidence | false |  |
| 12 | `DIAG-HANS-006` | 删除 | 0 | 坏 | construct_bad | 1.000000 | after_vs_evidence | false | S-删除-op0 |
| 13 | `DIAG-CHEF-03-bad` | 删除 | 1 | 坏 | construct_bad | 0.875000 | pair_after | true | S-删除-op1 |
| 14 | `S-删除-op2` | 删除 | 2 | 坏 | construct_bad |  | undefined | false |  |
| 15 | `DIAG-CHEF-04-bad` | 删除 | 3 | 坏 | construct_bad | 1.000000 | pair_after | true | S-删除-op3 |
| 16 | `S-废止-trap01` | 条款替换 |  | 坏 | abolish_trap | 0.750000 | after_vs_evidence | false |  |
| 17 | `S-废止-trap02` | 条款替换 |  | 坏 | abolish_trap | 0.666667 | after_vs_evidence | false |  |
| 18 | `S-版本-trap01` | 条款替换 |  | 坏 | version_trap | 0.625000 | after_vs_evidence | false |  |
| 19 | `S-版本-trap02` | 条款替换 |  | 坏 | version_trap | 0.545455 | after_vs_evidence | false |  |
| 20 | `S-正确-数值01` | 数值 |  | 正确 | correct | 1.000000 | after_vs_evidence | false |  |
| 21 | `S-正确-日期01` | 日期 |  | 正确 | correct | 0.900000 | after_vs_evidence | false |  |
| 22 | `S-正确-条款01` | 条款替换 |  | 正确 | correct | 0.888889 | after_vs_evidence | false |  |
| 23 | `S-正确-删除01` | 删除 |  | 正确 | correct | 1.000000 | after_vs_evidence | false |  |
| 24 | `DIAG-CHEF-03-good` | 删除 |  | 正确 | correct | 0.875000 | pair_after | false |  |
| 25 | `DIAG-CHEF-04-good` | 删除 |  | 正确 | correct | 1.000000 | pair_after | false |  |

## 12. Acceptance 如何被本页覆盖

| #544 Acceptance | 何处 |
|---|---|
| 算子 / 两库抽取规则书面锁，可复核 | §1、§2；jsonl 每条有 stratum 与 operator |
| 坏槽：高重叠但金标=坏，生产同族，非极端刷分句 | §3、§5；HANS-007/008 不入集 |
| 金标二元坏/好；删除类记 `nli_construct_ok` | §4 |
| Ronin 起草；用户抽检 ≥30% 计划已写 | §4。计划已写，抽检未做 |
| 冻结清单在 `docs/evidence/patch-events/`，文件名含 SENS-S-FREEZE 与 formal-S | 本页与 `SENS-S-FREEZE-formal-S.jsonl` |
| 记 sha256；冻结后禁止边跑边加槽 | §7。sha256=`e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19` |
| 名单含 `DIAG-CHEF-03-bad` 与 `DIAG-CHEF-04-bad` | jsonl `must_carry=true` |
| CHEF：token_overlap≥0.8 且好侧 ok=True，否则对无效 | §6。重叠 0.875000 与 1.000000 |
| CHEF-03 好侧年限未扰仍绿 | §6.1 |
| 不跑 LIVE-2；不改 τ/ρ；不激活；不合 #543；无 secret_names | §0、§8、§9、§10 |
