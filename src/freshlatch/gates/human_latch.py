"""人审写路径唯一出口(ADR-0006 §6):UI/端点只准经本模块把人的决定落档。

- 作废(discard):claim.voided=True + invalidation_list + latch_log;status 的机器判定
  (stale/unknown)原样保留——stale 与 void 并存不互斥(void 是人的决定,stale 是机器判定)。
- 续命(renew):W5–W8 实装,本期 fail-closed 拒绝(RENEW_NOT_OPEN);W5 生效链
  (checksum 校验 → 新 validity_basis + last_confirmed_at)在本模块调规则闸实现。
- 「Agent 不得把红灯改回绿灯」只约束 Agent 侧工具链;人审是 L0 合法出口,
  此口径与 gates/rule_gate.py 模块注释一致。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

VALID_ACTIONS = ("discard", "renew")

# 错误码(结构化,端点直接透传给 UI)
RENEW_NOT_OPEN = "RENEW_NOT_OPEN"
UNKNOWN_CLAIM = "UNKNOWN_CLAIM"
INVALID_ACTION = "INVALID_ACTION"


@dataclass
class HumanDecision:
    claim_id: str
    action: str  # discard | renew(W5 前拒绝)
    evidence_id: str | None = None  # renew 用(W5);discard 忽略
    reviewer_note: str | None = None  # 人审备注 → invalidation_list.reason


@dataclass
class DecisionResult:
    claim_id: str
    ok: bool
    action: str = ""
    error_code: str | None = None
    detail: str = ""


def apply_decisions(
    store,
    claims_by_id: dict,
    decisions: list[dict],
    *,
    pending_ids: set[str] | None = None,
    now: Callable[[], datetime] | None = None,
) -> list[dict]:
    """整轮决定列表逐条落档。单条失败不影响其余;已作废的重复 discard 幂等跳过。

    写路径唯一:invalidation_list / latch_log 只从这里(及重跑的 rerun 分支)写。
    pending_ids 给定时,claim_id 必须在待审清单内(防止对绿灯主张落人审决定)。
    """
    now = now or datetime.now
    results: list[DecisionResult] = []
    for raw in decisions or []:
        d = HumanDecision(
            claim_id=str(raw.get("claim_id", "")),
            action=str(raw.get("action", "")),
            evidence_id=raw.get("evidence_id"),
            reviewer_note=raw.get("reviewer_note"),
        )
        results.append(_apply_one(store, claims_by_id, d, now, pending_ids))
    return [r.__dict__ for r in results]


def _apply_one(store, claims_by_id: dict, d: HumanDecision, now: Callable[[], datetime],
               pending_ids: set[str] | None) -> DecisionResult:
    if pending_ids is not None and d.claim_id not in pending_ids:
        return DecisionResult(d.claim_id, ok=False, action=d.action,
                              error_code=UNKNOWN_CLAIM, detail="该主张不在本轮待审清单")
    claim = claims_by_id.get(d.claim_id)
    if claim is None:
        return DecisionResult(d.claim_id, ok=False, action=d.action,
                              error_code=UNKNOWN_CLAIM, detail="该主张不在本轮待审清单")
    if d.action not in VALID_ACTIONS:
        return DecisionResult(d.claim_id, ok=False, action=d.action,
                              error_code=INVALID_ACTION,
                              detail=f"action 只能是 {'|'.join(VALID_ACTIONS)};收到: {d.action!r}")
    if d.action == "renew":
        # W5 实装:此处接规则闸 checksum 链(无 evidence_id 不得续命、checksum 对不上不得续命)
        return DecisionResult(d.claim_id, ok=False, action=d.action,
                              error_code=RENEW_NOT_OPEN,
                              detail="续命 W5 开放:必须带 T1 原文证据 + checksum 校验(ADR-0006 §4)")
    # discard:作废(幂等——interrupt 重执行语义下可能二次落档)
    if claim.voided:
        return DecisionResult(d.claim_id, ok=True, action="discard",
                              detail="已作废,幂等跳过(invalidation_list 已有该 id)")
    ts = now().isoformat(timespec="seconds")
    store.add_invalidation(d.claim_id, ts, actor="human", reason=d.reviewer_note)
    store.log_latch(ts, d.claim_id, "discard", evidence_id=None, actor="human")
    claim.voided = True
    claim.voided_at = ts
    return DecisionResult(d.claim_id, ok=True, action="discard",
                          detail=f"已作废并进作废名单(voided_at={ts});机器判定 {claim.status} 保留")
