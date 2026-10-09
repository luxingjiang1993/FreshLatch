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


def _append_arm_record(
    records: dict[str, list[dict[str, Any]]],
    arm: str,
    candidate: Mapping[str, Any],
    produced: Mapping[str, Any],
    *,
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ingested: set[str],
    latency_ms: float,
    cost: float,
) -> None:
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


def run_arms(
    candidates: Sequence[object],
    *,
    generator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    decoding: Decoding,
    ingested_t1: Collection[str] = (),
) -> dict[str, Any]:
    """四组各写一份实验记录。作废的条目不记成放行。

    T 与 B1 共用同一份 rewrite after_text（以 T 请求生成一次），再分叉决策：
    T = 绑定∧核验；B1 = 仅核验；两边核验不过均 hard reject。C / B2 仍各自独立生成。
    """
    ingested = set(ingested_t1)
    rows = [_candidate_record(item) for item in candidates]
    reject_duplicate_claim_ids(rows)

    records: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
    voids: list[dict[str, str]] = []
    blocked = _void_reason(decoding)
    for candidate in rows:
        claim_id = str(candidate["claim_id"])
        if blocked is not None:
            for arm in ARMS:
                voids.append({"claim_id": claim_id, "arm": arm, "reason": blocked})
            continue

        # C：独立 rewrite，生成即放行。
        produced_c, failed_c, latency_c, cost_c = _generate_edit(
            "C", candidate, generator, decoding
        )
        if produced_c is None:
            voids.append({"claim_id": claim_id, "arm": "C", "reason": failed_c or "生成失败"})
        else:
            _append_arm_record(
                records,
                "C",
                candidate,
                produced_c,
                verifier=verifier,
                ingested=ingested,
                latency_ms=latency_c,
                cost=cost_c,
            )

        # T/B1 共享 after：以 T 臂请求生成一次 rewrite（含生产检索模式），
        # 再分别决策。禁止 B1 再独立生成，避免生成噪声盖住绑定缝。
        produced_shared, failed_shared, latency_shared, cost_shared = _generate_edit(
            "T", candidate, generator, decoding
        )
        if produced_shared is None:
            reason = failed_shared or "生成失败"
            voids.append({"claim_id": claim_id, "arm": "T", "reason": reason})
            voids.append({"claim_id": claim_id, "arm": "B1", "reason": reason})
        else:
            _append_arm_record(
                records,
                "T",
                candidate,
                produced_shared,
                verifier=verifier,
                ingested=ingested,
                latency_ms=latency_shared,
                cost=cost_shared,
            )
            _append_arm_record(
                records,
                "B1",
                candidate,
                produced_shared,
                verifier=verifier,
                ingested=ingested,
                latency_ms=latency_shared,
                cost=cost_shared,
            )

        # B2：独立 claim→diff；核验失败不 hard reject。
        produced_b2, failed_b2, latency_b2, cost_b2 = _generate_edit(
            "B2", candidate, generator, decoding
        )
        if produced_b2 is None:
            voids.append({"claim_id": claim_id, "arm": "B2", "reason": failed_b2 or "生成失败"})
        else:
            _append_arm_record(
                records,
                "B2",
                candidate,
                produced_b2,
                verifier=verifier,
                ingested=ingested,
                latency_ms=latency_b2,
                cost=cost_b2,
            )

    return {
        **records,
        "voids": voids,
        "cost_notes": {arm: cost_note(records[arm]) for arm in ARMS},
    }
