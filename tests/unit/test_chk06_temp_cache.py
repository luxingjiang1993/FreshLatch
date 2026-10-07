"""#338:神经精排证据脚本的缓存根来自 tempfile,不写死 /tmp。只读源码。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = (
    "- 额外依赖：`requirements-eval-neural-rerank.txt`（fastembed==0.8.1）。"
    "生产 `requirements.txt` 仍是 fastembed==0.7.1，不含 bge-reranker。"
)


def test_weight_bytes_cache_root_uses_tempdir():
    text = (ROOT / "scripts/run_neural_rerank_compare.py").read_text(encoding="utf-8")
    assert '"/tmp/fastembed_cache"' not in text
    assert "'/tmp/fastembed_cache'" not in text
    assert "import tempfile" in text
    assert "tempfile.gettempdir()" in text
    assert HISTORICAL in text
    base = (ROOT / "src/freshlatch/store/base.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
