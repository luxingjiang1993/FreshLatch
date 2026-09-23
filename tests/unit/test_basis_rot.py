"""β+ 档 3b 主缝:check_basis + apply_rot(ADR-0025 / #143)。

只钉外部行为。不得升格为「checksum 已证明 latch」或统计结论。
禁改 gold;禁自动 void;checksum_fn 语料现算,禁读库列套套。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from freshlatch.gates.basis_rot import (
    BASIS_CHECKSUM_MISMATCH,
    apply_rot,
    check_basis,
)
from freshlatch.models import Claim
from freshlatch.store.base import Chunk, Document
from freshlatch.store.checksum import make_checksum_fn, sha256_hex
from freshlatch.store.sqlite_store import SQLiteStore

DOC = "t0-competitor-notes"
EID = f"{DOC}#p2@T1"


def _now_factory():
    step = {"n": 0}

    def now() -> datetime:
        step["n"] += 1
        return datetime(2026, 9, 23, 14, 0, step["n"])

    return now


def _fresh_claim(*, basis, last_confirmed_at: str = "2026-09-22T10:00:00") -> Claim:
    return Claim(
        claim_id="c-rot",
        statement="竞品客单价仍显著高于我们",
        status="fresh",
        reason="人审续命后绿灯",
        validity_basis=basis,
        last_confirmed_at=last_confirmed_at,
        t1_evidence_ids=[EID],
    )


def _store(tmp_path, *, checksum: str = "recorded-aaa") -> SQLiteStore:
    store = SQLiteStore(tmp_path / "freshlatch.db")
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
    return store


def _write_corpus(corpus: Path, body: bytes) -> Path:
    path = corpus / "t1" / f"{DOC}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


# -- check_basis -----------------------------------------------------------------


def test_check_basis_skip_without_basis():
    """无 validity_basis 的 fresh 不检(半激活诚实;不偷开 3a)。"""
    claim = Claim(claim_id="c1", statement="x", status="fresh", reason="Agent 绿灯")
    calls: list[tuple] = []

    def spy(doc_id: str, as_of: str) -> str | None:
        calls.append((doc_id, as_of))
        return "should-not-run"

    r = check_basis(claim, spy)
    assert r.verdict == "skip"
    assert calls == []


def test_check_basis_skip_voided():
    """voided 主张不因本机制降级(不侵占人审 L0)。"""
    claim = _fresh_claim(basis={"doc_id": DOC, "checksum": "old"})
    claim.voided = True
    r = check_basis(claim, lambda doc, at: "other")
    assert r.verdict == "skip"
    assert claim.status == "fresh"
    assert claim.voided is True


def test_check_basis_skip_non_fresh():
    """仅 fresh 受检;stale/unknown 跳过。"""
    for status in ("stale", "unknown"):
        claim = _fresh_claim(basis={"doc_id": DOC, "checksum": "old"})
        claim.status = status
        r = check_basis(claim, lambda doc, at: "other")
        assert r.verdict == "skip", status


def test_check_basis_single_object_ok():
    """单对象 basis 与现算一致 → ok。"""
    claim = _fresh_claim(basis={"doc_id": DOC, "checksum": "live-111"})
    r = check_basis(claim, lambda doc, at: "live-111")
    assert r.verdict == "ok"


def test_check_basis_single_object_mismatch():
    """单对象 basis 与现算不符 → mismatch。"""
    claim = _fresh_claim(basis={"doc_id": DOC, "checksum": "recorded-111"})
    r = check_basis(claim, lambda doc, at: "live-999")
    assert r.verdict == "mismatch"


def test_check_basis_list_all_members_any_mismatch(tmp_path):
    """list 全员受检:仅首元相符、次元不符 → mismatch(禁只比 [0])。"""
    claim = _fresh_claim(basis=[
        {"doc_id": "doc-a", "checksum": "ok-a"},
        {"doc_id": "doc-b", "checksum": "stale-b"},
    ])
    seen: list[str] = []

    def fn(doc_id: str, as_of: str) -> str | None:
        seen.append(doc_id)
        return {"doc-a": "ok-a", "doc-b": "live-b"}[doc_id]

    r = check_basis(claim, fn)
    assert r.verdict == "mismatch"
    assert seen == ["doc-a", "doc-b"]  # 不得在首元相符后提前返回 ok


def test_check_basis_list_all_ok():
    """list 全员相符 → ok。"""
    claim = _fresh_claim(basis=[
        {"doc_id": "doc-a", "checksum": "a1"},
        {"doc_id": "doc-b", "checksum": "b1"},
    ])
    r = check_basis(claim, lambda doc, at: {"doc-a": "a1", "doc-b": "b1"}[doc])
    assert r.verdict == "ok"


def test_check_basis_uses_corpus_fn_not_store_column(tmp_path):
    """篡改语料后:库列仍等于 basis,语料现算 fn 仍判 mismatch(禁套套)。"""
    corpus = tmp_path / "corpus"
    raw = (
        b"---\nid: t0-competitor-notes\nas_of: T1\n"
        b"title: \xe7\xab\x9e\xe5\x93\x81\xe7\xac\x94\xe8\xae\xb0\nchecksum:\n---\n\n## p2\n"
        b"T1:original\n"
    )
    path = _write_corpus(corpus, raw)
    recorded = sha256_hex(raw)
    store = _store(tmp_path, checksum=recorded)
    chunk = store.get_chunk(DOC, "p2", as_of="T1")
    assert chunk is not None and chunk.checksum == recorded

    claim = _fresh_claim(basis={"doc_id": DOC, "checksum": recorded})
    path.write_bytes(raw + b"\n# tampered\n")
    assert sha256_hex(path.read_bytes()) != recorded
    # 库列未变(= basis),若读库列会假绿
    still = store.get_chunk(DOC, "p2", as_of="T1")
    assert still is not None and still.checksum == recorded

    prod = make_checksum_fn(corpus)
    assert prod(DOC, "T1") != recorded
    r = check_basis(claim, prod)
    assert r.verdict == "mismatch"


# -- apply_rot -------------------------------------------------------------------


def test_apply_rot_downgrades_to_unknown_keeps_basis(tmp_path):
    """不符 → unknown + 可观察机械码;保留 basis 与 last_confirmed_at;写 basis_rot。"""
    store = _store(tmp_path)
    basis = {"doc_id": DOC, "checksum": "recorded-111"}
    claim = _fresh_claim(basis=basis, last_confirmed_at="2026-09-22T10:00:00")
    result = apply_rot(store, claim, now=_now_factory())

    assert result.outcome == "applied"
    assert claim.status == "unknown"
    assert BASIS_CHECKSUM_MISMATCH in claim.reason
    assert claim.validity_basis == basis
    assert claim.last_confirmed_at == "2026-09-22T10:00:00"
    assert claim.voided is False  # 禁自动 void

    rows = store.list_latch_rows(claim_id=claim.claim_id)
    assert len(rows) == 1
    row = rows[0]
    assert row["action"] == "basis_rot"
    assert row["actor"] == "system"
    assert row["machine_status_before"] == "fresh"
    assert row["override"] is False  # 不得为 true;非人审对抗语义
    assert BASIS_CHECKSUM_MISMATCH in (row.get("reviewer_note") or "")


def test_apply_rot_idempotent_already_unknown(tmp_path):
    """已 unknown 再 apply → already_rotten;不重复写成功降级行;状态不抖动。"""
    store = _store(tmp_path)
    basis = {"doc_id": DOC, "checksum": "recorded-111"}
    claim = _fresh_claim(basis=basis)
    first = apply_rot(store, claim, now=_now_factory())
    assert first.outcome == "applied"
    reason_after = claim.reason
    rows_after = store.list_latch_rows(claim_id=claim.claim_id)

    second = apply_rot(store, claim, now=_now_factory())
    assert second.outcome == "already_rotten"
    assert claim.status == "unknown"
    assert claim.reason == reason_after
    assert claim.validity_basis == basis
    assert store.list_latch_rows(claim_id=claim.claim_id) == rows_after


def test_apply_rot_noop_on_stale(tmp_path):
    """非 fresh 非 unknown 不写。"""
    store = _store(tmp_path)
    claim = _fresh_claim(basis={"doc_id": DOC, "checksum": "x"})
    claim.status = "stale"
    r = apply_rot(store, claim, now=_now_factory())
    assert r.outcome == "noop"
    assert claim.status == "stale"
    assert store.list_latch_rows(claim_id=claim.claim_id) == []


# -- pipeline 接线:命中腐烂不进 Lead -----------------------------------------------


def test_runner_skips_lead_on_basis_rot(tmp_path, monkeypatch):
    """复验入口:mismatch → apply_rot 后本轮不进 Lead。"""
    from freshlatch.runner import Runner

    store = _store(tmp_path)
    claim = _fresh_claim(basis={"doc_id": DOC, "checksum": "recorded-111"})
    spawned: list[str] = []

    class FakeLead:
        steps_used = 0

        def run(self):
            raise AssertionError("命中腐烂不得进入 Lead")

    def fake_spawn(self, c):
        spawned.append(c.claim_id)
        return FakeLead()

    monkeypatch.setattr(Runner, "_spawn_lead", fake_spawn)
    runner = Runner(store, checksum_fn=lambda doc, at: "live-999")
    result = runner.run([claim], trajectory_dir=tmp_path / "traj")

    assert spawned == []
    assert claim.status == "unknown"
    assert BASIS_CHECKSUM_MISMATCH in claim.reason
    assert claim.validity_basis == {"doc_id": DOC, "checksum": "recorded-111"}
    assert result.decisions[claim.claim_id].status == "unknown"
    rows = store.list_latch_rows(claim_id=claim.claim_id)
    assert len(rows) == 1 and rows[0]["action"] == "basis_rot"


def test_runner_tampered_corpus_rots_without_lead(tmp_path, monkeypatch):
    """验收链:篡改已续命 basis 对应语料 → 复验入口 unknown + basis_rot + 不进 Lead。"""
    from freshlatch.runner import Runner

    corpus = tmp_path / "corpus"
    raw = (
        b"---\nid: t0-competitor-notes\nas_of: T1\n"
        b"title: notes\nchecksum:\n---\n\n## p2\nT1:original\n"
    )
    path = _write_corpus(corpus, raw)
    recorded = sha256_hex(raw)
    store = _store(tmp_path, checksum=recorded)
    claim = _fresh_claim(basis={"doc_id": DOC, "checksum": recorded})
    path.write_bytes(raw + b"\n# tampered\n")

    spawned: list[str] = []

    class FakeLead:
        steps_used = 0

        def run(self):
            raise AssertionError("命中腐烂不得进入 Lead")

    def fake_spawn(self, c):
        spawned.append(c.claim_id)
        return FakeLead()

    monkeypatch.setattr(Runner, "_spawn_lead", fake_spawn)
    runner = Runner(store, checksum_fn=make_checksum_fn(corpus))
    runner.run([claim], trajectory_dir=tmp_path / "traj")

    assert spawned == []
    assert claim.status == "unknown"
    assert BASIS_CHECKSUM_MISMATCH in claim.reason
    assert claim.validity_basis == {"doc_id": DOC, "checksum": recorded}
    assert claim.last_confirmed_at == "2026-09-22T10:00:00"
    assert store.list_latch_rows(claim_id=claim.claim_id)[0]["action"] == "basis_rot"


def test_runner_enters_lead_when_basis_ok(tmp_path, monkeypatch):
    """basis 相符的 fresh 仍进 Lead。"""
    from freshlatch.runner import ClaimDecision, Runner

    store = _store(tmp_path)
    claim = _fresh_claim(basis={"doc_id": DOC, "checksum": "live-111"})
    spawned: list[str] = []

    class FakeLead:
        steps_used = 3

        def run(self):
            return ClaimDecision(claim_id=claim.claim_id, status="fresh",
                                reason="Lead ok", evidence_ids=[EID],
                                auditor_verdict="fresh")

    def fake_spawn(self, c):
        spawned.append(c.claim_id)
        return FakeLead()

    monkeypatch.setattr(Runner, "_spawn_lead", fake_spawn)
    # 跳过 _finalize 复杂闸链:只关心「进了 Lead」
    monkeypatch.setattr(Runner, "_finalize", lambda self, c, d: setattr(c, "status", d.status))
    runner = Runner(store, checksum_fn=lambda doc, at: "live-111")
    runner.run([claim], trajectory_dir=tmp_path / "traj")
    assert spawned == [claim.claim_id]
    assert claim.status == "fresh"
