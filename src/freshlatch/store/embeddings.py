"""DashScope text-embedding-v4 预计算。运行时打分不在本模块,只负责取向量。

密钥只从环境变量读取,禁止写入日志、报告或异常文本。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from freshlatch.models import EMBED_MODEL, MODEL_REGISTRY

_embed_base = MODEL_REGISTRY["embed"].base_url
if not isinstance(_embed_base, str) or not _embed_base:
    raise RuntimeError("embed 缺少 base_url")
_ENDPOINT = _embed_base + "/embeddings"


def redact(text: str) -> str:
    secret = os.environ.get("DASHSCOPE_API_KEY") or ""
    if secret and secret in text:
        text = text.replace(secret, "[redacted]")
    return text


def embed_texts(texts: list[str], *, timeout: float = 60.0) -> list[list[float]]:
    """按输入顺序返回向量。失败抛错,由检索臂降级,不在这里改走 BM25。"""
    key = os.environ.get("DASHSCOPE_API_KEY")
    if not key:
        raise RuntimeError("缺少 DASHSCOPE_API_KEY")
    if not texts:
        return []
    body = json.dumps({"model": EMBED_MODEL, "input": texts}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        _ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = redact(exc.read().decode("utf-8", errors="replace")[:180])
        raise RuntimeError(f"embedding HTTP {exc.code}: {detail}") from None
    rows = sorted(payload["data"], key=lambda item: item["index"])
    return [list(item["embedding"]) for item in rows]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
