"""Auditor:单轮 structured-output 判定 SOP(W5–W8 实装,#20/ADR-0009;#22 落地)。

形态(spec 03 §3.2 既定,#20 确认推翻须新工单):一次 structured-output 调用,无工具无循环,
输入 = 证据包(主张 + Lead 判定包 + 白名单内证据块文本),输出 = verdict + dimension_match +
理由。freshness_audit SKILL.md 即 system prompt(Runner 沿派驻链注入,#19 skills 接线);
教义表缺失时回退内联 AUDITOR_PERSONA,调用方须落 skill_fallback 事件(不静默降级)。

stale 路径维度核对(#22/ADR-0010):输入为 Lead 的 mark_stale 反证包时,stale 判定必须给出
dimension_match(反证锚定维度与主张前提/度量维度是否一致);闸不变量 7 只机械消费该结构化
flag——语义判断全部住在本角色层(闸管不变量,人格管语义质量)。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

# 证据包 schema 版本(#20 子决策 1:冻结输入契约,「同输入同判定」可守;版本随验收报告登记)。
EVIDENCE_PACKET_SCHEMA_VERSION = "1"

VERDICT_STATUSES = ("fresh", "stale", "unknown")

# 教义表加载失败的兜底人格(单一真相仍在 skills/freshness_audit/SKILL.md;不复制铁律全文)。
AUDITOR_PERSONA = """你是 Auditor,FreshLatch 的判定尺。你对给定主张与证据包做单轮三档判定
(fresh/stale/unknown),无检索、无工具、无放行权;你的输出进规则闸,闸才是绿灯唯一出口。
判定对象永远是主张签发原文;判 fresh/stale 的证据必须锚 T1;理由必须引用证据包内的证据 id,
写不出对应关系即降档 unknown。stale 判定时必须核对反证锚定的前提/度量维度与主张是否一致
(定价≠成本),并输出 dimension_match。完整教义(skills/freshness_audit/SKILL.md)正常由
Runner 整份注入本提示;若你未见教义表,说明注入失败,仍须按本兜底口径执行。"""


@dataclass
class EvidencePacket:
    """Auditor 的证据包(输入契约,schema 版本化)。evidence_texts 只装本会话 retrieve
    白名单内返回过的块文本——包外内容一律不进入判定(防编造)。"""

    claim_id: str
    statement: str
    t0_evidence_ids: list[str]
    lead_status: str          # fresh | stale(Lead 试图落的判定,即触发路径)
    lead_reason: str
    lead_evidence_ids: list[str]
    evidence_texts: dict[str, str]
    schema_version: str = EVIDENCE_PACKET_SCHEMA_VERSION

    def as_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "claim_id": self.claim_id,
            "statement": self.statement,
            "t0_evidence_ids": list(self.t0_evidence_ids),
            "lead_status": self.lead_status,
            "lead_reason": self.lead_reason,
            "lead_evidence_ids": list(self.lead_evidence_ids),
            "evidence_texts": dict(self.evidence_texts),
        }


@dataclass
class AuditorVerdict:
    """Auditor structured-output 的结构化判定(闸可机械消费)。"""
    status: str                                   # fresh | stale | unknown
    reason: str = ""
    dimension_match: bool | None = None           # 仅 stale 判定的维度核对;None = 未给/不适用
    schema_version: str = EVIDENCE_PACKET_SCHEMA_VERSION  # 应答所对的证据包契约版本(留档)


def parse_verdict(content: object, *, schema_version: str = EVIDENCE_PACKET_SCHEMA_VERSION) -> AuditorVerdict:
    """structured-output 解析,fail-closed:非 JSON / status 非法 → unknown。

    机器绝不把解析失败当 fresh(ADR-0009 在场不变量的兜底读法);dimension_match 只接受
    bool,其余类型归 None(闸不机械消费含糊字段)。
    """
    try:
        payload = json.loads(content)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return AuditorVerdict(status="unknown",
                              reason=f"[Auditor 输出非 JSON,fail-closed] {str(content)[:100]}",
                              schema_version=schema_version)
    if not isinstance(payload, dict):
        return AuditorVerdict(status="unknown",
                              reason=f"[Auditor 输出非对象,fail-closed] {str(content)[:100]}",
                              schema_version=schema_version)
    status = payload.get("status")
    if status not in VERDICT_STATUSES:
        return AuditorVerdict(status="unknown",
                              reason=f"[Auditor status 非法:{status!r},fail-closed]",
                              schema_version=schema_version)
    dm = payload.get("dimension_match")
    return AuditorVerdict(
        status=status,
        reason=str(payload.get("reason", "")),
        dimension_match=dm if isinstance(dm, bool) else None,
        schema_version=schema_version,
    )


class Auditor:
    """单轮判定员:一次调用一次判定,同证据包必出同判定(金标可复现性的来源)。"""

    def __init__(self, llm, *, doctrine: str | None = None) -> None:
        self.llm = llm
        self._doctrine = doctrine  # freshness_audit SKILL.md 正文(Runner 注入);None = 兜底

    @property
    def using_fallback(self) -> bool:
        return self._doctrine is None

    def build_packet(self, claim, *, lead_status: str, lead_reason: str,
                     lead_evidence_ids: list[str],
                     evidence_texts: dict[str, str] | None = None) -> EvidencePacket:
        """装配证据包:块文本只从白名单 evidence_texts 取,缺的 id 不编造文本。"""
        texts = evidence_texts or {}
        return EvidencePacket(
            claim_id=claim.claim_id,
            statement=claim.statement,
            t0_evidence_ids=list(claim.t0_evidence_ids),
            lead_status=lead_status,
            lead_reason=lead_reason,
            lead_evidence_ids=list(lead_evidence_ids),
            evidence_texts={eid: texts[eid] for eid in lead_evidence_ids if eid in texts},
        )

    def judge(self, packet: EvidencePacket, *, decoding=None) -> AuditorVerdict:
        """单轮 structured-output 判定。system = 教义表(兜底内联人格),user = 证据包 JSON。"""
        system = self._doctrine if self._doctrine is not None else AUDITOR_PERSONA
        msg = self.llm.chat(
            [{"role": "system", "content": system},
             {"role": "user", "content": json.dumps(packet.as_dict(), ensure_ascii=False)}],
            response_format={"type": "json_object"},
            decoding=decoding,
        )
        return parse_verdict(getattr(msg, "content", None), schema_version=packet.schema_version)
