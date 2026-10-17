import os
import shutil
from pathlib import Path

import pytest

# 单测强制关掉本地 embedding 和神经 reranker，避免下载 BAAI 权重。
# 生产进程未设置这两个变量时：embedder 默认挂上，hybrid+rerank 走 bge-reranker-base。
os.environ["FRESHLATCH_LOCAL_EMBED"] = "0"
os.environ["FRESHLATCH_NEURAL_RERANK"] = "0"

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRATCH_DIR = _REPO_ROOT / ".scratch"


@pytest.fixture(scope="session", autouse=True)
def _clean_scratch_after_session():
    """I-06(#681)：session teardown 清空 `.scratch/` 暂存区。

    `.scratch/` 是 gitignored 的调试暂存区（见 .gitignore），但历史残留会污染
    pe_freeze 表面积扫描（rglob 全仓）。teardown 保证测后无残留、永不入库。
    """
    yield
    shutil.rmtree(_SCRATCH_DIR, ignore_errors=True)
