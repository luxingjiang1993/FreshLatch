"""工具表 + 角色白名单常量。禁令唯一真相在代码(白名单 fail-closed,ADR-0001)。

默认 Lead 白名单是 LEAD_TOOLS_W3(含 spawn_critic,不含 spawn_auditor)。
spawn_auditor 符号保留但 ADR-0009 废止:Auditor 走闸路径单轮判定,不经 Lead spawn。
未挂载 = 模型物理上不可见,不需要「返回未实装」的运行时分支。
"""

from __future__ import annotations

FOCUS_DIMENSIONS: tuple[str, ...] = (
    "competitor_pricing",   # 竞品价格:主张前提建立在竞品定价/价格对标数据上;
    "regulatory_stance",    # 监管口径:主张前提建立在监管政策/官方口径上;
    "interview_reversal",   # 访谈改口:主张前提建立在访谈/纪要/口头口径上(机制维度);
    "cost_model",           # 成本模型:主张前提建立在成本/费用结构测算上;
    "market_structure",     # 市场结构:主张前提建立在市场规模/格局/份额判断上;
    "tech_ecosystem",       # 技术生态:主张前提建立在技术栈/生态位判断上;
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
        "retrieve", "检索语料库,返回相关证据块(evidence_id 形如 doc_id#p2)。"
                    "检索串由主张查询变换产出;query 若传入会被忽略,调用方不得自由改写。",
        {"query": {"type": "string", "description": "忽略。检索串由主张查询变换产出"},
         "source_type": {"type": "string", "description": "可选:private|public|internal"},
         "as_of": {"type": "string", "description": "可选:T0 签发时快照|T1 复验时刻快照"},
         "tenant_id": {"type": "string", "description": "可选:显式传入才按租户硬过滤;不传则不过滤租户"}}, ["query"]),
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
        "mark_stale", "判定主张已失效;reason 必须含显式因果句(指出 T1 原文哪一句推翻了主张哪个前提);"
                      "evidence_ids 必填,逐字引用 retrieve 返回的 T1 证据 id(形如 doc#p2@T1),不得编造;"
                      "dimension 必填,填本反证自身攻击的维度(封闭枚举 6 值之一,非法值整 call 拒绝并回列词表)",
        {"claim_id": {"type": "string"},
         "reason": {"type": "string"},
         "evidence_ids": {"type": "array", "items": {"type": "string"},
                          "description": "推翻性 T1 证据 id,retrieve 返回过什么才能引用什么"},
         "dimension": {"type": "string",
                       "description": f"本反证自身攻击的维度(前提出处语义):{'/'.join(FOCUS_DIMENSIONS)}. "
                                    "维度 = 本反证所攻击之主张前提的证据出处类型,不是反证内容的主题词。"
                                    "判法:问『原主张凭什么为真?』——答所依赖的证据类型即维度。"
                                    "interview_reversal 是机制维度:凡证据出自访谈/纪要/口头口径,"
                                    "无论其内容谈的是定价、成本还是监管,一律填 interview_reversal。"
                                    "Prefer:访谈/纪要→interview_reversal;采用率/规模普查→market_structure;"
                                    "客单价/报价→competitor_pricing。"
                                    "禁止默认 cost_model:仅当主张前提建立在成本/费用结构测算上才填;有疑勿填 cost_model。"}},
        ["claim_id", "reason", "evidence_ids", "dimension"]),
    "mark_gap": _fn(
        "mark_gap", "记录证据缺口(T1 无覆盖、证据不足)",
        {"description": {"type": "string"}}, ["description"]),
    "spawn_critic": _fn(
        "spawn_critic", "派驻 Critic 专找该主张的反证(只传主张原文+focus+evidence_ids,深度恒 1)",
        {"focus": {"type": "string", "description": f"可选:{'/'.join(FOCUS_DIMENSIONS)},省略=不限方向"}},
        []),
    "spawn_auditor": _fn(
        "spawn_auditor", "废止(ADR-0009/0010):勿调用。Auditor 由闸路径单轮判定,不经 Lead spawn",
        {"claim_id": {"type": "string"}}, ["claim_id"]),
    "spawn_forensic": _fn(
        "spawn_forensic", "派驻 Forensic 审核长期记忆(只传记忆条目集,深度恒 1)",
        {"focus": {"type": "string", "description": f"可选:{'/'.join(FOCUS_DIMENSIONS)},省略=全面审核"}}, []),
    "finish_reverify": _fn(
        "finish_reverify", "收尾宣布本轮复验结束", {}, []),
    "report_finding": _fn(
        "report_finding", "Critic 结论唯一出口:报告反证(须锚 T1 evidence_id)",
        {"finding": {"type": "string"}}, ["finding"]),
    "verdict": _fn(
        "verdict", "Auditor 判定唯一出口:fresh|stale|unknown + 理由(进规则闸,Auditor 不得拥有放行权)",
        {"status": {"type": "string"}, "reason": {"type": "string"}}, ["status"]),
    # 记忆审核工具 (W9-W12)
    "list_memories": _fn(
        "list_memories", "获取本课题长期记忆条目召回集(记忆刑侦专用)",
        {"as_of": {"type": "string", "description": "可选:T0|T1,默认返回可召回的记忆条目"}}, []),
    "flag_contradiction": _fn(
        "flag_contradiction", "标记两条记忆条目互斥(需说明互斥原因)",
        {"memory_id_a": {"type": "string", "description": "第一条记忆ID"},
         "memory_id_b": {"type": "string", "description": "第二条记忆ID"},
         "reason": {"type": "string", "description": "两条记忆如何互斥的说明"}},
        ["memory_id_a", "memory_id_b", "reason"]),
    "flag_dead": _fn(
        "flag_dead", "标记记忆条目已死(需提供T1证据证明其失效)",
        {"memory_id": {"type": "string", "description": "记忆ID"},
         "reason": {"type": "string", "description": "记忆为何失效的原因"},
         "evidence_ids": {"type": "array", "items": {"type": "string"}, "description": "证明记忆已死的T1证据ID列表"}},
        ["memory_id", "reason"]),
    "flag_unverified": _fn(
        "flag_unverified", "标记记忆条目未经证实(无source_ref或出处不可追溯)",
        {"memory_id": {"type": "string", "description": "记忆ID"},
         "reason": {"type": "string", "description": "为何认为该记忆未经证实的原因"}},
        ["memory_id", "reason"]),
    "propose_quarantine": _fn(
        "propose_quarantine", "提议将记忆条目移出召回集(待人确认,不是直接删除)",
        {"memory_ids": {"type": "array", "items": {"type": "string"}, "description": "提议隔离的记忆ID列表"},
         "reason": {"type": "string", "description": "提议隔离的原因"}},
        ["memory_ids"]),
}


# 架构插座:web_search 仅插座,不进任何角色白名单(§0.4.2/§4.6:评测期代码级禁联网)。
# eval 模式运行时纯本地;本期未挂载 = 模型物理上不可见,联网破坏 must_stale 可复现性。
WEB_SEARCH_SOCKET_NOTE = "web_search 为架构插座,W5–W8 再议;W1–W4 不在任何白名单"


def optional_tenant_id(args: dict) -> str | None:
    """工具参数里的可选租户。未传或空白表示不启租户过滤。"""
    raw = args.get("tenant_id") if isinstance(args, dict) else None
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    return text or None


def tool_specs(names: list[str]) -> list[dict]:
    """按白名单取 OpenAI schema;白名单外的名字在本层就炸,不留给模型。"""
    return [_TOOL_DEFS[n] for n in names]


# -- 角色白名单(阶段挂载视图)----------------------------------------------------

# 历史 W1 视图(无 spawn_critic)。现行默认 Lead = LEAD_TOOLS_W3,不含 spawn_auditor。
LEAD_TOOLS_W1: tuple[str, ...] = (
    "retrieve", "read_source", "reverify_claim", "mark_stale", "mark_gap", "finish_reverify",
)
LEAD_TOOLS_W3: tuple[str, ...] = LEAD_TOOLS_W1 + ("spawn_critic",)
LEAD_TOOLS_W9: tuple[str, ...] = LEAD_TOOLS_W3 + ("list_memories", "spawn_forensic")  # W9-W12: 添加记忆审核能力

# Critic:只许判死不许判活、无放行、无 spawn(深度恒 1)
CRITIC_TOOLS: tuple[str, ...] = ("retrieve", "read_source", "mark_stale", "report_finding")

# Auditor(W5–W8 历史挂载视图):单轮判定 SOP。现行不经 Lead spawn_auditor(ADR-0009)。
AUDITOR_TOOLS: tuple[str, ...] = ("verdict",)

# Forensic(W9-W12):记忆审核专用，可访问记忆相关工具，不能改主张或放行
FORENSIC_TOOLS: tuple[str, ...] = (
    "list_memories", "retrieve", "read_source",  # 读取记忆和语料进行对比
    "flag_dead", "flag_contradiction", "flag_unverified",  # 标记问题记忆
    "propose_quarantine",  # 提议隔离
)
