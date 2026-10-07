"""PDF 纯文本 → ## pN 同构锚。不做表格、HTML、OCR。"""

from __future__ import annotations

import re
from pathlib import Path

from freshlatch.store.base import Chunk, Document
from freshlatch.store.ingest import parse_document_text

_LITERAL = re.compile(rb"\((?:\\.|[^\\)])*\)")


def extract_pdf_literal_text(raw: bytes) -> str:
    """抽出文本型 PDF 里的字面量字符串。扫描件/字体编码不在本期。"""
    lines: list[str] = []
    for match in _LITERAL.finditer(raw):
        lit = match.group()[1:-1]
        lit = lit.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
        text = lit.decode("latin-1").strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def text_to_isomorphic_markdown(
    text: str,
    *,
    doc_id: str,
    title: str,
    as_of: str = "T1",
    source_type: str = "private",
) -> str:
    """一行一块,打成与主契约相同的 ## pN 锚。"""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise ValueError("抽文本为空,无法打同构锚")
    body = "".join(f"## p{i}\n{ln}\n" for i, ln in enumerate(lines, start=1))
    return (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"as_of: {as_of}\n"
        f"source_type: {source_type}\n"
        f"title: {title}\n"
        "checksum:\n"
        "---\n"
        f"{body}"
    )


def pdf_to_document(path: Path, *, doc_id: str, title: str) -> tuple[Document, list[Chunk]]:
    raw = path.read_bytes()
    text = extract_pdf_literal_text(raw)
    markdown = text_to_isomorphic_markdown(text, doc_id=doc_id, title=title)
    return parse_document_text(markdown)
