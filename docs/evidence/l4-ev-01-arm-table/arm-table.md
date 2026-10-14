# Recall@k / MRR 分臂表

- level: smoke
- k: 10
- n: 2
- code_pin: 0678d7610da01943b77904de88543574b884fac4
- gold_path: tests/eval/fixtures/l4_ev_01_arm_gold.json
- gold_sha256: bf2eafa1bcffb5ff0afe5e2ab3f14216ea455c604d56beb00563df518595dad8
- fixture_version: l4-ev-01-smoke
- production_retrieval_mode: hybrid+rerank
- rrf_k: 60
- neural_rerank_k: 10
- neural_rerank_env: 0
- 解码: 夹具内向量，无 temperature，无 seed
- 检索 top_k 等于 k
- replaces_frozen_baseline: false
- 冻结基线文件不在本目录重写

| arm | Recall@k | MRR | observed_retrieval_mode | observed_rerank_mode |
| --- | --- | --- | --- | --- |
| bm25 | 0 | 0 | bm25 | none |
| dense | 1 | 1 | dense | none |
| hybrid | 1 | 0.416666666667 | hybrid | none |
| hybrid+rerank | 1 | 0.416666666667 | hybrid+rerank | lexical_fallback |
