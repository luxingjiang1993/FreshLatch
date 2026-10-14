"""L4-EV-T1-CASE: 冻结名次上的 T1 个案锁。

只读 `per-query.json` 与 `temporal_new_over_old.json`。
不新增通过线,不改质量闸退出码。c2 是反序,c3 是双缺失,两者分开锁。
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess

import pytest

from freshlatch.eval import quality_gate as qg
from freshlatch.eval.retrieve_typed import conflict_pair_correct
from freshlatch.packs import repo_root

ROOT = repo_root()
PER_QUERY = ROOT / "docs" / "evidence" / "neural-rerank" / "per-query.json"
TEMPORAL = ROOT / "data" / "eval" / "temporal_new_over_old.json"
QUALITY_GATE = "src/freshlatch/eval/quality_gate.py"

# 诊断 §4.3 写死的条款 id。改金标必须先改这里,否则个案锁失败。
_FROZEN_PAIRS = {
    "s6-d1-c1-q1": ("p1-cac-o16#p9@T1", "p1-cac-o11#p13@T1"),
    "s6-d1-c2-q1": ("p1-cac-o16#p7@T1", "p1-cac-o11#p2@T1"),
    "s6-d1-c3-q1": ("p1-cac-o16#p8@T1", "p1-cac-o13#p2@T1"),
}
_TRAP_GOLD_ID = "tno-trap-supersede-1"
_TRAP_SOURCE_REF = "trap-supersede-1"
_R1_FLOORS = ("R1_RECALL_AT_10_FLOOR", "R1_MRR_AT_10_FLOOR")
_COUNTED_PASS_TRUE = re.compile(r"counted_as_pass\s*=\s*true", re.IGNORECASE)
_PERCENT_FLOOR = re.compile(
    r"(?i)(?:_FLOOR\s*=\s*\d|floor\s*=\s*\d|\d+(?:\.\d+)?\s*%)"
)


def _load() -> tuple[dict[str, list[str]], dict]:
    rows = json.loads(PER_QUERY.read_text(encoding="utf-8"))
    gold = json.loads(TEMPORAL.read_text(encoding="utf-8"))
    assert isinstance(rows, list)
    ranked_by_id: dict[str, list[str]] = {}
    for row in rows:
        qid = str(row["id"])
        assert qid not in ranked_by_id
        ranked = row["k10"]["neural_ranked"]
        assert isinstance(ranked, list)
        ranked_by_id[qid] = [str(part) for part in ranked]
    return ranked_by_id, gold


def _keep_item(gold: dict, qid: str) -> dict:
    items = [
        item
        for item in gold["items"]
        if isinstance(item, dict) and qid in item.get("source_refs", [])
    ]
    assert len(items) == 1
    item = items[0]
    assert item["disposition"] == "keep"
    return item


def _frozen_pair(gold: dict, qid: str) -> tuple[str, str]:
    item = _keep_item(gold, qid)
    in_force = str(item["in_force"])
    superseded = str(item["superseded"])
    expected_in_force, expected_superseded = _FROZEN_PAIRS[qid]
    assert in_force == expected_in_force
    assert superseded == expected_superseded
    return in_force, superseded


def test_c1_in_force_ranks_before_superseded():
    """验收 1: s6-d1-c1-q1 的 in_force 下标小于 superseded。"""
    ranked_by_id, gold = _load()
    qid = "s6-d1-c1-q1"
    in_force, superseded = _frozen_pair(gold, qid)
    ranked = ranked_by_id[qid]
    # 诊断 §4.3: in_force 第 1 位, superseded 第 3 位。
    assert ranked.index(in_force) == 0
    assert ranked.index(superseded) == 2
    assert ranked.index(in_force) < ranked.index(superseded)
    assert conflict_pair_correct(ranked, {"in_force": in_force, "superseded": superseded}) is True


def test_c2_superseded_ranks_before_in_force():
    """验收 2: s6-d1-c2-q1 反序, superseded 下标小于 in_force。"""
    ranked_by_id, gold = _load()
    qid = "s6-d1-c2-q1"
    in_force, superseded = _frozen_pair(gold, qid)
    ranked = ranked_by_id[qid]
    # 诊断 §4.3: superseded 第 3 位, in_force 第 4 位。两条都在列表里。
    assert ranked.index(superseded) == 2
    assert ranked.index(in_force) == 3
    assert ranked.index(superseded) < ranked.index(in_force)
    assert conflict_pair_correct(ranked, {"in_force": in_force, "superseded": superseded}) is False


def test_c3_both_clauses_absent_from_neural_ranked():
    """验收 3: s6-d1-c3-q1 的 in_force 与 superseded 都不在列表中。"""
    ranked_by_id, gold = _load()
    qid = "s6-d1-c3-q1"
    in_force, superseded = _frozen_pair(gold, qid)
    ranked = ranked_by_id[qid]
    # 诊断 §4.3: 双缺失。两条都不在时 conflict_pair_correct 为假。
    assert in_force not in ranked
    assert superseded not in ranked
    assert conflict_pair_correct(ranked, {"in_force": in_force, "superseded": superseded}) is False


def test_trap_id_absent_matches_unresolved():
    """验收 4: tno-trap-supersede-1 不在 per-query id 集合,与 unresolved 一致。"""
    ranked_by_id, gold = _load()
    assert _TRAP_GOLD_ID not in ranked_by_id
    item = next(row for row in gold["items"] if row["id"] == _TRAP_GOLD_ID)
    assert item["disposition"] == "keep"
    assert item["source_refs"] == [_TRAP_SOURCE_REF]
    assert _TRAP_SOURCE_REF not in ranked_by_id
    score = qg.score_new_over_old_accuracy([item], ranked_by_id)
    assert score.n == 1
    assert score.scored == 0
    assert score.correct == 0
    assert score.unresolved == 1
    assert score.value == "unavailable"

    keep = [row for row in gold["items"] if row.get("disposition") == "keep"]
    assert [row["id"] for row in keep] == [
        _TRAP_GOLD_ID,
        "tno-s6-d1-c1-q1",
        "tno-s6-d1-c2-q1",
        "tno-s6-d1-c3-q1",
    ]
    # 四条 keep 合在一起: trap 为 unresolved,正确只来自 c1。计数来自诊断 §4.3。
    combined = qg.score_new_over_old_accuracy(keep, ranked_by_id)
    assert (combined.n, combined.scored, combined.correct, combined.unresolved) == (4, 3, 1, 1)


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
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return ref
    return None


def _added_diff_lines(diff_text: str) -> list[str]:
    added: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            added.append(line[1:])
    return added


def _assert_counted_as_pass_keywords_are_false(source: str) -> None:
    tree = ast.parse(source)
    found = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.keyword) or node.arg != "counted_as_pass":
            continue
        assert isinstance(node.value, ast.Constant)
        assert node.value.value is False
        found += 1
    assert found > 0


def test_quality_gate_diff_does_not_pass_t1_or_add_percent_floor():
    """验收 5: 质量闸源码 diff 不把 conflict-pair 或 T1 设成通过,也不加百分数地板。"""
    source_path = ROOT / QUALITY_GATE
    source = source_path.read_text(encoding="utf-8")
    _assert_counted_as_pass_keywords_are_false(source)
    floor_names = [name for name in vars(qg) if name.endswith("_FLOOR")]
    assert tuple(floor_names) == _R1_FLOORS

    base = _git_base_ref()
    if base is None:
        pytest.skip("origin/main 缺失,跳过质量闸源码 diff 检查")
    diff = subprocess.run(
        ["git", "diff", "-U0", base, "--", QUALITY_GATE],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if diff.returncode != 0:
        pytest.skip(
            "无法对 base 做 git diff,跳过质量闸源码 diff 检查: "
            + (diff.stderr or "").strip()
        )
    for line in _added_diff_lines(diff.stdout or ""):
        assert _COUNTED_PASS_TRUE.search(line) is None, line
        assert _PERCENT_FLOOR.search(line) is None, line
