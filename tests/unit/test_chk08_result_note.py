"""#348:RESULT.md 原文不动，只在末尾追加 2026-10-08 注记。"""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE_SHA256 = "1678e3aeec1b98813a0a62e816b2e39b1af8b7ba9b0a04ac477b5e358f56f151"
MARKER = "\n## 注记（2026-10-08）\n"
HISTORICAL = (
    "- 额外依赖：`requirements-eval-neural-rerank.txt`（fastembed==0.8.1）。"
    "生产 `requirements.txt` 仍是 fastembed==0.7.1，不含 bge-reranker。"
)


def test_result_note_is_appended_without_rewriting_the_record():
    text = (ROOT / "docs/evidence/neural-rerank/RESULT.md").read_text(encoding="utf-8")
    body, note = text.split(MARKER, 1)
    assert hashlib.sha256(body.encode("utf-8")).hexdigest() == BASELINE_SHA256
    assert "2026-10-08" in MARKER
    assert "fastembed==0.8.1" in note
    assert "#344" in note
    script = (ROOT / "scripts/run_neural_rerank_compare.py").read_text(encoding="utf-8")
    assert HISTORICAL in script
