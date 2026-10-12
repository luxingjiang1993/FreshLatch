# SENS-LIVE-2 协议锁（跑前）

日期：2026-10-12（UTC+8）
票：PE-Y-SENS-LIVE-2 · GitHub #542
状态：名单已冻结，尚未打分。本页不写分数，不写过线。

冻结名单 sha256：`baf33f5b9e0ea801c736d67385a94546fb6bd24af1ada0e4f27d1b9f5da1fa8c`

清单：`docs/evidence/patch-events/SENS-LIVE-2-set-S.jsonl`
代码：`SENSITIVITY_SET_S` 与 `FROZEN_SENSITIVITY_SET_SHA256`
哈希对象：26 条规范记录，字段 `sample_id, stratum, operator, gold, kind, after_text, evidence_text, note, heuristic, subcase, pair_id, token_overlap, wice_note, nli_construct_ok`。JSON `ensure_ascii=false`、`sort_keys=true`、分隔符 `(',', ':')` 的 UTF-8 sha256。哈希不含本常量本身，也不含协议头。

`patch_events_verify.py` sha256（跑前）：`58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918`
与 SENS-DIAG-1A 所记相同，故 `ENTAILMENT_TAU = 0.5` 字节未改。

## 1. 仪器（不改）

| 项 | 锁 |
|---|---|
| model_id | `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` |
| ok | argmax 为 entailment 且 P(entailment) ≥ τ |
| τ | 0.5 |
| S2 ρ | 坏 → ok=False ≥ 0.90 |
| S3 ρ | 正确 → ok=True ≥ 0.70 |
| premise / hypothesis | evidence_text / after_text |

禁止放宽 τ，禁止降低 ρ，禁止改 ADR-0040 型号或 ok 公式。
无 secret_names，无新开云密钥。权重只用仓内已能加载的公开模型缓存。

## 2. 算子

沿用构造器四层，每层 operator 0..3 至少一条 construct_bad：

| 层 | op0 | op1 | op2 | op3 |
|---|---|---|---|---|
| 数值 | 数值小幅改动 | 数量级 | 错配证据里的另一个数 | 单位错配 |
| 日期 | 年份 ±1 | 月份平移 | 日期角色对调（施行日取公布日） | 主体绑错施行日 |
| 条款替换 | 应当 / 不得翻转 | 主体错配 | 同句架错挂办法名 | 证据块不含该义务 |
| 删除 | 已废止限定仍称有效 | 年限 5 年改为 3 年 | 空证据硬拒 | 删掉「大约」 |

废止陷阱、版本陷阱各两条，文本与 #538 正式 S 相同，不新写极端废止句。
两库只提供抽取纪律，不提供过线分数：

- legal-hallucination-bench：坏改用二元金标；废止法陷阱保持有限条，不扩成刷分集。
- verified-chinese-law-kb：版本轴上「已废止仍称有效」才是坏槽。证据里被肯定的子串不得再标成坏。

## 3. 坏槽准入

1. 与生产坏改同族：改数字、改日期角色或主体、错挂办法或主体、删或硬化义务。不写与证据无关的极端句。
2. 金标=坏时，主张不得是证据里被肯定的子串。#538 里 `S-日期-op2`、`S-删除-op0` 因此退役。
3. 高重叠：新换上的坏槽，after 对 evidence 的 token_overlap 在跑前均 ≥ 0.833333。CHEF 对另锁两侧 after ≥ 0.8。
4. 下列原槽重叠低于 0.8，跑前已经看见，保留，不按分数改句：
   - `S-条款-op1` 0.777778，生产主体错配。
   - `S-条款-op3` 0.333333，证据块不含该义务，低重叠是算子本身。
   - `S-删除-op2` 空证据，重叠无定义，硬拒对照。
   - 四条废止/版本陷阱 0.545455–0.750000，显式矛盾，不是本轮新写的高重叠坏槽。
5. 坏槽条数锁死 20。与 #538 同口径。禁止再加易拒句把 S2 稀释过去。

词重叠式（与 SENS-DIAG-1A 相同，jieba 0.42.1）：

```text
token_overlap = |set(jieba 内容词(a)) ∩ set(jieba 内容词(b))| / min(|set(a)|, |set(b)|)
```

内容词去掉空白与纯标点。CHEF 行的该列是两侧 after。其他行是 after 对 evidence。

## 4. 相对 #538 的替换（跑前写死）

退役、不再出现在正式 S：

| 退役 id | 原因 |
|---|---|
| S-日期-op2 | 施行日是证据子串。DIAG 标 nli_construct_ok=no |
| S-日期-op3 | 「本办法」未在证据中出现 |
| S-条款-op2 | 表面重叠 0.571429，低于 0.8 |
| S-删除-op0 | 主张是被肯定例外的子串。DIAG 标 nli_construct_ok=no |
| S-删除-op1 | 弱主张被强证据蕴含。同族改由 5 年→3 年承担 |
| S-删除-op3 | 同族删「大约」改由 DIAG-CHEF-04-bad 承担，避免两条近重复 |

换上：

| 新 id | 槽 | 文本要点 |
|---|---|---|
| DIAG-HANS-002 | 日期 op2 | 施行日取公布日 |
| DIAG-HANS-003 | 日期 op3 | 旧办法错取新办法施行日 |
| DIAG-HANS-004 | 条款 op2 | 同句架，标准合同办法改为认证办法 |
| DIAG-HANS-006 | 删除 op0 | 已废止的年限限定被说成仍然有效 |
| DIAG-CHEF-03-bad | 删除 op1 | Must-carry。不少于 5 年改为不少于 3 年 |
| DIAG-CHEF-04-bad | 删除 op3 | Must-carry。删掉「大约」 |

刻意不入集：

| id | 原因 |
|---|---|
| DIAG-HANS-001 | 与 HANS-002 同一证据的另一方向。留一条即可，避免同一证据计两次 |
| DIAG-HANS-005 | 条款 op2 已由 HANS-004 承担。不再加第二条易拒句 |
| DIAG-HANS-007 | DIAG 里插入相反例外已变红。不放在 CHEF-03 旁边稀释 must-carry |
| DIAG-HANS-008 | 「处理者不应当保存记录」是极端否定。同族由删「大约」承担 |

入集时不用模型分数做筛。DIAG 只用来区分「金标在 NLI 下不成立的旧槽」和「高重叠义务冲突」。DIAG 的 P_entail 不进入本页 S2。

## 5. CHEF 对

只入两对，文本与 DIAG 夹具相同：

| pair_id | 好侧 | 坏侧 | 跑前 token_overlap |
|---|---|---|---|
| DIAG-CHEF-03 | DIAG-CHEF-03-good | DIAG-CHEF-03-bad | 0.875000 |
| DIAG-CHEF-04 | DIAG-CHEF-04-good | DIAG-CHEF-04-bad | 1.000000 |

有效对：token_overlap ≥ 0.8 且好侧 ok=True。否则对无效。
好侧 ok 只能跑后知道。无效对不从 S2 分母剔除。S2 分母是全部 gold=坏 的 20 条。

## 6. 删除类 meta-eval（跑前）

| id | nli_construct_ok | wice_note | 判断 |
|---|---|---|---|
| DIAG-HANS-006 | yes | not_supported | 已废止限定仍称有效，主张不被蕴含 |
| DIAG-CHEF-03-bad | yes | not_supported | 3 年不是证据里的 5 年 |
| DIAG-CHEF-04-bad | yes | not_supported | 删「大约」是义务硬化。产品协议定为坏。沿用 DIAG 已写的 yes，不改成 partial |
| S-删除-op2 | yes | not_supported | 空证据 |

#538 原文 S-删除-op3 曾标 partial。正式条不用那条文本。不把 partial 事后改写成 yes 或 no 来解释 CHEF-04。
若 CHEF-03 或 CHEF-04 跑后仍 ok=True，记为仪器对数字替换或删弱化词放行。不改金标，不改 τ/ρ，不把该条移出分母。

## 7. 开跑纪律

1. 真跑程序先打印 `FROZEN_S_SHA256`，与本页哈希一致，才允许加载权重。
2. 打印之前不得调用 `predict_xnli_probs`。
3. 打分结束后再哈希一次。不一致则整跑作废，不写过线。
4. 看见分数之后禁止改名单、改 τ、改 ρ、改 ok 公式。
5. 报告不得写 `activation_prerequisite_met=是`。
6. 不得开 PE-Y-05、GATE 真探针、n=400，不得复活 #507。
7. DIAG 分不得代替本页 S2。#538 的「S2 实测 0.7000、未通过」不得改写成过线。
