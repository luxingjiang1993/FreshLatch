"""I3 #251：Hard-Gold 骨架（分文件 · 不改臂 · traps/对抗≥30%）。

零 LLM。断言 PRODUCTION_RETRIEVAL_MODE == bm25。
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from freshlatch.eval.retrieve_eval import (
    hard_gold_trap_adversarial_stats,
    run_hard_gold_retrieve,
)
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

ROOT = Path(__file__).resolve().parents[2]
HARD_GOLD = ROOT / "data" / "eval" / "retrieve_hard_gold.json"
SMOKE_GOLD = ROOT / "data" / "eval" / "retrieve_gold.json"
SPEC = ROOT / "docs" / "hard-gold.md"


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
        corpus=ROOT / "data" / "corpus",
        hard_gold_path=HARD_GOLD,
        trap_root=ROOT / "data" / "traps",
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
