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

# -- #241 修后逃逸形:元标记子句剥除后残留「主张数字回声」(70% 来自 statement) --
C9_STATEMENT = "目标市场 WhatsApp Business 渗透率不低于 70%"
C9_POST239_ECHO_REASON = (
    "T1 原文明确指出：'本轮未复测 WhatsApp Business 渗透率:1–2 月轮次的渗透率问题"
    "(72% 主渠道口径)在本轮问卷中未保留,原因是项目组已把渠道策略重心转向客服场景而非"
    "通讯工具选型,该指标不再列入跟踪项。' 该句直接推翻了主张 c9 中关于『目标市场 "
    "WhatsApp Business 渗透率不低于 70%』的前提，因该指标已不再被追踪，故无法支持原主张。"
)
# 最小合成形:元标记 + 仅复述主张内数字,无独立实质锚
C9_MIN_ECHO_REASON = (
    "本轮未复测该指标,该句直接推翻了主张中『渗透率不低于 70%』的前提,故主张失效"
)

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
        # #246 缺口 paraphrase 族
        "本期无新测量该指标,原主张失效",
        "之后无任何更新记录进入本档,因此主张不成立",
        "数据缺口声明:本期无覆盖,故前提无法维持",
    ]
    for reason in variants:
        assert is_meta_only_disproof(reason), reason


# -- #246 本跑 c10 实录 reason(trajectory run-20261001-010402) -----------------

C10_STATEMENT = "雅加达双语客服专员综合用工成本约 450 美元/月"

C10_RECORDED_GAP_REASON = (
    "T1 原文明确声明『雅加达与马尼拉双语客服专员、渠道经理的综合用工成本,本期无新测量』,"
    "且『2 月调研数据(雅加达约 450 美元/月)之后无任何更新记录进入本档』,说明该主张所依赖的 "
    "450 美元/月数据已过时,且 T1 未提供任何新证据支持其仍成立。因此,主张前提被 T1 原文明确推翻。"
)

C10_MIN_GAP_REASON = (
    "本期无新测量,之后无任何更新记录进入本档,因此主张前提被推翻"
)


def test_c10_recorded_gap_shape_blocked_with_statement():
    """#246:本跑 c10 缺口声明形在传入 statement 后必打回。"""
    assert is_meta_only_disproof(C10_RECORDED_GAP_REASON, claim_statement=C10_STATEMENT)


def test_t1_prefix_alone_not_numeric_anchor():
    """#246:『T1 原文…』时点标签不是实质数值锚(与 cN 噪声同向)。"""
    reason = "T1 原文明确声明本期无新测量,因此主张前提被推翻"
    assert is_meta_only_disproof(reason)


C9_ABANDON_TRACK_72_REASON = (
    "T1 原文明确指出：'本轮未复测 WhatsApp Business 渗透率:1–2 月轮次的渗透率问题"
    "(72% 主渠道口径)在本轮问卷中未保留,原因是项目组已把渠道策略重心转向客服场景而非"
    "通讯工具选型,该指标不再列入跟踪项。' 该句表明签发时主张所依赖的核心数据（72% 渗透率）"
    "在 T1 已被主动放弃追踪，且无新数据替代，因此无法支持『不低于 70%』的前提。"
)


def test_c9_abandon_track_72_false_anchor_blocked():
    """#246:『放弃追踪』子句中的 72% 不得当独立实质锚(活模逃逸形)。"""
    assert is_meta_only_disproof(C9_ABANDON_TRACK_72_REASON, claim_statement=C9_STATEMENT)


C10_DATE_NOISE_GAP_REASON = (
    "T1 原文明确声明『雅加达与马尼拉双语客服专员、渠道经理的综合用工成本,本期无新测量;"
    "2026 年 11 月的最低工资例行调整尚未发生,2 月调研数据(雅加达约 450 美元/月、马尼拉约 "
    "520 美元/月)之后无任何更新记录进入本档』，该句直接推翻主张『雅加达双语客服专员综合用工"
    "成本约 450 美元/月』的前提——即该数据在 T1 时点仍有效；因无新数据覆盖，原数据已过时，无法支撑主张。"
)


def test_c10_date_noise_gap_shape_blocked():
    """#246:年月日历噪声 + 尚未发生 不得撑开缺口形放行。"""
    assert is_meta_only_disproof(C10_DATE_NOISE_GAP_REASON, claim_statement=C10_STATEMENT)


def test_c9_post239_echo_shape_blocked_with_statement():
    """#241:修后逃逸形(元+主张 70% 回声)在传入 claim.statement 后必打回。"""
    assert is_meta_only_disproof(C9_POST239_ECHO_REASON, claim_statement=C9_STATEMENT)


def test_c9_min_echo_synthetic_blocked_with_statement():
    """#241:最小「元标记 + 主张数字回声」合成形必打回(不依赖整段长 reason)。"""
    assert is_meta_only_disproof(C9_MIN_ECHO_REASON, claim_statement=C9_STATEMENT)


def test_echo_alone_without_statement_may_still_pass():
    """缺省不传 claim_statement 时不启用回声黑名单——对无回声依赖的历史形打回不弱化;
    本测钉:仅回声形在缺省下仍可能放行(行为与 ADR-0008 当日一致),接线处必须传 statement。"""
    # 最小回声形缺省:残留子句含 70 → 按旧算法放行
    assert not is_meta_only_disproof(C9_MIN_ECHO_REASON)


def test_meta_plus_independent_numeric_still_passes_with_statement():
    """元 + 独立实质数值锚(不在主张 statement 内)传入 statement 后仍放行。"""
    statement = "竞品 SeaDesk 客单价仍为 99 美元/月"
    reason = "本期未复测该指标,但 T1 渠道纪要显示价格已降至 79 美元,因此原主张失效"
    assert not is_meta_only_disproof(reason, claim_statement=statement)


def test_c3_c7_legit_still_pass_with_their_statements():
    """#241 回归:c3/c7 合法数值锚在传入各自 statement 后仍放行(防误伤)。"""
    c3_stmt = "渠道伙伴分成比例维持在 25% 及以下"
    c7_stmt = "竞品 SeaDesk 客单价仍为 99 美元/月"
    assert not is_meta_only_disproof(C3_LEGIT, claim_statement=c3_stmt)
    assert not is_meta_only_disproof(C7_LEGIT, claim_statement=c7_stmt)


def test_default_none_does_not_weaken_historical_blocks():
    """缺省 claim_statement=None 时,对无回声依赖的历史形状打回行为不弱化。"""
    assert is_meta_only_disproof(C9_RUN2_REASON)
    assert is_meta_only_disproof(C9_REPRO2_REASON)
    assert is_meta_only_disproof(C9_RUN2_REASON, claim_statement=None)
    assert is_meta_only_disproof(C9_REPRO2_REASON, claim_statement=C9_STATEMENT)


def test_doctrine_fragments_stop_tracking_is_not_disproof():
    """#241/#246 教义辅路径:reverify/rubric/persona 明示停追踪/缺口≠推翻。"""
    from pathlib import Path

    from freshlatch.roles.critic import CRITIC_PERSONA
    from freshlatch.roles.lead import LEAD_PERSONA

    root = Path(__file__).resolve().parent.parent.parent
    skill = (root / "skills/reverify/SKILL.md").read_text(encoding="utf-8")
    rubric = (root / "skills/freshness_audit/references/verdict-rubric.md").read_text(
        encoding="utf-8"
    )
    for text in (skill, rubric, LEAD_PERSONA, CRITIC_PERSONA):
        assert "停追踪" in text
        assert "无新测量" in text or "数据缺口" in text
    assert "mark_gap" in skill and "unknown" in skill
    assert "unknown" in rubric
    assert "mark_gap" in LEAD_PERSONA and "unknown" in LEAD_PERSONA
    # Critic 无 mark_gap 白名单,引导至不得 mark_stale
    assert "不得 mark_stale" in CRITIC_PERSONA
