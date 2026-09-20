"""混淆矩阵与点回/反证机器判据单测(gate 1,零 LLM,InMemoryStore)。"""

from freshlatch.eval.checks import (
    check_counterevidence,
    check_point_back,
    expected_evidence_id,
    parse_evidence_id,
)
from freshlatch.eval.matrix import BUCKETS, MISSING, confusion_matrix
from freshlatch.store.base import Chunk, Document, InMemoryStore

GOLD = {
    "must_stale": ["c1"],
    "must_fresh": ["c4"],
    "must_unknown": ["c9"],
    "causal_chain": {
        "c1": {"t1_doc": "doc-a", "anchor": "p2", "change": "x", "why_stale": "y"},
        "c4": {"t1_doc": "doc-b", "anchor": "p3", "change": "x", "why_fresh": "y"},
    },
}


def _store() -> InMemoryStore:
    store = InMemoryStore()
    for doc_id, clause, as_of in (("doc-a", "p2", "T1"), ("doc-b", "p3", "T1"), ("doc-a", "p1", "T0")):
        chunk = Chunk(doc_id=doc_id, chunk_id=f"{doc_id}-{clause}", clause_id=clause,
                      title="t", text="原文", source_type="public", as_of=as_of,
                      doc_version="v1", checksum="", tokens=1)
        doc = Document(doc_id=doc_id, as_of=as_of, source_type="public", title="t",
                       doc_version="v1", checksum="", full_text="原文")
        store.add_document(doc, [chunk])
    return store


# -- 混淆矩阵 ---------------------------------------------------------------


def test_matrix_all_hit():
    m = confusion_matrix(GOLD, {"c1": "stale", "c4": "fresh", "c9": "unknown"})
    assert m.all_hit and m.total == 3
    assert m.hits == {"must_stale": 1, "must_fresh": 1, "must_unknown": 1}
    assert not any(m.misses.values())


def test_matrix_counts_by_verdict():
    m = confusion_matrix(GOLD, {"c1": "fresh", "c4": "stale", "c9": "stale"})
    assert m.counts["must_stale"]["fresh"] == ["c1"]
    assert m.counts["must_fresh"]["stale"] == ["c4"]
    assert m.misses["must_stale"][0] == {"claim_id": "c1", "predicted": "fresh", "expected": "stale"}


def test_matrix_missing_counted_as_miss():
    m = confusion_matrix(GOLD, {"c1": "stale"})
    assert m.misses["must_fresh"][0]["predicted"] == MISSING
    assert not m.all_hit


def test_matrix_buckets_cover_all_claims():
    m = confusion_matrix(GOLD, {})
    assert m.total == 3


# -- evidence_id 解析与点回 ---------------------------------------------------


def test_parse_evidence_id():
    assert parse_evidence_id("doc-a#p2@T1") == ("doc-a", "p2", "T1")
    assert parse_evidence_id("no-anchor@T1") is None
    assert parse_evidence_id("doc#p2@T2") is None
    assert parse_evidence_id("garbage") is None


def test_point_back_resolvable():
    store = _store()
    res = check_point_back(store, ["doc-a#p2@T1", "doc-a#p9@T1"])
    assert res == {"doc-a#p2@T1": True, "doc-a#p9@T1": False}


def test_expected_id_from_causal_chain():
    assert expected_evidence_id(GOLD, "c1") == "doc-a#p2@T1"
    assert expected_evidence_id(GOLD, "c9") is None  # must_unknown 无登记,天然豁免


# -- J2 有效反证机器判据 -------------------------------------------------------


def test_counterevidence_machine_valid():
    store = _store()
    r = check_counterevidence(store, GOLD, "c1", "doc-a 原文:竞品已降价,推翻价格优势前提",
                              ["doc-a#p2@T1"])
    assert r["pointable"] and r["anchor_aligned"] and r["valid_machine"]
    assert r["causal_sentence_proxy"]  # reason 提及 t1_doc(代理判据)


def test_counterevidence_wrong_anchor_not_aligned():
    store = _store()
    r = check_counterevidence(store, GOLD, "c1", "doc-a 原文推翻前提", ["doc-b#p3@T1"])
    assert r["pointable"] and not r["anchor_aligned"] and not r["valid_machine"]


def test_counterevidence_unpointable():
    store = _store()
    r = check_counterevidence(store, GOLD, "c1", "doc-a 原文推翻前提", ["doc-a#p9@T1"])
    assert not r["pointable"] and not r["valid_machine"]


# -- 对照 prompt 红线(§4.2:泄题即废,机器盯死) ---------------------------------


def test_control_prompt_redline():
    from freshlatch.eval.control import CONTROL_PROMPT, _parse_verdict

    for leak in ("T1", "T0", "快照", "复验", "金标", "gold", "must_stale"):
        assert leak not in CONTROL_PROMPT, f"对照 prompt 泄题: {leak}"


def test_control_verdict_parse():
    from freshlatch.eval.control import _parse_verdict

    assert _parse_verdict('{"verdict": "alive"}') == "alive"
    assert _parse_verdict('前言 {"verdict": "dead"} 后记') == "dead"
    assert _parse_verdict("成立") == "unparseable"
    assert _parse_verdict('{"verdict": "yes"}') == "unparseable"
    assert _parse_verdict("") == "unparseable"
