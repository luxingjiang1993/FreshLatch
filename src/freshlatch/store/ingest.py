"""语料 ingestion:解析双镜像 markdown(元数据头 + ## pN 锚点)→ Document + Chunk。

结构感知分块:按 `## ` 标题切块,一块一个条款级锚点,切块确定(金标复现优先,§2.3)。
"""

from __future__ import annotations

import re
from pathlib import Path

from freshlatch.store.base import Chunk, Document, normalize_tenant_id
from freshlatch.store.checksum import sha256_hex
from freshlatch.store.pipeline import tokenize

# 容许 CRLF(Windows checkout / CI 偶发);解析前归一化为 \n
META_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
CLAUSE_RE = re.compile(r"^## (p\d+)\s*$", re.MULTILINE)
AS_OF_DIR = {"t0": "T0", "t1": "T1"}


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _meta_flag(value: str | None) -> bool:
    """frontmatter 显式布尔。缺省或非真值视为未标记,不扫描正文。"""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y"}


def parse_document_text(
    text: str,
    *,
    checksum: str | None = None,
) -> tuple[Document, list[Chunk]]:
    """从 markdown 正文解析 Document + Chunk(与磁盘文件同构)。

    checksum 缺省时对 UTF-8 编码后的正文现算 sha256(粘贴/内存路径);
    磁盘路径请走 parse_document,以文件原始字节为权威指纹(ADR-0017)。
    """
    text = _normalize_newlines(text)
    if checksum is None:
        checksum = sha256_hex(text.encode("utf-8"))
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
    tenant_id = normalize_tenant_id(meta.get("tenant_id"))
    poison = _meta_flag(meta.get("poison"))
    untrusted = _meta_flag(meta.get("untrusted"))

    # 按二级标题切分,锚点 = 标题文本(p2 等);引言(首个 ## 之前)不入块
    parts = CLAUSE_RE.split(body)
    chunks: list[Chunk] = []
    for i in range(1, len(parts) - 1, 2):
        clause_id = parts[i].strip()
        chunk_text = parts[i + 1].strip()
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
                tenant_id=tenant_id,
                poison=poison,
                untrusted=untrusted,
            )
        )

    doc = Document(
        doc_id=doc_id, as_of=as_of, source_type=source_type, title=title,
        doc_version="1.0", checksum=checksum, full_text=text,
        tenant_id=tenant_id, poison=poison, untrusted=untrusted,
    )
    return doc, chunks


def parse_document(path: Path) -> tuple[Document, list[Chunk]]:
    """读语料文件:权威 checksum = 文件字节 sha256(弃 frontmatter 手填)。

    解析前把正文换行归一化为 \\n,避免 CRLF 导致 frontmatter 匹配失败;
    指纹仍对磁盘原始字节现算(与 checksum_fn 同口径)。
    """
    raw = path.read_bytes()
    checksum = sha256_hex(raw)
    text = raw.decode("utf-8")
    return parse_document_text(text, checksum=checksum)


def wrap_paste_as_t1_markdown(
    text: str,
    *,
    doc_id: str = "paste-change",
    title: str = "粘贴变更要点",
) -> str:
    """把职人粘贴的变更要点包成可 ingest 的 T1 markdown。

    若正文已含 ``## pN`` 条款头则原样保留切块;否则整段落入 ``## p1``。
    """
    body = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not CLAUSE_RE.search(body):
        body = f"## p1\n{body}\n"
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        "as_of: T1\n"
        "source_type: private\n"
        f"title: {title}\n"
        "checksum:\n"
        "---\n"
        f"{body}\n"
    )


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
