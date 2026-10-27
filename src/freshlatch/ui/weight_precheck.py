"""I-02(#679):开始复验前的本地权重文件层预检(纯 stat,毫秒级)。

放独立模块而非 ``store/local_embed.py`` / ``store/neural_rerank.py``：
后两者在 RESULT-Y 期 L4 do-not-touch 清单内(#679 硬约束不碰 RESULT-Y/L4)。
这里只读目录树判断权重快照在不在,不 import fastembed、不加载模型、不触网
(真加载 reranker 约 8 秒,不满足「点开始后 ≤10s 出面板」)。

#751:未设 ``FASTEMBED_CACHE_PATH`` 时默认根必须与 fastembed 落点一致
(``tempfile.gettempdir()/fastembed_cache``),不得再扫 ``~/.cache/fastembed_cache``。
"""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

from freshlatch.models import LOCAL_EMBED_MODEL, NEURAL_RERANK_MODEL
from freshlatch.store.local_embed import EMBED_CACHE_ENV, local_embed_cache_dir

_logger = logging.getLogger(__name__)


def fastembed_default_cache_root() -> Path:
    """未设 ``FASTEMBED_CACHE_PATH`` 时与 fastembed 一致的默认缓存根。

    fastembed 未传 ``cache_dir`` 时落到临时目录下的 ``fastembed_cache``
    (见 ``docs/ops/local-embed.md``),Windows 即 ``%TEMP%\\fastembed_cache``。
    """
    return Path(tempfile.gettempdir()) / "fastembed_cache"


def __getattr__(name: str):
    """兼容旧名 ``FASTEMBED_DEFAULT_CACHE``:每次解析,避免导入瞬间冻死路径。"""
    if name == "FASTEMBED_DEFAULT_CACHE":
        return fastembed_default_cache_root()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _cache_roots(cache_dir: str | None) -> list[Path]:
    """预检要看的缓存根:显式目录优先,否则看 fastembed 默认缓存。不存在也列出。"""
    raw = cache_dir if cache_dir is not None else local_embed_cache_dir()
    if raw:
        return [Path(raw)]
    return [fastembed_default_cache_root()]


def resolved_cache_dir(cache_dir: str | None = None) -> str:
    """运维可见的解析后缓存根(绝对路径字符串)。

    #753:未设 ``FASTEMBED_CACHE_PATH`` 时仍返回 ``gettempdir()/fastembed_cache``,
    不得用 ``null`` 隐瞒默认根。doctor 与 ``GET /api/retrieval/precheck`` 共用。
    """
    return str(_cache_roots(cache_dir)[0].resolve())


def warn_if_fastembed_cache_path_unset() -> str | None:
    """UI 启动:未设 ``FASTEMBED_CACHE_PATH`` 时打中文硬警告;已设则静默。

    口径与 ``docs/ops/local-embed.md`` 一致:未设时权重落临时目录
    (``resolved_cache_dir()`` = ``gettempdir()/fastembed_cache``),重启易丢。
    只警告、不阻断启动。返回警告文案便于单测断言;已设返回 None。
    """
    if local_embed_cache_dir():
        return None
    resolved = resolved_cache_dir()
    # 与 local-embed.md「缓存目录」节同口径;Windows 给绝对路径示例
    msg = (
        f"警告:未设置 {EMBED_CACHE_ENV}。"
        f"权重将落临时目录(当前解析根={resolved}),重启后易丢失。"
        f"请设为持久目录,例如 Windows PowerShell:"
        f' $env:{EMBED_CACHE_ENV}="D:\\cache\\freshlatch-embed" '
        f"(详见 docs/ops/local-embed.md)。"
    )
    print(msg, file=sys.stderr)
    _logger.warning(msg)
    return msg


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
