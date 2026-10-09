"""四臂提示词正文只重述已锁定的句子。B2 的 diff 段是补定 draft，不是预注册原文。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "docs" / "evidence" / "patch-events" / "prompts"
_SHARED = (
    "可发送的提示词正文。",
    "补定，2026-10-08。不是预注册原文。",
    "补定，2026-10-09。不是预注册原文。",
    "根据下面给出的 before_text，改写一句纯文本。",
    "不要求模型输出 JSON 或 diff。",
    "不设专门失败令牌。",
    "不让模型打分。",
    "before_text 写进 C、T、B1 和 B2 的 claim 提示词。",
    "模型输出是纯文本。",
    "生成模型只读 DEFAULT_MODEL。",
    "温度只读 default_llm.temperature：0",
)


def _text(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


def test_four_prompt_bodies_stay_separate():
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
        assert "0.6" not in body
        assert "你是" not in body
        assert "请输出" not in body
        assert "不是可发送的提示词正文。" not in body
        assert "挡住把待改原文写进" not in body
        assert "留空。挡住 C、T、B1 与 B2 claim 的提示词正文。" not in body
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
    assert "B1 带上请求里已经有的 evidence_text。" not in c_text
    assert "B2 的 claim 也带上这份 evidence_text。" not in c_text
    assert "evidence_id" not in c_text
    assert "claim_text" not in c_text
    assert "证据段" not in c_text

    assert "只用请求里已经带的 evidence_text。" in t_text
    assert "提示词里不再检索。" in t_text
    assert "输出：纯文本 after_text。" in t_text
    assert "T 的 after_text 去掉首尾空白后须与 evidence_text 逐字相同。" in t_text
    assert "无证据改写" not in t_text
    assert "B1 带上请求里已经有的 evidence_text。" not in t_text
    assert "B2 的 claim 也带上这份 evidence_text。" not in t_text
    assert "claim_text" not in t_text
    assert "证据段" not in t_text

    assert "做法：改写。" in b1_text
    assert "输出：纯文本 after_text。" in b1_text
    assert "B1 带上请求里已经有的 evidence_text。" in b1_text
    assert "B1 的 after_text 去掉首尾空白后须与 evidence_text 逐字相同。" in b1_text
    assert "无证据改写" not in b1_text
    assert "不再检索" not in b1_text
    assert "claim_text" not in b1_text
    assert "B2 的 claim 也带上这份 evidence_text。" not in b1_text
    assert "hard reject" not in b1_text
    assert "挡住写完 B1 提示词。" not in b1_text

    claim, diff = b2_text.split("## diff 段", 1)
    assert "输出一句纯文本 claim_text。" in claim
    assert "只陈述要改什么。" in claim
    assert "不带 diff。diff 不在 claim 阶段输出。" in claim
    assert "B2 的 claim 也带上这份 evidence_text。" in claim
    assert "after_text" not in claim
    assert "挡住写完 B2 的 claim 提示词。" not in claim
    assert "已定" not in diff
    assert "### B2 diff 段提示词" in diff
    assert "补定 draft，不是预注册原文" in diff
    assert (
        "根据下面给出的 before_text、上一阶段的 claim_text，以及请求里已经有的 evidence_text，改写一句纯文本。这一句是 after_text。claim_text 不是 after_text。不要输出 diff 标记。提示词不再检索。"
        in diff
    )
    assert "这一段不写提示词。" not in diff
    assert "挡住 B2 的 diff 阶段提示词。" not in diff
