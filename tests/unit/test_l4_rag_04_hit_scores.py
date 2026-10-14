"""L4-RAG-04: hit 可测分、rerank ON/OFF manifest、显式 BM25 不记 bm25_fallback。

夹具确定性,不调用付费 LLM,不重跑 224 题。
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from freshlatch.models import NEURAL_RERANK_MODEL, Claim
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import RunContext
from freshlatch.store.base import (
    PRODUCTION_RETRIEVAL_MODE,
    Chunk,
    Document,
    InMemoryStore,
    chunk_evidence_id,
)
from freshlatch.store.neural_rerank import NEURAL_RERANK_K, RERANK_MODE_LEXICAL, RERANK_MODE_NEURAL
from freshlatch.store.pipeline import HIT_SCORE_FIELDS, RRF_K, pack_vec
from freshlatch.store.sqlite_store import SQLiteStore

REPO_FILES = {
    "base": "src/freshlatch/store/base.py",
    "pipeline": "src/freshlatch/store/pipeline.py",
    "neural": "src/freshlatch/store/neural_rerank.py",
    "pyproject": "pyproject.toml",
    "models": "src/freshlatch/models.py",
}

_DO_NOT_TOUCH = (
    "src/freshlatch/store/base.py",
    "docs/evidence/patch-events/RESULT-Y.md",
    "docs/evidence/patch-events/PREREG-Y.md",
    "docs/evidence/quality-gate/PREREG.md",
    "docs/evidence/neural-rerank/summary.json",
    "docs/evidence/neural-rerank/per-query.json",
    "data/eval/guard_should.json",
    "data/eval/cite_sentence.json",
    "data/eval/temporal_new_over_old.json",
    "data/eval/gold.json",
)


def _chunk(doc_id: str, text: str, vec: list[float] | None, *, clause: str = "p1") -> Chunk:
    return Chunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}::chunk-{clause}@T1",
        clause_id=clause,
        title="t",
        text=text,
        source_type="private",
        as_of="T1",
        doc_version="v1",
        checksum="c",
        tokens=4,
        vec=None if vec is None else pack_vec(vec),
    )


def _doc() -> Document:
    return Document(
        doc_id="d",
        as_of="T1",
        source_type="private",
        title="t",
        doc_version="v1",
        checksum="c",
        full_text="x",
    )


class _PreferTail:
    """神经精排把「旁注」放到前面。不加载模型。"""

    def rerank(self, query: str, docs: list[str]) -> list[float]:
        return [1.0 if "旁注" in doc else 0.0 for doc in docs]


def _enable(monkeypatch, encoder) -> None:
    monkeypatch.setenv("FRESHLATCH_NEURAL_RERANK", "1")
    monkeypatch.setattr(
        "freshlatch.store.neural_rerank._load_encoder",
        lambda: encoder,
    )


def _hybrid_store() -> InMemoryStore:
    store = InMemoryStore()
    # 两块语料时 BM25Okapi 的 IDF 为 0,词面分会被 s>0 滤掉。第三块只为把 IDF 抬成正数。
    store.add_document(
        _doc(),
        [
            _chunk("head", "席位标价已经改写", [1.0, 0.0]),
            _chunk("tail", "无关旁注", [0.0, 1.0], clause="p2"),
            _chunk("other", "其它段落完全无关", [0.0, 0.0], clause="p3"),
        ],
    )
    store.query_embedder = lambda _q: [1.0, 0.0]
    return store


def _assert_distinguishable(scores: dict) -> None:
    assert set(scores) == set(HIT_SCORE_FIELDS)
    comparable = []
    for name in HIT_SCORE_FIELDS:
        value = scores[name]
        assert value is None or isinstance(value, float)
        comparable.append(None if value is None else value)
    assert len(set(comparable)) >= 2


def test_frozen_pins_always_run():
    """不依赖 git。浅克隆也要锁住检索常量。"""
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert RRF_K == 60
    assert NEURAL_RERANK_K == 10
    assert NEURAL_RERANK_MODEL == "BAAI/bge-reranker-base"
    base = Path(REPO_FILES["base"]).read_text(encoding="utf-8")
    pipeline = Path(REPO_FILES["pipeline"]).read_text(encoding="utf-8")
    neural = Path(REPO_FILES["neural"]).read_text(encoding="utf-8")
    pyproject = Path(REPO_FILES["pyproject"]).read_text(encoding="utf-8")
    models = Path(REPO_FILES["models"]).read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
    assert "RRF_K = 60" in pipeline
    assert "scores[eid] += 1.0 / (k + rank)" in pipeline
    assert "NEURAL_RERANK_K = 10" in neural
    assert "fastembed==0.8.1" in pyproject
    assert "BAAI/bge-small-zh-v1.5" in models
    assert "BAAI/bge-reranker-base" in models
    assert "counted_as_pass = true" not in pipeline.lower()
    assert "counted_as_pass = true" not in neural.lower()


def test_tool_observation_has_distinguishable_scores_and_rejects_mode(monkeypatch):
    """验收 1: hybrid+rerank 观察里每个 hit 有可区分分字段,模型传 retrieval_mode 被拒。"""
    _enable(monkeypatch, _PreferTail())
    store = _hybrid_store()
    ctx = RunContext(store=store, mode="online")
    lead = LeadReverifier(ctx, Claim(claim_id="c-rag04", statement="席位标价"), llm=None)
    rejected = lead._t_retrieve({
        "query": "模型自拟",
        "as_of": "T1",
        "retrieval_mode": "dense",
    })
    assert rejected == {"error": "生产路径不可指定 retrieval_mode"}
    assert ctx.retrieval_used == 0
    assert not any(event.get("type") == "retrieve" for event in ctx.events)

    observation = lead._t_retrieve({"query": "模型自拟", "as_of": "T1"})
    assert observation["retrieval_mode"] == "hybrid+rerank"
    assert observation["rerank_mode"] == RERANK_MODE_NEURAL
    assert observation["grade"] == "correct"
    assert observation["sufficiency"] == "sufficient"
    assert observation["grade_token"] == "grade=correct"
    assert "error" not in observation
    blocks = observation["blocks"]
    assert len(blocks) >= 2
    for block in blocks:
        assert set(block) >= {"evidence_id", "as_of", "source_type", "text", "scores"}
        _assert_distinguishable(block["scores"])
    by_id = {block["evidence_id"]: block["scores"] for block in blocks}
    assert by_id["head#p1@T1"] != by_id["tail#p2@T1"]
    assert by_id["tail#p2@T1"]["rerank"] == 1.0
    assert by_id["head#p1@T1"]["rerank"] == 0.0
    assert by_id["head#p1@T1"]["dense"] == 1.0
    assert by_id["tail#p2@T1"]["dense"] == 0.0
    assert by_id["head#p1@T1"]["bm25"] is not None
    assert by_id["head#p1@T1"]["rrf"] is not None
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"


def test_score_book_does_not_change_hit_order(monkeypatch):
    """记分不改融合结果。无 book 的直接 retrieve 与 try_retrieve 的 id 序一致。"""
    _enable(monkeypatch, _PreferTail())
    store = _hybrid_store()
    store.bind_eval_retrieval_mode("hybrid+rerank")
    plain = [chunk_evidence_id(chunk) for chunk in store.retrieve("席位标价", as_of="T1", top_k=2)]
    store.bind_eval_retrieval_mode(None)
    ctx = RunContext(store=store, mode="online")
    watched = ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert [chunk_evidence_id(chunk) for chunk in watched] == plain
    assert plain[0] == "tail#p2@T1"


def test_manifest_separates_rerank_on_and_off(monkeypatch):
    """验收 2: 同一夹具的两次 manifest 分出 rerank on 与 off,不改生产常量。"""
    _enable(monkeypatch, _PreferTail())
    store = _hybrid_store()
    ctx = RunContext(store=store, mode="online")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    on = ctx.last_retrieval_manifest
    ctx.set_retrieval_switch("hybrid+rerank_lexical")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    off = ctx.last_retrieval_manifest
    assert on["rerank"] == "on"
    assert off["rerank"] == "off"
    assert on["retrieval_mode"] == "hybrid+rerank"
    assert off["retrieval_mode"] == "hybrid+rerank_lexical"
    assert on["rerank_mode"] == RERANK_MODE_NEURAL
    assert off["rerank_mode"] == RERANK_MODE_LEXICAL
    assert on["production_retrieval_mode"] == "hybrid+rerank"
    assert off["production_retrieval_mode"] == "hybrid+rerank"
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert [row["evidence_id"] for row in on["hits"]] != [
        row["evidence_id"] for row in off["hits"]
    ]
    assert on["hits"][0]["evidence_id"] == "tail#p2@T1"
    assert off["hits"][0]["evidence_id"] == "head#p1@T1"
    for row in on["hits"] + off["hits"]:
        _assert_distinguishable(row["scores"])


def test_explicit_bm25_switch_is_not_fallback():
    """验收 3: 运维开关切到 bm25 时 last_retrieval_mode 不是 bm25_fallback。"""
    bare = InMemoryStore()
    bare.add_document(_doc(), [_chunk("bare", "席位标价已经改写", None)])
    ctx = RunContext(store=bare, mode="online")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert bare.last_retrieval_mode == "bm25_fallback"
    ctx.set_retrieval_switch("bm25")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert bare.last_retrieval_mode == "bm25"
    assert ctx.events[-1]["retrieval_mode"] == "bm25"
    assert ctx.last_retrieval_manifest["retrieval_mode"] == "bm25"
    assert ctx.last_retrieval_manifest["rerank"] != "on"
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"

    armed = _hybrid_store()
    armed_ctx = RunContext(store=armed, mode="online")
    armed_ctx.set_retrieval_switch("bm25")
    armed_ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert armed.last_retrieval_mode == "bm25"
    assert armed.last_retrieval_mode != "bm25_fallback"


def test_sqlite_explicit_bm25_switch_is_not_fallback(tmp_path):
    """SQLite 同一规则:缺向量才是 bm25_fallback,显式开关记 bm25。"""
    store = SQLiteStore(tmp_path / "rag04.db")
    store.add_document(_doc(), [_chunk("bare", "席位标价已经改写", None)])
    ctx = RunContext(store=store, mode="online")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert store.last_retrieval_mode == "bm25_fallback"
    ctx.set_retrieval_switch("bm25")
    ctx.try_retrieve("席位标价", as_of="T1", top_k=2)
    assert store.last_retrieval_mode == "bm25"
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"


def _git_base_ref() -> str | None:
    """浅克隆没有 origin/main 时返回 None,不 fetch。"""
    candidates = ["origin/main"]
    extra = os.environ.get("GITHUB_BASE_REF", "").strip()
    if extra:
        candidates.append(f"origin/{extra}")
    seen: list[str] = []
    for ref in candidates:
        if ref in seen:
            continue
        seen.append(ref)
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=".",
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return ref
    return None


def test_do_not_touch_paths_skip_when_base_missing():
    """有 base 时 Do-not-touch 路径不在 diff 里。缺 ref 则跳过,避免 CI exit 128。"""
    base = _git_base_ref()
    if base is None:
        pytest.skip("origin/main 缺失,跳过 Do-not-touch git 路径检查")
    diff = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=".",
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if diff.returncode != 0:
        pytest.skip(
            "无法对 base 做 git diff,跳过 Do-not-touch git 路径检查: "
            + (diff.stderr or "").strip()
        )
    changed = [line.strip().replace("\\", "/") for line in diff.stdout.splitlines() if line.strip()]
    for path in _DO_NOT_TOUCH:
        assert path not in changed
    assert not any(path.startswith("data/exp/x1/") for path in changed)
