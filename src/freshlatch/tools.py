"""工具表 + 角色白名单常量。禁令唯一真相在代码(白名单 fail-closed,ADR-0001)。

阶段挂载(§1.2):W1–W2 Lead 白名单无 spawn_critic;W1–W4 无 spawn_auditor 与记忆卫生工具。
未挂载 = 模型物理上不可见,不需要「返回未实装」的运行时分支。
"""

from __future__ import annotations

FOCUS_DIMENSIONS: tuple[str, ...] = (
    "competitor_pricing",   # 竞品价格
    "regulatory_stance",    # 监管口径
    "interview_reversal",   # 访谈改口
    "cost_model",           # 成本模型
    "market_structure",     # 市场结构
    "tech_ecosystem",       # 技术生态
)

# -- 复验工具 OpenAI schema(§3.1)------------------------------------------------

def _fn(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


_TOOL_DEFS: dict[str, dict] = {
    "retrieve": _fn(
        "retrieve", "检索语料库,返回相关证据块(evidence_id 形如 doc_id#p2)",
        {"query": {"type": "string", "description": "检索词"},
         "source_type": {"type": "string", "description": "可选:private|public|internal"},
         "as_of": {"type": "string", "description": "可选:T0 签发时快照|T1 复验时刻快照"}}, ["query"]),
    "read_source": _fn(
        "read_source", "按 doc_id 读原文全文(ground truth 是原文,不是 chunk)",
        {"doc_id": {"type": "string"}, "as_of": {"type": "string", "description": "T0|T1,默认 T1"}}, ["doc_id"]),
    "reverify_claim": _fn(
        "reverify_claim", "对主张下判定并给出证据(fresh 的唯一写入口,进规则闸;stale 必须走 mark_stale)",
        {"claim_id": {"type": "string"},
         "status": {"type": "string", "description": "fresh|unknown"},
         "evidence_ids": {"type": "array", "items": {"type": "string"}}},
        ["claim_id", "status"]),
    "mark_stale": _fn(
        "mark_stale", "判定主张已失效;reason 必须含显式因果句(指出 T1 原文哪一句推翻了主张哪个前提)",
        {"claim_id": {"type": "string"}, "reason": {"type": "string"}}, ["claim_id", "reason"]),
    "mark_gap": _fn(
        "mark_gap", "记录证据缺口(T1 无覆盖、证据不足)",
        {"description": {"type": "string"}}, ["description"]),
    "spawn_critic": _fn(
        "spawn_critic", "派驻 Critic 专找该主张的反证(只传主张原文+focus+evidence_ids,深度恒 1)",
        {"focus": {"type": "string", "description": f"可选:{'/'.join(FOCUS_DIMENSIONS)},省略=不限方向"}},
        []),
    "spawn_auditor": _fn(
        "spawn_auditor", "派驻 Auditor 做单轮判定(W5–W8 挂载)",
        {"claim_id": {"type": "string"}}, ["claim_id"]),
    "finish_reverify": _fn(
        "finish_reverify", "收尾宣布本轮复验结束", {}, []),
    "report_finding": _fn(
        "report_finding", "Critic 结论唯一出口:报告反证(须锚 T1 evidence_id)",
        {"finding": {"type": "string"}}, ["finding"]),
    "verdict": _fn(
        "verdict", "Auditor 判定唯一出口:fresh|stale|unknown + 理由(进规则闸,Auditor 不得拥有放行权)",
        {"status": {"type": "string"}, "reason": {"type": "string"}}, ["status"]),
}


# 架构插座:web_search 仅插座,不进任何角色白名单(§0.4.2/§4.6:评测期代码级禁联网)。
# eval 模式运行时纯本地;本期未挂载 = 模型物理上不可见,联网破坏 must_stale 可复现性。
WEB_SEARCH_SOCKET_NOTE = "web_search 为架构插座,W5–W8 再议;W1–W4 不在任何白名单"


def tool_specs(names: list[str]) -> list[dict]:
    """按白名单取 OpenAI schema;白名单外的名字在本层就炸,不留给模型。"""
    return [_TOOL_DEFS[n] for n in names]


# -- 角色白名单(阶段挂载视图)----------------------------------------------------

# W1–W2 Lead:无 spawn_critic(Critic W3 才启用)、无 spawn_auditor(W5–W8)
LEAD_TOOLS_W1: tuple[str, ...] = (
    "retrieve", "read_source", "reverify_claim", "mark_stale", "mark_gap", "finish_reverify",
)
LEAD_TOOLS_W3: tuple[str, ...] = LEAD_TOOLS_W1 + ("spawn_critic",)

# Critic:只许判死不许判活、无放行、无 spawn(深度恒 1)
CRITIC_TOOLS: tuple[str, ...] = ("retrieve", "read_source", "mark_stale", "report_finding")

# Auditor(W5–W8):单轮判定 SOP,唯一出口 verdict,不得拥有放行权
AUDITOR_TOOLS: tuple[str, ...] = ("verdict",)
