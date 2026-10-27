"""HYG-05：复验单两页从静态文件读入，业务模块不再嵌整页 HTML。"""

from __future__ import annotations

from pathlib import Path

from freshlatch.ui import app as appmod
from freshlatch.ui import session_state as ss

ROOT = Path(__file__).resolve().parents[2]
APP_PY = ROOT / "src" / "freshlatch" / "ui" / "app.py"
SESSION_STATE_PY = ROOT / "src" / "freshlatch" / "ui" / "session_state.py"
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
    assert ">一键样例</button>" in appmod.HTML_PAGE
    # #755:会话可变容器真相源在 session_state;app.py 可再导出同对象
    ss_src = SESSION_STATE_PY.read_text(encoding="utf-8")
    assert "_state: dict" in ss_src
    assert appmod._state is ss._state
    assert "def create_app" not in src
