# Batch 3（γ）ACCEPTANCE

> 判据单一真相：`docs/research/C3-判定拉齐预登记卡.md` + ADR-0018。
> 分条措辞：`docs/research/γ-与假绿仪器分条措辞设计评估.md` §4.1。
> 三节并列。禁止合成「抗假绿总通过」。
> 本文件不改判据，不改 `data/eval/gold.json`。

## 1. 假绿仪器

预锁可引用句：

> 以已关假绿相关图之仅表明句 / 诚实边界为准；本批不重审对照是否成立。

旧图句子停在本节，只作指针，本批不重审、不改写。出处：`reports/w5w8_acceptance/ACCEPTANCE_SUMMARY.md`。

> 新假绿对照（qwen-flash，temp=0.0，seed=None，n=1，预登记仪器）仅表明 must_stale 假绿 0/4（c1 unknown / c2 unknown / c3 unknown / c7 unknown）→ 对照不成立且不作废；不是仪器已证明产品无假绿，也不是可放宽 4/4 alive，也不是一期评测闭合。

> 假绿仪器 C（qwen-flash，temp=0.0，seed=None，n=1，C 预登记；私有多锚 p1+p2+p3 + 反默认-unknown 旁句）仅表明 must_stale 假绿 4/4（c1/c2/c3/c7 全 alive）→ 对照成立；不是一期评测闭合，不是判定层已愈，不是可改 `gold.json` / 通过线，也不是产品已愈假绿（对照成立只说明无工具基线打出假绿）；亦不改写旧预登记仪器对照不成立句。

> 主链抗假绿（qwen-flash，temp=0，seed=None，n=3，主链抗假绿预登记；入口 run_gold）仅表明 must_stale（c1/c2/c3/c7）判 fresh 合计为 0；以假绿仪器 C 对照成立为假绿可诱导前提；不是一期评测闭合，不是判定层已愈，不是产品已愈假绿的统计证明，也不改写 C / 旧仪器 / K3 / K6-4 已锁仅表明句。

## 2. γ 判定拉齐

预锁可引用句：

> 以 `docs/research/C3-判定拉齐预登记卡.md` 之 γ-INV/SMOKE + 禁改 gold（ADR-0018）为准；γ 通过 ≠ 假绿对照成立。

| ID | 层 | 落点 | 本批读法 |
|---|---|---|---|
| γ-INV-1 | invariant | `tests/unit/test_gamma_inv_alignment.py`（#118，`02b40bd`） | 双判一致仍为 fresh 唯一绿路；确定性单测，不是统计证明 |
| γ-INV-2 | invariant | 同上 | 维度跨检 / 预检异议路径；维度不符不得 stale 绿放 |
| γ-INV-3 | invariant | 本节审计 | 验收相关 diff 无偷偷改 `must_*` |
| γ-SMOKE-1/2 | smoke | `docs/evidence/batch3/gamma-smoke-119.md` | 仅表明；n=1 不报方差 |

γ-SMOKE 仅表明句（#119，不改写）：

> γ-SMOKE-1（qwen-flash，temp=0.0，seed=None，n=1，日期 2026-09-23，commit db85e679f95839af5295e69617283e71cfaaf265，入口既有 run_gold，层=smoke）仅表明加固后 must_stale（c1/c2/c3/c7）判 fresh 合计为 0。四条终态都是 stale，Lead stale 且 Auditor stale，无异议。不是统计证明，不是产品已验证，不是假绿已根治，γ 通过也不等于假绿对照成立。

这句停在 γ 拉齐条。它不改写第 1 节的假绿仪器句子，也不等于假绿对照成立。

### γ-INV-3 禁改 gold 审计

验收窗：`f8274ac`（#118 之前）至 `c4db1ae`（含 #118 `02b40bd`、#119 `e0657ba`）。

- `git rev-parse f8274ac:data/eval/gold.json` 与 `c4db1ae:data/eval/gold.json` 同为 `c7a14683de82bb795fd67bbb505bd6f7128b7c2a`
- `git diff f8274ac..c4db1ae -- data/eval/gold.json` 为空
- `must_stale` / `must_fresh` / `must_unknown` / `must_quarantine` 无改写
- 本 ACCEPTANCE 提交不修改 `data/eval/gold.json`

### 非本批交付

主张 c3-form 锚点（旧 #32 规格锚定与主张误伤探针）不是本批 γ。不得把下列文件当成 Batch 3 交付或通过线：

- `docs/implementation/c3-fix-spec-anchor-and-probe.md`
- `docs/verification/c3-fix-acceptance-report.md`
- `docs/task-completion/task-33-c3-fix-behavioral-acceptance.md`

## 3. 消融 / 多 seed

预锁可引用句：

> 规格已锁（`docs/research/γ-消融表与多seed规格时序设计评估.md`）、实跑未做；未跑 ≠ 已证明。

同文件 §4.2 预锁句：

> Batch 3：消融表与多 seed 仅锁规格（表头/记录字段/smoke 框）；实跑未做；未跑 ≠ 已证明；不得报方差/显著。实跑另开 to-spec/NEXT。禁改 gold 仍受 ADR-0018 约束。

本批不做消融实跑，不锁方差通过线。实跑结果为空。要方差声称须另预登记样本量与容差。

### 消融表头附录（锁列，不填实跑）

因子名取自 #118 加固触点。下表没有结果列，没有数值通过线。

| 消融因子 | 对照条件 | 期望方向（定性） | 记录字段 | 层 | 禁升格 |
|---|---|---|---|---|---|
| Auditor 缺席 | 相对完整加固路径 | 更易 unknown/异议，不得无依据 fresh | 模型、温度、日期、seed、n、commit | smoke | 未跑 ≠ 已证明；不得报方差 |
| 维度跨检关闭 | 相对完整加固路径 | 更易 unknown/异议，不得无依据 fresh | 模型、温度、日期、seed、n、commit | smoke | 未跑 ≠ 已证明；不得报方差 |
| 维度预检关闭 | 相对完整加固路径 | 更易 unknown/异议，不得无依据 fresh | 模型、温度、日期、seed、n、commit | smoke | 未跑 ≠ 已证明；不得报方差 |

实跑结果：空。

## 禁升格清单（可核对，不是第四条通过线）

本文件不包含下列主张：

- γ 通过 ⇒ 假绿对照成立 / 假绿已根治
- 消融规格已锁 ⇒ 消融已证明 / 测量闭合
- 主链抗假绿仅表明句 ⇒ 可升格为 γ-INV 通过线
- α-demo / γ-SMOKE ⇒ 产品已验证
