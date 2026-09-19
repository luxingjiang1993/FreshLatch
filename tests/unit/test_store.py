"""检索层单测:ingestion 确定性、13 列 schema、WHERE 过滤、金标命中回放(§8.1 T2 验收)。"""

import json
from pathlib import Path

import pytest

from freshlatch.store.base import InMemoryStore
from freshlatch.store.ingest import ingest_into, load_corpus, parse_document
from freshlatch.store.sqlite_store import SQLiteStore

CORPUS = Path("data/corpus")
GOLD = json.loads(Path("data/eval/gold.json").read_text(encoding="utf-8"))
DocketClaims = json.loads(Path("data/t0_docket.json").read_text(encoding="utf-8"))["claims"]


@pytest.fixture()
def memory_store():
    store = InMemoryStore()
    ingest_into(store, CORPUS)
    return store


def test_corpus_mirror_parity():
    """双镜像一一对应:同 doc_id 在 t0/ 与 t1/ 各一篇。"""
    t0 = {p.stem for p in (CORPUS / "t0").glob("*.md")}
    t1 = {p.stem for p in (CORPUS / "t1").glob("*.md")}
    assert len(t0) == 12 and t0 == t1


def test_chunk_schema_13_columns():
    """chunk schema 13 列在位(3 留位空)。"""
    doc, chunks = parse_document(CORPUS / "t0" / "t0-competitor-notes.md")
    assert len(chunks) >= 2
    c = chunks[0]
    cols = [c.doc_id, c.chunk_id, c.clause_id, c.title, c.text, c.source_type,
            c.as_of, c.doc_version, c.checksum, c.tokens, c.parent_id,
            c.hypo_questions, c.vec]
    assert len(cols) == 13
    assert c.parent_id is None and c.hypo_questions is None and c.vec is None
    assert c.checksum == ""  # 留位为空


def test_ingestion_deterministic():
    """切块确定:同一文件两次解析 chunk_id 序列一致(金标复现优先)。"""
    _, a = parse_document(CORPUS / "t1" / "t0-regulatory-memo.md")
    _, b = parse_document(CORPUS / "t1" / "t0-regulatory-memo.md")
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]


def test_where_filters(memory_store):
    """as_of / source_type 过滤语义(内存假实现与 SQLite 共用同一语义)。"""
    t1_private = memory_store.retrieve("竞品 价格", as_of="T1", source_type="private")
    assert t1_private and all(c.as_of == "T1" and c.source_type == "private" for c in t1_private)
    t0_only = memory_store.retrieve("监管 数据 存储", as_of="T0")
    assert t0_only and all(c.as_of == "T0" for c in t0_only)


def test_read_source_fallback(memory_store):
    text = memory_store.read_source("t0-regulatory-memo", as_of="T1")
    assert text and "PDP" in text
    assert memory_store.read_source("no-such-doc", as_of="T1") is None


def test_anchor_lookup(memory_store):
    c = memory_store.get_chunk("t0-regulatory-memo", "p2", as_of="T1")
    assert c is not None and "境内存储" in c.text


def test_gold_hit_replay(memory_store):
    """金标命中回放:每条 must_stale 的 causal_chain 致死段落,用其主张文本能在 T1 top10 召回。"""
    claim_by_id = {c["claim_id"]: c for c in DocketClaims}
    failures = []
    for cid in GOLD["must_stale"]:
        chain = GOLD["causal_chain"][cid]
        doc_id, anchor = chain["t1_doc"], chain["anchor"]
        hits = memory_store.retrieve(claim_by_id[cid]["statement"], as_of="T1", top_k=10)
        got = {f"{c.doc_id}#{c.clause_id}" for c in hits}
        if f"{doc_id}#{anchor}" not in got:
            failures.append((cid, f"{doc_id}#{anchor}", sorted(got)))
    assert not failures, f"must_stale 证据块未进 top10: {failures}"


def test_sqlite_store_roundtrip(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    n = ingest_into(store, CORPUS)
    assert n == sum(len(cs) for _, cs in load_corpus(CORPUS))
    # 主键防冲突:T0/T1 双镜像必须同时存在(曾因 chunk_id 不含 as_of 互相覆盖)
    assert store.get_chunk("t0-competitor-notes", "p2", as_of="T0") is not None
    assert store.get_chunk("t0-competitor-notes", "p2", as_of="T1") is not None
    assert store.get_chunk("t0-competitor-notes", "p2", as_of="T0").tokens > 0
    hits = store.retrieve("竞品 降价 价格", as_of="T1")
    assert any("competitor-notes" in c.doc_id for c in hits)
    assert set(store.list_invalidation()) == set()
