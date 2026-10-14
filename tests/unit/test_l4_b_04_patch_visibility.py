"""L4-B-04: 审计面可见 as_of / patch_id / 有效期。

夹具只在 tests/fixtures/l4_b_04/。不读 data/exp/x1/。
错版与过窗在 RRF 前被既有 filter_patch_metadata 丢掉。
空元数据仍是空操作。TestClient 读 HTML,不开浏览器,不调用付费 LLM。
"""

from __future__ import annotations

import inspect
import json
import os
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.store.pipeline as pipeline
import freshlatch.ui.app as appmod
from freshlatch.sheet import project_audit
from freshlatch.store.base import (
    PRODUCTION_RETRIEVAL_MODE,
    Chunk,
    InMemoryStore,
    chunk_evidence_id,
)
from freshlatch.store.ingest import parse_document
from freshlatch.store.pipeline import RRF_K, filter_patch_metadata, meta_text, pack_vec
from freshlatch.store.sqlite_store import SQLiteStore

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "l4_b_04"
QUERY = "席位月费"
PATCH_KEEP = "b04-keep"
PATCH_DROP = "b04-drop"
VALID_AT = "2026-10-14"
KEEP_ID = "b04-price-keep#p1@T1"
DROP_ID = "b04-price-drop#p1@T1"
EXPIRED_ID = "b04-price-expired#p1@T1"
BLANK_ID = "b04-price-blank#p1@T1"
T0_ID = "b04-price-keep-t0#p1@T0"

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


def load_b04_corpus(names: list[str] | None = None) -> list[tuple]:
    """测试树夹具。parse_document 不读补丁列,这里把 frontmatter 写回 Chunk。"""
    paths = sorted(FIXTURE.glob("*.md"))
    if names is not None:
        wanted = set(names)
        paths = [path for path in paths if path.name in wanted]
    loaded = []
    for path in paths:
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


def _ids(chunks: list[Chunk]) -> list[str]:
    return [chunk.chunk_id for chunk in chunks]


@pytest.fixture(params=["memory", "sqlite"])
def version_store(request, tmp_path):
    if request.param == "memory":
        store = InMemoryStore()
    else:
        store = SQLiteStore(tmp_path / "b04.db")
    for doc, chunks in load_b04_corpus():
        store.add_document(doc, chunks)
    return _arm_hybrid(store)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "ui.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    saved = {
        "trajectory": appmod._state.get("trajectory"),
        "claims": list(appmod._state.get("claims") or []),
        "running": appmod._state.get("running"),
        "latch": dict(appmod._state.get("latch") or appmod.EMPTY_LATCH),
    }
    appmod._state["trajectory"] = None
    appmod._state["claims"] = []
    appmod._state["running"] = False
    appmod._state["latch"] = dict(appmod.EMPTY_LATCH)
    try:
        yield TestClient(appmod.app)
    finally:
        appmod._state["trajectory"] = saved["trajectory"]
        appmod._state["claims"] = saved["claims"]
        appmod._state["running"] = saved["running"]
        appmod._state["latch"] = saved["latch"]


def _write_jsonl(path: Path, events: list[dict]) -> None:
    lines = [json.dumps(event, ensure_ascii=False) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _section(html: str, element_id: str) -> str:
    marker = f'id="{element_id}"'
    assert marker in html
    return html.split(marker, 1)[1].split("</div>", 1)[0]


def test_wrong_version_filtered_before_rrf(version_store, monkeypatch):
    """同一主张的错 patch 与过窗不进 BM25 / dense / RRF 候选池。"""
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

    hits = version_store.retrieve(
        QUERY, as_of="T1", patch_id=PATCH_KEEP, valid_at=VALID_AT, top_k=10,
    )
    assert version_store.last_retrieval_mode == "hybrid"
    assert seen["pool"] and seen["dense"] and seen["fused"]
    for bucket in (seen["pool"][0], seen["dense"][0], seen["fused"][0]):
        assert "b04-price-keep::chunk-p1@T1" in bucket
        assert "b04-price-blank::chunk-p1@T1" in bucket
        assert "b04-price-drop::chunk-p1@T1" not in bucket
        assert "b04-price-expired::chunk-p1@T1" not in bucket
        assert not any(item.endswith("@T0") for item in bucket)
    evidence = {chunk_evidence_id(chunk) for chunk in hits}
    assert KEEP_ID in evidence
    assert BLANK_ID in evidence
    assert DROP_ID not in evidence
    assert EXPIRED_ID not in evidence
    assert T0_ID not in evidence
    dropped = next(
        chunk for _doc, chunks in load_b04_corpus() for chunk in chunks
        if chunk.doc_id == "b04-price-drop"
    )
    assert dropped.doc_version == PATCH_KEEP
    assert dropped.patch_id == PATCH_DROP


def test_blank_metadata_filter_is_noop(tmp_path, monkeypatch):
    """三字段皆空时,指定 patch_id 与 valid_at 仍不改变候选序列。"""
    blank_only = load_b04_corpus([
        "b04-price-blank.md",
        "b04-price-blank-filler.md",
    ])
    pools: list[list[str]] = []
    real_bm25 = pipeline.recall_bm25

    def spy_bm25(query, pool, **kwargs):
        pools.append(_ids(pool))
        return real_bm25(query, pool, **kwargs)

    monkeypatch.setattr(pipeline, "recall_bm25", spy_bm25)
    memory = InMemoryStore()
    sqlite = SQLiteStore(tmp_path / "blank.db")
    for store in (memory, sqlite):
        for doc, chunks in blank_only:
            store.add_document(doc, chunks)
        before = len(pools)
        plain = store.retrieve(QUERY, as_of="T1", top_k=10)
        tagged = store.retrieve(
            QUERY, as_of="T1", top_k=10, patch_id=PATCH_KEEP, valid_at=VALID_AT,
        )
        assert pools[before] == pools[before + 1]
        assert set(pools[before]) == {
            "b04-price-blank-filler::chunk-p1@T1",
            "b04-price-blank::chunk-p1@T1",
        }
        assert _ids(tagged) == _ids(plain)
        assert all(chunk.patch_id is None for chunk in plain)

    chunks = [chunk for _doc, rows in blank_only for chunk in rows]
    assert all(
        chunk.patch_id is None and chunk.valid_from is None and chunk.valid_to is None
        for chunk in chunks
    )
    assert _ids(filter_patch_metadata(chunks, patch_id=PATCH_KEEP, valid_at=VALID_AT)) == _ids(chunks)
    assert filter_patch_metadata(chunks) is chunks
    assert filter_patch_metadata(chunks, patch_id="  ", valid_at="") is chunks


def test_audit_shows_kept_patch_fields(client, tmp_path):
    """错版不在审计命中里;留下的块能看见 as_of、patch_id 与有效期。"""
    store = appmod._store()
    for doc, chunks in load_b04_corpus():
        store.add_document(doc, chunks)
    _arm_hybrid(store)
    hits = store.retrieve(
        QUERY, as_of="T1", patch_id=PATCH_KEEP, valid_at=VALID_AT, top_k=10,
    )
    evidence = [chunk_evidence_id(chunk) for chunk in hits]
    assert KEEP_ID in evidence
    assert DROP_ID not in evidence
    assert EXPIRED_ID not in evidence

    path = tmp_path / "kept.jsonl"
    _write_jsonl(path, [{
        "type": "retrieve",
        "query": QUERY,
        "as_of": "T1",
        "claim_id": "c-b04",
        "evidence_ids": evidence,
        "hits": len(hits),
    }])
    projected = project_audit(path)
    assert KEEP_ID in {row["evidence_id"] for row in projected["hits"]}
    assert all("patch_id" not in row for row in projected["hits"])

    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    panel = _section(html, "audit-hits")
    assert 'class="hit-as-of"' in panel
    assert 'class="hit-patch-id"' in panel
    assert 'class="hit-valid-from"' in panel
    assert 'class="hit-valid-to"' in panel
    assert 'data-hit-as-of="T1"' in panel
    assert 'data-hit-patch-id="b04-keep"' in panel
    assert 'data-hit-valid-from="2024-01-01"' in panel
    assert 'data-hit-valid-to="2026-12-31"' in panel
    assert "as_of T1" in panel
    assert "patch_id b04-keep" in panel
    assert "valid_from 2024-01-01" in panel
    assert "valid_to 2026-12-31" in panel
    assert PATCH_DROP not in panel
    assert DROP_ID not in panel
    assert "2019-01-01" not in panel
    assert "2020-01-01" not in panel
    assert "patch_id 无" in panel
    assert "valid_from 无" in panel
    assert "valid_to 无" in panel

    body = client.get("/api/claims").json()
    rows = {row["evidence_id"]: row for row in body["audit"]["hits"]}
    assert rows[KEEP_ID]["as_of"] == "T1"
    assert rows[KEEP_ID]["patch_id"] == PATCH_KEEP
    assert rows[KEEP_ID]["valid_from"] == "2024-01-01"
    assert rows[KEEP_ID]["valid_to"] == "2026-12-31"
    assert rows[BLANK_ID]["as_of"] == "T1"
    assert rows[BLANK_ID]["patch_id"] is None
    assert rows[BLANK_ID]["valid_from"] is None
    assert rows[BLANK_ID]["valid_to"] is None
    assert DROP_ID not in rows
    assert EXPIRED_ID not in rows


def test_trajectory_patch_fields_kept_when_store_misses(client, tmp_path):
    """事件里已经写出的四列直接上屏。库中没有该块时不把它们抹掉。"""
    path = tmp_path / "carried.jsonl"
    _write_jsonl(path, [{
        "type": "lead_step",
        "claim_id": "c-carry",
        "tool": "retrieve",
        "args": {"query": QUERY, "as_of": "T1"},
        "result": {
            "blocks": [{
                "evidence_id": KEEP_ID,
                "as_of": "T1",
                "patch_id": PATCH_KEEP,
                "valid_from": "2024-01-01",
                "valid_to": "2026-12-31",
                "text": "席位月费为九十九元。",
                "scores": {"bm25": None, "dense": None, "rrf": None, "rerank": None},
            }],
        },
    }])
    projected = project_audit(path)
    hit = projected["hits"][0]
    assert hit["patch_id"] == PATCH_KEEP
    assert hit["valid_from"] == "2024-01-01"
    assert hit["valid_to"] == "2026-12-31"
    assert hit["as_of"] == "T1"

    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    panel = _section(html, "audit-hits")
    assert 'data-hit-patch-id="b04-keep"' in panel
    assert "valid_from 2024-01-01" in panel
    assert "valid_to 2026-12-31" in panel
    page = (REPO / "src/freshlatch/ui/static/reverify.html").read_text(encoding="utf-8")
    assert "function auditPatchText" in page
    for key in ("as_of", "patch_id", "valid_from", "valid_to"):
        assert key in page.split("function auditPatchText", 1)[1].split("function auditScoreText", 1)[0]


def test_filter_stays_before_rrf_and_mode_unchanged():
    """融合公式与生产臂不动。过滤器仍写在 rrf_fuse 之前。"""
    for cls in (InMemoryStore, SQLiteStore):
        body = inspect.getsource(cls.retrieve)
        assert body.index("filter_patch_metadata") < body.index("rrf_fuse")
    base = (REPO / "src/freshlatch/store/base.py").read_text(encoding="utf-8")
    pipe = (REPO / "src/freshlatch/store/pipeline.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
    assert base.count("PRODUCTION_RETRIEVAL_MODE =") == 1
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert RRF_K == 60
    assert "RRF_K = 60" in pipe
    assert "1.0 / (k + rank)" in pipe
    assert FIXTURE.is_dir()
    assert not (REPO / "data" / "exp" / "x1").joinpath("b04-price-keep.md").exists()


def test_do_not_touch_paths_skip_when_base_missing():
    """有 base 时 Do-not-touch 路径不在 diff 里。缺 ref 则跳过。"""
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "origin/main^{commit}"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        extra = os.environ.get("GITHUB_BASE_REF", "").strip()
        if not extra:
            pytest.skip("origin/main 缺失,跳过 Do-not-touch git 路径检查")
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"origin/{extra}^{{commit}}"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if probe.returncode != 0:
            pytest.skip("无法解析 base,跳过 Do-not-touch git 路径检查")
        base = f"origin/{extra}"
    else:
        base = "origin/main"
    diff = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if diff.returncode != 0:
        pytest.skip("无法对 base 做 git diff,跳过 Do-not-touch git 路径检查")
    changed = [
        line.strip().replace("\\", "/")
        for line in diff.stdout.splitlines()
        if line.strip()
    ]
    for path in _DO_NOT_TOUCH:
        assert path not in changed
        assert not any(item == path or item.startswith(path + "/") for item in changed)
    assert not any(item.startswith("data/exp/x1/") for item in changed)
