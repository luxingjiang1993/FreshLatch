"""#239:反默认 cost_model 教义/工具描述可断言片段(确定性层,零 LLM)。

钉住 Prefer 规则与「禁止默认 cost_model」落在工具 schema、focus 词表投影、
Lead/Critic persona 与 reverify 教义恢复行——表现层活模另票/同票 B 项验收。
"""

from pathlib import Path

from freshlatch.roles.critic import CRITIC_PERSONA
from freshlatch.roles.lead import LEAD_PERSONA, MARK_STALE_DIMENSION_PRECHECK
from freshlatch.tools import _TOOL_DEFS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS = REPO_ROOT / "skills"

ANTI_DEFAULT = "禁止默认 cost_model"
PREFER_INTERVIEW = "Prefer interview_reversal"
PREFER_MARKET = "Prefer market_structure"
PREFER_PRICING = "Prefer competitor_pricing"


def test_mark_stale_dimension_description_forbids_default_cost_model():
    desc = _TOOL_DEFS["mark_stale"]["function"]["parameters"]["properties"]["dimension"][
        "description"
    ]
    assert ANTI_DEFAULT in desc
    assert "interview_reversal" in desc
    assert "原主张凭什么为真" in desc


def test_focus_dimensions_md_has_prefer_rules_against_cost_model():
    text = (SKILLS / "devil_advocate" / "references" / "focus-dimensions.md").read_text(
        encoding="utf-8"
    )
    assert ANTI_DEFAULT in text
    assert PREFER_INTERVIEW in text or "Prefer `interview_reversal`" in text
    assert PREFER_MARKET in text or "Prefer `market_structure`" in text
    assert PREFER_PRICING in text or "Prefer `competitor_pricing`" in text


def test_reverify_doctrine_prefers_retry_different_dimension():
    text = (SKILLS / "reverify" / "SKILL.md").read_text(encoding="utf-8")
    assert "机械跨检预检" in text
    assert "不同" in text and "mark_stale" in text
    assert "勿重复" in text or "另一" in text


def test_lead_persona_recovery_prefers_dimension_retry():
    assert "不同" in LEAD_PERSONA and "mark_stale" in LEAD_PERSONA
    assert ANTI_DEFAULT in LEAD_PERSONA or "不得因内容谈" in LEAD_PERSONA


def test_critic_persona_has_anti_default_cost_model():
    assert ANTI_DEFAULT in CRITIC_PERSONA or "不得因内容谈" in CRITIC_PERSONA
    assert "interview_reversal" in CRITIC_PERSONA


def test_precheck_constant_mentions_retry_other_dimension():
    formatted = MARK_STALE_DIMENSION_PRECHECK.format(dim="cost_model")
    assert "勿重复本维 cost_model" in formatted
    assert "另一" in formatted
