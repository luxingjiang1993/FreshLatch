"""神经 rerank 对照的纯函数。不下载权重。"""

from pathlib import Path

from freshlatch.eval.neural_rerank import (
    KEEP_LEXICAL,
    P95_BUDGET_MS,
    SUGGEST_TICKET,
    mcnemar_p,
    order_by_scores,
    recommend_neural_rerank,
    same_id_set,
)
from freshlatch.eval.retrieve_eval import ndcg_at_k
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

ROOT = Path(__file__).resolve().parents[2]


def test_production_mode_unchanged_and_reranker_not_in_prod_requirements():
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "bge-reranker" not in req
    assert "fastembed==0.7.1" in req
    extra = (ROOT / "requirements-eval-neural-rerank.txt").read_text(encoding="utf-8")
    assert "fastembed==0.8.1" in extra
    assert "bge-reranker" not in extra


def test_order_by_scores_breaks_ties_by_input_order():
    assert order_by_scores(["a", "b", "c"], [0.2, 0.9, 0.2]) == ["b", "a", "c"]


def test_ndcg_binary_matches_ideal_at_rank_one():
    assert ndcg_at_k(["gold", "other"], ["gold"], 10) == 1.0
    assert ndcg_at_k(["other", "gold"], ["gold"], 10) < 1.0


def test_k10_same_set_is_the_invalid_run_check():
    assert same_id_set(["a", "b"], ["b", "a"]) is True
    assert same_id_set(["a", "b"], ["a", "c"]) is False


def test_mcnemar_matches_issue_285_two_versus_fourteen():
    assert mcnemar_p(2, 14) == 0.004180908203124997
    assert mcnemar_p(0, 0) == 1.0


def test_recommendation_is_locked_before_numbers():
    assert P95_BUDGET_MS == 800.0
    assert (
        recommend_neural_rerank(
            ndcg_estimate=0.02,
            ndcg_ci_low=0.001,
            mrr_ci_low=0.001,
            p95_ms=100.0,
        )
        == SUGGEST_TICKET
    )
    assert (
        recommend_neural_rerank(
            ndcg_estimate=0.02,
            ndcg_ci_low=0.001,
            mrr_ci_low=0.001,
            p95_ms=800.1,
        )
        == KEEP_LEXICAL
    )
    assert (
        recommend_neural_rerank(
            ndcg_estimate=0.009,
            ndcg_ci_low=0.001,
            mrr_ci_low=0.001,
            p95_ms=10.0,
        )
        == KEEP_LEXICAL
    )
    assert (
        recommend_neural_rerank(
            ndcg_estimate=0.02,
            ndcg_ci_low=-0.001,
            mrr_ci_low=0.01,
            p95_ms=10.0,
        )
        == KEEP_LEXICAL
    )


def test_prereg_locks_the_decision_sentence():
    text = (ROOT / "docs/evidence/neural-rerank/PREREG.md").read_text(encoding="utf-8")
    assert "seed=20261007" in text or "种子 20261007" in text
    assert "10000" in text
    assert "800" in text
    assert "0.01" in text
    assert SUGGEST_TICKET in text
    assert KEEP_LEXICAL in text
    assert "不得改" in text
