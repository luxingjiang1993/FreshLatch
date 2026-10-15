# 成立 patch 实验 · 新预注册

锁死日期：2026-10-15。票 L4-C-04。起草自 `63f91d19a9db99920dd6053f9653d1f6409eb78f`（L4-C-01 #631 之后）。

本页是**另一份** prereg。它不是 `docs/evidence/patch-events/PREREG-Y.md` 的同尺再填,也不是 `docs/evidence/quality-gate/PREREG.md` 的改写。写完假阳性判据、止损判据、manifest 字段行与 `replaces_frozen_baseline=false` 之后,不得为了让某次运行好看而改这些字段。

本期没有开跑。`run_status=unrun`。`measurement_status=unmeasured`。空着不是 0,也不是通过。

## 1. 丙防火墙

历史分层只认 `docs/evidence/patch-events/RESULT-Y.md`：结果丙。本页不改写该文件,也不改 `docs/evidence/patch-events/PREREG-Y.md` 的历史成立格。不得把历史结果丙改判为乙。

本页不是路线 Y 的另一次正式主跑。`second_formal_y=false`。同尺充数会毁掉止损意义。

B-04 夹具只作边界锚。`counts_as_establishment=false`。夹具绿不是结果乙,也不进本页成立格。

仍不得称优于 RARR·KPR。未过成立格时,综合档不得标产品 L5。即便将来成立格通过,本票仍不得单独把产品标成 L5,仍不得称优于 RARR·KPR。

本页不发明 SESOI。`numeric_line=unregistered`。`sesoi` 保持 null。主人在开跑之前、在看见任何分数之前另锁数字门槛之前,不得开跑,不得把空位写成通过。

## 2. 事前假阳性判据

下面每一条在看见测量结果之前写死。命中任何一条,该次「成立」作废。

| id | 判据 |
|---|---|
| FP-UNMEASURED | `measurement_status=unmeasured` 或 `run_status=unrun` 时,把 `counted_as_pass` 写成 true,或把 `establishment.status` 写成已成立 |
| FP-B04 | 把 B-04 夹具写入成立格,或把夹具绿记成结果乙。`counts_as_establishment=false`。夹具绿不是结果乙 |
| FP-REJUDGE | 改写历史成立格,或把历史结果丙改判为乙。不得把历史结果丙改判为乙 |
| FP-SECOND-Y | 把本页写成路线 Y 的另一次正式主跑。本页不是路线 Y 的另一次正式主跑。`second_formal_y=false` |
| FP-L5 | 成立格未通过,或仅凭本票,却标产品 L5。不得标产品 L5 |
| FP-SUPERIOR | 称优于文献对照。不得称优于 RARR·KPR |
| FP-FLOORS | 用改 floors、改 gold、改 x1、改默认生产臂来充当成立。不改 floors。不改默认臂 |
| FP-SESOI | 在本页写入一个数字门槛并把它叫做已锁的 SESOI。本页不发明 SESOI。`numeric_line=unregistered` |
| FP-NULL-AS-ZERO | 把 null 或 unmeasured 当成 0 或通过。空着不是 0 |

## 3. 事前成立与止损

成立格本期只有结构,没有数字。`establishment.status=unmeasured`。`counted_as_pass=false`。`false_accept_rate`、`point_estimate`、`ci95_low`、`ci95_high`、`n`、`k` 都是 null。无定义不是成立。

数字门槛不在本页发明。将来若主人要开跑,必须先在本页写 amendment,写明比较对象与数字线,且 amendment 的日期早于任何非空分数。本期没有这份 amendment。`numeric_line=unregistered`。

止损:

| id | 止损 |
|---|---|
| STOP-UNRUN | 主人未说「跑」则保持 `run_status=unrun`,不填分。本票的写入器拒绝任何非 null 分数 |
| STOP-FAIL | 将来若成立格未过:不得标产品 L5,不得加 n,不得改本页判据后再用同一页充数 |
| STOP-PASS | 将来若成立格已过:仍不得称优于 RARR·KPR,不得把历史结果丙改判为乙,本票仍不得单独把产品标成 L5 |
| STOP-SAME-YARDSTICK | 禁止回到 `PREREG-Y` 同尺再填一格。同尺充数会毁掉止损意义 |

`replaces_frozen_baseline=false`。

## 4. manifest 字段列表

冻结的是字段,不是一次已跑的分数。检索块记录现行生产臂的名字与常数,权重 hash 为 null。模型块的生成器与 NLI 为 null。该句是模型锁定批注之前的脚手架锁句。型号两格以文末「模型锁定批注」为准；`generator_sha256` 与 `nli_sha256` 仍是 null。源块里,历史页、质量闸预注册、冻结 per-query、金标、x1 题集与 B-04 夹具只记 sha256,`counts_as_establishment=false`。实验语料 hash 为 null。

解码:temperature、seed、model 均为 null。本期不调用 LLM。托管端点若将来开跑会漂移;本期未开跑,随机层没有可复现的样本。

manifest_fields: retrieval.mode, retrieval.embedding_model, retrieval.embedding_dim, retrieval.fusion, retrieval.rrf_k, retrieval.rerank_model, retrieval.rerank_k, retrieval.fastembed, retrieval.production_default_unchanged, retrieval.weight_sha256, model.generator_model, model.generator_sha256, model.nli_model, model.nli_sha256, model.temperature, model.seed, model.measurement_status, sources.result_y, sources.prereg_y, sources.quality_gate_prereg, sources.frozen_per_query, sources.frozen_summary, sources.gold, sources.x1_questions, sources.b04_fixtures, sources.experiment_corpus, decoding.temperature, decoding.seed, decoding.model, decoding.note, establishment.status, establishment.counted_as_pass, establishment.sesoi, establishment.numeric_line, establishment.false_accept_rate, establishment.point_estimate, establishment.ci95_low, establishment.ci95_high, establishment.n, establishment.k, firewall.historical_result_y, firewall.historical_cells_rewritten, firewall.b04_counts_as_establishment, firewall.second_formal_y, firewall.claims_rarr_kpr_superiority, firewall.product_l5, firewall.floors_unchanged, firewall.production_arm_unchanged, criteria.false_positive, criteria.stop, criteria.sesoi, criteria.numeric_line

机器页: `docs/evidence/patch-establishment/manifest.json` 与 `docs/evidence/patch-establishment/measurement.json`。

入口只重写这两份空测量:

`python -m freshlatch.eval patch-establishment --out docs/evidence/patch-establishment`

它拒绝把输出放进 `docs/evidence/neural-rerank/`、`docs/evidence/quality-gate/`、`docs/evidence/patch-events/`、`docs/evidence/temporal-trained-retrieval/`、`data/exp/x1/`、`data/eval/`。它不改本页,不写 `RESULT-Y.md`。

## 5. 不改默认臂 / 不改 floors

不改默认臂。不改 floors。

`PRODUCTION_RETRIEVAL_MODE` 仍是 `hybrid+rerank`。`temporal_trained` 不是本页的臂。运维开关不因本页增加取值。

不改 `docs/evidence/quality-gate/PREREG.md` 的 floors。质量闸各行保持 `counted_as_pass=false`,`status=TBD`。不改写注册 T1 / R1 的 `value=`。不改 `docs/evidence/neural-rerank/per-query.json`。

## 6. 结论只进本目录

实验结论只写入 `docs/evidence/patch-establishment/`。

不得写入 `docs/evidence/patch-events/RESULT-Y.md`。不得改 `docs/evidence/patch-events/PREREG-Y.md` 的历史成立格。人读的空结果页是 `docs/evidence/patch-establishment/RESULT.md`。该页在开跑前必须保持 `run_status=unrun` 与 `measurement_status=unmeasured`。

未过成立格时,综合档不得标产品 L5。过了成立格,仍不得称优于 RARR·KPR,不得把历史结果丙改判为乙。

## 7. 复现两层

确定性层: manifest 字段、防火墙布尔、锚文件 sha256 必须逐位一致。`replaces_frozen_baseline=false`。

随机层: 本期无运行。不报容差,不报方差。temperature、seed、model 都是 null。单次运行不能在本页判成立。

违例: 任一分数非 null; `counted_as_pass` 为 true; `product_l5` 为 true; 锚 sha256 与文件字节不符; 历史成立格字节变化; 出现发明的 SESOI; 把 B-04 夹具放进成立格。

## 8. Provenance

- Kind: new（本页）+ adapt（事前锁判据的 ml-prereg 习惯; HELM / RAGhelm scorecard 的 manifest 字段习惯）。
- 前沿矩阵 C-04: RARR（https://arxiv.org/abs/2210.08726）与 KPR（https://arxiv.org/abs/2609.26634）只提供边界句。本页不迁移它们的分数,不称已复现,不得称优于 RARR·KPR。
- 票面写过「矩阵 §1.10 FiscalQA 对照」。本仓前沿矩阵没有 §1.10 这一节。FiscalQA 的分数与语料不进本页成立格。
- 历史锚: `docs/evidence/patch-events/RESULT-Y.md` 的结果丙; #601 §9 与 §11。§11 要求另开预注册页,不动质量闸地板,不发明 SESOI。
- Why not copy as-is: 同尺充数会毁掉止损意义。

## 9. 主人如何审本页

Trust=Gate。合并前,以及任何「跑」之前,主人看这一页,而不是看夹具是否变绿。

1. 第 2 节九条假阳性判据与第 3 节四条止损仍在,id 没有增删。
2. 第 1–3 节脚手架原句仍含 `numeric_line=unregistered`。文末 Amendment-01 把 `criteria.numeric_line` 锁为 `registered:interval_gt0`,`sesoi` 仍 null,不得把该线叫做 SESOI。测量分数仍 null。
3. 第 4 节的 manifest 字段行仍在。`manifest.json` 里 `generator_sha256`、`nli_sha256` 与权重 hash 仍是 null。`generator_model` 与 `nli_model` 已按文末「模型锁定批注」写入。实验语料 path 与 sha256 已按 Amendment-01 清单写入，`role=frozen_corpus_unrun`，`measurement_status=unmeasured`，`counts_as_establishment=false`。B-04 的 `counts_as_establishment=false`。
4. 第 5 节仍写不改默认臂、不改 floors。`PRODUCTION_RETRIEVAL_MODE` 仍是 `hybrid+rerank`。
5. `measurement.json` 仍是 `run_status=unrun`、`measurement_status=unmeasured`、`counted_as_pass=false`。分数仍 null。`sesoi` 仍 null。
6. 历史结果丙没有被改判。`second_formal_y=false`。不得称优于 RARR·KPR。不得标产品 L5。
7. 离线质量闸的 `value=` 与合入本页之前一致。
8. 文末「激活批注」已写，并勾上「主人写激活批注」。批注如实写 `SPLIT.json` 的 `built_n=91`、`gap_n=9`。目标 n=100 是配额锁，不是已建成的 formal 针。`establishment.n` 仍是 null。「主人明文「跑」」未勾。文末「模型锁定批注」已把 `generator_model` 与 `nli_model` 从 `MODEL_REGISTRY` 锁入 manifest。`generator_sha256` 与 `nli_sha256` 仍是 null。`built_n` 仍是 91。不得「跑」，不得往 `RESULT.md` 填分数。

主人点头之前,不要把 `measurement_status` 改成已测量,不要往成立格填数字,不要改质量闸地板,不要开跑。

## Amendment-01 · 开跑前数字线（日期：2026-10-15 · 早于任何非空分数）

状态：协议已锁（比较 A · 数字线 L1 · 目标 n=100）/ 激活批注已写 / 生成器与 NLI 型号已从 `MODEL_REGISTRY` 锁入 manifest / 未开跑。本 Amendment 仍不是开跑,不写任何非空分数。实验语料 path 与 sha256 已写入 manifest，`role=frozen_corpus_unrun`，`measurement_status=unmeasured`。`built_n=91`，缺额不补。激活清单仍未齐：`generator_sha256` 与 `nli_sha256` 仍是 null，主人未明文「跑」。未明文「跑」之前不得开跑，不得写 RESULT。

第 1–8 节的假阳性 id 与止损 id 不增删、不改写。第 3 节「本期没有这份 amendment」与「numeric_line=unregistered」留在原处,作为看见本 Amendment 之前的脚手架锁句。本 Amendment 在任何非空分数出现之前补上比较对象与数字线,不涂掉那些原句,也不把门槛叫做 SESOI。

### 比较对象

- 臂：T（attested / fail-closed）对 C（无证据改写）。B1/B2 若保留则只作报告,不进成立格。
- 语料：新实验语料,不是 `data/corpus/pe_v2` 正式 Y 名单。path 与 sha256 已写入 manifest `sources.experiment_corpus`（`data/patch-establishment/v1`）。语料已冻，`measurement_status=unmeasured`，因此仍不得「跑」。
- 选取：固定 k := T 自然放行数。正式针 n=100（已锁）。pilot 另计,不进成立格。k_min、bootstrap 次数、种子与 temperature 主人未锁。生成器与 NLI 的型号已由「模型锁定批注」从 `MODEL_REGISTRY` 写入，不改模型 id。未锁参数不是已生效门槛,也不得在看见分数之后补写。
- `second_formal_y=false`。这不是 `PREREG-Y` 同尺再填。STOP-SAME-YARDSTICK 仍有效。

### 数字线（numeric_line）

- `sesoi=null`。本页不发明 SESOI,不继承改名 SESOI,不得把该线叫做 SESOI。
- `criteria.numeric_line=registered:interval_gt0`。这是判据行,不是已测量分数。
- 成立：主比较（T−C 固定-k 误放率差）点估计 > 0 且 95% CI 下界 > 0 且有定义。
- 无定义 / 下界≤0 / 点≤0 → 不成立。
- `establishment.numeric_line` 仍是 `unregistered`。`false_accept_rate`、`point_estimate`、`ci95_low`、`ci95_high`、`n`、`k` 都是 null。`run_status=unrun`。`measurement_status=unmeasured`。`counted_as_pass=false`。空着不是 0。

### 丙防火墙（重申）

- 历史分层只认 `docs/evidence/patch-events/RESULT-Y.md`：结果丙。不得把历史结果丙改判为乙。不得写回该文件,不得改 `docs/evidence/patch-events/PREREG-Y.md` 的历史成立格。
- 本跑不是路线 Y 的另一次正式主跑。`second_formal_y=false`。STOP-SAME-YARDSTICK。
- B-04 夹具 `counts_as_establishment=false`。夹具绿不是结果乙。
- 不得称优于 RARR·KPR。不得标产品 L5。即便将来成立格通过,本页仍不得单独把产品标成 L5。
- 不改 floors。不改默认臂。`PRODUCTION_RETRIEVAL_MODE` 仍是 `hybrid+rerank`。不改 gold,不改 x1。

### 止损增量

- STOP-UNRUN 仍有效,直至主人明文「跑」。写入器拒绝任何非 null 分数。
- 正式针完成后未成立 → 收口。禁止同页二跑,禁止加 n,禁止改尺后再用同一页充数。
- 过成立格仍不得称优于 RARR·KPR,不得把历史结果丙改判为乙,不得标产品 L5。

### 激活前清单

- [x] 实验语料路径与 sha256 写入 manifest `sources.experiment_corpus`（path=`data/patch-establishment/v1`，sha256 已写入；`role=frozen_corpus_unrun`；`measurement_status=unmeasured`；`counts_as_establishment=false`；本项不是激活，不是「跑」，不是成立）
- [x] 生成器 `generator_model` 与 NLI `nli_model` 写入 manifest（2026-10-15；主人锁 `MODEL_REGISTRY` 默认：`default_llm.model`=`qwen-flash`，`nli.model`=`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`；不改模型 id；本项不是「跑」，不是成立）
- [ ] 生成器 `generator_sha256` 与 NLI `nli_sha256` 写入 manifest（当前仍为 null；不发明 hash；temperature、seed 仍 null）
- [x] 主人确认比较对象与数字线：比较 A,数字线 L1,n=100（2026-10-15）
- [x] 主人写激活批注（2026-10-15；见下方「激活批注」；`built_n=91`；`gap_n=9`；目标 n=100 未满额建成；`run_status=unrun`；`sesoi=null`；分数仍 null；本项不是「跑」，不是成立）
- [ ] 主人明文「跑」

清单仍未齐。不得「跑」。Trust=Gate。合并与开跑都要主人另行点头。激活批注之后,仍须主人明文「跑」才可进入正式针。正式针若将来开跑,也不得把本次建成的 91 假装成已建成 n=100。

### 激活批注

日期：2026-10-15。相对语料冻结针 `fcc13a4044ed58802da4141d3377b3701e0e024b`（#634）。票 L4-C-04。Trust=Gate。

本批注只登记开跑前已经锁住的事实。它勾上「主人写激活批注」。它不勾「主人明文「跑」」。它不是开跑,不是成立,不往 `docs/evidence/patch-establishment/RESULT.md` 填分数。

- `run_status=unrun`。`measurement_status=unmeasured`。`establishment.status=unmeasured`。`counted_as_pass=false`。`sesoi=null`。`establishment.numeric_line` 仍是 `unregistered`。`criteria.numeric_line=registered:interval_gt0`。不得把该线叫做 SESOI。本页不发明 SESOI。
- `false_accept_rate`、`point_estimate`、`ci95_low`、`ci95_high`、`establishment.n`、`establishment.k` 都是 null。空着不是 0,也不是通过。
- 比较对象仍是比较 A：臂 T（attested / fail-closed）对 C（无证据改写）。B1/B2 若保留则只作报告,不进成立格。数字线 L1 已由主人在 2026-10-15 确认。k_min、bootstrap 次数、种子与 temperature 在本批注写下时未锁。生成器与 NLI 的型号随后由「模型锁定批注」锁入，不改模型 id。未锁参数不是已生效门槛,也不得在看见分数之后补写。
- 语料：`sources.experiment_corpus.path=data/patch-establishment/v1`，sha256 `cda7c5afffdba09550abb33cc5132453a91357c076d81752e9ca9eeca0397d1d`。`role=frozen_corpus_unrun`。`measurement_status=unmeasured`。`counts_as_establishment=false`。本批注不重冻该树,不改树内字节。
- 正式针配额目标 `target_n=100` 已锁,配额不改小。`data/patch-establishment/v1/SPLIT.json` 记录建成 `built_n=91`，缺额 `gap_n=9`。删除层 `built=16`（正确 12 / 坏 4，坏槽目标仍是 13，该层 `gap=9`）。数值、日期、条款替换各 `built=25`、`gap=0`。`shortfalls` 里 reason 为「语料不足」的记录是 9 条,与 `gap_n` 同数；其余 shortfall 是算子不改时的跳过,不是把缺额补成满额。本批注不把建成数写成 100,也不把 91 或 9 写进 `establishment.n` / `establishment.k`。
- 生成器 `generator_model` / `generator_sha256` 与 NLI `nli_model` / `nli_sha256` 在本批注写下时仍是 null。解码 temperature、seed、model 仍是 null。型号两格随后由「模型锁定批注」补上；hash 两格仍未勾。
- `second_formal_y=false`。STOP-SAME-YARDSTICK。本批注不是路线 Y 的另一次正式主跑。不得回到 `PREREG-Y` 同尺再填一格。
- 历史分层仍只认 `docs/evidence/patch-events/RESULT-Y.md`：结果丙。不得把历史结果丙改判为乙。不得改 `docs/evidence/patch-events/PREREG-Y.md` 的历史成立格。B-04 夹具 `counts_as_establishment=false`。夹具绿不是结果乙。不得称优于 RARR·KPR。不得标产品 L5。不改 floors。不改默认臂。`PRODUCTION_RETRIEVAL_MODE` 仍是 `hybrid+rerank`。不改 gold,不改 x1。
- STOP-UNRUN 仍有效,直至主人明文「跑」。写入器拒绝任何非 null 分数。清单仍未齐。不得「跑」。

## 模型锁定批注

日期：2026-10-15。主人 Oriental Ronin 批准：正式跑的生成器与 NLI 用 `MODEL_REGISTRY` 默认，不改模型 id。票 L4-C-04-lock-models。Trust=Watch。

本批注只锁型号。它不勾「主人明文「跑」」。它不是开跑，不是成立，不往 `docs/evidence/patch-establishment/RESULT.md` 填分数。

- `generator_model` = `MODEL_REGISTRY["default_llm"].model` = `qwen-flash`。别名 `DEFAULT_MODEL`。
- `nli_model` = `MODEL_REGISTRY["nli"].model` = `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`。别名 `NLI_MODEL`。
- `generator_sha256` 与 `nli_sha256` 仍是 null。不发明 hash。解码 temperature、seed、model 仍是 null。
- `data/patch-establishment/v1/SPLIT.json` 的 `built_n` 仍是 91，`gap_n` 仍是 9。目标 n=100 不改小，缺额不补。语料 path 与 sha256 不重冻。
- `run_status=unrun`。`measurement_status=unmeasured`。`sesoi=null`。本页不发明 SESOI。
- 不改 floors。不改 gold。不改 x1。不改默认生产臂。`PRODUCTION_RETRIEVAL_MODE` 仍是 `hybrid+rerank`。
- 激活批注里「型号两格仍是 null」记录的是本批注之前的状态。型号两格以本批注为准。hash 两格仍是 null。清单仍未齐，因为 hash 未写，且主人未明文「跑」。不得「跑」。
