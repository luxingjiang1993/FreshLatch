"""运行时读取包属性，使测试对包上的替换在调用点可见。"""

from __future__ import annotations


def _pkg_attr(name: str):
    import freshlatch.eval.x1_drafts as pkg

    return getattr(pkg, name)
