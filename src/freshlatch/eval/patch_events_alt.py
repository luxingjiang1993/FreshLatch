"""平行轨旁路：同文四闸 + ``compare_alt_natural``。

层身份：设计探针 / 冒烟（平行轨）。不报方差；不作统计显著；
可分开 ≠ 甲；本轨数字不得填冲甲 RESULT。

只读复用 ``verify_edit`` 与 T1 绑定语义；不改 ``compare_primary``，
不写 ``docs/evidence/patch-events/PREREG.md`` / 主 ``RESULT.md``。
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from typing import Any

from freshlatch.eval.patch_events_verify import verify_edit
from freshlatch.evidence_id import parse_evidence_id

ARMS: tuple[str, ...] = ("C", "T", "B1", "B2")
CONTRASTS: tuple[str, ...] = ("B1", "B2")


def _bound_t1(evidence_id: str, ingested: set[str]) -> bool:
    parsed = parse_evidence_id(evidence_id)
    if parsed is None:
        return False
    doc_id, anchor, as_of = parsed
    if as_of != "T1":
        return False
    return f"{doc_id}#{anchor}@T1" in ingested


def _has_after_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def decide_same_text_gate(
    arm: str,
    candidate: Mapping[str, Any],
    *,
    ingested_t1: Collection[str] = (),
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]] = verify_edit,
) -> dict[str, Any]:
    """同文单臂闸判。``arm`` 为 C/T/B1/B2；B1 语义为 B1′（无 evidence_id）。"""
    if arm not in ARMS:
        raise ValueError(f"arm 非法: {arm!r}")

    after_text = candidate.get("after_text")
    claim_id = str(candidate["claim_id"])
    gold = candidate["construction_gold"]
    ingested = set(ingested_t1)

    if arm == "C":
        return {
            "claim_id": claim_id,
            "arm": "C",
            "construction_gold": gold,
            "after_text": after_text if isinstance(after_text, str) else "",
            "evidence_id": "",
            "evidence_text": "",
            "decision": "release",
            "reject_reason": "",
            "reverify_ok": None,
        }

    evidence_text = str(candidate.get("evidence_text") or "")

    if arm == "B2":
        reverify: Mapping[str, Any] | None = None
        if _has_after_text(after_text):
            reverify = verifier(
                {
                    "arm": "B2",
                    "claim_id": claim_id,
                    "after_text": after_text,
                    "evidence_id": "",
                    "evidence_text": evidence_text,
                }
            )
            return {
                "claim_id": claim_id,
                "arm": "B2",
                "construction_gold": gold,
                "after_text": str(after_text),
                "evidence_id": "",
                "evidence_text": evidence_text,
                "decision": "release",
                "reject_reason": "",
                "reverify_ok": bool(reverify.get("ok")),
            }
        return {
            "claim_id": claim_id,
            "arm": "B2",
            "construction_gold": gold,
            "after_text": "",
            "evidence_id": "",
            "evidence_text": evidence_text,
            "decision": "reject",
            "reject_reason": "无 after_text",
            "reverify_ok": None,
        }

    if arm == "B1":
        # B1′：禁止 evidence_id；同文锁定后才见 evidence_text。
        verdict = verifier(
            {
                "arm": "B1",
                "claim_id": claim_id,
                "after_text": after_text,
                "evidence_id": "",
                "evidence_text": evidence_text,
            }
        )
        ok = bool(verdict.get("ok"))
        if ok:
            return {
                "claim_id": claim_id,
                "arm": "B1",
                "construction_gold": gold,
                "after_text": after_text if isinstance(after_text, str) else "",
                "evidence_id": "",
                "evidence_text": evidence_text,
                "decision": "release",
                "reject_reason": "",
                "reverify_ok": True,
            }
        return {
            "claim_id": claim_id,
            "arm": "B1",
            "construction_gold": gold,
            "after_text": after_text if isinstance(after_text, str) else "",
            "evidence_id": "",
            "evidence_text": evidence_text,
            "decision": "reject",
            "reject_reason": str(verdict.get("reason") or "核验未通过"),
            "reverify_ok": False,
        }

    # T：attested 绑定 + 同时刻核验；不过 hard reject。
    evidence_id = str(candidate.get("evidence_id") or "")
    if not _bound_t1(evidence_id, ingested):
        return {
            "claim_id": claim_id,
            "arm": "T",
            "construction_gold": gold,
            "after_text": after_text if isinstance(after_text, str) else "",
            "evidence_id": evidence_id,
            "evidence_text": evidence_text,
            "decision": "reject",
            "reject_reason": "证据未绑定已入库 T1",
            "reverify_ok": False,
        }
    verdict = verifier(
        {
            "arm": "T",
            "claim_id": claim_id,
            "after_text": after_text,
            "evidence_id": evidence_id,
            "evidence_text": evidence_text,
        }
    )
    ok = bool(verdict.get("ok"))
    if ok:
        return {
            "claim_id": claim_id,
            "arm": "T",
            "construction_gold": gold,
            "after_text": after_text if isinstance(after_text, str) else "",
            "evidence_id": evidence_id,
            "evidence_text": evidence_text,
            "decision": "release",
            "reject_reason": "",
            "reverify_ok": True,
        }
    return {
        "claim_id": claim_id,
        "arm": "T",
        "construction_gold": gold,
        "after_text": after_text if isinstance(after_text, str) else "",
        "evidence_id": evidence_id,
        "evidence_text": evidence_text,
        "decision": "reject",
        "reject_reason": str(verdict.get("reason") or "核验未通过"),
        "reverify_ok": False,
    }


def run_same_text_gates(
    candidates: Sequence[Mapping[str, Any]],
    *,
    ingested_t1: Collection[str] = (),
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]] = verify_edit,
) -> list[dict[str, Any]]:
    """对每条同文候选跑 C/T/B1/B2 四闸，返回扁平闸判记录。"""
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        for arm in ARMS:
            rows.append(
                decide_same_text_gate(
                    arm,
                    candidate,
                    ingested_t1=ingested_t1,
                    verifier=verifier,
                )
            )
    return rows


def _arm_natural(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        raise ValueError("候选数为 0")
    releases = [row for row in rows if row.get("decision") == "release"]
    release_n = len(releases)
    false_n = sum(1 for row in releases if row.get("construction_gold") == "坏")
    false_rate: float | None
    if release_n == 0:
        false_rate = None
    else:
        false_rate = false_n / release_n
    return {
        "自然放行数": release_n,
        "自然放行率": release_n / n,
        "自然误放率": false_rate,
        "候选数": n,
    }


def compare_alt_natural(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """各臂自然放行率 / 自然误放率；差 = 对照自然误放 − T 自然误放。

    放行数为 0 时自然误放率为 ``None``（无定义），禁止写成 ``0.0``。
    """
    grouped: dict[str, list[Mapping[str, Any]]] = {arm: [] for arm in ARMS}
    for row in rows:
        arm = row.get("arm")
        if arm not in grouped:
            raise ValueError(f"arm 非法: {arm!r}")
        grouped[str(arm)].append(row)

    missing = [arm for arm, items in grouped.items() if not items]
    if missing:
        raise ValueError(f"旁路比较缺臂: {', '.join(missing)}")

    arms = {arm: _arm_natural(items) for arm, items in grouped.items()}
    t_rate = arms["T"]["自然误放率"]
    contrasts: list[dict[str, Any]] = []
    for contrast in CONTRASTS:
        right = arms[contrast]["自然误放率"]
        if t_rate is None or right is None:
            delta: float | None = None
        else:
            delta = right - t_rate
        contrasts.append(
            {
                "name": f"T-{contrast}",
                "natural_false_accept_delta": delta,
            }
        )
    return {"arms": arms, "contrasts": contrasts}
