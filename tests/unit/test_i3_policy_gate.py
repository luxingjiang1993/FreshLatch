"""I3 #249：Policy-as-code thin · 出处禁区旁路（政策拒 ≠ 新鲜度拒）。

零 LLM。不改 rule_gate 不变量正文；经 apply_policy_after_rule_gate 组合。
"""

from __future__ import annotations

from pathlib import Path

from freshlatch.gates.policy_gate import (
    ERR_POLICY_SOURCE_BAN,
    PolicyContext,
    apply_policy_after_rule_gate,
    apply_policy_gate,
    extract_provenance_refs,
    load_policy_rules,
)
from freshlatch.gates.rule_gate import GateContext, GateDecision, GateResult, rule_gate
from freshlatch.models import Claim
from freshlatch.runner import ClaimDecision, Runner
from freshlatch.store.base import Chunk, Document, InMemoryStore

ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / "data" / "policy" / "source_ban.json"
FIXTURE_DOC = ROOT / "docs" / "evidence" / "i3" / "policy-source-ban.md"
BANNED_URL = "https://banned.example/reports/q3.pdf"
CLEAN_URL = "https://www.mckinsey.com/reports/ok.pdf"
BANNED_DOC = "banned-source-demo"
CLEAN_DOC = "clean-source-demo"
BANNED_EVIDENCE = f"{BANNED_DOC}#p1@T1"
CLEAN_EVIDENCE = f"{CLEAN_DOC}#p1@T1"


def _rules():
    return load_policy_rules(RULES)


def _claim(cid: str = "pol-c1") -> Claim:
    return Claim(claim_id=cid, statement="渠道月活环比上升",
                 t0_evidence_ids=["t0-channel#p1"])


def _ingest(store: InMemoryStore, *, doc_id: str, text: str) -> str:
    store.add_document(
        Document(doc_id=doc_id, as_of="T1", source_type="report", title=doc_id,
                 doc_version="v1", checksum="pol-fixture", full_text=text),
        [Chunk(doc_id=doc_id, chunk_id=f"{doc_id}-p1", clause_id="p1",
               title=doc_id, text=text, source_type="report", as_of="T1",
               doc_version="v1", checksum="pol-fixture", tokens=max(1, len(text)))],
    )
    return f"{doc_id}#p1@T1"


def test_load_declarative_source_ban_rules():
    """声明式 JSON 可加载；至少含出处域名/路径模式。"""
    rules = _rules()
    assert rules.version == "1"
    assert rules.rules
    source_bans = [r for r in rules.rules if r.kind == "source_ban"]
    assert source_bans
    patterns = set()
    for r in source_bans:
        patterns.update(r.patterns)
    assert "banned.example" in patterns
    assert any("leaked-internal" in p for p in patterns)


def test_fixture_doc_states_policy_ne_freshness():
    """夹具文档标明政策拒 ≠ 新鲜度拒。"""
    body = FIXTURE_DOC.read_text(encoding="utf-8")
    assert "政策拒" in body
    assert "新鲜度拒" in body
    assert "POLICY_SOURCE_BAN" in body


def test_source_ban_hit_is_policy_reject_not_green():
    """命中出处禁区 → 政策拒码可见、不得绿灯。"""
    result = apply_policy_gate(
        PolicyContext(provenance=[BANNED_URL]),
        _rules(),
    )
    assert not result.allowed and not result.green
    assert result.error_code == ERR_POLICY_SOURCE_BAN
    assert "政策拒" in result.reason
    assert "新鲜度拒" in result.reason


def test_path_pattern_ban_hits():
    """路径模式 */leaked-internal/* 命中。"""
    result = apply_policy_gate(
        PolicyContext(provenance=["https://ok.example/leaked-internal/memo.pdf"]),
        _rules(),
    )
    assert result.error_code == ERR_POLICY_SOURCE_BAN


def test_miss_does_not_block():
    """未命中禁区 → 旁路放行。"""
    result = apply_policy_gate(
        PolicyContext(provenance=[CLEAN_URL, CLEAN_DOC]),
        _rules(),
    )
    assert result.allowed and result.green


def test_combine_after_rule_gate_blocks_green():
    """rule_gate 已绿时政策旁路仍可拒；不改 rule_gate 谓词。"""
    green = GateResult(allowed=True, green=True, reason="过闸:绿灯")
    blocked = apply_policy_after_rule_gate(
        green, provenance=[BANNED_URL], rules=_rules(),
    )
    assert not blocked.green
    assert blocked.error_code == ERR_POLICY_SOURCE_BAN


def test_combine_skips_when_rule_gate_already_red():
    """规则闸已非绿时政策旁路不改写原错误码。"""
    red = GateResult(allowed=False, green=False, error_code="NO_T1_EVIDENCE",
                     reason="无 t1")
    out = apply_policy_after_rule_gate(red, provenance=[BANNED_URL], rules=_rules())
    assert out.error_code == "NO_T1_EVIDENCE"


def test_rule_gate_invariants_still_green_without_policy():
    """既有应绿路径：rule_gate 本身未改语义（无政策上下文时仍绿）。"""
    decision = GateDecision(
        status="fresh",
        t1_evidence_ids=[CLEAN_EVIDENCE],
        auditor_verdict="fresh",
        t1_evidence_texts=["干净出处正文，无禁区域名。"],
    )
    result = rule_gate(_claim(), decision, GateContext())
    assert result.green


def test_finalize_banned_provenance_not_fresh():
    """已入库禁区出处 T1：_finalize 绿灯出口旁路不得 fresh。"""
    store = InMemoryStore()
    text = f"来源声明 source_url: {BANNED_URL}\n月活环比上升。"
    eid = _ingest(store, doc_id=BANNED_DOC, text=text)
    claim = _claim()
    decision = ClaimDecision(
        claim_id=claim.claim_id,
        status="fresh",
        reason="证据新且支持",
        evidence_ids=[eid],
        auditor_verdict="fresh",
        auditor_reason="同意 fresh",
    )
    Runner(store, mode="eval")._finalize(claim, decision)
    assert claim.status != "fresh"
    assert ERR_POLICY_SOURCE_BAN in (claim.reason or "")


def test_finalize_clean_provenance_still_fresh():
    """未命中禁区：既有应绿夹具行为与改前一致。"""
    store = InMemoryStore()
    text = f"来源声明 source_url: {CLEAN_URL}\n月活环比上升。"
    eid = _ingest(store, doc_id=CLEAN_DOC, text=text)
    claim = _claim("pol-clean")
    decision = ClaimDecision(
        claim_id=claim.claim_id,
        status="fresh",
        reason="证据新且支持",
        evidence_ids=[eid],
        auditor_verdict="fresh",
        auditor_reason="同意 fresh",
    )
    Runner(store, mode="eval")._finalize(claim, decision)
    assert claim.status == "fresh"


def test_extract_provenance_from_evidence_and_urls():
    refs = extract_provenance_refs(
        evidence_ids=[BANNED_EVIDENCE],
        texts=[f"见 {BANNED_URL} 附件"],
    )
    assert BANNED_DOC in refs
    assert BANNED_EVIDENCE in refs
    assert any("banned.example" in r for r in refs)
