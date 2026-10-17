"""I-02(#679):开始复验前的本地权重文件层预检(纯 stat,毫秒级)。

放独立模块而非 ``store/local_embed.py`` / ``store/neural_rerank.py``：
后两者在 RESULT-Y 期 L4 do-not-touch 清单内(#679 硬约束不碰 RESULT-Y/L4)。
这里只读目录树判断权重快照在不在,不 import fastembed、不加载模型、不触网
(真加载 reranker 约 8 秒,不满足「点开始后 ≤10s 出面板」)。
"""

from __future__ import annotations

from pathlib import Path

from freshlatch.models import LOCAL_EMBED_MODEL, NEURAL_RERANK_MODEL
from freshlatch.store.local_embed import local_embed_cache_dir

# 未设置 FASTEMBED_CACHE_PATH 时 fastembed 的默认缓存根(docs/ops/local-embed.md)。
FASTEMBED_DEFAULT_CACHE = Path.home() / ".cache" / "fastembed_cache"


def _cache_roots(cache_dir: str | None) -> list[Path]:
    """预检要看的缓存根:显式目录优先,否则看 fastembed 默认缓存。不存在也列出。"""
    raw = cache_dir if cache_dir is not None else local_embed_cache_dir()
    if raw:
        return [Path(raw)]
    return [FASTEMBED_DEFAULT_CACHE]


def fastembed_weights_present(model_short: str, cache_dir: str | None = None) -> bool:
    """文件层看权重快照在不在:任何 ``*.onnx`` 命中即算有。

    兼容 huggingface_hub 快照布局(``models--<org>--<name>/snapshots/<rev>/...``)
    与直接放置的模型目录。
    """
    for root in _cache_roots(cache_dir):
        if not root.is_dir():
            continue
        for cand in root.glob(f"models--*{model_short}*"):
            if cand.is_dir() and any(cand.glob("snapshots/**/*.onnx")):
                return True
        for cand in root.glob(f"*{model_short}*"):
            if cand.is_dir() and not cand.name.startswith("models--"):
                if any(cand.rglob("*.onnx")):
                    return True
    return False


def local_embed_weights_ready(cache_dir: str | None = None) -> bool:
    """embedding 权重(BAAI/bge-small-zh-v1.5)缓存是否就绪。"""
    return fastembed_weights_present(LOCAL_EMBED_MODEL.split("/")[-1], cache_dir)


def neural_rerank_weights_ready(cache_dir: str | None = None) -> bool:
    """reranker 权重(BAAI/bge-reranker-base,约 1.1GB)缓存是否就绪。"""
    return fastembed_weights_present(NEURAL_RERANK_MODEL.split("/")[-1], cache_dir)
