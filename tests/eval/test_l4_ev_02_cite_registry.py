"""L4-EV-02: citation registry 夹具进 CI。

确定性集合比较,直接调用 TurnRegistry / check_evidence_ids。
不调用付费 LLM,不跑 freshlatch.eval run,不断言质量闸 status=pass 或注册 A1 地板。

检查器正确时本文件为绿。若日后 registry 外的 id 被放行,outside 测试变红,CI 随之失败。
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from freshlatch.evidence import (
    CITE_OUTSIDE_REGISTRY,
    TurnRegistry,
    check_evidence_ids,
    registry_refusal_code,
)
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import RRF_K

REPO = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "l4_ev_02_registry_cite.json"

_DO_NOT_TOUCH = (
    "src/freshlatch/eval/quality_gate.py",
    "src/freshlatch/evidence.py",
    "src/freshlatch/roles/lead.py",
    "src/freshlatch/roles/loop.py",
    "src/freshlatch/store/base.py",
    "src/freshlatch/store/pipeline.py",
    "src/freshlatch/store/neural_rerank.py",
    "src/freshlatch/store/local_embed.py",
    "pyproject.toml",
    "requirements.txt",
    "requirements-eval-neural-rerank.txt",
    ".github/workflows/ci.yml",
    "CONTEXT.md",
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

_PAID_SECRET_NAMES = (
    "DASHSCOPE_API_KEY",
    "DEEPSEEK_API_KEY",
    "MOONSHOT_API_KEY",
)


def _load_fixture() -> dict:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    registry = payload["registry"]
    assert isinstance(registry, list) and registry
    assert payload["outside"] and payload["subset"]
    for group in (payload["outside"], payload["subset"]):
        for case in group:
            assert case["claim_id"]
            assert case["evidence_ids"]
            assert all(item.endswith("@T1") for item in case["evidence_ids"])
    assert all(item.endswith("@T1") for item in registry)
    return payload


def check_fixture_cite(evidence_ids: list[str], registry_ids: list[str]):
    """对本轮 TurnRegistry 做确定性集合比较。

    返回 (通过时的 id 列表或 None, 拒因码或 None)。
    registry 外的 id 得到 cite_outside_registry;子集得到 None。
    """
    registry = TurnRegistry()
    registry.admit(registry_ids)
    ids, err = check_evidence_ids(evidence_ids, registry, require_t1=True)
    return ids, registry_refusal_code(err)


def test_fixture_outside_registry_refused():
    """验收 1:夹具主张引用 registry 外 id 时,检查器返回 cite_outside_registry。"""
    payload = _load_fixture()
    registry_ids = payload["registry"]
    registry_set = set(registry_ids)
    for case in payload["outside"]:
        cited = case["evidence_ids"]
        assert not set(cited) <= registry_set
        ids, code = check_fixture_cite(cited, registry_ids)
        assert ids is None
        assert code == CITE_OUTSIDE_REGISTRY


def test_fixture_subset_passes():
    """验收 2:引用集合是 registry 子集时,检查器放行并原样返回这些 id。"""
    payload = _load_fixture()
    registry_ids = payload["registry"]
    registry_set = set(registry_ids)
    for case in payload["subset"]:
        cited = case["evidence_ids"]
        assert set(cited) <= registry_set
        ids, code = check_fixture_cite(cited, registry_ids)
        assert code is None
        assert ids == cited


def test_fixture_lives_under_tests():
    """夹具只放 tests/,不放 data/exp/x1/。"""
    rel = FIXTURE.relative_to(REPO).as_posix()
    assert rel.startswith("tests/")
    assert not rel.startswith("data/exp/x1/")
    assert FIXTURE.is_file()


def test_ci_workflow_has_no_llm_eval_or_quality_pass():
    """验收 3:现有 pytest tests/ 已覆盖 tests/eval。工作流无 LLM runner、无付费密钥、无 status=pass。"""
    text = (REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "python -m pytest tests/" in text
    assert "freshlatch.eval run" not in text
    assert "status=pass" not in text
    for name in _PAID_SECRET_NAMES:
        assert name not in text


def test_frozen_retrieval_pins():
    """检索常量不依赖 git,浅克隆也必须跑。"""
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert RRF_K == 60
    assert NEURAL_RERANK_K == 10


def _git_base_ref() -> str | None:
    """解析对比基线。浅克隆没有 origin/main 时返回 None,不 fetch。"""
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
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return ref
    return None


def test_do_not_touch_paths_skip_when_base_missing():
    """有 base 时 Do-not-touch 与 score_citation_overlap 所在文件不在 diff 里。

    缺少 base ref 时 skip,避免 git diff 以 128 失败。
    """
    base = _git_base_ref()
    if base is None:
        pytest.skip("origin/main 缺失,跳过 Do-not-touch git 路径检查")
    diff = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=REPO,
        capture_output=True,
        text=True,
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
    overlap = subprocess.run(
        [
            "git", "diff", "--name-only", base, "--",
            "src/freshlatch/eval/quality_gate.py",
            "data/eval/cite_sentence.json",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if overlap.returncode != 0:
        pytest.skip(
            "无法对 base 做 git diff,跳过 citation 文件检查: "
            + (overlap.stderr or "").strip()
        )
    assert overlap.stdout.strip() == ""
