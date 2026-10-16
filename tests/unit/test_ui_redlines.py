"""主界面四条红线(§5.6)之前三条:代码/DOM 断言进 CI,必要不充分。

红线 4(不得被复述成「又一个 EvidenceOS」)只有复述测试能判,机器不可测,不在此。
止损条款高于验收:任何「为了过本测试」修改主按钮/主界面的动作判定为违规(ADR-0007 §3)。
"""

import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path

from freshlatch.ui.app import BADGE, HTML_PAGE, MAIN_BUTTON_TEXT

UI_SRC = Path(__file__).resolve().parent.parent.parent / "src" / "freshlatch" / "ui" / "app.py"


def test_main_button_whitelist():
    """红线 2(#663):首页主 CTA = 一键样例;导入为次按钮;不得叫「生成答案」。"""
    assert MAIN_BUTTON_TEXT == "一键样例"
    assert 'id="btn-run" onclick="startSample()">一键样例</button>' in HTML_PAGE
    assert "function startSample(" in HTML_PAGE
    assert "/api/t1-source/synthetic" in HTML_PAGE
    assert "await runReverify()" in HTML_PAGE
    assert 'class="big"' in HTML_PAGE
    assert HTML_PAGE.count('class="big"') == 1
    assert 'onclick="importDocket()"' in HTML_PAGE
    assert "主张导入稿" in HTML_PAGE
    # 导入按钮保持 ghost,不占用唯一主按钮
    assert 'class="ghost" type="button" onclick="importDocket()"' in HTML_PAGE
    assert "正在用新材料核对旧结论" in HTML_PAGE
    assert "大约两分钟" in HTML_PAGE
    assert 'id="reverify-progress"' in HTML_PAGE
    assert "生成答案" not in HTML_PAGE
    # HumanLatch 动词集仍只经 discard|renew,本票不改
    assert "action: 'discard'" in HTML_PAGE
    assert "action:'renew'" in HTML_PAGE


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


# #664 三类白话清单。展示映射,不新增后端状态。

_PROTOCOL_WORDS = ("claim", "latch", "T0", "fail-closed")
_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "source", "track", "wbr",
}


class _CraftsmanMainPath(HTMLParser):
    """职人默认主路径可见文本。脚本、审计面板、弹层、高级折叠内文不计入。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._stack: list[str] = []
        self._summary_done = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = dict(attrs)
        classes = set((ad.get("class") or "").split())
        entering = None
        if not self._stack:
            if tag in ("script", "style"):
                entering = "raw"
            elif ad.get("id") == "audit-panel" or "modal" in classes:
                entering = "hide"
            elif ad.get("id") == "advanced-evidence":
                entering = "advanced"
        else:
            top = self._stack[-1]
            if top == "raw":
                entering = "raw"
            elif top == "hide":
                entering = "hide"
            elif top == "summary":
                entering = "summary"
            elif top == "advanced":
                entering = "summary" if tag == "summary" and not self._summary_done else "hide"
        if entering:
            self._stack.append(entering)
        if tag in _VOID_TAGS and self._stack:
            self._stack.pop()

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS or not self._stack:
            return
        top = self._stack.pop()
        if top == "summary":
            self._summary_done = True
        elif top == "advanced":
            self._summary_done = False

    def handle_data(self, data: str) -> None:
        if not self._stack or self._stack[-1] == "summary":
            self.parts.append(data)


def _craftsman_main_text(html: str) -> str:
    parser = _CraftsmanMainPath()
    parser.feed(html)
    return "".join(parser.parts)


def _grab_js(name: str) -> str:
    """按花括号配平截取顶层 function,供 node 跑展示映射。"""
    key = f"function {name}("
    start = HTML_PAGE.index(key)
    i = HTML_PAGE.index("{", start)
    depth = 0
    quote = ""
    k = i
    while k < len(HTML_PAGE):
        ch = HTML_PAGE[k]
        if quote:
            if ch == "\\":
                k += 2
                continue
            if ch == quote:
                quote = ""
            k += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            k += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return HTML_PAGE[start:k + 1]
        k += 1
    raise AssertionError(f"函数未闭合: {name}")


def test_issue_664_three_lists_are_display_maps():
    """三类清单可见且各有一行定义;映射仍是 fresh / stale|unknown / latch pending。"""
    assert 'id="vernacular-lists"' in HTML_PAGE
    assert 'data-map="fresh"' in HTML_PAGE
    assert 'data-map="stale|unknown"' in HTML_PAGE
    assert 'data-map="latch pending"' in HTML_PAGE
    assert ">仍可信</h3>" in HTML_PAGE
    assert ">可能过期</h3>" in HTML_PAGE
    assert ">要你确认</h3>" in HTML_PAGE
    assert "证据仍支撑这条结论" in HTML_PAGE
    assert "材料变了或证据不够" in HTML_PAGE
    assert "系统拦下，需你拍板" in HTML_PAGE
    assert set(BADGE) == {"fresh", "stale", "unknown", "void"}
    bucket = _grab_js("vernacularBucket")
    assert "/api/" not in bucket
    assert 'c.status === "fresh"' in bucket
    assert 'c.status === "stale" || c.status === "unknown"' in bucket
    assert "awaitingConfirm" in bucket
    advanced = HTML_PAGE.split('id="advanced-evidence"', 1)[1].split('id="craftsman-badges"', 1)[0]
    assert "<summary>高级/证据</summary>" in advanced
    for marker in ('id="how-to-read"', 'id="t1-checksums"', 'id="gate-results"', 'id="claim-ledger"'):
        assert marker in advanced


def test_issue_664_craftsman_main_path_has_no_protocol_pile():
    """默认职人主路径可见文案无 claim/latch/T0/fail-closed;协议在高级/证据。"""
    from fastapi.testclient import TestClient

    from freshlatch.ui.app import app

    for html in (HTML_PAGE, TestClient(app).get("/").text):
        text = _craftsman_main_text(html)
        assert "仍可信" in text and "可能过期" in text and "要你确认" in text
        assert "高级/证据" in text
        for word in _PROTOCOL_WORDS:
            assert word not in text, word
    assert "protocol-inline" in HTML_PAGE
    assert 'html[data-view="craftsman"] .protocol-inline{display:none}' in HTML_PAGE


def test_issue_664_decide_leaves_confirm_list_and_block_keeps_lists():
    """作废/续命后离开要你确认;挡续命只出成功说明,不清空三类清单。"""
    names = (
        "esc", "pickedAction", "renewOptions", "renewButton", "explainRenewBlocked",
        "awaitingConfirm", "vernacularBucket", "vernacularItemHtml", "fillVernacular",
        "renderVernacularLists",
    )
    src = "\n".join(_grab_js(name) for name in names)
    script = r"""
const RENEW_BLOCKED_COPY = __COPY__;
let PENDING_DECISIONS = [];
let STATE = {claims: [], latch: {pending: []}};
const els = {};
function makeEl(id){
  return {id: id, innerHTML: "", textContent: "", attrs: {},
    setAttribute(k, v){ this.attrs[k] = v; },
    classList: {add(c){ this._c = c; }}};
}
for (const id of ["list-still-trusted-items","list-maybe-stale-items","list-needs-you-items","renew-blocked-note"]) {
  els[id] = makeEl(id);
}
global.document = {getElementById(id){ return els[id] || null; }};
__SRC__
function textOf(id){ return els[id].innerHTML; }
STATE.claims = [
  {claim_id:"a", status:"fresh", statement:"仍成立的结论", t0_evidence_ids:[], t1_evidence_ids:[]},
  {claim_id:"b", status:"stale", statement:"过期结论", t0_evidence_ids:[], t1_evidence_ids:[]},
  {claim_id:"c", status:"unknown", statement:"证据不够", t0_evidence_ids:[], t1_evidence_ids:[]},
  {claim_id:"d", status:"stale", statement:"请你拍板", t0_evidence_ids:[], t1_evidence_ids:[]}
];
STATE.latch = {thread_id:"t", pending:[{claim_id:"c"},{claim_id:"d"}]};
renderVernacularLists();
if (!textOf("list-still-trusted-items").includes("仍成立的结论")) process.exit(2);
if (!textOf("list-maybe-stale-items").includes("过期结论")) process.exit(3);
if (textOf("list-maybe-stale-items").includes("证据不够")) process.exit(4);
if (!textOf("list-needs-you-items").includes("证据不够")) process.exit(5);
if (!textOf("list-needs-you-items").includes("请你拍板")) process.exit(6);
if (!textOf("list-needs-you-items").includes(">作废<")) process.exit(7);
if (!textOf("list-needs-you-items").includes(">续命<")) process.exit(8);
PENDING_DECISIONS = [{claim_id:"d", action:"discard"}];
renderVernacularLists();
if (textOf("list-needs-you-items").includes("请你拍板")) process.exit(9);
if (!textOf("list-maybe-stale-items").includes("请你拍板")) process.exit(10);
if (!textOf("list-still-trusted-items").includes("仍成立的结论")) process.exit(11);
if (!textOf("list-needs-you-items").includes("证据不够")) process.exit(12);
PENDING_DECISIONS = [{claim_id:"c", action:"renew"}];
renderVernacularLists();
if (textOf("list-needs-you-items").includes("证据不够")) process.exit(13);
const before = {
  fresh: textOf("list-still-trusted-items"),
  maybe: textOf("list-maybe-stale-items"),
  confirm: textOf("list-needs-you-items")
};
explainRenewBlocked("d");
if (textOf("list-still-trusted-items") !== before.fresh) process.exit(14);
if (textOf("list-maybe-stale-items") !== before.maybe) process.exit(15);
if (textOf("list-needs-you-items") !== before.confirm) process.exit(16);
if (!els["renew-blocked-note"].textContent.includes("挡住=产品在干活")) process.exit(17);
if (STATE.claims.length !== 4) process.exit(19);
console.log("ok");
""".replace("__COPY__", json.dumps(
        "续命被挡住。挡住=产品在干活:没有可核对的新材料,或既有闸拦住了。清单还在。"
    )).replace("__SRC__", src)
    # 成功文案必须与页面常量一致,避免测试另写一套
    assert "挡住=产品在干活" in HTML_PAGE
    assert 'title="本轮无已检索 T1 原文块,续命不可用"' in HTML_PAGE
    assert "explainRenewBlocked" in _grab_js("renewButton")
    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "ok" in proc.stdout
    blocked = _grab_js("explainRenewBlocked")
    assert "STATE.claims" not in blocked
    assert "innerHTML" not in blocked
    submit = HTML_PAGE.split("async function submitDecisions(")[1].split("\nasync function ")[0]
    assert "renewBlocked" in submit
    assert "RENEW_BLOCKED_COPY" in submit
    assert "list-still-trusted-items" not in submit

