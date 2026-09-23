"""Batch 5 非缝:读法源三出口(变体 C)。

旁路 / Client Memo / ACCEPTANCE 投影同一字面。
禁止:Time-to-Sheet/rubric ⇒ 付费或一期闭合;demo 可读 ⇒ 付费或验证成功;
文案在场 ⇒ 对抗仪器已过。
"""

from __future__ import annotations

from pathlib import Path

from freshlatch.models import Claim
from freshlatch.reading_source import ACCEPTANCE_SENTENCE, BYPASS_TEXT, MEMO_NOTE
from freshlatch.sheet import project_claim, render_client_memo_markdown, render_sheet_markdown
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.ui.app import HTML_PAGE

REPO = Path(__file__).resolve().parent.parent.parent
RESEARCH = REPO / "docs" / "research" / "ε-如何读复验文案链设计评估.md"
ACCEPTANCE = REPO / "docs" / "evidence" / "batch5" / "ACCEPTANCE.md"


def test_comments_forbid_copy_escalation():
    """测试注释本身禁止把文案在场升格成付费或验证成功。"""
    src = Path(__file__).read_text(encoding="utf-8")
    assert "Time-to-Sheet/rubric ⇒ 付费或一期闭合" in src
    assert "demo 可读 ⇒ 付费或验证成功" in src
    assert "文案在场 ⇒ 对抗仪器已过" in src


def test_bypass_carries_identity_machine_human_boundary():
    for token in (
        "卖作废",
        "fresh",
        "stale",
        "unknown",
        "void",
        "非法律",
        "非自动",
        "void≠stale",
    ):
        assert token in BYPASS_TEXT


def test_sheet_and_ui_project_the_same_bypass(tmp_path):
    """复验单 Markdown 与 UI 旁路都是读法源缩写,不各写各的。"""
    assert BYPASS_TEXT in HTML_PAGE
    assert 'id="how-to-read"' in HTML_PAGE
    md = render_sheet_markdown([], question="课题")
    assert BYPASS_TEXT in md
    assert md.startswith("# 复验单")


def test_client_memo_keeps_disclaimer_and_human_machine_note(tmp_path):
    """Memo 免责保留非法律/非自动,附注含人/机一句,仍无人审事件流与商业裁决。"""
    store = SQLiteStore(tmp_path / "freshlatch.db")
    claim = Claim(
        claim_id="c1",
        statement="主张仍在",
        status="stale",
        reason="机器理由",
        t1_evidence_ids=["doc#p1@T1"],
    )
    md = render_client_memo_markdown(
        [project_claim(store, claim)],
        question="课题问句",
        generated_at="2026-09-23T12:00:00+08:00",
    )
    assert "非法律意见" in md
    assert "非自动" in md
    assert MEMO_NOTE in md
    assert "void 是人的决定" in md
    assert "机器判定" in md
    assert "void≠stale" in md
    body = md.split("## DEM-3")[0]
    assert "Lead" not in body
    assert "Critic" not in body
    assert "建议进入" not in body
    assert "建议不进入" not in body
    assert "人审作废" not in md
    assert "人审续命" not in md


def test_acceptance_sentence_is_preregistered_verbatim():
    """预锁整句必须与评估文档、ACCEPTANCE 逐字一致。改字即验收作废。"""
    research = RESEARCH.read_text(encoding="utf-8")
    acceptance = ACCEPTANCE.read_text(encoding="utf-8")
    assert ACCEPTANCE_SENTENCE in research
    assert ACCEPTANCE_SENTENCE in acceptance
    assert "仅表明" in ACCEPTANCE_SENTENCE
    assert "不表明产品验证成功" in ACCEPTANCE_SENTENCE
