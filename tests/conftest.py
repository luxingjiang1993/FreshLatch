import os
import sys
from pathlib import Path

# 单测强制关掉本地 embedding，避免 TestClient / ingest 下载 BAAI 权重。
# 生产进程未设置该变量时，attach_local_embedder 默认挂上。
os.environ["FRESHLATCH_LOCAL_EMBED"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
