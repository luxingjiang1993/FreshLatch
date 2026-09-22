# 预登记:主链抗假绿(另条证明跑前锁定)

> **锁定语**:本文写于跑任何「主链抗假绿」有效证明之前。事后修改本文的通过线、作废线、decoding、主张集或仅表明句模板,视为该次运行无效(ADR-0007;HARKing)。
> **层级**:产品侧工程 / 冒烟证明。通过只表示「这一次主链跑出 must_stale→fresh 合计为 0」。不报方差,不升格为一期测量闭合,不宣布判定层已愈,不宣布产品已愈假绿,不替代 K3 / K6-4。
> **决议**:[决议:主链抗假绿评测构念与通过线](https://github.com/luxingjiang1993/FreshLatch/issues/82);修窗策略见 [决议:主链压不住假绿时的修复策略族](https://github.com/luxingjiang1993/FreshLatch/issues/83)。评估见 `docs/research/主链抗假绿评测构念与通过线设计评估.md`、`docs/research/主链压不住假绿时的修复策略族设计评估.md`。
> **仪器 C**:`docs/evidence/w4/false-green-control-c-prereg.md` 与 `CONTROL_PROMPT_C` **冻结只读**;C 对照成立句保留。不得用 C 的 4/4 校准本文任何数字,不得改写 C / 旧仪器 / K3 / K6-4 已锁仅表明句。

## 构念

主链抗假绿测的是:在真实复验主链(`Lead` + 工具 + 规则闸,入口 `run_gold`)下,金标 `must_stale` 主张**不得**被判 `fresh`(产品侧假绿 = 不该绿却绿)。

与假绿仪器 C **异构另条**:C 证明无工具基线可诱导 must_stale→`alive`;本条证明有主链时压得住假绿。对照成立 ≠ 产品已愈——本条是另条证明,不是 C 附录。

既有 K3 / K6-4 must_stale 读数**不得**自动升格为本证明。

## 主张集(跑前写死)

与 `data/eval/gold.json` 的 `must_stale` 同构:**c1、c2、c3、c7**(四条,不增不减)。不得把 must_fresh / must_unknown / 干扰项并进本通过线。

## 通过线(证明成立)

- 预算内(见 decoding)对主张集的每一次主链终态中,`must_stale→fresh` **合计 = 0** 即过。
- 格数:n=3 × 四条 = 至多 12 格;任一格 `fresh` = **未过**(可引用),不得改本通过线;不作废。
- `stale` / `unknown` 细账进报告,不进通过线。

## 作废线(读数不可解释)

与「未过」正交。触任一条 → 整刀作废,落 `docs/evidence/w4/main-chain-anti-false-green-<date>-void.md`:

1. 缺原料 / 报告不完整 / 未按本文 decoding 与入口执行;
2. 跑后改通过线 / 作废线 / decoding / 主张集 / 仅表明句模板;
3. 动了 C 预登记 / `CONTROL_PROMPT_C` / 旧 `CONTROL_PROMPT` 路径或 C/旧仪器读数叙事;
4. 改了 `gold.json` 判定语义或名单,或放宽任何已锁 K 通过线(含 K3 / K6-4);
5. must_stale 任一条机判无法落入 `fresh`/`stale`/`unknown`(或报告层等价 `unparseable`)。

`fresh>0` 只是未过,不作废。不得见格子后放宽「允许 1 格 fresh」。

## decoding(逐运行入档,本处先写死默认)

| 项 | 锁定值 |
|---|---|
| 模型 | `qwen-flash`(`DecodingParams` 默认;活托管端点,跨会话复现只能近似) |
| temperature | `0.0` |
| seed | `None`(temp=0 时 seed 无采样意义;禁止 temp=0 多 seed 假信心) |
| 每条主张重复 | n=3(`--runs 3`) |
| 入口 | `python -m freshlatch.eval run --gold data/eval/gold.json --runs 3 --temperature 0.0`(勿传 seed,或显式 seed 缺省为 None) |
| 评测对象 | 端到端真主链(`run_gold`);**禁止**用 `control` / `control-c` 冒充本证明 |

诚实框定:temp=0 + n=3 = 冒烟,不估运行间噪声,不报方差。

## 报告落档契约

有效跑(或作废备忘)报告**必须**可核对:

- 显式声明本预登记路径或等价 `instrument` 标记(建议 raw 注记 `main_chain_anti_false_green`);
- `decoding` 全字段(模型 / temperature / seed / runs);
- must_stale 四条在各 run 的终态;`must_stale→fresh` 合计;
- `recorded_at`;原料 JSON 路径。

## 成败「仅表明」句(落 ACCEPTANCE 归证明跑票)

**成功句**(fresh 合计 = 0 且不作废)——逐字:

> 主链抗假绿（qwen-flash，temp=0，seed=None，n=3，主链抗假绿预登记；入口 run_gold）仅表明 must_stale（c1/c2/c3/c7）判 fresh 合计为 0；以假绿仪器 C 对照成立为假绿可诱导前提；不是一期评测闭合，不是判定层已愈，不是产品已愈假绿的统计证明，也不改写 C / 旧仪器 / K3 / K6-4 已锁仅表明句。

**失败句**(fresh 合计 = {k}>0 且不作废)——逐字;`{k}` / `{逐条摘要}` 跑时填:

> 主链抗假绿（qwen-flash，temp=0，seed=None，n=3，主链抗假绿预登记；入口 run_gold）仅表明 must_stale 判 fresh 合计为 {k}>0（{逐条摘要}）→ 未过且不作废；不得放宽 fresh=0 通过线；失败处置走修窗（策略票）；不改写 C 对照成立句，也不写成判定层已愈或一期闭合。

## 未过 → 修窗(策略已锁;本预登记只钉入口)

有效跑未过 → **必须**按 [决议:主链压不住假绿时的修复策略族](https://github.com/luxingjiang1993/FreshLatch/issues/83) 开修窗:闸/工具主杠杆;弃人格唯一主修;改代码前根因备忘;禁见格子改本通过线。本预登记**不授权**预修猜改。

## 有效跑配额

- 本图另条证明:**首跑一刀有效**(成功或失败未过均计);作废不消耗名额,修到可跑后允许且仅允许再开一刀有效跑。
- 未过修窗后的同线复验:仍用本文 decoding / 通过线,另计为修窗验收跑(策略票形态),不得借机放宽本文。
- 禁止多刀有效跑钓鱼至 fresh=0。

## 记录但不进通过线 / 不作废线

| 格子 | 备注 |
|---|---|
| must_stale→stale / unknown 条数 | 细账;unknown≠假绿 |
| must_fresh / must_unknown / 干扰项 | 同包 `run_gold` 可能跑到;明显回退记报告,不并联本通过线 |
| K3 / K6-4 已有 must_stale 读数 | 不得升格为本证明 |

## 代码契约(最小门闩)

| 件 | 规格 |
|---|---|
| 入口 | 现成 `run_gold` / `python -m freshlatch.eval run`;**不**旁增替身 runner |
| 参数 | `--runs 3 --temperature 0.0`;模型默认 `qwen-flash`;seed 缺省 `None` |
| C / 旧 control | **不改不删** `CONTROL_PROMPT` / `CONTROL_PROMPT_C` / C 预登记 |
| 红线单测 | `tests/unit/test_main_chain_anti_false_green_prereg.py` 盯本文锁定字面 |

## 本预登记明确不授权的事

- 不改 `gold.json`、不改 C/旧仪器、不放宽本通过线或已锁 K 线。
- 不把本证明写成一期评测闭合、判定层已愈、产品已愈假绿、或 W5–W8 全量验收通过。
- 不用 C 的 4/4 或旧仪器 0/4 校准本文。
- 本预登记文件本身**不跑** LLM;首跑归 [落盘:主链抗假绿另条证明跑与ACCEPTANCE](https://github.com/luxingjiang1993/FreshLatch/issues/85)。
