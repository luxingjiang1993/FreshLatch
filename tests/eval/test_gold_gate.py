"""gold.json 直接驱动规则闸(§2.7 验收三:金标就是测试数据,一份两用)。"""

import json
from pathlib import Path

import pytest

from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import Claim

GOLD = json.loads(Path("data/eval/gold.json").read_text(encoding="utf-8"))


def ctx() -> GateContext:
    return GateContext(checksum_fn=lambda doc_id, as_of: None)


@pytest.mark.parametrize("cid", GOLD["must_stale"])
def test_must_stale_never_green(cid):
    """must_stale:任何 fresh 请求(带不带 T1 证据)都不得发绿。"""
    claim = Claim(claim_id=cid, statement="x", t0_evidence_ids=[])
    no_ev = rule_gate(claim, GateDecision(status="fresh", t1_evidence_ids=[]), ctx())
    assert not no_ev.green and no_ev.error_code == "NO_T1_EVIDENCE"
    # ADR-0009 双判一致:Auditor 缺席不构成任何绿格(fail-closed)
    no_aud = rule_gate(claim, GateDecision(status="fresh", t1_evidence_ids=["t0-x#p2"]), ctx())
    assert not no_aud.green and no_aud.error_code == "AUDITOR_ABSENT"
    with_ev = rule_gate(claim, GateDecision(status="fresh", t1_evidence_ids=["t0-x#p2"],
                                            auditor_verdict="fresh"), ctx())
    # 机械闸只查不变量、不查语义:伪造 T1 证据在闸层无法识别(纯函数零 I/O)。
    # 「must_stale 必须被判 stale」是语义层判据,由金标 runner(T10)判定,不在闸内。
    assert with_ev.green


@pytest.mark.parametrize("cid", GOLD["must_unknown"])
def test_must_unknown_never_green_without_t1(cid):
    """must_unknown:T1 无原文覆盖 → 无 t1_evidence_ids → 不得 fresh。"""
    claim = Claim(claim_id=cid, statement="x", t0_evidence_ids=[])
    r = rule_gate(claim, GateDecision(status="fresh", t1_evidence_ids=[]), ctx())
    assert not r.green and r.error_code == "NO_T1_EVIDENCE"


@pytest.mark.parametrize("cid", GOLD["must_fresh"])
def test_must_fresh_green_path_ok(cid):
    """must_fresh:携带 T1 证据 + Auditor 双判一致的 fresh 请求机械过闸(语义由 runner 判)。"""
    claim = Claim(claim_id=cid, statement="x", t0_evidence_ids=[])
    r = rule_gate(claim, GateDecision(status="fresh", t1_evidence_ids=["t0-x#p2"],
                                      auditor_verdict="fresh"), ctx())
    assert r.green


def test_gold_partition_complete():
    """金标分桶完整性:12 条主张 × 三档 + quarantine 占位在位。"""
    all_ids = GOLD["must_stale"] + GOLD["must_fresh"] + GOLD["must_unknown"]
    assert sorted(all_ids, key=lambda c: int(c[1:])) == [f"c{i}" for i in range(1, 13)]
    assert len(set(all_ids)) == 12
    assert GOLD["must_quarantine"] == []
    for cid in GOLD["must_stale"]:
        assert cid in GOLD["causal_chain"], f"{cid} 缺 causal_chain 登记"
