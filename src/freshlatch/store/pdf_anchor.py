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


def build_text_pdf(lines: list[str]) -> bytes:
    """生成仅含 Helvetica 字面量的单页 PDF,供脱敏冒烟样本。"""

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    commands = ["BT", "/F1 12 Tf", "72 720 Td"]
    for i, line in enumerate(lines):
        if i:
            commands.append("0 -18 Td")
        commands.append(f"({esc(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        b"4 0 obj << /Length %d >> stream\n" % len(stream) + stream + b"\nendstream\nendobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    header = b"%PDF-1.4\n"
    parts = [header]
    offsets = [0]
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        parts.append(obj)
        cursor += len(obj)
    xref_pos = cursor
    xref = [b"xref\n", f"0 {len(offsets)}\n".encode("ascii"), b"0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode("ascii"))
    trailer = (
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode("ascii")
    return b"".join(parts + xref) + trailer
