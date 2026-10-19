# Dense 索引重建附注（#259）

- 复跑票: #259
- 记录日: 2026-10-03
- 命令: `PYTHONPATH=src python scripts/build_dense_index.py`
- 主报告: `reports/dense-rebuild.md`（status=ok · text-embedding-v4 · chunks=94 · corpus=84 · traps=10 · dim=1024 · scope=corpus+traps）
- 产物: `data/dense/index.sqlite`（gitignore；未提交密钥）
- 相对 #258: 索引范围由仅 corpus 扩为 corpus+traps，与 hard A0 / 臂对比同库
