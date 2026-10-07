"""PE-03：同一批候选上的 C / T / B1 / B2。

组别只写实验记录。不写产品账本，不改生产检索默认，不改生成默认模型。
温度或种子缺省则该次生成作废，不补成 0 再记成功。
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from freshlatch.eval.patch_events_exp import normalize_experiment_record
from freshlatch.eval.patch_events_rows import cost_note, reject_duplicate_claim_ids
from freshlatch.evidence_id import parse_evidence_id
from freshlatch.llm import DEFAULT_MODEL
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

ARMS: tuple[str, ...] = ("C", "T", "B1", "B2")


@dataclass(frozen=True)
class Decoding:
    """本次生成的温度和种子。缺一则作废，不用别的数填上。"""

    temperature: float | None
    seed: int | None


def _candidate_record(item: object) -> dict[str, Any]:
    if isinstance(item, Mapping):
        return dict(item)
    record = getattr(item, "record", None)
    if isinstance(record, dict):
        return dict(record)
    raise TypeError("候选须是实验记录或带 record 的构造结果")


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def _bound_t1(evidence_id: str, ingested: set[str]) -> bool:
    parsed = parse_evidence_id(evidence_id)
    if parsed is None:
        return False
    doc_id, anchor, as_of = parsed
    if as_of != "T1":
        return False
    return f"{doc_id}#{anchor}@T1" in ingested


def _generation_request(
    arm: str,
    phase: str,
    candidate: Mapping[str, Any],
    decoding: Decoding,
    *,
    retrieval_mode: str | None,
    claim_text: str = "",
) -> dict[str, Any]:
    return {
        "arm": arm,
        "phase": phase,
        "claim_id": candidate["claim_id"],
        "model": DEFAULT_MODEL,
        "temperature": decoding.temperature,
        "seed": decoding.seed,
        "retrieval_mode": retrieval_mode,
        "before_text": candidate["before_text"],
        "evidence_id": candidate["evidence_id"],
        "evidence_text": candidate["evidence_text"],
        "edit_type": candidate["edit_type"],
        "claim_text": claim_text,
    }


def _void_reason(decoding: Decoding) -> str | None:
    if decoding.temperature is None:
        return "温度缺省"
    if decoding.seed is None:
        return "种子缺省"
    return None


def _generate_edit(
    arm: str,
    candidate: Mapping[str, Any],
    generator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    decoding: Decoding,
) -> tuple[dict[str, Any] | None, str | None, float, float]:
    retrieval = PRODUCTION_RETRIEVAL_MODE if arm == "T" else None
    if arm != "B2":
        produced = generator(
            _generation_request(arm, "rewrite", candidate, decoding, retrieval_mode=retrieval)
        )
        if produced.get("void") or "after_text" not in produced:
            return None, "生成失败", 0.0, 0.0
        return dict(produced), None, _number(produced.get("latency_ms")), _number(produced.get("cost"))

    claim = generator(
        _generation_request(arm, "claim", candidate, decoding, retrieval_mode=None)
    )
    claim_text = str(claim.get("claim_text") or "")
    if claim.get("void") or not claim_text:
        return None, "生成失败", 0.0, 0.0
    diff = generator(
        _generation_request(
            arm,
            "diff",
            candidate,
            decoding,
            retrieval_mode=None,
            claim_text=claim_text,
        )
    )
    latency = _number(claim.get("latency_ms")) + _number(diff.get("latency_ms"))
    cost = _number(claim.get("cost")) + _number(diff.get("cost"))
    if diff.get("void") or "after_text" not in diff:
        return None, "生成失败", latency, cost
    return dict(diff), None, latency, cost


def _finish(
    arm: str,
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
    evidence_id = "" if arm == "C" else str(produced.get("evidence_id") or "")
    payload: dict[str, Any] = {
        "claim_id": candidate["claim_id"],
        "edit_type": candidate["edit_type"],
        "arm": arm,
        "ablation": "",
        "construction_gold": candidate["construction_gold"],
        "before_text": candidate["before_text"],
        "after_text": str(produced["after_text"]),
        "evidence_id": evidence_id,
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


def _decide(
    arm: str,
    produced: Mapping[str, Any],
    candidate: Mapping[str, Any],
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ingested: set[str],
) -> tuple[str, str, float | None, bool | None]:
    if arm == "C":
        return "release", "", None, None

    evidence_id = str(produced.get("evidence_id") or "")
    if arm == "T" and not _bound_t1(evidence_id, ingested):
        return "reject", "证据未绑定已入库 T1", None, False

    verdict = verifier(
        {
            "arm": arm,
            "claim_id": candidate["claim_id"],
            "after_text": produced.get("after_text"),
            "evidence_id": evidence_id,
            "evidence_text": candidate["evidence_text"],
        }
    )
    ok = bool(verdict.get("ok"))
    score = verdict.get("score")
    if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float))):
        score = None
    reason = str(verdict.get("reason") or "核验未通过")
    if arm == "B2":
        return "release", "", score, ok
    if ok:
        return "release", "", score, True
    return "reject", reason, score, False


def run_arms(
    candidates: Sequence[object],
    *,
    generator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    decoding: Decoding,
    ingested_t1: Collection[str] = (),
) -> dict[str, Any]:
    """四组各写一份实验记录。作废的条目不记成放行。"""
    ingested = set(ingested_t1)
    rows = [_candidate_record(item) for item in candidates]
    reject_duplicate_claim_ids(rows)

    records: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
    voids: list[dict[str, str]] = []
    blocked = _void_reason(decoding)
    for arm in ARMS:
        for candidate in rows:
            claim_id = str(candidate["claim_id"])
            if blocked is not None:
                voids.append({"claim_id": claim_id, "arm": arm, "reason": blocked})
                continue
            produced, failed, latency_ms, cost = _generate_edit(arm, candidate, generator, decoding)
            if produced is None:
                voids.append({"claim_id": claim_id, "arm": arm, "reason": failed or "生成失败"})
                continue
            decision, reject_reason, score, reverify_ok = _decide(
                arm, produced, candidate, verifier, ingested
            )
            records[arm].append(
                _finish(
                    arm,
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
        "cost_notes": {arm: cost_note(records[arm]) for arm in ARMS},
    }
