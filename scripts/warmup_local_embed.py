"""预热本地 embedding 与 reranker 权重。有网时下载，离线时直接失败。

embedding 模型固定为 BAAI/bge-small-zh-v1.5（fastembed，dim=512）。
reranker 模型固定为 BAAI/bge-reranker-base（TextCrossEncoder，CPU）。
两者的缓存目录都用环境变量 FASTEMBED_CACHE_PATH。
不调用付费 API。不改 PRODUCTION_RETRIEVAL_MODE。

用法:
    FASTEMBED_CACHE_PATH=/var/cache/freshlatch-embed python scripts/warmup_local_embed.py
"""

from __future__ import annotations

import sys

from freshlatch.store.local_embed import (  # noqa: E402
    EMBED_CACHE_ENV,
    LOCAL_EMBED_DIM,
    LOCAL_EMBED_MODEL,
    LocalEmbedUnavailable,
    embed_offline_requested,
    embed_texts_local,
    local_embed_cache_dir,
    local_embed_unavailable_message,
)
from freshlatch.store.neural_rerank import (  # noqa: E402
    NEURAL_RERANK_MODEL,
    NeuralRerankUnavailable,
    neural_rerank_unavailable_message,
    warmup_neural_rerank,
)


def main() -> int:
    cache = local_embed_cache_dir()
    if embed_offline_requested():
        print(
            local_embed_unavailable_message(RuntimeError("offline")),
            file=sys.stderr,
        )
        print(
            neural_rerank_unavailable_message(RuntimeError("offline")),
            file=sys.stderr,
        )
        print(
            f"当前是离线模式，预热脚本不会下载。请去掉 HF_HUB_OFFLINE / "
            f"FRESHLATCH_EMBED_OFFLINE，或把已有缓存指到 {EMBED_CACHE_ENV}。",
            file=sys.stderr,
        )
        return 2
    try:
        vecs = embed_texts_local(["预热"])
    except LocalEmbedUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if len(vecs) != 1 or len(vecs[0]) != LOCAL_EMBED_DIM:
        print(
            f"预热后维度不是 {LOCAL_EMBED_DIM}: model={LOCAL_EMBED_MODEL}",
            file=sys.stderr,
        )
        return 1
    try:
        warmup_neural_rerank()
    except NeuralRerankUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 1
    where = cache or "(fastembed default cache)"
    print(
        f"ok model={LOCAL_EMBED_MODEL} dim={LOCAL_EMBED_DIM} "
        f"rerank={NEURAL_RERANK_MODEL} cache_dir={where}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
