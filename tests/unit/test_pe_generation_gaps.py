"""提示词正文和核验谓词未写。正式入口在温度未锁定时拒绝发请求。"""

from __future__ import annotations

from pathlib import Path

from freshlatch.eval import patch_events_formal as formal
from freshlatch.models import MODEL_REGISTRY

ROOT = Path(__file__).resolve().parents[2]
GAPS = ROOT / "docs" / "evidence" / "patch-events" / "PROMPT-AND-VERIFY-GAPS.md"
_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")


def test_formal_entry_still_refuses_while_temperature_unlocked(monkeypatch, capsys):
    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)
    seen: list[str] = []

    def wrapped(key, default=None):
        seen.append(str(key))
        return None

    monkeypatch.setattr("os.getenv", wrapped)

    def blocked(*_args, **_kwargs):
        raise AssertionError("温度未锁定时不得构造样本或发请求")

    monkeypatch.setattr(formal, "construct_samples", blocked)
    monkeypatch.setattr(formal, "run_formal", blocked)
    assert MODEL_REGISTRY["default_llm"].temperature is None
    assert formal.main([]) == 0
    assert formal.main(["--formal"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "不把温度补成 0" in captured.err
    assert "没有可调用的自动核验器" in captured.err
    for key in _SECRET_ENV:
        assert key not in seen


def test_gap_note_lists_sentences_that_block_prompt_and_verifier():
    text = GAPS.read_text(encoding="utf-8")
    assert "状态：正文未写" in text
    for sentence in (
        "没有一句规定模型看到的是一行 JSON、纯文本，还是 diff。",
        "没有一句规定提示词删掉这两段，还是留着但禁止使用。",
        "没有一句规定提示词只根据给定 T1 chunk 改写，还是先按检索模式取 chunk 再改写。",
        "没有一句定义 claim 与 `before_text` 的差别",
        "没有一句规定 rewrite 阶段各写一份，还是共用一份。",
        "没有一句列出生成提示词可以出现主张、证据、修改类型或检索模式中的哪些。",
        "没有一句规定提示词要求模型在无法修改时输出的标记。",
        "没有一句把「不过」写成可执行谓词。",
        "没有一句规定一致是子串包含、同一数字，还是别的关系。",
        "没有一句说自动核验复用这两句，也没有一句说不复用。",
        "没有一句规定分数的范围、高分是否更该放行，或没有分数时如何排序。",
        "没有一句规定自动核验在这道闸之外还要看什么。",
        "这次不锁这类例子。",
        "不写四臂提示词正文。",
        "不规定分数刻度。",
        "不把生成温度写成 0，也不写成已锁定。",
    ):
        assert sentence in text
    assert "你是修改核对员" not in text
    assert not (ROOT / "src" / "freshlatch" / "eval" / "patch_events_verify.py").exists()
