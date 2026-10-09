"""路线 C：强制抄句（copy-constrained）生成契约。

叠在已验证的 B 机制之上（选取 R · T/B1 同 after · 核验硬门），
只提供 C 旁路入口；默认不改 B 臂自由改写路径。

T 的 rewrite after_text 由硬契约产出（= 请求内 evidence_text 原文），
不是 B 的软提示对齐。B1 仍经 ``run_arms`` 同 after 再分叉。
不放松 ``verify_edit`` / 绑定闸 / hard reject。
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from typing import Any

from freshlatch.eval.patch_events_arms import Decoding, run_arms


def forced_copy_after_text(evidence_text: object) -> str:
    """硬契约：after 为证据句原文（供 T rewrite；核验仍为 after.strip()==evidence）。"""
    if not isinstance(evidence_text, str):
        raise TypeError("evidence_text 须为 str")
    return evidence_text


def correct_slot_is_copyable(candidate: Mapping[str, Any]) -> bool:
    """正确金标槽须保证可抄：evidence_text 为非空（去空白后仍有内容）。

    坏槽不在此强制；不可抄的正确槽由调用方作废换条，算子不改矮。
    """
    if str(candidate.get("construction_gold") or "") != "正确":
        return True
    evidence = candidate.get("evidence_text")
    return isinstance(evidence, str) and evidence.strip() != ""


def make_copy_constrained_generator(
    inner: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> Callable[[Mapping[str, Any]], Mapping[str, Any]]:
    """包装生成器：T/rewrite 强制抄句；其余臂/阶段交给 inner（缺省则非 T 路径失败）。"""

    def generator(request: Mapping[str, Any]) -> dict[str, Any]:
        arm = str(request.get("arm") or "")
        phase = str(request.get("phase") or "")
        if arm == "T" and phase == "rewrite":
            evidence_text = request.get("evidence_text")
            after = forced_copy_after_text(evidence_text)
            return {
                "after_text": after,
                "evidence_id": str(request.get("evidence_id") or ""),
                "latency_ms": 0.0,
                "cost": 0.0,
                "copy_constrained": True,
            }
        if inner is None:
            return {"void": True, "reason": "非 T/rewrite 且未提供 inner 生成器"}
        return dict(inner(request))

    return generator


def run_arms_c(
    candidates: Sequence[object],
    *,
    generator: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    decoding: Decoding,
    ingested_t1: Collection[str] = (),
    enforce_copyable_correct: bool = True,
) -> dict[str, Any]:
    """路线 C 四臂入口：T 强制抄句 + 继承 ``run_arms`` 同 after 再分叉。

    ``enforce_copyable_correct`` 为真时，不可抄的正确槽整条作废（四臂记 void），
    不把坏样改成「抄对仍标坏」。
    """
    rows: list[Any] = list(candidates)
    if enforce_copyable_correct:
        kept: list[Any] = []
        pre_voids: list[dict[str, str]] = []
        for item in rows:
            if isinstance(item, Mapping):
                record = dict(item)
            else:
                raw = getattr(item, "record", None)
                record = dict(raw) if isinstance(raw, dict) else None
            if record is None:
                kept.append(item)
                continue
            if not correct_slot_is_copyable(record):
                claim_id = str(record.get("claim_id") or "")
                for arm in ("C", "T", "B1", "B2"):
                    pre_voids.append(
                        {
                            "claim_id": claim_id,
                            "arm": arm,
                            "reason": "正确槽不可抄（evidence_text 空）",
                        }
                    )
                continue
            kept.append(item)
        rows = kept
    else:
        pre_voids = []

    wrapped = make_copy_constrained_generator(generator)
    result = run_arms(
        rows,
        generator=wrapped,
        verifier=verifier,
        decoding=decoding,
        ingested_t1=ingested_t1,
    )
    if pre_voids:
        result = {**result, "voids": [*pre_voids, *list(result.get("voids") or [])]}
    return result
