"""本地 chunk / query embedding。模型固定为 BAAI/bge-small-zh-v1.5（fastembed，dim=512）。

不读付费 API key，不走云端 embedding。
``rerank_lexical`` 仍是 jieba token overlap，这里不加载神经 reranker。
"""

from __future__ import annotations

import os
from typing import Callable

from freshlatch.store.base import Chunk
from freshlatch.store.pipeline import pack_vec

LOCAL_EMBED_MODEL = "BAAI/bge-small-zh-v1.5"
LOCAL_EMBED_DIM = 512

_model = None


def _load_model():
    """首次调用才 import fastembed。未调用时不下载权重。"""
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        _model = TextEmbedding(model_name=LOCAL_EMBED_MODEL)
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
