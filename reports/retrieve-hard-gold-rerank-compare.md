# hybrid 与 hybrid+rerank 对比（Hard-Gold hard 集）

- 对比臂: 本地词重叠精排,不是 bge,不是 α 加权
- 解码: 无 LLM temperature/seed;延迟在本机 perf_counter 上测量
- n: 20（冒烟级,不声称统计显著,不报方差）
- hybrid Recall@10: 0.5000
- hybrid+rerank Recall@10: 0.5000
- p95: 189.2 ms
- 门槛: Recall@10 严格更好且 p95≤800ms
- rerank 列确为 hybrid+rerank: pass
- 判决: 生产默认关
- 代码生产默认: bm25

未同时满足两条门槛时生产默认保持关。本页不是统计结论。
