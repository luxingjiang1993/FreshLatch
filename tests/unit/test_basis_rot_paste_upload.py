"""Bugbot 回归:粘贴/上传 T1 续命后篡改语料文件须能腐烂(ADR-0025)。

根因:仅 store.add_document、不落盘时 make_checksum_fn 恒 None → 永不 mismatch。
修复:confirm_paste / ingest_upload_texts 经 write_corpus_doc 落盘。
不得升格为「checksum 已证明 latch」;不改 gold;不自动 void。
"""

from __future__ import annotations

from pathlib import Path

import freshlatch.ui.app as appmod
from fastapi.testclient import TestClient
from freshlatch.gates.basis_rot import BASIS_CHECKSUM_MISMATCH
from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.runner import Runner
from freshlatch.store.checksum import make_checksum_fn, sha256_hex
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.t1_source import T1SourceSession


def _renew_fresh(store: SQLiteStore, tmp_path: Path, eid: str, corpus: Path) -> Claim:
    claim = Claim(claim_id="c-paste-rot", statement="竞品仍贵", status="stale", reason="待审")
    latch = HumanLatch(
        store, tmp_path / "cp.db", mode="online",
        checksum_fn=make_checksum_fn(corpus),
    )
    rnd = latch.enter_round([claim])
    results = latch.decide(rnd.thread_id, [
        {"claim_id": "c-paste-rot", "action": "renew", "evidence_id": eid},
    ])
    assert results[0]["ok"] is True, results[0]
    assert claim.status == "fresh"
    assert claim.validity_basis
    return claim


def test_paste_renew_then_tamper_rots(tmp_path, monkeypatch):
    """粘贴确认 → 续命 → 篡改落盘文件 → Runner 掉灯 + basis_rot,不进 Lead。"""
    store = SQLiteStore(tmp_path / "t.db")
    corpus = tmp_path / "corpus"
    sess = T1SourceSession(store, corpus_root=corpus)
    sess.save_paste_draft("变更要点:竞品客单价已显著下降。\n仍高于我方的叙事不再成立。")
    assert sess.confirm_paste().ok
    path = corpus / "t1" / "paste-change.md"
    assert path.is_file()
    recorded = sha256_hex(path.read_bytes())

    eid = f"{sess.draft_doc_id}#p1@T1"
    claim = _renew_fresh(store, tmp_path, eid, corpus)
    assert claim.validity_basis["checksum"] == recorded

    path.write_bytes(path.read_bytes() + b"\n# tampered-paste\n")

    spawned: list[str] = []

    class FakeLead:
        steps_used = 0

        def run(self):
            raise AssertionError("命中腐烂不得进入 Lead")

    def fake_spawn(self, c):
        spawned.append(c.claim_id)
        return FakeLead()

    monkeypatch.setattr(Runner, "_spawn_lead", fake_spawn)
    Runner(store, checksum_fn=make_checksum_fn(corpus)).run(
        [claim], trajectory_dir=tmp_path / "traj",
    )
    assert spawned == []
    assert claim.status == "unknown"
    assert BASIS_CHECKSUM_MISMATCH in claim.reason
    rows = store.list_latch_rows(claim_id=claim.claim_id)
    assert any(r["action"] == "basis_rot" for r in rows), rows


def test_upload_renew_then_api_claims_rots(tmp_path, monkeypatch):
    """上传入库 → 续命 → 篡改文件 → GET /api/claims 真写库 unknown + basis_rot。"""
    store = SQLiteStore(tmp_path / "t.db")
    corpus = tmp_path / "corpus"
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "CORPUS", corpus)
    appmod._state.update({
        "claims": [], "question": "", "trajectory": None,
        "running": False, "latch": dict(appmod.EMPTY_LATCH),
        "retrieve_zero_hits": [], "budget": dict(appmod.EMPTY_BUDGET),
    })
    appmod._reset_t1_source(store)

    md = (
        "---\n"
        "doc_id: upload-rot\n"
        "as_of: T1\n"
        "source_type: private\n"
        "title: 上传腐烂样例\n"
        "checksum:\n"
        "---\n"
        "## p1\n"
        "上传锚词:客户侧定价已变。\n"
    )
    http = TestClient(appmod.app)
    r = http.post(
        "/api/t1-source/upload",
        files=[("files", ("upload-rot.md", md.encode("utf-8"), "text/markdown"))],
    )
    assert r.status_code == 200
    path = corpus / "t1" / "upload-rot.md"
    assert path.is_file()

    claim = _renew_fresh(store, tmp_path, "upload-rot#p1@T1", corpus)
    appmod._state["claims"] = [claim]
    path.write_bytes(path.read_bytes() + b"\n# tampered-upload\n")

    body = http.get("/api/claims").json()["claims"][0]
    assert body["status"] == "unknown"
    assert BASIS_CHECKSUM_MISMATCH in (body.get("reason") or "")
    assert claim.status == "unknown"
    rows = store.list_latch_rows(claim_id=claim.claim_id)
    assert any(x["action"] == "basis_rot" for x in rows)


def test_paste_without_corpus_root_still_ingests(tmp_path):
    """无 corpus_root 时仍可入库(草稿闸单测兼容);不强制落盘。"""
    store = SQLiteStore(tmp_path / "t.db")
    sess = T1SourceSession(store, corpus_root=None)
    sess.save_paste_draft("无根路径仍确认")
    assert sess.confirm_paste().ok
    assert store.get_chunk("paste-change", "p1", as_of="T1") is not None
    assert not (tmp_path / "t1" / "paste-change.md").exists()
