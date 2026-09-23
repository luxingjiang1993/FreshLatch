"""跨轮腐烂重检:check_basis + apply_rot(ADR-0025 / β+ 档 3b)。

复验入口与 UI 拉单共用本模块,禁止各自复制比对逻辑。
仅检 status==fresh 且 validity_basis 非空;voided / 无 basis 跳过(半激活诚实)。
不符 → unknown + BASIS_CHECKSUM_MISMATCH;保留 basis 与 last_confirmed_at;
写 latch_log action=basis_rot(机械行,非人审按钮,override 不得为 true)。
禁自动 void;不得升格为「checksum 已证明 latch」。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Literal

from freshlatch.models import AsOf, Claim

BASIS_CHECKSUM_MISMATCH = "BASIS_CHECKSUM_MISMATCH"

BasisVerdict = Literal["skip", "ok", "mismatch"]
RotOutcome = Literal["applied", "already_rotten", "noop"]


@dataclass(frozen=True)
class BasisCheckResult:
    """check_basis 外部结果。"""

    verdict: BasisVerdict
    detail: str = ""


@dataclass(frozen=True)
class RotApplyResult:
    """apply_rot 外部结果。"""

    outcome: RotOutcome
    detail: str = ""


def _basis_entries(basis: object) -> list[dict]:
    """单对象 → [obj];list 原样;其余 → []。"""
    if isinstance(basis, list):
        return [e for e in basis if isinstance(e, dict)]
    if isinstance(basis, dict):
        return [basis]
    return []


def check_basis(
    claim: Claim,
    checksum_fn: Callable[[str, AsOf], str | None],
    *,
    as_of: AsOf = "T1",
) -> BasisCheckResult:
    """用语料现算 checksum 比对 validity_basis。

    跳过:voided、status != fresh、basis 空。
    单对象比对该 doc;list 全员受检,任一不符即 mismatch(禁只比首元)。
    checksum_fn 必须语料现算;本函数不读库列。
    与 renew 闸同口径:actual 空/None = 无法比对该条目,不记 mismatch
    (注入点未启用时不误杀)。
    """
    if claim.voided:
        return BasisCheckResult("skip", "voided 跳过")
    if claim.status != "fresh":
        return BasisCheckResult("skip", f"status={claim.status} 非 fresh,跳过")
    if not claim.validity_basis:
        return BasisCheckResult("skip", "无 validity_basis,跳过(半激活)")

    entries = _basis_entries(claim.validity_basis)
    if not entries:
        return BasisCheckResult("skip", "validity_basis 形状无法解析,跳过")

    for entry in entries:
        doc_id = str(entry.get("doc_id", "") or "")
        claimed = str(entry.get("checksum", "") or "")
        actual = checksum_fn(doc_id, as_of)
        if actual and claimed != actual:
            return BasisCheckResult(
                "mismatch",
                f"basis 不符: {doc_id} 声称 {claimed!r},现算 {actual!r}",
            )
    return BasisCheckResult("ok", "basis 与现算一致")


def apply_rot(
    store,
    claim: Claim,
    *,
    now: Callable[[], datetime] | None = None,
    run_id: str | None = None,
) -> RotApplyResult:
    """持久化腐烂:status→unknown,写机械码与 latch_log;保留 basis / last_confirmed_at。

    已是 unknown → already_rotten(幂等,不重复写成功降级行)。
    非 fresh → noop。禁止改 voided / 自动 void。
    """
    if claim.status == "unknown":
        return RotApplyResult("already_rotten", "已 unknown,幂等跳过")
    if claim.status != "fresh":
        return RotApplyResult("noop", f"status={claim.status},不降级")

    now = now or datetime.now
    ts = now().isoformat(timespec="seconds")
    prior = claim.reason
    # 保留 basis 与续命时刻(ADR-0025);只改 status / reason
    claim.status = "unknown"
    claim.reason = (
        f"[机械腐烂:{BASIS_CHECKSUM_MISMATCH}] validity_basis 与语料现算不符"
        + (f";原理由: {prior}" if prior else "")
    )
    store.log_latch(
        ts,
        claim.claim_id,
        "basis_rot",
        evidence_id=None,
        actor="system",
        machine_status_before="fresh",
        override=False,  # 机械行,不得冒充人审对抗(ADR-0023)
        run_id=run_id,
        reviewer_note=BASIS_CHECKSUM_MISMATCH,
    )
    return RotApplyResult("applied", claim.reason)


def apply_rot_if_mismatch(
    store,
    claim: Claim,
    checksum_fn: Callable[[str, AsOf], str | None],
    *,
    now: Callable[[], datetime] | None = None,
    run_id: str | None = None,
    as_of: AsOf = "T1",
) -> RotApplyResult:
    """双触发共用接线:check → 仅 mismatch 时 apply_rot。

    复验入口与 UI 拉单都必须经此(或等价的 check_basis+apply_rot 组合),
    禁止另写比对/降级逻辑。
    """
    check = check_basis(claim, checksum_fn, as_of=as_of)
    if check.verdict != "mismatch":
        return RotApplyResult("noop", check.detail)
    return apply_rot(store, claim, now=now, run_id=run_id)


def rot_claims(
    store,
    claims: list[Claim],
    checksum_fn: Callable[[str, AsOf], str | None],
    *,
    now: Callable[[], datetime] | None = None,
    run_id: str | None = None,
    as_of: AsOf = "T1",
) -> list[RotApplyResult]:
    """对可见主张列表逐条跑 apply_rot_if_mismatch(UI 拉单/渲染用)。"""
    return [
        apply_rot_if_mismatch(
            store, c, checksum_fn, now=now, run_id=run_id, as_of=as_of,
        )
        for c in claims
    ]
