"""主界面四条红线(§5.6)之前三条:代码/DOM 断言进 CI,必要不充分。

红线 4(不得被复述成「又一个 EvidenceOS」)只有复述测试能判,机器不可测,不在此。
止损条款高于验收:任何「为了过本测试」修改主按钮/主界面的动作判定为违规(ADR-0007 §3)。
"""

from pathlib import Path

from freshlatch.ui.app import HTML_PAGE, MAIN_BUTTON_TEXT

UI_SRC = Path(__file__).resolve().parent.parent.parent / "src" / "freshlatch" / "ui" / "app.py"


def test_main_button_whitelist():
    """红线 2:主按钮文案 ∈ {开始复验}。"""
    assert MAIN_BUTTON_TEXT == "开始复验"
    assert ">开始复验</button>" in HTML_PAGE


def test_no_chat_main_box():
    """红线 1:无聊天主框(无输入框/发送按钮类聊天形态)。"""
    assert "<textarea" not in HTML_PAGE
    for marker in ("placeholder=\"输入", "发送", "chat-input", "message-input"):
        assert marker not in HTML_PAGE


def test_forbidden_phrase_scan():
    """红线 3:源码级违禁词扫描(只防手滑,不能证明气质)。"""
    src = UI_SRC.read_text(encoding="utf-8")
    assert "开始调查" not in src
    assert "生成答案" not in src


def test_synthetic_badge_present():
    """界面标注 SYNTHETIC(合成红线,§0.4.5)。"""
    assert "SYNTHETIC" in HTML_PAGE
