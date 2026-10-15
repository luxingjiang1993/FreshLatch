"""把本仓薄探针挂进已安装的 garak, 再调用文档化 CLI.

只应由 optional_garak_tool_injection_scan.py 在操作者显式开启后拉起.
导入本模块不会 import garak.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_PROBE_KEY = "probes.freshlatch_tool_injection.ToolInjection"


def _install_adapters() -> None:
    """扩展 garak 的 probes 搜索路径, 并让 --spec 能解析到本仓探针."""
    import garak.probes as probes_pkg
    from garak._plugins import PluginCache

    probes_pkg.__path__.append(str(_ROOT / "probes"))
    import garak.detectors as detectors_pkg

    detectors_pkg.__path__.append(str(_ROOT / "detectors"))
    sys.path.insert(0, str(_ROOT))

    import importlib

    importlib.import_module("garak.probes.freshlatch_tool_injection")
    importlib.import_module("garak.detectors.freshlatch_tool_injection")

    original = PluginCache.instance

    def instance():
        data = original()
        probes = data.setdefault("probes", {})
        probes.setdefault(
            _PROBE_KEY,
            {
                "active": False,
                "description": "FreshLatch tool-injection prompt set",
                "tier": 9,
                "tags": ["owasp:llm01"],
            },
        )
        return data

    PluginCache.instance = staticmethod(instance)


def main() -> None:
    _install_adapters()
    from garak.__main__ import main as garak_main

    garak_main()


if __name__ == "__main__":
    main()
