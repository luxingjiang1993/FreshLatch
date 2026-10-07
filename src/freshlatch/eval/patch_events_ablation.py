"""PE-04：只在 T 上打开消融开关。

四项各自写实验记录，arm 保持 T。hybrid+rerank 列单独记账，不并进主臂那一行。
本模块不改生产检索默认，不把消融行送进三条主比较，也不抽取另外三条随机流。
"""

from __future__ import annotations

import random
from collections.abc import Callable, Collection, Mapping, Sequence
from typing import Any

from freshlatch.eval.patch_events_arms import (
    Decoding,
    _bound_t1,
    _candidate_record,
    _number,
    _void_reason,
)
from freshlatch.eval.patch_events_exp import normalize_experiment_record
from freshlatch.eval.patch_events_metrics import ABLATION_ORDER, SEED, ablation_intervals
from freshlatch.llm import DEFAULT_MODEL
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

HYBRID_COLUMN = "hybrid+rerank"
_BM25_MODE = "bm25"
_PRIMARY_ARMS = ("C", "T", "B1", "B2")
_COLUMNS = (*ABLATION_ORDER, HYBRID_COLUMN)


def _retrieval_mode(column: str) -> str:
    if column == "retrieval_bm25":
        return _BM25_MODE
    return PRODUCTION_RETRIEVAL_MODE


def _gate(column: str) -> str:
    """hybrid+rerank 列沿用主臂 T 的全部闸。其余列只打开自己的那一项。"""
    if column == HYBRID_COLUMN:
        return ""
    return column


def _request(
    column: str,
    candidate: Mapping[str, Any],
    decoding: Decoding,
) -> dict[str, Any]:
    gate = _gate(column)
    return {
        "arm": "T",
        "phase": "rewrite",
        "ablation": gate,
        "ledger": HYBRID_COLUMN if column == HYBRID_COLUMN else "",
        "claim_id": candidate["claim_id"],
        "model": DEFAULT_MODEL,
        "temperature": decoding.temperature,
        "seed": decoding.seed,
        "retrieval_mode": _retrieval_mode(column),
        "before_text": candidate["before_text"],
        "evidence_id": candidate["evidence_id"],
        "evidence_text": candidate["evidence_text"],
        "edit_type": candidate["edit_type"],
    }


def _generate(
    column: str,
    candidate: Mapping[str, Any],
    generator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    decoding: Decoding,
) -> tuple[dict[str, Any] | None, str | None, float, float]:
    produced = generator(_request(column, candidate, decoding))
    if produced.get("void") or "after_text" not in produced:
        return None, "生成失败", 0.0, 0.0
    return dict(produced), None, _number(produced.get("latency_ms")), _number(produced.get("cost"))


def _finish(
    column: str,
    candidate: Mapping[str, Any],
    produced: Mapping[str, Any],
    *,
    decision: str,
    reject_reason: str,
    score: float | None,
    reverify_ok: bool | None,
    latency_ms: float,
    cost: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "claim_id": candidate["claim_id"],
        "edit_type": candidate["edit_type"],
        "arm": "T",
        "ablation": _gate(column),
        "construction_gold": candidate["construction_gold"],
        "before_text": candidate["before_text"],
        "after_text": str(produced["after_text"]),
        "evidence_id": str(produced.get("evidence_id") or ""),
        "evidence_text": candidate["evidence_text"],
        "decision": decision,
        "reject_reason": reject_reason,
        "score": score,
        "latency_ms": latency_ms,
        "cost": cost,
    }
    if reverify_ok is not None:
        payload["reverify_ok"] = reverify_ok
    return normalize_experiment_record(payload)


def _score(value: object) -> float | None:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _decide(
    column: str,
    produced: Mapping[str, Any],
    candidate: Mapping[str, Any],
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ingested: set[str],
) -> tuple[str, str, float | None, bool | None]:
    gate = _gate(column)
    evidence_id = str(produced.get("evidence_id") or "")
    if gate != "no_chunk_bind" and not _bound_t1(evidence_id, ingested):
        return "reject", "证据未绑定已入库 T1", None, False
    if gate == "no_auto_verify":
        return "release", "", None, None
    verdict = verifier(
        {
            "arm": "T",
            "ablation": gate,
            "ledger": HYBRID_COLUMN if column == HYBRID_COLUMN else "",
            "claim_id": candidate["claim_id"],
            "after_text": produced.get("after_text"),
            "evidence_id": evidence_id,
            "evidence_text": candidate["evidence_text"],
        }
    )
    ok = bool(verdict.get("ok"))
    score = _score(verdict.get("score"))
    reason = str(verdict.get("reason") or "核验未通过")
    if ok:
        return "release", "", score, True
    if gate == "soft_warning":
        return "release", reason, score, False
    return "reject", reason, score, False


def _cost_note(records: Sequence[Mapping[str, Any]]) -> str:
    if any(_number(row.get("cost")) > 0 for row in records):
        return ""
    return "没有调用"


def run_ablations(
    candidates: Sequence[object],
    *,
    generator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    decoding: Decoding,
    ingested_t1: Collection[str] = (),
) -> dict[str, Any]:
    """四项消融各写一份 T 记录，并另记 hybrid+rerank 列。"""
    ingested = set(ingested_t1)
    rows = [_candidate_record(item) for item in candidates]
    seen: set[str] = set()
    for row in rows:
        claim_id = str(row["claim_id"])
        if claim_id in seen:
            raise ValueError(f"claim_id 重复: {claim_id}")
        seen.add(claim_id)

    records: dict[str, list[dict[str, Any]]] = {column: [] for column in _COLUMNS}
    voids: list[dict[str, str]] = []
    blocked = _void_reason(decoding)
    for column in _COLUMNS:
        for candidate in rows:
            claim_id = str(candidate["claim_id"])
            if blocked is not None:
                voids.append({"claim_id": claim_id, "ablation": column, "reason": blocked})
                continue
            produced, failed, latency_ms, cost = _generate(column, candidate, generator, decoding)
            if produced is None:
                voids.append(
                    {
                        "claim_id": claim_id,
                        "ablation": column,
                        "reason": failed or "生成失败",
                    }
                )
                continue
            decision, reject_reason, score, reverify_ok = _decide(
                column, produced, candidate, verifier, ingested
            )
            records[column].append(
                _finish(
                    column,
                    candidate,
                    produced,
                    decision=decision,
                    reject_reason=reject_reason,
                    score=score,
                    reverify_ok=reverify_ok,
                    latency_ms=latency_ms,
                    cost=cost,
                )
            )
    return {
        **records,
        "voids": voids,
        "cost_notes": {column: _cost_note(records[column]) for column in _COLUMNS},
    }


def primary_comparison_rows(
    arm_result: Mapping[str, Any],
    ablation_result: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """三条主比较只收 C/T/B1/B2 里 ablation 为空的记录。消融结果整表不并入。"""
    del ablation_result
    rows: list[dict[str, Any]] = []
    for arm in _PRIMARY_ARMS:
        for row in arm_result[arm]:
            if row.get("ablation", "") != "":
                continue
            rows.append(row)
    return rows


def ablation_interval_report(
    main_rows: Sequence[Mapping[str, Any]],
    ablation_result: Mapping[str, Any],
    *,
    ingested_t1: Collection[str] = (),
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    """消融区间只消耗调用方传入的流。未传入时另起一条与 bootstrap_ablation 同种子的随机流。"""
    stream = rng if rng is not None else random.Random(SEED)
    flat = [
        row
        for row in main_rows
        if row.get("arm") == "T" and row.get("ablation", "") == ""
    ]
    for tag in ABLATION_ORDER:
        flat.extend(ablation_result[tag])
    return ablation_intervals(flat, ingested_t1=ingested_t1, rng=stream)
