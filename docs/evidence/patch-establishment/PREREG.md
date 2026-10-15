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

冻结的是字段,不是一次已跑的分数。检索块记录现行生产臂的名字与常数,权重 hash 为 null。模型块的生成器与 NLI 为 null。源块里,历史页、质量闸预注册、冻结 per-query、金标、x1 题集与 B-04 夹具只记 sha256,`counts_as_establishment=false`。实验语料 hash 为 null。

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
3. 第 4 节的 manifest 字段行仍在。`manifest.json` 里模型 hash、权重 hash 仍是 null。实验语料 path 与 sha256 已按 Amendment-01 清单写入，`role=frozen_corpus_unrun`，`measurement_status=unmeasured`，`counts_as_establishment=false`。B-04 的 `counts_as_establishment=false`。
4. 第 5 节仍写不改默认臂、不改 floors。`PRODUCTION_RETRIEVAL_MODE` 仍是 `hybrid+rerank`。
5. `measurement.json` 仍是 `run_status=unrun`、`measurement_status=unmeasured`、`counted_as_pass=false`。
6. 历史结果丙没有被改判。`second_formal_y=false`。不得称优于 RARR·KPR。不得标产品 L5。
7. 离线质量闸的 `value=` 与合入本页之前一致。

主人点头之前,不要把 `measurement_status` 改成已测量,不要往成立格填数字,不要改质量闸地板,不要开跑。

## Amendment-01 · 开跑前数字线（日期：2026-10-15 · 早于任何非空分数）

状态：协议已锁（比较 A · 数字线 L1 · n=100）/ 未激活。本 Amendment 只是开跑前协议锁,不是激活,不是开跑,不写任何非空分数。实验语料 path 与 sha256 已写入 manifest，但仍 `measurement_status=unmeasured`。激活清单未齐、主人未明文「跑」之前不得开跑。

第 1–8 节的假阳性 id 与止损 id 不增删、不改写。第 3 节「本期没有这份 amendment」与「numeric_line=unregistered」留在原处,作为看见本 Amendment 之前的脚手架锁句。本 Amendment 在任何非空分数出现之前补上比较对象与数字线,不涂掉那些原句,也不把门槛叫做 SESOI。

### 比较对象

- 臂：T（attested / fail-closed）对 C（无证据改写）。B1/B2 若保留则只作报告,不进成立格。
- 语料：新实验语料,不是 `data/corpus/pe_v2` 正式 Y 名单。path 与 sha256 已写入 manifest `sources.experiment_corpus`（`data/patch-establishment/v1`）。语料已冻，`measurement_status=unmeasured`，因此仍不得「跑」。
- 选取：固定 k := T 自然放行数。正式针 n=100（已锁）。pilot 另计,不进成立格。k_min、bootstrap 次数、种子、模型与 temperature 主人未锁;未锁参数不是已生效门槛,也不得在看见分数之后补写。
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
- [ ] 生成器与 NLI（若用）的型号与 hash 写入 manifest（当前仍为 null）
- [x] 主人确认比较对象与数字线：比较 A,数字线 L1,n=100（2026-10-15）
- [ ] 主人写激活批注
- [ ] 主人明文「跑」

清单未齐。不得「跑」。Trust=Gate。合并与开跑都要主人另行点头。语料冻结之后,仍须主人明文「跑」才可进入正式针。
