# QG-12 Track A 第一次 G1/A1/T1 离线冻结

日期：2026-10-13

`git rev-parse HEAD`：`934713d332bbb901fdbe15741900de9108a824c6`

命令：`python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md`

进程退出码：0

三份正式金标与当次 `docs/evidence/quality-gate/PREREG.md` 的 sha256（只记录，未修改这些文件）：

- `data/eval/guard_should.json`：`63144c205f02ebbde88b9dd95217dfc9a1d69f6813590d1dd4818481d50022de`
- `data/eval/cite_sentence.json`：`7b299a0bce8589bc2fd810a706572be27b4409ab03bc8a6c6b4d8024ee65bc94`
- `data/eval/temporal_new_over_old.json`：`3a1b959a6aa63b89d10fa883982c11b7b7234aacdb537d754a1587010e40c8a0`
- `docs/evidence/quality-gate/PREREG.md`：`f583650f41ccb36f522359c05ab66cc74f3558ad3f8e3be007fb306af6032188`

```
离线产品质量闸
offline=true
locked_gate=true
owner_freeze=confirmed
fingerprints=match
arm=hybrid+rerank
embed_model=BAAI/bge-small-zh-v1.5
embed_dim=512
rrf_k=60
rerank_model=BAAI/bge-reranker-base
rerank_k=10
fastembed=0.8.1
denominator=data/exp/x1/questions.json
n=267
n_arm=224
n_guardrail=43
questions_sha256=2cd7c5fb1e14859049c148e4dafc95b4d3c0abb4fa1080965dcc57b0d57c73fe
baseline=docs/evidence/neural-rerank/summary.json
baseline_sha256=8fb4f1271b844c979b28bf351cf22ecbad354e3f5f35f7d2e1e7d760efb8e526
excluded_lexical_used=false
paid_llm=false
qg04=separate
segment id=G1-should-refuse status=unregistered file=data/eval/guard_should.json file_present=true counted_as_pass=false
segment id=A1 status=unregistered file=data/eval/cite_sentence.json file_present=true counted_as_pass=false
segment id=T1-new-over-old status=unregistered file=data/eval/temporal_new_over_old.json file_present=true counted_as_pass=false
metric id=G1-should-refuse-accuracy status=TBD value=1.0 baseline=none n=12 scored=12 correct=12 unresolved=0 n_should_refuse=8 n_should_pass=4 source=gold-bucket-agreement counted_as_pass=false
metric id=A1-citation-recall status=TBD value=0.42857142857142855 baseline=none n=7 scored=7 unresolved=0 source=cited-vs-relevant counted_as_pass=false
metric id=A1-citation-precision status=TBD value=0.6 baseline=none n=7 scored=5 unresolved=2 source=cited-vs-relevant counted_as_pass=false
metric id=T1-new-over-old-accuracy status=TBD value=0.3333333333333333 baseline=none n=4 scored=3 correct=1 unresolved=1 source=frozen-per-query-replay counted_as_pass=false
metric id=R1-recall@10 status=TBD value=0.9732142857142857 baseline=0.9732142857142857 source=frozen-per-query-replay delta=0.0 r1_no_regression=true counted_as_pass=false
metric id=R1-mrr@10 status=TBD value=0.8381855867346939 baseline=0.8381855867346939 source=frozen-per-query-replay delta=0.0 r1_no_regression=true counted_as_pass=false
metric id=guardrail-0hit status=TBD value=unavailable baseline=none n=43 source=no-guardrail-hits counted_as_pass=false
metric id=conflict-pair-ordering status=TBD value=0.3333333333333333 baseline=none correct=1 n=3 source=frozen-per-query-replay counted_as_pass=false
metric id=multi-hop-full-hit status=TBD value=0.7555555555555555 baseline=none n=45 source=frozen-per-query-replay counted_as_pass=false
trap_smoke id=trap-smoke status=not_counted file=data/eval/retrieve_traps.json present=true level=smoke n=3 in_denominator=false counted_as_pass=false
```

本页是 descriptive-only。这些数字不是通过线。本页不改 owner_freeze 行，不新增 segment_registered 行，不把旁列升成 P0。

G1 的 value 是 `label` 对 `gold.json` 三档的一致性，不是模型拒绝率，也不是 CI `must_*` 闸。

点估计只作为上面围栏里 stdout 的 `value=` 原样出现。本页不另写一套数字，不发明 SESOI，不写绝对百分数。`n_should_refuse` 与 `n_should_pass` 不除成率。旁列 `conflict-pair-ordering` 与 `multi-hop-full-hit` 不拿来当 T1 地板。
