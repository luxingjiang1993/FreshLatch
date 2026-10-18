"""DEM-6 职人/审计视图:复验单 UI 套件(α-demo)。

层标注:demo。禁止升格为「产品已验证 / latch 已证」——latch 由 Void→Stay-Red / 闸证明。
测试 seam:复验单 UI(源码/DOM 断言 + TestClient),不开第四类 harness。
切换不改变 Latch/Gate 语义:本套件只断言呈现密度与切换可见性。
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from freshlatch.ui.app import HTML_PAGE, VIEW_MODE_DEFAULT, _VIEW_MODE_TOKEN, app


def test_default_view_is_craftsman():
    """DEM-6:默认进入职人视图(去角色化成交面)。"""
    assert VIEW_MODE_DEFAULT == "craftsman"
    assert 'id="view-craftsman"' in HTML_PAGE
    assert 'id="view-audit"' in HTML_PAGE
    assert f'let VIEW_MODE = "{_VIEW_MODE_TOKEN}"' in HTML_PAGE
    assert 'id="view-craftsman" class="on"' in HTML_PAGE
    # 默认审计面板无 visible(成交面不露轨迹)
    assert 'id="audit-panel"' in HTML_PAGE
    assert 'id="audit-panel" class="visible"' not in HTML_PAGE


def test_can_switch_to_audit_view():
    """DEM-6 / L4-UI-01:可切换审计视图。标签是中性词,页面源码不含角色专名。"""
    assert "function setViewMode(" in HTML_PAGE
    assert 'setViewMode(&quot;audit&quot;)' in HTML_PAGE
    assert 'id="audit-panel"' in HTML_PAGE
    assert "工具轨迹" in HTML_PAGE
    assert "查询" in HTML_PAGE
    assert "命中" in HTML_PAGE
    assert "判定依据" in HTML_PAGE
    assert "未知原因" in HTML_PAGE
    assert "复验 / 反证 / 闸" in HTML_PAGE
    for role in ("Lead", "Critic", "Auditor"):
        assert role not in HTML_PAGE
    # 切换后可见性:add/remove visible
    assert 'panel.classList.add("visible")' in HTML_PAGE
    assert 'panel.classList.remove("visible")' in HTML_PAGE


def test_craftsman_default_surface_hides_role_chrome():
    """DEM-6:职人默认成交面不用 Lead/Critic/轨迹路径作状态栏文案。"""
    assert "STATUS_RUNNING_CRAFTSMAN" in HTML_PAGE
    assert "STATUS_DONE_CRAFTSMAN" in HTML_PAGE
    for name in ("STATUS_RUNNING_CRAFTSMAN", "STATUS_DONE_CRAFTSMAN"):
        m = re.search(rf'{name}\s*=\s*[\'"]([^\'"]*)[\'"]', HTML_PAGE)
        assert m, f"缺常量 {name}"
        text = m.group(1)
        for leak in ("Lead", "Critic", "Auditor", "Forensic", "轨迹"):
            assert leak not in text, f"职人文案 {name} 泄漏「{leak}」: {text}"


def test_audit_view_exposes_trajectory_and_roles():
    """DEM-6 / L4-UI-01:审计视图展示轨迹字段,状态文案不用角色专名。"""
    assert "STATUS_RUNNING_AUDIT" in HTML_PAGE
    assert "STATUS_DONE_AUDIT" in HTML_PAGE
    m = re.search(r'STATUS_RUNNING_AUDIT\s*=\s*[\'"]([^\'"]*)[\'"]', HTML_PAGE)
    assert m
    for role in ("Lead", "Critic", "Auditor"):
        assert role not in m.group(1)
    assert "复验" in m.group(1)
    assert "闸" in m.group(1)
    assert 'VIEW_MODE === "audit"' in HTML_PAGE


def test_switch_back_hides_audit_as_default_deal_surface():
    """DEM-6:切回职人后工程角色信息不作为默认成交面。"""
    assert 'setViewMode(&quot;craftsman&quot;)' in HTML_PAGE
    assert 'VIEW_MODE === "craftsman"' in HTML_PAGE
    body = HTML_PAGE.split("function renderViewChrome(")[1].split("\nfunction ")[0]
    assert 'classList.remove("visible")' in body


def test_view_switch_does_not_call_latch_or_gate():
    """DEM-6:切换不改变作废/续命/闸行为——setViewMode 只改呈现,不碰 latch API。"""
    body = HTML_PAGE.split("function setViewMode(")[1].split("\nfunction ")[0]
    for forbidden in ("/api/latch/", "/api/reverify", "submitDecisions", "confirmVoid", "confirmRenew"):
        assert forbidden not in body, f"setViewMode 不得触发 {forbidden}"


def test_served_html_injects_view_mode_default():
    """服务出去的 HTML 注入 VIEW_MODE_DEFAULT,占位符不得残留。"""
    html = TestClient(app).get("/").text
    assert "职人视图" in html
    assert "审计视图" in html
    assert "setViewMode" in html
    assert "__VIEW_MODE_DEFAULT__" not in html
    assert f'let VIEW_MODE = "{VIEW_MODE_DEFAULT}"' in html
    assert 'id="view-craftsman" class="on"' in html
    assert 'id="audit-panel" class="visible"' not in html


# -- I-11(#710 / 决议 #704):职人首屏降噪 -------------------------------------------------


def test_i11_craftsman_first_screen_noise_hidden_by_view_css():
    """预算计数/课题标签/导入稿入口只在审计视图露出;元素保留在 DOM(测试 seam 不变)。"""
    for rule in (
        'html[data-view="craftsman"] #budget-progress{display:none}',
        'html[data-view="craftsman"] #pack-badge{display:none}',
        'html[data-view="craftsman"] #btn-import-draft{display:none}',
    ):
        assert rule in HTML_PAGE, f"缺职人隐藏规则: {rule}"
    assert 'id="budget-progress"' in HTML_PAGE
    assert 'id="pack-badge"' in HTML_PAGE
    assert 'id="btn-import-draft"' in HTML_PAGE
    # SYNTHETIC 短中文由服务端按视图注入(见 test_i11_served_html_synthetic_label)
    from freshlatch.ui.app import SYN_BADGE_FULL_TEXT
    assert SYN_BADGE_FULL_TEXT in HTML_PAGE


def test_i11_t1_status_plain_language_branch():
    """职人首屏只露白话 T1 状态(就绪/缺源料);三卡面板只在审计视图渲染。"""
    assert "function renderT1StatusShort(" in HTML_PAGE
    assert "已就绪" in HTML_PAGE
    assert "缺源料" in HTML_PAGE
    assert 'id="t1-status-short"' in HTML_PAGE
    branch = '(VIEW_MODE === "audit") ? renderT1Source() : renderT1StatusShort()'
    assert branch in HTML_PAGE
    # 导入稿全文同样只进审计视图
    assert 'if(VIEW_MODE === "audit"){' in HTML_PAGE
    assert 'id="claim-import-draft"' in HTML_PAGE


def test_i11_served_html_synthetic_label():
    """职人服务态 HTML 用短中文「当前为演示合成包」;审计视图保留原标签。"""
    from freshlatch.ui.app import SYN_BADGE_FULL_TEXT, SYN_BADGE_SHORT_TEXT

    craftsman = TestClient(app).get("/").text
    assert SYN_BADGE_SHORT_TEXT in craftsman
    assert SYN_BADGE_FULL_TEXT not in craftsman
    audit = TestClient(app).get("/?view=audit").text
    assert SYN_BADGE_FULL_TEXT in audit
    assert SYN_BADGE_SHORT_TEXT not in audit
