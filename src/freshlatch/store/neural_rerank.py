"""生产精排：本地 BAAI/bge-reranker-base，只重排 hybrid 的前 10 条。

权重缺失或推理失败时退回 ``rerank_lexical``，并记 ``last_rerank_mode=lexical_fallback``。
不调用付费 API。pytest 把 ``FRESHLATCH_NEURAL_RERANK=0``，不构造 ``TextCrossEncoder``。
"""

from __future__ import annotations

import logging
import os

from freshlatch.models import NEURAL_RERANK_MODEL
from freshlatch.store.base import Chunk
from freshlatch.store.local_embed import embed_offline_requested, local_embed_cache_dir
from freshlatch.store.pipeline import rerank_lexical

logger = logging.getLogger(__name__)
NEURAL_RERANK_K = 10
RERANK_MODE_NEURAL = "bge-reranker-base"
RERANK_MODE_LEXICAL = "lexical"
RERANK_MODE_FALLBACK = "lexical_fallback"
RERANK_MODE_NONE = "none"
NEURAL_RERANK_ENV = "FRESHLATCH_NEURAL_RERANK"

_encoder = None


class NeuralRerankUnavailable(RuntimeError):
    """权重不在缓存里，或离线加载失败。"""


class NeuralRerankDisabled(RuntimeError):
    """``FRESHLATCH_NEURAL_RERANK=0``。不加载模型。"""


def neural_rerank_disabled() -> bool:
    return os.environ.get(NEURAL_RERANK_ENV, "1") == "0"


def neural_rerank_unavailable_message(exc: BaseException) -> str:
    cache = local_embed_cache_dir() or "(fastembed default cache)"
    if isinstance(exc, NeuralRerankDisabled):
        hint = (
            f"{NEURAL_RERANK_ENV}=0，未加载模型。"
            "生产进程不要设这个变量；要词重叠精排请用 "
            'set_retrieval_switch("hybrid+rerank_lexical")。'
        )
    else:
        hint = (
            "请在有网环境运行 python scripts/warmup_local_embed.py，"
            "再用 FASTEMBED_CACHE_PATH 指向该缓存。离线环境不会自动下载。"
        )
    return (
        "本地 reranker 不可用，退回 rerank_lexical。"
        f"last_rerank_mode={RERANK_MODE_FALLBACK} "
        f"model={NEURAL_RERANK_MODEL} cache_dir={cache} "
        f"exc_type={type(exc).__name__}。{hint}"
    )


def _warn_fallback(exc: BaseException) -> None:
    logger.warning("%s", neural_rerank_unavailable_message(exc))


def _cross_encoder_cls():
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder


def _load_encoder():
    """首次调用才 import fastembed。未调用时不下载权重。"""
    global _encoder
    if _encoder is None:
        try:
            cls = _cross_encoder_cls()
        except ImportError as exc:
            raise NeuralRerankUnavailable(neural_rerank_unavailable_message(exc)) from exc
        kwargs: dict = {"model_name": NEURAL_RERANK_MODEL, "cuda": False}
        cache = local_embed_cache_dir()
        if cache:
            kwargs["cache_dir"] = cache
        if embed_offline_requested():
            kwargs["local_files_only"] = True
        try:
            _encoder = cls(**kwargs)
        except Exception as exc:
            raise NeuralRerankUnavailable(neural_rerank_unavailable_message(exc)) from exc
    return _encoder


def _rerank_neural(query: str, chunks: list[Chunk]) -> list[Chunk]:
    if not chunks:
        return []
    encoder = _load_encoder()
    docs = [chunk.text for chunk in chunks]
    scores = [float(item) for item in encoder.rerank(query, docs)]
    if len(scores) != len(chunks):
        raise RuntimeError(f"rerank 分数条数 {len(scores)} 与候选 {len(chunks)} 不一致")
    order = sorted(range(len(chunks)), key=lambda i: (-scores[i], i))
    return [chunks[i] for i in order]


def warmup_neural_rerank() -> None:
    """构造 cross-encoder 并打一条预热。失败时异常信息含模型名和缓存目录。"""
    encoder = _load_encoder()
    scores = [float(item) for item in encoder.rerank("预热", ["预热文档"])]
    if len(scores) != 1:
        raise NeuralRerankUnavailable(
            neural_rerank_unavailable_message(
                RuntimeError(f"warmup scores {len(scores)}")
            )
        )


def rerank_hybrid_candidates(
    query: str,
    chunks: list[Chunk],
    *,
    top_k: int,
    lexical_only: bool,
) -> tuple[list[Chunk], str]:
    """重排 hybrid 已经给出的候选。

    神经路径只把前 ``NEURAL_RERANK_K`` 条送进 cross-encoder。多出来的尾巴保持 hybrid 原序。
    ``lexical_only`` 时整段 ``top_k`` 走 ``rerank_lexical``，不加载模型。
    """
    limit = min(len(chunks), top_k)
    body = list(chunks[:limit])
    if lexical_only:
        return rerank_lexical(query, body, top_k=limit), RERANK_MODE_LEXICAL
    head_n = min(NEURAL_RERANK_K, limit)
    head = body[:head_n]
    tail = body[head_n:]
    if neural_rerank_disabled():
        _warn_fallback(NeuralRerankDisabled(NEURAL_RERANK_ENV))
        return rerank_lexical(query, head, top_k=head_n) + tail, RERANK_MODE_FALLBACK
    try:
        ranked = _rerank_neural(query, head)
    except Exception as exc:
        _warn_fallback(exc)
        return rerank_lexical(query, head, top_k=head_n) + tail, RERANK_MODE_FALLBACK
    return ranked + tail, RERANK_MODE_NEURAL
