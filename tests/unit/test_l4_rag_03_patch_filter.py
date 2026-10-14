"""L4-RAG-03: patch_id / 有效期过滤先于 RRF。

夹具只在 tests/fixtures/l4_rag_03/。不读 data/exp/x1/。
"""

from __future__ import annotations

import inspect
import subprocess
from pathlib import Path

import pytest

from freshlatch.models import LOCAL_EMBED_MODEL, NEURAL_RERANK_MODEL
from freshlatch.store.base import (
    PRODUCTION_RETRIEVAL_MODE,
    Chunk,
    InMemoryStore,
    chunk_evidence_id,
)
from freshlatch.store.ingest import ingest_into, parse_document
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import (
    RRF_K,
    filter_patch_metadata,
    meta_text,
    pack_vec,
)
from freshlatch.store.sqlite_store import SQLiteStore

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "l4_rag_03"
CORPUS = ROOT / "data" / "corpus"
QUERY = "专业版席位标价"

# 本票改代码前,对 data/corpus 小库的 BM25 候选 chunk_id 序列。
_BEFORE_PRIVATE_T1 = (
    "t0-competitor-notes::chunk-p1@T1",
    "t0-competitor-notes::chunk-p3@T1",
    "t0-competitor-notes::chunk-p2@T1",
)
_BEFORE_REGULATORY_T0 = (
    "t0-regulatory-memo::chunk-p2@T0",
    "t0-regulatory-memo::chunk-p1@T0",
    "t0-regulatory-memo::chunk-p3@T0",
    "t0-market-census::chunk-p1@T0",
)
_BEFORE_PRICE_T1 = (
    "t0-cost-model::chunk-p3@T1",
    "t0-competitor-economics::chunk-p2@T1",
    "t0-trade-press::chunk-p2@T1",
    "t0-cost-model::chunk-p1@T1",
    "t0-competitor-notes::chunk-p1@T1",
    "t0-trade-press::chunk-p3@T1",
    "t0-competitor-economics::chunk-p1@T1",
    "t0-cost-model::chunk-p2@T1",
    "t0-competitor-notes::chunk-p3@T1",
    "t0-competitor-news::chunk-p1@T1",
)

_DO_NOT_TOUCH = (
    "data/exp/x1",
    "docs/evidence/neural-rerank",
    "docs/evidence/quality-gate/PREREG.md",
    "docs/evidence/patch-events/RESULT-Y.md",
    "docs/evidence/patch-events/PREREG-Y.md",
    "data/eval/guard_should.json",
    "data/eval/cite_sentence.json",
    "data/eval/temporal_new_over_old.json",
    "data/eval/gold.json",
)


def _frontmatter(text: str) -> dict[str, str]:
    head = text.split("---", 2)[1]
    meta: dict[str, str] = {}
    for line in head.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


def load_patch_corpus() -> list[tuple]:
    """测试树夹具。parse_document 不读补丁列,这里把 frontmatter 写回 Chunk。"""
    loaded = []
    for path in sorted(FIXTURE.glob("*.md")):
        doc, chunks = parse_document(path)
        meta = _frontmatter(path.read_text(encoding="utf-8"))
        version = meta.get("doc_version") or doc.doc_version
        doc.doc_version = version
        for chunk in chunks:
            chunk.doc_version = version
            chunk.patch_id = meta_text(meta.get("patch_id"))
            chunk.valid_from = meta_text(meta.get("valid_from"))
            chunk.valid_to = meta_text(meta.get("valid_to"))
            chunk.vec = pack_vec([1.0, 0.0])
        loaded.append((doc, chunks))
    return loaded


def _arm_hybrid(store):
    store.query_embedder = lambda _query: [1.0, 0.0]
    store.bind_eval_retrieval_mode("hybrid")
    return store


@pytest.fixture(params=["memory", "sqlite"])
def patch_store(request, tmp_path):
    if request.param == "memory":
        store = InMemoryStore()
    else:
        store = SQLiteStore(tmp_path / "patch.db")
    for doc, chunks in load_patch_corpus():
        store.add_document(doc, chunks)
    return _arm_hybrid(store)


def _ids(chunks: list[Chunk]) -> list[str]:
    return [chunk.chunk_id for chunk in chunks]


def test_filter_drops_other_patch_and_keeps_blank_fields():
    """纯函数:p1 剔除,三字段皆空的块保留,doc_version 不参与。"""
    keep = Chunk(
        doc_id="b", chunk_id="b", clause_id="p1", title="t", text="x",
        source_type="private", as_of="T1", doc_version="p2", checksum="",
        tokens=1, patch_id="p2",
    )
    drop = Chunk(
        doc_id="a", chunk_id="a", clause_id="p1", title="t", text="x",
        source_type="private", as_of="T1", doc_version="p2", checksum="",
        tokens=1, patch_id="p1",
    )
    blank = Chunk(
        doc_id="o", chunk_id="o", clause_id="p1", title="t", text="x",
        source_type="private", as_of="T1", doc_version="p1", checksum="",
        tokens=1,
    )
    window = Chunk(
        doc_id="w", chunk_id="w", clause_id="p1", title="t", text="x",
        source_type="private", as_of="T1", doc_version="v1", checksum="",
        tokens=1, valid_from="2026-01-01", valid_to="2026-06-30",
    )
    same = filter_patch_metadata([drop, keep, blank, window])
    assert same == [drop, keep, blank, window]
    patched = filter_patch_metadata([drop, keep, blank, window], patch_id="p2")
    assert _ids(patched) == ["b", "o", "w"]
    early = filter_patch_metadata([window, blank], valid_at="2025-12-31")
    assert _ids(early) == ["o"]
    on_start = filter_patch_metadata([window], valid_at="2026-01-01")
    on_end = filter_patch_metadata([window], valid_at="2026-06-30")
    after = filter_patch_metadata([window], valid_at="2026-07-01")
    assert _ids(on_start) == ["w"]
    assert _ids(on_end) == ["w"]
    assert after == []
    body = inspect.getsource(filter_patch_metadata).split('"""', 2)[-1]
    assert "doc_version" not in body


def test_other_patch_absent_from_pool_before_rrf(patch_store, monkeypatch):
    """查询指定 p2 时,p1 不进入 BM25 / dense / RRF 的候选池。"""
    import freshlatch.store.pipeline as pipeline

    seen: dict[str, list] = {"pool": [], "dense": [], "fused": []}
    real_bm25 = pipeline.recall_bm25
    real_dense = pipeline.rank_dense
    real_rrf = pipeline.rrf_fuse

    def spy_bm25(query, pool, **kwargs):
        seen["pool"].append(_ids(pool))
        return real_bm25(query, pool, **kwargs)

    def spy_dense(query_vec, pool, **kwargs):
        seen["dense"].append(_ids(pool))
        return real_dense(query_vec, pool, **kwargs)

    def spy_rrf(left, right, **kwargs):
        seen["fused"].append(_ids(list(left) + list(right)))
        return real_rrf(left, right, **kwargs)

    monkeypatch.setattr(pipeline, "recall_bm25", spy_bm25)
    monkeypatch.setattr(pipeline, "rank_dense", spy_dense)
    monkeypatch.setattr(pipeline, "rrf_fuse", spy_rrf)

    hits = patch_store.retrieve(QUERY, as_of="T1", patch_id="p2", top_k=10)
    assert patch_store.last_retrieval_mode == "hybrid"
    assert seen["pool"] and seen["dense"] and seen["fused"]
    for bucket in (seen["pool"][0], seen["dense"][0], seen["fused"][0]):
        assert not any(item.startswith("claim-price-p1::") for item in bucket)
        assert not any(item.startswith("claim-price-decoy::") for item in bucket)
        assert not any(item.endswith("@T0") for item in bucket)
        assert any(item.startswith("claim-price-p2::") for item in bucket)
        assert any(item.startswith("claim-price-open::") for item in bucket)
    assert all(chunk.patch_id != "p1" for chunk in hits)
    assert any(chunk.patch_id == "p2" and chunk.as_of == "T1" for chunk in hits)
    decoy = next(
        chunk for _doc, chunks in load_patch_corpus() for chunk in chunks
        if chunk.doc_id == "claim-price-decoy"
    )
    assert decoy.doc_version == "p2"
    assert decoy.patch_id == "p1"
    assert chunk_evidence_id(decoy) not in {chunk_evidence_id(c) for c in hits}


def test_valid_at_drops_closed_window_before_recall(patch_store, monkeypatch):
    import freshlatch.store.pipeline as pipeline

    seen: list[list[str]] = []
    real_bm25 = pipeline.recall_bm25

    def spy_bm25(query, pool, **kwargs):
        seen.append(_ids(pool))
        return real_bm25(query, pool, **kwargs)

    monkeypatch.setattr(pipeline, "recall_bm25", spy_bm25)
    hits = patch_store.retrieve(QUERY, as_of="T1", valid_at="2026-07-01", top_k=10)
    assert patch_store.last_retrieval_mode == "hybrid"
    assert seen
    assert not any(item.startswith("claim-price-window::") for item in seen[0])
    assert any(item.startswith("claim-price-open::") for item in seen[0])
    assert all(chunk.doc_id != "claim-price-window" for chunk in hits)
    inside = patch_store.retrieve(QUERY, as_of="T1", valid_at="2026-06-30", top_k=10)
    assert any(item.startswith("claim-price-window::") for item in seen[1])
    assert any(chunk.doc_id == "claim-price-window" for chunk in inside)


def test_sqlite_roundtrip_keeps_patch_fields(tmp_path):
    store = SQLiteStore(tmp_path / "round.db")
    for doc, chunks in load_patch_corpus():
        store.add_document(doc, chunks)
    got = store.get_chunk("claim-price-p2", "p1", as_of="T1")
    assert got is not None
    assert got.patch_id == "p2"
    assert got.valid_from == "2024-01-01"
    assert got.valid_to == "2026-12-31"
    assert got.doc_version == "v9"
    opened = store.get_chunk("claim-price-open", "p1", as_of="T1")
    assert opened is not None
    assert opened.patch_id is None
    assert opened.valid_from is None
    assert opened.valid_to is None


def test_as_of_where_stays_t0_t1_only():
    """as_of 仍是 T0/T1 WHERE。补丁条件不写进这条 SQL。"""
    source = Path("src/freshlatch/store/sqlite_store.py").read_text(encoding="utf-8")
    retrieve = source.split("def retrieve(", 1)[1].split("def read_source(", 1)[0]
    sql_block = retrieve.split("sql, params", 1)[1].split("filter_patch_metadata", 1)[0]
    assert 'sql += " WHERE as_of = ?"' in sql_block
    assert "patch_id" not in sql_block
    assert "valid_from" not in sql_block
    assert "valid_to" not in sql_block
    assert "doc_version" not in sql_block


def test_blank_patch_fields_keep_small_corpus_ids(tmp_path):
    """三字段皆空的小库,候选 id 序列与本票之前一致。"""
    memory = InMemoryStore()
    ingest_into(memory, CORPUS)
    sqlite = SQLiteStore(tmp_path / "small.db")
    ingest_into(sqlite, CORPUS)

    def check(store):
        private = _ids(store.retrieve(
            "竞品 价格", as_of="T1", source_type="private", top_k=10,
        ))
        regulatory = _ids(store.retrieve("监管 数据 存储", as_of="T0", top_k=10))
        price = _ids(store.retrieve("竞品 降价 价格", as_of="T1", top_k=10))
        assert tuple(private) == _BEFORE_PRIVATE_T1
        assert tuple(regulatory) == _BEFORE_REGULATORY_T0
        assert tuple(price) == _BEFORE_PRICE_T1
        forced = _ids(store.retrieve(
            "竞品 降价 价格", as_of="T1", top_k=10, patch_id="p2", valid_at="2026-10-14",
        ))
        assert tuple(forced) == _BEFORE_PRICE_T1
        sample = store.retrieve("竞品 价格", as_of="T1", top_k=10)
        assert sample
        assert all(
            chunk.patch_id is None and chunk.valid_from is None and chunk.valid_to is None
            for chunk in sample
        )

    check(memory)
    check(sqlite)


def test_old_sqlite_rows_gain_null_patch_columns(tmp_path):
    """旧库打开后补三列。旧行三字段为空,检索 id 仍是原条款。"""
    import sqlite3

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
    hits = store.retrieve("legacytoken", top_k=5, patch_id="p2")
    assert _ids(hits) == ["legacy-doc::chunk-p1@T1"]
    assert hits[0].patch_id is None
    assert hits[0].valid_from is None
    assert hits[0].valid_to is None
    conn = sqlite3.connect(path)
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(chunks)")}
    finally:
        conn.close()
    assert {"patch_id", "valid_from", "valid_to"} <= cols


def test_frozen_retrieval_pins_stay():
    """不依赖 git。生产臂、RRF、精排 K、本地模型名与 fastembed pin 不动。"""
    from freshlatch.eval.quality_gate import (
        FROZEN_ARM,
        FROZEN_FASTEMBED,
        FROZEN_RERANK_K,
        FROZEN_RRF_K,
    )
    from freshlatch.store.local_embed import LOCAL_EMBED_DIM

    base = (ROOT / "src/freshlatch/store/base.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
    assert base.count("PRODUCTION_RETRIEVAL_MODE =") == 1
    assert PRODUCTION_RETRIEVAL_MODE == FROZEN_ARM == "hybrid+rerank"
    assert RRF_K == FROZEN_RRF_K == 60
    assert NEURAL_RERANK_K == FROZEN_RERANK_K == 10
    assert LOCAL_EMBED_DIM == 512
    assert LOCAL_EMBED_MODEL == "BAAI/bge-small-zh-v1.5"
    assert NEURAL_RERANK_MODEL == "BAAI/bge-reranker-base"
    pin = f"fastembed=={FROZEN_FASTEMBED}"
    assert pin in (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert pin in (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_do_not_touch_git_diff_empty():
    """浅克隆没有 origin/main 时跳过,避免 git diff 退出 128。"""
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "origin/main^{commit}"],
        cwd=ROOT,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip("base ref missing")
    proc = subprocess.run(
        ["git", "diff", "--stat", "origin/main", "--", *_DO_NOT_TOUCH],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == ""


def test_assertions_do_not_name_a_registered_shift():
    text = Path(__file__).read_text(encoding="utf-8")
    banned = "注册" + " T1 " + "上升"
    rate = "通过" + "率"
    assert banned not in text
    assert rate not in text
    counted = "counted_as_pass=" + "true"
    assert counted not in text
