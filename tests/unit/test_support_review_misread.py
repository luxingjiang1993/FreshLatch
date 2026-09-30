"""支撑复盘读反当反证——确定性夹具(#243)。

验证对象:本跑 c6 实录 reason(把「与该判断不符」读成推翻主张)与最小合成形
必被打回;c3/c7 合法数值锚与 #241 meta 形不受误伤。纯函数 + 工具层 + 落档路由。
零 LLM。
"""

from pathlib import Path

import pytest

from freshlatch.gates.support_review import (
    SUPPORT_REVIEW_MISREAD_MESSAGE,
    is_support_review_misread_as_disproof,
)
from freshlatch.gates.meta_gate import is_meta_only_disproof
from tests.unit.test_meta_gate import (
    C3_LEGIT,
    C7_LEGIT,
    C9_POST239_ECHO_REASON,
    C9_RUN2_REASON,
    C9_STATEMENT,
)

# -- #243 本跑 c6 实录 reason(trajectory run-20260930-232438;仅原文)-------------

C6_STATEMENT = "竞品 SeaDesk 收缩东南亚免费版、聚焦付费商户,意味着市场窗口打开"

C6_RECORDED_MISREAD_REASON = (
    "T1 原文 p3 明确指出：『3 月有分析认为免费版收缩意味着「市场付费意愿低、窗口不佳」；"
    "9 月回看，SeaDesk 付费续约率与该判断不符』，此句直接推翻了主张中『市场窗口打开』的前提"
    "——即免费版收缩预示着市场机会扩大。相反，T1 原文表明该收缩行为被当时市场解读为窗口不佳，"
    "且后续数据（高续约率）证明其判断错误，说明市场窗口并未打开，反而可能受限于付费意愿不足。"
)

# 最小合成形:复盘否定「窗口不佳」+ 误当推翻主张(不依赖整段长 reason)
C6_MIN_MISREAD_REASON = (
    "9 月回看续约率与该判断不符，此句直接推翻了主张中市场窗口打开的前提，"
    "说明市场窗口并未打开"
)

# 旁近定价当窗口反证(I1 找错形 / 本跑 Critic 回吐形)
C6_PRICING_AS_WINDOW_REASON = (
    "T1 原文明确指出，SeaDesk 在 2026 年 7 月发布 Lite 入门版，报价 39 美元/月/店，"
    "此事实直接推翻了『竞品 SeaDesk 收缩东南亚免费版、聚焦付费商户，意味着市场窗口打开』"
    "这一主张，市场窗口非但未开，反而被进一步压缩。"
)

# 支撑事实(续约率/毛利)反读成推翻(本跑 escape 形)
C6_SUPPORT_FACTS_AS_DISPROOF_REASON = (
    "T1 原文明确指出，SeaDesk 收缩免费版是因亏损，但其付费续约率高达 91%，付费业务毛利健康，"
    "且通过推出 Lite 入门版并降价进一步拓展市场；因此，『收缩免费版意味着市场窗口打开』"
    "这一主张被 T1 原文推翻——实际行为反映的是对高付费意愿市场的聚焦，而非窗口开启。"
)


@pytest.mark.parametrize(
    "reason",
    [C6_RECORDED_MISREAD_REASON, C6_MIN_MISREAD_REASON,
     C6_PRICING_AS_WINDOW_REASON, C6_SUPPORT_FACTS_AS_DISPROOF_REASON],
)
def test_c6_misread_shapes_blocked(reason):
    """#243:支撑复盘读反 / 旁近定价 / 支撑事实反读 ⇒ 须打回。"""
    assert is_support_review_misread_as_disproof(reason)


@pytest.mark.parametrize("reason", [C3_LEGIT, C7_LEGIT])
def test_legit_stale_anchors_not_blocked(reason):
    """#243 回归:c3/c7 合法数值锚不得被读反闸误伤。"""
    assert not is_support_review_misread_as_disproof(reason)


def test_empty_reason_not_misread():
    """空理由不是读反形(理由存在性归工具层字数校验)。"""
    assert not is_support_review_misread_as_disproof("")


def test_review_support_without_overturn_conclusion_passes():
    """仅复述复盘支撑句、未下『推翻主张/窗口未打开』结论 → 不是本闸打回形。"""
    reason = (
        "T1 复盘称 9 月回看付费续约率与该判断不符,否定了当时『窗口不佳』分析,"
        "与主张市场窗口打开同向"
    )
    assert not is_support_review_misread_as_disproof(reason)


def test_meta_shapes_remain_meta_only_not_support_review():
    """#241 回归:元陈述形仍走 meta 闸;读反闸不抢判。"""
    assert is_meta_only_disproof(C9_RUN2_REASON, claim_statement=C9_STATEMENT)
    assert not is_support_review_misread_as_disproof(C9_RUN2_REASON)
    assert is_meta_only_disproof(C9_POST239_ECHO_REASON, claim_statement=C9_STATEMENT)
    assert not is_support_review_misread_as_disproof(C9_POST239_ECHO_REASON)


def test_doctrine_fragments_support_review_not_disproof():
    """#243 教义主缝:reverify/rubric/persona 明示『复盘否定窗口不佳 ≠ 主张被推翻』。"""
    from freshlatch.roles.critic import CRITIC_PERSONA
    from freshlatch.roles.lead import LEAD_PERSONA

    root = Path(__file__).resolve().parent.parent.parent
    skill = (root / "skills/reverify/SKILL.md").read_text(encoding="utf-8")
    rubric = (root / "skills/freshness_audit/references/verdict-rubric.md").read_text(
        encoding="utf-8"
    )
    devil = (root / "skills/devil_advocate/SKILL.md").read_text(encoding="utf-8")
    needle = "窗口不佳"
    for text in (skill, rubric, LEAD_PERSONA, CRITIC_PERSONA, devil):
        assert needle in text
        assert "支撑" in text or "不是推翻" in text
    assert "reverify_claim" in skill and "fresh" in skill
    assert SUPPORT_REVIEW_MISREAD_MESSAGE  # 锁档消息非空


# -- #245 本跑 c5 实录 reason(trajectory run-20261001-010246;仅原文)-------------

C5_STATEMENT = "我方单会话服务成本仍低于竞品"

C5_RECORDED_COUNTERFACTUAL_REASON = (
    "T1 原文明确指出，若竞品进一步降价至 49 美元档，我方成本优势将收窄至约 20%，需重新评估。"
    "这表明在当前竞品报价下，我方单会话服务成本已不再显著低于竞品，且存在被追平甚至反超的风险，"
    "因此主张『仍低于』的结论不成立。"
)

# 最小合成形:情景标记 + 结论不成立(不依赖整段长 reason)
C5_MIN_COUNTERFACTUAL_REASON = (
    "若竞品进一步降价至 49 美元档需重新评估，因此主张仍低于的结论不成立"
)


@pytest.mark.parametrize(
    "reason",
    [C5_RECORDED_COUNTERFACTUAL_REASON, C5_MIN_COUNTERFACTUAL_REASON],
)
def test_c5_counterfactual_shapes_blocked(reason):
    """#245:反事实/敏感性升格为现时推翻 ⇒ 须打回。"""
    assert is_support_review_misread_as_disproof(reason)


C6_COST_AS_WINDOW_REASON = (
    "T1 原文明确指出，SeaDesk 7 月新报价为标准版 79 美元/月/店，据此折算其单会话成本约 "
    "0.019 美元，而我方成本为 0.009 美元，仍约为竞品的 47%，说明我方成本优势依然存在。"
    "因此，SeaDesk 收缩免费版、聚焦付费商户并未改变我方在成本结构上的相对优势，无法支持"
    "『市场窗口打开』这一主张。该反证直接攻击主张的核心前提——即『竞品收缩免费版意味着"
    "市场窗口打开』，而 T1 原文已通过成本结构对比表明，即使在收缩免费版后，竞品仍不具备"
    "成本劣势，故市场窗口未因该动作而打开。"
)


def test_c6_cost_as_window_shape_blocked():
    """#245:成本对比当市场窗口反证(活模逃逸形) ⇒ 须打回。"""
    assert is_support_review_misread_as_disproof(C6_COST_AS_WINDOW_REASON)


def test_present_tense_price_drop_still_passes():
    """#245 预登记:现时『已降价至』无敏感性情景标记 ⇒ 合法 stale 放行(c7 形)。"""
    assert not is_support_review_misread_as_disproof(C7_LEGIT)


def test_doctrine_fragments_counterfactual_not_present_overturn():
    """#245 教义主缝:reverify/rubric/persona 明示敏感性/反事实 ≠ 现时推翻。"""
    from freshlatch.roles.critic import CRITIC_PERSONA
    from freshlatch.roles.lead import LEAD_PERSONA

    root = Path(__file__).resolve().parent.parent.parent
    skill = (root / "skills/reverify/SKILL.md").read_text(encoding="utf-8")
    rubric = (root / "skills/freshness_audit/references/verdict-rubric.md").read_text(
        encoding="utf-8"
    )
    devil = (root / "skills/devil_advocate/SKILL.md").read_text(encoding="utf-8")
    needle = "需重新评估"
    for text in (skill, rubric, LEAD_PERSONA, CRITIC_PERSONA, devil):
        assert needle in text or "反事实" in text or "敏感性" in text
        assert "现时" in text or "不是推翻" in text or "不得 mark_stale" in text
