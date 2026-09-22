"""语料 checksum 现算(ADR-0017 / Batch 2 档 2)。

权威源 = 语料文件字节的 sha256,禁止读 store 内 chunks/documents.checksum 库列
(套套逻辑 = 假激活)。ingest 与 checksum_fn 必须同口径。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable


def sha256_hex(data: bytes) -> str:
    """原始字节 → 小写 hex sha256。"""
    return hashlib.sha256(data).hexdigest()


def corpus_doc_path(corpus_root: Path, doc_id: str, as_of: str) -> Path:
    """`data/corpus/{t0|t1}/{doc_id}.md`;as_of 接受 T0/T1 或 t0/t1。"""
    return Path(corpus_root) / str(as_of).lower() / f"{doc_id}.md"


def sha256_corpus_file(corpus_root: Path, doc_id: str, as_of: str) -> str | None:
    """对语料文件现算 sha256;文件不存在返回 None(闸侧视为未启用/无法比对)。"""
    path = corpus_doc_path(corpus_root, doc_id, as_of)
    if not path.is_file():
        return None
    return sha256_hex(path.read_bytes())


def make_checksum_fn(corpus_root: Path) -> Callable[[str, str], str | None]:
    """生产 renew 注入点:只读语料文件现算,绝不读库列。

    本函数不得升格为「checksum 已证明 latch」——仅机械一致性闸牙(ADR-0017)。
    """
    root = Path(corpus_root)

    def checksum_fn(doc_id: str, as_of: str) -> str | None:
        return sha256_corpus_file(root, doc_id, as_of)

    return checksum_fn
