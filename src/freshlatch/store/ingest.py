"""语料 ingestion:解析双镜像 markdown(元数据头 + ## pN 锚点)→ Document + Chunk。

结构感知分块:按 `## ` 标题切块,一块一个条款级锚点,切块确定(金标复现优先,§2.3)。
"""

from __future__ import annotations

import re
from pathlib import Path

from freshlatch.models import AsOf
from freshlatch.store.base import Chunk, Document
from freshlatch.store.pipeline import tokenize

META_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
CLAUSE_RE = re.compile(r"^## (p\d+)\s*$", re.MULTILINE)
AS_OF_DIR = {"t0": "T0", "t1": "T1"}


def parse_document(path: Path) -> tuple[Document, list[Chunk]]:
    text = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = text
    m = META_RE.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        body = text[m.end():]

    doc_id = meta["doc_id"]
    as_of = meta["as_of"]  # 目录即 as_of 维度,下方断言兜底一致性
    source_type = meta["source_type"]
    title = meta.get("title", doc_id)
    checksum = meta.get("checksum", "")  # 三处留位之一,本期为空

    # 按二级标题切分,锚点 = 标题文本(p2 等)
    parts = CLAUSE_RE.split(body)
    head = parts[0].strip()  # 元数据头之后、首个 ## 之前的引言(若有)
    chunks: list[Chunk] = []
    idx = 1
    while idx + 1 < len(parts) + 1 and idx < len(parts):
        clause_id = parts[idx].strip()
        chunk_text = parts[idx + 1].strip() if idx + 1 < len(parts) else ""
        full = f"## {clause_id}\n{chunk_text}"
        chunks.append(
            Chunk(
                doc_id=doc_id,
                chunk_id=f"{doc_id}::chunk-{clause_id}@{as_of}",  # chunk_id 含快照,双镜像主键不冲突
                clause_id=clause_id,
                title=title,
                text=full,
                source_type=source_type,
                as_of=as_of,
                doc_version="1.0",
                checksum=checksum,
                tokens=len(tokenize(full)),
            )
        )
        idx += 2

    doc = Document(
        doc_id=doc_id, as_of=as_of, source_type=source_type, title=title,
        doc_version="1.0", checksum=checksum, full_text=text,
    )
    return doc, chunks


def load_corpus(corpus_root: Path) -> list[tuple[Document, list[Chunk]]]:
    """corpus_root 下 t0/ 与 t1/ 两个镜像目录,目录本身即 as_of 维度。"""
    out: list[tuple[Document, list[Chunk]]] = []
    for as_of_dir, as_of in AS_OF_DIR.items():
        for path in sorted((corpus_root / as_of_dir).glob("*.md")):
            doc, chunks = parse_document(path)
            assert doc.as_of == as_of, f"{path}: 元数据头 as_of={doc.as_of} 与目录 {as_of_dir}/ 不一致"
            out.append((doc, chunks))
    return out


def ingest_into(store, corpus_root: Path) -> int:
    """全量入库,返回 chunk 总数。重复执行幂等(PRIMARY KEY + INSERT OR REPLACE)。"""
    total = 0
    for doc, chunks in load_corpus(corpus_root):
        store.add_document(doc, chunks)
        total += len(chunks)
    return total
