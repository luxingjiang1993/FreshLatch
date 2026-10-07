"""#350:RERANK_MODE_NEURAL 登记在 models.py，旧导入路径再导出。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_rerank_mode_neural_is_registered_and_reexported():
    from freshlatch.models import MODEL_REGISTRY, RERANK_MODE_NEURAL as from_models
    from freshlatch.store.neural_rerank import RERANK_MODE_NEURAL as from_store

    assert from_models == "bge-reranker-base"
    assert from_store == from_models
    assert "judge_qwen" in MODEL_REGISTRY
    assert "judge_deepseek" in MODEL_REGISTRY
    assert "judge_kimi" in MODEL_REGISTRY
    store = (ROOT / "src/freshlatch/store/neural_rerank.py").read_text(encoding="utf-8")
    models = (ROOT / "src/freshlatch/models.py").read_text(encoding="utf-8")
    assert 'RERANK_MODE_NEURAL = "bge-reranker-base"' in models
    assert "RERANK_MODE_NEURAL =" not in store
    base = (ROOT / "src/freshlatch/store/base.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
