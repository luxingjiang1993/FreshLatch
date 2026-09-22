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
    """DEM-6:可切换审计视图并看到轨迹/角色信息。"""
    assert "function setViewMode(" in HTML_PAGE
    assert 'setViewMode(&quot;audit&quot;)' in HTML_PAGE
    assert 'id="audit-panel"' in HTML_PAGE
    assert "Agent 轨迹" in HTML_PAGE or "工具轨迹" in HTML_PAGE
    assert "Lead" in HTML_PAGE  # 审计视图文案允许角色名
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
    """DEM-6:审计视图才展示轨迹路径与角色向状态文案。"""
    assert "STATUS_RUNNING_AUDIT" in HTML_PAGE
    assert "STATUS_DONE_AUDIT" in HTML_PAGE
    m = re.search(r'STATUS_RUNNING_AUDIT\s*=\s*[\'"]([^\'"]*)[\'"]', HTML_PAGE)
    assert m and "Lead" in m.group(1)
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
