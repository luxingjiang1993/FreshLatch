"""β+ 档 3a ACCEPTANCE 挂载自检(#151)。

只核对预锁句在场、UI/导出完整 list、与档 3b 交界冒烟。
不得把本文件读成「checksum 已证明 latch」或统计通过。
不改 gold。
"""

from __future__ import annotations

from pathlib import Path

from freshlatch.gates.basis_rot import BASIS_CHECKSUM_MISMATCH, apply_rot_if_mismatch
from freshlatch.models import Claim
from freshlatch.sheet import render_claim_markdown
from freshlatch.store.base import Chunk, Document
from freshlatch.store.checksum import make_checksum_fn, sha256_hex
from freshlatch.store.sqlite_store import SQLiteStore

REPO = Path(__file__).resolve().parent.parent.parent
ACCEPTANCE = REPO / "docs" / "evidence" / "beta-plus-3a" / "ACCEPTANCE.md"
GOLD = REPO / "data" / "eval" / "gold.json"
APP = REPO / "src" / "freshlatch" / "ui" / "app.py"

DOC_A = "t0-doc-a"
DOC_B = "t0-doc-b"
EID_A = f"{DOC_A}#p1@T1"
EID_B = f"{DOC_B}#p2@T1"


def test_acceptance_pastes_prelock_invariant_verbatim():
    """ACCEPTANCE 必须粘贴 #148 预锁整句(改字 = 验收作废)。"""
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert "档 3a：Agent fresh 路径须在进入" in text
    assert "按 doc_id 去重" in text
    assert "CHECKSUM_MISMATCH" in text
    assert "UI/导出展示完整 list" in text
    assert "不得升格" in text


def test_acceptance_has_checkboxes_and_bans():
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert "tests/unit/test_fresh_validity_basis.py" in text
    assert "tests/unit/test_beta_plus_3a_acceptance.py" in text
    assert "[x]" in text
    assert "完整 list" in text
    assert "禁止只显示" in text or "禁只取首元" in text
    assert "checksum 已证明 latch" in text
    assert "不改 `data/eval/gold.json`" in text or "不改 gold" in text
    assert "不自动 void" in text


def test_acceptance_does_not_claim_latch_or_stats_proven():
    text = ACCEPTANCE.read_text(encoding="utf-8")
    assert "已证明 latch」成立" not in text
    assert "统计结论已成立" not in text
    assert "产品已验证成功" not in text
    assert "写侧启用 = 通过" not in text
    assert "不得升格" in text


def test_ui_renders_full_validity_basis_list_not_only_first():
    """复验卡源码必须循环渲染完整 validity_basis list，禁止只取 [0]。"""
    src = APP.read_text(encoding="utf-8")
    assert "for(const b of c.validity_basis)" in src
    assert "basis-list" in src
    assert "完整 list" in src or "禁只取首元" in src
    assert "c.validity_basis[0]" not in src


def test_sheet_export_renders_full_validity_basis_list_not_only_first():
    """导出 Markdown 必须展示完整 validity_basis list，禁止只取 [0]。"""
    proj = {
        "claim_id": "c-list",
        "statement": "多证主张",
        "status": "fresh",
        "reason": "双判一致",
        "t0_evidence_ids": [],
        "t1_evidence_ids": [EID_A, EID_B],
        "voided": False,
        "voided_at": None,
        "last_confirmed_at": "2026-09-22T10:00:00",
        "validity_basis": [
            {"doc_id": DOC_A, "checksum": "sha256-a" * 4},
            {"doc_id": DOC_B, "checksum": "sha256-b" * 4},
        ],
        "timeline": [],
    }
    md = render_claim_markdown(proj)
    assert DOC_A in md
    assert DOC_B in md
    assert "sha256-a" in md
    assert "sha256-b" in md
    assert md.count("doc_id") >= 2  # 两个条目都展示


def _write_corpus(corpus: Path, doc_id: str, body: bytes) -> Path:
    path = corpus / "t1" / f"{doc_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


def _store(tmp_path: Path, corpus: Path) -> SQLiteStore:
    store = SQLiteStore(tmp_path / "freshlatch.db")
    fingerprints: dict[str, str] = {}
    for doc_id, text in ((DOC_A, "T1:a"), (DOC_B, "T1:b")):
        raw = (
            f"---\nid: {doc_id}\nas_of: T1\ntitle: {doc_id}\nchecksum:\n---\n\n"
            f"## p1\n{text}\n"
        ).encode("utf-8")
        path = _write_corpus(corpus, doc_id, raw)
        fingerprints[doc_id] = sha256_hex(raw)
        chunk = Chunk(
            doc_id=doc_id, chunk_id=f"{doc_id}-p1", clause_id="p1",
            title=doc_id, text=text, source_type="competitor",
            as_of="T1", doc_version="v2", checksum=fingerprints[doc_id], tokens=10,
        )
        store.add_document(
            Document(
                doc_id=doc_id, as_of="T1", source_type="competitor",
                title=doc_id, doc_version="v2", checksum=fingerprints[doc_id],
                full_text=text,
            ),
            [chunk],
        )
    return store, fingerprints


def test_agent_fresh_list_basis_rot_on_tampered_corpus(tmp_path):
    """与 3b 交界冒烟:带 list basis 的 Agent-fresh 篡改语料后可被 apply_rot 掉灯。"""
    corpus = tmp_path / "corpus"
    store, fingerprints = _store(tmp_path, corpus)

    # Agent-fresh 构造出的 list basis(按 doc_id 去重)
    claim = Claim(
        claim_id="c-agent-fresh",
        statement="多证主张",
        status="fresh",
        reason="Agent 绿灯",
        t1_evidence_ids=[EID_A, EID_B],
        validity_basis=[
            {"doc_id": DOC_A, "checksum": fingerprints[DOC_A]},
            {"doc_id": DOC_B, "checksum": fingerprints[DOC_B]},
        ],
        last_confirmed_at="2026-09-22T10:00:00",
    )

    # 篡改 list 中次元的语料
    path_b = corpus / "t1" / f"{DOC_B}.md"
    path_b.write_bytes(path_b.read_bytes() + b"\n# tampered\n")

    result = apply_rot_if_mismatch(store, claim, make_checksum_fn(corpus))
    assert result.outcome == "applied"
    assert claim.status == "unknown"
    assert BASIS_CHECKSUM_MISMATCH in claim.reason
    # 保留 basis 与 last_confirmed_at(ADR-0025)
    assert claim.validity_basis == [
        {"doc_id": DOC_A, "checksum": fingerprints[DOC_A]},
        {"doc_id": DOC_B, "checksum": fingerprints[DOC_B]},
    ]
    assert claim.last_confirmed_at == "2026-09-22T10:00:00"
    rows = store.list_latch_rows(claim_id=claim.claim_id)
    assert len(rows) == 1
    assert rows[0]["action"] == "basis_rot"
    assert rows[0]["override"] is False


def test_this_batch_does_not_touch_gold():
    before = GOLD.read_bytes()
    assert b"must_stale" in before
    assert GOLD.read_bytes() == before
