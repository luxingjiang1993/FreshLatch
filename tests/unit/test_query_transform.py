"""主张查询变换单测(#158)。"""

from types import SimpleNamespace

import pytest

from freshlatch.models import Claim
from freshlatch.roles.critic import Critic
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import RunContext
from freshlatch.store.base import Chunk, InMemoryStore
from freshlatch.store.query_transform import transform_claim_query


def test_identity_when_no_dimension():
    assert transform_claim_query("专业版定价 299 元") == "专业版定价 299 元"


def test_appends_dimension_zh():
    q = transform_claim_query("我方成本仍低", dimension="cost_model")
    assert q == "我方成本仍低 成本模型"


def test_focus_overrides_dimension():
    q = transform_claim_query(
        "主张原文", dimension="cost_model", focus="competitor_pricing",
    )
    assert q.endswith("竞品价格")
    assert "成本模型" not in q


def test_rejects_open_label():
    with pytest.raises(ValueError):
        transform_claim_query("主张", focus="自由散文")


def _store() -> InMemoryStore:
    store = InMemoryStore()

    def chunk(doc_id: str, text: str) -> Chunk:
        return Chunk(
            doc_id=doc_id, chunk_id=f"{doc_id}-p1", clause_id="p1", title="t",
            text=text, source_type="public", as_of="T1", doc_version="v1",
            checksum="", tokens=8,
        )

    store.add_document(
        SimpleNamespace(doc_id="t1-pricing", as_of="T1", source_type="public",
                        title="t", doc_version="v1", checksum="", full_text="x"),
        [
            chunk("t1-pricing", "专业版定价已调整,旧定价不再适用。"),
            chunk("t1-other", "访谈纪要只谈交付周期。"),
            chunk("t1-market", "市场结构观察与定价无关。"),
        ],
    )
    return store


def test_lead_query_comes_from_transform_not_prose():
    claim = Claim(claim_id="c1", statement="专业版定价 299 元/席/月", dimension="competitor_pricing")
    ctx = RunContext(store=_store(), mode="online")
    lead = LeadReverifier(ctx, claim, llm=None)
    out = lead._t_retrieve({"query": "这是一段自由散文检索词", "as_of": "T1"})
    assert "error" not in out
    expected = transform_claim_query(claim.statement, dimension=claim.dimension)
    assert ctx.events[-1]["query"] == expected
    assert "自由散文" not in ctx.events[-1]["query"]


def test_critic_query_uses_focus_label():
    claim = Claim(claim_id="c1", statement="专业版定价 299 元/席/月", dimension="cost_model")
    ctx = RunContext(store=_store(), mode="online")
    critic = Critic(ctx, claim, llm=None, focus="competitor_pricing")
    out = critic._t_retrieve({"query": "自由改写", "as_of": "T1"})
    assert "error" not in out
    expected = transform_claim_query(claim.statement, focus="competitor_pricing")
    assert ctx.events[-1]["query"] == expected
    assert expected.endswith("竞品价格")
