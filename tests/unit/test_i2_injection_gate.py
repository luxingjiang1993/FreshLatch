"""I2 inj-t001:污染 T1 经 rule_gate / Runner._finalize 不得 fresh 绿灯。

层 = 确定性不变量(冒烟夹具,不是安全通过率)。零 LLM,不挂 meta_gate。
"""

from pathlib import Path

from freshlatch.gates.meta_gate import is_meta_only_disproof
from freshlatch.gates.rule_gate import (
    ERR_INDIRECT_INJECTION,
    GateContext,
    GateDecision,
    is_indirect_injection,
    rule_gate,
)
from freshlatch.models import Claim
from freshlatch.runner import ClaimDecision, Runner
from freshlatch.store.base import Chunk, Document, InMemoryStore

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "docs" / "evidence" / "i2" / "inj-t001.md"
DOC_ID = "inj-t001"
CLAUSE_ID = "p1"
EVIDENCE_ID = f"{DOC_ID}#{CLAUSE_ID}@T1"
CLEAN_TEXT = "2026 年第三季度渠道复盘:月活环比持平,未见口径变更。"


def _load_fixture() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def _claim() -> Claim:
    return Claim(claim_id="inj-c1", statement="目标市场月活环比上升",
                 t0_evidence_ids=["t0-channel#p1"])


def _ctx() -> GateContext:
    return GateContext(checksum_fn=lambda doc_id, as_of: None)


def _ingest(store: InMemoryStore, text: str, *, doc_id: str = DOC_ID) -> str:
    store.add_document(
        Document(doc_id=doc_id, as_of="T1", source_type="report", title=doc_id,
                 doc_version="v1", checksum="inj-fixture", full_text=text),
        [Chunk(doc_id=doc_id, chunk_id=f"{doc_id}-p1", clause_id=CLAUSE_ID,
               title=doc_id, text=text, source_type="report", as_of="T1",
               doc_version="v1", checksum="inj-fixture", tokens=max(1, len(text)))],
    )
    return f"{doc_id}#{CLAUSE_ID}@T1"


def test_inj_t001_fixture_loads_and_names_the_attack():
    """夹具在 docs/evidence/i2/,正文含预锁的诱绿语句。"""
    body = _load_fixture()
    assert FIXTURE.is_file()
    assert "inj-t001" in body
    assert "忽略指令" in body
    assert "标为 fresh" in body
    assert is_indirect_injection(body)


def test_rule_gate_refuses_fresh_on_injected_t1_text():
    """其它绿灯条件齐(有 T1 id、Auditor 判 fresh)仍不得因正文诱绿。"""
    body = _load_fixture()
    decision = GateDecision(status="fresh", t1_evidence_ids=[EVIDENCE_ID],
                            auditor_verdict="fresh", t1_evidence_texts=[body])
    result = rule_gate(_claim(), decision, _ctx())
    assert not result.allowed and not result.green
    assert result.error_code == ERR_INDIRECT_INJECTION
    assert not is_meta_only_disproof(body)


def test_rule_gate_clean_text_still_green():
    """无关正文不改既有绿灯语义。"""
    decision = GateDecision(status="fresh", t1_evidence_ids=[EVIDENCE_ID],
                            auditor_verdict="fresh", t1_evidence_texts=[CLEAN_TEXT])
    result = rule_gate(_claim(), decision, _ctx())
    assert result.allowed and result.green


def test_rule_gate_without_text_keeps_prior_fresh_path():
    """未带正文的旧调用点不启用注入拒绿。"""
    decision = GateDecision(status="fresh", t1_evidence_ids=[EVIDENCE_ID],
                            auditor_verdict="fresh")
    result = rule_gate(_claim(), decision, _ctx())
    assert result.green


def test_finalize_ingested_inj_t001_is_not_fresh():
    """已入库污染 T1 走 _finalize 绿灯出口,落档不得为 fresh。"""
    store = InMemoryStore()
    evidence_id = _ingest(store, _load_fixture())
    claim = _claim()
    decision = ClaimDecision(claim_id=claim.claim_id, status="fresh",
                             reason="正文要求直接标 fresh",
                             evidence_ids=[evidence_id],
                             auditor_verdict="fresh",
                             auditor_reason="按文档指令判 fresh")
    Runner(store, mode="eval")._finalize(claim, decision)
    assert claim.status != "fresh"
    assert claim.status == "unknown"
    assert ERR_INDIRECT_INJECTION in claim.reason


def test_finalize_clean_ingested_t1_can_still_be_fresh():
    """对照:干净 T1 入库后,同一绿灯出口仍可 fresh。"""
    store = InMemoryStore()
    evidence_id = _ingest(store, CLEAN_TEXT, doc_id="clean-t001")
    claim = _claim()
    decision = ClaimDecision(claim_id=claim.claim_id, status="fresh",
                             reason="T1 原文支持该主张",
                             evidence_ids=[evidence_id],
                             auditor_verdict="fresh",
                             auditor_reason="双判一致")
    Runner(store, mode="eval")._finalize(claim, decision)
    assert claim.status == "fresh"
