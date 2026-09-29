"""Evidence-bound / attested patch API(ADR-0029 / #198+#199)。

独立 Verify+ 补丁缝:propose 暂存、confirm 应用。不扩展 HumanLatch VALID_ACTIONS。
产品路径记账走 patch_events.append_product_confirm(arm=T, before/after)。

#199:confirm 成功路径强制单条再验(同构 latch rerun 粒度)→ 重算 disposition;
正式事件 reverify=true;禁止整包全量再验作为唯一/默认路径。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Collection, Iterable, Mapping, MutableSequence, Sequence

from freshlatch.models import Claim
from freshlatch.patch_events import append_product_confirm
from freshlatch.prepublish import disposition_for_claims

# 错误码(结构化;端点/UI 直接透传)
PATCH_UNKNOWN_CLAIM = "PATCH_UNKNOWN_CLAIM"
PATCH_INELIGIBLE = "PATCH_INELIGIBLE"
PATCH_EMPTY_AFTER = "PATCH_EMPTY_AFTER"
PATCH_EMPTY_T1 = "PATCH_EMPTY_T1"
PATCH_T1_NOT_ARCHIVED = "PATCH_T1_NOT_ARCHIVED"
PATCH_NO_DRAFT = "PATCH_NO_DRAFT"
PATCH_REVERIFY_UNAVAILABLE = "PATCH_REVERIFY_UNAVAILABLE"

# 可提案资格:未 discard 的 unknown|stale(ADR-0029)
_ELIGIBLE_STATUSES: frozenset[str] = frozenset({"unknown", "stale"})

# 单主张再验回调:(verdict, note);可原地改 claim.status(同构 latch reverify_fn)
ClaimReverifyFn = Callable[[Claim], tuple[str, str]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_patch_eligible(claim: Claim) -> bool:
    """资格闸:仅未 discard(voided)的 unknown|stale 可提案/确认。"""
    if claim.voided:
        return False
    return claim.status in _ELIGIBLE_STATUSES


def default_patch_span(claim_id: str) -> str:
    """patch_span 自动默认(claim_id + 正文替换)。"""
    return f"{claim_id}·正文替换"


@dataclass
class PatchDraft:
    """会话/Run 暂存草案;未 confirm 不改正文、不写正式账本。"""

    claim_id: str
    after_text: str
    t1_ids: list[str] = field(default_factory=list)
    proposed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "after_text": self.after_text,
            "t1_ids": list(self.t1_ids),
            "proposed_at": self.proposed_at,
        }


@dataclass
class PatchDraftStore:
    """按 run_id 隔离的进程内暂存;可丢弃,永不落正式 patch_events。"""

    _by_run: dict[str, dict[str, PatchDraft]] = field(default_factory=dict)

    def put(self, run_id: str, draft: PatchDraft) -> PatchDraft:
        bucket = self._by_run.setdefault(run_id, {})
        bucket[draft.claim_id] = draft
        return draft

    def get(self, run_id: str, claim_id: str) -> PatchDraft | None:
        return self._by_run.get(run_id, {}).get(claim_id)

    def discard(self, run_id: str, claim_id: str) -> bool:
        """清除单条草案;返回是否曾存在。"""
        bucket = self._by_run.get(run_id)
        if not bucket or claim_id not in bucket:
            return False
        del bucket[claim_id]
        if not bucket:
            self._by_run.pop(run_id, None)
        return True

    def clear_run(self, run_id: str) -> None:
        self._by_run.pop(run_id, None)


@dataclass(frozen=True)
class ProposePatchResult:
    ok: bool
    claim_id: str
    error_code: str | None = None
    detail: str = ""
    draft: PatchDraft | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "claim_id": self.claim_id,
            "error_code": self.error_code,
            "detail": self.detail,
            "draft": self.draft.to_dict() if self.draft else None,
        }


@dataclass(frozen=True)
class ConfirmPatchResult:
    ok: bool
    claim_id: str
    error_code: str | None = None
    detail: str = ""
    disposition: str | None = None
    before_text: str | None = None
    after_text: str | None = None
    # 成功确认后必跑单条再验(#199);钩子与真触发合一
    reverify_requested: bool = False
    reverify_triggered: bool = False
    reverify_verdict: str | None = None
    reverify_note: str = ""
    event: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "claim_id": self.claim_id,
            "error_code": self.error_code,
            "detail": self.detail,
            "disposition": self.disposition,
            "before_text": self.before_text,
            "after_text": self.after_text,
            "reverify_requested": self.reverify_requested,
            "reverify_triggered": self.reverify_triggered,
            "reverify_verdict": self.reverify_verdict,
            "reverify_note": self.reverify_note,
            "event": self.event,
        }


def _claims_by_id(claims: Sequence[Claim] | Mapping[str, Claim]) -> dict[str, Claim]:
    if isinstance(claims, Mapping):
        return dict(claims)
    return {c.claim_id: c for c in claims}


def _find_claim(
    claims: Sequence[Claim] | Mapping[str, Claim],
    claim_id: str,
) -> Claim | None:
    return _claims_by_id(claims).get(claim_id)


def propose_patch(
    *,
    claim_id: str,
    after_text: str,
    claims: Sequence[Claim] | Mapping[str, Claim],
    drafts: PatchDraftStore,
    run_id: str = "session",
    t1_ids: Sequence[str] | None = None,
) -> ProposePatchResult:
    """提案暂存:校验资格后写入 Run/会话草案。

    不改正文、不写正式 patch_events。fresh/void/已 discard → 拒绝。
    """
    claim = _find_claim(claims, claim_id)
    if claim is None:
        return ProposePatchResult(
            ok=False,
            claim_id=claim_id,
            error_code=PATCH_UNKNOWN_CLAIM,
            detail=f"未知主张: {claim_id}",
        )
    if not is_patch_eligible(claim):
        reason = "已 discard" if claim.voided else f"status={claim.status}"
        return ProposePatchResult(
            ok=False,
            claim_id=claim_id,
            error_code=PATCH_INELIGIBLE,
            detail=f"不可提案: {reason}(仅未 discard 的 unknown|stale)",
        )
    text = (after_text or "").strip()
    if not text:
        return ProposePatchResult(
            ok=False,
            claim_id=claim_id,
            error_code=PATCH_EMPTY_AFTER,
            detail="after_text 不可为空",
        )
    draft = PatchDraft(
        claim_id=claim_id,
        after_text=text,
        t1_ids=[str(x) for x in (t1_ids or [])],
        proposed_at=_utc_now(),
    )
    drafts.put(run_id, draft)
    return ProposePatchResult(ok=True, claim_id=claim_id, draft=draft)


def discard_patch_draft(
    *,
    claim_id: str,
    drafts: PatchDraftStore,
    run_id: str = "session",
) -> bool:
    """丢弃未确认草案;不影响主张正文与正式账本。"""
    return drafts.discard(run_id, claim_id)


def _reject_confirm(
    claim_id: str,
    error_code: str,
    detail: str,
) -> ConfirmPatchResult:
    return ConfirmPatchResult(
        ok=False,
        claim_id=claim_id,
        error_code=error_code,
        detail=detail,
        reverify_requested=False,
        reverify_triggered=False,
    )


def _validate_t1_ids(
    t1_ids: Sequence[str],
    archived_t1_ids: Collection[str],
) -> tuple[str | None, str]:
    """空列表或非本 Run 已入库 id → (error_code, detail);合法 → (None, "")。"""
    ids = [str(x).strip() for x in t1_ids if str(x).strip()]
    if not ids:
        return PATCH_EMPTY_T1, "t1_ids 不可为空(fail-closed)"
    archived = set(archived_t1_ids)
    missing = [eid for eid in ids if eid not in archived]
    if missing:
        return (
            PATCH_T1_NOT_ARCHIVED,
            f"t1_ids 须 ⊆ 本 Run 已入库 T1,非法: {', '.join(missing)}",
        )
    return None, ""


def single_claim_reverify(
    claim: Claim,
    *,
    store: Any,
    checksum_fn: Callable[..., Any] | None = None,
) -> tuple[str, str]:
    """单条强制再验:与 HumanLatch._default_reverify 同构粒度。

    只把该主张交给 Runner.run([claim]),禁止默认跑整包 claims。
    返回 (verdict, note);Runner._finalize 可能已原地改 claim.status。
    """
    from freshlatch.runner import Runner  # 延迟导入避免环

    runner = Runner(store, checksum_fn=checksum_fn)
    result = runner.run([claim])
    lead_decision = result.decisions[claim.claim_id]
    note = ""
    if lead_decision.status == "fresh" and claim.status != "fresh":
        note = "Lead 判 fresh,规则闸打回"
    return claim.status, note


def confirm_patch(
    *,
    claim_id: str,
    claims: Sequence[Claim] | Mapping[str, Claim],
    archived_t1_ids: Collection[str],
    minutes: float,
    after_text: str | None = None,
    t1_ids: Sequence[str] | None = None,
    patch_span: str | None = None,
    drafts: PatchDraftStore | None = None,
    run_id: str = "session",
    events_dir: Path | None = None,
    actor: str = "human",
    claim_list: MutableSequence[Claim] | None = None,
    reverify_fn: ClaimReverifyFn | None = None,
    store: Any | None = None,
    checksum_fn: Callable[..., Any] | None = None,
) -> ConfirmPatchResult:
    """确认应用:资格闸 + T1 硬闸 → 覆盖 statement → 单条再验 → 重算 disposition → 写 T 行。

    无证/非法 t1 → 拒绝且零改正文、零写正式账本。
    成功路径强制对该 claim 单条再验(注入 reverify_fn,或 store→single_claim_reverify);
    缺再验依赖则拒确认(零改正文)。正式事件 reverify=true。
    claim_list 若给出则用其重算包结论(否则用 claims 映射的值列表)。
    """
    claim = _find_claim(claims, claim_id)
    if claim is None:
        return _reject_confirm(claim_id, PATCH_UNKNOWN_CLAIM, f"未知主张: {claim_id}")
    if not is_patch_eligible(claim):
        reason = "已 discard" if claim.voided else f"status={claim.status}"
        return _reject_confirm(
            claim_id,
            PATCH_INELIGIBLE,
            f"不可确认: {reason}(仅未 discard 的 unknown|stale)",
        )

    draft = drafts.get(run_id, claim_id) if drafts is not None else None
    resolved_after = (after_text if after_text is not None else (draft.after_text if draft else ""))
    resolved_after = (resolved_after or "").strip()
    if not resolved_after:
        if draft is None and after_text is None:
            return _reject_confirm(claim_id, PATCH_NO_DRAFT, "无 after_text 且无暂存草案")
        return _reject_confirm(claim_id, PATCH_EMPTY_AFTER, "after_text 不可为空")

    if t1_ids is not None:
        resolved_t1 = [str(x) for x in t1_ids]
    elif draft is not None:
        resolved_t1 = list(draft.t1_ids)
    else:
        resolved_t1 = []

    err, detail = _validate_t1_ids(resolved_t1, archived_t1_ids)
    if err:
        return _reject_confirm(claim_id, err, detail)

    # 再验依赖前置闸:成功路径必须能触发单条再验(fail-closed,避免半提交)
    if reverify_fn is not None:
        effective_fn: ClaimReverifyFn = reverify_fn
    elif store is not None:
        def _store_backed_reverify(c: Claim) -> tuple[str, str]:
            return single_claim_reverify(c, store=store, checksum_fn=checksum_fn)

        effective_fn = _store_backed_reverify
    else:
        return _reject_confirm(
            claim_id,
            PATCH_REVERIFY_UNAVAILABLE,
            "confirm 成功路径须注入 reverify_fn 或 store 以触发单条再验",
        )

    # 包结论快照(记账 before_disp);确认前取
    pack_claims: Iterable[Claim]
    if claim_list is not None:
        pack_claims = claim_list
    elif isinstance(claims, Mapping):
        pack_claims = list(claims.values())
    else:
        pack_claims = list(claims)
    before_disp = disposition_for_claims(pack_claims)
    before_text = claim.statement

    # 硬闸已过:原地覆盖正文 + 挂载确认用 t1
    claim.statement = resolved_after
    claim.t1_evidence_ids = list(resolved_t1)

    # 单条强制再验(同构 latch rerun 粒度;仅目标 claim,非整包)
    verdict, note = effective_fn(claim)

    span = (patch_span or "").strip() or default_patch_span(claim_id)
    event = append_product_confirm(
        claim_id=claim_id,
        before_disp=before_disp,
        patch_span=span,
        t1_ids=list(resolved_t1),
        minutes=float(minutes),
        before_text=before_text,
        after_text=resolved_after,
        reverify=True,
        human_confirm=True,
        actor=actor,
        events_dir=events_dir,
    )

    if drafts is not None:
        drafts.discard(run_id, claim_id)

    # 再验后重算包结论(与主张态聚合一致)
    new_disp = disposition_for_claims(pack_claims)
    return ConfirmPatchResult(
        ok=True,
        claim_id=claim_id,
        disposition=new_disp,
        before_text=before_text,
        after_text=resolved_after,
        reverify_requested=True,
        reverify_triggered=True,
        reverify_verdict=verdict,
        reverify_note=note or "",
        event=event,
    )
