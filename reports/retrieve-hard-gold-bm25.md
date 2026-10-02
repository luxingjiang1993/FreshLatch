# Hard-Gold 骨架 · BM25 / 增益门复跑

> 层身份：冒烟 / 面试加固（I3）。本波 Hard-Gold = 骨架语料 + 增益门复跑；**未授权改臂**。
> 不报方差；不作统计显著。与冒烟 `retrieve_gold.json` 分文件。

- 日期: 2026-10-02
- hard gold: `data/eval/retrieve_hard_gold.json`
- n: 20（预登记 ≥20）
- traps/对抗: 8 （40.0%，预登记 ≥30%）
- BM25 Recall@10: 0.6000
- BM25 MRR@10: 0.3497
- 代码生产默认臂: `bm25`（断言须为 bm25）
- 增益门判决: 关（Hard-Gold 骨架已跑；改生产默认臂仍须另决议 + 过线；PRODUCTION_RETRIEVAL_MODE='bm25'）
- 臂对比备注: 无 dense 索引：本波仅 BM25 轨；按 I0 纪律标需索引，不得因此改臂。

增益门公式见 `docs/eval-retrieve.md` §3 / ADR-0026；本页不事后改门。
