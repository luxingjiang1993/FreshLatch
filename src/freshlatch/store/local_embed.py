"""本地 chunk / query embedding。模型固定为 BAAI/bge-small-zh-v1.5（fastembed，dim=512）。

不读付费 API key，不走云端 embedding。
神经 reranker 在 ``neural_rerank.py``，模型是 ``BAAI/bge-reranker-base``，缓存目录同是 ``FASTEMBED_CACHE_PATH``。
"""

from __future__ import annotations

import os
from typing import Callable

from freshlatch.models import LOCAL_EMBED_MODEL
from freshlatch.store.base import Chunk
from freshlatch.store.pipeline import pack_vec
LOCAL_EMBED_DIM = 512
# fastembed 自己的缓存目录变量，原样传给 TextEmbedding(cache_dir=...)。
EMBED_CACHE_ENV = "FASTEMBED_CACHE_PATH"

_model = None


class LocalEmbedUnavailable(RuntimeError):
    """权重不在缓存里，或离线加载失败。"""


def local_embed_cache_dir() -> str | None:
    """``FASTEMBED_CACHE_PATH``。未设置时返回 None，交给 fastembed 的默认缓存。"""
    raw = os.environ.get(EMBED_CACHE_ENV, "").strip()
    return raw or None


def embed_offline_requested() -> bool:
    """显式离线：不尝试下载。``HF_HUB_OFFLINE=1`` 与 ``FRESHLATCH_EMBED_OFFLINE=1`` 都算。"""
    return os.environ.get("HF_HUB_OFFLINE", "") == "1" or os.environ.get(
        "FRESHLATCH_EMBED_OFFLINE", ""
    ) == "1"


def local_embed_unavailable_message(exc: BaseException) -> str:
    cache = local_embed_cache_dir() or "(fastembed default cache)"
    return (
        f"本地 embedding 权重不可用。model={LOCAL_EMBED_MODEL} "
        f"cache_dir={cache} exc_type={type(exc).__name__}。"
        "请在有网环境运行 python scripts/warmup_local_embed.py，"
        "再用 FASTEMBED_CACHE_PATH 指向该缓存。离线环境不会自动下载。"
    )


def _load_model():
    """首次调用才 import fastembed。未调用时不下载权重。"""
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        kwargs: dict = {"model_name": LOCAL_EMBED_MODEL}
        cache = local_embed_cache_dir()
        if cache:
            kwargs["cache_dir"] = cache
        if embed_offline_requested():
            kwargs["local_files_only"] = True
        try:
            _model = TextEmbedding(**kwargs)
        except Exception as exc:
            raise LocalEmbedUnavailable(local_embed_unavailable_message(exc)) from exc
    return _model


def embed_texts_local(texts: list[str]) -> list[list[float]]:
    """批量本地向量。空输入不加载模型。维度必须是 512。"""
    if not texts:
        return []
    model = _load_model()
    out: list[list[float]] = []
    for vec in model.embed(texts):
        values = [float(x) for x in vec]
        if len(values) != LOCAL_EMBED_DIM:
            raise ValueError(
                f"本地向量维度 {len(values)} 不是 {LOCAL_EMBED_DIM}"
            )
        out.append(values)
    if len(out) != len(texts):
        raise ValueError("本地向量条数与文本数不一致")
    return out


def embed_query_local(query: str) -> list[float]:
    """单条 query。与 chunk 同一模型，供 hybrid 的 query_embedder。"""
    vecs = embed_texts_local([query])
    if len(vecs) != 1:
        raise ValueError("query 向量条数不是 1")
    return vecs[0]


def fill_chunk_vecs(
    chunks: list[Chunk],
    embedder: Callable[[list[str]], list[list[float]]],
) -> None:
    """只补缺 vec 的块。已有 vec 不动，避免覆盖调用方写入的向量。"""
    missing = [chunk for chunk in chunks if not chunk.vec]
    if not missing:
        return
    vecs = embedder([chunk.text for chunk in missing])
    if len(vecs) != len(missing):
        raise ValueError("embedder 返回条数与缺向量块数不一致")
    for chunk, vec in zip(missing, vecs):
        if not vec:
            continue
        chunk.vec = pack_vec([float(x) for x in vec])


def attach_local_embedder(store) -> None:
    """生产入口挂上本地 embedder。``FRESHLATCH_LOCAL_EMBED=0`` 时不挂，测试不下载权重。

    未设置环境变量时默认挂上。不改 ``PRODUCTION_RETRIEVAL_MODE``。
    """
    if os.environ.get("FRESHLATCH_LOCAL_EMBED", "1") == "0":
        return
    store.chunk_embedder = embed_texts_local
    store.query_embedder = embed_query_local
