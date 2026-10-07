"""HYG-05：复验单两页从静态文件读入，业务模块不再嵌整页 HTML。"""

from __future__ import annotations

from pathlib import Path

from freshlatch.ui import app as appmod

ROOT = Path(__file__).resolve().parents[2]
APP_PY = ROOT / "src" / "freshlatch" / "ui" / "app.py"
STATIC = ROOT / "src" / "freshlatch" / "ui" / "static"


def test_pages_loaded_from_static_not_inline():
    src = APP_PY.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" not in src
    assert 'HTML_PAGE = """' not in src
    assert 'PREPUBLISH_HTML = """' not in src
    reverify = (STATIC / "reverify.html").read_text(encoding="utf-8")
    prepublish = (STATIC / "prepublish.html").read_text(encoding="utf-8")
    assert appmod.HTML_PAGE == reverify
    assert appmod.PREPUBLISH_HTML == prepublish
    assert ">开始复验</button>" in appmod.HTML_PAGE
    assert "_state: dict" in src
    assert "def create_app" not in src
