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
    """红线 1:无聊天主框(无输入框/发送按钮类聊天形态)。

    允许的粘贴/表单面:T1 三卡草稿(#89)、主张导入稿(#88)、Evidence-bound 改稿条带(#200);
    均非聊天主框。仍禁止聊天态 marker。
    """
    assert HTML_PAGE.count("<textarea") == 3
    assert 'id="t1-paste-draft"' in HTML_PAGE
    assert 'id="claim-import-draft"' in HTML_PAGE
    assert "patch-after-" in HTML_PAGE
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


def test_div_tag_balance():
    """UI 模板 <div> 标签配平(源码级,防 T9 类回归:丢闭合标签卡片互相嵌套堆积)。

    回归:2026-09-20 左栏主张卡片全部堆进第一张 .claim——T9(44cf018)给
    renderClaims 加时间线块时把循环末尾 '</div></div>' 改成 '</div>',
    卡片闭合标签丢失,浏览器自动纠错把后续卡片解析进前一张。分两层查:
    1. 整个 HTML_PAGE 计数(循环体在源码里只出现一次,不平衡必然显形);
    2. renderClaims 循环体单独计数,把回归现场钉在最小范围。
    注意:这是必要不充分检查(防丢标签/手滑),不证明页面渲染正确。
    """
    import re

    opens = len(re.findall(r"<div\b", HTML_PAGE))
    closes = len(re.findall(r"</div>", HTML_PAGE))
    assert opens == closes, f"HTML_PAGE <div> 不配平:开 {opens} / 闭 {closes}"

    loop = HTML_PAGE.split("for(const c of STATE.claims)")[1].split("el.innerHTML = h;")[0]
    loop_opens = len(re.findall(r"<div\b", loop))
    loop_closes = len(re.findall(r"</div>", loop))
    assert loop_opens == loop_closes, (
        f"renderClaims 循环体内 <div> 不配平:开 {loop_opens} / 闭 {loop_closes}——单张卡片会缺闭合标签"
    )

