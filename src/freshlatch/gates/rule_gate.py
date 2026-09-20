"""规则闸:绿灯唯一出口。纯函数、零 I/O(名单/checksum 由调用方注入,ADR-0001)。

口径(§1.3):「Agent 不得把红灯改回绿灯」只约束 Agent 侧工具链;
人审(L0)是合法出口,由 gates/human_latch.py(W3 起)调本闸实现,此口径写在此(ADR-0006 §4)。

Auditor 字段(ADR-0009/0010,#22):闸只机械消费 Auditor 产出的结构化判定,语义判断全部
住在角色层——与不变量 6(元陈述闸,判定引擎住 meta_gate)同构。
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
    auditor_verdict: str | None = None  # fresh|stale|unknown(ADR-0009 在场不变量;None = 缺席)
    auditor_dimension_match: bool | None = None  # ADR-0010 不变量 7:False = Auditor 维度异议


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


# -- 落档仲裁真值表(单一真相在此;runner._finalize 消费;闸做 fail-closed 兜底) ------------

def arbitrate_fresh(auditor_verdict: str | None) -> str:
    """ADR-0009 3×3 的 fresh 请求行:auditor fresh → fresh;stale → stale;unknown/缺席 → unknown。

    Auditor 缺席不构成任何绿格(fail-closed 落 unknown)。stale 落档仍须过闸:
    不变量 7 优先——auditor stale 且 dimension_match=False(推翻证据维度不符)时
    DIMENSION_MISMATCH 打回落 unknown(与 ADR-0010 的异议落点一致,不造维度不符红卡)。
    """
    if auditor_verdict == "fresh":
        return "fresh"
    if auditor_verdict == "stale":
        return "stale"
    return "unknown"


def arbitrate_stale_mark(auditor_verdict: str | None,
                         dimension_match: bool | None) -> tuple[str, bool]:
    """mark_stale 路径真值表(ADR-0010,修订 ADR-0009 stale 行)。返回 (落档状态, 是否挂异议记录)。

    uphold(维度相符)stale 照旧落档,零变化;维度异议打回 unknown + 异议记录;
    Auditor fresh/unknown 不拦 stale(含 stale 落 stale,安全不对称),fresh 时异议随红卡进人审。
    """
    if auditor_verdict is None:
        return "unknown", False  # 缺席 fail-closed(闸另报 AUDITOR_ABSENT)
    if auditor_verdict == "stale":
        if dimension_match is False:
            return "unknown", True
        return "stale", False
    if auditor_verdict == "fresh":
        return "stale", True  # ADR-0009:Lead stale × Auditor fresh → stale + 异议记录
    return "stale", False     # auditor unknown:含 stale 落 stale


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
      7. stale 经 Auditor 维度核对异议(dimension_match=False)打回(ADR-0010:
         路由 unknown + 异议记录;语义判断住 Auditor 角色层,闸只消费结构化 flag);
         同条款兜底:Auditor 缺席不构成任何 stale 落档(fail-closed)
      8. fresh 需双判一致:auditor_verdict 在场且 == fresh(ADR-0009;Auditor 缺席
         不构成任何绿格;renew 是 L0 人审出口,不受此款约束)
    """
    # 5. stale 无反证打回(独立于非绿放行:stale 落档也要带可点回反证)
    if decision.status == "stale" and not decision.t1_evidence_ids:
        return GateResult(allowed=False, green=False, error_code="NO_STALE_EVIDENCE",
                          reason="stale 必须给出 t1 反证 evidence_ids(有效反证=可点回)")

    # 6. stale 纯元陈述打回(#17;判定引擎单一真相在 gates/meta_gate.py)
    if decision.status == "stale" and is_meta_only_disproof(decision.stale_reason):
        return GateResult(allowed=False, green=False, error_code="META_ONLY_DISPROOF",
                          reason=META_ONLY_MESSAGE)

    if decision.status == "stale":
        # 7(缺席兜底). Auditor 缺席不构成任何落档(ADR-0010:hook 保证在场,闸 fail-closed)
        if decision.auditor_verdict is None:
            return GateResult(allowed=False, green=False, error_code="AUDITOR_ABSENT",
                              reason="Auditor 缺席不构成任何落档(ADR-0010):stale 必须经 "
                                     "Auditor 单轮判定在场,路由 unknown")
        # 7. 维度异议打回(ADR-0010):语义判断住 Auditor,闸只机械消费结构化 flag
        if decision.auditor_verdict == "stale" and decision.auditor_dimension_match is False:
            return GateResult(allowed=False, green=False, error_code="DIMENSION_MISMATCH",
                              reason="Auditor 维度异议:反证未锚在主张同一前提/度量维度,"
                                     "stale 打回(ADR-0010 不变量 7),路由 unknown + 异议记录")

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

    # 8(fresh 侧). 双判一致:auditor_verdict 在场且 == fresh(ADR-0009;renew 不受约束)
    if decision.status == "fresh":
        if decision.auditor_verdict is None:
            return GateResult(allowed=False, green=False, error_code="AUDITOR_ABSENT",
                              reason="Auditor 缺席不构成任何绿格(ADR-0009):fresh 需双判一致,"
                                     "路由 unknown")
        if decision.auditor_verdict != "fresh":
            return GateResult(allowed=False, green=False, error_code="ARBITRATION_MISMATCH",
                              reason=f"双判未一致:Auditor 判 {decision.auditor_verdict},"
                                     "fresh 请求打回,路由 unknown")

    # 3. checksum 校验(留位:checksum_fn 返回空/None = 本期未启用,不拦)
    if decision.validity_basis:
        doc_id = decision.validity_basis.get("doc_id", "")
        claimed = decision.validity_basis.get("checksum", "")
        actual = ctx.checksum_fn(doc_id, "T1")  # AsOf 的 Literal 注解,str 值即类型
        if actual and claimed != actual:
            return GateResult(allowed=False, green=False, error_code="CHECKSUM_MISMATCH",
                              reason=f"checksum 对不上: {doc_id} 声称 {claimed!r},实际 {actual!r}")

    return GateResult(allowed=True, green=True, reason="过闸:绿灯")
