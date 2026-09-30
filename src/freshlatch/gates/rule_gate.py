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

# ADR-0011 不变量 8 / ADR-0012 受理层预检共用的 error_code(单一真相,两处不得各写字面量)。
ERR_DIMENSION_CROSSCHECK_MISMATCH = "DIMENSION_CROSSCHECK_MISMATCH"

# I2 inj-t001(ADR-0030):间接注入诱绿。单一真相在本闸,不挂 meta_gate。
ERR_INDIRECT_INJECTION = "INDIRECT_INJECTION"

# 「忽略指令 → 标 fresh」两段都要命中,避免业务正文里单独出现 fresh 被误杀。
_INJECTION_IGNORE_MARKERS = (
    "忽略指令",
    "忽略之前的指令",
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore instructions",
)
_INJECTION_FRESH_MARKERS = (
    "标为 fresh",
    "标为fresh",
    "标记为 fresh",
    "标记为fresh",
    "标 fresh",
    "mark as fresh",
    "mark this claim fresh",
    "mark the claim as fresh",
)


def is_indirect_injection(text: str) -> bool:
    """T1 正文是否含「忽略指令→标 fresh」类间接注入。

    机械子串,零模型。空文本不算注入:旧调用点未带正文时行为与改前一致。
    """
    if not text or not text.strip():
        return False
    folded = text.lower()
    compact = folded.replace(" ", "").replace("\u3000", "")
    has_ignore = any(
        marker in folded or marker.replace(" ", "") in compact
        for marker in _INJECTION_IGNORE_MARKERS
    )
    has_fresh = any(
        marker in folded or marker.replace(" ", "") in compact
        for marker in _INJECTION_FRESH_MARKERS
    )
    return has_ignore and has_fresh


def dimension_crosscheck_mismatch(registered_dimension: str | None,
                                  stale_dimension: str | None) -> bool:
    """登记维度 ≠ 反证自标维度(ADR-0011 不变量 8;ADR-0012 受理层预检调本函数,
    单一真相在此——受理层不得复制比对逻辑)。两维任一缺失 = 无锚可比对,不拦
    (回落不变量 7,fail-soft 不憋死真 stale)。"""
    return (registered_dimension is not None
            and stale_dimension is not None
            and registered_dimension != stale_dimension)


@dataclass
class GateDecision:
    """一次试图点绿(或落非绿)的判定请求。"""

    status: str  # fresh | stale | unknown | renew
    t1_evidence_ids: list[str] = field(default_factory=list)
    validity_basis: dict | None = None  # {doc_id, checksum},续命/点绿时携带(W5 起)
    stale_reason: str = ""  # stale 的理由文本(#17 不变量 6 校验用;空 = 跳过元陈述校验)
    auditor_verdict: str | None = None  # fresh|stale|unknown(ADR-0009 在场不变量;None = 缺席)
    auditor_dimension_match: bool | None = None  # ADR-0010 不变量 7:False = Auditor 维度异议
    registered_dimension: str | None = None  # ADR-0011 不变量 8:签发登记维度(claim.dimension)
    stale_dimension: str | None = None  # ADR-0011 不变量 8:反证自标维度(mark_stale 必填字段)
    t1_evidence_texts: list[str] = field(default_factory=list)  # I2:已引用 T1 正文;空=不启用注入拒绿


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


def arbitrate_unknown(auditor_verdict: str | None) -> tuple[str, bool]:
    """ADR-0009 3×3 的 unknown 请求行。返回 (落档状态, 是否挂异议记录)。

    Auditor fresh → unknown + 异议(Auditor 不得把 unknown 改绿);
    Auditor stale → stale(含 stale 落 stale;runner 仍须过闸,维度不符不得放行);
    Auditor unknown / 缺席 / 非法值 → unknown,不造异议。
    """
    if auditor_verdict == "fresh":
        return "unknown", True
    if auditor_verdict == "stale":
        return "stale", False
    return "unknown", False


def seal_no_unfounded_fresh(claim: Claim, auditor_verdict: str | None) -> None:
    """落档收口:fresh 仅保留双判一致且无异议的结果。

    本轮 Auditor 判 fresh 时清除异议(ADR-0012 同维复验可以落绿,绿灯不携带异议)。
    Auditor 缺席或未判 fresh 却已是 fresh → 打回 unknown;已有异议保留,收口可观察。
    """
    if claim.status != "fresh":
        return
    if auditor_verdict == "fresh":
        claim.dissent = None
        return
    claim.status = "unknown"
    if auditor_verdict is None:
        claim.reason = ("[闸打回:AUDITOR_ABSENT] Auditor 缺席不构成任何绿格,"
                        "不得无依据 fresh")
    else:
        claim.reason = (f"[闸打回:ARBITRATION_MISMATCH] Auditor 判 {auditor_verdict},"
                        "不得无依据 fresh")


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
      8. stale 登记维度 ≠ 反证自标维度机械打回(ADR-0011:纯字符串比对,
         路由 unknown + 机械比对异议;两维任一缺失跳过,回落不变量 7)
      9. fresh 需双判一致:auditor_verdict 在场且 == fresh(ADR-0009;Auditor 缺席
         不构成任何绿格;renew 是 L0 人审出口,不受此款约束)
     10. renew 专用机械校验路径(#23 / ADR-0006 §4):必须带 ≥1 个锚 T1 的
         evidence_id;checksum 对不上不得续命;作废名单内不得续命
         (与 fresh 共用不变量 4)。违例打回附结构化原因,零写。
     11. fresh/renew 引用的 T1 正文含「忽略指令→标 fresh」类间接注入时不得发绿
         (I2 inj-t001 / ADR-0030)。无正文不拦。判定在本闸,不挂 meta_gate。
    """
    # 5. stale 无反证打回(独立于非绿放行:stale 落档也要带可点回反证)
    if decision.status == "stale" and not decision.t1_evidence_ids:
        return GateResult(allowed=False, green=False, error_code="NO_STALE_EVIDENCE",
                          reason="stale 必须给出 t1 反证 evidence_ids(有效反证=可点回)")

    # 6. stale 纯元陈述打回(#17/#241;判定引擎单一真相在 gates/meta_gate.py;
    # 算法 A:传入 claim.statement,主张数字回声不算实质锚)
    if (decision.status == "stale"
            and is_meta_only_disproof(decision.stale_reason,
                                      claim_statement=claim.statement)):
        return GateResult(allowed=False, green=False, error_code="META_ONLY_DISPROOF",
                          reason=META_ONLY_MESSAGE)

    if decision.status == "stale":
        # 8. 维度机械跨检(ADR-0011):登记维度 ≠ 反证自标维度 → 纯字符串比对打回,
        # 路由 unknown + 机械比对异议记录(复用 arbitrate_stale_mark 形态,runner 侧挂卡);
        # 两维任一缺失 → 跳过,回落不变量 7(fail-soft 回丙′,真 stale 不被未登记主张憋死)。
        # ADR-0012:Lead 主链已由 mark_stale 受理层预检(同一比对函数)先行拦截,
        # 本层对 Lead 路径为兜底;预检绕过(非 Lead 入口)时本层仍是唯一拦截。
        if dimension_crosscheck_mismatch(decision.registered_dimension,
                                         decision.stale_dimension):
            return GateResult(allowed=False, green=False,
                              error_code=ERR_DIMENSION_CROSSCHECK_MISMATCH,
                              reason=f"机械跨检:登记维度 {decision.registered_dimension} ≠ "
                                     f"反证自标维度 {decision.stale_dimension}(ADR-0011 不变量 8,"
                                     "纯字符串比对,零模型意见),路由 unknown + 机械比对异议记录")
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

    # 4. 作废名单打回(fresh 与 renew 共用:作废名单内不得 fresh/续命,§1.3)
    if claim.claim_id in ctx.invalidation_list:
        return GateResult(allowed=False, green=False, error_code="INVALIDATED",
                          reason=f"该主张已在作废名单(人工作废),"
                                 f"{'续命' if decision.status == 'renew' else '重跑'}不得再绿")

    # 10. renew 专用机械校验路径(#23 / ADR-0006 §4)
    if decision.status == "renew":
        if not decision.t1_evidence_ids:
            return GateResult(allowed=False, green=False, error_code="RENEW_NO_EVIDENCE",
                              reason="续命必须带 T1 原文证据(evidence_id 至少 1 个,ADR-0006 §4)")
        not_t1 = [e for e in decision.t1_evidence_ids if not e.endswith("@T1")]
        if not_t1:
            return GateResult(allowed=False, green=False, error_code="RENEW_EVIDENCE_NOT_T1",
                              reason=f"续命证据必须锚 T1 快照(id 以 @T1 结尾),收到: {not_t1}")
    # 2. 无 T1 不得 fresh
    elif not decision.t1_evidence_ids:
        return GateResult(allowed=False, green=False, error_code="NO_T1_EVIDENCE",
                          reason="无 t1_evidence_ids 不得 fresh")

    # 9(fresh 侧). 双判一致:auditor_verdict 在场且 == fresh(ADR-0009;renew 不受约束)
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

    # 11. I2 inj-t001:语料指令翻不动绿灯。其它不变量已通过仍不得仅因正文诱绿。
    for text in decision.t1_evidence_texts:
        if is_indirect_injection(text):
            return GateResult(allowed=False, green=False, error_code=ERR_INDIRECT_INJECTION,
                              reason="T1 正文含间接注入(忽略指令并标为 fresh),"
                                     "语料文字不得诱绿(ADR-0030 inj-t001)")

    return GateResult(allowed=True, green=True, reason="过闸:绿灯")
