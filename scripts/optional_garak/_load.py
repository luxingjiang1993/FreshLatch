"""按文件路径加载本目录模块, 登记进 sys.modules.

不修改模块搜索路径. 探针与检测器在 bootstrap 预加载之后,
可以用普通 import 命中已登记的 freshlatch_match.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_local(name: str, path: Path):
    """加载 path 对应的模块. 已登记则直接返回."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
