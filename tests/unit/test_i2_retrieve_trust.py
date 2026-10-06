"""I2 召回信任边界:acl-t001 / poison-t001。确定性,零 LLM。"""

import asyncio
import json
import sqlite3
from pathlib import Path

import pytest

from freshlatch.forensic_tools import create_forensic_tools
from freshlatch.models import Claim
from freshlatch.roles.critic import Critic
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import RunContext
from freshlatch.store.base import Chunk, Document, InMemoryStore
from freshlatch.store.pipeline import recall_bm25
from freshlatch.store.sqlite_store import SQLiteStore

FIXTURE_DIR = Path("docs/evidence/i2")


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _chunk(spec: dict) -> Chunk:
    as_of = spec.get("as_of", "T1")
    clause_id = spec.get("clause_id", "p1")
    return Chunk(
        doc_id=spec["doc_id"],
        chunk_id=f"{spec['doc_id']}::chunk-{clause_id}@{as_of}",
        clause_id=clause_id,
        title=spec["doc_id"],
        text=spec["text"],
        source_type=spec.get("source_type", "private"),
        as_of=as_of,
        doc_version="1.0",
        checksum="i2",
        tokens=8,
        tenant_id=spec.get("tenant_id", "default"),
        poison=bool(spec.get("poison", False)),
        untrusted=bool(spec.get("untrusted", False)),
    )


def _populate(store, fixture: dict) -> list[Chunk]:
    """入库夹具块,并加一条不含查询词的干扰块,避免查询词 df=N 时 BM25 分为 0。"""
    chunks = [_chunk(spec) for spec in fixture["chunks"]]
    # BM25 IDF 在 df 接近 N 时为 0 或负,召回会丢掉 0 分。干扰块把 N 撑过 2*df。
    for i in range(4):
        chunks.append(_chunk({
            "doc_id": f"filler-{fixture['demo_id']}-{i}",
            "text": f"zzzfill{i} 无关条款 filleronly{i}",
            "tenant_id": "default",
        }))
    for chunk in chunks:
        store.add_document(
            Document(
                doc_id=chunk.doc_id,
                as_of=chunk.as_of,
                source_type=chunk.source_type,
                title=chunk.title,
                doc_version="1.0",
                checksum="i2",
                full_text=chunk.text,
                tenant_id=chunk.tenant_id,
                poison=chunk.poison,
                untrusted=chunk.untrusted,
            ),
            [chunk],
        )
    return chunks


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    if request.param == "memory":
        return InMemoryStore()
    return SQLiteStore(tmp_path / "i2.db")


def test_acl_t001_explicit_tenant_excludes_other(store):
    """显式 tenant_id=B 时结果不含租户 A。"""
    fixture = _load("acl-t001.json")
    _populate(store, fixture)
    hits = store.retrieve(fixture["query"], tenant_id="B", top_k=10)
    ids = {c.doc_id for c in hits}
    assert "acl-tenant-b" in ids
    assert "acl-tenant-a" not in ids
    assert all(c.tenant_id == "B" for c in hits)


def test_acl_t001_omitted_tenant_keeps_both(store):
    """未传 tenant_id 不启租户过滤,两租户块都可命中。"""
    fixture = _load("acl-t001.json")
    _populate(store, fixture)
    hits = store.retrieve(fixture["query"], top_k=10)
    ids = {c.doc_id for c in hits}
    assert ids == {"acl-tenant-a", "acl-tenant-b"}


def test_acl_t001_explicit_default_hides_other_tenants(store):
    """显式 tenant_id=default 只留缺省租户,不把 A/B 算进 default。"""
    fixture = _load("acl-t001.json")
    _populate(store, fixture)
    hits = store.retrieve(fixture["query"], tenant_id="default", top_k=10)
    assert hits == []


def test_poison_t001_high_score_excluded(store):
    """带 poison/untrusted 的高分块不进结果;未打标块仍在。"""
    fixture = _load("poison-t001.json")
    raw = _populate(store, fixture)
    ranked = recall_bm25(fixture["query"], raw, top_k=3)
    assert ranked and ranked[0].doc_id == "poison-bad"
    hits = store.retrieve(fixture["query"], top_k=1)
    ids = {c.doc_id for c in hits}
    assert "poison-bad" not in ids
    assert "untrusted-bad" not in ids
    assert ids == {"poison-good"}


def test_unlabeled_poison_wording_stays_retrievable(store):
    """正文写了 poison/untrusted 但没有元数据标签,不得当投毒硬门剔掉。"""
    chunk = _chunk({
        "doc_id": "wording-only",
        "text": "poison untrusted 这段只是正文用词 wordingmarker",
        "tenant_id": "default",
        "poison": False,
        "untrusted": False,
    })
    for i in range(2):
        filler = _chunk({
            "doc_id": f"wording-filler-{i}",
            "text": f"zzzfill{i} 无关条款 filleronly{i}",
        })
        store.add_document(
            Document(
                doc_id=filler.doc_id, as_of="T1", source_type="private", title="t",
                doc_version="1.0", checksum="i2", full_text=filler.text,
            ),
            [filler],
        )
    store.add_document(
        Document(
            doc_id=chunk.doc_id, as_of="T1", source_type="private", title="t",
            doc_version="1.0", checksum="i2", full_text=chunk.text,
        ),
        [chunk],
    )
    hits = store.retrieve("wordingmarker", top_k=5)
    assert any(c.doc_id == "wording-only" for c in hits)


def test_forensic_direct_retrieve_uses_store_filter(tmp_path):
    """Forensic 直调与 store.retrieve 同一过滤,不能旁路租户或投毒。"""
    store = SQLiteStore(tmp_path / "forensic.db")
    acl = _load("acl-t001.json")
    poison = _load("poison-t001.json")
    _populate(store, acl)
    _populate(store, poison)
    tools = create_forensic_tools(store)

    direct = store.retrieve(poison["query"], top_k=10)
    via_tool = asyncio.run(tools["retrieve"](poison["query"], top_k=10))
    assert via_tool["status"] == "success"
    direct_ids = {c.doc_id for c in direct}
    tool_ids = {block["evidence_id"].split("#")[0] for block in via_tool["blocks"]}
    assert "poison-bad" not in direct_ids
    assert "poison-bad" not in tool_ids
    assert "untrusted-bad" not in tool_ids
    assert direct_ids == tool_ids

    scoped = asyncio.run(tools["retrieve"](acl["query"], tenant_id="B", top_k=10))
    scoped_ids = {block["evidence_id"].split("#")[0] for block in scoped["blocks"]}
    assert scoped_ids == {"acl-tenant-b"}
    assert store.retrieve(acl["query"], tenant_id="B", top_k=10)[0].doc_id == "acl-tenant-b"


def test_try_retrieve_and_tools_pass_tenant(tmp_path):
    """try_retrieve / Lead / Critic 透传 tenant_id,并记入轨迹 filters。"""
    store = InMemoryStore()
    fixture = _load("acl-t001.json")
    _populate(store, fixture)
    ctx = RunContext(store=store, mode="online")
    hits = ctx.try_retrieve(fixture["query"], as_of="T1", top_k=10, tenant_id="B")
    assert {c.doc_id for c in hits} == {"acl-tenant-b"}
    assert ctx.events[-1]["filters"]["tenant_id"] == "B"
    assert ctx.events[-1]["filters"]["as_of"] == "T1"

    claim = Claim(claim_id="c-acl", statement=fixture["query"])
    lead = LeadReverifier(ctx, claim, llm=None)
    led = lead._t_retrieve({"query": "ignored", "as_of": "T1", "tenant_id": "A"})
    assert led["blocks"]
    assert all(b["evidence_id"].startswith("acl-tenant-a#") for b in led["blocks"])
    assert ctx.events[-1]["filters"]["tenant_id"] == "A"

    critic = Critic(ctx, claim, llm=None)
    crit = critic._t_retrieve({"query": "ignored", "as_of": "T1"})
    assert {b["evidence_id"].split("#")[0] for b in crit["blocks"]} == {
        "acl-tenant-a", "acl-tenant-b",
    }
    assert "tenant_id" not in ctx.events[-1]["filters"]


def test_sqlite_old_rows_default_trust_columns(tmp_path):
    """旧库 13 列 chunks 打开后补信任列;旧行 tenant=default 且非 poison。"""
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE chunks (
            doc_id TEXT NOT NULL,
            chunk_id TEXT NOT NULL,
            clause_id TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            source_type TEXT NOT NULL,
            as_of TEXT NOT NULL,
            doc_version TEXT NOT NULL DEFAULT '1.0',
            checksum TEXT NOT NULL DEFAULT '',
            tokens INTEGER NOT NULL DEFAULT 0,
            parent_id TEXT,
            hypo_questions TEXT,
            vec BLOB,
            PRIMARY KEY (chunk_id)
        )
        """
    )
    conn.executemany(
        "INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                "legacy-doc", "legacy-doc::chunk-p1@T1", "p1", "旧行",
                "legacytoken 旧库条款", "private", "T1", "1.0", "abc", 3,
                None, None, None,
            ),
            (
                "legacy-filler-0", "legacy-filler-0::chunk-p1@T1", "p1", "填充",
                "zzzfill0 无关条款 filleronly0", "private", "T1", "1.0", "abc", 3,
                None, None, None,
            ),
            (
                "legacy-filler-1", "legacy-filler-1::chunk-p1@T1", "p1", "填充",
                "zzzfill1 无关条款 filleronly1", "private", "T1", "1.0", "abc", 3,
                None, None, None,
            ),
        ],
    )
    conn.commit()
    conn.close()

    store = SQLiteStore(path)
    hits = store.retrieve("legacytoken", top_k=5)
    assert len(hits) == 1
    assert hits[0].tenant_id == "default"
    assert hits[0].poison is False
    assert hits[0].untrusted is False
    conn = sqlite3.connect(path)
    try:
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(chunks)")
        }
    finally:
        conn.close()
    assert {"tenant_id", "poison", "untrusted"} <= cols
