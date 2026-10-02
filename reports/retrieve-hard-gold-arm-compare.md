# BM25 / dense / hybrid 三列（Hard-Gold hard 集）

- RRF k: 60
- 融合: 名次倒数,不是 α 加权
- 模型: text-embedding-v4
- 解码: 向量为预计算嵌入,打分无 temperature/seed
- n: 20（冒烟级,不声称统计显著,不报方差）
- BM25 Recall@10: 0.3500
- dense Recall@10: 0.4500
- hybrid Recall@10: 0.5000
- A0 基线 Recall@10: 0.6000
- BM25 相对 A0 容差: 0.0
- BM25 相对 A0: fail
- hybrid >= min(BM25, dense): pass
- dense 列确为 dense: pass
- hybrid 列确为 hybrid: pass
- 通过线: fail

本页是冒烟对比,不是统计结论。生产默认仍是 BM25。
