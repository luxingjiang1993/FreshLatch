"""四臂提示词空壳只含已定字段。未锁定的段落留空，不发请求。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "docs" / "evidence" / "patch-events" / "prompts"
_SHARED = (
    "不是可发送的提示词正文。",
    "不要求模型输出 JSON 或 diff。",
    "不设专门失败令牌。",
    "不让模型打分。",
    "### 指示正文",
    "挡住 C、T、B1 与 B2 claim 的提示词正文。",
    "### before_text 段",
    "挡住把待改原文写进 C、T、B1 与 B2 claim 的提示词。",
)


def _text(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


def test_four_shells_stay_separate_and_unsent():
    names = sorted(path.name for path in PROMPTS.glob("*.md"))
    assert names == ["B1.md", "B2.md", "C.md", "T.md"]
    assert not list(PROMPTS.glob("*.py"))
    bodies = [_text(name) for name in names]
    assert len(set(bodies)) == 4
    for body in bodies:
        for sentence in _SHARED:
            assert sentence in body
        assert "高分" not in body
        assert "score" not in body.lower()
        assert "temperature" not in body.lower()
        assert "你是" not in body
        assert "请输出" not in body
    formal = (ROOT / "src" / "freshlatch" / "eval" / "patch_events_formal.py").read_text(encoding="utf-8")
    arms = (ROOT / "src" / "freshlatch" / "eval" / "patch_events_arms.py").read_text(encoding="utf-8")
    assert "prompts/" not in formal
    assert "prompts/" not in arms
    assert "LLMClient(" not in formal


def test_each_shell_keeps_only_its_locked_fields():
    c_text = _text("C.md")
    t_text = _text("T.md")
    b1_text = _text("B1.md")
    b2_text = _text("B2.md")

    assert "做法：无证据改写。" in c_text
    assert "提示词里不放 evidence。" in c_text
    assert "输出：纯文本 after_text。" in c_text
    assert "evidence_text" not in c_text
    assert "evidence_id" not in c_text
    assert "claim_text" not in c_text
    assert "证据段" not in c_text

    assert "只用请求里已经带的 evidence_text。" in t_text
    assert "提示词里不再检索。" in t_text
    assert "输出：纯文本 after_text。" in t_text
    assert "无证据改写" not in t_text
    assert "claim_text" not in t_text
    assert "证据段" not in t_text

    assert "做法：改写。" in b1_text
    assert "输出：纯文本 after_text。" in b1_text
    assert "无证据改写" not in b1_text
    assert "不再检索" not in b1_text
    assert "claim_text" not in b1_text
    assert "hard reject" not in b1_text
    assert "### B1 证据段" in b1_text
    assert "挡住写完 B1 提示词。" in b1_text

    claim, diff = b2_text.split("## diff 段", 1)
    assert "输出一句纯文本 claim_text。" in claim
    assert "只陈述要改什么。" in claim
    assert "不带 diff。diff 不在 claim 阶段输出。" in claim
    assert "after_text" not in claim
    assert "### B2 claim 证据段" in claim
    assert "挡住写完 B2 的 claim 提示词。" in claim
    assert "已定" not in diff
    assert "这一段不写提示词。" in diff
    assert "### B2 diff 段提示词" in diff
    assert "挡住 B2 的 diff 阶段提示词。" in diff
