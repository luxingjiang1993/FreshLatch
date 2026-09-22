# 预登记:假绿仪器 C(首跑前锁定)

> **锁定语**:本文写于旁增 `CONTROL_PROMPT_C`、跑任何 C 对照之前。事后修改本文的通过线、作废线、decoding、prompt 正文或私有多锚表,视为该次 C 运行无效(ADR-0007;HARKing)。
> **层级**:demo / 仪器层冒烟。通过只表示「这一次 C 跑出了 must_stale 4/4 假绿」。不报方差,不升格为一期测量闭合,不宣布判定层已愈,不替代 K3。
> **决议**:[决议:C预登记锁与成败可引用句](https://github.com/luxingjiang1993/FreshLatch/issues/77);构念包见 [决议:C构念与旋钮包](https://github.com/luxingjiang1993/FreshLatch/issues/76)。评估见 `docs/research/C预登记锁与成败可引用句设计评估.md`。
> **旧仪器**:`docs/evidence/w4/false-green-control-prereg.md` 与旧 `CONTROL_PROMPT` **冻结只读**;旧 #70「对照不成立」canonical 句保留,不得被 C 读数改写/删除。不得用旧 0/4 校准本文任何数字。

## 构念

假绿对照测的是:同模型、无工具、上下文里只有 T0 摘录时,被问「该主张现在是否仍然成立」,已死主张应被判 `alive`(假绿);本产品必须红。

仪器 C 相对旧预登记仪器的差分:**C 私有多锚**(每条送模主张同 doc `p1`+`p2`+`p3`) + **反默认-unknown 旁句**。时间框字面(「数周前」+「现在是否仍然成立」)保留。仍称假绿对照;失败 ≠ 产品无假绿。

测的不是 T0 阅读理解(「仅根据材料,主张是否成立」)。不得把后一种问法的格子,写成词表里的假绿对照。

## 锁定 prompt(`CONTROL_PROMPT_C`;改代码时必须逐字拷贝)

`src/freshlatch/eval/control.py` 旁增常量 `CONTROL_PROMPT_C`(旧 `CONTROL_PROMPT` **不改不删**)。正文在 format 占位与 JSON 花括号转义后须与下列一致:

```
你是市场研判助手。以下是一条数周前签发的研判主张,以及签发时所依据的文档摘录:

主张: {statement}
签发时所依据的文档摘录: {t0_excerpt}

若缺少签发之后的更新材料,不要因此默认 unknown。
请判断:该主张现在是否仍然成立?
只输出 JSON,格式:{{"verdict": "alive"|"dead"|"unknown"}}。
```

禁出现:「仅根据材料是否成立」及同构蕴涵问法;禁删「现在是否仍然成立」;禁删「数周前签发」。不得出现 T1 / 快照 / 复验 / 金标 / must_stale / gold。

红线单测:旧测继续盯 `CONTROL_PROMPT`;C 另测盯 `CONTROL_PROMPT_C`(`tests/unit/test_control.py`)。

## 通过线(对照成立)

- 主张名单:`gold.json` 的 `must_stale` = **c1、c2、c3、c7**(四条,不增不减)。
- 成立条件:四条基线判定均为 `alive`。
- 未满 4/4:对照**不成立**(可引用),不得改本通过线;不作废。
- `control_pass` 语义与此同构;不得把 must_fresh、must_unknown、干扰项 c13/c14 并进通过线。

## 作废线(读数不可解释)

与「对照不成立」正交。触任一条 → 整刀作废,落 `docs/evidence/w4/false-green-control-c-<date>-void.md`:

1. prompt 再次把「现在/仍然」与「不要使用签发之后 / 只根据材料」绑回同一用户消息(矛盾句回潮);
2. 红线泄漏(T1 / 快照 / 复验 / 金标 / must_stale / gold);
3. must_stale 任一条机判 `unparseable`;
4. 跑后改通过线 / 作废线 / decoding / prompt 正文 / 多锚表;
5. **C 特有**:跑时偏离下方已锁多锚表;使用旧 `CONTROL_PROMPT` 冒充 C;改共享 `t0_docket.json`;已锁 evidence id 在 store 中缺 chunk。

`unknown`/`dead` 再多,只是对照不成立,不作废。不得用旧仪器 0/4 设定本条。

## decoding(逐运行入档,本处先写死默认)

| 项 | 锁定值 |
|---|---|
| 模型 | `qwen-flash`(与 Lead 同档;活托管端点,跨会话复现只能近似) |
| temperature | `0.0` |
| seed | `None`(temp=0 时 seed 无采样意义;禁止 temp=0 多 seed 假信心) |
| 每条主张重复 | n=1 |
| 输出 | JSON mode `{"verdict": "alive"\|"dead"\|"unknown"}` |

禁止把本仪器改写成 K3。

## C 私有多锚表(跑前写死;共享 docket 只读)

政策:本跑**所有送模主张**(金标 12 + 干扰项 c13/c14)**同政策**;每条同 doc 的 `p1`+`p2`+`p3` 源序,以 `\n\n` 拼为 `{t0_excerpt}`。共享 docket 的既有单锚 id **不修改**。

| claim_id | C 私有 `t0_evidence_ids`(序) |
|---|---|
| c1 | `t0-competitor-notes#p1`, `t0-competitor-notes#p2`, `t0-competitor-notes#p3` |
| c2 | `t0-regulatory-memo#p1`, `t0-regulatory-memo#p2`, `t0-regulatory-memo#p3` |
| c3 | `t0-channel-interviews#p1`, `t0-channel-interviews#p2`, `t0-channel-interviews#p3` |
| c4 | `t0-market-census#p1`, `t0-market-census#p2`, `t0-market-census#p3` |
| c5 | `t0-cost-model#p1`, `t0-cost-model#p2`, `t0-cost-model#p3` |
| c6 | `t0-competitor-news#p1`, `t0-competitor-news#p2`, `t0-competitor-news#p3` |
| c7 | `t0-trade-press#p1`, `t0-trade-press#p2`, `t0-trade-press#p3` |
| c8 | `t0-tech-ecosystem#p1`, `t0-tech-ecosystem#p2`, `t0-tech-ecosystem#p3` |
| c9 | `t0-messaging-survey#p1`, `t0-messaging-survey#p2`, `t0-messaging-survey#p3` |
| c10 | `t0-talent-salary#p1`, `t0-talent-salary#p2`, `t0-talent-salary#p3` |
| c11 | `t0-payment-landscape#p1`, `t0-payment-landscape#p2`, `t0-payment-landscape#p3` |
| c12 | `t0-infra-reliability#p1`, `t0-infra-reliability#p2`, `t0-infra-reliability#p3` |
| c13 | `t0-competitor-economics#p1`, `t0-competitor-economics#p2`, `t0-competitor-economics#p3` |
| c14 | `t0-channel-coverage#p1`, `t0-channel-coverage#p2`, `t0-channel-coverage#p3` |

## excerpt 落档契约

有效跑(或作废备忘)报告**必须**含:

- `instrument`: `false_green_control_c`;
- `prompt_id`: `CONTROL_PROMPT_C`;
- 每条 claim:`t0_evidence_ids_sent`(上表逐字)、`t0_excerpt`(实际送模全文)、`t0_excerpt_char_len`;
- `decoding` 全字段;`recorded_at`;
- 任一条已锁 id 缺 chunk → **不得**静默跳过;整刀走作废线。

## 成败「仅表明」句(与旧句并存;落 ACCEPTANCE 归首跑票)

**旧仪器 canonical(#70)保留不动**:

> 新假绿对照（qwen-flash，temp=0.0，seed=None，n=1，预登记仪器）仅表明 must_stale 假绿 0/4（c1 unknown / c2 unknown / c3 unknown / c7 unknown）→ 对照不成立且不作废；不是仪器已证明产品无假绿，也不是可放宽 4/4 alive，也不是一期评测闭合。

**C 成功句**(4/4 alive 且不作废):

> 假绿仪器 C（qwen-flash，temp=0.0，seed=None，n=1，C 预登记；私有多锚 p1+p2+p3 + 反默认-unknown 旁句）仅表明 must_stale 假绿 4/4（c1/c2/c3/c7 全 alive）→ 对照成立；不是一期评测闭合，不是判定层已愈，不是可改 `gold.json` / 通过线，也不是产品已愈假绿（对照成立只说明无工具基线打出假绿）；亦不改写旧预登记仪器对照不成立句。

**C 失败句模板**(未满 4/4 且不作废):

> 假绿仪器 C（qwen-flash，temp=0.0，seed=None，n=1，C 预登记；私有多锚 p1+p2+p3 + 反默认-unknown 旁句）仅表明 must_stale 假绿 {k}/4（{逐条:如 c1 unknown / c2 alive / …}）→ 对照不成立且不作废；不是仪器已证明产品无假绿，也不是可放宽 4/4 alive，也不是一期评测闭合；亦不改写旧预登记仪器对照不成立句。

## 作废补跑与有效跑配额

- 作废不消耗有效跑名额;修到可跑后**允许且仅允许**再开一刀有效跑。
- 该有效跑再废 → 关图;canonical 回退开跑前态(旧 #70 句);另开努力。
- 有效读数(C 成功或 C 失败不成立)一旦产出 → 本图有效跑配额用尽,不得再抽。

## 记录但不进通过线 / 不作废线

| 格子 | 备注 |
|---|---|
| must_fresh(c4/c5/c6/c8) | 只读 T0 时倾向 `alive`;偏离只记录 |
| must_unknown 判 `alive` | 盲判绿信号;不要求、不禁止 |
| c13/c14(`must_fresh_distractor`) | 期望基线 `alive`,附表备查(#21),不进 12 条判分矩阵 |

## 并行代码契约

| 件 | 规格 |
|---|---|
| 常量 | 旁增 `CONTROL_PROMPT_C`;不改/不删 `CONTROL_PROMPT` |
| 运行入口 | `python -m freshlatch.eval control-c`(或等价);默认 `control` 仍走旧仪器 |
| 拼装 | 按私有多锚表取 chunk;共享 docket 只读 |
| 验收脚本 | `run_w4_acceptance.py` 等不得默默改成 C |

## 本预登记明确不授权的事

- 不改 `gold.json` 判定语义、不改共享 `t0_docket.json`、不替换旧 `CONTROL_PROMPT` 路径。
- 不把 C 通过说成一期评测闭合、判定层已愈、产品已愈假绿、或 W5–W8 全量验收通过。
- 不用旧仪器 0/4 校准通过线;不放宽「未满 4/4 也算对照成立」。
- 不在本文落盘前跑 C 对照(本句在落盘当下解除「旁增 prompt」门闩;跑数仍须用锁定 prompt + 本文判据 + 多锚表)。
- 本预登记文件本身**不跑** LLM;首跑归 [落盘:C仪器首跑与ACCEPTANCE_SUMMARY更新](https://github.com/luxingjiang1993/FreshLatch/issues/79)。
