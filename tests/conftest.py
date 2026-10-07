import os
import sys
from pathlib import Path

# 单测强制关掉本地 embedding 和神经 reranker，避免下载 BAAI 权重。
# 生产进程未设置这两个变量时：embedder 默认挂上，hybrid+rerank 走 bge-reranker-base。
os.environ["FRESHLATCH_LOCAL_EMBED"] = "0"
os.environ["FRESHLATCH_NEURAL_RERANK"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
