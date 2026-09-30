"""支撑复盘读反 / 旁近定价 / 反事实升格 / 成本当窗口误 stale 启发式(#243+#245;薄票辅缝)。

五类 must_fresh 误拦形(机制级,禁 claim_id 特判):
  A. 支撑复盘读反:把「与该判断不符 / 回看否定『窗口不佳』」读成主张被推翻。
  B. 旁近定价当窗口反证:用 Lite/入门版/降价叙事推翻『免费版收缩→市场窗口打开』。
  C. 支撑事实当反证:用付费续约率/毛利健康等支撑事实推出『窗口未开』。
  D. 反事实/敏感性升格(#245):把「若…则需重新评估 / 进一步降价至…档」未实现情景
     当成现时推翻(忽略同维现时「结论维持」)。
  E. 成本对比当窗口反证(#245):用单会话成本/成本优势叙事推翻『市场窗口打开』。

算法(确定性句法启发式,先于测试写死):
  1. 空理由 ⇒ False;
  2. 形 A/B/C/D/E 任一命中(各需推翻结论标记) ⇒ True;
  3. 合法数值锚 stale(c3/c7)不含本形 ⇒ 放行。

误伤方向单向(stale→unknown / 工具层打回引导 fresh),绝不向绿灯开口。
禁止 claim_id 特判;禁止读 T1 正文做语义比对。
"""

from __future__ import annotations

import re

# -- 形 A:复盘支撑读反 -----------------------------------------------------------
_SUPPORT_REVIEW_MARKERS: tuple[str, ...] = (
    "与该判断不符",
    "窗口不佳",
)
_RETROSPECT_MARKERS: tuple[str, ...] = (
    "回看",
    "复盘",
)

# -- 形 B:旁近定价当窗口反证 -----------------------------------------------------
_PRICING_SIDE_MARKERS: tuple[str, ...] = (
    "Lite",
    "入门版",
    "39 美元",
    "39美元",
)

# -- 形 C:支撑事实当反证 ---------------------------------------------------------
_SUPPORT_FACT_MARKERS: tuple[str, ...] = (
    "续约率",
    "毛利健康",
    "付费业务毛利",
)

_WINDOW_CLAIM_MARKERS: tuple[str, ...] = (
    "市场窗口",
    "窗口打开",
    "免费版收缩",
)

# -- 形 D:反事实/敏感性升格为现时推翻(#245) ---------------------------------------
_SENSITIVITY_SCENARIO_MARKERS: tuple[str, ...] = (
    "需重新评估",
    "进一步降价至",
    "敏感性更新",
    "敏感性",
)
# 「若…降价/收窄/档」未实现情景(预登记;现时「已降价至」无「若」不命中)
_IF_SCENARIO_RE = re.compile(r"若.{0,48}(降价|上涨|收窄|档)")
_COUNTERFACTUAL_OVERTURN: tuple[str, ...] = (
    "结论不成立",
    "已不再显著低于",
    "不再显著低于",
    "不具备显著优势",
    "成本优势将收窄",  # alone 不够,须与情景标记合取
)

# -- 形 E:把同业成本对比读成市场窗口反证(#245 活模逃逸) ---------------------------
_COST_AS_WINDOW_MARKERS: tuple[str, ...] = (
    "单会话成本",
    "成本优势",
    "约为竞品",
    "成本结构",
)

# 推翻结论:字面 + 宽松「主张…推翻」合取
_OVERTURN_LITERALS: tuple[str, ...] = (
    "推翻了主张",
    "直接推翻",
    "市场窗口并未打开",
    "窗口并未打开",
    "说明市场窗口并未",
    "市场窗口非但未开",
    "窗口非但未开",
    "而非窗口开启",
    "而非窗口打开",
    "市场窗口未因",
    "市场窗口未打开",
    "无法支持『市场窗口",
    "无法支持'市场窗口",
    "无法支持市场窗口",
    "直接攻击主张",
    "反向验证",
)
_OVERTURN_CLAIM_RE = re.compile(r"主张.{0,32}推翻|推翻.{0,32}主张")

# 闸层 / 工具层共用消息(单一真相)
SUPPORT_REVIEW_MISREAD_MESSAGE = (
    "stale 反证不得为支撑复盘读反、旁近定价/支撑事实/成本对比误拦或反事实升格:"
    "复盘否定当时『窗口不佳』是支撑不是推翻(与该判断不符 ≠ 主张被推翻);"
    "Lite/入门版/降价叙事 ≠ 市场窗口前提;"
    "付费续约率/毛利健康是对『窗口打开』的支撑,不得反读成推翻;"
    "单会话成本/成本优势对比 ≠ 市场窗口前提;"
    "敏感性/『若…则需重新评估』未实现情景 ≠ 现时推翻(现时结论以同维现时段落为准)。"
    "请回到 T1 找同维支持证据 → reverify_claim(fresh,[T1 证据 id]);"
    "不得因旁近复盘/定价/支撑事实/成本对比/反事实情景误判 stale。"
)

# Critic 白名单无 reverify_claim/mark_gap,引导语适配
SUPPORT_REVIEW_MISREAD_CRITIC_MESSAGE = (
    "mark_stale 打回:支撑复盘读反、旁近定价/支撑事实/成本对比误拦或反事实升格——"
    "复盘否定『窗口不佳』≠主张被推翻;"
    "Lite/入门版定价、续约率/毛利健康与单会话成本对比均不构成市场窗口推翻;"
    "『若…需重新评估』敏感性情景不构成现时推翻。"
    "请 report_finding 如实说明未见同维推翻性 T1 证据。"
)


def _has_overturn_conclusion(reason: str) -> bool:
    if any(m in reason for m in _OVERTURN_LITERALS):
        return True
    return bool(_OVERTURN_CLAIM_RE.search(reason))


def _has_counterfactual_overturn(reason: str) -> bool:
    """形 D 推翻结论:通用推翻字样 + 成本优势『结论不成立』族。"""
    if _has_overturn_conclusion(reason):
        return True
    return any(m in reason for m in _COUNTERFACTUAL_OVERTURN)


def _is_support_review_shape(reason: str) -> bool:
    has_support = any(m in reason for m in _SUPPORT_REVIEW_MARKERS)
    if not has_support:
        return False
    if "与该判断不符" not in reason and "窗口不佳" in reason:
        if not any(m in reason for m in _RETROSPECT_MARKERS):
            return False
    return _has_overturn_conclusion(reason)


def _is_pricing_as_window_shape(reason: str) -> bool:
    has_pricing = any(m in reason for m in _PRICING_SIDE_MARKERS)
    has_window = any(m in reason for m in _WINDOW_CLAIM_MARKERS)
    return has_pricing and has_window and _has_overturn_conclusion(reason)


def _is_support_facts_as_disproof(reason: str) -> bool:
    has_facts = any(m in reason for m in _SUPPORT_FACT_MARKERS)
    has_window = any(m in reason for m in _WINDOW_CLAIM_MARKERS)
    return has_facts and has_window and _has_overturn_conclusion(reason)


def _is_counterfactual_as_overturn(reason: str) -> bool:
    """形 D:情景标记 ∧ 推翻结论 ⇒ 打回。现时『已降价至』无情景标记 ⇒ 放行。"""
    has_scenario = any(m in reason for m in _SENSITIVITY_SCENARIO_MARKERS) or bool(
        _IF_SCENARIO_RE.search(reason)
    )
    if not has_scenario:
        return False
    return _has_counterfactual_overturn(reason)


def _is_cost_as_window_disproof(reason: str) -> bool:
    """形 E:成本对比叙事 ∧ 市场窗口主张 ∧ 推翻结论 ⇒ 打回。"""
    has_cost = any(m in reason for m in _COST_AS_WINDOW_MARKERS)
    has_window = any(m in reason for m in _WINDOW_CLAIM_MARKERS)
    return has_cost and has_window and _has_overturn_conclusion(reason)


def is_support_review_misread_as_disproof(reason: str) -> bool:
    """stale 理由是否把支撑复盘/旁近定价/支撑事实/反事实情景/成本对比读成推翻主张。"""
    if not reason:
        return False
    return (
        _is_support_review_shape(reason)
        or _is_pricing_as_window_shape(reason)
        or _is_support_facts_as_disproof(reason)
        or _is_counterfactual_as_overturn(reason)
        or _is_cost_as_window_disproof(reason)
    )
