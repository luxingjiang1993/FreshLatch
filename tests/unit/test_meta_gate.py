"""元陈述句法闸单测(TDD 先行,#17 规则闸不变量 6)。

验证对象:两次 c9 实录失败形状(见 docs/evidence/w4/repro-check.md 背离一)必被打回,
合法 stale 实录形状(c3/c7,含数值锚反证)与无元陈述理由必被放行。
纯函数直测,零 LLM、零磁盘。
"""

import pytest

from freshlatch.gates.meta_gate import is_meta_only_disproof

# -- c9 两次实录失败形状(repro-check.md 背离一;原话摘录,仅去证据号)-----------

C9_RUN2_REASON = ("本轮未复测 WhatsApp Business 渗透率:1–2 月轮次的渗透率问题"
                  "(72% 主渠道口径)在本轮问卷中未保留,原因是项目组已把渠道策略重心转向"
                  "客服场景而非通讯工具选型,该指标不再列入跟踪项,因此主张失效")

C9_REPRO2_REASON = "无法确认其是否仍不低于 70%,原主张前提已失效"

# -- 合法 stale 实录形状(trajectory 中 c3/c7 的真反证,含数值锚)--------------

C3_LEGIT = ("T1 原文明确指出:Manila BizLink 与曼谷 SiamReach 均改口要求分成比例"
            "提高至 45%,PT MegaSolusi 也表示 30% 仅接受首年,第二年需重谈;且原文直接"
            "声明 3 月纪要中的 25% 分成口径作废,因此渠道分成前提已被推翻")

C7_LEGIT = ("T1 原文明确指出 SeaDesk 标准版已于 2026 年 7 月降价至 79 美元/月/店,"
            "直接推翻了主张中「竞品 SeaDesk 客单价仍为 99 美元/月」这一前提")


@pytest.mark.parametrize("reason", [C9_RUN2_REASON, C9_REPRO2_REASON])
def test_c9_recorded_failure_shapes_blocked(reason):
    """c9 两次实录:纯元陈述当推翻 ⇒ 判纯元陈述,闸层打回(背离一的机制级修复验证)。"""
    assert is_meta_only_disproof(reason)


@pytest.mark.parametrize("reason", [C3_LEGIT, C7_LEGIT])
def test_legit_numeric_anchor_reasons_pass(reason):
    """合法 stale(数值锚反证)放行:c3/c7 实录形状不得误伤。"""
    assert not is_meta_only_disproof(reason)


def test_no_meta_marker_passes():
    """无元陈述标记的理由:无数值的实体性反证照常放行(标记词表不株连)。"""
    reason = "T1 监管备忘录明确宣布该牌照制度已取消,主张前提不成立"
    assert not is_meta_only_disproof(reason)


def test_meta_clause_with_substantive_numeric_clause_passes():
    """元陈述与实质反证共存时放行:「本期未复测,但 T1 显示价格降至 79 美元」不是纯元陈述。"""
    reason = "本期未复测该指标,但 T1 渠道纪要显示价格已降至 79 美元,因此原主张失效"
    assert not is_meta_only_disproof(reason)


def test_meta_reason_with_only_numeric_meta_clause_blocked():
    """数值落在元子句内部(如「是否仍不低于 70%」)不算实质锚——剥离子句后仍为空。"""
    reason = "本轮未复测,无法确认渗透率是否仍不低于 70%,故主张无法维持"
    assert is_meta_only_disproof(reason)


def test_empty_reason_not_meta_only():
    """空理由不是「纯元陈述」:理由存在性归工具层 ≥20 字校验,闸不重复管(向后兼容)。"""
    assert not is_meta_only_disproof("")


def test_all_meta_marker_variants_recognized():
    """封闭枚举标记词表抽查:每一族至少一个代表被识别为纯元陈述形状。"""
    variants = [
        "本期未复测该指标,原主张失效",
        "该指标不再列入跟踪项,因此主张不成立",
        "暂无新数据支持,故前提无法维持",
        "央行报告待发布,无法确认原口径,主张不再成立",
        "该笔收入未入账,本期未核实,因此主张失效",
        "问卷中未保留该问题,故无法确认,主张不成立",
    ]
    for reason in variants:
        assert is_meta_only_disproof(reason), reason
