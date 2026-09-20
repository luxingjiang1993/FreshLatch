"""3×3 混淆矩阵纯函数(§4.3):按 must_stale/must_fresh/must_unknown 报命中/漏判条数。

口径铁律:报条数,不报百分比——12 条小样本,百分比遮丑(#8)。
缺判(某主张无判定)计入漏判,预测值记 "missing",不并入 unknown 假装判过。
"""

from __future__ import annotations

from dataclasses import dataclass, field

BUCKETS = ("must_stale", "must_fresh", "must_unknown")
VERDICTS = ("fresh", "stale", "unknown")
MISSING = "missing"
EXPECTED_VERDICT = {"must_stale": "stale", "must_fresh": "fresh", "must_unknown": "unknown"}


@dataclass
class MatrixResult:
    counts: dict[str, dict[str, list[str]]] = field(default_factory=dict)  # bucket -> verdict -> [claim_id]
    hits: dict[str, int] = field(default_factory=dict)                       # bucket -> 命中条数
    misses: dict[str, list[dict]] = field(default_factory=dict)              # bucket -> [{claim_id, predicted}]

    @property
    def total(self) -> int:
        return sum(self.hits.values()) + sum(len(m) for m in self.misses.values())

    @property
    def all_hit(self) -> bool:
        return all(not m for m in self.misses.values())

    def to_dict(self) -> dict:
        return {"counts": self.counts, "hits": self.hits, "misses": self.misses,
                "total": self.total, "all_hit": self.all_hit}


def confusion_matrix(gold: dict, decisions: dict[str, str]) -> MatrixResult:
    """gold: gold.json 内容;decisions: {claim_id: 终态判定(fresh|stale|unknown)}。"""
    result = MatrixResult(counts={}, hits={}, misses={})
    for bucket in BUCKETS:
        by_verdict: dict[str, list[str]] = {v: [] for v in VERDICTS}
        hits, misses = 0, []
        for cid in gold[bucket]:
            predicted = decisions.get(cid, MISSING)
            if predicted in by_verdict:
                by_verdict[predicted].append(cid)
            if predicted == EXPECTED_VERDICT[bucket]:
                hits += 1
            else:
                misses.append({"claim_id": cid, "predicted": predicted,
                               "expected": EXPECTED_VERDICT[bucket]})
        result.counts[bucket] = by_verdict
        result.hits[bucket] = hits
        result.misses[bucket] = misses
    return result
