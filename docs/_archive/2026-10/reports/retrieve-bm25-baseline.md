# BM25 retrieve 基线（冒烟）

- 日期: 2026-09-28
- 语料文件数: 28
- chunk 数: 84
- retrieval_mode: bm25
- 解码: 无 LLM,不适用 temperature/seed
- n: 36（冒烟级,不声称统计显著,不报方差）
- K∈{5,10}
- Recall@5: 1.0000
- Recall@10: 1.0000
- MRR@10: 0.7324
- must_stale 回放: pass
- corpus+retrieve 金标聚合 checksum: `00a43c88db4522a8d5bb2ebe821c0e22c81302a9ed1a117ed5b64932afc60bcb`
- corpus checksum: `a1a35e9b55f48eaf4381a27855db987c3c5870fb6a43d4458829bcbacc5b0b04`
- retrieve 金标 checksum: `a62830b3c9e5b9fd10484ed06aa182d7a1ac25c0ca8cad739329230577f58255`

本页是 A0 冒烟基线,不是统计结论。查询表由主张金标规则派生,先于本页指标锁定。
