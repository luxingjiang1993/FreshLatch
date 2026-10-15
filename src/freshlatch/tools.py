"""工具表 + 角色白名单常量。禁令唯一真相在代码(白名单 fail-closed,ADR-0001)。

默认 Lead 白名单是 LEAD_TOOLS_W3(含 spawn_critic,不含 spawn_auditor)。
spawn_auditor 符号保留但 ADR-0009 废止:Auditor 走闸路径单轮判定,不经 Lead spawn。
未挂载 = 模型物理上不可见,不需要「返回未实装」的运行时分支。

工具权限三档(与人审出口不是同一个词):
tool_tier_0 读检索,无批可调用;
tool_tier_1 写观测,必须经 latch 里既有 HumanLatch 轮次放行;
tool_tier_2 生产臂与已禁调用,fail-closed,不进默认 Lead 白名单。
分档执行入口是 dispatch_tiered_tool。
"""

from __future__ import annotations

import json
from collections.abc import Callable

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
         "tenant_id": {"type": "string", "description": "可选声明。服务端按会话 tenant_id 注入 ACL;与会话不一致则拒绝,不传也不会变成全库"}}, ["query"]),
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
    """工具参数里的 tenant 声明。未传或空白表示调用方未声明。

    不是过滤真相。生产检索只拿它和会话 tenant_id 比对。
    """
    raw = args.get("tenant_id") if isinstance(args, dict) else None
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    return text or None


def tool_specs(names: list[str]) -> list[dict]:
    """按白名单取 OpenAI schema;白名单外的名字在本层就炸,不留给模型。"""
    return [_TOOL_DEFS[n] for n in names]


# -- 非法调用拒因(A-FC-01)------------------------------------------------------
# 循环把这些码回灌给模型。自纠预算在 run_loop,不在本模块。

REASON_UNKNOWN_TOOL = "unknown_tool"
REASON_ILLEGAL_TOOL_ARGS = "illegal_tool_args"
REASON_ILLEGAL_DIMENSION = "illegal_dimension"

# schema 向模型声明必填,但既有受理函数已经接受缺省。循环层不再因此拒绝。
# mark_stale.claim_id: Critic 签名与受理函数都不读它;Lead 缺省仍由受理函数整 call 拒绝。
_RUNTIME_OPTIONAL_REQUIRED = {
    ("mark_stale", "claim_id"),
}

_JSON_TYPE_CHECKS = {
    "string": lambda value: isinstance(value, str),
    "array": lambda value: isinstance(value, list),
    "object": lambda value: isinstance(value, dict) and not isinstance(value, list),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
}


def illegal_call_payload(*, reason_code: str, error: str) -> dict:
    """非法调用回给模型的观察。reason_code 与 error 同时在场。"""
    return {"error": error, "reason_code": reason_code}


def parse_tool_arguments(raw: str | None) -> tuple[dict | None, str | None]:
    """把工具参数 JSON 解析成对象。失败时返回中文错误,不抛给循环拆掉运行。"""
    text = raw if raw else "{}"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"工具参数不是合法 JSON: {exc.msg}"
    if not isinstance(parsed, dict):
        return None, f"工具参数必须是对象,收到: {type(parsed).__name__}"
    return parsed, None


def tool_schema_error(spec: dict, args: dict) -> str | None:
    """对照已发给模型的 JSON schema 再验。合法返回 None,不执行工具。

    只验必填、声明过的类型、additionalProperties=false。
    业务枚举(如 dimension)仍由工具处理函数整 call 拒绝。
    """
    params = spec["function"]["parameters"]
    properties = params.get("properties") or {}
    required = list(params.get("required") or [])
    name = spec["function"]["name"]
    if params.get("additionalProperties") is False:
        extra = [key for key in args if key not in properties]
        if extra:
            return f"非法参数字段: {extra};允许: {sorted(properties)}"
    missing = [
        key for key in required
        if key not in args and (name, key) not in _RUNTIME_OPTIONAL_REQUIRED
    ]
    if missing:
        return f"缺少必填参数: {missing}"
    for key, value in args.items():
        prop = properties.get(key)
        if not isinstance(prop, dict):
            continue
        expected = prop.get("type")
        if not isinstance(expected, str):
            continue
        check = _JSON_TYPE_CHECKS.get(expected)
        if check is None:
            continue
        if not check(value):
            return f"参数 {key} 类型应为 {expected},收到: {type(value).__name__}"
        items = prop.get("items") if expected == "array" else None
        item_type = items.get("type") if isinstance(items, dict) else None
        if item_type == "string" and any(not isinstance(item, str) for item in value):
            return f"参数 {key} 的元素必须是字符串"
    return None


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


# -- 工具权限三档(A-FC-03)------------------------------------------------------
# 档名只用 tool_tier_*。人审出口仍住规则闸与 HumanLatch,本模块不改那个词。

TOOL_TIER_0 = "tool_tier_0"
TOOL_TIER_1 = "tool_tier_1"
TOOL_TIER_2 = "tool_tier_2"
REASON_TOOL_TIER_DENIED = "tool_tier_denied"

# 夹具名:禁动生产臂。不进 _TOOL_DEFS,tool_specs 挂不上,也不进任何角色白名单。
FIXTURE_TOOL_TIER_2 = "arm_production"

# 读与检索。不改主张、缺口或记忆标记。
_TOOL_TIER_0_NAMES: tuple[str, ...] = (
    "retrieve",
    "read_source",
    "list_memories",
    "finish_reverify",
    "spawn_critic",
    "spawn_forensic",
)
# 写观测:主张 / 缺口 / 记忆标记,以及 Critic、Auditor 的写结论。
_TOOL_TIER_1_NAMES: tuple[str, ...] = (
    "reverify_claim",
    "mark_stale",
    "mark_gap",
    "flag_contradiction",
    "flag_dead",
    "flag_unverified",
    "propose_quarantine",
    "report_finding",
    "verdict",
)
# 已禁调用与生产臂夹具。默认 Lead 白名单不得出现这些名字。
_TOOL_TIER_2_NAMES: tuple[str, ...] = (
    "spawn_auditor",
    FIXTURE_TOOL_TIER_2,
)

TOOL_TIERS: dict[str, str] = {
    **{name: TOOL_TIER_0 for name in _TOOL_TIER_0_NAMES},
    **{name: TOOL_TIER_1 for name in _TOOL_TIER_1_NAMES},
    **{name: TOOL_TIER_2 for name in _TOOL_TIER_2_NAMES},
}

_ROLE_TOOL_WHITELISTS: tuple[tuple[str, ...], ...] = (
    LEAD_TOOLS_W1,
    LEAD_TOOLS_W3,
    LEAD_TOOLS_W9,
    CRITIC_TOOLS,
    AUDITOR_TOOLS,
    FORENSIC_TOOLS,
)

_unclassified = sorted(set(_TOOL_DEFS) - set(TOOL_TIERS))
if _unclassified:
    raise RuntimeError(f"工具未分档: {_unclassified}")
_banned_mounted = sorted(
    name
    for whitelist in _ROLE_TOOL_WHITELISTS
    for name in whitelist
    if TOOL_TIERS.get(name) == TOOL_TIER_2
)
if _banned_mounted:
    raise RuntimeError(f"{TOOL_TIER_2} 不得挂进角色白名单: {_banned_mounted}")
_mounted_names = {name for whitelist in _ROLE_TOOL_WHITELISTS for name in whitelist}
if "web_search" in _mounted_names or "web_search" in _TOOL_DEFS:
    raise RuntimeError("web_search 不得进入工具表或白名单")


def tool_tier_of(name: str) -> str | None:
    """工具权限档。未登记的名字返回 None,调度时 fail-closed。"""
    return TOOL_TIERS.get(name)


def dispatch_tiered_tool(
    name: str,
    args: dict,
    handler: Callable[[dict], dict],
    *,
    approval: object | None = None,
    trajectory: list | None = None,
) -> dict:
    """按权限档执行一次工具调用。

    tool_tier_0 直接执行。tool_tier_1 只在人审路径已签发本次工具的放行时执行。
    tool_tier_2 与未分级名字一律拒绝,不调用 handler。
    拒绝观察写入 trajectory,reason_code 为 tool_tier_denied。裸真值不算放行。
    """
    from freshlatch.latch.pipeline import human_review_allows_tool

    records = trajectory if trajectory is not None else []
    tier = tool_tier_of(name)
    if tier == TOOL_TIER_2 or tier is None:
        return _record_tier_denial(records, name, tier)
    if tier == TOOL_TIER_1 and not human_review_allows_tool(approval, name):
        return _record_tier_denial(records, name, tier)
    result = handler(args)
    records.append({
        "type": "tool_tier_observation",
        "tool": name,
        "tool_tier": tier,
        "ok": True,
        "result": result,
    })
    return result


def _record_tier_denial(records: list, name: str, tier: str | None) -> dict:
    """拒绝一次调用。不执行工具,观察留在调用方轨迹上。"""
    if tier == TOOL_TIER_2:
        error = f"{name} 属于 {TOOL_TIER_2},禁止调用"
    elif tier == TOOL_TIER_1:
        error = f"{name} 属于 {TOOL_TIER_1},未过人审"
    else:
        error = f"未分级工具 {name} 拒绝执行"
    observation = {
        "type": "tool_tier_observation",
        "tool": name,
        "tool_tier": tier,
        "ok": False,
        "fail_closed": tier != TOOL_TIER_1,
        "reason_code": REASON_TOOL_TIER_DENIED,
        "error": error,
    }
    records.append(observation)
    return observation
