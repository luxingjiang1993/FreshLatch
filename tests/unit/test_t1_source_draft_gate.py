"""DEM-2 / #89:T1 粘贴草稿可见性闸。挂 Latch/Gate + store retrieve seam。

草稿态不得进 retrieve、不得作续命证据;「确认入库」后才可。
不改 gold / 通过线;不开第四类 harness。
"""

from __future__ import annotations

from freshlatch.gates.human_latch import RENEW_EVIDENCE_UNRESOLVED
from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.store.base import Chunk, Document
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.t1_source import T1SourceSession

# 中文锚词:BM25/jieba 可召回;草稿态不应命中
ANCHOR = "DEM2草稿闸锚词竞品已降价至我方七成"
QUERY = "DEM2草稿闸锚词"


def _seed_decoy_t1(store: SQLiteStore) -> None:
    """BM25Okapi 在 N≤2 时单文档词 IDF=0;垫 ≥2 篇无关 T1 块使确认后可测 retrieve。"""
    for i, body in enumerate(
        ("无关干扰甲:仅谈监管口径。", "无关干扰乙:仅谈本地化强制要求。"),
        start=1,
    ):
        text = f"## p1\n{body}"
        doc_id = f"decoy-noise-{i}"
        store.add_document(
            Document(doc_id=doc_id, as_of="T1", source_type="private",
                     title=f"干扰{i}", doc_version="1.0", checksum="", full_text=text),
            [Chunk(doc_id=doc_id, chunk_id=f"{doc_id}::chunk-p1@T1",
                   clause_id="p1", title=f"干扰{i}", text=text, source_type="private",
                   as_of="T1", doc_version="1.0", checksum="", tokens=10)],
        )


def make_latch(store, tmp_path) -> HumanLatch:
    return HumanLatch(store, tmp_path / "checkpoints.db", mode="online")


def test_paste_draft_not_retrievable_until_confirm(tmp_path):
    """ADR-0016:粘贴先成草稿;未确认不得被 retrieve。"""
    store = SQLiteStore(tmp_path / "t.db")
    _seed_decoy_t1(store)
    sess = T1SourceSession(store)
    sess.save_paste_draft(f"变更要点:{ANCHOR}")

    assert sess.state.kind == "paste"
    assert sess.state.paste_status == "draft"
    assert sess.state.ready is False
    assert store.get_chunk(sess.draft_doc_id, "p1", as_of="T1") is None
    hits = store.retrieve(QUERY, as_of="T1")
    assert not any(ANCHOR in c.text for c in hits)

    result = sess.confirm_paste()
    assert result.ok
    assert sess.state.paste_status == "confirmed"
    assert sess.state.ready is True
    hits2 = store.retrieve(QUERY, as_of="T1")
    assert any(ANCHOR in c.text for c in hits2), "确认入库后应可被 retrieve"


def test_paste_draft_cannot_be_renew_evidence(tmp_path):
    """ADR-0016:未确认草稿不得作续命证据(点回失败 → RENEW_EVIDENCE_UNRESOLVED)。"""
    store = SQLiteStore(tmp_path / "t.db")
    sess = T1SourceSession(store)
    sess.save_paste_draft(f"变更要点:{ANCHOR}")
    # 草稿未入库时,即使知道将要用的 evidence_id 形态,点回也必须失败
    ghost_eid = f"{sess.draft_doc_id}#p1@T1"
    latch = make_latch(store, tmp_path)
    claim = Claim(claim_id="c1", statement="竞品仍贵", status="stale", reason="待审")
    rnd = latch.enter_round([claim])
    results = latch.decide(rnd.thread_id, [
        {"claim_id": "c1", "action": "renew", "evidence_id": ghost_eid},
    ])
    assert results[0]["ok"] is False
    assert results[0]["error_code"] == RENEW_EVIDENCE_UNRESOLVED
    assert claim.status == "stale"


def test_paste_confirmed_can_be_renew_evidence(tmp_path):
    """确认入库后 evidence_id 可点回,续命写路径可过。"""
    store = SQLiteStore(tmp_path / "t.db")
    sess = T1SourceSession(store)
    sess.save_paste_draft(f"变更要点:{ANCHOR}\n仍显著高于我方。")
    sess.confirm_paste()
    eid = f"{sess.draft_doc_id}#p1@T1"
    assert store.get_chunk(sess.draft_doc_id, "p1", as_of="T1") is not None

    latch = make_latch(store, tmp_path)
    claim = Claim(claim_id="c1", statement="竞品仍贵", status="stale", reason="待审")
    rnd = latch.enter_round([claim])
    results = latch.decide(rnd.thread_id, [
        {"claim_id": "c1", "action": "renew", "evidence_id": eid},
    ])
    assert results[0]["ok"] is True, results[0]
    assert claim.status == "fresh"


def test_not_ready_until_valid_source_selected(tmp_path):
    """未选定合法来源 → ready=False,不得假装已有最新 T1。"""
    store = SQLiteStore(tmp_path / "t.db")
    sess = T1SourceSession(store)
    assert sess.state.kind == "none"
    assert sess.state.ready is False
    assert sess.state.network_enabled is False
