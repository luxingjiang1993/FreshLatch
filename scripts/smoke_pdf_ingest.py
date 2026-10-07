"""重建 #165 脱敏 PDF 冒烟:抽文本 → ## pN → ingest → retrieve。不进主指标 n。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from freshlatch.store.base import InMemoryStore
from freshlatch.store.pdf_anchor import pdf_to_document

PDF = ROOT / "data" / "smoke" / "phase-a-smoke.pdf"
DOC_ID = "smoke-phase-a-165"
ANCHOR = "SMOKE-ANCHOR-165"


def main() -> int:
    store = InMemoryStore()
    doc, chunks = pdf_to_document(PDF, doc_id=DOC_ID, title="Phase A synthetic smoke")
    store.add_document(doc, chunks)
    hits = store.retrieve(ANCHOR, as_of="T1", top_k=10)
    ok = any(ANCHOR in c.text and c.doc_id == DOC_ID for c in hits)
    print(f"chunks={len(chunks)} hits={len(hits)} anchor_hit={ok}")
    print("scope=smoke not_in_main_metric_n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
