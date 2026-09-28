"""#165:脱敏 PDF → 同构锚 → retrieve。样本不进主指标 n。"""

from pathlib import Path

from freshlatch.store.base import InMemoryStore
from freshlatch.store.pdf_anchor import pdf_to_document

PDF = Path("data/smoke/phase-a-smoke.pdf")
ANCHOR = "SMOKE-ANCHOR-165"


def test_smoke_pdf_ingests_and_retrieves():
    store = InMemoryStore()
    doc, chunks = pdf_to_document(PDF, doc_id="smoke-phase-a-165", title="Phase A synthetic smoke")
    assert doc.as_of == "T1"
    assert chunks and all(c.clause_id.startswith("p") for c in chunks)
    assert any(c.text.startswith("## p") for c in chunks)
    store.add_document(doc, chunks)
    hits = store.retrieve(ANCHOR, as_of="T1", top_k=10)
    assert any(ANCHOR in c.text for c in hits)
