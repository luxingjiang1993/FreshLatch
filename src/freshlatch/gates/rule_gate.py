"""规则闸:绿灯唯一出口。纯函数、零 I/O(名单/checksum 由调用方注入,ADR-0001)。

口径(§1.3):「Agent 不得把红灯改回绿灯」只约束 Agent 侧工具链;
人审(L0)是合法出口,由 gates/human_latch.py(W3 起)调本闸实现,此口径写在此(ADR-0006 §4)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from freshlatch.gates.meta_gate import META_ONLY_MESSAGE, is_meta_only_disproof
from freshlatch.models import AsOf, Claim

GREEN_STATUSES = ("fresh", "renew")


@dataclass
class GateDecision:
    """一次试图点绿(或落非绿)的判定请求。"""

    status: str  # fresh | stale | unknown | renew
    t1_evidence_ids: list[str] = field(default_factory=list)
    validity_basis: dict | None = None  # {doc_id, checksum},续命/点绿时携带(W5 起)
    stale_reason: str = ""  # stale 的理由文本(#17 不变量 6 校验用;空 = 跳过元陈述校验)


@dataclass
class GateContext:
    invalidation_list: set[str] = field(default_factory=set)
    checksum_fn: Callable[[str, AsOf], str | None] = lambda doc_id, as_of: None
    eval_mode: bool = False


@dataclass
class GateResult:
    allowed: bool  # 该写是否被放行(stale/unknown 落档恒 True;绿请求过闸才 True)
    green: bool    # 是否实际发出绿灯(stale/unknown 请求恒 False——stale/unknown 不得绿灯)
    error_code: str | None = None
    reason: str = ""


def rule_gate(claim: Claim, decision: GateDecision, ctx: GateContext) -> GateResult:
    """任何 status=fresh/续命 的写都必须经过本函数。违例即打回并附结构化原因。

    校验项(全部机械执行):
      1. stale / unknown 不得绿灯(非绿请求直接放行落档,但永不发绿)
      2. 无 t1_evidence_ids 不得 fresh
      3. checksum 对不上不得 fresh / 续命(checksum 三处留位本期为空,注入即生效)
      4. claim_id ∈ invalidation_list 不得 fresh(重跑打回)
      5. stale 必须携带可点回的 t1 反证(无反证 id 打回;#15 有效反证=可点回)
      6. stale 反证不得为纯元陈述(#17:未复测/不再列入跟踪是证据缺口不是推翻,
         打回 META_ONLY_DISPROOF,经 stale 打回落 unknown 路由 unknown)
    """
    # 5. stale 无反证打回(独立于非绿放行:stale 落档也要带可点回反证)
    if decision.status == "stale" and not decision.t1_evidence_ids:
        return GateResult(allowed=False, green=False, error_code="NO_STALE_EVIDENCE",
                          reason="stale 必须给出 t1 反证 evidence_ids(有效反证=可点回)")

    # 6. stale 纯元陈述打回(#17;判定引擎单一真相在 gates/meta_gate.py)
    if decision.status == "stale" and is_meta_only_disproof(decision.stale_reason):
        return GateResult(allowed=False, green=False, error_code="META_ONLY_DISPROOF",
                          reason=META_ONLY_MESSAGE)

    if decision.status not in GREEN_STATUSES:
        return GateResult(allowed=True, green=False,
                          reason=f"非绿请求({decision.status})落档,规则闸不发绿")

    # 4. 作废名单打回
    if claim.claim_id in ctx.invalidation_list:
        return GateResult(allowed=False, green=False, error_code="INVALIDATED",
                          reason="该主张已在作废名单(人工作废),重跑不得再绿")

    # 2. 无 T1 不得 fresh
    if not decision.t1_evidence_ids:
        return GateResult(allowed=False, green=False, error_code="NO_T1_EVIDENCE",
                          reason="无 t1_evidence_ids 不得 fresh")

    # 3. checksum 校验(留位:checksum_fn 返回空/None = 本期未启用,不拦)
    if decision.validity_basis:
        doc_id = decision.validity_basis.get("doc_id", "")
        claimed = decision.validity_basis.get("checksum", "")
        actual = ctx.checksum_fn(doc_id, "T1")  # AsOf 的 Literal 注解,str 值即类型
        if actual and claimed != actual:
            return GateResult(allowed=False, green=False, error_code="CHECKSUM_MISMATCH",
                              reason=f"checksum 对不上: {doc_id} 声称 {claimed!r},实际 {actual!r}")

    return GateResult(allowed=True, green=True, reason="过闸:绿灯")
