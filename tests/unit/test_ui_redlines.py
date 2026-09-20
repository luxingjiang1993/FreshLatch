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


def test_served_html_js_escapes_intact():
    """服务出去的 HTML 必须含合法 JS 事件处理器。

    回归:Python 字符串里写 \\' 会被当转义符消耗,服务出去变成 onclick="f(''+x+'')",
    整个 <script> 语法错误、页面空白(2026-09-20 验收现场抓到)。现统一用 &quot;。
    """
    from fastapi.testclient import TestClient

    from freshlatch.ui.app import app

    html = TestClient(app).get("/").text
    assert "(''+" not in html, "onclick 处理器反斜杠转义被 Python 字符串消耗"
    for handler in ("pickClaim(&quot;", "showSource(&quot;"):
        assert handler in html, f"服务出去的 HTML 缺合法 {handler} 处理器"


def test_clause_click_to_highlight():
    """文档小节头可点击标黄(2026-09-20 验收反馈:p1/p3 只能干瞪眼)。

    证据锚点高亮仍是主路径(点证据 id → 定位+标黄);小节头点击是补充交互,
    纯前端,不碰主按钮/主界面红线(§5.6)。
    """
    assert "function pickClause(" in HTML_PAGE
    assert 'onclick="pickClause(&quot;' in HTML_PAGE


def test_tab_switch_keeps_manual_clause_selection():
    """T0/T1 页签跟随用户手动选中的小节,不跳回证据锚点(验收反馈二)。"""
    assert "let CURRENT_ANCHOR" in HTML_PAGE
    assert "CURRENT_ANCHOR,&quot;T0&quot;" in HTML_PAGE
    assert "CURRENT_ANCHOR,&quot;T1&quot;" in HTML_PAGE

