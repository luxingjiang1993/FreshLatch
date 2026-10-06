"""x1 embedding 内容哈希缓存。

包一层 `embed_texts`，不改 embeddings.py，也不打开 `data/dense/index.sqlite`。
键含 model 与 dim：任一变化即不命中。维度不符的向量不落盘。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

from freshlatch.store.checksum import sha256_hex
from freshlatch.store.embeddings import embed_texts
from freshlatch.store.pipeline import pack_vec, unpack_vec

EMBED_CACHE_TABLE = "embed_cache"


def make_embed_cache_key(model: str, dim: int, text: str) -> str:
    """缓存键 = sha256(model + 换行 + dim + 换行 + text)。"""
    return sha256_hex((model + "\n" + str(dim) + "\n" + text).encode("utf-8"))


def embed_texts_cached(
    texts: list[str],
    *,
    dim: int,
    cache_path: Path | str,
    model: str,
    embed_fn: Callable[[list[str]], list[list[float]]] | None = None,
) -> list[list[float]]:
    """按文本顺序返回向量。命中不调用 embed_fn；未命中才调用。

    未命中结果先核对 `len(vec) == dim`，不符则报错且不写入该行。
    """
    if not texts:
        return []
    caller = embed_fn if embed_fn is not None else embed_texts
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {EMBED_CACHE_TABLE} ("
            "key TEXT PRIMARY KEY NOT NULL,"
            "vec BLOB NOT NULL"
            ")"
        )
        keys = [make_embed_cache_key(model, dim, text) for text in texts]
        found: dict[str, list[float]] = {}
        miss_keys: list[str] = []
        miss_texts: list[str] = []
        seen_miss: set[str] = set()
        for text, key in zip(texts, keys):
            if key in found or key in seen_miss:
                continue
            row = conn.execute(
                f"SELECT vec FROM {EMBED_CACHE_TABLE} WHERE key = ?",
                (key,),
            ).fetchone()
            if row is None:
                seen_miss.add(key)
                miss_keys.append(key)
                miss_texts.append(text)
            else:
                found[key] = unpack_vec(row[0])
        if miss_texts:
            new_vecs = caller(miss_texts)
            if len(new_vecs) != len(miss_texts):
                raise RuntimeError("向量条数与文本数不一致")
            for key, vec in zip(miss_keys, new_vecs):
                if len(vec) != dim:
                    raise ValueError(
                        f"嵌入维度不符: got {len(vec)} want {dim}"
                    )
                blob = pack_vec(vec)
                conn.execute(
                    f"INSERT INTO {EMBED_CACHE_TABLE} (key, vec) VALUES (?, ?)",
                    (key, blob),
                )
                conn.commit()
                # 冷启动也走 unpack，与热启动逐位一致
                found[key] = unpack_vec(blob)
        return [found[key] for key in keys]
    finally:
        conn.close()
