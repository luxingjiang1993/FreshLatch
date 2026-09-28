"""#169 V1 顾问报告样例包（McK SoAI）主缝。

验收层：样例包可引用（主张清单 + T0/T1 摘录 + 出处元数据）；
文档钉「单一垂直 = 顾问报告」；仓内无整本 McKinsey PDF。
不升格为第二产品垂直；不改 thesis-1 / QuoteTTL 金标。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.packs import repo_root

PACK_ID = "v1-mck-soai"
PACK_DIR = repo_root() / "data" / "packs" / PACK_ID
FOCUS_SIX = {
    "competitor_pricing",
    "regulatory_stance",
    "interview_reversal",
    "cost_model",
    "market_structure",
    "tech_ecosystem",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_pack_directory_exists_with_required_files():
    assert PACK_DIR.is_dir(), f"缺少样例包目录: {PACK_DIR}"
    for name in ("README.md", "docket.json", "provenance.json"):
        assert (PACK_DIR / name).is_file(), f"缺少 {name}"
    assert (PACK_DIR / "corpus" / "t0").is_dir()
    assert (PACK_DIR / "corpus" / "t1").is_dir()


def test_claims_list_points_to_t0_excerpts_and_dimensions():
    docket = _load(PACK_DIR / "docket.json")
    assert "顾问" in docket["question"] or "State of AI" in docket["question"]
    claims = docket["claims"]
    assert len(claims) >= 3
    for claim in claims:
        assert claim["claim_id"].startswith("mck-")
        assert claim["statement"].strip()
        assert claim["dimension"] in FOCUS_SIX
        assert claim["t0_evidence_ids"], claim["claim_id"]
        for eid in claim["t0_evidence_ids"]:
            doc_id, anchor = eid.split("#", 1)
            t0 = PACK_DIR / "corpus" / "t0" / f"{doc_id}.md"
            assert t0.is_file(), f"缺少 T0 摘录: {t0}"
            text = t0.read_text(encoding="utf-8")
            assert f"## {anchor}" in text


def test_each_claim_has_provenance_url_and_date():
    docket = _load(PACK_DIR / "docket.json")
    provenance = _load(PACK_DIR / "provenance.json")
    sources = provenance["sources"]
    assert sources
    for claim in docket["claims"]:
        cid = claim["claim_id"]
        meta = provenance["claims"][cid]
        source_id = meta["source_id"]
        src = sources[source_id]
        assert src["url"].startswith("https://www.mckinsey.com/")
        assert src["as_of_date"]  # YYYY-MM-DD
        assert len(src["as_of_date"]) == 10
        assert meta.get("excerpt_wave") in {"T0", "T1"}


def test_t0_and_t1_excerpt_frontmatter_has_source_metadata():
    for wave in ("t0", "t1"):
        files = list((PACK_DIR / "corpus" / wave).glob("*.md"))
        assert files, f"{wave} 无摘录 md"
        for path in files:
            text = path.read_text(encoding="utf-8")
            assert text.startswith("---")
            header = text.split("---", 2)[1]
            assert "doc_id:" in header
            assert "as_of:" in header
            assert "source_url:" in header
            assert "source_date:" in header
            assert "https://www.mckinsey.com/" in header
            assert "## p1" in text
            # 摘录块，非整本镜像声明
            assert "摘录" in text or "excerpt" in text.lower()


def test_no_full_mckinsey_pdf_corpus_in_repo():
    root = repo_root()
    pdfs = list(root.rglob("*.pdf"))
    banned = []
    for path in pdfs:
        rel = path.relative_to(root).as_posix().lower()
        name = path.name.lower()
        if "mckinsey" in rel or "mck" in name or "state-of-ai" in name or "state_of_ai" in name:
            banned.append(rel)
        if "soai" in name and path.stat().st_size > 100_000:
            banned.append(rel)
    assert banned == [], f"禁止提交整本 McKinsey PDF 语料: {banned}"
    # 样例包目录下不得有任何 pdf
    pack_pdfs = list(PACK_DIR.rglob("*.pdf"))
    assert pack_pdfs == [], f"样例包内不得含 PDF: {pack_pdfs}"


def test_readme_and_product_docs_nail_advisor_vertical():
    root = repo_root()
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "单一垂直" in readme
    assert "顾问报告" in readme
    # thesis-1 / QuoteTTL 不算第二垂直
    pack_readme = (PACK_DIR / "README.md").read_text(encoding="utf-8")
    assert "顾问报告" in pack_readme
    assert "McKinsey" in pack_readme or "McK" in pack_readme
    assert "整本" in pack_readme or "PDF" in pack_readme

    product_hits = []
    for path in (root / "docs" / "product").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "顾问报告" in text and ("单一垂直" in text or "近端唯一" in text or "唯一垂直" in text):
            product_hits.append(path.name)
    assert product_hits, "docs/product/ 须可见「顾问报告」为近端唯一垂直"

    context = (root / "CONTEXT.md").read_text(encoding="utf-8")
    assert "顾问报告" in context
    assert "单一" in context or "唯一" in context


def test_pack_not_registered_as_second_active_pack_vertical():
    """V1 样例包可引用，但不挤进 KNOWN_PACK_IDS 冒充第二 active_pack 垂直。"""
    from freshlatch.packs import KNOWN_PACK_IDS, P1_PACK_ID, DEFAULT_PACK_ID

    assert KNOWN_PACK_IDS == (DEFAULT_PACK_ID, P1_PACK_ID)
    assert PACK_ID not in KNOWN_PACK_IDS
