"""人审写路径唯一出口(ADR-0006 §6):UI/端点只准经本模块把人的决定落档。

- 作废(discard):claim.voided=True + invalidation_list + latch_log;status 的机器判定
  (stale/unknown)原样保留——stale 与 void 并存不互斥(void 是人的决定,stale 是机器判定)。
- 续命(renew,#23):人带 T1 证据主张仍然成立 → 格式校验 → 点回校验 → 规则闸
  (证据时点 / checksum / 作废名单)→ 写新 validity_basis + last_confirmed_at +
  status=fresh + latch_log。renew 是 L0 人审出口,不受不变量 9 双判一致约束
  (人就是那个「第二判」)。
- 「Agent 不得把红灯改回绿灯」只约束 Agent 侧工具链;人审是 L0 合法出口,
  此口径与 gates/rule_gate.py 模块注释一致。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from freshlatch.evidence_id import parse_evidence_id
from freshlatch.gates.policy_gate import (
    apply_policy_after_rule_gate,
    extract_provenance_refs,
)
from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import AsOf, Claim

VALID_ACTIONS = ("discard", "renew")  # 封闭集;禁止新增 override action


def derive_override(action: str, machine_status_before: str) -> bool:
    """成功人审落档时的派生标签(ADR-0023)。不是第三按钮,也不表示模型变好。

    - discard 且落档前机器 status 为 fresh → True
    - renew 且落档前机器 status 为 stale 或 unknown → True
    - 其余成功人审 → False
    失败与幂等跳过不调用本函数写新行。
    """
    if action == "discard" and machine_status_before == "fresh":
        return True
    if action == "renew" and machine_status_before in ("stale", "unknown"):
        return True
    return False

# 错误码(结构化,端点直接透传给 UI)
RENEW_EVIDENCE_MALFORMED = "RENEW_EVIDENCE_MALFORMED"
RENEW_EVIDENCE_UNRESOLVED = "RENEW_EVIDENCE_UNRESOLVED"
UNKNOWN_CLAIM = "UNKNOWN_CLAIM"
INVALID_ACTION = "INVALID_ACTION"


@dataclass
class HumanDecision:
    claim_id: str
    action: str  # discard | renew
    evidence_id: str | None = None  # renew 必填(锚 T1);discard 忽略
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
    checksum_fn: Callable[[str, AsOf], str | None] | None = None,
    run_id: str | None = None,
) -> list[dict]:
    """整轮决定列表逐条落档。单条失败不影响其余;已作废的重复 discard 幂等跳过。

    写路径唯一:invalidation_list / latch_log 只从这里(及重跑的 rerun 分支)写。
    pending_ids 给定时,claim_id 必须在待审清单内(防止对绿灯主张落人审决定)。
    checksum_fn 续命链注入点(留位:缺省 None = checksum 未启用,闸不拦,同 runner)。
    run_id 可选:成功人审行写入 latch_log,供跨跑次串联;缺省不填。
    成功行必填 machine_status_before 与派生 override。失败或幂等跳过不新增对抗语义行。
    override 不是模型变好,本路径不计算 Override Rate。
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
        row_run_id = raw.get("run_id") if raw.get("run_id") else run_id
        results.append(
            _apply_one(store, claims_by_id, d, now, pending_ids, checksum_fn, row_run_id)
        )
    return [r.__dict__ for r in results]


def _apply_one(store, claims_by_id: dict, d: HumanDecision, now: Callable[[], datetime],
               pending_ids: set[str] | None,
               checksum_fn: Callable[[str, AsOf], str | None] | None,
               run_id: str | None = None) -> DecisionResult:
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
        return _apply_renew(store, claim, d, now, checksum_fn, run_id)
    # discard:作废(幂等——interrupt 重执行语义下可能二次落档)
    if claim.voided:
        # 幂等跳过:不新增 latch_log 行,避免把重复作废记成新的对抗语义
        return DecisionResult(d.claim_id, ok=True, action="discard",
                              detail="已作废,幂等跳过(invalidation_list 已有该 id)")
    machine_status_before = claim.status
    ts = now().isoformat(timespec="seconds")
    store.add_invalidation(d.claim_id, ts, actor="human", reason=d.reviewer_note)
    store.log_latch(
        ts, d.claim_id, "discard", evidence_id=None, actor="human",
        machine_status_before=machine_status_before,
        override=derive_override("discard", machine_status_before),
        run_id=run_id,
        reviewer_note=d.reviewer_note,
    )
    claim.voided = True
    claim.voided_at = ts
    return DecisionResult(d.claim_id, ok=True, action="discard",
                          detail=f"已作废并进作废名单(voided_at={ts});机器判定 {claim.status} 保留")


def _renew_already_logged(store, claim_id: str, evidence_id: str) -> bool:
    """同 claim+evidence 是否已有成功 renew 行(I3 #250 重放不双写)。"""
    list_fn = getattr(store, "list_latch_events", None)
    if list_fn is None:
        return False
    for row in list_fn(claim_id) or []:
        if row.get("action") == "renew" and str(row.get("evidence_id") or "") == evidence_id:
            return True
    return False


def _apply_renew(store, claim: Claim, d: HumanDecision, now: Callable[[], datetime],
                 checksum_fn: Callable[[str, AsOf], str | None] | None,
                 run_id: str | None = None) -> DecisionResult:
    """续命(#23 / ADR-0006 §4):人带 T1 证据主张仍然成立 → 过闸 → 写回转绿。

    三层各守一段,全过才写(任一违例零写,附结构化原因):
      1. 格式校验:`doc#anchor@T1`;
      2. 点回校验:证据必须点回真实 chunk(编造的 id 不得续命);
      3. 规则闸:证据锚 T1 / checksum 对不上 / 作废名单(#23 实装清单第 3 项)。

    I3 #250:同 claim+evidence 重放幂等跳过,不双写 latch_log 坏账行。
    """
    machine_status_before = claim.status  # 落档前机器判定;失败路径不得改 status
    if not str(d.evidence_id or "").strip():
        return DecisionResult(claim.claim_id, ok=False, action="renew",
                              error_code="RENEW_NO_EVIDENCE",
                              detail="续命必须带 T1 原文证据(evidence_id 至少 1 个,ADR-0006 §4)")
    # 重放幂等(合成夹具 · 非真事故复盘):已有同证据 renew 行则零写跳过
    if _renew_already_logged(store, claim.claim_id, str(d.evidence_id)):
        return DecisionResult(claim.claim_id, ok=True, action="renew",
                              detail=(f"已续命,幂等跳过(latch_log 已有 "
                                      f"{d.evidence_id};不双写坏账)"))
    parsed = parse_evidence_id(d.evidence_id)
    if parsed is None:
        return DecisionResult(claim.claim_id, ok=False, action="renew",
                              error_code=RENEW_EVIDENCE_MALFORMED,
                              detail=f"evidence_id 必须是 doc#anchor@T1 格式,收到: {d.evidence_id!r}")
    doc_id, anchor, as_of = parsed
    chunk = store.get_chunk(doc_id, anchor, as_of=as_of)
    if chunk is None:
        return DecisionResult(claim.claim_id, ok=False, action="renew",
                              error_code=RENEW_EVIDENCE_UNRESOLVED,
                              detail=f"证据点不回任何 {as_of} 原文块: {d.evidence_id}")
    basis = {"doc_id": chunk.doc_id, "checksum": chunk.checksum}  # 新 validity_basis(T1 doc+checksum)
    # I3 #249:规则闸之后组合出处禁区旁路(政策拒 ≠ 新鲜度拒;不改 rule_gate 正文)
    gate = apply_policy_after_rule_gate(
        rule_gate(
            claim,
            GateDecision(status="renew", t1_evidence_ids=[str(d.evidence_id)],
                         validity_basis=basis),
            GateContext(invalidation_list=set(store.list_invalidation()),
                        checksum_fn=checksum_fn or (lambda doc, at: None)),
        ),
        provenance=extract_provenance_refs(
            evidence_ids=[str(d.evidence_id)],
            texts=[getattr(chunk, "text", "") or ""],
        ),
    )
    if not gate.green:
        return DecisionResult(claim.claim_id, ok=False, action="renew",
                              error_code=gate.error_code, detail=gate.reason)
    ts = now().isoformat(timespec="seconds")
    prior = claim.reason
    claim.validity_basis = basis
    claim.last_confirmed_at = ts
    claim.t1_evidence_ids = list(dict.fromkeys([*claim.t1_evidence_ids, str(d.evidence_id)]))
    claim.status = "fresh"  # 卡片转绿(机器判定被人的决定取代,理由留痕不抹)
    claim.reason = f"[人审续命 {ts}] 依据 {d.evidence_id}" + (f";原机器判定: {prior}" if prior else "")
    store.log_latch(
        ts, claim.claim_id, "renew", evidence_id=str(d.evidence_id), actor="human",
        machine_status_before=machine_status_before,
        override=derive_override("renew", machine_status_before),
        run_id=run_id,
        reviewer_note=d.reviewer_note,
    )
    return DecisionResult(claim.claim_id, ok=True, action="renew",
                          detail=f"已续命(last_confirmed_at={ts},依据 {d.evidence_id})")
