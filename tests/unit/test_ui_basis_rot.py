"""β+ 档 3b UI 拉单:同一 check_basis/apply_rot 真写库(#144 / ADR-0025)。

禁止只改响应体;持久化观察点 = 内存主张 status + latch_log。
不得升格为「checksum 已证明 latch」。不改 gold;不自动 void。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.gates.basis_rot import BASIS_CHECKSUM_MISMATCH
from freshlatch.models import Claim
from freshlatch.store.base import Chunk, Document
from freshlatch.store.checksum import sha256_hex

DOC = "t0-competitor-notes"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    corpus = tmp_path / "corpus"
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "CORPUS", corpus)
    appmod._state.update({
        "claims": [], "question": "", "trajectory": None,
        "running": False, "latch": dict(appmod.EMPTY_LATCH),
        "retrieve_zero_hits": [], "budget": dict(appmod.EMPTY_BUDGET),
    })
    return TestClient(appmod.app), store, corpus


def _seed_doc(store, checksum: str) -> None:
    chunk = Chunk(
        doc_id=DOC, chunk_id=f"{DOC}-p2", clause_id="p2", title="竞品笔记",
        text="T1:竞品客单价仍显著高于我们。", source_type="competitor",
        as_of="T1", doc_version="v2", checksum=checksum, tokens=20,
    )
    store.add_document(
        Document(
            doc_id=DOC, as_of="T1", source_type="competitor", title="竞品笔记",
            doc_version="v2", checksum=checksum, full_text=chunk.text,
        ),
        [chunk],
    )


def _write_corpus(corpus: Path, body: bytes) -> Path:
    path = corpus / "t1" / f"{DOC}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


def test_api_claims_rots_tampered_basis_and_persists(client):
    """拉单后腐烂主张在持久化观察点为 unknown(非仅响应体改写)。"""
    http, store, corpus = client
    raw = (
        b"---\nid: t0-competitor-notes\nas_of: T1\n"
        b"title: notes\nchecksum:\n---\n\n## p2\nT1:original\n"
    )
    path = _write_corpus(corpus, raw)
    recorded = sha256_hex(raw)
    _seed_doc(store, recorded)

    claim = Claim(
        claim_id="c-rot",
        statement="竞品客单价仍显著高于我们",
        status="fresh",
        reason="人审续命后绿灯",
        validity_basis={"doc_id": DOC, "checksum": recorded},
        last_confirmed_at="2026-09-22T10:00:00",
    )
    appmod._state["claims"] = [claim]
    path.write_bytes(raw + b"\n# tampered\n")

    r = http.get("/api/claims")
    assert r.status_code == 200
    body = r.json()["claims"][0]
    assert body["status"] == "unknown"
    assert BASIS_CHECKSUM_MISMATCH in (body.get("reason") or "")

    # 真写库/真改状态:后续读与 latch_log 一致,不是一次性响应改写
    assert claim.status == "unknown"
    assert claim.validity_basis == {"doc_id": DOC, "checksum": recorded}
    assert claim.last_confirmed_at == "2026-09-22T10:00:00"
    assert claim.voided is False
    rows = store.list_latch_rows(claim_id="c-rot")
    assert len(rows) == 1
    assert rows[0]["action"] == "basis_rot"
    assert rows[0]["override"] is False

    again = http.get("/api/claims").json()["claims"][0]
    assert again["status"] == "unknown"
    assert len(store.list_latch_rows(claim_id="c-rot")) == 1  # 幂等


def test_api_claims_skips_fresh_without_basis(client):
    """无 basis 的 fresh 拉单不因此降级(半激活诚实)。"""
    http, store, corpus = client
    _write_corpus(corpus, b"irrelevant\n")
    claim = Claim(
        claim_id="c-half",
        statement="Agent 绿灯无 basis",
        status="fresh",
        reason="半激活",
    )
    appmod._state["claims"] = [claim]

    r = http.get("/api/claims")
    assert r.status_code == 200
    assert r.json()["claims"][0]["status"] == "fresh"
    assert claim.status == "fresh"
    assert store.list_latch_rows(claim_id="c-half") == []


def test_api_claims_uses_shared_basis_rot_module():
    """拉单路径必须 import 共享模块,无第二套比对逻辑。"""
    src = Path(appmod.__file__).read_text(encoding="utf-8")
    assert "from freshlatch.gates.basis_rot import rot_claims" in src
    assert "rot_claims(store" in src
    # 禁止在 UI 内再写一套 checksum 比对
    assert "BASIS_CHECKSUM_MISMATCH" not in src.split("rot_claims")[0]  # 常量只应来自共享模块
