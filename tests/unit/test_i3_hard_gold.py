"""I3 #251：Hard-Gold 骨架（分文件 · 不改臂 · traps/对抗≥30%）。

零 LLM。断言 PRODUCTION_RETRIEVAL_MODE == bm25。
#259：hard 臂对比与 A0 同库 = corpus + traps。
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from freshlatch.eval.retrieve_eval import (
    _ingest_eval_corpus,
    hard_gold_trap_adversarial_stats,
    run_arm_compare,
    run_hard_gold_retrieve,
)
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE, InMemoryStore
from freshlatch.store.ingest import load_corpus
from freshlatch.store.pipeline import pack_vec
from freshlatch.store.sqlite_store import SQLiteStore

ROOT = Path(__file__).resolve().parents[2]
HARD_GOLD = ROOT / "data" / "eval" / "retrieve_hard_gold.json"
SMOKE_GOLD = ROOT / "data" / "eval" / "retrieve_gold.json"
SPEC = ROOT / "docs" / "hard-gold.md"
CORPUS = ROOT / "data" / "corpus"
TRAPS = ROOT / "data" / "traps"


def test_spec_declares_skeleton_no_arm_change():
    body = SPEC.read_text(encoding="utf-8")
    assert "骨架" in body
    assert "不改臂" in body or "未授权改臂" in body
    assert "Hard-Gold" in body


def test_hard_gold_separate_file_from_smoke():
    assert HARD_GOLD.is_file()
    assert SMOKE_GOLD.is_file()
    assert HARD_GOLD.resolve() != SMOKE_GOLD.resolve()
    hard = json.loads(HARD_GOLD.read_text(encoding="utf-8"))
    smoke = json.loads(SMOKE_GOLD.read_text(encoding="utf-8"))
    assert hard.get("level") != "smoke"
    assert hard["queries"] != smoke["queries"]


def test_hard_gold_n_and_trap_ratio_preregistered():
    hard = json.loads(HARD_GOLD.read_text(encoding="utf-8"))
    stats = hard_gold_trap_adversarial_stats(hard)
    assert stats["n"] >= 20
    need = math.ceil(0.3 * stats["n"])
    assert stats["trap_adversarial_count"] >= need
    assert stats["trap_adversarial_ratio"] >= 0.30


def test_production_retrieval_mode_still_bm25():
    """Exit 硬断言：本波不改臂。"""
    assert PRODUCTION_RETRIEVAL_MODE == "bm25"


def test_run_hard_gold_bm25_report(tmp_path):
    out = run_hard_gold_retrieve(
        corpus=CORPUS,
        hard_gold_path=HARD_GOLD,
        trap_root=TRAPS,
        out_dir=tmp_path,
        dense_db=tmp_path / "no-dense.sqlite",  # 强制无 dense
    )
    assert out["production_retrieval_mode"] == "bm25"
    assert Path(out["report_path"]).is_file()
    body = Path(out["report_path"]).read_text(encoding="utf-8")
    assert "未授权改臂" in body or "不改臂" in body
    assert "bm25" in body.lower()
    assert out["stats"]["n"] >= 20
    raw = json.loads(Path(out["json_path"]).read_text(encoding="utf-8"))
    assert raw["production_retrieval_mode"] == "bm25"


def _write_dummy_dense(db_path: Path) -> int:
    """为 corpus+traps 写占位 vec（不打网；仅验同库 attached 与 BM25 列）。"""
    pairs = list(load_corpus(CORPUS)) + list(load_corpus(TRAPS))
    dim = 8
    n = 0
    store = SQLiteStore(db_path)
    for doc, chunks in pairs:
        for i, chunk in enumerate(chunks):
            # 确定性伪向量，避免全零导致余弦退化干扰模式标记
            vec = [0.0] * dim
            vec[i % dim] = 1.0
            chunk.vec = pack_vec(vec)
        store.add_document(doc, chunks)
        n += len(chunks)
    return n


def test_hard_arm_compare_same_corpus_as_a0(tmp_path):
    """#259：同库下臂对比 BM25 列须与 A0 R@10 一致（容差 0 保险丝不再假 fail）。"""
    a0_store = InMemoryStore()
    _ingest_eval_corpus(a0_store, CORPUS, trap_root=TRAPS)
    from freshlatch.eval.retrieve_eval import evaluate_retrieve, _load_json

    hard = _load_json(HARD_GOLD)
    a0_metrics = evaluate_retrieve(a0_store, hard)
    a0_path = tmp_path / "a0.json"
    a0_path.write_text(
        json.dumps({"metrics": {"recall": a0_metrics["recall"]}}, ensure_ascii=False),
        encoding="utf-8",
    )
    dense = tmp_path / "dense.sqlite"
    chunk_n = _write_dummy_dense(dense)
    assert chunk_n > 84  # 须含 traps
    arms = run_arm_compare(
        corpus=CORPUS,
        retrieve_gold_path=HARD_GOLD,
        dense_db=dense,
        a0_baseline_path=a0_path,
        out_dir=tmp_path,
        trap_root=TRAPS,
        report_name="retrieve-hard-gold-arm-compare.md",
        level_label="Hard-Gold hard 集",
    )
    assert arms["corpus_scope"] == "corpus+traps"
    assert arms["bm25_vs_a0"] == "pass"
    assert abs(arms["means"]["bm25"] - a0_metrics["recall"]["10"]) < 1e-9
    body = Path(arms["report_path"]).read_text(encoding="utf-8")
    assert "corpus+traps" in body
    assert "Hard-Gold" in body
