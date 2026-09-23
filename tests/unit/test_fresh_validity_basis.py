"""#150 / ADR-0024:runner fresh 构造 validity_basis list + 存量批迁。

主缝:Runner 组 GateDecision(fresh) 时由 t1_evidence_ids 按 doc_id 去重构造 list,
checksum=入库指纹;构造后进闸;不符不得 fresh;绿后写 claim.validity_basis。
非缝但必做:显式批迁 dict→一元 list,迁移后读路径只见 list。
不得升格为「checksum 已证明 latch」;禁改 gold;禁 checksum_fn 读库列。
"""

from __future__ import annotations

from freshlatch.models import Claim
from freshlatch.runner import ClaimDecision, Runner
from freshlatch.store.base import Chunk, Document, InMemoryStore


DOC_A = "doc-a"
DOC_B = "doc-b"
EID_A = f"{DOC_A}#p1@T1"
EID_B = f"{DOC_B}#p2@T1"
EID_A2 = f"{DOC_A}#p9@T1"  # 同 doc 第二锚,去重后仍一元


def _chunk(doc_id: str, clause_id: str, checksum: str) -> Chunk:
    return Chunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}-{clause_id}",
        clause_id=clause_id,
        title=doc_id,
        text=f"T1 正文 {doc_id}/{clause_id}",
        source_type="competitor",
        as_of="T1",
        doc_version="v1",
        checksum=checksum,
        tokens=10,
    )


def _seed(store: InMemoryStore, *chunks: Chunk) -> None:
    for c in chunks:
        store.add_document(
            Document(
                doc_id=c.doc_id, as_of=c.as_of, source_type=c.source_type,
                title=c.title, doc_version=c.doc_version, checksum=c.checksum,
                full_text=c.text,
            ),
            [c],
        )


def _finalize_fresh(
    store: InMemoryStore,
    evidence: list[str],
    *,
    checksum_fn=None,
) -> Claim:
    """Lead fresh × Auditor fresh → 落档;checksum_fn 默认对齐构造所用入库指纹(正例)。"""
    # 与 build_fresh_validity_basis 同口径:每 doc 取首次出现 chunk 的指纹
    fingerprints: dict[str, str] = {}
    for c in store._chunks:
        fingerprints.setdefault(c.doc_id, c.checksum)

    def default_fn(doc_id: str, as_of: str) -> str | None:
        return fingerprints.get(doc_id)

    runner = Runner(store, checksum_fn=checksum_fn or default_fn)
    claim = Claim(claim_id="c-fresh", statement="多证同构主张")
    decision = ClaimDecision(
        claim_id="c-fresh",
        status="fresh",
        reason="T1 多证支持",
        evidence_ids=evidence,
        auditor_verdict="fresh",
        auditor_reason="双判一致",
    )
    runner._finalize(claim, decision)
    return claim


def test_runner_fresh_builds_deduped_validity_basis_list():
    """多 doc evidence 按 doc_id 去重(保序)构造 list;绿后 claim 落同构 list。"""
    store = InMemoryStore()
    _seed(
        store,
        _chunk(DOC_A, "p1", "fp-a"),
        _chunk(DOC_A, "p9", "fp-a-other"),  # 同 doc 后出现,去重取首次
        _chunk(DOC_B, "p2", "fp-b"),
    )
    claim = _finalize_fresh(store, [EID_A, EID_B, EID_A2])
    assert claim.status == "fresh"
    assert claim.validity_basis == [
        {"doc_id": DOC_A, "checksum": "fp-a"},
        {"doc_id": DOC_B, "checksum": "fp-b"},
    ]


def test_runner_fresh_rejects_when_non_first_doc_checksum_mismatch():
    """篡改 list 中非首元现算 → CHECKSUM_MISMATCH,不得 fresh。"""
    store = InMemoryStore()
    _seed(store, _chunk(DOC_A, "p1", "fp-a"), _chunk(DOC_B, "p2", "fp-b"))

    def tamper_fn(doc_id: str, as_of: str) -> str | None:
        if doc_id == DOC_B:
            return "tampered-live"
        return "fp-a"

    claim = _finalize_fresh(store, [EID_A, EID_B], checksum_fn=tamper_fn)
    assert claim.status != "fresh"
    assert claim.status == "unknown"
    assert "CHECKSUM_MISMATCH" in claim.reason
    assert claim.validity_basis is None  # 闸打回零写 basis


def test_runner_fresh_unresolvable_evidence_not_empty_basis_green():
    """evidence 点不回 chunk → 显式不可构造,禁止空 basis 仍 fresh。"""
    store = InMemoryStore()
    # 只种 A,B 缺失
    _seed(store, _chunk(DOC_A, "p1", "fp-a"))
    claim = _finalize_fresh(store, [EID_A, EID_B])
    assert claim.status != "fresh"
    assert claim.validity_basis is None


def test_migrate_dict_basis_to_unary_list_no_dict_residual():
    """显式批迁:存量单对象 → 一元 list;迁移后读路径只见 list。"""
    from freshlatch.basis_migrate import migrate_claim_validity_basis, migrate_claims

    claim = Claim(
        claim_id="c-legacy",
        statement="历史续命",
        status="fresh",
        validity_basis={"doc_id": DOC_A, "checksum": "old-fp"},  # type: ignore[arg-type]
    )
    changed = migrate_claim_validity_basis(claim)
    assert changed is True
    assert claim.validity_basis == [{"doc_id": DOC_A, "checksum": "old-fp"}]
    assert isinstance(claim.validity_basis, list)

    already = Claim(
        claim_id="c-ok",
        statement="已是 list",
        validity_basis=[{"doc_id": DOC_B, "checksum": "x"}],
    )
    assert migrate_claim_validity_basis(already) is False
    assert already.validity_basis == [{"doc_id": DOC_B, "checksum": "x"}]

    none_claim = Claim(claim_id="c-none", statement="无 basis")
    assert migrate_claim_validity_basis(none_claim) is False
    assert none_claim.validity_basis is None

    batch = [
        Claim(claim_id="a", statement="a",
              validity_basis={"doc_id": "d1", "checksum": "c1"}),  # type: ignore[arg-type]
        Claim(claim_id="b", statement="b",
              validity_basis=[{"doc_id": "d2", "checksum": "c2"}]),
    ]
    n = migrate_claims(batch)
    assert n == 1
    for c in batch:
        if c.validity_basis is not None:
            assert isinstance(c.validity_basis, list)
            assert not isinstance(c.validity_basis, dict)
